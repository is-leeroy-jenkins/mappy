'''
  ******************************************************************************************
      Assembly:                Mappy
      Filename:                timezones.py
      Author:                  Terry D. Eppler
      Created:                 05-31-2022

      Last Modified By:        Terry D. Eppler
      Last Modified On:        05-01-2025
  ******************************************************************************************
  <copyright file="timezones.py" company="Terry D. Eppler">

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
    timezones.py
  </summary>
  ******************************************************************************************
'''
import time
import datetime as dt
from typing import Optional, Dict
if __package__:
	from .maps import Maps
else:
	from maps import Maps
if __package__:
	from .boogr import Error, Logger
else:
	from boogr import Error, Logger

def throw_if( name: str, value: object ) -> None:
	"""Validate that a required time-zone value is present.

	Purpose:
		Provides a lightweight guard for required Time Zone API inputs before
		coordinate validation, gateway request construction, UTC offset conversion,
		local-time conversion, and batch enrichment. The function rejects missing
		objects and blank strings so time-zone workflows fail before issuing
		ambiguous external API calls.

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

class Timezone:
	"""Resolve time-zone metadata from geographic coordinates.

	Purpose:
		Wraps the Google Time Zone API through the shared ``Maps`` gateway and
		normalizes API results for Streamlit display, spreadsheet enrichment, and
		row-level data workflows. The class validates coordinates, retrieves full
		time-zone payloads, extracts IANA time-zone identifiers, computes total UTC
		offsets, converts UTC datetimes into local time, and enriches batches of row
		dictionaries with time-zone fields.

	Attributes:
		timestamp: Unix timestamp used for the latest Google Time Zone API request.
		maps: Google Maps gateway used for Time Zone API requests.
		latitude: Latitude from the latest validated coordinate.
		longitude: Longitude from the latest validated coordinate.
		data: Raw Google Time Zone API response payload from the latest lookup.
		offset: Total UTC offset in hours from the latest lookup.
		local: ISO-formatted local time from the latest local-time conversion.
		rows: Batch rows from the latest enrichment request.
		lat_field: Latitude field name used by the latest batch enrichment.
		lng_field: Longitude field name used by the latest batch enrichment.
		utc_datetime: UTC datetime used by the latest local-time conversion.
	"""
	timestamp: Optional[ int ]
	maps: Optional[ Maps ]
	latitude: Optional[ float ]
	longitude: Optional[ float ]
	data: Optional[ Dict ]
	offset: Optional[ float ]
	local: Optional[ str ]
	rows: Optional[ list ]
	lat_field: Optional[ str ]
	lng_field: Optional[ str ]
	utc_datetime: Optional[ dt.datetime ]
	
	def __init__( self, maps: Maps ) -> None:
		"""Initialize the Time Zone service wrapper.

		Purpose:
			Stores the shared Google Maps gateway and initializes runtime state used by
			coordinate validation, lookup execution, offset extraction, local-time
			conversion, and batch row enrichment. The constructor performs local
			assignment only and prepares the instance for later API-backed operations.

		Args:
			maps: Google Maps gateway used for Time Zone API requests.
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
		"""Validate and normalize a latitude/longitude pair.

		Purpose:
			Converts coordinate inputs to floats and enforces valid geographic ranges
			before Google Time Zone API requests are built. The validated coordinate is
			stored on the instance for later lookup, local-time conversion, and
			enrichment output.

		Args:
			lat: Latitude in decimal degrees.
			lng: Longitude in decimal degrees.

		Returns:
			tuple: Validated latitude and longitude.

		Raises:
			Error: Raised after logging when validation or conversion fails.
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
			exception.module = 'mappy'
			exception.cause = 'Timezone'
			exception.method = 'validate_coordinates( self, lat: float, lng: float ) -> tuple'
			Logger( ).write( exception )
			raise exception
	
	def lookup( self, lat: float, lng: float ) -> Dict | None:
		"""Fetch the full Google Time Zone API payload for a coordinate.

		Purpose:
			Validates latitude and longitude, captures the current Unix timestamp,
			stores coordinate and timestamp state on the instance, and calls the shared
			Google Maps gateway using the ``timezone/json`` endpoint. The raw response
			payload is retained for ID extraction, offset calculation, local-time
			conversion, and batch enrichment.

		Args:
			lat: Latitude in decimal degrees.
			lng: Longitude in decimal degrees.

		Returns:
			Dict | None: Full Google Time Zone API response payload.

		Raises:
			Error: Raised after logging when validation, request construction, gateway
				execution, or response handling fails.
		"""
		try:
			latitude, longitude = self.validate_coordinates( lat, lng )
			timestamp_value = int( time.time( ) )
			
			self.latitude = latitude
			self.longitude = longitude
			self.timestamp = timestamp_value
			
			self.data = self.maps.request(
				'timezone/json',
				{
						'location': f'{self.latitude},{self.longitude}',
						'timestamp': str( self.timestamp )
				} )
			
			return self.data
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'Timezone'
			exception.method = 'lookup( self, lat: float, lng: float ) -> Dict | None'
			Logger( ).write( exception )
			raise exception
	
	def get_id( self, lat: float, lng: float ) -> Optional[ str ]:
		"""Fetch the IANA time-zone identifier for a coordinate.

		Purpose:
			Delegates to ``lookup`` and extracts the ``timeZoneId`` field from the
			Google Time Zone API payload. The method preserves the latest raw payload
			on the instance for diagnostics and downstream workflows.

		Args:
			lat: Latitude in decimal degrees.
			lng: Longitude in decimal degrees.

		Returns:
			Optional[str]: IANA time-zone identifier when available; otherwise ``None``.

		Raises:
			Error: Raised after logging when lookup or extraction fails.
		"""
		try:
			self.data = self.lookup( lat, lng )
			
			if not isinstance( self.data, dict ):
				return None
			
			return self.data.get( 'timeZoneId' )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'Timezone'
			exception.method = 'get_id( self, lat: float, lng: float ) -> Optional[ str ]'
			Logger( ).write( exception )
			raise exception
	
	def offset_hours( self, lat: float, lng: float ) -> Optional[ float ]:
		"""Fetch the total UTC offset in hours for a coordinate.

		Purpose:
			Delegates to ``lookup`` and combines the Google Time Zone API
			``rawOffset`` and ``dstOffset`` values into a decimal-hour offset. The
			computed value is stored on the instance for later display and enrichment
			workflows.

		Args:
			lat: Latitude in decimal degrees.
			lng: Longitude in decimal degrees.

		Returns:
			Optional[float]: Total UTC offset in hours when available; otherwise
				``None``.

		Raises:
			Error: Raised after logging when lookup or offset conversion fails.
		"""
		try:
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
			exception.module = 'mappy'
			exception.cause = 'Timezone'
			exception.method = 'offset_hours( self, lat: float, lng: float ) -> Optional[ float ]'
			Logger( ).write( exception )
			raise exception
	
	def local_time( self, lat: float, lng: float,
			utc_datetime: Optional[ dt.datetime ] = None ) -> Dict | None:
		"""Convert UTC time into local time for a coordinate.

		Purpose:
			Uses the Google Time Zone API ``rawOffset`` and ``dstOffset`` fields to
			translate a UTC datetime into local time at the supplied coordinate. Naive
			datetimes are treated as UTC, timezone-aware datetimes are normalized to
			UTC, and the resulting time-zone metadata, UTC time, local time, offset,
			latitude, and longitude are returned as a dictionary.

		Args:
			lat: Latitude in decimal degrees.
			lng: Longitude in decimal degrees.
			utc_datetime: Optional UTC datetime. When omitted, the current UTC time is
				used.

		Returns:
			Dict | None: Time-zone metadata and converted local-time fields when a
				payload is available; otherwise ``None``.

		Raises:
			Error: Raised after logging when lookup, datetime normalization, or
				conversion fails.
		"""
		try:
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
			
			return {
					'timeZoneId': self.data.get( 'timeZoneId' ),
					'timeZoneName': self.data.get( 'timeZoneName' ),
					'status': self.data.get( 'status' ),
					'rawOffset': raw_offset,
					'dstOffset': dst_offset,
					'offset_hours': self.offset,
					'utc_time': self.utc_datetime.isoformat( ),
					'local_time': self.local,
					'lat': self.latitude,
					'lng': self.longitude
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'Timezone'
			exception.method = 'local_time( self, lat: float, lng: float, utc_datetime: Optional[ dt.datetime ]=None ) -> Dict | None'
			Logger( ).write( exception )
			raise exception
	
	def batch_lookup( self, rows: list, lat_field: str = 'lat', lng_field: str = 'lng' ) -> list:
		"""Enrich row dictionaries with Google Time Zone API fields.

		Purpose:
			Iterates through copied row dictionaries, reads latitude and longitude
			values from configurable field names, performs a time-zone lookup for each
			row, and appends time-zone metadata, UTC offset, row-level status, and
			row-level error fields. Per-row failures are captured on the row so a
			batch can continue processing even when individual records are invalid.

		Args:
			rows: List of row dictionaries containing latitude and longitude values.
			lat_field: Field name containing latitude values.
			lng_field: Field name containing longitude values.

		Returns:
			list: Copied row dictionaries with appended time-zone fields.

		Raises:
			Error: Raised after logging when batch-level validation or setup fails.
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
						offset_value = round(
							(float( raw_offset ) + float( dst_offset )) / 3600.0,
							3 )
						
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
			exception.module = 'mappy'
			exception.cause = 'Timezone'
			exception.method = 'batch_lookup( self, *args ) -> list'
			Logger( ).write( exception )
			raise exception