'''
  ******************************************************************************************
      Assembly:                Mappy
      Filename:                geocode.py
      Author:                  Terry D. Eppler
      Created:                 05-31-2022

      Last Modified By:        Terry D. Eppler
      Last Modified On:        05-01-2025
  ******************************************************************************************
  <copyright file='geocode.py' company='Terry D. Eppler'>

	     Mappy is a python framework encapsulating the Google Maps functionality.
	     Copyright ©  2022  Terry Eppler

	     Purpose:
		    High-level Geocoding service that resolves addresses or city/state/country
		    triples into canonical address stores and coordinates.


     Permission is hereby granted, free of charge, to any person obtaining a copy
     of this software and associated documentation files (the “Software”),
     to deal in the Software without restriction,
     including without limitation the rights to use,
     copy, modify, merge, publish, distribute, sublicense,
     and/or sell copies of the Software,
     and to permit persons to whom the Software is furnished to do so,
     subject to the following conditions:

     The above copyright notice and this permission notice shall be included in all
     copies or substantial portions of the Software.

     THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
     INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
     FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT.
     IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
     DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
     ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
     DEALINGS IN THE SOFTWARE.

     You can contact me at:  terryeppler@gmail.com or eppler.terry@epa.gov

  </copyright>
  <summary>
    geocode.py
  </summary>
  ******************************************************************************************
'''
from typing import Any, Dict, Optional, List, Tuple
from caches import BaseCache
from exceptions import NotFound
from maps import Maps
from boogr import Error, Logger

def throw_if( name: str, value: object ) -> None:
	"""Validate that a required geocoding value is present.

	Purpose:
		Provides a lightweight guard for required Geocoder inputs before cache-key
		construction, coordinate validation, gateway requests, and batch processing.
		The function rejects missing objects and blank strings so geocoding workflows
		fail with clear validation messages before issuing external API calls.

	Args:
		name: Name of the argument being validated.
		value: Runtime value to validate.

	Raises:
		ValueError: Raised when ``value`` is ``None`` or an empty string.
	"""
	if value is None:
		raise ValueError( f'Argument "{name}" cannot be None.' )
	
	if isinstance( value, str ) and not value.strip( ):
		raise ValueError( f'Argument "{name}" cannot be empty.' )

def flatten_geocode( result: Dict[ str, Any ] ) -> Dict[ str, Any ]:
	"""Flatten a Google Geocoding result into Mappy's canonical row shape.

	Purpose:
		Extracts the formatted address, coordinates, place identifier, result types,
		country values, administrative areas, locality, and postal code from one
		Google Geocoding API result. The returned dictionary is used by single-record
		geocoding, reverse geocoding, batch geocoding, spreadsheet enrichment, and
		Streamlit result previews.

	Args:
		result: One result dictionary from the Google Geocoding API ``results`` list.

	Returns:
		Dict[str, Any]: Flattened geocode output suitable for rows, cache payloads,
			and UI display.
	"""
	geometry = result.get( 'geometry', { } ) or { }
	loc = geometry.get( 'location', { } ) or { }
	comps = result.get( 'address_components', [ ] ) or [ ]
	
	def comp( kind: str, want_long: bool = False ) -> Optional[ str ]:
		for c in comps:
			if kind in (c.get( 'types' ) or [ ]):
				return (c.get( 'long_name' ) if want_long else c.get( 'short_name' )) or None
		return None
	
	return {
			'formatted_address': result.get( 'formatted_address' ),
			'lat': loc.get( 'lat' ),
			'lng': loc.get( 'lng' ),
			'place_id': result.get( 'place_id' ),
			'types': ','.join( result.get( 'types', [ ] ) ) if result.get( 'types' ) else None,
			'country_code': comp( 'country' ),
			'country_name': comp( 'country', want_long=True ),
			'admin_level_1': comp( 'administrative_area_level_1' ),
			'admin_level_2': comp( 'administrative_area_level_2' ),
			'locality': comp( 'locality' ) or comp( 'postal_town' ),
			'postal_code': comp( 'postal_code' ),
	}

class Geocoder( ):
	"""Provide forward, reverse, structured, and batch geocoding.

	Purpose:
		Coordinates Google Geocoding API requests through the shared ``Maps`` gateway
		and optional cache backend. The class resolves free-form addresses,
		latitude/longitude pairs, and city/state/country triples into a consistent
		flattened output shape used by Streamlit workflows, Excel/CSV enrichment,
		local data-management updates, and downstream location intelligence tasks.

	Attributes:
		maps: Public reference to the Google Maps gateway.
		cache: Optional public cache backend reference.
		prefix: Cache namespace prefix used during key construction.
		data: Raw response payload returned by the Google Maps gateway.
		output: Last flattened geocoding result.
		parts: Structured query or cache-key parts from the latest request.
		city: City value from the latest structured lookup.
		address: Free-form address value from the latest lookup.
		state: State, province, territory, or region from the latest lookup.
		country: Country or country bias from the latest lookup.
		comps: Optional component parameters sent to the Geocoding API.
		key: Cache key for the latest lookup.
		query: Query text built for the latest structured lookup.
		latitude: Latitude from the latest reverse-geocode lookup.
		longitude: Longitude from the latest reverse-geocode lookup.
	"""
	maps: Optional[ Maps ]
	cache: Optional[ BaseCache ]
	prefix: Optional[ str ]
	data: Optional[ Dict ]
	output: Optional[ Dict ]
	parts: Optional[ Tuple ]
	city: Optional[ str ]
	address: Optional[ str ]
	state: Optional[ str ]
	country: Optional[ str ]
	comps: Optional[ Dict[ str, str ] ]
	key: Optional[ str ]
	query: Optional[ str ]
	latitude: Optional[ float ]
	longitude: Optional[ float ]
	
	def __init__( self, maps: Maps, cache: Optional[ BaseCache ] = None ) -> None:
		"""Initialize the geocoding service wrapper.

		Purpose:
			Stores the shared Google Maps gateway, optional cache backend, and runtime
			state used by forward, reverse, structured, and batch geocoding methods.
			The constructor performs local assignment only and prepares the instance for
			later API-backed lookup operations.

		Args:
			maps: Google Maps gateway used for Geocoding API requests.
			cache: Optional cache backend used to store and retrieve lookup results.
		"""
		self._maps = maps
		self._cache = cache
		self.maps = maps
		self.cache = cache
		self.prefix = None
		self.data = None
		self.output = None
		self.parts = None
		self.city = None
		self.address = None
		self.state = None
		self.country = None
		self.comps = None
		self.key = None
		self.query = None
		self.latitude = None
		self.longitude = None
	
	def key_for( self, prefix: str, *parts: str ) -> str | None:
		"""Build a stable cache key for a geocoding operation.

		Purpose:
			Combines an operation prefix and one or more identifying values into the
			cache-key format used by forward and reverse geocoding. The method stores
			the latest prefix and parts on the instance so cache behavior can be
			inspected during debugging and Streamlit workflows.

		Args:
			prefix: Cache namespace or operation prefix.
			*parts: Values that uniquely identify the request.

		Returns:
			str | None: Normalized cache key.

		Raises:
			Error: Raised after logging when validation or key construction fails.
		"""
		try:
			throw_if( 'prefix', prefix )
			throw_if( 'parts', parts )
			self.prefix = prefix
			self.parts = parts
			joined = ' '.join( str( p ).strip( ) for p in parts if p and str( p ).strip( ) )
			return f'{prefix}::{joined}'
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'Geocoder'
			exception.method = 'key_for( self, prefix: str, *parts: str ) -> str | None'
			Logger( ).write( exception )
			raise exception
	
	def validate_coordinates( self, latitude: float, longitude: float ) -> Tuple[ float, float ]:
		"""Validate and normalize a latitude/longitude pair.

		Purpose:
			Converts coordinate inputs to floats and enforces valid geographic ranges
			before reverse-geocoding requests are sent to the Google Geocoding API. The
			method prevents invalid coordinates from reaching cache-key generation or
			gateway request construction.

		Args:
			latitude: Latitude in decimal degrees.
			longitude: Longitude in decimal degrees.

		Returns:
			Tuple[float, float]: Validated latitude and longitude values.

		Raises:
			Error: Raised after logging when validation or conversion fails.
		"""
		try:
			throw_if( 'latitude', latitude )
			throw_if( 'longitude', longitude )
			lat = float( latitude )
			lng = float( longitude )
			if lat < -90.0 or lat > 90.0:
				raise ValueError( 'Latitude must be between -90 and 90.' )
			if lng < -180.0 or lng > 180.0:
				raise ValueError( 'Longitude must be between -180 and 180.' )
			return lat, lng
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'Geocoder'
			exception.method = 'validate_coordinates( self, latitude: float, longitude: float ) -> Tuple[ float, float ]'
			Logger( ).write( exception )
			raise exception
	
	def freeform( self, address: str, country: str = 'US' ) -> Dict[ str, Any ] | None:
		"""Geocode a free-form address string.

		Purpose:
			Resolves a human-readable address through the Google Geocoding API with an
			optional country bias. The method checks the cache before calling the
			gateway, stores raw and flattened response state on the instance, writes
			successful lookups back to the cache, and returns Mappy's canonical
			location output shape.

		Args:
			address: Human-entered address, place, or location text.
			country: Optional ISO-3166 alpha-2 country code used as a result bias.

		Returns:
			Dict[str, Any] | None: Flattened geocode result.

		Raises:
			Error: Raised after logging when validation, lookup, gateway handling, or
				result processing fails.
		"""
		try:
			throw_if( 'address', address )
			self.address = address.strip( )
			self.country = str( country or '' ).strip( )
			self.key = self.key_for( 'geocode', self.address, self.country )
			if self._cache:
				hit = self._cache.get( self.key )
				if hit:
					return hit
			self.comps = { 'country': self.country.upper( ) } if self.country else None
			self.data = self._maps.request( 'geocode/json',
				{ 'address': self.address, **(self.comps or { }) } )
			
			if self.data.get( 'status' ) != 'OK' or not self.data.get( 'results' ):
				raise NotFound( f'No geocode for "{self.address}" ' )
			self.output = flatten_geocode( self.data[ 'results' ][ 0 ] )
			self.output[ 'source' ] = 'geocode'
			self.output[ 'query' ] = self.address
			if self._cache:
				self._cache.set( self.key, self.output )
			return self.output
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'Geocoder'
			exception.method = 'freeform( self, address: str, country: str=US ) -> Dict[ str, Any ] | None'
			Logger( ).write( exception )
			raise exception
	
	def reverse( self, latitude: float, longitude: float ) -> Dict[ str, Any ] | None:
		"""Reverse geocode a latitude/longitude coordinate pair.

		Purpose:
			Resolves geographic coordinates into a canonical address using the Google
			Geocoding API. The method validates coordinates, checks the cache, stores raw
			and flattened response state on the instance, writes successful lookups to
			the cache, and returns the same row-friendly shape used by forward geocoding.

		Args:
			latitude: Latitude in decimal degrees.
			longitude: Longitude in decimal degrees.

		Returns:
			Dict[str, Any] | None: Flattened reverse-geocode result.

		Raises:
			Error: Raised after logging when validation, lookup, gateway handling, or
				result processing fails.
		"""
		try:
			self.latitude, self.longitude = self.validate_coordinates( latitude, longitude )
			self.key = self.key_for( 'reverse_geocode', str( self.latitude ),
				str( self.longitude ) )
			if self._cache:
				hit = self._cache.get( self.key )
				if hit:
					return hit
			self.data = self._maps.request( 'geocode/json',
				{ 'latlng': f'{self.latitude},{self.longitude}' } )
			
			if self.data.get( 'status' ) != 'OK' or not self.data.get( 'results' ):
				raise NotFound( f'No reverse geocode for "{self.latitude},{self.longitude}" ' )
			self.output = flatten_geocode( self.data[ 'results' ][ 0 ] )
			self.output[ 'source' ] = 'reverse_geocode'
			self.output[ 'query' ] = f'{self.latitude},{self.longitude}'
			if self._cache:
				self._cache.set( self.key, self.output )
			return self.output
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'Geocoder'
			exception.method = 'reverse( self, **kwargs ) -> Dict[ str, Any ] | None'
			Logger( ).write( exception )
			raise exception
	
	def city_state_country( self, city: str, state: str, country: str ) -> Dict[ str, Any ] | None:
		"""Geocode a structured city, state, and country query.

		Purpose:
			Builds a free-form geocoding query from structured locality fields and
			delegates to ``freeform`` so caching, gateway execution, response flattening,
			and error handling remain consistent with ordinary address lookups. The
			method stores the structured parts and final query on the instance for later
			inspection by enrichment or UI workflows.

		Args:
			city: City or locality value.
			state: State, province, territory, or region value.
			country: Country name or short country code.

		Returns:
			Dict[str, Any] | None: Flattened geocode result.

		Raises:
			Error: Raised after logging when validation or delegated geocoding fails.
		"""
		try:
			throw_if( 'city', city )
			throw_if( 'country', country )
			self.city = city
			self.state = state
			self.country = country
			self.parts = tuple( [ p for p in [ self.city, self.state, self.country ] if p ] )
			self.query = ', '.join( self.parts )
			hint = (self.country.strip( ).upper( )
			        if self.country and len( self.country.strip( ) ) <= 3
			        else '')
			return self.freeform( self.query, hint )
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'Geocoder'
			exception.method = 'city_state_country( self, city: str, state: str, country: str ) -> Dict[ str, Any ] | None'
			Logger( ).write( exception )
			raise exception
	
	def batch_freeform( self, addresses: List[ str ], country: str = 'US' ) -> List[
		Dict[ str, Any ] ]:
		"""Geocode a list of free-form addresses.

		Purpose:
			Processes multiple address strings while preserving row-level status for
			successful lookups, skipped empty rows, and failed lookups. The method uses
			``freeform`` for each populated address so cache behavior, gateway calls, and
			flattened output remain consistent with single-record geocoding workflows.

		Args:
			addresses: Address strings to geocode.
			country: ISO-3166 alpha-2 country code used as the default country bias.

		Returns:
			List[Dict[str, Any]]: Flattened row-level geocode results with
				``geocode_status`` and ``geocode_error`` fields.

		Raises:
			Error: Raised after logging when batch-level validation or processing fails.
		"""
		try:
			throw_if( 'addresses', addresses )
			if not isinstance( addresses, list ):
				raise ValueError( 'addresses must be a list of strings.' )
			results: List[ Dict[ str, Any ] ] = [ ]
			for address in addresses:
				value = str( address or '' ).strip( )
				if not value:
					results.append( {
							'formatted_address': None,
							'lat': None,
							'lng': None,
							'place_id': None,
							'types': None,
							'country_code': None,
							'country_name': None,
							'admin_level_1': None,
							'admin_level_2': None,
							'locality': None,
							'postal_code': None,
							'source': 'geocode',
							'query': value,
							'geocode_status': 'skipped_empty',
							'geocode_error': None
					} )
					continue
				try:
					item = self.freeform( value, country=country ) or { }
					item[ 'geocode_status' ] = 'ok'
					item[ 'geocode_error' ] = None
					results.append( item )
				except Exception as row_error:
					results.append( {
							'formatted_address': None,
							'lat': None,
							'lng': None,
							'place_id': None,
							'types': None,
							'country_code': None,
							'country_name': None,
							'admin_level_1': None,
							'admin_level_2': None,
							'locality': None,
							'postal_code': None,
							'source': 'geocode',
							'query': value,
							'geocode_status': 'error',
							'geocode_error': str( row_error )
					} )
			return results
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'Geocoder'
			exception.method = 'batch_freeform( self, *args ) -> List[ Dict[ str, Any ] ]'
			Logger( ).write( exception )
			raise exception