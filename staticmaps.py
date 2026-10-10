'''
  ******************************************************************************************
      Assembly:                Mappy
      Filename:                staticmaps.py
      Author:                  Terry D. Eppler
      Created:                 05-31-2022

      Last Modified By:        Terry D. Eppler
      Last Modified On:        05-01-2025
  ******************************************************************************************
  <copyright file="staticmaps.py" company="Terry D. Eppler">

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
    staticmaps.py
  </summary>
  ******************************************************************************************
  '''
from typing import Optional, Dict
from urllib.parse import urlencode
if __package__:
	from .boogr import Error, Logger
else:
	from boogr import Error, Logger
if __package__:
	from . import config as cfg
else:
	import config as cfg

def throw_if( name: str, value: object ) -> None:
	"""Validate that a required static-map value is present.

	Purpose:
		Provides a lightweight guard for required Google Static Maps inputs before
		coordinate validation, point normalization, URL construction, and bounding-box
		generation. The function rejects missing objects and blank strings so map URL
		workflows fail before producing incomplete or ambiguous query parameters.

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

class StaticMap( ):
	"""Generate Google Static Maps URLs.

	Purpose:
		Builds embeddable Google Static Maps URLs for single-point previews,
		multi-marker previews, polyline paths, and rectangular bounding boxes. The
		class stores map URL parameters, marker state, coordinate state, map type,
		path styling, and bounding-box values so Streamlit workflows and reporting
		pages can render or inspect the latest generated static map request.

	Attributes:
		api_key: Google Maps Platform API key read from configuration.
		zoom: Zoom level used by the latest generated map URL.
		size: Static map image dimensions in ``WIDTHxHEIGHT`` format.
		latitude: Latitude from the latest validated coordinate.
		longitude: Longitude from the latest validated coordinate.
		params: Query parameters used to build the latest Static Maps URL.
		markers: Marker parameter value used by the latest single-pin URL.
		base_url: Google Static Maps endpoint URL.
		points: Validated coordinate points used by multi-pin, path, or box maps.
		maptype: Static map type such as ``roadmap`` or ``satellite``.
		color: Marker or path color used by the latest generated URL.
		weight: Path stroke weight used by the latest generated URL.
		west: Western longitude of the latest bounding box.
		south: Southern latitude of the latest bounding box.
		east: Eastern longitude of the latest bounding box.
		north: Northern latitude of the latest bounding box.
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
		"""Initialize the Static Maps URL builder.

		Purpose:
			Reads the Google Maps API key from configuration and initializes runtime
			state used by coordinate validation, marker generation, URL construction,
			path rendering, and bounding-box previews. The constructor performs local
			assignment only and prepares the object for later URL-building methods.
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
		"""Validate and normalize a coordinate pair.

		Purpose:
			Converts latitude and longitude inputs to floats and enforces valid
			geographic coordinate ranges before Static Maps URL parameters are built.
			The validated coordinate is stored on the instance for later map generation
			and inspection.

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
			exception.cause = 'StaticMap'
			exception.method = 'validate_coordinate( self, lat: float, lng: float ) -> tuple'
			Logger( ).write( exception )
			raise exception
	
	def normalize_points( self, points: list ) -> list:
		"""Normalize supported point shapes into coordinate tuples.

		Purpose:
			Accepts a list of coordinate tuples, coordinate lists, or dictionaries with
			``lat``/``lng`` or ``latitude``/``longitude`` fields and converts each item
			into a validated coordinate tuple. The normalized point list is stored on
			the instance for multi-pin, path, and bounding-box URL generation.

		Args:
			points: Coordinate items to normalize.

		Returns:
			list: Validated coordinate tuples.

		Raises:
			Error: Raised after logging when validation or normalization fails.
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
			exception.module = 'mappy'
			exception.cause = 'StaticMap'
			exception.method = 'normalize_points( self, points: list ) -> list'
			Logger( ).write( exception )
			raise exception
	
	def build_url( self, params: Dict ) -> str | None:
		"""Build a Google Static Maps URL.

		Purpose:
			Copies caller-supplied Static Maps query parameters, injects the configured
			Google Maps API key, stores the final parameter dictionary on the instance,
			and returns a fully qualified URL suitable for embedding in Streamlit,
			Markdown, reports, or browser links.

		Args:
			params: Google Static Maps query parameters.

		Returns:
			str | None: Fully qualified Google Static Maps URL.

		Raises:
			Error: Raised after logging when validation or URL construction fails.
		"""
		try:
			throw_if( 'params', params )
			params_value = dict( params or { } )
			params_value[ 'key' ] = self.api_key
			self.params = params_value
			return f'{self.base_url}?{urlencode( self.params, doseq=True )}'
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'StaticMap'
			exception.method = 'build_url( self, params: Dict ) -> str | None'
			Logger( ).write( exception )
			raise exception
	
	def pin( self, lat: float, lng: float, zoom: int = 12, size: int = '400x300' ) -> str | None:
		"""Build a single-marker Static Maps URL.

		Purpose:
			Validates a center coordinate, clamps the zoom level to the supported
			Static Maps range, stores marker and map state on the instance, and
			returns a URL centered on the coordinate with one marker.

		Args:
			lat: Latitude for the marker and map center.
			lng: Longitude for the marker and map center.
			zoom: Zoom level from 1 through 20.
			size: Static map image dimensions in ``WIDTHxHEIGHT`` format.

		Returns:
			str | None: Fully qualified Static Maps URL.

		Raises:
			Error: Raised after logging when validation or URL construction fails.
		"""
		try:
			latitude, longitude = self.validate_coordinate( lat, lng )
			zoom_value = max( 1, min( int( zoom or 12 ), 20 ) )
			size_value = size or '400x300'
			marker_value = f'{latitude},{longitude}'
			self.latitude = latitude
			self.longitude = longitude
			self.zoom = zoom_value
			self.size = size_value
			self.markers = marker_value
			self.params = {
					'center': f'{self.latitude},{self.longitude}',
					'zoom': str( self.zoom ),
					'size': self.size,
					'markers': self.markers
			}
			return self.build_url( self.params )
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'StaticMap'
			exception.method = 'pin( self, lat: float, lng: float, zoom: int=12, size: int=400x300 ) -> str | None'
			Logger( ).write( exception )
			raise exception
	
	def pins( self, points: list, zoom: int = 0, size: int = '600x400',
			maptype: int = 'roadmap', color: int = 'red' ) -> str | None:
		"""Build a multi-marker Static Maps URL.

		Purpose:
			Normalizes one or more coordinate points, validates the requested map type,
			builds marker parameters for each point, and returns a Static Maps URL. When
			``zoom`` is greater than zero, the map is centered on the average coordinate
			and the zoom is clamped. When ``zoom`` is zero, Google is allowed to fit the
			visible area to the supplied points.

		Args:
			points: Coordinate tuples, coordinate lists, or coordinate dictionaries.
			zoom: Zoom level. Use zero to omit explicit zoom and let Google fit bounds.
			size: Static map image dimensions in ``WIDTHxHEIGHT`` format.
			maptype: Map type: ``roadmap``, ``satellite``, ``terrain``, or ``hybrid``.
			color: Marker color.

		Returns:
			str | None: Fully qualified Static Maps URL.

		Raises:
			Error: Raised after logging when validation or URL construction fails.
		"""
		try:
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
			self.params = {
					'size': self.size,
					'maptype': self.maptype,
					'markers': marker_values
			}
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
			exception.module = 'mappy'
			exception.cause = 'StaticMapUrl'
			exception.method = 'pins( self, *args ) -> str | None'
			Logger( ).write( exception )
			raise exception
	
	def path( self, points: list, size: int = '600x400', maptype: int = 'roadmap',
			color: int = '0x0000ff', weight: int = 5 ) -> str | None:
		"""Build a Static Maps URL showing a path.

		Purpose:
			Normalizes two or more coordinate points, validates the requested map type,
			builds a Static Maps path parameter with configured color and stroke
			weight, adds start and end markers, and includes the path points as visible
			bounds so the generated image frames the route.

		Args:
			points: Coordinate tuples, coordinate lists, or coordinate dictionaries.
			size: Static map image dimensions in ``WIDTHxHEIGHT`` format.
			maptype: Map type: ``roadmap``, ``satellite``, ``terrain``, or ``hybrid``.
			color: Path color.
			weight: Path stroke weight.

		Returns:
			str | None: Fully qualified Static Maps URL.

		Raises:
			Error: Raised after logging when validation or URL construction fails.
		"""
		try:
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
			
			self.params = {
					'size': self.size,
					'maptype': self.maptype,
					'path': path_value,
					'markers': [
							f'color:green|{self.points[ 0 ][ 0 ]},{self.points[ 0 ][ 1 ]}',
							f'color:red|{self.points[ -1 ][ 0 ]},{self.points[ -1 ][ 1 ]}'
					],
					'visible': path_points
			}
			
			return self.build_url( self.params )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'StaticMap'
			exception.method = 'path( self, points: list, size: int=600x400 ) -> str | None'
			Logger( ).write( exception )
			raise exception
	
	def bbox( self, west: float, south: float, east: float, north: float,
			size: int = '600x400', maptype: int = 'roadmap' ) -> str | None:
		"""Build a Static Maps URL showing a bounding box.

		Purpose:
			Validates bounding-box edges, converts them into southwest, northwest,
			northeast, southeast, and closing southwest coordinates, stores the box
			state on the instance, and delegates to ``path`` to render the rectangle
			as a red outline on a Static Maps image.

		Args:
			west: Western longitude.
			south: Southern latitude.
			east: Eastern longitude.
			north: Northern latitude.
			size: Static map image dimensions in ``WIDTHxHEIGHT`` format.
			maptype: Map type: ``roadmap``, ``satellite``, ``terrain``, or ``hybrid``.

		Returns:
			str | None: Fully qualified Static Maps URL.

		Raises:
			Error: Raised after logging when validation or URL construction fails.
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
			
			return self.path(
				points=self.points,
				size=self.size,
				maptype=self.maptype,
				color='0xff0000',
				weight=3 )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'StaticMap'
			exception.method = 'bbox( self, west: float, south: float, east: float, north: float ) -> str | None'
			Logger( ).write( exception )
			raise exception