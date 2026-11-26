'''
  ******************************************************************************************
      Assembly:                Iyrin
      Filename:                maps.py
      Author:                  Terry D. Eppler
      Created:                 05-31-2022

      Last Modified By:        Terry D. Eppler
      Last Modified On:        05-01-2025
  ******************************************************************************************
  <copyright file="maps.py" company="Terry D. Eppler">

	     Iyrin is a python framework encapsulating the Google Maps functionality.
	     Copyright ©  2022  Terry Eppler

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
    maps.py
  </summary>
  ******************************************************************************************
'''
import math
import time
from typing import Dict, Optional, List, Any, Tuple, Union
import requests
from urllib.parse import urlencode
import datetime as dt
from exceptions import GatewayError
from rates import RateLimiter
from boogr import Error, Logger
import config as cfg
from storage import BaseCache
from exceptions import NotFound
import pandas as pd

Coord = Tuple[ float, float ]
AddressOrCoord = Union[ str, Coord ]

def throw_if( name: str, value: object ) -> None:
	"""

		Purpose:
		Validate that a required value is not empty.

		Args:
		name (str): Name of the argument being validated.
		value (object): Value to validate.

		Returns:
		None: This operation has no return value.

	"""
	if value is None:
		raise ValueError( f'Argument "{name}" cannot be None.' )
	
	if isinstance( value, str ) and not value.strip( ):
		raise ValueError( f'Argument "{name}" cannot be empty.' )
	
	if isinstance( value, (list, tuple, dict, set) ) and len( value ) == 0:
		raise ValueError( f'Argument "{name}" cannot be empty.' )

def flatten_geocode( result: Dict[ str, Any ] ) -> Dict[ str, Any ]:
	"""

		Purpose:
			Reduce a geocode result into a compact, row-friendly dict.

		Args:
			result (Dict[str, Any]):
				One element from 'results' in Geocoding API response.

		Returns:
			Dict with formatted_address, lat, lng, place_id, types, and components.

	"""
	geometry = result.get( 'geometry', { } ) or { }
	loc = geometry.get( 'location', { } ) or { }
	comps = result.get( 'address_components', [ ] ) or [ ]
	
	def comp( kind: str, want_long: bool = False ) -> Optional[ str ]:
		"""Find an address component by Google component type.

		Purpose:
			Retrieve a matching Google address component using its documented type.

		Args:
			kind (str): Google address component type.
			want_long (bool): Return the long component name when True.

		Returns:
			Optional[str]: Component name, or None when not present.
		"""
		for c in comps:
			if kind in (c.get( 'types' ) or [ ]):
				return (c.get( 'long_name' ) if want_long else c.get( 'short_name' )) or None
		return None
	
	return { 'formatted_address': result.get( 'formatted_address' ), 'lat': loc.get( 'lat' ),
		'lng': loc.get( 'lng' ), 'place_id': result.get( 'place_id' ),
		'types': ','.join( result.get( 'types', [ ] ) ) if result.get( 'types' ) else None,
		'country_code': comp( 'country' ), 'country_name': comp( 'country', want_long=True ),
		'admin_level_1': comp( 'administrative_area_level_1' ),
		'admin_level_2': comp( 'administrative_area_level_2' ),
		'locality': comp( 'locality' ) or comp( 'postal_town' ),
		'postal_code': comp( 'postal_code' ), }

def fmt( o: AddressOrCoord ) -> str:
	"""

		Purpose:
			Normalize an origin/destination input to the API's expected string.

		Args:
			o (AddressOrCoord): Either "lat,lng" as tuple or a free-form string address.

		Returns: String representation for the API, "lat,lng" or the original string.

	"""
	throw_if( 'o', o )
	if isinstance( o, str ):
		return o
	if isinstance( o, tuple ) and len( o ) == 2:
		latitude, longitude = o
		if (type( latitude ) not in (int, float) or type( longitude ) not in (int,
			float) or not math.isfinite( latitude ) or not math.isfinite( longitude ) or not -90 <= latitude <= 90 or not -180 <= longitude <= 180):
			raise ValueError( 'Coordinates must be finite latitude/longitude values in range.' )
		return f'{latitude},{longitude}'
	raise TypeError( 'A location must be an address string or (latitude, longitude) tuple.' )

class Map( ):
	"""
	Google Maps HTTP gateway.

	Purpose:
		Manages authenticated Google Maps requests, throttling, retry state, and response diagnostics.

	Attributes:
		base_url (Optional[ str ]): Base URL for Google Maps Web Services.
		endpoint (Optional[ str ]): Current endpoint path.
		params (Optional[ Dict[ str, str ] ]): Parameters supplied for the current request.
		api_key (str): Configured Google Maps API credential.
		query_per_second (Optional[ float ]): Requested rate limit in queries per second.
		retries (Optional[ int ]): Maximum permitted retry attempts.
		min (Optional[ float ]): Initial retry backoff in seconds.
		max (Optional[ float ]): Maximum retry backoff in seconds.
		timeout (Optional[ float ]): HTTP request timeout in seconds.
		url (Optional[ str ]): Fully qualified URL for the current request.
		session (Optional[ requests.Session ]): Requests session used for HTTP transport.
		limiter (Optional[ RateLimiter ]): Rate limiter applied before each request.
		query (Optional[ Dict[ str, str ] ]): Current request query including the API credential.
		response (Optional[ requests.Response ]): Most recent HTTP response.
		last_url (Optional[ str ]): URL used for the most recent request.
		last_query (Optional[ Dict[ str, str ] ]): Last request query with the credential removed.
		last_status (Optional[ int ]): Last observed HTTP status code.
		last_elapsed_ms (Optional[ float ]): Last request elapsed time in milliseconds.
		last_payload_status (Optional[ str ]): Last Google API payload status.
		last_payload_error (Optional[ str ]): Last Google API payload error.
	"""
	base_url: Optional[ str ]
	endpoint: Optional[ str ]
	params: Optional[ Dict[ str, str ] ]
	api_key: str
	query_per_second: Optional[ float ]
	retries: Optional[ int ]
	min: Optional[ float ]
	max: Optional[ float ]
	timeout: Optional[ float ]
	url: Optional[ str ]
	session: Optional[ requests.Session ]
	limiter: Optional[ RateLimiter ]
	query: Optional[ Dict[ str, str ] ]
	response: Optional[ requests.Response ]
	last_url: Optional[ str ]
	last_query: Optional[ Dict[ str, str ] ]
	last_status: Optional[ int ]
	last_elapsed_ms: Optional[ float ]
	last_payload_status: Optional[ str ]
	last_payload_error: Optional[ str ]
	BASE = 'https://maps.googleapis.com/maps/api'
	
	def __init__( self, qps: float = 5.0, retries: int = 5, min: float = 1.0, max: float = 30.0,
		timeout: float = 15.0, api_key: Optional[ str ] = None ) -> None:
		"""Initialize the Google Maps session, rate limiter, credentials, and request state.

		Purpose:
			Initialize the Google Maps session, rate limiter, credentials, and request state.

		Args:
			qps (float): Requested Google Maps queries per second.
			retries (int): Maximum retry attempts for transient failures.
			min (float): Initial retry backoff in seconds.
			max (float): Maximum retry backoff in seconds.
			timeout (float): HTTP request timeout in seconds.
			api_key (Optional[str]): Explicit credential or None to use configuration.

		Returns:
			None: Initializes instance state.
		"""
		self.api_key = api_key if api_key is not None else cfg.GOOGLEMAPS_API_KEY
		self.query_per_second = qps
		self.limiter = RateLimiter( self.query_per_second )
		self.retries = retries
		self.min = min
		self.max = max
		self.timeout = timeout
		self.session = requests.Session( )
		self.base_url = self.BASE
		self.endpoint = None
		self.params = None
		self.url = None
		self.query = None
		self.response = None
		self.last_url = None
		self.last_query = None
		self.last_status = None
		self.last_elapsed_ms = None
		self.last_payload_status = None
		self.last_payload_error = None
	
	def request( self, endpoint: str, params: Dict[ str, str ] ) -> Dict | None:
		"""

	        Purpose:
	            Execute a GET request to the given Google Maps endpoint with query
	            params and robust retry/backoff for transient errors. The Google
	            Maps API key is injected as the "key" query parameter.

	        Args:
	            endpoint (str):
	                Endpoint path, e.g., "geocode/json", "distancematrix/json".
	            params (Dict[str, str]):
	                Query parameters for the request. "key" is injected.

	        Returns:
	            Parsed JSON dictionary on success.

        """
		try:
			throw_if( 'endpoint', endpoint )
			throw_if( 'params', params )
			throw_if( 'api_key', self.api_key )
			self.endpoint = endpoint
			self.params = params
			self.url = f'{self.base_url}/{self.endpoint}'
			self.last_url = self.url
			attempt = 0
			backoff = self.min
			while True:
				self.limiter.wait( )
				retryable_failure = False
				try:
					self.query = dict( self.params )
					self.query[ 'key' ] = self.api_key
					self.last_query = { key: value for key, value in self.query.items( ) if
						key != 'key' }
					start = time.perf_counter( )
					self.response = self.session.get( self.url, params=self.query, timeout=self.timeout )
					elapsed = time.perf_counter( ) - start
					self.last_elapsed_ms = round( elapsed * 1000.0, 3 )
					self.last_status = self.response.status_code
					if self.last_status != 200:
						if self.last_status in (408, 429, 500, 502, 503, 504):
							retryable_failure = True
							raise GatewayError( f'Transient HTTP {self.last_status}: '
							                    f'{self.response.text[ :200 ]}' )
						raise GatewayError( f'HTTP {self.last_status}: {self.response.text[ :200 ]}' )
					payload = self.response.json( )
					self.last_payload_status = None
					self.last_payload_error = None
					if isinstance( payload, dict ):
						payload_status = str( payload.get( 'status', '' ) or '' ).strip( )
						payload_error = str( payload.get( 'error_message', '' ) or '' ).strip( )
						self.last_payload_status = payload_status
						self.last_payload_error = payload_error
						hard_failures = { 'REQUEST_DENIED', 'OVER_DAILY_LIMIT', 'OVER_QUERY_LIMIT',
							'INVALID_REQUEST', 'MAX_ELEMENTS_EXCEEDED', 'MAX_DIMENSIONS_EXCEEDED',
							'UNKNOWN_ERROR' }
						if payload_status in hard_failures:
							message = payload_error or f'Google API status: {payload_status}'
							if payload_status in ('OVER_QUERY_LIMIT', 'UNKNOWN_ERROR'):
								retryable_failure = True
								raise GatewayError( f'Transient Google API status {payload_status}: {message}' )
							raise GatewayError( f'Google API status {payload_status}: {message}' )
					return payload
				except (requests.Timeout, requests.ConnectionError, GatewayError) as ex:
					if isinstance( ex, GatewayError ) and not retryable_failure:
						raise
					attempt += 1
					if attempt > self.retries:
						raise GatewayError( f'Exceeded retries: {ex}' ) from ex
					time.sleep( backoff )
					backoff = min( backoff * 2, self.max )
		except Exception as e:
			exception = Error( e )
			exception.module = 'mapping'
			exception.cause = 'Maps'
			exception.method = "request( self, endpoint: str, params: Dict[ str, str ] ) -> Dict | None"
			Logger( ).write( exception )
			raise exception from e

class Geocoder( ):
	"""
	Google geocoding client.

	Purpose:
		Resolves addresses and coordinates and optionally caches geocoding results.

	Attributes:
		maps (Optional[ Map ]): Google Maps gateway used for requests.
		cache (Optional[ BaseCache ]): Optional cache for resolved locations.
		_maps (Map): Google Maps gateway used by geocoding methods.
		_cache (Optional[BaseCache]): Optional cache used internally.
		prefix (Optional[ str ]): Namespace prefix for generated cache keys.
		data (Optional[ Dict ]): Most recently retrieved API payload.
		output (Optional[ Dict ]): Most recently normalized location record.
		parts (Optional[ Tuple ]): Current cache-key components.
		city (Optional[ str ]): Current city input.
		address (Optional[ str ]): Current address input.
		state (Optional[ str ]): Current state input.
		country (Optional[ str ]): Current country or region bias.
		comps (Optional[ Dict[ str, str ] ]): Extracted address component values.
		key (Optional[ str ]): Cache key for the current lookup.
		query (Optional[ str ]): Current geocoding search value.
		latitude (Optional[ float ]): Current latitude in decimal degrees.
		longitude (Optional[ float ]): Current longitude in decimal degrees.
	"""
	maps: Optional[ Map ]
	cache: Optional[ BaseCache ]
	_maps: Map
	_cache: Optional[ BaseCache ]
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
	
	def __init__( self, maps: Map, cache: Optional[ BaseCache ] = None ) -> None:
		"""Initialize geocoding with a Google Maps gateway and optional cache.

		Purpose:
			Initialize geocoding with a Google Maps gateway and optional cache.

		Args:
			maps (Map): Initialized Google Maps API gateway.
			cache (Optional[BaseCache]): Optional geocoding cache.

		Returns:
			None: Initializes instance state.
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
	
	def key_for( self, prefix: str, parts: List[ str ] ) -> str | None:
		"""

			Purpose:
				Create a stable cache key from a namespace prefix and one or more
				string parts.

			Args:
				prefix (str):
					Cache namespace or operation prefix.
				parts (List[str]):
					Values that uniquely identify the request.

			Returns:
				str | None:
					Normalized cache key.

		"""
		try:
			throw_if( 'prefix', prefix )
			throw_if( 'parts', parts )
			if not isinstance( prefix, str ) or not isinstance( parts, list ) or any(
					not isinstance( part, str ) for part in parts ):
				raise TypeError( 'prefix must be a string and parts a list of strings.' )
			self.prefix = prefix
			self.parts = parts
			joined = ' '.join( str( p ).strip( ) for p in parts if p and str( p ).strip( ) )
			return f'{self.prefix}::{joined}'
		except Exception as e:
			exception = Error( e )
			exception.module = 'mapping'
			exception.cause = 'Geocoder'
			exception.method = "key_for( self, prefix: str, parts: List[ str ] ) -> str | None"
			raise exception
	
	def validate_coordinates( self, latitude: float, longitude: float ) -> Tuple[ float, float ]:
		"""

			Purpose:
				Validate and normalize a latitude/longitude coordinate pair.

			Args:
				latitude (float):
					Latitude in decimal degrees.
				longitude (float):
					Longitude in decimal degrees.

			Returns:
				Tuple[float, float]:
					Validated latitude and longitude.

		"""
		try:
			throw_if( 'latitude', latitude )
			throw_if( 'longitude', longitude )
			if (type( latitude ) not in (int, float) or type( longitude ) not in (int,
				float) or not math.isfinite( latitude ) or not math.isfinite( longitude )):
				raise ValueError( 'Coordinates must be finite numeric values.' )
			lat = latitude
			lng = longitude
			if lat < -90.0 or lat > 90.0:
				raise ValueError( 'Latitude must be between -90 and 90.' )
			if lng < -180.0 or lng > 180.0:
				raise ValueError( 'Longitude must be between -180 and 180.' )
			return lat, lng
		except Exception as e:
			exception = Error( e )
			exception.module = 'mapping'
			exception.cause = 'Geocoder'
			exception.method = "validate_coordinates( self, latitude: float, longitude: float ) -> Tuple[ float, float ]"
			raise exception
	
	def freeform( self, address: str, country: str = 'US' ) -> Dict[ str, Any ] | None:
		"""

			Purpose:
				Geocode a free-form address string. Optionally bias by country code.

			Args:
				address (str):
					Any human-entered address string.
				country (str):
					ISO-3166 alpha-2 country code to bias results, such as 'US'
					or 'FR'. Pass an empty string to disable country bias.

			Returns:
				Dict[str, Any] | None:
					Flattened geocode result.

			Raises:
				NotFound:
					Raised when no results are returned.

		"""
		try:
			throw_if( 'address', address )
			self.address = address.strip( )
			self.country = str( country or '' ).strip( )
			self.key = self.key_for( 'geocode', [ self.address, self.country ] )
			if self._cache:
				hit = self._cache.get( self.key )
				if hit:
					return hit
			self.comps = { 'country': self.country.upper( ) } if self.country else None
			self.data = self._maps.request( 'geocode/json', { 'address': self.address,
				**(self.comps or { }) } )
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
			exception.module = 'mapping'
			exception.cause = 'Geocoder'
			exception.method = "freeform( self, address: str, country: str='US' ) -> Dict[ str, Any ] | None"
			raise exception
	
	def reverse( self, latitude: float, longitude: float ) -> Dict[ str, Any ] | None:
		"""

			Purpose:
				Reverse geocode a latitude/longitude pair into a canonical address.

			Args:
				latitude (float):
					Latitude in decimal degrees.
				longitude (float):
					Longitude in decimal degrees.

			Returns:
				Dict[str, Any] | None:
					Flattened geocode result.

			Raises:
				NotFound:
					Raised when no reverse-geocode result is returned.

		"""
		try:
			throw_if( 'latitude', latitude )
			throw_if( 'longitude', longitude )
			self.latitude, self.longitude = self.validate_coordinates( latitude, longitude )
			self.key = self.key_for( 'reverse_geocode', [ str( self.latitude ),
				str( self.longitude ) ] )
			if self._cache:
				hit = self._cache.get( self.key )
				if hit:
					return hit
			self.data = self._maps.request( 'geocode/json', {
				'latlng': f'{self.latitude},{self.longitude}' } )
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
			exception.module = 'mapping'
			exception.cause = 'Geocoder'
			exception.method = "reverse( self, latitude: float, longitude: float ) -> Dict[ str, Any ] | None"
			raise exception
	
	def city_state_country( self, city: str, state: str, country: str ) -> Dict[ str, Any ] | None:
		"""

			Purpose:
				Geocode a structured city/state/country triple.

			Args:
				city (str):
					City or locality.
				state (str):
					State, province, territory, or region. May be empty.
				country (str):
					Country name or ISO-2 country code.

			Returns:
				Dict[str, Any] | None:
					Flattened geocode result.

			Raises:
				NotFound:
					Raised when no result is available.

		"""
		try:
			throw_if( 'city', city )
			if state is None:
				throw_if( 'state', state )
			if not isinstance( state, str ):
				raise TypeError( 'state must be a string; an empty string is allowed.' )
			throw_if( 'country', country )
			self.city = city
			self.state = state
			self.country = country
			self.parts = tuple( [ p for p in [ self.city, self.state, self.country ] if p ] )
			self.query = ', '.join( self.parts )
			hint = (
				self.country.strip( ).upper( ) if self.country and len( self.country.strip( ) ) <= 3 else '')
			return self.freeform( self.query, hint )
		except Exception as e:
			exception = Error( e )
			exception.module = 'mapping'
			exception.cause = 'Geocoder'
			exception.method = "city_state_country( self, city: str, state: str, country: str ) -> Dict[ str, Any ] | None"
			raise exception
	
	def batch_freeform( self, addresses: List[ str ], country: str = 'US' ) -> List[
		Dict[ str, Any ] ]:
		"""

			Purpose:
				Geocode a list of free-form addresses while preserving row-level
				success and failure status.

			Args:
				addresses (List[str]):
					Address strings to geocode.
				country (str):
					ISO-3166 alpha-2 country code used as a default country bias.

			Returns:
				List[Dict[str, Any]]:
					List of flattened geocode results. Failed rows include
					geocode_status='error' and geocode_error.

		"""
		try:
			throw_if( 'addresses', addresses )
			if not isinstance( addresses, list ):
				raise ValueError( 'addresses must be a list of strings.' )
			results: List[ Dict[ str, Any ] ] = [ ]
			for address in addresses:
				value = str( address or '' ).strip( )
				if not value:
					results.append( { 'formatted_address': None, 'lat': None, 'lng': None,
						'place_id': None, 'types': None, 'country_code': None, 'country_name': None,
						'admin_level_1': None, 'admin_level_2': None, 'locality': None,
						'postal_code': None, 'source': 'geocode', 'query': value,
						'geocode_status': 'skipped_empty', 'geocode_error': None } )
					continue
				try:
					item = self.freeform( value, country=country ) or { }
					item[ 'geocode_status' ] = 'ok'
					item[ 'geocode_error' ] = None
					results.append( item )
				except Exception as row_error:
					results.append( { 'formatted_address': None, 'lat': None, 'lng': None,
						'place_id': None, 'types': None, 'country_code': None, 'country_name': None,
						'admin_level_1': None, 'admin_level_2': None, 'locality': None,
						'postal_code': None, 'source': 'geocode', 'query': value,
						'geocode_status': 'error', 'geocode_error': str( row_error ) } )
			return results
		except Exception as e:
			exception = Error( e )
			exception.module = 'mapping'
			exception.cause = 'Geocoder'
			exception.method = (
				"batch_freeform( self, addresses: List[ str ], country: str='US' ) -> List[ Dict[ str, "
				"Any ] ]:")
			raise exception

class DistanceMatrix( ):
	"""
	Google distance matrix client.

	Purpose:
		Calculates distance and duration matrices and presents route comparisons.

	Attributes:
		_maps (Map): Google Maps gateway used for distance requests.
		modes (List[ str ]): Supported Google travel modes.
		data (Dict[ str, Any ] | None): Most recent raw matrix response.
		rows (List[ Dict[ str, Any ] ] | None): Most recent flattened matrix results.
		origins (List[AddressOrCoord] | None): Normalized origins for the last request.
		destinations (List[AddressOrCoord] | None): Normalized destinations for the last request.
		mode (str | None): Travel mode for the last matrix request.
		departure_time (str | None): Last requested departure-time value.
		params (Dict[str, str] | None): Query sent to the Google Distance Matrix API.
	"""
	_maps: Map
	modes: List[ str ]
	data: Dict[ str, Any ] | None
	rows: List[ Dict[ str, Any ] ] | None
	origins: List[ AddressOrCoord ] | None
	destinations: List[ AddressOrCoord ] | None
	mode: str | None
	departure_time: str | None
	params: Dict[ str, str ] | None
	
	def __init__( self, maps: Map ) -> None:
		"""Initialize supported travel modes and response state.

		Purpose:
			Initialize supported travel modes and response state.

		Args:
			maps (Map): Initialized Google Maps API gateway.

		Returns:
			None: Initializes instance state.
		"""
		self._maps = maps
		self.modes = [ 'driving', 'walking', 'bicycling', 'transit' ]
		self.data = None
		self.rows = None
		self.origins = None
		self.destinations = None
		self.mode = None
		self.departure_time = None
		self.params = None
	
	def normalize_mode( self, mode: str ) -> str:
		"""

			Purpose:
				Validate and normalize a Google Distance Matrix travel mode.

			Args:
				mode (str): Travel mode: driving, walking, bicycling, or transit.

			Returns:
				str: Normalized travel mode.

		"""
		try:
			throw_if( 'mode', mode )
			if not isinstance( mode, str ):
				raise TypeError( 'mode must be a string.' )
			value = mode.strip( ).lower( )
			if value not in self.modes:
				raise ValueError( f'Unsupported travel mode "{mode}". Use one of: {self.modes}.' )
			return value
		except Exception as e:
			exception = Error( e )
			exception.module = 'mapping'
			exception.cause = 'DistanceMatrix'
			exception.method = "normalize_mode( self, mode: str ) -> str"
			Logger( ).write( exception )
			raise exception from e
	
	def normalize_inputs( self,
		values: List[ AddressOrCoord ] | Tuple[ AddressOrCoord, ... ] | AddressOrCoord ) -> List[
		AddressOrCoord ]:
		"""

			Purpose:
				Normalize one or many origins/destinations into a list.

			Args:
				values (List[AddressOrCoord] | AddressOrCoord): Single address/coordinate or a list/tuple of them.

			Returns:
				List[AddressOrCoord]: Normalized input list.

		"""
		try:
			throw_if( 'values', values )
			if isinstance( values, list ):
				locations = values
			elif isinstance( values, tuple ):
				if len( values ) == 2 and all( type( x ) in (int, float) for x in values ):
					locations = [ values ]
				else:
					locations = list( values )
			else:
				locations = [ values ]
			throw_if( 'locations', locations )
			for location in locations:
				fmt( location )
			return locations
		except Exception as e:
			exception = Error( e )
			exception.module = 'mapping'
			exception.cause = 'DistanceMatrix'
			exception.method = "normalize_inputs( self, values: List[ AddressOrCoord ] | Tuple[ AddressOrCoord, ... ] | AddressOrCoord ) -> List[ AddressOrCoord ]"
			Logger( ).write( exception )
			raise exception from e
	
	def convert_distance( self, meters: int | float | None ) -> Dict[ str, float | None ]:
		"""

			Purpose:
				Convert meters into kilometers and miles.

			Args:
				meters (int | float | None): Distance in meters.

			Returns:
				Dict[str, float | None]: Distance conversions.

		"""
		try:
			if meters is None:
				return { 'distance_km': None, 'distance_miles': None }
			if (type( meters ) not in (int, float) or not math.isfinite( meters ) or meters < 0):
				raise ValueError( 'meters must be a finite, nonnegative number.' )
			return { 'distance_km': round( meters / 1000.0, 3 ),
				'distance_miles': round( meters / 1609.344, 3 ) }
		except Exception as e:
			exception = Error( e )
			exception.module = 'mapping'
			exception.cause = 'DistanceMatrix'
			exception.method = "convert_distance( self, meters: int | float | None ) -> Dict[ str, float | None ]"
			Logger( ).write( exception )
			raise exception from e
	
	def convert_duration( self, seconds: int | float | None ) -> Dict[ str, float | None ]:
		"""

			Purpose:
				Convert seconds into minutes and hours.

			Args:
				seconds (int | float | None): Duration in seconds.

			Returns:
				Dict[str, float | None]: Duration conversions.

		"""
		try:
			if seconds is None:
				return { 'duration_minutes': None, 'duration_hours': None }
			if (type( seconds ) not in (int, float) or not math.isfinite( seconds ) or seconds < 0):
				raise ValueError( 'seconds must be a finite, nonnegative number.' )
			return { 'duration_minutes': round( seconds / 60.0, 2 ),
				'duration_hours': round( seconds / 3600.0, 3 ) }
		except Exception as e:
			exception = Error( e )
			exception.module = 'mapping'
			exception.cause = 'DistanceMatrix'
			exception.method = "convert_duration( self, seconds: int | float | None ) -> Dict[ str, float | None ]"
			Logger( ).write( exception )
			raise exception from e
	
	def flatten_element( self, origin: str, destination: str, mode: str,
		element: Dict[ str, Any ] ) -> Dict[ str, Any ]:
		"""

			Purpose:
				Flatten one Distance Matrix element into a row-friendly dictionary.

			Args:
				origin (str): Resolved origin label from the API.
				destination (str): Resolved destination label from the API.
				mode (str): Travel mode used for the request.
				element (Dict[str, Any]): One Distance Matrix element.

			Returns:
				Dict[str, Any]: Flattened route row.

		"""
		try:
			throw_if( 'element', element )
			throw_if( 'origin', origin )
			throw_if( 'destination', destination )
			throw_if( 'mode', mode )
			if not isinstance( element, dict ):
				raise TypeError( 'element must be a dictionary.' )
			distance = element.get( 'distance' ) or { }
			duration = element.get( 'duration' ) or { }
			duration_traffic = element.get( 'duration_in_traffic' ) or { }
			distance_meters = distance.get( 'value' )
			duration_seconds = duration.get( 'value' )
			traffic_seconds = duration_traffic.get( 'value' )
			row = { 'origin': origin, 'destination': destination, 'mode': mode,
				'status': element.get( 'status' ), 'distance_text': distance.get( 'text' ),
				'distance_meters': distance_meters, 'duration_text': duration.get( 'text' ),
				'duration_seconds': duration_seconds,
				'duration_in_traffic_text': duration_traffic.get( 'text' ),
				'duration_in_traffic_seconds': traffic_seconds }
			row.update( self.convert_distance( distance_meters ) )
			row.update( self.convert_duration( duration_seconds ) )
			if traffic_seconds is None:
				row[ 'duration_in_traffic_minutes' ] = None
				row[ 'duration_in_traffic_hours' ] = None
			else:
				traffic_duration = self.convert_duration( traffic_seconds )
				row[ 'duration_in_traffic_minutes' ] = traffic_duration[ 'duration_minutes' ]
				row[ 'duration_in_traffic_hours' ] = traffic_duration[ 'duration_hours' ]
			return row
		except Exception as e:
			exception = Error( e )
			exception.module = 'mapping'
			exception.cause = 'DistanceMatrix'
			exception.method = (
				"flatten_element( self, origin: str, destination: str, mode: str, element: Dict[ str, "
				"Any ] ) -> Dict[ str, Any ]:")
			Logger( ).write( exception )
			raise exception from e
	
	def matrix( self,
		origins: List[ AddressOrCoord ] | Tuple[ AddressOrCoord, ... ] | AddressOrCoord,
		destinations: List[ AddressOrCoord ] | Tuple[ AddressOrCoord, ... ] | AddressOrCoord,
		mode: str = 'driving', departure_time: str = '' ) -> List[ Dict[ str, Any ] ]:
		"""

			Purpose:
				Execute a Distance Matrix request for one or more origins and one
				or more destinations.

			Args:
				origins (List[AddressOrCoord] | AddressOrCoord): Origins.
				destinations (List[AddressOrCoord] | AddressOrCoord): Destinations.
				mode (str): Travel mode: driving, walking, bicycling, or transit.
				departure_time (str): Optional departure time. Use 'now' for traffic-aware driving.

			Returns:
				List[Dict[str, Any]]: Flattened route rows.

		"""
		try:
			throw_if( 'origins', origins )
			throw_if( 'destinations', destinations )
			if not isinstance( departure_time, str ):
				raise TypeError( 'departure_time must be a string.' )
			travel_mode = self.normalize_mode( mode )
			origin_values = self.normalize_inputs( origins )
			destination_values = self.normalize_inputs( destinations )
			self.origins = origin_values
			self.destinations = destination_values
			self.mode = travel_mode
			self.departure_time = departure_time
			origin_query = '|'.join( fmt( value ) for value in origin_values )
			destination_query = '|'.join( fmt( value ) for value in destination_values )
			params = { 'origins': origin_query, 'destinations': destination_query,
				'mode': travel_mode }
			if departure_time:
				params[ 'departure_time' ] = departure_time
			self.params = params
			self.data = self._maps.request( 'distancematrix/json', self.params )
			if not isinstance( self.data, dict ):
				raise ValueError( 'Distance Matrix response was not a dictionary.' )
			status = self.data.get( 'status' )
			if status != 'OK':
				raise RuntimeError( f'Google Distance Matrix request failed: {status or "UNKNOWN_STATUS"}. '
				                    f'{self.data.get( "error_message", "" )}' )
			origin_addresses = self.data.get( 'origin_addresses' ) or [ fmt( x ) for x in
				origin_values ]
			destination_addresses = self.data.get( 'destination_addresses' ) or [ fmt( x ) for x in
				destination_values ]
			api_rows = self.data.get( 'rows' )
			if not isinstance( api_rows, list ) or len( api_rows ) != len( origin_values ):
				raise ValueError( 'Distance Matrix response origin count does not match request.' )
			output_rows: List[ Dict[ str, Any ] ] = [ ]
			for origin_index, row in enumerate( api_rows ):
				if not isinstance( row, dict ):
					raise TypeError( 'Distance Matrix response row must be a dictionary.' )
				origin_label = (origin_addresses[
					                origin_index ] if origin_index < len( origin_addresses ) else fmt(
					origin_values[ origin_index ] ))
				elements = row.get( 'elements' )
				if not isinstance( elements, list ) or len( elements ) != len( destination_values ):
					raise ValueError( 'Distance Matrix response destination count does not match request.' )
				for destination_index, element in enumerate( elements ):
					destination_label = (destination_addresses[
						destination_index ] if destination_index < len( destination_addresses ) else fmt(
						destination_values[ destination_index ] ))
					output_rows.append( self.flatten_element( origin=origin_label, destination=destination_label, mode=travel_mode, element=element ) )
			self.rows = output_rows
			return output_rows
		except Exception as e:
			exception = Error( e )
			exception.module = 'mapping'
			exception.cause = 'DistanceMatrix'
			exception.method = (
				"matrix( self, origins: List[ AddressOrCoord ] | Tuple[ AddressOrCoord, ... ] | "
				"AddressOrCoord, destinations: List[ AddressOrCoord ] | Tuple[ AddressOrCoord, ... ] | "
				"AddressOrCoord, mode: str='driving', departure_time: str='' ) -> List[ Dict[ str, Any "
				"] ]:")
			Logger( ).write( exception )
			raise exception from e
	
	def summary( self, origin: AddressOrCoord, destination: AddressOrCoord,
		mode: str = 'driving' ) -> Dict:
		"""

			Purpose:
				Return a compact dict with meters/seconds and human text fields
				for one origin, one destination, and one travel mode.

			Args:
				origin (AddressOrCoord): Origin address string or (lat, lng) tuple.
				destination (AddressOrCoord): Destination address string or (lat, lng) tuple.
				mode (str): Travel mode: driving, walking, bicycling, transit.

			Returns:
				Dict: Distance and duration summary.

		"""
		try:
			throw_if( 'origin', origin )
			throw_if( 'destination', destination )
			rows = self.matrix( origins=origin, destinations=destination, mode=mode )
			if not rows:
				return { 'distance_text': None, 'distance_meters': None, 'duration_text': None,
					'duration_seconds': None, 'status': 'NO_RESULTS' }
			row = rows[ 0 ]
			return { 'distance_text': row.get( 'distance_text' ),
				'distance_meters': row.get( 'distance_meters' ),
				'distance_km': row.get( 'distance_km' ),
				'distance_miles': row.get( 'distance_miles' ),
				'duration_text': row.get( 'duration_text' ),
				'duration_seconds': row.get( 'duration_seconds' ),
				'duration_minutes': row.get( 'duration_minutes' ),
				'duration_hours': row.get( 'duration_hours' ),
				'duration_in_traffic_text': row.get( 'duration_in_traffic_text' ),
				'duration_in_traffic_seconds': row.get( 'duration_in_traffic_seconds' ),
				'duration_in_traffic_minutes': row.get( 'duration_in_traffic_minutes' ),
				'origin': row.get( 'origin' ), 'destination': row.get( 'destination' ),
				'mode': row.get( 'mode' ), 'status': row.get( 'status' ) }
		except Exception as e:
			exception = Error( e )
			exception.module = 'mapping'
			exception.cause = 'DistanceMatrix'
			exception.method = "summary( self, origin: AddressOrCoord, destination: AddressOrCoord, mode: str = 'driving' ) -> Dict"
			Logger( ).write( exception )
			raise exception from e
	
	def compare_modes( self, origin: AddressOrCoord, destination: AddressOrCoord,
		modes: List[ str ] | None = None, departure_time: str = '' ) -> List[ Dict[ str, Any ] ]:
		"""

			Purpose:
				Compare route distance and duration across multiple travel modes.

			Args:
				origin (AddressOrCoord): Origin address string or coordinate tuple.
				destination (AddressOrCoord): Destination address string or coordinate tuple.
				modes (List[str] | None): Optional travel modes. Defaults to all supported modes.
				departure_time (str): Optional departure time. Use 'now' for traffic-aware driving.

			Returns:
				List[Dict[str, Any]]: One flattened route summary per travel mode.

		"""
		try:
			throw_if( 'origin', origin )
			throw_if( 'destination', destination )
			if modes is not None:
				throw_if( 'modes', modes )
				if not isinstance( modes, list ):
					raise TypeError( 'modes must be a list of travel modes.' )
			selected_modes = self.modes if modes is None else modes
			results: List[ Dict[ str, Any ] ] = [ ]
			for mode in selected_modes:
				active_mode = self.normalize_mode( mode )
				active_departure = departure_time if active_mode == 'driving' else ''
				rows = self.matrix( origins=origin, destinations=destination, mode=active_mode, departure_time=active_departure )
				if rows:
					results.append( rows[ 0 ] )
			return results
		except Exception as e:
			exception = Error( e )
			exception.module = 'mapping'
			exception.cause = 'DistanceMatrix'
			exception.method = "compare_modes( self, **args )"
			Logger( ).write( exception )
			raise exception from e
	
	def to_dataframe( self, rows: List[ Dict[ str, Any ] ] | None = None ) -> pd.DataFrame:
		"""

			Purpose:
				Convert route rows into a pandas DataFrame for Streamlit display,
				export, or downstream analytics.

			Args:
				rows (List[Dict[str, Any]] | None):
					Optional rows. Defaults to the most recent matrix rows.

			Returns:
				pd.DataFrame:
					Route results as a DataFrame.

		"""
		try:
			active_rows = rows if rows is not None else self.rows
			if not active_rows:
				return pd.DataFrame( )
			return pd.DataFrame( active_rows )
		except Exception as e:
			exception = Error( e )
			exception.module = 'mapping'
			exception.cause = 'DistanceMatrix'
			exception.method = "to_dataframe( self, rows: List[ Dict[ str, Any ] ] | None = None ) -> pd.DataFrame"
			Logger( ).write( exception )
			raise exception

class Place( ):
	"""
	Google Places lookup client.

	Purpose:
		Resolves place details and text queries into canonical location records.

	Attributes:
		maps (Optional[ Map ]): Google Maps gateway used for Places requests.
		cache (Optional[ BaseCache ]): Optional response cache.
		country (Optional[ str ]): Current search region bias.
		query (Optional[ str ]): Current place search query.
		hit (Optional[ Dict[ str, Any ] ]): Most recent cache hit.
		params (Optional[ Dict[ str, str ] ]): Current API query parameters.
		request (Optional[ Dict[ str, str ] ]): Last request payload or query.
		search (Optional[ Dict ]): Most recent search response.
		results (Optional[ List ]): Most recent candidate locations.
		details (Optional[ Dict ]): Most recently retrieved place details.
		geometry (Optional[ Dict ]): Location geometry from a place response.
		key (Optional[ str ]): Cache key for the current lookup.
		output (Optional[ Dict ]): Most recent normalized location result.
		prefix (Optional[str]): Current cache-key namespace.
		parts (Optional[Tuple]): Components used to construct the current cache key.
		place_id (Optional[str]): Current Google Places identifier.
	"""
	maps: Optional[ Map ]
	cache: Optional[ BaseCache ]
	country: Optional[ str ]
	query: Optional[ str ]
	hit: Optional[ Dict[ str, Any ] ]
	params: Optional[ Dict[ str, str ] ]
	request: Optional[ Dict[ str, str ] ]
	search: Optional[ Dict ]
	results: Optional[ List ]
	details: Optional[ Dict ]
	geometry: Optional[ Dict ]
	key: Optional[ str ]
	output: Optional[ Dict ]
	prefix: Optional[ str ]
	parts: Optional[ Tuple ]
	place_id: Optional[ str ]
	
	def __init__( self, maps: Map, cache: Optional[ BaseCache ] = None ) -> None:
		"""

			Purpose:
				Initializes Place objects given a map and optional cache

			Args:
				maps (Maps): Maps gateway instance.
				cache (Optional[BaseCache]): Optional cache for query results.

			Returns:
				Places instance with text search and place-details helpers.

		"""
		self.maps = maps
		self.cache = cache
		self.country = None
		self.query = None
		self.hit = None
		self.params = None
		self.request = None
		self.search = None
		self.results = None
		self.details = None
		self.geometry = None
		self.key = None
		self.output = None
		self.prefix = None
		self.parts = None
		self.place_id = None
	
	def key_for( self, prefix: str, parts: List[ str ] ) -> str | None:
		"""

			Purpose:
				Create a stable cache key from a namespace prefix and one or more
				string parts.

			Args:
				prefix (str):
					Cache namespace or operation prefix.
				parts (List[str]):
					Values that uniquely identify the request.

			Returns:
				str | None:
					Normalized cache key.

		"""
		try:
			throw_if( 'prefix', prefix )
			throw_if( 'parts', parts )
			if not isinstance( prefix, str ) or not isinstance( parts, list ) or any(
					not isinstance( part, str ) for part in parts ):
				raise TypeError( 'prefix must be a string and parts a list of strings.' )
			self.prefix = prefix
			self.parts = parts
			joined = ' '.join( str( p ).strip( ) for p in parts if p and str( p ).strip( ) )
			return f'{self.prefix}::{joined}'
		except Exception as e:
			exception = Error( e )
			exception.module = 'mapping'
			exception.cause = 'Places'
			exception.method = "key_for( self, prefix: str, parts: List[ str ] ) -> str | None"
			raise exception
	
	def component_value( self, components: List[ Dict[ str, Any ] ], kind: str,
		want_long: bool = False ) -> Optional[ str ]:
		"""

			Purpose:
				Extract a single address component value from a Google Places or
				Geocoding address_components collection.

			Args:
				components (List[Dict[str, Any]]): Google address component dictionaries.
				kind (str): Component type to extract, such as country or locality.
				want_long (bool): When True, return long_name instead of short_name.

			Returns:
				Optional[str]: Component value when present; otherwise None.

		"""
		try:
			throw_if( 'components', components )
			throw_if( 'kind', kind )
			for component in components or [ ]:
				if kind in (component.get( 'types' ) or [ ]):
					if want_long:
						return component.get( 'long_name' ) or None
					return component.get( 'short_name' ) or None
			return None
		except Exception as e:
			exception = Error( e )
			exception.module = 'mapping'
			exception.cause = 'Places'
			exception.method = "component_value( self, components: List[ Dict[ str, Any ] ], kind: str, want_long: bool=False ) -> Optional[ str ]"
			raise exception
	
	def flatten_place_details( self, details: Dict[ str, Any ], query: str = '' ) -> Dict[
		str, Any ]:
		"""

			Purpose:
				Convert a Place Details result into the same flattened output shape
				used by Geocoder.flatten_geocode(...).

			Args:
				details (Dict[str, Any]): Google Place Details result dictionary.
				query (str): Original query text, when available.

			Returns:
				Dict[str, Any]: Canonical location dictionary.

		"""
		try:
			throw_if( 'details', details )
			geometry = (details.get( 'geometry' ) or { }).get( 'location' ) or { }
			components = details.get( 'address_components', [ ] ) or [ ]
			return { 'formatted_address': details.get( 'formatted_address' ),
				'lat': geometry.get( 'lat' ), 'lng': geometry.get( 'lng' ),
				'place_id': details.get( 'place_id' ),
				'types': ','.join( details.get( 'types', [ ] ) ) if details.get( 'types' ) else None,
				'country_code': self.component_value( components, 'country' ),
				'country_name': self.component_value( components, 'country', want_long=True ),
				'admin_level_1': self.component_value( components, 'administrative_area_level_1' ),
				'admin_level_2': self.component_value( components, 'administrative_area_level_2' ),
				'locality': (
						self.component_value( components, 'locality' ) or self.component_value( components, 'postal_town' )),
				'postal_code': self.component_value( components, 'postal_code' ),
				'name': details.get( 'name' ), 'business_status': details.get( 'business_status' ),
				'rating': details.get( 'rating' ),
				'user_ratings_total': details.get( 'user_ratings_total' ),
				'website': details.get( 'website' ),
				'formatted_phone_number': details.get( 'formatted_phone_number' ),
				'source': 'places', 'query': query }
		except Exception as e:
			exception = Error( e )
			exception.module = 'mapping'
			exception.cause = 'Places'
			exception.method = "flatten_place_details( self, details: Dict[ str, Any ], query: str = '' ) -> Dict[ str, Any ]"
			raise exception
	
	def place_details( self, place_id: str ) -> Dict[ str, Any ] | None:
		"""

			Purpose:
				Fetch and flatten details for a known Google place_id.

			Args:
				place_id (str): Google Places place identifier.

			Returns:
				Dict[str, Any] | None: Canonical flattened place details.

		"""
		try:
			throw_if( 'place_id', place_id )
			self.place_id = place_id
			self.key = self.key_for( 'place_details', [ self.place_id ] )
			if self.cache:
				self.hit = self.cache.get( self.key )
				if self.hit:
					return self.hit
			fields = ('formatted_address, geometry, address_component, place_id,type,'
			          'name, business_status, rating, user_ratings_total, website,'
			          'formatted_phone_number')
			self.request = { 'place_id': self.place_id, 'fields': fields }
			self.details = self.maps.request( 'place/details/json', self.request ).get( 'result', { } )
			if not self.details:
				raise NotFound( f'No place details found for "{place_id}" ' )
			self.output = self.flatten_place_details( self.details, query=place_id )
			if self.cache:
				self.cache.set( self.key, self.output )
			return self.output
		except Exception as e:
			exception = Error( e )
			exception.module = 'mapping'
			exception.cause = 'Places'
			exception.method = "place_details( self, place_id: str ) -> Dict[ str, Any ] | None"
			raise exception
	
	def text_to_location( self, query: str, country: str = 'US', latitude: Optional[ float ] = None, longitude: Optional[ float ] = None ) -> Dict[ str, Any ] | None:
		"""

			Purpose:
				Resolve a free-text query into a canonical address and coordinate
				record via Google Places Text Search and Place Details.

			Args:
				query (str):
					Arbitrary human-entered text such as "Newcastle, NSW, AU".
				country (str):
					ISO-2 region bias such as "AU" or "US".
				latitude (Optional[float]): Latitude for optional local search bias.
				longitude (Optional[float]): Longitude for optional local search bias.

			Returns:
				Dict[str, Any] | None:
					Canonical location dictionary compatible with Geocoder output.

			Raises:
				NotFound:
					Raised when no candidate is returned.

		"""
		try:
			throw_if( 'query', query )
			self.query = query.strip( )
			self.country = str( country or '' ).strip( )
			self.latitude = latitude
			self.longitude = longitude
			if (self.latitude is None) != (self.longitude is None):
				raise ValueError( 'Both location-bias coordinates must be supplied.' )
			self.params = { 'query': self.query }
			if self.country:
				self.params[ 'region' ] = self.country.upper( )
			if self.latitude is not None:
				if (isinstance( self.latitude, bool ) or isinstance( self.longitude, bool )
						or not isinstance( self.latitude, (int, float) )
						or not isinstance( self.longitude, (int, float) )
						or not -90 <= self.latitude <= 90
						or not -180 <= self.longitude <= 180):
					raise ValueError( 'Invalid location-bias coordinates.' )
				self.params[ 'location' ] = f'{self.latitude},{self.longitude}'
				self.params[ 'radius' ] = 50000
			self.key = self.key_for( 'places', [ self.query, self.country.upper( ),
				str( self.latitude ), str( self.longitude ) ] )
			if self.cache:
				self.hit = self.cache.get( self.key )
				if self.hit:
					return self.hit
			self.search = self.maps.request( 'place/textsearch/json', self.params )
			self.results = self.search.get( 'results' ) or [ ]
			if not self.results:
				raise NotFound( f'No places match for "{self.query}" ' )
			top = self.results[ 0 ]
			place_id = top.get( 'place_id' )
			if not place_id:
				raise NotFound( 'Top place had no place_id' )
			fields = ('formatted_address,geometry,address_component,place_id,type,'
			          'name,business_status,rating,user_ratings_total,website,'
			          'formatted_phone_number')
			_payload = { 'place_id': place_id, 'fields': fields }
			self.request = _payload
			self.details = self.maps.request( 'place/details/json', self.request ).get( 'result', { } )
			if not self.details:
				raise NotFound( f'No place details found for "{self.query}" ' )
			self.output = self.flatten_place_details( self.details, query=self.query )
			if self.cache:
				self.cache.set( self.key, self.output )
			return self.output
		except Exception as e:
			exception = Error( e )
			exception.module = 'mapping'
			exception.cause = 'Places'
			exception.method = "text_to_location( self, **args ) -> Dict[ str, Any ] | None"
			raise exception
	
	def search_candidates( self, query: str, country: str = 'US', lmt: int = 5 ) -> List[
		Dict[ str, Any ] ]:
		"""

			Purpose:
				Return multiple Places Text Search candidates for a query. This is
				intended for future UI candidate-selection workflows.

			Args:
				query (str): Free-text search query.
				country (str): ISO-2 region bias.
				lmt (int): Maximum candidates to return.

			Returns:
				List[Dict[str, Any]]: Raw candidate dictionaries returned by Text Search.

		"""
		try:
			throw_if( 'query', query )
			self.query = query.strip( )
			self.country = str( country or '' ).strip( )
			self.params = { 'query': self.query }
			if self.country:
				self.params[ 'region' ] = self.country.upper( )
			self.search = self.maps.request( 'place/textsearch/json', self.params )
			self.results = self.search.get( 'results' ) or [ ]
			if not self.results:
				raise NotFound( f'No places match for "{self.query}" ' )
			return self.results[ :max( 1, int( lmt ) ) ]
		except Exception as e:
			exception = Error( e )
			exception.module = 'mapping'
			exception.cause = 'Places'
			exception.method = "search_candidates( self, **args ) -> List[ Dict[ str, Any ] ]"
			raise exception

class Timezone( ):
	"""
	Google time zone client.

	Purpose:
		Retrieves timezone identifiers, UTC offsets, and time-enriched location records.

	Attributes:
		timestamp (Optional[ int ]): Unix timestamp used for timezone lookup.
		maps (Optional[ Map ]): Google Maps gateway used for timezone requests.
		latitude (Optional[ float ]): Current latitude in decimal degrees.
		longitude (Optional[ float ]): Current longitude in decimal degrees.
		data (Optional[ Dict ]): Most recent timezone API payload.
		offset (Optional[ float ]): Computed UTC offset including daylight saving time.
		local (Optional[ str ]): Last computed local datetime representation.
		rows (Optional[ list ]): Input rows for batch enrichment.
		lat_field (Optional[ str ]): Latitude field name for batch enrichment.
		lng_field (Optional[ str ]): Longitude field name for batch enrichment.
		utc_datetime (Optional[ dt.datetime ]): UTC datetime used for local time conversion.
	"""
	timestamp: Optional[ int ]
	maps: Optional[ Map ]
	latitude: Optional[ float ]
	longitude: Optional[ float ]
	data: Optional[ Dict ]
	offset: Optional[ float ]
	local: Optional[ str ]
	rows: Optional[ list ]
	lat_field: Optional[ str ]
	lng_field: Optional[ str ]
	utc_datetime: Optional[ dt.datetime ]
	
	def __init__( self, maps: Map ) -> None:
		"""Initialize timezone lookup state for the supplied Maps gateway.

		Purpose:
			Initialize timezone lookup state for the supplied Maps gateway.

		Args:
			maps (Map): Initialized Google Maps API gateway.

		Returns:
			None: Initializes instance state.
		"""
		self.maps = maps
		self.timestamp = None
		self.latitude = None
		self.longitude = None
		self.data = None
		self.offset = None
		self.local = None
		self.rows = None
		self.lat_field = None
		self.lng_field = None
		self.utc_datetime = None
	
	def validate_coordinates( self, lat: float, lng: float ) -> tuple:
		"""

			Purpose:
				Validate and normalize a latitude and longitude pair.

			Args:
				lat (float):
					Latitude in decimal degrees.

				lng (float):
					Longitude in decimal degrees.

			Returns:
				tuple:
					Validated latitude and longitude.

		"""
		try:
			throw_if( 'lat', lat )
			throw_if( 'lng', lng )
			if (type( lat ) not in (int, float) or type( lng ) not in (int,
				float) or not math.isfinite( lat ) or not math.isfinite( lng )):
				raise ValueError( 'Coordinates must be finite numeric values.' )
			latitude = lat
			longitude = lng
			if latitude < -90.0 or latitude > 90.0:
				raise ValueError( 'Latitude must be between -90 and 90.' )
			if longitude < -180.0 or longitude > 180.0:
				raise ValueError( 'Longitude must be between -180 and 180.' )
			self.latitude = latitude
			self.longitude = longitude
			return self.latitude, self.longitude
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'mapping'
			exception.cause = 'Timezone'
			exception.method = "validate_coordinates( self, lat: float, lng: float ) -> tuple"
			raise exception
	
	def lookup( self, lat: float, lng: float ) -> Dict | None:
		"""

			Purpose:
				Fetch the full Google Time Zone API response for a coordinate.

			Args:
				lat (float):
					Latitude.

				lng (float):
					Longitude.

			Returns:
				Dict | None:
					Full time zone response payload, including timeZoneId, timeZoneName,
					rawOffset, dstOffset, and status when available.

		"""
		try:
			throw_if( 'lat', lat )
			throw_if( 'lng', lng )
			latitude, longitude = self.validate_coordinates( lat, lng )
			timestamp_value = int( time.time( ) )
			self.latitude = latitude
			self.longitude = longitude
			self.timestamp = timestamp_value
			self.data = self.maps.request( 'timezone/json', {
				'location': f'{self.latitude},{self.longitude}',
				'timestamp': str( self.timestamp ) } )
			return self.data
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'mapping'
			exception.cause = 'Timezone'
			exception.method = "lookup( self, lat: float, lng: float ) -> Dict | None"
			raise exception
	
	def get_id( self, lat: float, lng: float ) -> Optional[ str ]:
		"""

			Purpose:
				Fetch the IANA time zone id for a coordinate.

			Args:
				lat (float):
					Latitude.

				lng (float):
					Longitude.

			Returns:
				Optional[str]:
					Time zone id string or None if unavailable.

		"""
		try:
			throw_if( 'lat', lat )
			throw_if( 'lng', lng )
			self.data = self.lookup( lat, lng )
			if not isinstance( self.data, dict ):
				return None
			return self.data.get( 'timeZoneId' )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'mapping'
			exception.cause = 'Timezone'
			exception.method = "get_id( self, lat: float, lng: float ) -> Optional[ str ]"
			raise exception
	
	def offset_hours( self, lat: float, lng: float ) -> Optional[ float ]:
		"""

			Purpose:
				Fetch the total UTC offset in hours for a coordinate.

			Args:
				lat (float):
					Latitude.

				lng (float):
					Longitude.

			Returns:
				Optional[float]:
					Total UTC offset in hours, including daylight-saving offset
					when returned by the API.

		"""
		try:
			throw_if( 'lat', lat )
			throw_if( 'lng', lng )
			self.data = self.lookup( lat, lng )
			if not isinstance( self.data, dict ):
				return None
			raw_offset = self.data.get( 'rawOffset', 0 ) or 0
			dst_offset = self.data.get( 'dstOffset', 0 ) or 0
			offset_value = round( (float( raw_offset ) + float( dst_offset )) / 3600.0, 3 )
			self.offset = offset_value
			return self.offset
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'mapping'
			exception.cause = 'Timezone'
			exception.method = "offset_hours( self, lat: float, lng: float ) -> Optional[ float ]"
			raise exception
	
	def local_time( self, lat: float, lng: float,
		utc_datetime: Optional[ dt.datetime ] = None ) -> Dict | None:
		"""

			Purpose:
				Convert a UTC datetime into local time at a coordinate using the
				Google Time Zone API rawOffset and dstOffset fields.

			Args:
				lat (float):
					Latitude.

				lng (float):
					Longitude.

				utc_datetime (Optional[dt.datetime]):
					Optional UTC datetime. If None, the current UTC time is used.

			Returns:
				Dict | None:
					Dictionary containing timezone metadata, UTC time, local time,
					and total offset hours.

		"""
		try:
			throw_if( 'lat', lat )
			throw_if( 'lng', lng )
			self.data = self.lookup( lat, lng )
			if not isinstance( self.data, dict ):
				return None
			if utc_datetime is None:
				utc_value = dt.datetime.now( dt.timezone.utc )
			else:
				utc_value = utc_datetime
				if utc_value.tzinfo is None:
					utc_value = utc_value.replace( tzinfo=dt.timezone.utc )
				else:
					utc_value = utc_value.astimezone( dt.timezone.utc )
			raw_offset = self.data.get( 'rawOffset', 0 ) or 0
			dst_offset = self.data.get( 'dstOffset', 0 ) or 0
			total_seconds = float( raw_offset ) + float( dst_offset )
			local_value = utc_value + dt.timedelta( seconds=total_seconds )
			offset_value = round( total_seconds / 3600.0, 3 )
			self.utc_datetime = utc_value
			self.offset = offset_value
			self.local = local_value.isoformat( )
			return { 'timeZoneId': self.data.get( 'timeZoneId' ),
				'timeZoneName': self.data.get( 'timeZoneName' ),
				'status': self.data.get( 'status' ), 'rawOffset': raw_offset,
				'dstOffset': dst_offset, 'offset_hours': self.offset,
				'utc_time': self.utc_datetime.isoformat( ), 'local_time': self.local,
				'lat': self.latitude, 'lng': self.longitude }
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'mapping'
			exception.cause = 'Timezone'
			exception.method = ('local_time( self, **args)')
			raise exception
	
	def batch_lookup( self, rows: list, lat_field: str = 'lat', lng_field: str = 'lng' ) -> list:
		"""

			Purpose:
				Enrich a list of row dictionaries with Google Time Zone API fields.

			Args:
				rows (list):
					List of dictionaries containing latitude and longitude fields.

				lat_field (str):
					Latitude field name.

				lng_field (str):
					Longitude field name.

			Returns:
				list:
					List of copied row dictionaries with timezone fields appended.

		"""
		try:
			throw_if( 'rows', rows )
			if not isinstance( rows, list ):
				raise ValueError( 'rows must be a list of dictionaries.' )
			lat_field_value = lat_field or 'lat'
			lng_field_value = lng_field or 'lng'
			self.rows = rows
			self.lat_field = lat_field_value
			self.lng_field = lng_field_value
			output = [ ]
			for row in self.rows:
				item = dict( row or { } )
				try:
					lat_value = item.get( self.lat_field )
					lng_value = item.get( self.lng_field )
					data = self.lookup( lat_value, lng_value )
					if not isinstance( data, dict ):
						item[ 'timeZoneId' ] = None
						item[ 'timeZoneName' ] = None
						item[ 'rawOffset' ] = None
						item[ 'dstOffset' ] = None
						item[ 'offset_hours' ] = None
						item[ 'timezone_status' ] = 'not_found'
						item[ 'timezone_error' ] = 'No timezone response returned.'
					
					else:
						raw_offset = data.get( 'rawOffset', 0 ) or 0
						dst_offset = data.get( 'dstOffset', 0 ) or 0
						offset_value = round((float( raw_offset ) + float( dst_offset ))/3600.0, 3)
						self.offset = offset_value
						item[ 'timeZoneId' ] = data.get( 'timeZoneId' )
						item[ 'timeZoneName' ] = data.get( 'timeZoneName' )
						item[ 'rawOffset' ] = raw_offset
						item[ 'dstOffset' ] = dst_offset
						item[ 'offset_hours' ] = self.offset
						item[ 'timezone_status' ] = data.get( 'status', 'OK' )
						item[ 'timezone_error' ] = None
				
				except Exception as row_error:
					item[ 'timeZoneId' ] = None
					item[ 'timeZoneName' ] = None
					item[ 'rawOffset' ] = None
					item[ 'dstOffset' ] = None
					item[ 'offset_hours' ] = None
					item[ 'timezone_status' ] = 'error'
					item[ 'timezone_error' ] = str( row_error )
				output.append( item )
			return output
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'mapping'
			exception.cause = 'Timezone'
			exception.method = "batch_lookup( self, **args ) -> list"
			raise exception

# ------- Static Maps

class StaticMap( ):
	"""
	Google Static Maps URL builder.

	Purpose:
		Builds static map URLs for markers, paths, and geographic bounding boxes.

	Attributes:
		api_key (Optional[ str ]): Google Maps credential attached to static URLs.
		zoom (Optional[ int ]): Zoom level for the current static map.
		size (Optional[ str ]): Map image dimensions in pixels.
		latitude (Optional[ float ]): Latitude of the current marker.
		longitude (Optional[ float ]): Longitude of the current marker.
		params (Optional[ Dict ]): Current Static Maps query parameters.
		markers (Optional[ str ]): Encoded marker coordinates.
		base_url (Optional[ str ]): Static Maps HTTP endpoint.
		points (Optional[ list ]): Coordinates used for markers or path geometry.
		maptype (Optional[ str ]): Selected static map layer type.
		color (Optional[ str ]): Marker or path color.
		weight (Optional[ int ]): Path line weight.
		west (Optional[ float ]): Western bounding longitude.
		south (Optional[ float ]): Southern bounding latitude.
		east (Optional[ float ]): Eastern bounding longitude.
		north (Optional[ float ]): Northern bounding latitude.
	"""
	api_key: Optional[ str ]
	zoom: Optional[ int ]
	size: Optional[ str ]
	latitude: Optional[ float ]
	longitude: Optional[ float ]
	params: Optional[ Dict ]
	markers: Optional[ str ]
	base_url: Optional[ str ]
	points: Optional[ list ]
	maptype: Optional[ str ]
	color: Optional[ str ]
	weight: Optional[ int ]
	west: Optional[ float ]
	south: Optional[ float ]
	east: Optional[ float ]
	north: Optional[ float ]
	
	def __init__( self ) -> None:
		"""Initialize Google Static Maps URL configuration and output state.

		Purpose:
			Initialize Google Static Maps URL configuration and output state.

		Returns:
			None: Initializes instance state.
		"""
		self.api_key = cfg.GOOGLEMAPS_API_KEY
		self.zoom = None
		self.size = None
		self.latitude = None
		self.longitude = None
		self.params = None
		self.markers = None
		self.base_url = 'https://maps.googleapis.com/maps/api/staticmap'
		self.points = None
		self.maptype = None
		self.color = None
		self.weight = None
		self.west = None
		self.south = None
		self.east = None
		self.north = None
	
	def validate_coordinate( self, lat: float, lng: float ) -> tuple:
		"""

			Purpose:
				Validate and normalize a latitude and longitude pair.

			Args:
				lat (float):
					Latitude in decimal degrees.

				lng (float):
					Longitude in decimal degrees.

			Returns:
				tuple:
					Validated latitude and longitude.
		"""
		try:
			throw_if( 'lat', lat )
			throw_if( 'lng', lng )
			latitude = float( lat )
			longitude = float( lng )
			if latitude < -90.0 or latitude > 90.0:
				raise ValueError( 'Latitude must be between -90 and 90.' )
			if longitude < -180.0 or longitude > 180.0:
				raise ValueError( 'Longitude must be between -180 and 180.' )
			self.latitude = latitude
			self.longitude = longitude
			return self.latitude, self.longitude
		except Exception as e:
			exception = Error( e )
			exception.module = 'mapping'
			exception.cause = 'StaticMap'
			exception.method = "validate_coordinate( self, lat: float, lng: float ) -> tuple"
			Logger( ).write( exception )
			raise exception
	
	def normalize_points( self, points: list ) -> list:
		"""

			Purpose:
				Normalize coordinate tuples, coordinate lists, or dictionaries with
				lat/lng fields into validated coordinate tuples.

			Args:
				points (list):
					List of coordinates. Supported item shapes include:
					(lat, lng), [lat, lng], {'lat': value, 'lng': value}, and
					{'latitude': value, 'longitude': value}.

			Returns:
				list:
					List of validated coordinate tuples.

		"""
		try:
			throw_if( 'points', points )
			if not isinstance( points, list ):
				raise ValueError( 'points must be a list.' )
			output = [ ]
			for point in points:
				if isinstance( point, dict ):
					lat_value = point.get( 'lat', point.get( 'latitude' ) )
					lng_value = point.get( 'lng', point.get( 'longitude' ) )
					output.append( self.validate_coordinate( lat_value, lng_value ) )
				elif isinstance( point, tuple ) and len( point ) == 2:
					output.append( self.validate_coordinate( point[ 0 ], point[ 1 ] ) )
				elif isinstance( point, list ) and len( point ) == 2:
					output.append( self.validate_coordinate( point[ 0 ], point[ 1 ] ) )
				else:
					raise ValueError( f'Unsupported point format: {point}' )
			if not output:
				raise ValueError( 'At least one coordinate is required.' )
			self.points = output
			return self.points
		except Exception as e:
			exception = Error( e )
			exception.module = 'mapping'
			exception.cause = 'StaticMap'
			exception.method = "normalize_points( self, points: list ) -> list"
			Logger( ).write( exception )
			raise exception
	
	def build_url( self, params: Dict ) -> str | None:
		"""

			Purpose:
				Build a Google Static Maps URL from a parameter dictionary.

			Args:
				params (Dict):
					Google Static Maps query parameters.

			Returns:
				str | None:
					Fully-qualified Google Static Maps URL.

		"""
		try:
			throw_if( 'params', params )
			params_value = dict( params or { } )
			params_value[ 'key' ] = self.api_key
			self.params = params_value
			return f'{self.base_url}?{urlencode( self.params, doseq=True )}'
		except Exception as e:
			exception = Error( e )
			exception.module = 'mapping'
			exception.cause = 'StaticMap'
			exception.method = "build_url( self, params: Dict ) -> str | None"
			Logger( ).write( exception )
			raise exception
	
	def pin( self, lat: float, lng: float, zoom: int = 12, size: str = '400x300',
		scale: int = 1 ) -> str | None:
		"""

			Purpose:
				Build a static map URL centered on a coordinate with a single marker.

			Args:
				lat (float):
					Latitude for the pin.

				lng (float):
					Longitude for the pin.

				zoom (int):
					Zoom level from 1 through 20.

				size (str):
					Image dimensions in WxH format.

				scale (int):
					Google Static Maps image resolution multiplier, 1 or 2.

			Returns:
				str | None:
					Fully-qualified URL string suitable for embedding.

		"""
		try:
			throw_if( 'lat', lat )
			throw_if( 'lng', lng )
			latitude, longitude = self.validate_coordinate( lat, lng )
			zoom_value = max( 1, min( int( zoom or 12 ), 20 ) )
			if type( scale ) is not int or scale not in (1, 2):
				raise ValueError( 'scale must be 1 or 2.' )
			size_value = size or '400x300'
			marker_value = f'{latitude},{longitude}'
			self.latitude = latitude
			self.longitude = longitude
			self.zoom = zoom_value
			self.size = size_value
			self.scale = scale
			self.markers = marker_value
			self.params = { 'center': f'{self.latitude},{self.longitude}', 'zoom': str( self.zoom ),
				'size': self.size, 'scale': self.scale, 'markers': self.markers }
			return self.build_url( self.params )
		except Exception as e:
			exception = Error( e )
			exception.module = 'mapping'
			exception.cause = 'StaticMap'
			exception.method = ("pin( self, lat: float, lng: float, zoom: int=12, "
			                    "size: str='400x300', scale: int=1 ) -> str | None")
			Logger( ).write( exception )
			raise exception
	
	def pins( self, points: list, zoom: int = 0, size: int = '600x400', maptype: int = 'roadmap',
		color: int = 'red' ) -> str | None:
		"""

			Purpose:
				Build a static map URL with multiple markers. If zoom is zero,
				Google is allowed to fit the visible area to the supplied points.

			Args:
				points (list):
					List of coordinate tuples, coordinate lists, or dictionaries
					containing lat/lng fields.

				zoom (int):
					Zoom level. Use zero to omit explicit zoom.

				size (str):
					Image dimensions in WxH format.

				maptype (str):
					Map type: roadmap, satellite, terrain, or hybrid.

				color (str):
					Marker color.

			Returns:
				str | None:
					Fully-qualified URL string suitable for embedding.

		"""
		try:
			throw_if( 'points', points )
			coordinates = self.normalize_points( points )
			zoom_value = int( zoom or 0 )
			size_value = size or '600x400'
			maptype_value = str( maptype or 'roadmap' ).strip( ).lower( )
			color_value = color or 'red'
			if maptype_value not in [ 'roadmap', 'satellite', 'terrain', 'hybrid' ]:
				raise ValueError( 'maptype must be roadmap, satellite, terrain, or hybrid.' )
			self.points = coordinates
			self.zoom = zoom_value
			self.size = size_value
			self.maptype = maptype_value
			self.color = color_value
			marker_values = [ ]
			for lat_value, lng_value in self.points:
				marker_values.append( f'color:{self.color}|{lat_value},{lng_value}' )
			self.params = { 'size': self.size, 'maptype': self.maptype, 'markers': marker_values }
			if self.zoom > 0:
				center_lat = sum( p[ 0 ] for p in self.points ) / len( self.points )
				center_lng = sum( p[ 1 ] for p in self.points ) / len( self.points )
				self.params[ 'center' ] = f'{center_lat},{center_lng}'
				self.params[ 'zoom' ] = str( max( 1, min( self.zoom, 20 ) ) )
			else:
				self.params[ 'visible' ] = [ f'{lat},{lng}' for lat, lng in self.points ]
			return self.build_url( self.params )
		except Exception as e:
			exception = Error( e )
			exception.module = 'mapping'
			exception.cause = 'StaticMapUrl'
			exception.method = (
				"pins( self, points: list, zoom: int=0, size: int='600x400', maptype: int='roadmap', "
				"color: int='red' ) -> str | None:")
			Logger( ).write( exception )
			raise exception
	
	def path( self, points: list, size: int = '600x400', maptype: int = 'roadmap',
		color: int = '0x0000ff', weight: int = 5 ) -> str | None:
		"""

			Purpose:
				Build a static map URL showing a path through two or more points.

			Args:
				points (list):
					List of coordinate tuples, coordinate lists, or dictionaries
					containing lat/lng fields.

				size (str):
					Image dimensions in WxH format.

				maptype (str):
					Map type: roadmap, satellite, terrain, or hybrid.

				color (str):
					Path color.

				weight (int):
					Path stroke weight.

			Returns:
				str | None:
					Fully-qualified URL string suitable for embedding.

		"""
		try:
			throw_if( 'points', points )
			coordinates = self.normalize_points( points )
			size_value = size or '600x400'
			maptype_value = str( maptype or 'roadmap' ).strip( ).lower( )
			color_value = color or '0x0000ff'
			weight_value = max( 1, int( weight or 5 ) )
			if len( coordinates ) < 2:
				raise ValueError( 'At least two coordinates are required for a path.' )
			if maptype_value not in [ 'roadmap', 'satellite', 'terrain', 'hybrid' ]:
				raise ValueError( 'maptype must be roadmap, satellite, terrain, or hybrid.' )
			self.points = coordinates
			self.size = size_value
			self.maptype = maptype_value
			self.color = color_value
			self.weight = weight_value
			path_points = [ f'{lat},{lng}' for lat, lng in self.points ]
			path_parts = [ f'color:{self.color}', f'weight:{self.weight}' ] + path_points
			path_value = '|'.join( path_parts )
			self.params = { 'size': self.size, 'maptype': self.maptype, 'path': path_value,
				'markers': [ f'color:green|{self.points[ 0 ][ 0 ]},{self.points[ 0 ][ 1 ]}',
					f'color:red|{self.points[ -1 ][ 0 ]},{self.points[ -1 ][ 1 ]}' ],
				'visible': path_points }
			return self.build_url( self.params )
		except Exception as e:
			exception = Error( e )
			exception.module = 'mapping'
			exception.cause = 'StaticMap'
			exception.method = "path( self, **args ) -> str | None"
			Logger( ).write( exception )
			raise exception
	
	def bbox( self, west: float, south: float, east: float, north: float, size: int = '600x400',
		maptype: int = 'roadmap' ) -> str | None:
		"""

			Purpose:
				Build a static map URL showing a rectangular bounding box.

			Args:
				west (float):
					Western longitude.

				south (float):
					Southern latitude.

				east (float):
					Eastern longitude.

				north (float):
					Northern latitude.

				size (str):
					Image dimensions in WxH format.

				maptype (str):
					Map type: roadmap, satellite, terrain, or hybrid.

			Returns:
				str | None:
					Fully-qualified URL string suitable for embedding.

		"""
		try:
			throw_if( 'west', west )
			throw_if( 'south', south )
			throw_if( 'east', east )
			throw_if( 'north', north )
			west_value = float( west )
			south_value = float( south )
			east_value = float( east )
			north_value = float( north )
			size_value = size or '600x400'
			maptype_value = maptype or 'roadmap'
			southwest = self.validate_coordinate( south_value, west_value )
			northwest = self.validate_coordinate( north_value, west_value )
			northeast = self.validate_coordinate( north_value, east_value )
			southeast = self.validate_coordinate( south_value, east_value )
			self.west = west_value
			self.south = south_value
			self.east = east_value
			self.north = north_value
			self.size = size_value
			self.maptype = maptype_value
			self.points = [ southwest, northwest, northeast, southeast, southwest ]
			return self.path( points=self.points, size=self.size, maptype=self.maptype,
				color='0xff0000', weight=3 )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'mapping'
			exception.cause = 'StaticMap'
			exception.method = "bbox( self, **args ) -> str | None"
			Logger( ).write( exception )
			raise exception
