'''
  ******************************************************************************************
      Assembly:                Mappy
      Filename:                excel.py
      Author:                  Terry D. Eppler
      Created:                 05-31-2022

      Last Modified By:        Terry D. Eppler
      Last Modified On:        05-01-2025
  ******************************************************************************************
  <copyright file="excel.py" company="Terry D. Eppler">

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
    excel.py
  </summary>
  ******************************************************************************************
  '''
from typing import Optional, Dict, List
import pandas as pd
if __package__:
	from .caches import BaseCache
else:
	from caches import BaseCache
if __package__:
	from .geocode import Geocoder
else:
	from geocode import Geocoder
if __package__:
	from .maps import Maps
else:
	from maps import Maps
if __package__:
	from .places import Place
else:
	from places import Place
if __package__:
	from .boogr import Error, Logger
else:
	from boogr import Error, Logger

def throw_if( name: str, value: object ) -> None:
	"""Validate that a required Excel workflow value is present.

	Purpose:
		Provides a lightweight guard for required file paths, dataframes, output
		containers, column names, and geocoding inputs before spreadsheet enrichment
		operations continue. The function rejects missing objects and blank strings so
		file and dataframe workflows fail with clear validation errors.

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

class Excel:
	"""Read, write, and enrich spreadsheet location records.

	Purpose:
		Provides file-based and dataframe-oriented helpers for reading CSV/XLSX data,
		preserving string fields, resolving addresses through Geocoder and Places
		fallback services, appending canonical geospatial output columns, writing
		enriched files, and storing summary metrics for Streamlit display or
		downstream reporting.

	Attributes:
		api_key: Google Maps Platform API key supplied to the helper.
		maps: Maps gateway used by Geocoder and Places wrappers.
		geocoder: Geocoder service used as the primary location resolver.
		places: Places service used as the fallback location resolver.
		input_path: Input CSV/XLSX path used by the latest enrichment operation.
		output_path: Output CSV/XLSX path used by the latest enrichment operation.
		dataframe: DataFrame read or enriched by the latest operation.
		worksheet: Excel worksheet name or index context used by read/write operations.
		output: Output-column container from the latest enrichment operation.
		address: Address column name used by address-based enrichment.
		cache: Optional cache backend shared by Geocoder and Places.
		file_path: File path used by the latest read or write operation.
		last_summary: Summary metrics from the latest enrichment result.
		city: City column name or current city value used by enrichment.
		state: State column name or current state value used by enrichment.
		country: Country column name or current country value used by enrichment.
	"""
	api_key: str
	maps: Optional[ Maps ]
	geocoder: Optional[ Geocoder ]
	places: Optional[ Place ]
	input_path: Optional[ str ]
	output_path: Optional[ str ]
	dataframe: Optional[ pd.DataFrame ]
	worksheet: Optional[ str ]
	output: Optional[ Dict[ str, List ] ]
	address: Optional[ str ]
	cache: Optional[ BaseCache ]
	file_path: Optional[ str ]
	last_summary: Optional[ Dict ]
	city: Optional[ str ]
	state: Optional[ str ]
	country: Optional[ str ]
	
	def __init__( self, api: str, cache: Optional[ BaseCache ] = None ) -> None:
		"""Initialize the Excel enrichment helper.

		Purpose:
			Stores the supplied API key, optional cache backend, shared Maps gateway,
			Geocoder wrapper, Places fallback wrapper, and runtime state used by later
			read, write, resolution, enrichment, and summary methods.

		Args:
			api: Google Maps Platform API key.
			cache: Optional cache backend shared by Geocoder and Places.
		"""
		throw_if( 'api', api )
		self.api_key = api
		self.cache = cache
		self.maps = Maps( api_key=self.api_key )
		self.geocoder = Geocoder( self.maps, cache=self.cache )
		self.places = Place( self.maps, cache=self.cache )
		self.input_path = None
		self.output_path = None
		self.dataframe = None
		self.worksheet = None
		self.output = None
		self.address = None
		self.file_path = None
		self.last_summary = None
		self.city = None
		self.state = None
		self.country = None
	
	def read( self, path: str, sheet: Optional[ str ] ) -> pd.DataFrame:
		"""Read a CSV or Excel file into a cleaned DataFrame.

		Purpose:
			Loads CSV or XLSX input while preserving string-like values, including
			leading zeros. Object columns are filled, converted to strings, and stripped
			so downstream geocoding and column-detection workflows operate on stable
			text values.

		Args:
			path: Input file path ending in ``.csv`` or an Excel-compatible extension.
			sheet: Optional worksheet name for Excel input.

		Returns:
			pd.DataFrame: Loaded and cleaned DataFrame.

		Raises:
			Error: Raised after logging when validation, file reading, or dataframe
				normalization fails.
		"""
		try:
			throw_if( 'path', path )
			
			path_value = path
			sheet_value = sheet
			
			self.file_path = path_value
			self.worksheet = sheet_value
			
			if self.file_path.lower( ).endswith( '.csv' ):
				self.dataframe = pd.read_csv( self.file_path, dtype=str )
			else:
				self.dataframe = pd.read_excel(
					self.file_path,
					sheet_name=self.worksheet or 0,
					dtype=str )
			
			for column in self.dataframe.columns:
				if self.dataframe[ column ].dtype == object:
					self.dataframe[ column ] = (
							self.dataframe[ column ]
							.fillna( '' )
							.astype( str )
							.str.strip( )
					)
			
			return self.dataframe
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'Excel'
			exception.method = 'read( self, path: str, sheet: Optional[ str ] ) -> pd.DataFrame'
			Logger( ).write( exception )
			raise exception
	
	def write( self, df: pd.DataFrame, path: str, sheet: Optional[ str ] ) -> None:
		"""Write a DataFrame to CSV or Excel.

		Purpose:
			Copies the supplied DataFrame, stores the output path and worksheet context
			on the instance, and writes the data with the index suppressed. CSV output
			uses ``to_csv`` and non-CSV output uses ``to_excel`` with a default sheet
			name when one is not supplied.

		Args:
			df: DataFrame to persist.
			path: Output file path ending in ``.csv`` or an Excel-compatible extension.
			sheet: Optional Excel worksheet name.

		Raises:
			Error: Raised after logging when validation or file writing fails.
		"""
		try:
			throw_if( 'df', df )
			throw_if( 'path', path )
			
			path_value = path
			sheet_value = sheet or 'Sheet1'
			dataframe_value = df.copy( )
			
			self.file_path = path_value
			self.dataframe = dataframe_value
			self.worksheet = sheet_value
			
			if self.file_path.lower( ).endswith( '.csv' ):
				self.dataframe.to_csv( self.file_path, index=False )
			else:
				self.dataframe.to_excel(
					self.file_path,
					index=False,
					sheet_name=self.worksheet )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'Excel'
			exception.method = 'write( self, df: pd.DataFrame, path: str, sheet: Optional[ str ] ) -> None'
			Logger( ).write( exception )
			raise exception
	
	def create_outputs( self ) -> Dict[ str, List ]:
		"""Create the standard geospatial output-column container.

		Purpose:
			Builds the dictionary of empty lists used during file enrichment. Each list
			represents one canonical output column appended to the source DataFrame,
			including formatted address, coordinates, place metadata, administrative
			components, row-level status, and row-level error fields.

		Returns:
			Dict[str, List]: Output-column container with empty value lists.

		Raises:
			Error: Raised after logging when output-container construction fails.
		"""
		try:
			return {
					'formatted_address': [ ],
					'lat': [ ],
					'lng': [ ],
					'place_id': [ ],
					'types': [ ],
					'country_code': [ ],
					'country_name': [ ],
					'admin_level_1': [ ],
					'admin_level_2': [ ],
					'locality': [ ],
					'postal_code': [ ],
					'geocode_status': [ ],
					'geocode_error': [ ],
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'Excel'
			exception.method = 'create_outputs( self ) -> Dict[ str, List ]'
			Logger( ).write( exception )
			raise exception
	
	def append_empty( self, outputs: Dict[ str, List ], status: str = 'skipped_empty',
			error: Optional[ str ] = None ) -> None:
		"""Append an empty geocode result to the output container.

		Purpose:
			Adds placeholder values to every canonical geospatial output column for a
			source row that cannot or should not be geocoded. The method preserves row
			alignment between the original DataFrame and appended enrichment columns.

		Args:
			outputs: Output-column container created by ``create_outputs``.
			status: Row-level geocode status to append.
			error: Optional row-level error message.

		Raises:
			Error: Raised after logging when validation or output mutation fails.
		"""
		try:
			throw_if( 'outputs', outputs )
			
			outputs[ 'formatted_address' ].append( None )
			outputs[ 'lat' ].append( None )
			outputs[ 'lng' ].append( None )
			outputs[ 'place_id' ].append( None )
			outputs[ 'types' ].append( None )
			outputs[ 'country_code' ].append( None )
			outputs[ 'country_name' ].append( None )
			outputs[ 'admin_level_1' ].append( None )
			outputs[ 'admin_level_2' ].append( None )
			outputs[ 'locality' ].append( None )
			outputs[ 'postal_code' ].append( None )
			outputs[ 'geocode_status' ].append( status or 'skipped_empty' )
			outputs[ 'geocode_error' ].append( error )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'Excel'
			exception.method = 'append_empty( self, outputs: Dict[ str, List ], status: str=skipped_empty ) -> None'
			Logger( ).write( exception )
			raise exception
	
	def append_result( self, outputs: Dict[ str, List ], result: Dict,
			status: str, error: Optional[ str ] = None ) -> None:
		"""Append one resolved geospatial result to the output container.

		Purpose:
			Extracts canonical geocode or Places result fields and appends them to the
			enrichment output lists. The method keeps each output column aligned with
			the source DataFrame row and appends row-level status and error metadata
			alongside the resolved location values.

		Args:
			outputs: Output-column container created by ``create_outputs``.
			result: Flattened Geocoder or Places result dictionary.
			status: Row-level resolution status.
			error: Optional row-level error message.

		Raises:
			Error: Raised after logging when validation or output mutation fails.
		"""
		try:
			throw_if( 'outputs', outputs )
			
			result_value = result or { }
			status_value = status or 'not_found'
			
			outputs[ 'formatted_address' ].append( result_value.get( 'formatted_address' ) )
			outputs[ 'lat' ].append( result_value.get( 'lat' ) )
			outputs[ 'lng' ].append( result_value.get( 'lng' ) )
			outputs[ 'place_id' ].append( result_value.get( 'place_id' ) )
			outputs[ 'types' ].append( result_value.get( 'types' ) )
			outputs[ 'country_code' ].append( result_value.get( 'country_code' ) )
			outputs[ 'country_name' ].append( result_value.get( 'country_name' ) )
			outputs[ 'admin_level_1' ].append( result_value.get( 'admin_level_1' ) )
			outputs[ 'admin_level_2' ].append( result_value.get( 'admin_level_2' ) )
			outputs[ 'locality' ].append( result_value.get( 'locality' ) )
			outputs[ 'postal_code' ].append( result_value.get( 'postal_code' ) )
			outputs[ 'geocode_status' ].append( status_value )
			outputs[ 'geocode_error' ].append( error )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'Excel'
			exception.method = 'append_result( self, outputs: Dict[ str, List ], result: Dict, status: str ) -> None'
			Logger( ).write( exception )
			raise exception
	
	def summarize( self, df: pd.DataFrame ) -> Dict:
		"""Build summary metrics for an enriched DataFrame.

		Purpose:
			Counts total rows and row-level geocoding statuses from the latest
			enrichment result. The summary is stored on the instance for Streamlit
			display, reporting, audit checks, and downstream validation of enrichment
			coverage.

		Args:
			df: Enriched DataFrame containing optional ``geocode_status`` values.

		Returns:
			Dict: Summary metrics for the enrichment result.

		Raises:
			Error: Raised after logging when validation or summary generation fails.
		"""
		try:
			throw_if( 'df', df )
			
			status_counts = { }
			
			if 'geocode_status' in df.columns:
				status_counts = df[ 'geocode_status' ].value_counts( dropna=False ).to_dict( )
			
			summary = {
					'rows_total': int( len( df ) ),
					'rows_ok': int( status_counts.get( 'ok', 0 ) ),
					'rows_ok_places': int( status_counts.get( 'ok_places', 0 ) ),
					'rows_not_found': int( status_counts.get( 'not_found', 0 ) ),
					'rows_skipped_empty': int( status_counts.get( 'skipped_empty', 0 ) ),
					'rows_error': int( status_counts.get( 'error', 0 ) ),
					'status_counts': status_counts,
			}
			
			self.last_summary = summary
			
			return self.last_summary
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'Excel'
			exception.method = 'summarize( self, df: pd.DataFrame ) -> Dict'
			Logger( ).write( exception )
			raise exception
	
	def detect_columns( self, df: pd.DataFrame ) -> Dict:
		"""Suggest likely location columns from a DataFrame.

		Purpose:
			Inspects DataFrame column names using normalized lowercase comparisons and
			returns likely address, city, state, and country column names. The result
			supports Streamlit defaults, manual enrichment setup, and file-ingestion
			workflows where users upload heterogeneous location datasets.

		Args:
			df: DataFrame to inspect.

		Returns:
			Dict: Suggested column names keyed by ``address``, ``city``, ``state``,
				and ``country``.

		Raises:
			Error: Raised after logging when validation or column inspection fails.
		"""
		try:
			throw_if( 'df', df )
			
			columns = list( df.columns )
			lower_map = { str( column ).strip( ).lower( ): column for column in columns }
			
			def find_first( names: List[ str ] ) -> Optional[ str ]:
				for name in names:
					if name in lower_map:
						return lower_map[ name ]
				return None
			
			return {
					'address': find_first(
						[
								'address',
								'street address',
								'full address',
								'location',
								'mailing address'
						] ),
					'city': find_first(
						[
								'city',
								'town',
								'locality',
								'municipality'
						] ),
					'state': find_first(
						[
								'state',
								'st',
								'province',
								'region',
								'admin_level_1'
						] ),
					'country': find_first(
						[
								'country',
								'country_code',
								'cntry',
								'nation'
						] )
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'Excel'
			exception.method = 'detect_columns( self, df: pd.DataFrame ) -> Dict'
			Logger( ).write( exception )
			raise exception
	
	def resolve_address( self, address: str, country: Optional[ str ] = None ) -> Dict:
		"""Resolve one free-form address with Geocoder and Places fallback.

		Purpose:
			Attempts to resolve a free-form address through Geocoder first, then falls
			back to Places Text Search when geocoding fails. The method returns a
			standard row-resolution dictionary containing a result payload, status, and
			error text so file enrichment can continue without failing an entire batch.

		Args:
			address: Free-form address text.
			country: Optional ISO-2 country bias. Defaults to ``US`` when omitted.

		Returns:
			Dict: Row-level resolution result with ``result``, ``status``, and
				``error`` fields.

		Raises:
			Error: Raised after logging when top-level validation or resolution setup
				fails.
		"""
		try:
			throw_if( 'address', address )
			
			address_value = str( address ).strip( )
			country_value = str( country or 'US' ).strip( ).upper( )
			
			self.address = address_value
			self.country = country_value
			
			try:
				result = self.geocoder.freeform( self.address, country=self.country )
				return {
						'result': result or { },
						'status': 'ok',
						'error': None
				}
			
			except Exception as geocode_error:
				try:
					result = self.places.text_to_location( self.address, country=self.country )
					return {
							'result': result or { },
							'status': 'ok_places',
							'error': None
					}
				
				except Exception as places_error:
					return {
							'result': { },
							'status': 'not_found',
							'error': f'{geocode_error}; {places_error}'
					}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'Excel'
			exception.method = 'resolve_address( self, address: str, country: Optional[ str ]=None ) -> Dict'
			Logger( ).write( exception )
			raise exception
	
	def resolve_city_state_country( self, city: str, state: Optional[ str ],
			country: str ) -> Dict:
		"""Resolve one structured city/state/country location.

		Purpose:
			Attempts to resolve a structured location through Geocoder first, then
			falls back to Places Text Search using a composed query when geocoding
			fails. The method returns a standard row-resolution dictionary so file
			enrichment can preserve row-level status without stopping the batch.

		Args:
			city: City or locality value.
			state: Optional state, province, region, or territory value.
			country: Country name or ISO-2 country code.

		Returns:
			Dict: Row-level resolution result with ``result``, ``status``, and
				``error`` fields.

		Raises:
			Error: Raised after logging when top-level resolution setup fails.
		"""
		try:
			city_value = str( city or '' ).strip( )
			state_value = str( state or '' ).strip( )
			country_value = str( country or '' ).strip( )
			
			if not any( [ city_value, state_value, country_value ] ):
				return {
						'result': { },
						'status': 'skipped_empty',
						'error': None
				}
			
			self.city = city_value
			self.state = state_value
			self.country = country_value
			
			try:
				result = self.geocoder.city_state_country(
					self.city,
					self.state,
					self.country )
				return {
						'result': result or { },
						'status': 'ok',
						'error': None
				}
			
			except Exception as geocode_error:
				query = ', '.join(
					[ value for value in [ self.city, self.state, self.country ] if value ] )
				
				try:
					result = self.places.text_to_location( query, country=self.country )
					return {
							'result': result or { },
							'status': 'ok_places',
							'error': None
					}
				
				except Exception as places_error:
					return {
							'result': { },
							'status': 'not_found',
							'error': f'{geocode_error}; {places_error}'
					}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'Excel'
			exception.method = 'resolve_city_state_country( self, city: str, state: Optional[ str ], country: str ) -> Dict'
			Logger( ).write( exception )
			raise exception
	
	def enrich_from_address( self, inpath: str, outpath: str, address: str, sheet: Optional[ str ],
			cntry: Optional[ str ] ) -> pd.DataFrame:
		"""Enrich a file using one free-form address column.

		Purpose:
			Reads a CSV/XLSX file, validates the address column, resolves each
			populated address through Geocoder and Places fallback, appends canonical
			geospatial output columns, stores enrichment state and summary metrics, and
			writes the enriched DataFrame to the requested output path.

		Args:
			inpath: Input CSV/XLSX path containing the address column.
			outpath: Output CSV/XLSX path to write enriched results.
			address: Column name containing free-form address text.
			sheet: Optional Excel worksheet name.
			cntry: Optional column name containing country-bias values.

		Returns:
			pd.DataFrame: Enriched DataFrame written to ``outpath``.

		Raises:
			Error: Raised after logging when validation, reading, enrichment, summary,
				or writing fails.
		"""
		try:
			throw_if( 'inpath', inpath )
			throw_if( 'outpath', outpath )
			throw_if( 'address', address )
			
			self.input_path = inpath
			self.output_path = outpath
			self.address = address
			self.worksheet = sheet
			self.country = cntry
			
			df = self.read( self.input_path, self.worksheet )
			
			if self.address not in df.columns:
				raise ValueError( f'Address column "{self.address}" was not found.' )
			
			outputs = self.create_outputs( )
			resolved = { }
			
			for _, row in df.iterrows( ):
				addr = str( row.get( self.address ) or '' ).strip( )
				
				if not addr:
					self.append_empty( outputs )
					continue
				
				hint = (
						str( row.get( self.country ) or '' ).strip( ).upper( )
						if (self.country and self.country in df.columns)
						else 'US'
				)
				cache_key = f'{addr}::{hint}'
				
				if cache_key not in resolved:
					resolved[ cache_key ] = self.resolve_address( addr, country=hint )
				
				item = resolved[ cache_key ]
				self.append_result(
					outputs,
					item.get( 'result', { } ),
					item.get( 'status', 'not_found' ),
					item.get( 'error' ) )
			
			for key, values in outputs.items( ):
				df[ key ] = values
			
			self.dataframe = df
			self.output = outputs
			self.summarize( self.dataframe )
			self.write( self.dataframe, self.output_path, self.worksheet )
			
			return self.dataframe
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'Excel'
			exception.method = 'enrich_from_address( self, *args ) -> pd.DataFrame'
			Logger( ).write( exception )
			raise exception
	
	def enrich( self, inpath: str, outpath: str, city: str, state: Optional[ str ], cntry: str,
			sheet: Optional[ str ] = None, ) -> pd.DataFrame:
		"""Enrich a file using city, state, and country columns.

		Purpose:
			Reads a CSV/XLSX file, validates the configured city, optional state, and
			country columns, resolves each populated location through Geocoder and
			Places fallback, appends canonical geospatial output columns, stores
			enrichment state and summary metrics, and writes the enriched DataFrame to
			the requested output path.

		Args:
			inpath: Input CSV/XLSX path containing location columns.
			outpath: Output CSV/XLSX path to write enriched results.
			city: Column name containing city or locality values.
			state: Optional column name containing state, province, region, or
				territory values.
			cntry: Column name containing country names or ISO-2 country codes.
			sheet: Optional Excel worksheet name.

		Returns:
			pd.DataFrame: Enriched DataFrame written to ``outpath``.

		Raises:
			Error: Raised after logging when validation, reading, enrichment, summary,
				or writing fails.
		"""
		try:
			throw_if( 'inpath', inpath )
			throw_if( 'outpath', outpath )
			throw_if( 'city', city )
			throw_if( 'cntry', cntry )
			
			self.input_path = inpath
			self.output_path = outpath
			self.city = city
			self.state = state
			self.country = cntry
			self.worksheet = sheet
			
			df = self.read( self.input_path, self.worksheet )
			
			if self.city not in df.columns:
				raise ValueError( f'City column "{self.city}" was not found.' )
			
			if self.country not in df.columns:
				raise ValueError( f'Country column "{self.country}" was not found.' )
			
			if self.state and self.state not in df.columns:
				raise ValueError( f'State column "{self.state}" was not found.' )
			
			outputs = self.create_outputs( )
			resolved = { }
			
			for _, row in df.iterrows( ):
				city_value = str( row.get( self.city ) or '' ).strip( )
				state_value = (
						str( row.get( self.state ) or '' ).strip( )
						if (self.state and self.state in df.columns)
						else ''
				)
				country_value = str( row.get( self.country ) or '' ).strip( )
				
				if not any( [ city_value, state_value, country_value ] ):
					self.append_empty( outputs )
					continue
				
				cache_key = f'{city_value}::{state_value}::{country_value}'
				
				if cache_key not in resolved:
					resolved[ cache_key ] = self.resolve_city_state_country(
						city_value,
						state_value,
						country_value )
				
				item = resolved[ cache_key ]
				self.append_result(
					outputs,
					item.get( 'result', { } ),
					item.get( 'status', 'not_found' ),
					item.get( 'error' ) )
			
			for key, values in outputs.items( ):
				df[ key ] = values
			
			self.dataframe = df
			self.output = outputs
			self.summarize( self.dataframe )
			self.write( self.dataframe, self.output_path, self.worksheet )
			
			return self.dataframe
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'Excel'
			exception.method = 'enrich( self, *args ) -> pd.DataFrame'
			Logger( ).write( exception )
			raise exception