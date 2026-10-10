'''
  ******************************************************************************************
      Assembly:                Mappy
      Filename:                places.py
      Author:                  Terry D. Eppler
      Created:                 05-31-2022

      Last Modified By:        Terry D. Eppler
      Last Modified On:        05-01-2025
  ******************************************************************************************
  <copyright file='places.py' company='Terry D. Eppler'>

	     Mappy is a python framework encapsulating the Google Maps functionality.
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
    places.py
  </summary>
  ******************************************************************************************
'''
from typing import Any, Dict, Optional, List
if __package__:
	from .caches import BaseCache
else:
	from caches import BaseCache
if __package__:
	from .exceptions import NotFound
else:
	from exceptions import NotFound
if __package__:
	from .maps import Maps
else:
	from maps import Maps
if __package__:
	from .boogr import Error, Logger
else:
	from boogr import Error, Logger

def throw_if( name: str, value: object ) -> None:
	"""Validate that a required Places value is present.

	Purpose:
		Provides a lightweight guard for required Places inputs before cache-key
		construction, text-search requests, details requests, and output flattening.
		The function rejects missing objects and blank strings so fallback location
		workflows fail before issuing ambiguous external API calls.

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

class Place( ):
	"""Resolve locations with Google Places Text Search and Place Details.

	Purpose:
		Provides a fallback and enrichment layer for locations that are not resolved
		adequately by Geocoding alone. The class uses the shared ``Maps`` gateway and
		optional cache backend to perform Places Text Search, retrieve Place Details,
		extract address components, and return a canonical row shape compatible with
		``Geocoder`` output.

	Attributes:
		map: Optional Google Maps gateway reference retained for compatibility.
		cache: Optional cache backend used for Text Search and Details results.
		country: Region bias from the latest Places lookup.
		query: Free-text query from the latest Text Search operation.
		hit: Cached payload returned by the latest cache lookup.
		params: Query parameters sent to the latest Places Text Search request.
		request: Reserved request-state dictionary retained for compatibility.
		search: Raw Places Text Search response payload.
		results: Candidate list returned by Places Text Search.
		details: Raw Place Details result payload.
		geometry: Geometry dictionary from the latest details payload.
		key: Cache key used by the latest lookup.
		output: Last flattened Places output.
	"""
	map: Optional[ Maps ]
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
	
	def __init__( self, maps: Maps, cache: Optional[ BaseCache ] = None ) -> None:
		"""Initialize the Places service wrapper.

		Purpose:
			Stores the shared Google Maps gateway, optional cache backend, and runtime
			state used by text-search, place-details, candidate-search, and output
			flattening methods. The constructor performs local assignment only and
			prepares the instance for later API-backed lookup operations.

		Args:
			maps: Google Maps gateway used for Places API requests.
			cache: Optional cache backend used to store and retrieve Places results.
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
	
	def key_for( self, prefix: str, *parts: str ) -> str | None:
		"""Build a stable cache key for a Places operation.

		Purpose:
			Combines a namespace prefix and one or more identifying values into the
			cache-key format used by Text Search and Place Details workflows. The
			method prevents collisions between different Places operations while
			preserving a predictable key structure for cache backends.

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
			joined = ' '.join( str( p ).strip( ) for p in parts if p and str( p ).strip( ) )
			return f'{prefix}::{joined}'
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'Place'
			exception.method = 'key_for( self, prefix: str, *parts: str ) -> str | None'
			Logger( ).write( exception )
			raise exception
	
	def component_value( self, components: List[ Dict[ str, Any ] ], kind: str,
			want_long: bool = False ) -> Optional[ str ]:
		"""Extract one address component from a Google component list.

		Purpose:
			Reads Google Places or Geocoding ``address_components`` dictionaries and
			returns the requested short or long component value. The helper centralizes
			component extraction for Places output flattening so country, administrative
			area, locality, and postal-code fields remain consistent with Geocoder
			output.

		Args:
			components: Google address component dictionaries.
			kind: Component type to extract, such as ``country`` or ``locality``.
			want_long: When ``True``, return ``long_name`` instead of ``short_name``.

		Returns:
			Optional[str]: Component value when present; otherwise ``None``.

		Raises:
			Error: Raised after logging when component extraction fails.
		"""
		try:
			for component in components or [ ]:
				if kind in (component.get( 'types' ) or [ ]):
					if want_long:
						return component.get( 'long_name' ) or None
					
					return component.get( 'short_name' ) or None
			
			return None
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'Place'
			exception.method = 'component_value( self, *args ) -> Optional[ str ]'
			Logger( ).write( exception )
			raise exception
	
	def flatten_place_details( self, details: Dict[ str, Any ], query: str = '' ) -> Dict[
		str, Any ]:
		"""Flatten a Google Place Details result into Mappy's canonical shape.

		Purpose:
			Converts a Place Details payload into the same row-oriented output used by
			Geocoder, while adding Places-specific fields such as business status,
			rating, ratings count, website, phone number, and name. The flattened
			result supports Streamlit display, Excel/CSV enrichment, cache storage, and
			interchangeable fallback behavior with geocoding results.

		Args:
			details: Google Place Details result dictionary.
			query: Original user query or place identifier associated with the result.

		Returns:
			Dict[str, Any]: Canonical location dictionary with Places metadata.

		Raises:
			Error: Raised after logging when validation or output flattening fails.
		"""
		try:
			throw_if( 'details', details )
			geometry = (details.get( 'geometry' ) or { }).get( 'location' ) or { }
			components = details.get( 'address_components', [ ] ) or [ ]
			return {
					'formatted_address': details.get( 'formatted_address' ),
					'lat': geometry.get( 'lat' ),
					'lng': geometry.get( 'lng' ),
					'place_id': details.get( 'place_id' ),
					'types': ','.join( details.get( 'types', [ ] ) )
					if details.get( 'types' ) else None,
					'country_code': self.component_value( components, 'country' ),
					'country_name': self.component_value( components, 'country', want_long=True ),
					'admin_level_1': self.component_value( components,
						'administrative_area_level_1' ),
					'admin_level_2': self.component_value( components,
						'administrative_area_level_2' ),
					'locality': (
							self.component_value( components, 'locality' )
							or self.component_value( components, 'postal_town' )
					),
					'postal_code': self.component_value( components, 'postal_code' ),
					'name': details.get( 'name' ),
					'business_status': details.get( 'business_status' ),
					'rating': details.get( 'rating' ),
					'user_ratings_total': details.get( 'user_ratings_total' ),
					'website': details.get( 'website' ),
					'formatted_phone_number': details.get( 'formatted_phone_number' ),
					'source': 'places',
					'query': query
			}
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'Place'
			exception.method = 'flatten_place_details( self, *args ) -> Dict[ str, Any ]'
			Logger( ).write( exception )
			raise exception
	
	def place_details( self, place_id: str ) -> Dict[ str, Any ] | None:
		"""Fetch and flatten details for a known Google Place identifier.

		Purpose:
			Retrieves a Place Details payload for a supplied ``place_id``, checks the
			cache before calling the gateway, stores raw details and flattened output
			on the instance, writes successful results to the cache, and returns the
			canonical Places output shape used by downstream Mappy workflows.

		Args:
			place_id: Google Places place identifier.

		Returns:
			Dict[str, Any] | None: Canonical flattened place details.

		Raises:
			Error: Raised after logging when validation, lookup, gateway handling, or
				result processing fails.
		"""
		try:
			throw_if( 'place_id', place_id )
			self.key = self.key_for( 'place_details', place_id )
			if self.cache:
				self.hit = self.cache.get( self.key )
				if self.hit:
					return self.hit
			
			fields = ('formatted_address,geometry,address_component,place_id,type,'
			          'name,business_status,rating,user_ratings_total,website,'
			          'formatted_phone_number')
			self.details = self.maps.request( 'place/details/json', {
					'place_id': place_id,
					'fields': fields
			} ).get( 'result', { } )
			if not self.details:
				raise NotFound( f'No place details found for "{place_id}" ' )
			self.output = self.flatten_place_details( self.details, query=place_id )
			if self.cache:
				self.cache.set( self.key, self.output )
			return self.output
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'Place'
			exception.method = 'place_details( self, place_id: str ) -> Dict[ str, Any ] | None'
			Logger( ).write( exception )
			raise exception
	
	def text_to_location( self, query: str, country: str = 'US' ) -> Dict[ str, Any ] | None:
		"""Resolve free text into a canonical location record.

		Purpose:
			Uses Places Text Search to find the top candidate for a user-supplied
			location query, retrieves the candidate's Place Details payload, flattens
			the result into Mappy's canonical geospatial row shape, and caches the
			output when a cache backend is configured. This is the primary Places
			fallback path for locations that Geocoder does not resolve adequately.

		Args:
			query: Free-text location query, such as a city, landmark, business, or
				ambiguous place name.
			country: Optional ISO-2 region bias such as ``US`` or ``AU``.

		Returns:
			Dict[str, Any] | None: Canonical location dictionary compatible with
				Geocoder output.

		Raises:
			Error: Raised after logging when validation, search, details lookup, or
				result processing fails.
		"""
		try:
			throw_if( 'query', query )
			self.query = query.strip( )
			self.country = str( country or '' ).strip( )
			self.key = self.key_for( 'places', self.query, self.country.upper( ) )
			if self.cache:
				self.hit = self.cache.get( self.key )
				if self.hit:
					return self.hit
			self.params = { 'query': self.query }
			if self.country:
				self.params[ 'region' ] = self.country.upper( )
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
			self.details = self.maps.request( 'place/details/json', {
					'place_id': place_id,
					'fields': fields
			} ).get( 'result', { } )
			if not self.details:
				raise NotFound( f'No place details found for "{self.query}" ' )
			self.output = self.flatten_place_details( self.details, query=self.query )
			if self.cache:
				self.cache.set( self.key, self.output )
			return self.output
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'Place'
			exception.method = 'text_to_location( self, query: str, country: str=US ) -> Dict[ str, Any ] | None'
			Logger( ).write( exception )
			raise exception
	
	def search_candidates( self, query: str, country: str = 'US', lmt: int = 5 ) -> List[
		Dict[ str, Any ] ]:
		"""Return Places Text Search candidates for a query.

		Purpose:
			Performs a Places Text Search and returns the top raw candidate dictionaries
			for future UI candidate-selection workflows, diagnostics, and manual
			disambiguation. The method stores query, country, parameters, search
			payload, and results on the instance for inspection.

		Args:
			query: Free-text search query.
			country: Optional ISO-2 region bias.
			lmt: Maximum number of candidates to return.

		Returns:
			List[Dict[str, Any]]: Raw candidate dictionaries returned by Text Search.

		Raises:
			Error: Raised after logging when validation, gateway handling, or candidate
				retrieval fails.
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
			exception.module = 'mappy'
			exception.cause = 'Place'
			exception.method = 'search_candidates( self, *args ) -> List[ Dict[ str, Any ] ]'
			Logger( ).write( exception )
			raise exception