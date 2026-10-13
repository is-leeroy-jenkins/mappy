'''
  ******************************************************************************************
      Assembly:                Mappy
      Filename:                distances.py
      Author:                  Terry D. Eppler
      Created:                 05-31-2022

      Last Modified By:        Terry D. Eppler
      Last Modified On:        05-01-2025
  ******************************************************************************************
  <copyright file="distances.py" company="Terry D. Eppler">

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
    distances.py
  </summary>
  ******************************************************************************************
'''
from __future__ import annotations
from typing import Any, Dict, List, Tuple, Union
import pandas as pd
if __package__:
	from .maps import Maps
else:
	from maps import Maps
if __package__:
	from .boogr import Error, Logger
else:
	from boogr import Error, Logger

def throw_if( name: str, value: object ) -> None:
	"""Validate that a required distance-matrix value is present.

	Purpose:
		Provides a lightweight guard for required Distance Matrix inputs before mode
		normalization, origin/destination formatting, gateway request construction,
		and row flattening. The function rejects missing objects and blank strings so
		route workflows fail before issuing ambiguous external API calls.

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

Coord = Tuple[ float, float ]
AddressOrCoord = Union[ str, Coord ]

def fmt( o: AddressOrCoord ) -> str:
	"""Normalize an address or coordinate for the Distance Matrix API.

	Purpose:
		Converts a coordinate tuple into the ``lat,lng`` string expected by Google
		Distance Matrix requests while preserving free-form address strings. The
		helper is used when constructing origin and destination query strings and
		when fallback labels are needed for flattened route rows.

	Args:
		o: Address string or ``(latitude, longitude)`` coordinate tuple.

	Returns:
		str: API-ready origin or destination text.
	"""
	if isinstance( o, tuple ) and len( o ) == 2:
		return f'{o[ 0 ]},{o[ 1 ]}'
	
	return str( o )

class DistanceMatrix( ):
	"""Provide route, matrix, comparison, and dataframe helpers.

	Purpose:
		Wraps the Google Distance Matrix API through the shared ``Maps`` gateway and
		normalizes results into row-friendly dictionaries. The class supports single
		route summaries, many-origin/many-destination matrices, mode comparisons,
		metric conversions, and pandas DataFrame output for Streamlit display,
		spreadsheet enrichment, and downstream analytics.

	Attributes:
		_maps: Shared Google Maps gateway used for Distance Matrix requests.
		modes: Supported Google Distance Matrix travel modes.
		data: Raw Distance Matrix response payload from the latest request.
		rows: Flattened route rows from the latest matrix request.
	"""
	_maps: Maps
	modes: List[ str ]
	data: Dict[ str, Any ] | None
	rows: List[ Dict[ str, Any ] ] | None
	
	def __init__( self, maps: Maps ) -> None:
		"""Initialize the Distance Matrix service wrapper.

		Purpose:
			Stores the shared Google Maps gateway, supported travel modes, and runtime
			state used by matrix, summary, comparison, conversion, and dataframe helper
			methods. The constructor performs local assignment only and prepares the
			instance for later API-backed route operations.

		Args:
			maps: Google Maps gateway used for Distance Matrix API requests.
		"""
		self._maps = maps
		self.modes = [ 'driving', 'walking', 'bicycling', 'transit' ]
		self.data = None
		self.rows = None
	
	def normalize_mode( self, mode: str ) -> str:
		"""Validate and normalize a travel mode.

		Purpose:
			Converts a requested travel mode to lowercase and verifies it is one of
			the Google Distance Matrix modes supported by Mappy. The normalized value
			is used in gateway parameters and route output rows.

		Args:
			mode: Travel mode such as ``driving``, ``walking``, ``bicycling``, or
				``transit``.

		Returns:
			str: Normalized travel mode.

		Raises:
			Error: Raised after logging when validation or normalization fails.
		"""
		try:
			throw_if( 'mode', mode )
			value = str( mode ).strip( ).lower( )
			if value not in self.modes:
				raise ValueError( f'Unsupported travel mode "{mode}". Use one of: {self.modes}.' )
			
			return value
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'DistanceMatrix'
			exception.method = 'normalize_mode( self, mode: str ) -> str'
			Logger( ).write( exception )
			raise exception
	
	def normalize_inputs( self, values: List[ AddressOrCoord ] | Tuple[ AddressOrCoord, ... ]
	                                    | AddressOrCoord ) -> List[ AddressOrCoord ]:
		"""Normalize one or many origins or destinations into a list.

		Purpose:
			Accepts a single address, a single coordinate tuple, a list of addresses
			or coordinates, or a tuple of values and returns a list shape suitable for
			Distance Matrix query construction. Single coordinate tuples are preserved
			as one coordinate instead of being expanded into two independent values.

		Args:
			values: Single origin/destination value or a collection of values.

		Returns:
			List[AddressOrCoord]: Normalized input list.

		Raises:
			Error: Raised after logging when validation or normalization fails.
		"""
		try:
			throw_if( 'values', values )
			if isinstance( values, list ):
				return values
			if isinstance( values, tuple ):
				if len( values ) == 2 and all( isinstance( x, (int, float) ) for x in values ):
					return [ values ]
				return list( values )
			return [ values ]
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'DistanceMatrix'
			exception.method = 'normalize_inputs( self, values: object ) -> List[ AddressOrCoord ]'
			Logger( ).write( exception )
			raise exception
	
	def convert_distance( self, meters: int | float | None ) -> Dict[ str, float | None ]:
		"""Convert meters into kilometers and miles.

		Purpose:
			Normalizes Google Distance Matrix meter values into kilometer and mile
			fields used by summaries, matrix rows, dataframe output, and Streamlit
			display. Missing distance values are preserved as ``None``.

		Args:
			meters: Distance in meters.

		Returns:
			Dict[str, float | None]: Dictionary containing ``distance_km`` and
				``distance_miles``.

		Raises:
			Error: Raised after logging when conversion fails.
		"""
		try:
			if meters is None:
				return {
						'distance_km': None,
						'distance_miles': None
				}
			value = float( meters )
			return {
					'distance_km': round( value / 1000.0, 3 ),
					'distance_miles': round( value / 1609.344, 3 )
			}
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'DistanceMatrix'
			exception.method = 'convert_distance( self, meters: int | float | None ) -> Dict[ str, float | None ]'
			Logger( ).write( exception )
			raise exception
	
	def convert_duration( self, seconds: int | float | None ) -> Dict[ str, float | None ]:
		"""Convert seconds into minutes and hours.

		Purpose:
			Normalizes Google Distance Matrix duration values into minute and hour
			fields used by summaries, matrix rows, dataframe output, and Streamlit
			display. Missing duration values are preserved as ``None``.

		Args:
			seconds: Duration in seconds.

		Returns:
			Dict[str, float | None]: Dictionary containing ``duration_minutes`` and
				``duration_hours``.

		Raises:
			Error: Raised after logging when conversion fails.
		"""
		try:
			if seconds is None:
				return {
						'duration_minutes': None,
						'duration_hours': None
				}
			value = float( seconds )
			return {
					'duration_minutes': round( value / 60.0, 2 ),
					'duration_hours': round( value / 3600.0, 3 )
			}
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'DistanceMatrix'
			exception.method = 'convert_duration( self, seconds: int | float | None ) -> Dict[ str, float | None ]'
			Logger( ).write( exception )
			raise exception
	
	def flatten_element( self, origin: str, destination: str, mode: str,
			element: Dict[ str, Any ] ) -> Dict[ str, Any ]:
		"""Flatten one Distance Matrix element into a route row.

		Purpose:
			Converts one Google Distance Matrix element into a dictionary containing
			origin, destination, mode, status, text fields, raw meter/second values,
			converted distance values, converted duration values, and traffic-aware
			duration values when available. The row shape is reused by summary,
			comparison, dataframe, and Streamlit display workflows.

		Args:
			origin: Resolved origin label from the API or fallback input value.
			destination: Resolved destination label from the API or fallback input
				value.
			mode: Travel mode used for the request.
			element: One Distance Matrix element dictionary.

		Returns:
			Dict[str, Any]: Flattened route row.

		Raises:
			Error: Raised after logging when validation or row flattening fails.
		"""
		try:
			throw_if( 'origin', origin )
			throw_if( 'destination', destination )
			throw_if( 'mode', mode )
			element = element or { }
			distance = element.get( 'distance' ) or { }
			duration = element.get( 'duration' ) or { }
			duration_traffic = element.get( 'duration_in_traffic' ) or { }
			distance_meters = distance.get( 'value' )
			duration_seconds = duration.get( 'value' )
			traffic_seconds = duration_traffic.get( 'value' )
			row = {
					'origin': origin,
					'destination': destination,
					'mode': mode,
					'status': element.get( 'status' ),
					'distance_text': distance.get( 'text' ),
					'distance_meters': distance_meters,
					'duration_text': duration.get( 'text' ),
					'duration_seconds': duration_seconds,
					'duration_in_traffic_text': duration_traffic.get( 'text' ),
					'duration_in_traffic_seconds': traffic_seconds
			}
			row.update( self.convert_distance( distance_meters ) )
			row.update( self.convert_duration( duration_seconds ) )
			
			if traffic_seconds is None:
				row[ 'duration_in_traffic_minutes' ] = None
				row[ 'duration_in_traffic_hours' ] = None
			else:
				row[ 'duration_in_traffic_minutes' ] = round( float( traffic_seconds ) / 60.0, 2 )
				row[ 'duration_in_traffic_hours' ] = round( float( traffic_seconds ) / 3600.0, 3 )
			return row
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'DistanceMatrix'
			exception.method = 'flatten_element( self, *args ) -> Dict[ str, Any ]'
			Logger( ).write( exception )
			raise exception
	
	def matrix( self,
			origins: List[ AddressOrCoord ] | Tuple[ AddressOrCoord, ... ] | AddressOrCoord,
			destinations: List[ AddressOrCoord ] | Tuple[ AddressOrCoord, ... ] | AddressOrCoord,
			mode: str = 'driving', departure_time: str = '' ) -> List[ Dict[ str, Any ] ]:
		"""Execute a Distance Matrix request.

		Purpose:
			Builds a Distance Matrix request for one or more origins and destinations,
			normalizes the selected travel mode, optionally applies a departure time,
			calls the shared Google Maps gateway, and flattens each returned element
			into route rows. The latest raw payload and flattened rows are stored on
			the instance for summaries, comparisons, dataframe conversion, and UI
			inspection.

		Args:
			origins: Single origin or collection of origins.
			destinations: Single destination or collection of destinations.
			mode: Travel mode such as ``driving``, ``walking``, ``bicycling``, or
				``transit``.
			departure_time: Optional departure time. Use ``now`` for traffic-aware
				driving results when supported.

		Returns:
			List[Dict[str, Any]]: Flattened route rows.

		Raises:
			Error: Raised after logging when validation, gateway execution, response
				handling, or row flattening fails.
		"""
		try:
			travel_mode = self.normalize_mode( mode )
			origin_values = self.normalize_inputs( origins )
			destination_values = self.normalize_inputs( destinations )
			origin_query = '|'.join( fmt( value ) for value in origin_values )
			destination_query = '|'.join( fmt( value ) for value in destination_values )
			params = {
					'origins': origin_query,
					'destinations': destination_query,
					'mode': travel_mode
			}
			if departure_time and str( departure_time ).strip( ):
				params[ 'departure_time' ] = str( departure_time ).strip( )
			self.data = self._maps.request( 'distancematrix/json', params )
			if not isinstance( self.data, dict ):
				raise ValueError( 'Distance Matrix response was not a dictionary.' )
			origin_addresses = self.data.get( 'origin_addresses' ) or [ fmt( x ) for x in
			                                                            origin_values ]
			destination_addresses = self.data.get( 'destination_addresses' ) or [
					fmt( x ) for x in destination_values ]
			api_rows = self.data.get( 'rows' ) or [ ]
			output_rows: List[ Dict[ str, Any ] ] = [ ]
			for origin_index, row in enumerate( api_rows ):
				origin_label = (
						origin_addresses[ origin_index ]
						if origin_index < len( origin_addresses )
						else fmt( origin_values[ origin_index ] ))
				elements = row.get( 'elements' ) or [ ]
				for destination_index, element in enumerate( elements ):
					destination_label = (
							destination_addresses[ destination_index ]
							if destination_index < len( destination_addresses )
							else fmt( destination_values[ destination_index ] ))
					output_rows.append( self.flatten_element( origin=origin_label,
						destination=destination_label, mode=travel_mode, element=element ) )
			self.rows = output_rows
			return output_rows
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'DistanceMatrix'
			exception.method = 'matrix( self, *args ) -> List[ Dict[ str, Any ] ]'
			Logger( ).write( exception )
			raise exception
	
	def summary( self, origin: AddressOrCoord, destination: AddressOrCoord,
			mode: str = 'driving' ) -> Dict:
		"""Return a compact route summary.

		Purpose:
			Executes a one-origin, one-destination matrix request and returns the
			first flattened route as a compact summary containing distance, duration,
			traffic-aware duration, origin, destination, mode, and status fields. When
			no rows are returned, the method preserves a predictable no-results shape.

		Args:
			origin: Origin address string or ``(latitude, longitude)`` tuple.
			destination: Destination address string or ``(latitude, longitude)`` tuple.
			mode: Travel mode such as ``driving``, ``walking``, ``bicycling``, or
				``transit``.

		Returns:
			Dict: Compact distance and duration summary.

		Raises:
			Error: Raised after logging when matrix execution or summary construction
				fails.
		"""
		try:
			rows = self.matrix( origins=origin, destinations=destination, mode=mode )
			if not rows:
				return {
						'distance_text': None,
						'distance_meters': None,
						'duration_text': None,
						'duration_seconds': None,
						'status': 'NO_RESULTS'
				}
			
			row = rows[ 0 ]
			return {
					'distance_text': row.get( 'distance_text' ),
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
					'origin': row.get( 'origin' ),
					'destination': row.get( 'destination' ),
					'mode': row.get( 'mode' ),
					'status': row.get( 'status' )
			}
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'DistanceMatrix'
			exception.method = 'summary( self, origin: AddressOrCoord, destination: AddressOrCoord, mode: str=driving ) -> Dict'
			Logger( ).write( exception )
			raise exception
	
	def compare_modes( self, origin: AddressOrCoord, destination: AddressOrCoord,
			modes: List[ str ] | None = None, departure_time: str = '' ) -> List[
		Dict[ str, Any ] ]:
		"""Compare route results across travel modes.

		Purpose:
			Executes a single-route matrix request for each selected travel mode and
			returns the first flattened route row for each successful mode. Driving
			requests can preserve the supplied departure time for traffic-aware
			results, while non-driving modes omit it to avoid unsupported combinations.

		Args:
			origin: Origin address string or coordinate tuple.
			destination: Destination address string or coordinate tuple.
			modes: Optional travel modes to compare. Defaults to all supported modes.
			departure_time: Optional departure time. Use ``now`` for traffic-aware
				driving results when supported.

		Returns:
			List[Dict[str, Any]]: One flattened route row per successful travel mode.

		Raises:
			Error: Raised after logging when validation, matrix execution, or comparison
				construction fails.
		"""
		try:
			selected_modes = modes or self.modes
			results: List[ Dict[ str, Any ] ] = [ ]
			for mode in selected_modes:
				active_mode = self.normalize_mode( mode )
				active_departure = departure_time if active_mode == 'driving' else ''
				rows = self.matrix(
					origins=origin,
					destinations=destination,
					mode=active_mode,
					departure_time=active_departure )
				if rows:
					results.append( rows[ 0 ] )
			return results
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'DistanceMatrix'
			exception.method = 'compare_modes( self, *args ) -> List[ Dict[ str, Any ] ]'
			Logger( ).write( exception )
			raise exception
	
	def to_dataframe( self, rows: List[ Dict[ str, Any ] ] | None = None ) -> pd.DataFrame:
		"""Convert route rows into a pandas DataFrame.

		Purpose:
			Transforms caller-supplied rows or the latest matrix rows into a DataFrame
			for Streamlit display, CSV/Excel export, diagnostics, or downstream
			analytics. Missing or empty rows return an empty DataFrame.

		Args:
			rows: Optional route rows. Defaults to the most recent matrix rows.

		Returns:
			pd.DataFrame: Route results as a DataFrame.

		Raises:
			Error: Raised after logging when dataframe conversion fails.
		"""
		try:
			active_rows = rows if rows is not None else self.rows
			if not active_rows:
				return pd.DataFrame( )
			return pd.DataFrame( active_rows )
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'DistanceMatrix'
			exception.method = 'to_dataframe( self, rows: List[ Dict[ str, Any ] ] | None=None ) -> pd.DataFrame'
			Logger( ).write( exception )
			raise exception