
from __future__ import annotations

from bs4 import BeautifulSoup
from collections import deque, Counter
from exceptions import NotFound
from boogr import Error
import html as html_lib
import json
import os
from typing import Optional
import matplotlib
import pandas as pd
import plotly.graph_objects as go
import pydeck as pdk
import streamlit as st
import streamlit.components.v1 as components
from streamlit_js_eval import get_geolocation
import sqlite3
import re
import datetime as dt
from typing import Optional
import time
from urllib.parse import urljoin, urlparse
from pathlib import Path
import config as cfg
from maps import Maps
from typing import Any, Optional, Dict, List, Tuple
from geocode import Geocoder
from places import Place
from distances import DistanceMatrix
from timezones import Timezone
from staticmaps import StaticMap
from excel import Excel
from caches import InMemoryCache, SQLiteCache
from generators import Chat, Claude, Grok, Mistral, Gemini
from fetchers import (
	GoogleWeather,
	OpenWeather,
	HistoricalWeather,
	ClimateData,
	TidesAndCurrents,
	AirNow,
	UvIndex,
	OpenAQ,
	PurpleAir,
	EnviroFacts,
	Firms,
	EoNet,
	USGSEarthquakes,
	USGSWaterData,
	USGSTheNationalMap,
	GlobalImagery,
	NavalObservatory,
	SatelliteCenter,
	SpaceWeather,
	AstroCatalog,
	AstroQuery,
	StarMap,
	StarChart,
	WebCrawler,
	WebFetcher )

# ---------------------------------------------------------------------
# SESSION STATE INITIALIZATION
# ---------------------------------------------------------------------

# ------- Data State

if 'source' not in st.session_state:
	st.session_state[ 'source' ]= ''

if 'df_source' not in st.session_state:
	st.session_state[ 'df_source' ] = pd.DataFrame( )

if 'df_frame' not in st.session_state:
	st.session_state[ 'df_frame' ] = pd.DataFrame( )

if 'df_default' not in st.session_state:
	st.session_state[ 'df_default' ] = pd.DataFrame( )

if 'df_original' not in st.session_state:
	st.session_state[ 'df_original' ] = pd.DataFrame( )

if 'df_raw' not in st.session_state:
	st.session_state[ 'df_raw' ] = pd.DataFrame( )

if 'df_dataset' not in st.session_state:
	st.session_state[ 'df_dataset' ] = pd.DataFrame( )

if 'df_reports_geocode_preview' not in st.session_state:
	st.session_state[ 'df_reports_geocode_preview' ] = pd.DataFrame( )

if 'df_geocoding_map_results' not in st.session_state:
	st.session_state[ 'df_geocoding_map_results' ] = pd.DataFrame( )

if 'pipeline_log' not in st.session_state:
	st.session_state[ 'pipeline_log' ] = [ ]

# -------- GENERATIVE AI VARIABLES --------------------

if 'model' not in st.session_state:
	st.session_state[ 'model' ] = ''

if 'max_tools' not in st.session_state:
	st.session_state[ 'max_tools' ] = 0

if 'max_tokens' not in st.session_state:
	st.session_state[ 'max_tokens' ] = 0

if 'temperature' not in st.session_state:
	st.session_state[ 'temperature' ] = 0.0

if 'top_percent' not in st.session_state:
	st.session_state[ 'top_percent' ] = 0.0

if 'frequency_penalty' not in st.session_state:
	st.session_state[ 'frequency_penalty' ] = 0.0

if 'presense_penalty' not in st.session_state:
	st.session_state[ 'presense_penalty' ] = 0.0

if 'background' not in st.session_state:
	st.session_state[ 'background' ] = False

if 'parallel_tools' not in st.session_state:
	st.session_state[ 'parallel_tools' ] = False

if 'store' not in st.session_state:
	st.session_state[ 'store' ] = False

if 'stream' not in st.session_state:
	st.session_state[ 'stream' ] = False

if 'response_format' not in st.session_state:
	st.session_state[ 'response_format' ] = ''

if 'tool_choice' not in st.session_state:
	st.session_state[ 'tool_choice' ] = ''

if 'reasoning' not in st.session_state:
	st.session_state[ 'reasoning' ] = ''

if 'stops' not in st.session_state:
	st.session_state[ 'stops' ] = [ ]

if 'include' not in st.session_state:
	st.session_state[ 'include' ] = [ ]

if 'input' not in st.session_state:
	st.session_state[ 'input' ] = [ ]

if 'tools' not in st.session_state:
	st.session_state[ 'tools' ] = [ ]

if 'messages' not in st.session_state:
	st.session_state[ 'messages' ] = [ ]

# ------- Mappy State

if 'mode' not in st.session_state:
	st.session_state[ 'mode' ] = 'Geocoding'

if 'previous_mode' not in st.session_state:
	st.session_state[ 'previous_mode' ] = ''

if 'timezone' not in st.session_state:
	st.session_state[ 'timezone' ] = dt.timezone

if 'distances' not in st.session_state:
	st.session_state[ 'distances' ] = None

if 'geocoder' not in st.session_state:
	st.session_state[ 'geocoder' ] = None

if 'places' not in st.session_state:
	st.session_state[ 'places' ] = None

if 'static_maps' not in st.session_state:
	st.session_state[ 'static_maps' ] = None

if 'qps' not in st.session_state:
	st.session_state[ 'qps' ] = 10

# ------------ Location State

if 'coordinates' not in st.session_state:
	st.session_state[ 'coordinates' ] = ( )

if 'latitude' not in st.session_state:
	st.session_state[ 'latitude' ] = 0.0

if 'longitude' not in st.session_state:
	st.session_state[ 'longitude' ] = 0.0

if 'location' not in st.session_state:
	st.session_state[ 'location' ] = ''

if 'country' not in st.session_state:
	st.session_state[ 'country' ] = ''

if 'state' not in st.session_state:
	st.session_state[ 'state' ] = ''

if 'city' not in st.session_state:
	st.session_state[ 'city' ] = ''

if 'zipcode' not in st.session_state:
	st.session_state[ 'zipcode' ] = ''

if 'description' not in st.session_state:
	st.session_state[ 'description' ] = ''

if 'origin' not in st.session_state:
	st.session_state[ 'origin' ] = ''

if 'destination' not in st.session_state:
	st.session_state[ 'destination' ] = ''

if 'radius' not in st.session_state:
	st.session_state[ 'radius' ] = 25.0

if 'zoom' not in st.session_state:
	st.session_state[ 'zoom' ] = 8

if 'map_size' not in st.session_state:
	st.session_state[ 'map_size' ] = '600x400'

if 'year' not in st.session_state:
	st.session_state[ 'year' ] = dt.datetime.now( ).year

if 'month' not in st.session_state:
	st.session_state[ 'month' ] = dt.datetime.now( ).month

if 'day' not in st.session_state:
	st.session_state[ 'day' ] = dt.datetime.now( ).day

if 'calendar_date' not in st.session_state:
	st.session_state[ 'calendar_date' ] = dt.date.today( )

if 'browser_geolocation' not in st.session_state:
	st.session_state[ 'browser_geolocation' ] = None

if 'browser_geolocation_loaded' not in st.session_state:
	st.session_state[ 'browser_geolocation_loaded' ] = False

if 'browser_geolocation_enabled' not in st.session_state:
	st.session_state[ 'browser_geolocation_enabled' ] = True

if 'browser_geolocation_reverse_geocoded' not in st.session_state:
	st.session_state[ 'browser_geolocation_reverse_geocoded' ] = False

if 'browser_geolocation_error' not in st.session_state:
	st.session_state[ 'browser_geolocation_error' ] = ''

if 'browser_geolocation_permission_denied' not in st.session_state:
	st.session_state[ 'browser_geolocation_permission_denied' ] = False

# ------- API Key State

if 'google_api_key' not in st.session_state:
	st.session_state[ 'google_api_key' ] = ''

if 'google_cse_id' not in st.session_state:
	st.session_state[ 'google_cse_id' ] = ''

if 'googlemaps_api_key' not in st.session_state:
	st.session_state[ 'googlemaps_api_key' ] = ''

if 'geocoding_api_key' not in st.session_state:
	st.session_state[ 'geocoding_api_key' ] = ''

if 'google_cloud_project_id' not in st.session_state:
	st.session_state[ 'google_cloud_project_id' ] = ''

if 'google_cloud_location' not in st.session_state:
	st.session_state[ 'google_cloud_location' ] = ''

if 'google_weather_api_key' not in st.session_state:
	st.session_state[ 'google_weather_api_key' ] = ''

if 'govinfo_api_key' not in st.session_state:
	st.session_state[ 'govinfo_api_key' ] = ''

if 'nasa_api_key' not in st.session_state:
	st.session_state[ 'nasa_api_key' ] = ''

if 'airnow_api_key' not in st.session_state:
	st.session_state[ 'airnow_api_key' ] = ''

if 'openaq_api_key' not in st.session_state:
	st.session_state[ 'openaq_api_key' ] = ''

if 'nasa_earthdata_token' not in st.session_state:
	st.session_state[ 'nasa_earthdata_token' ] = ''

if 'opensky_api_client_id' not in st.session_state:
	st.session_state[ 'opensky_api_client_id' ] = ''

if 'firms_map_key' not in st.session_state:
	st.session_state[ 'firms_map_key' ] = ''

if 'opensky_api_credentials' not in st.session_state:
	st.session_state[ 'opensky_api_credentials' ] = ''

if 'purpleair_api_key' not in st.session_state:
	st.session_state[ 'purpleair_api_key' ] = ''

if 'openai_api_key' not in st.session_state:
	st.session_state[ 'openai_api_key' ] = ''

if 'gemini_api_key' not in st.session_state:
	st.session_state[ 'gemini_api_key' ] = ''

if 'claude_api_key' not in st.session_state:
	st.session_state[ 'claude_api_key' ] = ''

if 'mistral_api_key' not in st.session_state:
	st.session_state[ 'mistral_api_key' ] = ''

if 'xai_api_key' not in st.session_state:
	st.session_state[ 'xai_api_key' ] = ''

if st.session_state.google_api_key == '':
	default = cfg.GOOGLE_API_KEY
	if default:
		st.session_state.google_api_key = default
		os.environ[ 'GOOGLE_API_KEY' ] = default

if st.session_state.google_cse_id == '':
	default = cfg.GOOGLE_CSE_ID
	if default:
		st.session_state.google_cse_id = default
		os.environ[ 'GOOGLE_CSE_ID' ] = default

if st.session_state.googlemaps_api_key == '':
	default = cfg.GOOGLEMAPS_API_KEY
	if default:
		st.session_state.googlemaps_api_key = default
		os.environ[ 'GOOGLEMAPS_API_KEY' ] = default

if st.session_state.geocoding_api_key == '':
	default = cfg.GEOCODING_API_KEY
	if default:
		st.session_state.geocoding_api_key = default
		os.environ[ 'GEOCODING_API_KEY' ] = default

if st.session_state.google_cloud_project_id == '':
	default = cfg.GOOGLE_CLOUD_PROJECT_ID
	if default:
		st.session_state.google_cloud_project_id = default
		os.environ[ 'GOOGLE_CLOUD_PROJECT_ID' ] = default

if st.session_state.google_cloud_location == '':
	default = cfg.GOOGLE_CLOUD_LOCATION
	if default:
		st.session_state.google_cloud_location = default
		os.environ[ 'GOOGLE_CLOUD_LOCATION' ] = default

if st.session_state.google_weather_api_key == '':
	default = cfg.GOOGLE_WEATHER_API_KEY
	if default:
		st.session_state.google_weather_api_key = default
		os.environ[ 'GOOGLE_WEATHER_API_KEY' ] = default

if st.session_state.govinfo_api_key == '':
	default = cfg.GOVINFO_API_KEY
	if default:
		st.session_state.govinfo_api_key = default
		os.environ[ 'GOVINFO_API_KEY' ] = default

if st.session_state.nasa_api_key == '':
	default = cfg.NASA_API_KEY
	if default:
		st.session_state.nasa_api_key = default
		os.environ[ 'NASA_API_KEY' ] = default

if st.session_state.airnow_api_key == '':
	default = cfg.AIRNOW_API_KEY
	if default:
		st.session_state.airnow_api_key = default
		os.environ[ 'AIRNOW_API_KEY' ] = default

if st.session_state.openaq_api_key == '':
	default = cfg.OPENAQ_API_KEY
	if default:
		st.session_state.openaq_api_key = default
		os.environ[ 'OPENAQ_API_KEY' ] = default

if st.session_state.nasa_earthdata_token == '':
	default = cfg.NASA_EARTHDATA_TOKEN
	if default:
		st.session_state.nasa_earthdata_token = default
		os.environ[ 'NASA_EARTHDATA_TOKEN' ] = default

if st.session_state.opensky_api_client_id == '':
	default = cfg.OPENSKY_API_CLIENT_ID
	if default:
		st.session_state.opensky_api_client_id = default
		os.environ[ 'OPENSKY_API_CLIENT_ID' ] = default

if st.session_state.firms_map_key == '':
	default = cfg.FIRMS_MAP_KEY
	if default:
		st.session_state.firms_map_key = default
		os.environ[ 'FIRMS_MAP_KEY' ] = default

if st.session_state.opensky_api_credentials == '':
	default = cfg.OPENSKY_API_CREDENTIALS
	if default:
		st.session_state.opensky_api_credentials = default
		os.environ[ 'OPENSKY_API_CREDENTIALS' ] = default

if st.session_state.purpleair_api_key == '':
	default = getattr( cfg, 'PURPLEAIR_API_KEY', '' )
	if default:
		st.session_state.purpleair_api_key = default
		os.environ[ 'PURPLEAIR_API_KEY' ] = default

if st.session_state.openai_api_key == '':
	default = getattr( cfg, 'OPENAI_API_KEY', '' )
	if default:
		st.session_state.openai_api_key = default
		os.environ[ 'OPENAI_API_KEY' ] = default

if st.session_state.claude_api_key == '':
	default = getattr( cfg, 'CLAUDE_API_KEY', '' )
	if default:
		st.session_state.claude_api_key = default
		os.environ[ 'CLAUDE_API_KEY' ] = default

if st.session_state.gemini_api_key == '':
	default = getattr( cfg, 'GEMINI_API_KEY', '' )
	if default:
		st.session_state.gemini_api_key = default
		os.environ[ 'GEMINI_API_KEY' ] = default

if st.session_state.mistral_api_key == '':
	default = getattr( cfg, 'MISTRAL_API_KEY', '' )
	if default:
		st.session_state.mistral_api_key = default
		os.environ[ 'MISTRAL_API_KEY' ] = default

if st.session_state.xai_api_key == '':
	default = getattr( cfg, 'XAI_API_KEY', '' )
	if default:
		st.session_state.xai_api_key = default
		os.environ[ 'XAI_API_KEY' ] = default

# ---------------------------------------------------------------------
# UTILITIES
# ---------------------------------------------------------------------

def throw_if( name: str, value: object ) -> None:
	"""Validate that a required value is present.
	
	Purpose:
		Raises a clear validation error when a required argument is missing, blank, or
		empty. The helper is used by Streamlit utilities and data workflows before values
		are consumed by UI, database, or service logic.
	
	Args:
		name: str value used by the `throw_if` workflow.
		value: object value used by the `throw_if` workflow.
	
	Raises:
		Exception: Propagates validation, UI, data, database, or provider errors
			raised by the existing implementation.
	"""
	if value is None:
		raise ValueError( f'Argument "{name}" cannot be empty!' )
	
	if isinstance( value, str ) and not value.strip( ):
		raise ValueError( f'Argument "{name}" cannot be empty!' )
	
	if isinstance( value, (list, tuple, dict, set) ) and len( value ) == 0:
		raise ValueError( f'Argument "{name}" cannot be empty!' )

def style_subheaders( ) -> None:
	"""Handle the style subheaders workflow.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the style subheaders
		workflow. The function preserves the existing UI behavior, session-state
		interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	"""
	st.markdown(
		"""
		<style>
		div[data-testid="stMarkdownContainer"] h2,
		div[data-testid="stMarkdownContainer"] h3,
		div[data-testid="stChatMessage"] div[data-testid="stMarkdownContainer"] h2,
		div[data-testid="stChatMessage"] div[data-testid="stMarkdownContainer"] h3 {
			color: rgb(0, 120, 252) !important;
		}
		</style>
		""",
		unsafe_allow_html=True, )

def init_state( key: str, value: Any ) -> None:
	"""Handle the init state workflow.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the init state workflow. The
		function preserves the existing UI behavior, session-state interactions, dataframe
		handling, database access, and service integrations defined by the application
		code.
	
	Args:
		key: str value used by the `init_state` workflow.
		value: Any value used by the `init_state` workflow.
	"""
	if key not in st.session_state:
		st.session_state[ key ] = value

def init_env_state( key: str, config_name: str, env_name: str ) -> None:
	"""Handle the init env state workflow.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the init env state workflow.
		The function preserves the existing UI behavior, session-state interactions,
		dataframe handling, database access, and service integrations defined by the
		application code.
	
	Args:
		key: str value used by the `init_env_state` workflow.
		config_name: str value used by the `init_env_state` workflow.
		env_name: str value used by the `init_env_state` workflow.
	"""
	init_state( key, '' )
	if st.session_state.get( key, '' ) == '':
		default = getattr( cfg, config_name, '' )
		if default:
			st.session_state[ key ] = default
			os.environ[ env_name ] = default

def normalize( obj: str ) -> str:
	"""Handle the normalize workflow.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the normalize workflow. The
		function preserves the existing UI behavior, session-state interactions, dataframe
		handling, database access, and service integrations defined by the application
		code.
	
	Args:
		obj: str Runtime value used by the `normalize` workflow.
	
	Returns:
		str: Result produced by the `normalize` workflow.
	"""
	if obj is None or isinstance( obj, (str, int, float, bool) ):
		return obj
	
	if isinstance( obj, dict ):
		return { k: normalize( v ) for k, v in obj.items( ) }
	
	if isinstance( obj, (list, tuple, set) ):
		return [ normalize( v ) for v in obj ]
	if hasattr( obj, "model_dump" ):
		try:
			return obj.model_dump( )
		except Exception:
			return str( obj )
	return str( obj )

def set_blue_divider( ) -> None:
	"""Set the blue divider used by the application.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the set blue divider
		workflow. The function preserves the existing UI behavior, session-state
		interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	"""
	st.markdown( cfg.BLUE_DIVIDER, unsafe_allow_html=True )

def log_step( msg: str ) -> None:
	"""Handle the log step workflow.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the log step workflow. The
		function preserves the existing UI behavior, session-state interactions, dataframe
		handling, database access, and service integrations defined by the application
		code.
	
	Args:
		msg: str value used by the `log_step` workflow.
	"""
	st.session_state.pipeline_log.append( msg )

# ------------- CELESTIAL MAP UTILITY

def render_celestial_map( asset_root: str = 'assets/starmap', height: int = 1400,
		latitude: Optional[ float ] = None, longitude: Optional[ float ] = None,
		tile_url: Optional[ str ] = None, tile_attribution: Optional[ str ] = None,
		tile_subdomains: Optional[ str ] = None, location: Optional[ str ] = None,
		zoom: Optional[ int ] = None ) -> None:
	"""Render the celestial map interface section.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the render celestial map
		workflow. The function preserves the existing UI behavior, session-state
		interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	
	Args:
		asset_root: str value used by the `render_celestial_map` workflow. Defaults to
			`'assets/starmap'`.
		height: int value used by the `render_celestial_map` workflow. Defaults to `1400`.
		latitude: Optional[float] value used by the `render_celestial_map` workflow. Defaults to
			`None`.
		longitude: Optional[float] value used by the `render_celestial_map` workflow. Defaults to
			`None`.
		tile_url: Optional[str] value used by the `render_celestial_map` workflow. Defaults to
			`None`.
		tile_attribution: Optional[str] value used by the `render_celestial_map` workflow. Defaults to
			`None`.
		tile_subdomains: Optional[str] value used by the `render_celestial_map` workflow. Defaults to
			`None`.
		location: Optional[str] value used by the `render_celestial_map` workflow. Defaults to
			`None`.
		zoom: Optional[int] value used by the `render_celestial_map` workflow. Defaults to
			`None`.
	"""
	try:
		root = Path( asset_root )
		index_path = root / 'index.html'
		style_path = root / 'style.css'
		data_paths = {
				'constellations': root / 'data' / 'constellations.json',
				'lines': root / 'data' / 'constellations.lines.json',
				'stars': root / 'data' / 'stars.6.json',
				'dsos': root / 'data' / 'dsos.bright.json',
				'starnames': root / 'data' / 'starnames.json',
				'planets': root / 'data' / 'planets.json',
				'mw': root / 'data' / 'mw.json',
				'constellationBorders': root / 'data' / 'constellations.borders.json',
				'dsonames': root / 'data' / 'dsonames.json',
		}
		
		module_paths = [
				root / 'js' / 'modules' / 'CelestialMath.js',
				root / 'js' / 'modules' / 'StarData.js',
				root / 'js' / 'modules' / 'MapRenderer.js',
				root / 'js' / 'modules' / 'LocationPicker.js',
				root / 'js' / 'modules' / 'UIController.js',
				root / 'js' / 'modules' / 'StarDetailsPanel.js',
				root / 'js' / 'modules' / 'ImageExporter.js',
				root / 'js' / 'main.js', ]
		
		required_paths = [ index_path, style_path, *data_paths.values( ), *module_paths ]
		missing_paths = [ str( path ) for path in required_paths if not path.exists( ) ]
		if missing_paths:
			st.error( 'Celestial Map assets are missing.' )
			st.code( '\n'.join( missing_paths ) )
			return
		
		html = index_path.read_text( encoding='utf-8' )
		css = style_path.read_text( encoding='utf-8' )
		local_data: Dict[ str, object ] = { }
		for key, path in data_paths.items( ):
			local_data[ key ] = json.loads( path.read_text( encoding='utf-8' ) )
		
		if has_valid_coordinates( latitude, longitude ):
			default_latitude = float( latitude )
			default_longitude = float( longitude )
		else:
			default_latitude = get_default_latitude( )
			default_longitude = get_default_longitude( )
		
		if location is not None and str( location ).strip( ):
			default_location = str( location ).strip( )
		else:
			default_location = get_default_location( )
		
		default_zoom = int( zoom if zoom is not None else st.session_state.get( 'zoom', 8 ) or 8 )
		default_payload = {
				'latitude': default_latitude,
				'longitude': default_longitude,
				'location': default_location,
				'zoom': default_zoom,
				'tileUrl': (
						'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
				),
				'tileAttribution': (
						'&copy; OpenStreetMap contributors &copy; CARTO'
				),
				'tileSubdomains': 'abcd',
		}
		
		html = html.replace(
			'<link rel="stylesheet" href="style.css">',
			f'<style>\n{css}\n</style>' )
		
		for relative_path in [
				'js/modules/CelestialMath.js',
				'js/modules/StarData.js',
				'js/modules/MapRenderer.js',
				'js/modules/LocationPicker.js',
				'js/modules/UIController.js',
				'js/modules/StarDetailsPanel.js',
				'js/modules/ImageExporter.js',
				'js/main.js',
		]:
			html = re.sub( rf'\s*<script\s+src="{re.escape( relative_path )}"></script>',
				'', html, flags=re.IGNORECASE )
		
		data_script = ('<script>\n'
		               'window.StarMapApp = window.StarMapApp || {};\n'
		               f'window.StarMapApp.LOCAL_DATA = {json.dumps( local_data )};\n'
		               f'window.StarMapApp.DEFAULT_LOCATION = {json.dumps( default_payload )};\n'
		               '</script>')
		
		inline_scripts = [ data_script ]
		for path in module_paths:
			source = path.read_text( encoding='utf-8' )
			if path.name == 'main.js':
				source = source.replace(
					"this.locationPicker = new LocationPicker('locationPicker', {\n"
					"                onLocationChange: (lat, lon) => this.handleLocationChange(lat, lon)\n"
					"            });",
					"const defaultLocation = window.StarMapApp.DEFAULT_LOCATION || {};\n"
					"            this.locationPicker = new LocationPicker('locationPicker', {\n"
					"                initialLat: defaultLocation.latitude,\n"
					"                initialLon: defaultLocation.longitude,\n"
					"                onLocationChange: (lat, lon) => this.handleLocationChange(lat, lon)\n"
					"            });" )
				
				source = source.replace(
					"this.selectedCoords = { lat: 30.0444, lon: 31.2357 };",
					"this.selectedCoords = {\n"
					"                lat: Number(defaultLocation.latitude || 30.0444),\n"
					"                lon: Number(defaultLocation.longitude || 31.2357)\n"
					"            };" )
				
				source = source.replace(
					"this.locationPicker.setView(this.selectedCoords.lat, this.selectedCoords.lon);",
					"this.locationPicker.setView(\n"
					"                    this.selectedCoords.lat,\n"
					"                    this.selectedCoords.lon,\n"
					"                    Number(defaultLocation.zoom || 8)\n"
					"                );\n"
					"                this.ui.updateLocationDisplay(\n"
					"                    this.selectedCoords.lat,\n"
					"                    this.selectedCoords.lon\n"
					"                );" )
			
			inline_scripts.append( f'<script>\n{source}\n</script>' )
		
		local_data_override = """
		<script>
		(function () {
		    window.StarMapApp = window.StarMapApp || {};
		
		    if (!window.StarMapApp.StarData || !window.StarMapApp.LOCAL_DATA) {
		        return;
		    }
		
		    window.StarMapApp.StarData.prototype.load = async function () {
		        this.data = window.StarMapApp.LOCAL_DATA;
		        return this.data;
		    };
		})();
		</script>
		"""
		
		inline_scripts.append( local_data_override )
		html = html.replace( '</body>', '\n'.join( inline_scripts ) + '\n</body>' )
		components.html( html, height=int( height ), scrolling=True )
	except Exception as ex:
		st.error( f'Celestial Map failed to render: {ex}' )

# ------------- LOCATION STATE UTILITIES

def has_valid_coordinates( latitude: object, longitude: object ) -> bool:
	"""Handle the has valid coordinates workflow.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the has valid coordinates
		workflow. The function preserves the existing UI behavior, session-state
		interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	
	Args:
		latitude: object value used by the `has_valid_coordinates` workflow.
		longitude: object value used by the `has_valid_coordinates` workflow.
	
	Returns:
		bool: Result produced by the `has_valid_coordinates` workflow.
	"""
	try:
		throw_if( 'latitude', latitude )
		throw_if( 'longitude', longitude )
		lat_value = float( latitude )
		lon_value = float( longitude )
	except Exception:
		return False
	
	if not (-90.0 <= lat_value <= 90.0):
		return False
	
	if not (-180.0 <= lon_value <= 180.0):
		return False
	
	if lat_value == 0.0 and lon_value == 0.0:
		return False
	
	return True

def has_valid_global_coordinates( ) -> bool:
	"""Handle the has valid global coordinates workflow.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the has valid global
		coordinates workflow. The function preserves the existing UI behavior, session-
		state interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	
	Returns:
		bool: Result produced by the `has_valid_global_coordinates` workflow.
	"""
	return has_valid_coordinates(
		st.session_state.get( 'latitude', None ),
		st.session_state.get( 'longitude', None ) )

def set_coordinates( latitude: object, longitude: object ) -> None:
	"""Set the coordinates used by the application.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the set coordinates
		workflow. The function preserves the existing UI behavior, session-state
		interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	
	Args:
		latitude: object value used by the `set_coordinates` workflow.
		longitude: object value used by the `set_coordinates` workflow.
	"""
	if not has_valid_coordinates( latitude, longitude ):
		return
	
	lat_value = float( latitude )
	lon_value = float( longitude )
	
	st.session_state[ 'latitude' ] = lat_value
	st.session_state[ 'longitude' ] = lon_value
	st.session_state[ 'coordinates' ] = (lat_value, lon_value)

def get_location_state( ) -> Dict[ str, object ]:
	"""Return the location state used by the application.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the get location state
		workflow. The function preserves the existing UI behavior, session-state
		interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	
	Returns:
		Dict[str, object]: Result produced by the `get_location_state` workflow.
	"""
	return { 'coordinates': st.session_state.get( 'coordinates', ( ) ),
	         'latitude': st.session_state.get( 'latitude', 0.0 ),
	         'longitude': st.session_state.get( 'longitude', 0.0 ),
	         'location': st.session_state.get( 'location', '' ),
	         'country': st.session_state.get( 'country', '' ),
	         'state': st.session_state.get( 'state', '' ),
	         'city': st.session_state.get( 'city', '' ),
	         'zipcode': st.session_state.get( 'zipcode', '' ),
	         'description': st.session_state.get( 'description', '' ),
	         'origin': st.session_state.get( 'origin', '' ),
	         'destination': st.session_state.get( 'destination', '' ),
	         'radius': st.session_state.get( 'radius', 25.0 ),
	         'zoom': st.session_state.get( 'zoom', 8 ),
	         'map_size': st.session_state.get( 'map_size', '600x400' ),
	         'year': st.session_state.get( 'year', dt.datetime.now( ).year ),
	         'month': st.session_state.get( 'month', dt.datetime.now( ).month ),
	         'day': st.session_state.get( 'day', dt.datetime.now( ).day ),
	         'calendar_date': st.session_state.get( 'calendar_date', dt.date.today( ) ),
	         }

def set_location_state( location: Optional[ str ] = None, city: Optional[ str ] = None,
		state: Optional[ str ] = None, country: Optional[ str ] = None,
		zipcode: Optional[ str ] = None, description: Optional[ str ] = None,
		latitude: Optional[ float ] = None, longitude: Optional[ float ] = None ) -> None:
	"""Set the location state used by the application.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the set location state
		workflow. The function preserves the existing UI behavior, session-state
		interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	
	Args:
		location: Optional[str] value used by the `set_location_state` workflow. Defaults to
			`None`.
		city: Optional[str] value used by the `set_location_state` workflow. Defaults to
			`None`.
		state: Optional[str] value used by the `set_location_state` workflow. Defaults to
			`None`.
		country: Optional[str] value used by the `set_location_state` workflow. Defaults to
			`None`.
		zipcode: Optional[str] value used by the `set_location_state` workflow. Defaults to
			`None`.
		description: Optional[str] value used by the `set_location_state` workflow. Defaults to
			`None`.
		latitude: Optional[float] value used by the `set_location_state` workflow. Defaults to
			`None`.
		longitude: Optional[float] value used by the `set_location_state` workflow. Defaults to
			`None`.
	"""
	if location is not None:
		st.session_state[ 'location' ] = str( location ).strip( )
	
	if city is not None:
		st.session_state[ 'city' ] = str( city ).strip( )
	
	if state is not None:
		st.session_state[ 'state' ] = str( state ).strip( )
	
	if country is not None:
		st.session_state[ 'country' ] = str( country ).strip( )
	
	if zipcode is not None:
		st.session_state[ 'zipcode' ] = str( zipcode ).strip( )
	
	if description is not None:
		st.session_state[ 'description' ] = str( description ).strip( )
	
	if latitude is not None and longitude is not None:
		set_coordinates( latitude, longitude )

def compose_location_from_state( ) -> str:
	"""Handle the compose location from state workflow.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the compose location from
		state workflow. The function preserves the existing UI behavior, session-state
		interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	
	Returns:
		str: Result produced by the `compose_location_from_state` workflow.
	"""
	location = str( st.session_state.get( 'location', '' ) ).strip( )
	if location:
		return location
	
	parts = [ ]
	
	for key in [ 'city', 'state', 'zipcode', 'country' ]:
		value = st.session_state.get( key, '' )
		text = str( value ).strip( )
		
		if text and text.lower( ) not in [ 'nan', 'none', 'null' ]:
			parts.append( text )
	
	return ', '.join( parts )

def resolve_table_name( requested: str, tables: List[ str ] ) -> Optional[ str ]:
	"""Handle the resolve table name workflow.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the resolve table name
		workflow. The function preserves the existing UI behavior, session-state
		interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	
	Args:
		requested: str value used by the `resolve_table_name` workflow.
		tables: List[str] value used by the `resolve_table_name` workflow.
	
	Returns:
		Optional[str]: Result produced by the `resolve_table_name` workflow.
	"""
	if not requested or not tables:
		return None
	
	for table in tables:
		if table == requested:
			return table
	
	requested_lower = requested.lower( )
	for table in tables:
		if str( table ).lower( ) == requested_lower:
			return table
	
	return None

def get_default_location( fallback: str = 'Washington, DC' ) -> str:
	"""Return the default location used by the application.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the get default location
		workflow. The function preserves the existing UI behavior, session-state
		interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	
	Args:
		fallback: str value used by the `get_default_location` workflow. Defaults to
			`'Washington, DC'`.
	
	Returns:
		str: Result produced by the `get_default_location` workflow.
	"""
	location = compose_location_from_state( )
	if location:
		return location
	
	return fallback

def get_default_zipcode( fallback: str = '20001' ) -> str:
	"""Return the default zipcode used by the application.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the get default zipcode
		workflow. The function preserves the existing UI behavior, session-state
		interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	
	Args:
		fallback: str value used by the `get_default_zipcode` workflow. Defaults to `'20001'`.
	
	Returns:
		str: Result produced by the `get_default_zipcode` workflow.
	"""
	zipcode = str( st.session_state.get( 'zipcode', '' ) ).strip( )
	if zipcode:
		return zipcode
	
	return fallback

def get_default_latitude( fallback: float = 38.907200 ) -> float:
	"""Return the default latitude used by the application.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the get default latitude
		workflow. The function preserves the existing UI behavior, session-state
		interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	
	Args:
		fallback: float value used by the `get_default_latitude` workflow. Defaults to
			`38.9072`.
	
	Returns:
		float: Result produced by the `get_default_latitude` workflow.
	"""
	if has_valid_global_coordinates( ):
		return float( st.session_state.get( 'latitude', fallback ) )
	
	return float( fallback )

def get_default_longitude( fallback: float = -77.036900 ) -> float:
	"""Return the default longitude used by the application.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the get default longitude
		workflow. The function preserves the existing UI behavior, session-state
		interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	
	Args:
		fallback: float value used by the `get_default_longitude` workflow. Defaults to
			`-77.0369`.
	
	Returns:
		float: Result produced by the `get_default_longitude` workflow.
	"""
	if has_valid_global_coordinates( ):
		return float( st.session_state.get( 'longitude', fallback ) )
	
	return float( fallback )

def set_global_coordinates_from_result( latitude: object, longitude: object,
		location: Optional[ str ] = None, description: Optional[ str ] = None ) -> None:
	"""Set the global coordinates from result used by the application.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the set global coordinates
		from result workflow. The function preserves the existing UI behavior, session-
		state interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	
	Args:
		latitude: object value used by the `set_global_coordinates_from_result` workflow.
		longitude: object value used by the `set_global_coordinates_from_result` workflow.
		location: Optional[str] value used by the `set_global_coordinates_from_result` workflow.
			Defaults to `None`.
		description: Optional[str] value used by the `set_global_coordinates_from_result` workflow.
			Defaults to `None`.
	"""
	if not has_valid_coordinates( latitude, longitude ):
		return
	
	set_location_state(
		location=location,
		description=description,
		latitude=float( latitude ),
		longitude=float( longitude ) )

def create_bounding_box_from_center( latitude: object, longitude: object,
		delta: float = 0.125 ) -> Dict[ str, float ]:
	"""Create the bounding box from center used by the application.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the create bounding box from
		center workflow. The function preserves the existing UI behavior, session-state
		interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	
	Args:
		latitude: object value used by the `create_bounding_box_from_center` workflow.
		longitude: object value used by the `create_bounding_box_from_center` workflow.
		delta: float value used by the `create_bounding_box_from_center` workflow. Defaults
			to `0.125`.
	
	Returns:
		Dict[str, float]: Result produced by the `create_bounding_box_from_center`
			workflow.
	"""
	lat_value = get_default_latitude( )
	lng_value = get_default_longitude( )
	
	if has_valid_coordinates( latitude, longitude ):
		lat_value = float( latitude )
		lng_value = float( longitude )
	
	return {
			'west': lng_value - float( delta ),
			'south': lat_value - float( delta ),
			'east': lng_value + float( delta ),
			'north': lat_value + float( delta ),
			'nw_lng': lng_value - float( delta ),
			'nw_lat': lat_value + float( delta ),
			'se_lng': lng_value + float( delta ),
			'se_lat': lat_value - float( delta ),
			'center_lat': lat_value,
			'center_lng': lng_value,
	}

# ------------- BROWSER GEOLOCATION UTILITIES

def get_geolocation_error_message( error_code: object, error_message: object ) -> str:
	"""Return the geolocation error message used by the application.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the get geolocation error
		message workflow. The function preserves the existing UI behavior, session-state
		interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	
	Args:
		error_code: object value used by the `get_geolocation_error_message` workflow.
		error_message: object value used by the `get_geolocation_error_message` workflow.
	
	Returns:
		str: Result produced by the `get_geolocation_error_message` workflow.
	"""
	try:
		code = int( error_code )
	except Exception:
		code = -1
	
	message = str( error_message or '' ).strip( )
	
	if code == 0:
		return f'Browser does not support geolocation. {message}'.strip( )
	
	if code == 1:
		return f'Browser location permission was denied. {message}'.strip( )
	
	if code == 2:
		return f'Browser position is unavailable. {message}'.strip( )
	
	if code == 3:
		return f'Browser location request timed out. {message}'.strip( )
	
	if message:
		return message
	
	return 'Browser geolocation failed.'

def update_location_from_browser( geo: Dict[ str, object ] ) -> bool:
	"""Handle the update location from browser workflow.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the update location from
		browser workflow. The function preserves the existing UI behavior, session-state
		interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	
	Args:
		geo: Dict[str, object] value used by the `update_location_from_browser` workflow.
	
	Returns:
		bool: Result produced by the `update_location_from_browser` workflow.
	"""
	try:
		if not geo:
			return False
		
		if 'error' in geo:
			error = geo.get( 'error', { } )
			error_code = None
			error_message = ''
			
			if isinstance( error, dict ):
				error_code = error.get( 'code', None )
				error_message = error.get( 'message', '' )
			
			st.session_state[ 'browser_geolocation_error' ] = get_geolocation_error_message(
				error_code,
				error_message )
			
			if error_code == 1:
				st.session_state[ 'browser_geolocation_permission_denied' ] = True
			
			st.session_state[ 'browser_geolocation_loaded' ] = False
			return False
		
		coords = geo.get( 'coords', { } )
		
		if not coords:
			st.session_state[ 'browser_geolocation_error' ] = (
					'Browser geolocation did not return coordinates.')
			return False
		
		latitude = coords.get( 'latitude', None )
		longitude = coords.get( 'longitude', None )
		accuracy = coords.get( 'accuracy', None )
		
		if not has_valid_coordinates( latitude, longitude ):
			st.session_state[ 'browser_geolocation_error' ] = (
					'Browser geolocation returned invalid coordinates.')
			return False
		
		set_location_state(
			description=f'Browser geolocation. Accuracy: {accuracy} meters.',
			latitude=float( latitude ),
			longitude=float( longitude ) )
		
		st.session_state[ 'browser_geolocation' ] = geo
		st.session_state[ 'browser_geolocation_loaded' ] = True
		st.session_state[ 'browser_geolocation_permission_denied' ] = False
		st.session_state[ 'browser_geolocation_error' ] = ''
		
		return True
	
	except Exception as ex:
		st.session_state[ 'browser_geolocation_error' ] = str( ex )
		return False

def bootstrap_browser_geolocation( geocoder: Geocoder ) -> None:
	"""Handle the bootstrap browser geolocation workflow.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the bootstrap browser
		geolocation workflow. The function preserves the existing UI behavior, session-
		state interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	
	Args:
		geocoder: Geocoder value used by the `bootstrap_browser_geolocation` workflow.
	"""
	try:
		if not st.session_state.get( 'browser_geolocation_enabled', True ):
			return
		
		if st.session_state.get( 'browser_geolocation_loaded', False ):
			return
		
		if st.session_state.get( 'browser_geolocation_permission_denied', False ):
			return
		
		geo_payload = get_geolocation( )
		
		if not geo_payload:
			return
		
		updated = update_location_from_browser( geo_payload )
		
		if not updated:
			return
		
		if not st.session_state.get( 'browser_geolocation_reverse_geocoded', False ):
			latitude = st.session_state.get( 'latitude', None )
			longitude = st.session_state.get( 'longitude', None )
			
			if geocoder is not None and has_valid_coordinates( latitude, longitude ):
				try:
					location_text = f'{float( latitude ):.6f},{float( longitude ):.6f}'
					geocoder.freeform( location_text )
					
					if not st.session_state.get( 'location', '' ):
						st.session_state[ 'location' ] = location_text
					
					st.session_state[ 'browser_geolocation_reverse_geocoded' ] = True
				
				except Exception:
					st.session_state[ 'location' ] = (
							f'{float( latitude ):.6f},{float( longitude ):.6f}')
		
		st.rerun( )
	
	except Exception as ex:
		st.session_state[ 'browser_geolocation_error' ] = str( ex )

# ------------- VISUALIZATION UTILITIES

def create_reports_map( df: pd.DataFrame, df_overlay: Optional[ pd.DataFrame ] = None,
		use_user_location: bool = True, key_prefix: str = 'reports_map' ) -> None:
	"""Create the reports map used by the application.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the create reports map
		workflow. The function preserves the existing UI behavior, session-state
		interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	
	Args:
		df: pd.DataFrame value used by the `create_reports_map` workflow.
		df_overlay: Optional[pd.DataFrame] value used by the `create_reports_map` workflow.
			Defaults to `None`.
		use_user_location: bool value used by the `create_reports_map` workflow. Defaults to `True`.
		key_prefix: str value used by the `create_reports_map` workflow. Defaults to
			`'reports_map'`.
	"""
	try:
		st.subheader( 'Locations' )
		df_source = pd.DataFrame( ) if df is None else df.copy( )
		df_overlay_source = pd.DataFrame( ) if df_overlay is None else df_overlay.copy( )
		required_cols = [ 'Latitude', 'Longitude' ]
		
		if not df_source.empty:
			missing_cols = [ col for col in required_cols if col not in df_source.columns ]
			if missing_cols:
				st.warning( f'Map requires missing column(s): {", ".join( missing_cols )}' )
				return
		
		if not df_overlay_source.empty:
			overlay_missing_cols = [
					col for col in required_cols if col not in df_overlay_source.columns ]
			
			if overlay_missing_cols:
				df_overlay_source = pd.DataFrame( )
		
		total_count = len( df_source )
		df_base_map = pd.DataFrame( )
		
		if not df_source.empty:
			df_source[ 'Latitude' ] = pd.to_numeric( df_source[ 'Latitude' ], errors='coerce' )
			df_source[ 'Longitude' ] = pd.to_numeric( df_source[ 'Longitude' ], errors='coerce' )
			
			base_mask = (df_source[ 'Latitude' ].notna( )
			             & df_source[ 'Longitude' ].notna( )
			             & df_source[ 'Latitude' ].between( -90.0, 90.0 )
			             & df_source[ 'Longitude' ].between( -180.0, 180.0 )
			             & ~((df_source[ 'Latitude' ] == 0.0)
			                 & (df_source[ 'Longitude' ] == 0.0)))
			
			df_base_map = df_source.loc[ base_mask ].copy( )
		
		mapped_count = len( df_base_map )
		missing_count = total_count - mapped_count
		df_overlay_map = pd.DataFrame( )
		
		if not df_overlay_source.empty:
			df_overlay_source[ 'Latitude' ] = pd.to_numeric( df_overlay_source[ 'Latitude' ],
				errors='coerce' )
			
			df_overlay_source[ 'Longitude' ] = pd.to_numeric( df_overlay_source[ 'Longitude' ],
				errors='coerce' )
			
			overlay_mask = (df_overlay_source[ 'Latitude' ].notna( )
			                & df_overlay_source[ 'Longitude' ].notna( )
			                & df_overlay_source[ 'Latitude' ].between( -90.0, 90.0 )
			                & df_overlay_source[ 'Longitude' ].between( -180.0, 180.0 )
			                & ~((df_overlay_source[ 'Latitude' ] == 0.0)
			                    & (df_overlay_source[ 'Longitude' ] == 0.0)))
			
			df_overlay_map = df_overlay_source.loc[ overlay_mask ].copy( )
		
		df_user_map = pd.DataFrame( )
		
		if use_user_location and df_base_map.empty and df_overlay_map.empty:
			user_latitude = st.session_state.get( 'latitude', None )
			user_longitude = st.session_state.get( 'longitude', None )
			
			if has_valid_coordinates( user_latitude, user_longitude ):
				user_location = compose_location_from_state( )
				user_description = st.session_state.get( 'description', '' )
				
				if not user_location:
					user_location = (f'{float( user_latitude ):.4f},'
					                 f'{float( user_longitude ):.4f}')
				
				df_user_map = pd.DataFrame( [ {
						'ID': 'USER-LOCATION',
						'CalendarDate': dt.datetime.now( ).strftime( '%Y-%m-%d %H:%M:%S' ),
						'City': user_location,
						'State': '',
						'Country': '',
						'Latitude': float( user_latitude ),
						'Longitude': float( user_longitude ),
						'Shape': 'User Location',
						'Summary': (user_description
						            or 'Current user location fallback.'), } ] )
		
		metric_c1, metric_c2, metric_c3, metric_c4 = st.columns( 4, border=True )
		metric_c1.metric( 'Total Records', f'{total_count:,}' )
		metric_c2.metric( 'Mapped Records', f'{mapped_count:,}' )
		metric_c3.metric( 'Missing / Invalid Coordinates', f'{missing_count:,}' )
		metric_c4.metric( 'Overlay / User Records',
			f'{len( df_overlay_map ) + len( df_user_map ):,}' )
		
		if df_base_map.empty and df_overlay_map.empty and df_user_map.empty:
			st.info( 'No usable base, overlay, or user-location coordinates are available.' )
			return
		
		if not df_base_map.empty:
			filter_c1, filter_c2, filter_c3, filter_c4 = st.columns(
				[ 0.25, 0.25, 0.25, 0.25 ], border=True )
			
			with filter_c1:
				if 'Year' in df_base_map.columns:
					year_options = sorted(
						[ str( value ) for value in df_base_map[ 'Year' ].dropna( ).unique( ) ] )
					selected_years = st.multiselect( 'Year', year_options,
						key=f'{key_prefix}_years' )
					
					if selected_years:
						df_base_map = df_base_map[
							df_base_map[ 'Year' ].astype( str ).isin( selected_years ) ]
			
			with filter_c2:
				if 'Country' in df_base_map.columns:
					country_options = sorted(
						[ str( value ) for value in df_base_map[ 'Country' ].dropna( ).unique( ) ] )
					selected_countries = st.multiselect( 'Country', country_options,
						key=f'{key_prefix}_countries' )
					
					if selected_countries:
						df_base_map = df_base_map[
							df_base_map[ 'Country' ].astype( str ).isin( selected_countries ) ]
			
			with filter_c3:
				if 'State' in df_base_map.columns:
					state_options = sorted(
						[ str( value ) for value in df_base_map[ 'State' ].dropna( ).unique( ) ] )
					selected_states = st.multiselect( 'State', state_options,
						key=f'{key_prefix}_states' )
					
					if selected_states:
						df_base_map = df_base_map[
							df_base_map[ 'State' ].astype( str ).isin( selected_states ) ]
			
			with filter_c4:
				if 'Shape' in df_base_map.columns:
					shape_options = sorted(
						[ str( value ) for value in df_base_map[ 'Shape' ].dropna( ).unique( ) ] )
					selected_shapes = st.multiselect( 'Shape', shape_options,
						key=f'{key_prefix}_shapes' )
					
					if selected_shapes:
						df_base_map = df_base_map[
							df_base_map[ 'Shape' ].astype( str ).isin( selected_shapes ) ]
		
		if df_base_map.empty and df_overlay_map.empty and df_user_map.empty:
			st.info( 'No mapped records match the selected filters.' )
			return
		
		map_style_options = {
				'Carto Positron': 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
				'Carto Dark Matter': 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
				'Carto Voyager': 'https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json',
				'Dark': 'dark',
				'Light': 'light',
				'Road': 'road',
				'Satellite': 'satellite',
				'Dark - No Labels': 'dark_no_labels',
				'Light - No Labels': 'light_no_labels',
				'Streamlit Theme': None,
		}
		
		control_c1, control_c2, control_c3, control_c4 = st.columns(
			[ 0.20, 0.20, 0.30, 0.30 ], border=True )
		
		with control_c1:
			zoom_level = st.slider( 'Initial Zoom', min_value=0, max_value=50, step=1,
				value=5, key=f'{key_prefix}_zoom' )
		
		with control_c2:
			point_radius = st.slider( 'Point Radius', min_value=1, max_value=50, value=1,
				step=5, key=f'{key_prefix}_radius' )
		
		with control_c3:
			selected_map_style = st.selectbox(
				'Map Style',
				list( map_style_options.keys( ) ),
				index=1,
				key=f'{key_prefix}_style' )
			
			map_style = map_style_options[ selected_map_style ]
		
		with control_c4:
			if len( df_base_map ) > 100:
				max_records = st.slider( 'Maximum Records', min_value=100,
					max_value=len( df_base_map ), value=min( 2500, len( df_base_map ) ),
					step=500, key=f'{key_prefix}_limit' )
				
				df_base_map = df_base_map.head( max_records )
			elif not df_base_map.empty:
				st.caption( f'Displaying all {len( df_base_map ):,} mapped base records.' )
			elif not df_overlay_map.empty:
				st.caption( f'Displaying {len( df_overlay_map ):,} overlay record(s).' )
			else:
				st.caption( 'Displaying current user/global location fallback.' )
		
		for df_target in [ df_base_map, df_overlay_map, df_user_map ]:
			if df_target.empty:
				continue
			
			for col in [ 'ID', 'CalendarDate', 'City', 'State', 'Country', 'Shape', 'Summary' ]:
				if col not in df_target.columns:
					df_target[ col ] = ''
			
			df_target[ 'MapSummary' ] = df_target[ 'Summary' ].astype( str ).str.slice( 0, 300 )
			df_target[ 'Position' ] = df_target.apply(
				lambda row: [ float( row[ 'Longitude' ] ), float( row[ 'Latitude' ] ) ],
				axis=1 )
		
		if not df_base_map.empty:
			df_view = df_base_map
		elif not df_overlay_map.empty:
			df_view = df_overlay_map
		else:
			df_view = df_user_map
		
		view_state = pdk.ViewState( latitude=float( df_view[ 'Latitude' ].median( ) ),
			longitude=float( df_view[ 'Longitude' ].median( ) ), zoom=zoom_level, pitch=0 )
		
		layers = [ ]
		
		if not df_base_map.empty:
			layers.append( pdk.Layer( 'ScatterplotLayer', data=df_base_map,
				get_position='Position', get_radius=point_radius,
				get_fill_color=[ 0, 120, 252, 160 ],
				get_line_color=[ 255, 255, 255, 180 ], line_width_min_pixels=1,
				radius_min_pixels=4, radius_max_pixels=24, filled=True,
				stroked=True, pickable=True ) )
		
		if not df_overlay_map.empty:
			layers.append( pdk.Layer( 'ScatterplotLayer', data=df_overlay_map,
				get_position='Position', get_radius=max( point_radius * 2, 20000 ),
				get_fill_color=[ 255, 80, 0, 220 ], get_line_color=[ 255, 255, 255, 255 ],
				line_width_min_pixels=2, radius_min_pixels=8, radius_max_pixels=40, filled=True,
				stroked=True, pickable=True ) )
		
		if not df_user_map.empty:
			layers.append( pdk.Layer( 'ScatterplotLayer', data=df_user_map,
				get_position='Position', get_radius=max( point_radius * 2, 20000 ),
				get_fill_color=[ 0, 180, 80, 230 ],
				get_line_color=[ 255, 255, 255, 255 ], line_width_min_pixels=2,
				radius_min_pixels=10, radius_max_pixels=42, filled=True, stroked=True,
				pickable=True ) )
		
		tooltip = {
				'html': (
						'<b>ID:</b> {ID}<br/>'
						'<b>Date:</b> {CalendarDate}<br/>'
						'<b>Location:</b> {City}, {State}, {Country}<br/>'
						'<b>Coordinates:</b> {Latitude}, {Longitude}<br/>'
						'<b>Shape:</b> {Shape}<br/>'
						'<b>Summary:</b> {MapSummary}'
				),
				'style': {
						'backgroundColor': 'rgba(0, 0, 0, 0.85)',
						'color': 'white',
						'fontSize': '12px',
				},
		}
		
		set_blue_divider( )
		
		deck = pdk.Deck( layers=layers, initial_view_state=view_state,
			map_style=map_style, tooltip=tooltip )
		
		st.pydeck_chart( deck, use_container_width=True )
		
		show_table = st.checkbox( 'Show mapped records table', value=False,
			key=f'{key_prefix}_show_table' )
		
		if show_table:
			if df_base_map.empty:
				if not df_user_map.empty:
					st.info( 'No base mapped records are available.' )
					st.data_editor( df_user_map, key=f'{key_prefix}_user_location_table',
						use_container_width=True, disabled=True )
				else:
					st.info( 'No base mapped records are available to display.' )
			
			else:
				display_cols = [ 'ID', 'Year', 'Month', 'Day', 'CalendarDate', 'City', 'State',
				                 'Country', 'Latitude', 'Longitude', 'Shape', 'Summary' ]
				display_cols = [ col for col in display_cols if col in df_base_map.columns ]
				
				st.data_editor( df_base_map[ display_cols ], key=f'{key_prefix}_table',
					use_container_width=True, disabled=True )
	
	except Exception as e:
		st.error( f'Interactive map failed: {e}' )

# ------------ GIS MAPPING UTILITIES

def compose_location_query( city: object, state: object, country: object ) -> str:
	"""Handle the compose location query workflow.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the compose location query
		workflow. The function preserves the existing UI behavior, session-state
		interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	
	Args:
		city: object value used by the `compose_location_query` workflow.
		state: object value used by the `compose_location_query` workflow.
		country: object value used by the `compose_location_query` workflow.
	
	Returns:
		str: Result produced by the `compose_location_query` workflow.
	"""
	parts = [ ]
	
	for value in [ city, state, country ]:
		if value is None:
			continue
		
		text = str( value ).strip( )
		if text and text.lower( ) not in [ 'nan', 'none', 'null' ]:
			parts.append( text )
	
	return ', '.join( parts )

def get_value_by_path( obj: object, path: List[ object ] ) -> object:
	"""Return the value by path used by the application.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the get value by path
		workflow. The function preserves the existing UI behavior, session-state
		interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	
	Args:
		obj: object value used by the `get_value_by_path` workflow.
		path: List[object] value used by the `get_value_by_path` workflow.
	
	Returns:
		object: Result produced by the `get_value_by_path` workflow.
	"""
	current = obj
	
	for key in path:
		if current is None:
			return None
		
		if isinstance( current, dict ):
			current = current.get( key )
			continue
		
		if isinstance( current, (list, tuple) ) and isinstance( key, int ):
			if 0 <= key < len( current ):
				current = current[ key ]
				continue
			return None
		
		if hasattr( current, str( key ) ):
			current = getattr( current, str( key ) )
			continue
		
		return None
	
	return current

def extract_coordinates( result: object ) -> Tuple[ Optional[ float ], Optional[ float ] ]:
	"""Handle the extract coordinates workflow.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the extract coordinates
		workflow. The function preserves the existing UI behavior, session-state
		interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	
	Args:
		result: object value used by the `extract_coordinates` workflow.
	
	Returns:
		Tuple[Optional[float], Optional[float]]: Result produced by the
			`extract_coordinates` workflow.
	"""
	if result is None:
		return None, None
	
	lat_paths = [
			[ 'lat' ],
			[ 'latitude' ],
			[ 'location', 'lat' ],
			[ 'location', 'latitude' ],
			[ 'geometry', 'location', 'lat' ],
			[ 'geometry', 'location', 'latitude' ],
			[ 'result', 'geometry', 'location', 'lat' ],
			[ 'results', 0, 'geometry', 'location', 'lat' ],
			[ 'candidates', 0, 'geometry', 'location', 'lat' ],
	]
	
	lon_paths = [
			[ 'lng' ],
			[ 'lon' ],
			[ 'longitude' ],
			[ 'location', 'lng' ],
			[ 'location', 'lon' ],
			[ 'location', 'longitude' ],
			[ 'geometry', 'location', 'lng' ],
			[ 'geometry', 'location', 'lon' ],
			[ 'geometry', 'location', 'longitude' ],
			[ 'result', 'geometry', 'location', 'lng' ],
			[ 'results', 0, 'geometry', 'location', 'lng' ],
			[ 'candidates', 0, 'geometry', 'location', 'lng' ],
	]
	
	lat_value = None
	lon_value = None
	
	for path in lat_paths:
		lat_value = get_value_by_path( result, path )
		if lat_value is not None:
			break
	
	for path in lon_paths:
		lon_value = get_value_by_path( result, path )
		if lon_value is not None:
			break
	
	try:
		latitude = float( lat_value ) if lat_value is not None else None
		longitude = float( lon_value ) if lon_value is not None else None
	except Exception:
		return None, None
	
	if not has_valid_coordinates( latitude, longitude ):
		return None, None
	
	return latitude, longitude

def count_missing_report_coordinate_rows( table_name: str ) -> int:
	"""Handle the count missing report coordinate rows workflow.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the count missing report
		coordinate rows workflow. The function preserves the existing UI behavior,
		session-state interactions, dataframe handling, database access, and service
		integrations defined by the application code.
	
	Args:
		table_name: str value used by the `count_missing_report_coordinate_rows` workflow.
	
	Returns:
		int: Result produced by the `count_missing_report_coordinate_rows` workflow.
	"""
	try:
		throw_if( 'table_name', table_name )
		query = f"""
			SELECT COUNT(*) AS RowCount
			FROM "{table_name}"
			WHERE (
			          Latitude IS NULL
			          OR Longitude IS NULL
			          OR Latitude < -90
			          OR Latitude > 90
			          OR Longitude < -180
			          OR Longitude > 180
			          OR (Latitude = 0 AND Longitude = 0)
			      )
			  AND City IS NOT NULL
			  AND TRIM(City) <> ''
			  AND Country IS NOT NULL
			  AND TRIM(Country) <> '';
		"""
		with create_connection( ) as conn:
			row = conn.execute( query ).fetchone( )
			return int( row[ 0 ] or 0 )
	
	except Exception as e:
		st.error( f'Unable to count missing coordinate rows: {e}' )
		return 0

def read_missing_report_locations( table_name: str, limit: Optional[ int ] = None ) -> pd.DataFrame:
	"""Read the missing report locations for application processing.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the read missing report
		locations workflow. The function preserves the existing UI behavior, session-state
		interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	
	Args:
		table_name: str value used by the `read_missing_report_locations` workflow.
		limit: Optional[int] value used by the `read_missing_report_locations` workflow.
			Defaults to `None`.
	
	Returns:
		pd.DataFrame: Result produced by the `read_missing_report_locations` workflow.
	"""
	try:
		throw_if( 'table_name', table_name )
		query = f"""
			SELECT
			    TRIM(City) AS City,
			    TRIM(COALESCE(State, '')) AS State,
			    TRIM(Country) AS Country,
			    COUNT(*) AS RowCount
			FROM "{table_name}"
			WHERE (
			          Latitude IS NULL
			          OR Longitude IS NULL
			          OR Latitude < -90
			          OR Latitude > 90
			          OR Longitude < -180
			          OR Longitude > 180
			          OR (Latitude = 0 AND Longitude = 0)
			      )
			  AND City IS NOT NULL
			  AND TRIM(City) <> ''
			  AND Country IS NOT NULL
			  AND TRIM(Country) <> ''
			GROUP BY TRIM(City), TRIM(COALESCE(State, '')), TRIM(Country)
			ORDER BY RowCount DESC, City, State, Country
		"""
		if limit:
			query += f' LIMIT {int( limit )}'
		
		with create_connection( ) as conn:
			return pd.read_sql_query( query, conn )
	
	except Exception as e:
		st.error( f'Unable to read missing report locations: {e}' )
		return pd.DataFrame( )

def preview_report_coordinate_updates( table_name: str, geocoder: Geocoder, places: Place,
		use_places: bool = True, limit: Optional[ int ] = None ) -> pd.DataFrame:
	"""Handle the preview report coordinate updates workflow.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the preview report
		coordinate updates workflow. The function preserves the existing UI behavior,
		session-state interactions, dataframe handling, database access, and service
		integrations defined by the application code.
	
	Args:
		table_name: str value used by the `preview_report_coordinate_updates` workflow.
		geocoder: Geocoder value used by the `preview_report_coordinate_updates` workflow.
		places: Place value used by the `preview_report_coordinate_updates` workflow.
		use_places: bool value used by the `preview_report_coordinate_updates` workflow. Defaults
			to `True`.
		limit: Optional[int] value used by the `preview_report_coordinate_updates` workflow.
			Defaults to `None`.
	
	Returns:
		pd.DataFrame: Result produced by the `preview_report_coordinate_updates`
			workflow.
	
	Raises:
		Exception: Propagates validation, UI, data, database, or provider errors
			raised by the existing implementation.
	"""
	try:
		throw_if( 'table_name', table_name )
		throw_if( 'geocoder', geocoder )
		
		df_locations = read_missing_report_locations( table_name, limit )
		
		if df_locations.empty:
			return pd.DataFrame( )
		
		records: List[ Dict[ str, object ] ] = [ ]
		
		for row in df_locations.itertuples( index=False ):
			query = compose_location_query( row.City, row.State, row.Country )
			
			record = {
					'City': row.City,
					'State': row.State,
					'Country': row.Country,
					'Query': query,
					'RowCount': row.RowCount,
					'Latitude': None,
					'Longitude': None,
					'Source': '',
					'Status': '',
					'Message': '',
			}
			
			if not query:
				record[ 'Status' ] = 'Skipped'
				record[ 'Message' ] = 'Location query could not be composed.'
				records.append( record )
				continue
			
			try:
				result = geocoder.freeform( query )
				latitude, longitude = extract_coordinates( result )
				
				if latitude is None or longitude is None:
					raise NotFound( 'No usable coordinates returned by Geocoder.' )
				
				record[ 'Latitude' ] = latitude
				record[ 'Longitude' ] = longitude
				record[ 'Source' ] = 'Geocoder'
				record[ 'Status' ] = 'Matched'
				record[ 'Message' ] = 'Resolved by Geocoder.'
			
			except NotFound as e:
				if use_places and places is not None:
					try:
						result = places.text_to_location( query )
						latitude, longitude = extract_coordinates( result )
						
						if latitude is None or longitude is None:
							record[ 'Source' ] = 'Places'
							record[ 'Status' ] = 'Failed'
							record[ 'Message' ] = 'No usable coordinates returned by Places.'
						else:
							record[ 'Latitude' ] = latitude
							record[ 'Longitude' ] = longitude
							record[ 'Source' ] = 'Places'
							record[ 'Status' ] = 'Matched'
							record[ 'Message' ] = 'Resolved by Places fallback.'
					
					except Exception as ex:
						record[ 'Source' ] = 'Places'
						record[ 'Status' ] = 'Failed'
						record[ 'Message' ] = str( ex )
				else:
					record[ 'Source' ] = 'Geocoder'
					record[ 'Status' ] = 'Failed'
					record[ 'Message' ] = str( e )
			
			except Exception as e:
				record[ 'Source' ] = 'Geocoder'
				record[ 'Status' ] = 'Failed'
				record[ 'Message' ] = str( e )
			
			records.append( record )
		
		return pd.DataFrame( records )
	
	except Exception as e:
		st.error( f'Unable to preview coordinate updates: {e}' )
		return pd.DataFrame( )

def apply_report_coordinate_updates( table_name: str, df_updates: pd.DataFrame ) -> int:
	"""Apply the report coordinate updates operation.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the apply report coordinate
		updates workflow. The function preserves the existing UI behavior, session-state
		interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	
	Args:
		table_name: str value used by the `apply_report_coordinate_updates` workflow.
		df_updates: pd.DataFrame value used by the `apply_report_coordinate_updates` workflow.
	
	Returns:
		int: Result produced by the `apply_report_coordinate_updates` workflow.
	
	Raises:
		Exception: Propagates validation, UI, data, database, or provider errors
			raised by the existing implementation.
	"""
	try:
		throw_if( 'table_name', table_name )
		
		if df_updates is None or df_updates.empty:
			return 0
		
		required_cols = [ 'City', 'State', 'Country', 'Latitude', 'Longitude', 'Status' ]
		missing_cols = [ col for col in required_cols if col not in df_updates.columns ]
		
		if missing_cols:
			raise ValueError( f'Missing update column(s): {", ".join( missing_cols )}' )
		
		df_apply = df_updates.copy( )
		df_apply = df_apply[ df_apply[ 'Status' ].astype( str ).str.lower( ) == 'matched' ]
		df_apply[ 'Latitude' ] = pd.to_numeric( df_apply[ 'Latitude' ], errors='coerce' )
		df_apply[ 'Longitude' ] = pd.to_numeric( df_apply[ 'Longitude' ], errors='coerce' )
		
		valid_mask = (
				df_apply[ 'Latitude' ].notna( )
				& df_apply[ 'Longitude' ].notna( )
				& df_apply[ 'Latitude' ].between( -90.0, 90.0 )
				& df_apply[ 'Longitude' ].between( -180.0, 180.0 )
				& ~(
				(df_apply[ 'Latitude' ] == 0.0)
				& (df_apply[ 'Longitude' ] == 0.0)
		)
		)
		
		df_apply = df_apply.loc[ valid_mask ].copy( )
		
		if df_apply.empty:
			return 0
		
		updated_count = 0
		cursor = None
		
		with create_connection( ) as conn:
			try:
				conn.execute( 'PRAGMA busy_timeout = 30000;' )
				cursor = conn.cursor( )
				cursor.execute( 'BEGIN IMMEDIATE;' )
				
				for row in df_apply.itertuples( index=False ):
					cursor.execute(
						f"""
						UPDATE "{table_name}"
						SET Latitude = ?,
						    Longitude = ?
						WHERE
							(Latitude IS NULL OR Longitude IS NULL
							 OR Latitude = '' OR Longitude = ''
							 OR Latitude = 0 OR Longitude = 0)
							AND COALESCE(City, '') = COALESCE(?, '')
							AND COALESCE(State, '') = COALESCE(?, '')
							AND COALESCE(Country, '') = COALESCE(?, '');
						""",
						(
								float( row.Latitude ),
								float( row.Longitude ),
								'' if pd.isna( row.City ) else str( row.City ),
								'' if pd.isna( row.State ) else str( row.State ),
								'' if pd.isna( row.Country ) else str( row.Country ),
						) )
					
					updated_count += int( cursor.rowcount or 0 )
				
				conn.commit( )
			
			except Exception:
				conn.rollback( )
				raise
			
			finally:
				if cursor is not None:
					cursor.close( )
		
		with create_connection( ) as conn:
			try:
				conn.execute( 'PRAGMA wal_checkpoint(TRUNCATE);' )
			except sqlite3.OperationalError:
				pass
		
		return int( updated_count )
	
	except Exception as e:
		st.error( f'Unable to apply coordinate updates: {e}' )
		return 0

def append_geocoding_map_result( query: str, source: str, result: object ) -> None:
	"""Handle the append geocoding map result workflow.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the append geocoding map
		result workflow. The function preserves the existing UI behavior, session-state
		interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	
	Args:
		query: str value used by the `append_geocoding_map_result` workflow.
		source: str value used by the `append_geocoding_map_result` workflow.
		result: object value used by the `append_geocoding_map_result` workflow.
	"""
	try:
		throw_if( 'query', query )
		throw_if( 'source', source )
		
		latitude, longitude = extract_coordinates( result )
		
		if latitude is None or longitude is None:
			st.warning( 'The geocoding result did not contain usable coordinates for the map.' )
			return
		
		set_location_state(
			location=query,
			description=f'{source} result for {query}',
			latitude=latitude,
			longitude=longitude )
		
		df_new = pd.DataFrame(
			[
					{
							'ID': f'GEOCODED-{int( time.time( ) )}',
							'CalendarDate': dt.datetime.now( ).strftime( '%Y-%m-%d %H:%M:%S' ),
							'City': query,
							'State': '',
							'Country': '',
							'Latitude': latitude,
							'Longitude': longitude,
							'Shape': 'Geocoded Result',
							'Summary': f'{source} result for {query}',
							'Source': source,
							'Query': query,
					}
			]
		)
		
		df_current = st.session_state.get( 'df_geocoding_map_results', pd.DataFrame( ) )
		
		if df_current is None or df_current.empty:
			st.session_state[ 'df_geocoding_map_results' ] = df_new
		else:
			st.session_state[ 'df_geocoding_map_results' ] = pd.concat(
				[ df_current, df_new ],
				ignore_index=True )
	
	except Exception as e:
		st.error( f'Unable to append geocoding result to map: {e}' )

# ------------ DATABASE UTILITIES

def initialize_database( ) -> None:
	"""Handle the initialize database workflow.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the initialize database
		workflow. The function preserves the existing UI behavior, session-state
		interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	"""
	Path( 'stores/sqlite' ).mkdir( parents=True, exist_ok=True )
	with create_connection( ) as connection:
		conn.execute(
			"""
            CREATE TABLE IF NOT EXISTS chat_history
            (
                id
                INTEGER
                PRIMARY
                KEY
                AUTOINCREMENT,
                role
                TEXT,
                content
                TEXT
            )
			"""
		)
		
		conn.execute(
			"""
            CREATE TABLE IF NOT EXISTS embeddings
            (
                id
                INTEGER
                PRIMARY
                KEY
                AUTOINCREMENT,
                chunk
                TEXT,
                vector
                BLOB
            )
			"""
		)
		
		conn.execute(
			"""
            CREATE TABLE IF NOT EXISTS Prompts
            (
                PromptsId
                INTEGER
                NOT
                NULL
                PRIMARY
                KEY
                AUTOINCREMENT,
                Caption
                TEXT,
                Name
                TEXT
            (
                80
            ),
                Text TEXT,
                Version TEXT
            (
                80
            ),
                ID TEXT
            (
                80
            )
                )
			"""
		)
		
		prompt_columns = [ row[ 1 ] for row in
		                   conn.execute( 'PRAGMA table_info("Prompts");' ).fetchall( ) ]
		
		if 'Caption' not in prompt_columns:
			conn.execute( 'ALTER TABLE "Prompts" ADD COLUMN "Caption" TEXT;' )
		
		conn.commit( )

class ManagedConnection( sqlite3.Connection ):
	"""Represent the Managed Connection component for the Mappy Streamlit application.
	
	Purpose:
		Provides the Managed Connection class used by the Mappy Streamlit application. The
		class preserves application state, data-access behavior, and UI-facing integration
		points required by the existing workflow.
	"""
	
	def __enter__( self ) -> "ManagedConnection":
		"""Enter the managed connection context.
		
		Purpose:
			Supports the Mappy Streamlit application by executing the enter workflow. The
			function preserves the existing UI behavior, session-state interactions, dataframe
			handling, database access, and service integrations defined by the application
			code.
		
		Returns:
			'ManagedConnection': Result produced by the `__enter__` workflow.
		"""
		return self
	
	def __exit__( self, exc_type: object, exc_value: object, traceback: object ) -> bool:
		"""Exit the managed connection context.
		
		Purpose:
			Supports the Mappy Streamlit application by executing the exit workflow. The
			function preserves the existing UI behavior, session-state interactions, dataframe
			handling, database access, and service integrations defined by the application
			code.
		
		Args:
			exc_type: object value used by the `__exit__` workflow.
			exc_value: object value used by the `__exit__` workflow.
			traceback: object value used by the `__exit__` workflow.
		
		Returns:
			bool: Result produced by the `__exit__` workflow.
		"""
		try:
			if exc_type is None:
				self.commit( )
			else:
				self.rollback( )
		finally:
			self.close( )
		
		return False

def create_connection( ) -> sqlite3.Connection:
	"""Create the connection used by the application.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the create connection
		workflow. The function preserves the existing UI behavior, session-state
		interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	
	Returns:
		sqlite3.Connection: Result produced by the `create_connection` workflow.
	"""
	conn = sqlite3.connect( cfg.DB_PATH, timeout=60.0, isolation_level=None,
		check_same_thread=False, factory=ManagedConnection )
	
	conn.execute( 'PRAGMA busy_timeout = 30000;' )
	conn.execute( 'PRAGMA foreign_keys = ON;' )
	
	try:
		conn.execute( 'PRAGMA journal_mode = WAL;' )
	except sqlite3.OperationalError:
		pass
	
	return conn

def list_tables( ) -> List[ str ]:
	"""Handle the list tables workflow.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the list tables workflow.
		The function preserves the existing UI behavior, session-state interactions,
		dataframe handling, database access, and service integrations defined by the
		application code.
	
	Returns:
		List[str]: Result produced by the `list_tables` workflow.
	"""
	with create_connection( ) as conn:
		_query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
		rows = conn.execute( _query ).fetchall( )
		return [ r[ 0 ] for r in rows ]

def create_schema( table: str ) -> List[ Tuple ]:
	"""Create the schema used by the application.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the create schema workflow.
		The function preserves the existing UI behavior, session-state interactions,
		dataframe handling, database access, and service integrations defined by the
		application code.
	
	Args:
		table: str value used by the `create_schema` workflow.
	
	Returns:
		List[Tuple]: Result produced by the `create_schema` workflow.
	"""
	with create_connection( ) as conn:
		return conn.execute( f'PRAGMA table_info("{table}");' ).fetchall( )

def read_table( table: str, limit: int = None, offset: int = 0 ) -> pd.DataFrame:
	"""Read the table for application processing.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the read table workflow. The
		function preserves the existing UI behavior, session-state interactions, dataframe
		handling, database access, and service integrations defined by the application
		code.
	
	Args:
		table: str value used by the `read_table` workflow.
		limit: int value used by the `read_table` workflow. Defaults to `None`.
		offset: int value used by the `read_table` workflow. Defaults to `0`.
	
	Returns:
		pd.DataFrame: Result produced by the `read_table` workflow.
	"""
	if not table:
		return pd.DataFrame( )
	
	query = f'SELECT * FROM "{table}"'
	if limit:
		query += f' LIMIT {int( limit )} OFFSET {int( offset )}'
	
	with create_connection( ) as conn:
		cur = conn.cursor( )
		cur.execute( query )
		
		raw_columns = [ d[ 0 ] for d in (cur.description or [ ]) ]
		rows = cur.fetchall( )
	
	seen: Dict[ str, int ] = { }
	columns: List[ str ] = [ ]
	
	for col in raw_columns:
		name = str( col )
		if name not in seen:
			seen[ name ] = 0
			columns.append( name )
		else:
			seen[ name ] += 1
			columns.append( f'{name}_{seen[ name ]}' )
	
	def _scalarize( value: Any ) -> Any:
		"""Handle the scalarize workflow.
		
		Purpose:
			Supports the Mappy Streamlit application by executing the scalarize workflow. The
			function preserves the existing UI behavior, session-state interactions, dataframe
			handling, database access, and service integrations defined by the application
			code.
		
		Args:
			value: Any value used by the `_scalarize` workflow.
		
		Returns:
			Any: Result produced by the `_scalarize` workflow.
		"""
		if value is None or isinstance( value, (str, int, float, bool) ):
			return value
		
		if isinstance( value, bytes ):
			try:
				return value.decode( 'utf-8' )
			except Exception:
				return value.hex( )
		
		if isinstance( value, (list, tuple, set, dict) ):
			try:
				return str( normalize( value ) )
			except Exception:
				return str( value )
		
		if hasattr( value, 'model_dump' ):
			try:
				return str( value.model_dump( ) )
			except Exception:
				return str( value )
		
		return str( value )
	
	normalized_rows: List[ Dict[ str, Any ] ] = [ ]
	for row in rows:
		record: Dict[ str, Any ] = { }
		for idx, col in enumerate( columns ):
			record[ col ] = _scalarize( row[ idx ] )
		normalized_rows.append( record )
	
	return pd.DataFrame( normalized_rows, columns=columns )

def render_table( df: pd.DataFrame ) -> None:
	"""Render the table interface section.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the render table workflow.
		The function preserves the existing UI behavior, session-state interactions,
		dataframe handling, database access, and service integrations defined by the
		application code.
	
	Args:
		df: pd.DataFrame value used by the `render_table` workflow.
	"""
	if df is None:
		st.info( 'No data available.' )
		return
	
	try:
		st.data_editor( df, use_container_width=True )
		return
	except Exception:
		pass
	
	fallback_df = df.copy( )
	fallback_df = fallback_df.where( pd.notnull( fallback_df ), '' )
	
	for col in fallback_df.columns:
		fallback_df[ col ] = fallback_df[ col ].map(
			lambda x: x if isinstance( x, (str, int, float, bool) ) or x == '' else str( x ) )
	
	st.markdown( fallback_df.to_html( index=False, escape=True ), unsafe_allow_html=True )

def make_display_safe( df: pd.DataFrame ) -> pd.DataFrame:
	"""Handle the make display safe workflow.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the make display safe
		workflow. The function preserves the existing UI behavior, session-state
		interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	
	Args:
		df: pd.DataFrame value used by the `make_display_safe` workflow.
	
	Returns:
		pd.DataFrame: Result produced by the `make_display_safe` workflow.
	"""
	display_df = df.copy( )
	
	for col in display_df.columns:
		display_df[ col ] = display_df[ col ].map( lambda x: '' if x is None else str( x ) )
	
	return display_df

def drop_table( table: str ) -> None:
	"""Handle the drop table workflow.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the drop table workflow. The
		function preserves the existing UI behavior, session-state interactions, dataframe
		handling, database access, and service integrations defined by the application
		code.
	
	Args:
		table: str value used by the `drop_table` workflow.
	"""
	if not table:
		return
	
	with create_connection( ) as conn:
		conn.execute( f'DROP TABLE IF EXISTS "{table}";' )
		conn.commit( )

def create_index( table: str, column: str ) -> None:
	"""Create the index used by the application.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the create index workflow.
		The function preserves the existing UI behavior, session-state interactions,
		dataframe handling, database access, and service integrations defined by the
		application code.
	
	Args:
		table: str value used by the `create_index` workflow.
		column: str value used by the `create_index` workflow.
	
	Raises:
		Exception: Propagates validation, UI, data, database, or provider errors
			raised by the existing implementation.
	"""
	if not table or not column:
		return
	
	# ------------------------------------------------------------------
	# Validate table exists
	# ------------------------------------------------------------------
	tables = list_tables( )
	if table not in tables:
		raise ValueError( 'Invalid table name.' )
	
	# ------------------------------------------------------------------
	# Validate column exists
	# ------------------------------------------------------------------
	schema = create_schema( table )
	valid_columns = [ col[ 1 ] for col in schema ]
	
	if column not in valid_columns:
		raise ValueError( 'Invalid column name.' )
	
	# ------------------------------------------------------------------
	# Sanitize index name (identifier only)
	# ------------------------------------------------------------------
	safe_index_name = re.sub( r"[^0-9a-zA-Z_]+", "_", f"idx_{table}_{column}" )
	
	# ------------------------------------------------------------------
	# Create index safely (quote identifiers)
	# ------------------------------------------------------------------
	sql = f'CREATE INDEX IF NOT EXISTS "{safe_index_name}" ON "{table}"("{column}");'
	
	with create_connection( ) as conn:
		conn.execute( sql )
		conn.commit( )

def apply_filters( df: pd.DataFrame ) -> pd.DataFrame:
	"""Apply the filters operation.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the apply filters workflow.
		The function preserves the existing UI behavior, session-state interactions,
		dataframe handling, database access, and service integrations defined by the
		application code.
	
	Args:
		df: pd.DataFrame value used by the `apply_filters` workflow.
	
	Returns:
		pd.DataFrame: Result produced by the `apply_filters` workflow.
	"""
	st.subheader( 'Advanced Filters' )
	conditions = [ ]
	col1, col2, col3 = st.columns( 3 )
	column = col1.selectbox( 'Column', df.columns )
	operator = col2.selectbox( 'Operator', [ '=', '!=', '>', '<', '>=', '<=', 'contains' ] )
	value = col3.text_input( 'Value' )
	if value:
		if operator == '=':
			df = df[ df[ column ] == value ]
		elif operator == '!=':
			df = df[ df[ column ] != value ]
		elif operator == '>':
			df = df[ df[ column ].astype( float ) > float( value ) ]
		elif operator == '<':
			df = df[ df[ column ].astype( float ) < float( value ) ]
		elif operator == '>=':
			df = df[ df[ column ].astype( float ) >= float( value ) ]
		elif operator == '<=':
			df = df[ df[ column ].astype( float ) <= float( value ) ]
		elif operator == 'contains':
			df = df[ df[ column ].astype( str ).str.contains( value ) ]
	
	return df

def create_aggregation( df: pd.DataFrame ):
	"""Create the aggregation used by the application.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the create aggregation
		workflow. The function preserves the existing UI behavior, session-state
		interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	
	Args:
		df: pd.DataFrame value used by the `create_aggregation` workflow.
	"""
	st.subheader( 'Aggregation Engine' )
	numeric_cols = df.select_dtypes( include=[ 'number' ] ).columns.tolist( )
	if not numeric_cols:
		st.info( 'No numeric columns available.' )
		return
	
	col = st.selectbox( 'Column', numeric_cols )
	agg = st.selectbox( 'Aggregation', [ 'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'MEDIAN' ] )
	
	if agg == 'COUNT':
		result = df[ col ].count( )
	elif agg == 'SUM':
		result = df[ col ].sum( )
	elif agg == 'AVG':
		result = df[ col ].mean( )
	elif agg == 'MIN':
		result = df[ col ].min( )
	elif agg == 'MAX':
		result = df[ col ].max( )
	elif agg == 'MEDIAN':
		result = df[ col ].median( )
	
	st.metric( 'Result', result )

def create_visualization( df: pd.DataFrame ) -> None:
	"""Create the visualization used by the application.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the create visualization
		workflow. The function preserves the existing UI behavior, session-state
		interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	
	Args:
		df: pd.DataFrame value used by the `create_visualization` workflow.
	"""
	
	set_blue_divider( )
	
	st.markdown( '##### Visualization Engine' )
	
	if df is None or df.empty:
		st.info( 'No data available.' )
		return
	
	df_plot = df.copy( )
	
	for col in df_plot.columns:
		if df_plot[ col ].dtype == object:
			df_plot[ col ] = df_plot[ col ].map( lambda x: '' if x is None else str( x ) )
	
	numeric_cols: List[ str ] = [ ]
	for col in df_plot.columns:
		series_num = pd.to_numeric( df_plot[ col ], errors='coerce' )
		if series_num.notna( ).any( ):
			numeric_cols.append( col )
	
	categorical_cols: List[ str ] = [ col for col in df_plot.columns if col not in numeric_cols ]
	
	chart = st.selectbox( 'Chart Type',
		[ 'Histogram', 'Bar', 'Line', 'Scatter', 'Box', 'Pie', 'Correlation' ] )
	
	if chart == 'Histogram':
		if not numeric_cols:
			st.info( 'No numeric columns available.' )
			return
		
		col = st.selectbox( 'Column', numeric_cols )
		values = pd.to_numeric( df_plot[ col ], errors='coerce' ).dropna( ).tolist( )
		
		fig = go.Figure( data=[ go.Histogram( x=values ) ] )
		fig.update_layout( xaxis_title=col, yaxis_title='Count' )
		st.plotly_chart( fig, use_container_width=True )
	
	elif chart == 'Bar':
		if not numeric_cols:
			st.info( 'No numeric columns available.' )
			return
		
		x = st.selectbox( 'X', df_plot.columns )
		y = st.selectbox( 'Y', numeric_cols )
		
		x_values = df_plot[ x ].astype( str ).tolist( )
		y_values = pd.to_numeric( df_plot[ y ], errors='coerce' ).fillna( 0 ).tolist( )
		
		fig = go.Figure( data=[ go.Bar( x=x_values, y=y_values ) ] )
		fig.update_layout( xaxis_title=x, yaxis_title=y )
		st.plotly_chart( fig, use_container_width=True )
	
	elif chart == 'Line':
		if not numeric_cols:
			st.info( 'No numeric columns available.' )
			return
		
		x = st.selectbox( 'X', df_plot.columns )
		y = st.selectbox( 'Y', numeric_cols )
		
		x_values = df_plot[ x ].astype( str ).tolist( )
		y_values = pd.to_numeric( df_plot[ y ], errors='coerce' ).fillna( 0 ).tolist( )
		
		fig = go.Figure( data=[ go.Scatter( x=x_values, y=y_values, mode='lines' ) ] )
		fig.update_layout( xaxis_title=x, yaxis_title=y )
		st.plotly_chart( fig, use_container_width=True )
	
	elif chart == 'Scatter':
		if len( numeric_cols ) < 2:
			st.info( 'At least two numeric columns are required.' )
			return
		
		x = st.selectbox( 'X', numeric_cols, key='viz_scatter_x' )
		y = st.selectbox( 'Y', numeric_cols, key='viz_scatter_y' )
		
		x_series = pd.to_numeric( df_plot[ x ], errors='coerce' )
		y_series = pd.to_numeric( df_plot[ y ], errors='coerce' )
		mask = x_series.notna( ) & y_series.notna( )
		
		x_values = x_series[ mask ].tolist( )
		y_values = y_series[ mask ].tolist( )
		
		fig = go.Figure( data=[ go.Scatter( x=x_values, y=y_values, mode='markers' ) ] )
		fig.update_layout( xaxis_title=x, yaxis_title=y )
		st.plotly_chart( fig, use_container_width=True )
	
	elif chart == 'Box':
		if not numeric_cols:
			st.info( 'No numeric columns available.' )
			return
		
		col = st.selectbox( 'Column', numeric_cols, key='viz_box_col' )
		values = pd.to_numeric( df_plot[ col ], errors='coerce' ).dropna( ).tolist( )
		
		fig = go.Figure( data=[ go.Box( y=values, name=col ) ] )
		fig.update_layout( yaxis_title=col )
		st.plotly_chart( fig, use_container_width=True )
	
	elif chart == 'Pie':
		if not categorical_cols:
			st.info( 'No categorical columns available.' )
			return
		
		col = st.selectbox( 'Category Column', categorical_cols )
		counts = df_plot[ col ].astype( str ).value_counts( )
		
		fig = go.Figure(
			data=[ go.Pie( labels=counts.index.tolist( ), values=counts.values.tolist( ) ) ] )
		st.plotly_chart( fig, use_container_width=True )
	
	elif chart == 'Correlation':
		if len( numeric_cols ) < 2:
			st.info( 'At least two numeric columns are required.' )
			return
		
		corr_df = pd.DataFrame( )
		for col in numeric_cols:
			corr_df[ col ] = pd.to_numeric( df_plot[ col ], errors='coerce' )
		
		corr = corr_df.corr( )
		
		fig = go.Figure(
			data=[ go.Heatmap(
				z=corr.values.tolist( ),
				x=corr.columns.tolist( ),
				y=corr.index.tolist( ) ) ] )
		st.plotly_chart( fig, use_container_width=True )

def convert_dataframe( table_name: str, df: pd.DataFrame ) -> None:
	"""Handle the convert dataframe workflow.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the convert dataframe
		workflow. The function preserves the existing UI behavior, session-state
		interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	
	Args:
		table_name: str value used by the `convert_dataframe` workflow.
		df: pd.DataFrame value used by the `convert_dataframe` workflow.
	"""
	columns = [ ]
	for col in df.columns:
		sql_type = get_sqlite_type( df[ col ].dtype )
		safe_col = col.replace( ' ', '_' )
		columns.append( f'{safe_col} {sql_type}' )
	
	create_stmt = f'CREATE TABLE IF NOT EXISTS {table_name} ({", ".join( columns )});'
	with create_connection( ) as conn:
		conn.execute( create_stmt )
		conn.commit( )

def insert_data( table_name: str, df: pd.DataFrame ) -> None:
	"""Handle the insert data workflow.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the insert data workflow.
	
	Args:
		table_name: str value representing the name of the table.
		df: pd.DataFrame value used by the `insert_data` workflow.
	"""
	df = df.copy( )
	df.columns = [ c.replace( ' ', '_' ) for c in df.columns ]
	placeholders = ', '.join( [ '?' ] * len( df.columns ) )
	stmt = f'INSERT INTO {table_name} VALUES ({placeholders});'
	with create_connection( ) as conn:
		conn.executemany( stmt, df.values.tolist( ) )
		conn.commit( )

def get_sqlite_type( dtype: str ) -> str:
	"""Return the sqlite type used by the application.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the get sqlite type
		workflow. The function preserves the existing UI behavior, session-state
		interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	
	Args:
		dtype: str Runtime value used by the `get_sqlite_type` workflow.
	
	Returns:
		str: Result produced by the `get_sqlite_type` workflow.
	"""
	dtype_str = str( dtype ).lower( )
	
	# ------------------------------------------------------------------
	# Integer Types (including nullable Int64)
	# ------------------------------------------------------------------
	if 'int' in dtype_str:
		return 'INTEGER'
	
	# ------------------------------------------------------------------
	# Float Types
	# ------------------------------------------------------------------
	if 'float' in dtype_str:
		return 'REAL'
	
	# ------------------------------------------------------------------
	# Boolean
	# ------------------------------------------------------------------
	if 'bool' in dtype_str:
		return 'INTEGER'
	
	# ------------------------------------------------------------------
	# Datetime
	# ------------------------------------------------------------------
	if 'datetime' in dtype_str:
		return 'TEXT'
	
	# ------------------------------------------------------------------
	# Categorical
	# ------------------------------------------------------------------
	if 'category' in dtype_str:
		return 'TEXT'
	
	# ------------------------------------------------------------------
	# Default fallback
	# ------------------------------------------------------------------
	return 'TEXT'

def create_custom_table( table_name: str, columns: list ) -> None:
	"""Create the custom table used by the application.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the create custom table
		workflow. The function preserves the existing UI behavior, session-state
		interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	
	Args:
		table_name: str value used by the `create_custom_table` workflow.
		columns: list value used by the `create_custom_table` workflow.
	
	Raises:
		Exception: Propagates validation, UI, data, database, or provider errors
			raised by the existing implementation.
	"""
	if not table_name:
		raise ValueError( 'Table name required.' )
	
	# Validate identifier
	if not re.match( r"^[A-Za-z_][A-Za-z0-9_]*$", table_name ):
		raise ValueError( 'Invalid table name.' )
	
	col_defs = [ ]
	
	for col in columns:
		col_name = col[ 'name' ]
		col_type = col[ 'type' ].upper( )
		
		if not re.match( r"^[A-Za-z_][A-Za-z0-9_]*$", col_name ):
			raise ValueError( f"Invalid column name: {col_name}" )
		
		definition = f'"{col_name}" {col_type}'
		
		if col[ 'primary_key' ]:
			definition += ' PRIMARY KEY'
			if col[ 'auto_increment' ] and col_type == 'INTEGER':
				definition += ' AUTOINCREMENT'
		
		if col[ "not_null" ]:
			definition += " NOT NULL"
		
		col_defs.append( definition )
	
	sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({", ".join( col_defs )});'
	
	with create_connection( ) as conn:
		conn.execute( sql )
		conn.commit( )

def is_safe_query( query: str ) -> bool:
	"""Handle the is safe query workflow.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the is safe query workflow.
		The function preserves the existing UI behavior, session-state interactions,
		dataframe handling, database access, and service integrations defined by the
		application code.
	
	Args:
		query: str value used by the `is_safe_query` workflow.
	
	Returns:
		bool: Result produced by the `is_safe_query` workflow.
	"""
	if not query or not isinstance( query, str ):
		return False
	
	q = query.strip( ).lower( )
	
	# ------------------------------------------------------------------
	# Block multiple statements
	# ------------------------------------------------------------------
	if ';' in q[ :-1 ]:
		return False
	
	# ------------------------------------------------------------------
	# Remove SQL comments
	# ------------------------------------------------------------------
	q = re.sub( r"--.*?$", "", q, flags=re.MULTILINE )
	q = re.sub( r"/\*.*?\*/", "", q, flags=re.DOTALL )
	q = q.strip( )
	
	# ------------------------------------------------------------------
	# Allowed starting keywords
	# ------------------------------------------------------------------
	allowed_starts = ('select', 'with', 'explain', 'pragma')
	if not q.startswith( allowed_starts ):
		return False
	
	# ------------------------------------------------------------------
	# Block dangerous keywords anywhere
	# ------------------------------------------------------------------
	blocked_keywords = ('insert ', 'update ', 'delete ', 'drop ', 'alter ',
	                    'create ', 'attach ', 'detach ', 'vacuum ', 'replace ', 'trigger ')
	
	for keyword in blocked_keywords:
		if keyword in q:
			return False
	
	return True

def create_identifier( name: str ) -> str:
	"""Create the identifier used by the application.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the create identifier
		workflow. The function preserves the existing UI behavior, session-state
		interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	
	Args:
		name: str value used by the `create_identifier` workflow.
	
	Returns:
		str: Result produced by the `create_identifier` workflow.
	
	Raises:
		Exception: Propagates validation, UI, data, database, or provider errors
			raised by the existing implementation.
	"""
	if not name or not isinstance( name, str ):
		raise ValueError( 'Invalid Identifier.' )
	
	safe = re.sub( r'[^0-9a-zA-Z_]', '_', name.strip( ) )
	if not re.match( r'^[A-Za-z_]', safe ):
		safe = f'_{safe}'
	
	if not safe:
		raise ValueError( 'Invalid identifier after sanitization.' )
	
	return safe

def get_indexes( table: str ) -> List[ int ]:
	"""Return the indexes used by the application.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the get indexes workflow.
		The function preserves the existing UI behavior, session-state interactions,
		dataframe handling, database access, and service integrations defined by the
		application code.
	
	Args:
		table: str value used by the `get_indexes` workflow.
	
	Returns:
		List[ int ]: Result produced by the `get_indexes` workflow.
	"""
	with create_connection( ) as conn:
		rows = conn.execute( f'PRAGMA index_list("{table}");' ).fetchall( )
		return rows

def add_column( table: str, column: str, col_type: str ):
	"""Handle the add column workflow.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the add column workflow. The
		function preserves the existing UI behavior, session-state interactions, dataframe
		handling, database access, and service integrations defined by the application
		code.
	
	Args:
		table: str value used by the `add_column` workflow.
		column: str value used by the `add_column` workflow.
		col_type: str value used by the `add_column` workflow.
	"""
	column = create_identifier( column )
	col_type = col_type.upper( )
	
	with create_connection( ) as conn:
		conn.execute(
			f'ALTER TABLE "{table}" ADD COLUMN "{column}" {col_type};' )
		conn.commit( )

def rename_column( table_name: str, old_name: str, new_name: str ) -> None:
	"""Handle the rename column workflow.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the rename column workflow.
		The function preserves the existing UI behavior, session-state interactions,
		dataframe handling, database access, and service integrations defined by the
		application code.
	
	Args:
		table_name: str value used by the `rename_column` workflow.
		old_name: str value used by the `rename_column` workflow.
		new_name: str value used by the `rename_column` workflow.
	
	Raises:
		Exception: Propagates validation, UI, data, database, or provider errors
			raised by the existing implementation.
	"""
	if not table_name or not old_name or not new_name:
		return
	
	with create_connection( ) as conn:
		try:
			conn.execute(
				f'ALTER TABLE "{table_name}" RENAME COLUMN "{old_name}" TO "{new_name}";'
			)
			conn.commit( )
			return
		except Exception:
			pass
		
		row = conn.execute(
			"""
            SELECT sql
            FROM sqlite_master
            WHERE type ='table' AND name =?
			""",
			(table_name,)
		).fetchone( )
		
		if not row or not row[ 0 ]:
			raise ValueError( "Table definition not found." )
		
		create_sql = row[ 0 ]
		
		indexes = conn.execute(
			"""
            SELECT sql
            FROM sqlite_master
            WHERE type ='index' AND tbl_name=? AND sql IS NOT NULL
			""",
			(table_name,)
		).fetchall( )
		
		schema = conn.execute( f'PRAGMA table_info("{table_name}");' ).fetchall( )
		cols = [ r[ 1 ] for r in schema ]
		if old_name not in cols:
			raise ValueError( "Column not found." )
		
		mapped_cols = [ (new_name if c == old_name else c) for c in cols ]
		
		temp_table = f"{table_name}__rebuild_temp"
		
		col_defs: List[ str ] = [ ]
		pk_cols = [ r for r in schema if int( r[ 5 ] or 0 ) > 0 ]
		single_pk = len( pk_cols ) == 1
		
		for row in schema:
			col_name = row[ 1 ]
			col_type = row[ 2 ] or ''
			not_null = int( row[ 3 ] or 0 )
			default_value = row[ 4 ]
			pk = int( row[ 5 ] or 0 )
			
			out_name = new_name if col_name == old_name else col_name
			col_def = f'"{out_name}" {col_type}'.strip( )
			
			if not_null:
				col_def += ' NOT NULL'
			
			if default_value is not None:
				col_def += f' DEFAULT {default_value}'
			
			if single_pk and pk == 1:
				col_def += ' PRIMARY KEY'
			
			col_defs.append( col_def )
		
		new_create_sql = f'CREATE TABLE "{temp_table}" ({", ".join( col_defs )});'
		
		old_select = ", ".join( [ f'"{c}"' for c in cols ] )
		new_insert = ", ".join( [ f'"{c}"' for c in mapped_cols ] )
		
		conn.execute( "BEGIN" )
		conn.execute( new_create_sql )
		conn.execute(
			f'INSERT INTO "{temp_table}" ({new_insert}) SELECT {old_select} FROM "{table_name}";'
		)
		
		conn.execute( f'DROP TABLE "{table_name}";' )
		conn.execute( f'ALTER TABLE "{temp_table}" RENAME TO "{table_name}";' )
		
		for idx in indexes:
			idx_sql = idx[ 0 ]
			if idx_sql:
				idx_sql = idx_sql.replace( f'"{old_name}"', f'"{new_name}"' )
				conn.execute( idx_sql )
		
		conn.commit( )

def create_profile_table( table: str ) -> object:
	"""Create the profile table used by the application.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the create profile table
		workflow. The function preserves the existing UI behavior, session-state
		interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	
	Args:
		table: str value used by the `create_profile_table` workflow.
	
	Returns:
		object: Result produced by the `create_profile_table` workflow.
	"""
	df = read_table( table )
	profile_rows = [ ]
	total_rows = len( df )
	for col in df.columns:
		series = df[ col ]
		null_count = series.isna( ).sum( )
		distinct_count = series.nunique( dropna=True )
		row = \
			{
					'column': col, 'dtype': str( series.dtype ),
					'null_%': round( (null_count / total_rows) * 100, 2 ) if total_rows else 0,
					'distinct_%': round( (
							                     distinct_count / total_rows) * 100,
						2 ) if total_rows else 0,
			}
		
		if pd.api.types.is_numeric_dtype( series ):
			row[ 'min' ] = series.min( )
			row[ 'max' ] = series.max( )
			row[ 'mean' ] = series.mean( )
		else:
			row[ 'min' ] = None
			row[ 'max' ] = None
			row[ 'mean' ] = None
		
		profile_rows.append( row )
	
	return pd.DataFrame( profile_rows )

def drop_column( table: str, column: str ):
	"""Handle the drop column workflow.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the drop column workflow.
		The function preserves the existing UI behavior, session-state interactions,
		dataframe handling, database access, and service integrations defined by the
		application code.
	
	Args:
		table: str value used by the `drop_column` workflow.
		column: str value used by the `drop_column` workflow.
	
	Raises:
		Exception: Propagates validation, UI, data, database, or provider errors
			raised by the existing implementation.
	"""
	if not table or not column:
		raise ValueError( 'Table and column required.' )
	
	with create_connection( ) as conn:
		# ------------------------------------------------------------
		# Fetch original CREATE TABLE statement
		# ------------------------------------------------------------
		row = conn.execute(
			"""
            SELECT sql
            FROM sqlite_master
            WHERE type ='table' AND name =?
			""",
			(table,)
		).fetchone( )
		
		if not row or not row[ 0 ]:
			raise ValueError( 'Table definition not found.' )
		
		create_sql = row[ 0 ]
		
		# ------------------------------------------------------------
		# Extract column definitions
		# ------------------------------------------------------------
		open_paren = create_sql.find( "(" )
		close_paren = create_sql.rfind( ")" )
		
		if open_paren == -1 or close_paren == -1:
			raise ValueError( "Malformed CREATE TABLE statement." )
		
		inner = create_sql[ open_paren + 1: close_paren ]
		
		column_defs = [ c.strip( ) for c in inner.split( "," ) ]
		
		# Remove target column
		new_defs = [ ]
		for col_def in column_defs:
			col_name = col_def.split( )[ 0 ].strip( '"' )
			if col_name != column:
				new_defs.append( col_def )
		
		if len( new_defs ) == len( column_defs ):
			raise ValueError( "Column not found." )
		
		# ------------------------------------------------------------
		# Build new CREATE TABLE statement
		# ------------------------------------------------------------
		temp_table = f"{table}_rebuild_temp"
		
		new_create_sql = (
				f'CREATE TABLE "{temp_table}" ('
				+ ", ".join( new_defs )
				+ ");"
		)
		
		# ------------------------------------------------------------
		# Begin transaction
		# ------------------------------------------------------------
		conn.execute( "BEGIN" )
		
		conn.execute( new_create_sql )
		
		remaining_cols = [
				c.split( )[ 0 ].strip( '"' )
				for c in new_defs
		]
		
		col_list = ", ".join( [ f'"{c}"' for c in remaining_cols ] )
		
		conn.execute(
			f'INSERT INTO "{temp_table}" ({col_list}) '
			f'SELECT {col_list} FROM "{table}";'
		)
		
		# Preserve indexes
		indexes = conn.execute(
			"""
            SELECT sql
            FROM sqlite_master
            WHERE type ='index' AND tbl_name=? AND sql IS NOT NULL
			""",
			(table,)
		).fetchall( )
		
		conn.execute( f'DROP TABLE "{table}";' )
		conn.execute(
			f'ALTER TABLE "{temp_table}" RENAME TO "{table}";'
		)
		
		# Recreate indexes
		for idx in indexes:
			idx_sql = idx[ 0 ]
			if column not in idx_sql:
				conn.execute( idx_sql )
		
		conn.commit( )

def rename_table( old_name: str, new_name: str ) -> None:
	"""Handle the rename table workflow.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the rename table workflow.
		The function preserves the existing UI behavior, session-state interactions,
		dataframe handling, database access, and service integrations defined by the
		application code.
	
	Args:
		old_name: str value used by the `rename_table` workflow.
		new_name: str value used by the `rename_table` workflow.
	
	Raises:
		Exception: Propagates validation, UI, data, database, or provider errors
			raised by the existing implementation.
	"""
	if not old_name or not new_name:
		return
	
	with create_connection( ) as conn:
		try:
			conn.execute( f'ALTER TABLE "{old_name}" RENAME TO "{new_name}";' )
			conn.commit( )
			return
		except Exception:
			pass
		
		row = conn.execute(
			"""
            SELECT sql
            FROM sqlite_master
            WHERE type ='table' AND name =?
			""",
			(old_name,)
		).fetchone( )
		
		if not row or not row[ 0 ]:
			raise ValueError( "Table definition not found." )
		
		create_sql = row[ 0 ]
		
		indexes = conn.execute(
			"""
            SELECT sql
            FROM sqlite_master
            WHERE type ='index' AND tbl_name=? AND sql IS NOT NULL
			""",
			(old_name,)
		).fetchall( )
		
		open_paren = create_sql.find( "(" )
		if open_paren == -1:
			raise ValueError( "Malformed CREATE TABLE statement." )
		
		temp_name = f"{new_name}__rebuild_temp"
		
		conn.execute( "BEGIN" )
		conn.execute( f'CREATE TABLE "{temp_name}" {create_sql[ open_paren: ]}' )
		
		cols = [ r[ 1 ] for r in conn.execute( f'PRAGMA table_info("{old_name}");' ).fetchall( ) ]
		col_list = ", ".join( [ f'"{c}"' for c in cols ] )
		
		conn.execute(
			f'INSERT INTO "{temp_name}" ({col_list}) SELECT {col_list} FROM "{old_name}";'
		)
		
		conn.execute( f'DROP TABLE "{old_name}";' )
		conn.execute( f'ALTER TABLE "{temp_name}" RENAME TO "{new_name}";' )
		
		for idx in indexes:
			idx_sql = idx[ 0 ]
			if idx_sql:
				idx_sql = idx_sql.replace( f'ON "{old_name}"', f'ON "{new_name}"' )
				conn.execute( idx_sql )
		
		conn.commit( )

# ------------- DATASET UTILITIES

def has_loaded_dataset( df_frame: object ) -> bool:
	"""Handle the has loaded dataset workflow.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the has loaded dataset
		workflow. The function preserves the existing UI behavior, session-state
		interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	
	Args:
		df_frame: object value used by the `has_loaded_dataset` workflow.
	
	Returns:
		bool: Result produced by the `has_loaded_dataset` workflow.
	"""
	return (
			isinstance( df_frame, pd.DataFrame )
			and not df_frame.empty
			and len( df_frame.columns ) > 0
	)

def get_loaded_dataset( ) -> pd.DataFrame | None:
	"""Return the loaded dataset used by the application.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the get loaded dataset
		workflow. The function preserves the existing UI behavior, session-state
		interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	
	Returns:
		pd.DataFrame | None: Result produced by the `get_loaded_dataset` workflow.
	"""
	df_frame = st.session_state.get( 'df_dataset', None )
	if not has_loaded_dataset( df_frame ):
		return None
	
	return df_frame.copy( )

def store_loaded_dataset( df_dataset: pd.DataFrame,
		df_original: pd.DataFrame | None = None ) -> None:
	"""Handle the store loaded dataset workflow.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the store loaded dataset
		workflow. The function preserves the existing UI behavior, session-state
		interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	
	Args:
		df_dataset: pd.DataFrame value used by the `store_loaded_dataset` workflow.
		df_original: pd.DataFrame | None value used by the `store_loaded_dataset` workflow.
			Defaults to `None`.
	"""
	if not has_loaded_dataset( df_dataset ):
		return
	
	df_source = df_dataset.copy( )
	df_base = df_original.copy( ) if isinstance( df_original, pd.DataFrame ) else df_source.copy( )
	
	st.session_state[ 'df_raw' ] = df_source.copy( )
	st.session_state[ 'df_original' ] = df_base.copy( )
	st.session_state[ 'df_dataset' ] = df_source.copy( )

# ------------ GENERATIVE AI UTILITIES

def _model_selector( key_prefix: str, label: str, options: list[ str ], default_model: str ) -> str:
	"""Handle the model selector workflow.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the model selector workflow.
		The function preserves the existing UI behavior, session-state interactions,
		dataframe handling, database access, and service integrations defined by the
		application code.
	
	Args:
		key_prefix: str value used by the `_model_selector` workflow.
		label: str value used by the `_model_selector` workflow.
		options: list[str] value used by the `_model_selector` workflow.
		default_model: str value used by the `_model_selector` workflow.
	
	Returns:
		str: Result produced by the `_model_selector` workflow.
	"""
	base_options = list( options or [ ] )
	default_value = str( default_model or '' ).strip( )
	
	if default_value and default_value not in base_options:
		base_options.insert( 0, default_value )
	
	if 'Custom...' not in base_options:
		base_options.append( 'Custom...' )
	
	idx_default = base_options.index( default_value ) if default_value in base_options else 0
	
	selected = st.selectbox(
		label=label,
		options=base_options,
		index=idx_default,
		key=f'{key_prefix}_model_select'
	)
	
	if selected == 'Custom...':
		return st.text_input(
			'Custom Model',
			value=default_value,
			key=f'{key_prefix}_model_custom'
		)
	
	return str( selected or '' ).strip( )

def _invoke_provider( fetcher: object, prompt: str, params: Dict[ str, Any ] ) -> Any:
	"""Handle the invoke provider workflow.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the invoke provider
		workflow. The function preserves the existing UI behavior, session-state
		interactions, dataframe handling, database access, and service integrations
		defined by the application code.
	
	Args:
		fetcher: object value used by the `_invoke_provider` workflow.
		prompt: str value used by the `_invoke_provider` workflow.
		params: Dict[str, Any] value used by the `_invoke_provider` workflow.
	
	Returns:
		Any: Result produced by the `_invoke_provider` workflow.
	
	Raises:
		Exception: Propagates validation, UI, data, database, or provider errors
			raised by the existing implementation.
	"""
	try:
		if fetcher is None:
			raise ValueError( 'Provider wrapper cannot be None.' )
		
		if not hasattr( fetcher, 'fetch' ):
			raise TypeError( 'Provider wrapper must expose a fetch method.' )
		
		text = str( prompt or '' ).strip( )
		if not text:
			raise ValueError( 'Prompt cannot be empty.' )
		
		arguments = dict( params or { } )
		provider_name = type( fetcher ).__name__
		
		if provider_name in ('Chat', 'Gemini'):
			return fetcher.fetch( prompt=text, **arguments )
		
		if provider_name in ('Grok', 'Claude', 'Mistral'):
			return fetcher.fetch( query=text, **arguments )
		
		try:
			return fetcher.fetch( prompt=text, **arguments )
		except TypeError:
			return fetcher.fetch( query=text, **arguments )
	
	except Exception as ex:
		raise ex

def _render_output( placeholder: object, result: Any ) -> None:
	"""Handle the render output workflow.
	
	Purpose:
		Supports the Mappy Streamlit application by executing the render output workflow.
		The function preserves the existing UI behavior, session-state interactions,
		dataframe handling, database access, and service integrations defined by the
		application code.
	
	Args:
		placeholder: object value used by the `_render_output` workflow.
		result: Any value used by the `_render_output` workflow.
	
	Raises:
		Exception: Propagates validation, UI, data, database, or provider errors
			raised by the existing implementation.
	"""
	try:
		if placeholder is None:
			raise ValueError( 'Output placeholder cannot be None.' )
		
		if result is None:
			placeholder.info( 'No response was returned.' )
			return
		
		if isinstance( result, str ):
			text = result.strip( )
			if not text:
				placeholder.info( 'No response text was returned.' )
				return
			
			try:
				parsed = json.loads( text )
				placeholder.json( parsed )
				return
			except Exception:
				placeholder.markdown( text )
				return
		
		if isinstance( result, (dict, list, tuple) ):
			placeholder.json( result )
			return
		
		if hasattr( result, 'model_dump' ):
			placeholder.json( result.model_dump( ) )
			return
		
		if hasattr( result, 'to_dict' ):
			placeholder.json( result.to_dict( ) )
			return
		
		placeholder.markdown( str( result ) )
	
	except Exception as ex:
		st.error( f'Unable to render provider output: {ex}' )

# ---------------------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------------------

st.set_page_config( page_title='Mappy', layout='wide', page_icon=cfg.FAVICON,
	initial_sidebar_state='expanded', )

style_subheaders( )

# ==============================================================================
# SIDEBAR
# ==============================================================================
st.logo( cfg.LOGO, size='Large' )
with st.sidebar:
	# ------- Map Mode
	set_blue_divider( )
	st.markdown( '#### 🛰️ GIS Mapping' )
	with st.expander( 'Mode', expanded=True ):
		mode = st.radio( label='Mode', options=cfg.MODES, label_visibility='collapsed' )
		if mode:
			st.session_state[ 'mode' ] = mode
		else:
			st.sessionn_state[ 'mode' ] = 'Geocoding'
		
		previous_mode = st.session_state.get( 'previous_mode', None )
		if previous_mode != mode:
			st.session_state[ 'previous_mode' ] = mode
			st.rerun( )
	
	# -------- Settings
	set_blue_divider( )
	st.markdown( '#### 🎚️ Configuration' )
	
	# ------- User Location
	with st.expander( label='Location', expanded=False ):
		st.checkbox( 'Use browser location on load',
			value=st.session_state.get( 'browser_geolocation_enabled', True ),
			key='browser_geolocation_enabled' )
		
		if st.session_state.get( 'browser_geolocation_loaded', False ):
			st.success( 'Browser location loaded.' )
			st.write( f"Latitude: {float( st.session_state.get( 'latitude', 0.0 ) ):.6f}" )
			st.write( f"Longitude: {float( st.session_state.get( 'longitude', 0.0 ) ):.6f}" )
		
		elif st.session_state.get( 'browser_geolocation_permission_denied', False ):
			st.warning( 'Browser location permission was denied.' )
		
		else:
			st.info( 'Browser location has not been loaded yet.' )
		
		error = st.session_state.get( 'browser_geolocation_error', '' )
		if error:
			st.warning( error )
		
		if st.button( 'Reset', key='browser_geolocation_reset', width='stretch' ):
			st.session_state[ 'browser_geolocation' ] = None
			st.session_state[ 'browser_geolocation_loaded' ] = False
			st.session_state[ 'browser_geolocation_reverse_geocoded' ] = False
			st.session_state[ 'browser_geolocation_error' ] = ''
			st.session_state[ 'browser_geolocation_permission_denied' ] = False
			st.rerun( )
	
	# ------- Query
	with st.expander( label='Frequency', expanded=False ):
		qps = st.slider( 'Queries Per Second', min_value=1, max_value=50, value=10, )
	
	# ------- Cache
	with st.expander( label='Persistence', expanded=False ):
		cache_backend = st.selectbox( 'Select', options=[ 'none', 'memory', 'sqlite' ],
			key='cache_backend' )
		cache: Optional[ object ] = None
		if cache_backend == 'memory':
			cache = InMemoryCache( )
		elif cache_backend == 'sqlite':
			cache_path = st.text_input( 'SQLite Cache Path', value='mappy_cache.db', )
			cache = SQLiteCache( cache_path )
	
	# ------- Data
	set_blue_divider( )
	st.markdown( '#### 🏛️ Data' )
	with st.expander( label='Source', expanded=False ):
		st.caption( 'Sources' )
		source = st.selectbox( label='Select Table',
			options=[ 'Default Data', 'Database Data', 'Custom Data' ], key='source_selectbox' )
		
		uploaded = st.file_uploader( label='Upload Spreadsheet', type=[ 'xlsx', 'xls', 'csv' ],
			key='source_uploader' )
		
		df_default = pd.DataFrame( )
		df_original = pd.DataFrame( )
		df_tables = pd.DataFrame( columns=[ 'name' ] )
		database_path = Path( cfg.DB_PATH )
		database_folder = database_path.parent
		
		if database_folder and str( database_folder ) not in ('.', ''):
			database_folder.mkdir( parents=True, exist_ok=True )
		
		if source == 'Default Data':
			try:
				with sqlite3.connect( cfg.DB_PATH ) as connection:
					df_tables = pd.read_sql_query(
						"""
                        SELECT name
                        FROM sqlite_master
                        WHERE type = 'table'
                          AND name NOT LIKE 'sqlite_%'
                        ORDER BY name;
						""",
						connection )
					
					table_options = df_tables[ 'name' ].tolist( ) \
						if 'name' in df_tables.columns else [ ]
					
					if cfg.DEFAULT_DATA in table_options:
						table_name = str( cfg.DEFAULT_DATA ).replace( '"', '""' )
						df_default = pd.read_sql_query( f'SELECT * FROM "{table_name}"',
							connection )
						
						df_original = df_default.copy( )
						log_step( f'Loaded Database Table: {cfg.DEFAULT_DATA}' )
					else:
						st.warning(
							f'Default table "{cfg.DEFAULT_DATA}" was not found in the database.' )
			
			except Exception as ex:
				st.error( f'Error loading default data: {ex}' )
		
		elif source == 'Database Data':
			try:
				with sqlite3.connect( cfg.DB_PATH ) as connection:
					df_tables = pd.read_sql_query(
						"""
                        SELECT name
                        FROM sqlite_master
                        WHERE type = 'table'
                          AND name NOT LIKE 'sqlite_%'
                        ORDER BY name;
						""",
						connection )
					
					table_options = df_tables[ 'name' ].tolist( )[ :3 ] \
						if 'name' in df_tables.columns else [ ]
					
					if table_options:
						selected_table = st.selectbox( label='Select Database Table',
							options=table_options, key='database_table_selectbox' )
						
						if selected_table:
							table_name = str( selected_table ).replace( '"', '""' )
							df_default = pd.read_sql_query( f'SELECT * FROM "{table_name}"',
								connection )
							
							df_original = df_default.copy( )
							log_step( f'Loaded Database Table: {selected_table}' )
					else:
						st.warning( 'No tables were found in the database.' )
			
			except Exception as ex:
				st.error( f'Error loading database data: {ex}' )
		
		elif source == 'Custom Data':
			try:
				if uploaded is not None:
					if uploaded.name.lower( ).endswith( ('.xlsx', '.xls') ):
						df_default = pd.read_excel( uploaded )
					else:
						df_default = pd.read_csv( uploaded )
					
					df_original = df_default.copy( )
					log_step( f'Loaded uploaded file: {uploaded.name}' )
				else:
					st.info( 'Upload a spreadsheet to load data.' )
			
			except Exception as ex:
				st.error( f'Error loading uploaded data: {ex}' )
		
		if has_loaded_dataset( df_default ):
			store_loaded_dataset( df_default, df_original )
	
	# ------- Security
	set_blue_divider( )
	st.markdown( '#### 🔒 Credentials' )
	with st.expander( label='API', expanded=False ):
		google_key = st.text_input( 'Google API Key', type='password',
			value=st.session_state.google_api_key or '',
			help='Overrides GOOGLE_API_KEY from config.py for this session only.' )
		
		if google_key:
			st.session_state.google_api_key = google_key
			os.environ[ 'GOOGLE_API_KEY' ] = google_key
		
		googlemaps_key = st.text_input( 'Google Maps API Key', type='password',
			value=st.session_state.googlemaps_api_key or '',
			help='Overrides GOOGLEMAPS_API_KEY from config.py for this session only.' )
		
		if googlemaps_key:
			st.session_state.googlemaps_api_key = googlemaps_key
			os.environ[ 'GOOGLEMAPS_API_KEY' ] = googlemaps_key
		
		googleweather_key = st.text_input( 'Google Weather API Key', type='password',
			value=st.session_state.google_weather_api_key or '',
			help='Overrides GOOGLE_WEATHER_API_KEY from config.py for this session only.' )
		
		if googleweather_key:
			st.session_state.google_weather_api_key = googleweather_key
			os.environ[ 'GOOGLE_WEATHER_API_KEY' ] = googleweather_key
		
		geocoding_key = st.text_input( 'Geocoding API Key', type='password',
			value=st.session_state.geocoding_api_key or '',
			help='Overrides GEOCODING_API_KEY from config.py for this session only.' )
		
		if geocoding_key:
			st.session_state.geocoding_api_key = geocoding_key
			os.environ[ 'GEOCODING_API_KEY' ] = geocoding_key
		
		google_cse_id = st.text_input( 'Google Custom Search ID', type='password',
			value=st.session_state.google_cse_id or '',
			help='Overrides GOOGLE_CSE_ID from config.py for this session only.' )
		
		if google_cse_id:
			st.session_state.google_cse_id = google_cse_id
			os.environ[ 'GOOGLE_CSE_ID' ] = google_cse_id
		
		govinfo_key = st.text_input( 'Gov Info API', type='password',
			value=st.session_state.govinfo_api_key or '',
			help='Overrides GOVINFO_API_KEY from config.py for this session only.' )
		
		if govinfo_key:
			st.session_state.govinfo_api_key = govinfo_key
			os.environ[ 'GOVINFO_API_KEY' ] = govinfo_key
		
		airnow_key = st.text_input( 'Air Quality Now', type='password',
			value=st.session_state.airnow_api_key or '',
			help='Overrides AIRNOW_API_KEY from config.py for this session only.' )
		
		if airnow_key:
			st.session_state.airnow_api_key = airnow_key
			os.environ[ 'AIRNOW_API_KEY' ] = airnow_key
		
		nasa_key = st.text_input( 'NASA API Key', type='password',
			value=st.session_state.nasa_api_key or '',
			help='Overrides NASA_API_KEY from config.py for this session only.' )
		
		if nasa_key:
			st.session_state.nasa_api_key = nasa_key
			os.environ[ 'NASA_API_KEY' ] = nasa_key
		
		nasa_token = st.text_input( 'NASA Earth Data', type='password',
			value=st.session_state.nasa_earthdata_token or '',
			help='Overrides NASA_EARTHDATA_TOKEN from config.py for this session only.' )
		
		if nasa_token:
			st.session_state.nasa_earthdata_token = nasa_token
			os.environ[ 'NASA_EARTHDATA_TOKEN' ] = nasa_token
		
		openaq_key = st.text_input( 'Open Air Quality', type='password',
			value=st.session_state.openaq_api_key or '',
			help='Overrides OPENAQ_API_KEY from config.py for this session only.' )
		
		if openaq_key:
			st.session_state.openaq_api_key = openaq_key
			os.environ[ 'OPENAQ_API_KEY' ] = openaq_key
		
		opensky_client = st.text_input( 'Open Sky Client ID', type='password',
			value=st.session_state.opensky_api_client_id or '',
			help='Overrides OPENSKY_API_CLIENT_ID from config.py for this session only.' )
		
		if opensky_client:
			st.session_state.opensky_api_client_id = opensky_client
			os.environ[ 'OPENSKY_API_CLIENT_ID' ] = opensky_client
		
		firms_key = st.text_input( 'FIRMS Map Client', type='password',
			value=st.session_state.firms_map_key or '',
			help='Overrides FIRMS_MAP_KEY from config.py for this session only.' )
		
		if firms_key:
			st.session_state.firms_map_key = firms_key
			os.environ[ 'FIRMS_MAP_KEY' ] = firms_key
		
		opensky_credentials = st.text_input( 'Open Sky Credentials', type='password',
			value=st.session_state.opensky_api_credentials or '',
			help='Overrides OPENSKY_API_CREDENTIALS from config.py for this session only.' )
		
		if opensky_credentials:
			st.session_state.opensky_api_credentials = opensky_credentials
			os.environ[ 'OPENSKY_API_CREDENTIALS' ] = opensky_credentials
		
		purpleair_key = st.text_input( 'Purple Air API', type='password',
			value=st.session_state.purpleair_api_key or '',
			help='Overrides Purple Air API from config.py for this session only.' )
		
		if purpleair_key:
			st.session_state.purpleair_api_key = purpleair_key
			os.environ[ 'PURPLEAIR_API_KEY' ] = purpleair_key
		
		openai_key = st.text_input( 'OpenAI API', type='password',
			value=st.session_state.openai_api_key or '',
			help='Overrides OpenAI API from config.py for this session only.' )
		
		if openai_key:
			st.session_state.openai_api_key = openai_key
			os.environ[ 'OPENAI_API_KEY' ] = openai_key
		
		gemini_key = st.text_input( 'Gemini API', type='password',
			value=st.session_state.gemini_api_key or '',
			help='Overrides Gemini API from config.py for this session only.' )
		
		if gemini_key:
			st.session_state.gemini_api_key = gemini_key
			os.environ[ 'GEMINI_API_KEY' ] = gemini_key
		
		claude_key = st.text_input( 'Claude API', type='password',
			value=st.session_state.claude_api_key or '',
			help='Overrides Claude API from config.py for this session only.' )
		
		if claude_key:
			st.session_state.claude_api_key = claude_key
			os.environ[ 'CLAUDE_API_KEY' ] = claude_key
		
		mistral_key = st.text_input( 'Mistral API', type='password',
			value=st.session_state.mistral_api_key or '',
			help='Overrides Mistral API from config.py for this session only.' )
		
		if mistral_key:
			st.session_state.mistral_api_key = mistral_key
			os.environ[ 'MISTRAL_API_KEY' ] = mistral_key
		
		xai_key = st.text_input( 'xAI API', type='password',
			value=st.session_state.xai_api_key or '',
			help='Overrides xAI API from config.py for this session only.' )
		
		if xai_key:
			st.session_state.xai_api_key = xai_key
			os.environ[ 'XAI_API_KEY' ] = xai_key
	
	maps = Maps( qps=qps, )
	distances = DistanceMatrix( maps )
	timezone = Timezone( maps )
	geocoder = Geocoder( maps, cache=cache )
	places = Place( maps, cache=cache )
	static_maps = StaticMap( )

# ------------------------------------------------------------------------------
# BROWSER GEOLOCATION BOOTSTRAP
# ------------------------------------------------------------------------------
bootstrap_browser_geolocation( geocoder )

# ==============================================================================
# GEOCODING MODE
# ==============================================================================
if mode == 'Geocoding':
	left, center, right = st.columns( [ 0.05, 0.9, 0.05 ] )
	with center:
		st.subheader( 'Geocoding' )
		st.divider( )
		
		geo_c1, geo_c2 = st.columns( [ 0.60, 0.40 ], border=True, gap='small' )
		with geo_c2:
			st.caption( '' )
			geosub_c1, geosub_c2 = st.columns( 2 )
			with geosub_c1:
				use_places = st.checkbox( 'Use Places fallback', value=True,
					key='geocoding_fallback' )
			
			with geosub_c2:
				if st.button( label='Clear Map Results', icon='💫', width='stretch',
						key='clear_map_results' ):
					st.session_state[ 'df_geocoding_map_results' ] = pd.DataFrame( )
					st.rerun( )
		
		with geo_c1:
			query = st.text_input( 'Enter Address or Location', key='location' )
			btn_c1, btn_c2 = st.columns( 2 )
			with btn_c1:
				if st.button( 'Resolve Location', width='stretch', icon='📍' ):
					if not query:
						st.warning( 'Enter a Location.' )
					else:
						try:
							result = geocoder.freeform( query )
							append_geocoding_map_result( query, 'Geocoder', result )
							st.json( result )
						except NotFound:
							if use_places:
								try:
									st.warning( 'Geocoding failed.' )
									result = places.text_to_location( query )
									append_geocoding_map_result( query, 'Places', result )
									st.json( result )
								except Exception as e:
									st.error( str( e ) )
							else:
								st.warning( 'Geocoding failed and Places fallback is disabled.' )
						except Exception as e:
							st.error( str( e ) )
			
			with btn_c2:
				if st.button( label='Clear Location', width='stretch', icon='🧹' ):
					st.info( 'Use Ctrl+A / Backspace to clear the location field.' )
		
		st.divider( )
		
		# ------------------------------------------------------------------------------
		# REPORTS MAP
		# ------------------------------------------------------------------------------
		try:
			tables = list_tables( )
			if cfg.DEFAULT_DATA not in tables:
				st.warning( f'Default table "{cfg.DEFAULT_DATA}" was not found in {cfg.DB_PATH}.' )
			else:
				df_reports = read_table( cfg.DEFAULT_DATA )
				df_overlay = st.session_state.get( 'df_geocoding_map_results', pd.DataFrame( ) )
				create_reports_map( df_reports, df_overlay=df_overlay )
				if df_overlay is not None and not df_overlay.empty:
					with st.expander( 'Geocoded Map Results', expanded=False ):
						st.data_editor( df_overlay, key='geocoding_map_results_table',
							use_container_width=True, disabled=True )
		
		except Exception as e:
			st.error( f'Reports map failed: {e}' )

# ==============================================================================
# MAP MODE
# ==============================================================================
elif mode == 'Interactive Map':
	left, center, right = st.columns( [ 0.05, 0.9, 0.05 ] )
	with center:
		st.subheader( 'Interactive Map' )
		st.divider( )
		tables = list_tables( )
		if not tables:
			st.info( 'No tables available.' )
		else:
			default_table = resolve_table_name( cfg.DEFAULT_DATA, tables )
			if default_table is None:
				default_table = tables[ 0 ]
			
			default_index = tables.index( default_table )
			
			control_c1, control_c2, control_c3 = st.columns( [ 0.35, 0.35, 0.30 ], border=True )
			with control_c1:
				table = st.selectbox( 'Table', tables, index=default_index,
					key='map_mode_table' )
			
			with control_c2:
				include_overlay = st.checkbox( 'Show Geocoded Overlay', value=True,
					key='map_mode_show_overlay' )
			
			with control_c3:
				refresh_map = st.button( label='Refresh Map', key='map_mode_refresh', icon='🔄',
					width='stretch' )
				
				if refresh_map:
					st.rerun( )
			
			df_map_source = read_table( table )
			df_overlay = pd.DataFrame( )
			
			if include_overlay:
				df_overlay = st.session_state.get( 'df_geocoding_map_results',
					pd.DataFrame( ) )
			
			create_reports_map( df_map_source, df_overlay=df_overlay )
			if include_overlay and df_overlay is not None and not df_overlay.empty:
				with st.expander( 'Geocoded Overlay Records', expanded=False ):
					st.data_editor( df_overlay, key='map_mode_overlay_records',
						use_container_width=True, disabled=True )

# ==============================================================================
# DISTANCES MODE
# ==============================================================================
elif mode == 'Distances':
	left, center, right = st.columns( [ 0.05, 0.9, 0.05 ] )
	with center:
		st.subheader( 'Distance Matrix' )
		st.divider( )
		
		global_location = get_default_location( )
		location_state = get_location_state( )
		current_location = compose_location_from_state( )
		
		status_c1, status_c2, status_c3 = st.columns( 3, border=True )
		status_c1.metric( 'Location', current_location if current_location else global_location )
		status_c2.metric( 'Latitude', f'{float( location_state[ "latitude" ] ):.4f}' )
		status_c3.metric( 'Longitude', f'{float( location_state[ "longitude" ] ):.4f}' )
		
		set_blue_divider( )
		
		dist_c1, dist_c2 = st.columns( [ 0.50, 0.50 ], border=True )
		
		with dist_c1:
			use_global_origin = st.checkbox( 'Use User-Location as Origin',
				value=bool( current_location ), key='distance_use_global_origin' )
			
			if use_global_origin:
				origin = current_location
				st.text_input( 'Origin', value=origin, key='distance_origin_display',
					disabled=True )
			else:
				origin_default = st.session_state.get( 'origin', '' ) or current_location
				origin = st.text_input( 'Origin', value=origin_default,
					key='distance_origin_input' )
		
		with dist_c2:
			use_global_destination = st.checkbox( 'Use User-Location as Destination', value=False,
				key='distance_use_global_destination' )
			
			if use_global_destination:
				destination = current_location
				st.text_input( 'Destination', value=destination, key='distance_destination_display',
					disabled=True )
			else:
				destination_default = st.session_state.get( 'destination', '' )
				destination = st.text_input( 'Destination', value=destination_default,
					key='distance_destination_input' )
		
		ctl_c1, ctl_c2, ctl_c3 = st.columns( [ 0.30, 0.30, 0.40 ], border=True )
		with ctl_c1:
			travel_mode = st.selectbox( 'Travel Mode',
				[ 'driving', 'walking', 'bicycling', 'transit' ], key='travel_key' )
		
		with ctl_c2:
			update_global_route = st.checkbox( 'Save Route to Global State', value=True,
				key='distance_save_route_state' )
		
		with ctl_c3:
			run_distance = st.button( 'Calculate Distance', key='distance_calculate', icon='📐',
				width='stretch' )
		
		if run_distance:
			if not origin or not destination:
				st.warning( 'Provide both origin and destination.' )
			else:
				try:
					if update_global_route:
						st.session_state[ 'origin' ] = str( origin ).strip( )
						st.session_state[ 'destination' ] = str( destination ).strip( )
					
					summary = distances.summary( origin, destination, mode=travel_mode )
					st.session_state[ 'distance_last_result' ] = summary or { }
					st.success( 'Distance Matrix request completed.' )
				
				except Exception as ex:
					st.error( f'Distance Matrix request failed: {ex}' )
		
		result = st.session_state.get( 'distance_last_result', { } )
		if result:
			set_blue_divider( )
			st.markdown( '##### Distance Result' )
			st.data_editor( pd.DataFrame( [ result ] ), key='distance_result_table',
				use_container_width=True, disabled=True )
			st.json( result )

# ==============================================================================
# MAPS MODE
# ==============================================================================
elif mode == 'Static Maps':
	left, center, right = st.columns( [ 0.05, 0.9, 0.05 ] )
	with center:
		st.subheader( 'Static Map' )
		st.divider( )
		
		global_location = get_default_location( )
		location_state = get_location_state( )
		has_global_coords = has_valid_global_coordinates( )
		
		status_c1, status_c2, status_c3 = st.columns( 3, border=True )
		status_c1.metric( 'Location', compose_location_from_state( ) or global_location )
		status_c2.metric( 'Latitude', f'{float( location_state[ "latitude" ] ):.4f}' )
		status_c3.metric( 'Longitude', f'{float( location_state[ "longitude" ] ):.4f}' )
		
		set_blue_divider( )
		
		map_c1, map_c2 = st.columns( [ 0.50, 0.50 ], border=True )
		with map_c1:
			use_global_coordinates = st.checkbox( 'Use User-Location', value=has_global_coords,
				key='maps_use_global_coordinates' )
			
			if use_global_coordinates:
				lat = float( location_state[ 'latitude' ] )
				lng = float( location_state[ 'longitude' ] )
				
				coord_c1, coord_c2 = st.columns( 2 )
				with coord_c1:
					st.number_input( 'Latitude', value=lat, format='%.4f',
						key='maps_global_latitude_display', disabled=True )
				
				with coord_c2:
					st.number_input( 'Longitude', value=lng, format='%.4f',
						key='maps_global_longitude_display', disabled=True )
			
			else:
				manual_default_lat = (float( location_state[ 'latitude' ] )
				                      if has_global_coords
				                      else 0.0)
				
				manual_default_lng = (float( location_state[ 'longitude' ] )
				                      if has_global_coords
				                      else 0.0)
				
				coord_c1, coord_c2 = st.columns( 2 )
				with coord_c1:
					lat = st.number_input( 'Latitude', value=manual_default_lat, format='%.4f',
						key='maps_manual_latitude' )
				
				with coord_c2:
					lng = st.number_input( 'Longitude', value=manual_default_lng, format='%.4f',
						key='maps_manual_longitude' )
		
		with map_c2:
			zoom_default = int( st.session_state.get( 'zoom', 8 ) or 8 )
			size_default = str( st.session_state.get( 'map_size', '600x400' ) or '600x400' )
			size_options = [ '400x400', '600x400', '800x600' ]
			
			if size_default not in size_options:
				size_default = '600x400'
			
			zoom = st.slider( 'Zoom', min_value=1, max_value=20, value=zoom_default,
				key='maps_zoom' )
			
			size = st.selectbox( 'Image Size', size_options,
				index=size_options.index( size_default ), key='maps_size' )
			
			save_coordinates = st.checkbox( 'Save Coordinates to Global State', value=True,
				key='maps_save_coordinates' )
		
		if st.button( 'Generate Map', icon='🗺️', key='maps_generate', width='content' ):
			if use_global_coordinates and not has_global_coords:
				st.warning( 'User coordinates are not set.' )
			elif not has_valid_coordinates( lat, lng ):
				st.warning( 'Provide valid coordinates before generating a map.' )
			else:
				try:
					if save_coordinates:
						set_coordinates( lat, lng )
						st.session_state[ 'zoom' ] = int( zoom )
						st.session_state[ 'map_size' ] = str( size )
					
					url = static_maps.pin(
						lat=float( lat ),
						lng=float( lng ),
						zoom=int( zoom ),
						size=str( size ) )
					
					st.session_state[ 'maps_last_url' ] = url
					st.session_state[ 'maps_last_latitude' ] = float( lat )
					st.session_state[ 'maps_last_longitude' ] = float( lng )
					st.success( 'Static map generated.' )
				
				except Exception as ex:
					st.error( f'Static map generation failed: {ex}' )
		
		map_url = st.session_state.get( 'maps_last_url', '' )
		
		if map_url:
			set_blue_divider( )
			st.markdown( '##### Static Map Result' )
			st.image( map_url )
			st.code( map_url )

# ==============================================================================
# TIME ZONE MODE
# ==============================================================================
elif mode == 'Time Zones':
	left, center, right = st.columns( [ 0.05, 0.9, 0.05 ] )
	with center:
		st.subheader( 'Time Zone Lookup' )
		st.divider( )
		
		global_location = get_default_location( )
		location_state = get_location_state( )
		has_global_coords = has_valid_global_coordinates( )
		
		status_c1, status_c2, status_c3 = st.columns( 3, border=True )
		status_c1.metric( 'Location', compose_location_from_state( ) or global_location )
		status_c2.metric( 'Latitude', f'{float( location_state[ "latitude" ] ):.4f}' )
		status_c3.metric( 'Longitude', f'{float( location_state[ "longitude" ] ):.4f}' )
		
		set_blue_divider( )
		
		tz_c1, tz_c2 = st.columns( [ 0.50, 0.50 ], border=True )
		with tz_c1:
			use_global_coordinates = st.checkbox( 'User Location', value=has_global_coords,
				key='timezone_use_global_coordinates' )
			
			if use_global_coordinates:
				lat_tz = float( location_state[ 'latitude' ] )
				lng_tz = float( location_state[ 'longitude' ] )
				
				coord_c1, coord_c2 = st.columns( 2 )
				with coord_c1:
					st.number_input(
						'Latitude',
						value=lat_tz,
						format='%.6f',
						key='timezone_global_latitude_display',
						disabled=True )
				
				with coord_c2:
					st.number_input(
						'Longitude',
						value=lng_tz,
						format='%.6f',
						key='timezone_global_longitude_display',
						disabled=True )
			
			else:
				manual_default_lat = (
						float( location_state[ 'latitude' ] )
						if has_global_coords
						else 0.0)
				
				manual_default_lng = (
						float( location_state[ 'longitude' ] )
						if has_global_coords
						else 0.0)
				
				coord_c1, coord_c2 = st.columns( 2 )
				with coord_c1:
					lat_tz = st.number_input(
						'Latitude',
						value=manual_default_lat,
						format='%.6f',
						key='timezone_manual_latitude' )
				
				with coord_c2:
					lng_tz = st.number_input(
						'Longitude',
						value=manual_default_lng,
						format='%.6f',
						key='timezone_manual_longitude' )
		
		with tz_c2:
			save_coordinates = st.checkbox( 'Save Coordinates to Global State', value=True,
				key='timezone_save_coordinates' )
			
			run_timezone = st.button( 'Lookup Time Zone', key='timezone_lookup', icon='🔍',
				width='content' )
		
		if run_timezone:
			if use_global_coordinates and not has_global_coords:
				st.warning(
					'Global coordinates are not set. Resolve a location first or enter manually.' )
			elif not has_valid_coordinates( lat_tz, lng_tz ):
				st.warning( 'Provide valid coordinates before looking up a time zone.' )
			else:
				try:
					if save_coordinates:
						set_coordinates( lat_tz, lng_tz )
					
					result = timezone.lookup( float( lat_tz ), float( lng_tz ) )
					
					st.session_state[ 'timezone_last_result' ] = result or { }
					st.session_state[ 'timezone_last_latitude' ] = float( lat_tz )
					st.session_state[ 'timezone_last_longitude' ] = float( lng_tz )
					st.success( 'Time zone lookup completed.' )
				
				except Exception as ex:
					st.error( f'Time zone lookup failed: {ex}' )
		
		result = st.session_state.get( 'timezone_last_result', { } )
		
		if result:
			set_blue_divider( )
			st.markdown( '##### Time Zone Result' )
			
			lat_c, lng_c = st.columns( 2 )
			with lat_c:
				st.metric(
					'Latitude',
					f'{float( st.session_state.get( "timezone_last_latitude", 0.0 ) ):.6f}' )
			with lng_c:
				st.metric(
					'Longitude',
					f'{float( st.session_state.get( "timezone_last_longitude", 0.0 ) ):.6f}' )
			
			st.json( result )

# =============================================================================
# SCRAPING MODE
# ==============================================================================
elif mode == 'Web Scraper':
	from processing import render_web_document_processing

	left, center, right = st.columns( [ 0.05, 0.9, 0.05 ] )
	with center:
		st.subheader( f'🕷️ Web Scraping' )
		st.divider( )

		if 'webscrape_clear_request' not in st.session_state:
			st.session_state[ 'webscrape_clear_request' ] = False

		if 'webscrape_results' not in st.session_state:
			st.session_state[ 'webscrape_results' ] = [ ]

		if 'webscrape_summary' not in st.session_state:
			st.session_state[ 'webscrape_summary' ] = { }

		if st.session_state.get( 'webscrape_clear_request', False ):
			st.session_state[ 'webfetcher_url' ] = ''
			st.session_state[ 'webscrape_results' ] = [ ]
			st.session_state[ 'webscrape_summary' ] = { }
			st.session_state[ 'webscrape_clear_request' ] = False

		def clear_webscrape_state( ) -> None:
			"""Clear the webscrape state state.

			Purpose:
				Supports the Mappy Streamlit application by executing the clear webscrape state
				workflow. The function preserves the existing UI behavior, session-state
				interactions, dataframe handling, database access, and service integrations
				defined by the application code.
			"""
			st.session_state[ 'webscrape_clear_request' ] = True

		col_left, col_right = st.columns( [ 1, 2 ], border=True )

		with col_left:
			target_url = st.text_input(
				'Enter Target URL',
				placeholder='https://example.com',
				key='webfetcher_url' )

			st.markdown( '##### Core Output' )

			include_title = st.checkbox(
				'Page Title',
				value=True,
				key='wf_page_title' )

			include_basic_text = st.checkbox(
				'Basic Text',
				value=True,
				key='wf_basic_text' )

			include_raw_html = st.checkbox(
				'Raw HTML',
				value=False,
				key='wf_raw_html' )

			st.markdown( cfg.BLUE_DIVIDER, unsafe_allow_html=True )

			st.markdown( '##### Structured Extraction' )

			method_c1, method_c2 = st.columns( [ 0.5, 0.5 ] )

			registry_labels = {
					'scrape_headings': 'Headings',
					'scrape_paragraphs': 'Paragraphs',
					'scrape_lists': 'Lists',
					'scrape_tables': 'Tables',
					'scrape_articles': 'Articles',
					'scrape_sections': 'Sections',
					'scrape_divisions': 'Divisions',
					'scrape_blockquotes': 'Blockquotes',
					'scrape_hyperlinks': 'Hyperlinks',
					'scrape_images': 'Images',
			}

			selected_methods = [ ]
			registry_items = list( registry_labels.items( ) )

			with method_c1:
				for method_name, label in registry_items[ :5 ]:
					if st.checkbox( label, key=f'wf_{method_name}' ):
						selected_methods.append( method_name )

			with method_c2:
				for method_name, label in registry_items[ 5: ]:
					if st.checkbox( label, key=f'wf_{method_name}' ):
						selected_methods.append( method_name )

			st.markdown( cfg.BLUE_DIVIDER, unsafe_allow_html=True )

			st.markdown( '##### Crawl Controls' )

			enable_recursive = st.checkbox(
				'Recursive Crawl',
				value=False,
				key='wf_recursive' )

			max_depth = st.number_input(
				'Max Depth',
				min_value=0,
				max_value=10,
				value=1,
				step=1,
				key='wf_max_depth',
				disabled=(not enable_recursive) )

			max_pages = st.number_input(
				'Max Pages',
				min_value=1,
				max_value=500,
				value=10,
				step=1,
				key='wf_max_pages' )

			same_domain_only = st.checkbox(
				'Same Domain Only',
				value=True,
				key='wf_same_domain_only',
				disabled=(not enable_recursive) )

			request_timeout = st.number_input(
				'Request Timeout',
				min_value=1,
				max_value=120,
				value=10,
				step=1,
				key='wf_request_timeout' )

			delay_seconds = st.number_input(
				'Delay Between Pages',
				min_value=0.0,
				max_value=10.0,
				value=0.25,
				step=0.25,
				format='%.2f',
				key='wf_delay_seconds',
				disabled=(not enable_recursive) )

			max_bytes = st.number_input(
				'Max Bytes Per Page',
				min_value=1000,
				max_value=10000000,
				value=1000000,
				step=1000,
				key='wf_max_bytes' )

			use_playwright = st.checkbox(
				'Use Playwright Renderer',
				value=False,
				help=(
						'Use only when the page requires JavaScript rendering. '
						'This requires Playwright and installed browser binaries.'
				),
				key='wf_use_playwright' )

			button_c1, button_c2 = st.columns( 2 )

			with button_c1:
				run_scraper = st.button(
					'Run Scraper',
					key='webfetcher_run' )

			with button_c2:
				st.button(
					'Clear',
					key='webfetcher_clear',
					on_click=clear_webscrape_state )

		with col_right:
			if run_scraper:
				try:
					if not target_url or not target_url.strip( ):
						raise ValueError( 'A target URL is required.' )

					crawler = WebCrawler( use_playwright=bool( use_playwright ) )
					result = crawler.crawl( seed_url=target_url.strip( ),
						include_title=bool( include_title ),
						include_basic_text=bool( include_basic_text ),
						include_raw_html=bool( include_raw_html ),
						selected_methods=selected_methods,
						recursive=bool( enable_recursive ),
						max_depth=int( max_depth ),
						max_pages=int( max_pages ),
						same_domain_only=bool( same_domain_only ),
						request_timeout=int( request_timeout ),
						delay_seconds=float( delay_seconds ),
						max_bytes=int( max_bytes ) )

					st.session_state[ 'webscrape_results' ] = result.get( 'pages', [ ] )
					st.session_state[ 'webscrape_summary' ] = result.get( 'summary', { } )
					st.rerun( )

				except Exception as exc:
					st.error( str( exc ) )

			summary = st.session_state.get( 'webscrape_summary', { } )
			results = st.session_state.get( 'webscrape_results', [ ] )
			renderer = WebFetcher( )

			if summary:
				st.subheader( 'Summary' )

				metric_c1, metric_c2, metric_c3, metric_c4 = st.columns( 4 )

				with metric_c1:
					st.metric( 'Pages', summary.get( 'pages_processed', 0 ) )

				with metric_c2:
					st.metric( 'Errors', summary.get( 'errors', 0 ) )

				with metric_c3:
					st.metric( 'Bytes', summary.get( 'total_content_bytes', 0 ) )

				with metric_c4:
					st.metric( 'Seconds', summary.get( 'elapsed_seconds', 0 ) )

				with st.expander( 'Crawl Summary JSON', expanded=False ):
					st.json( summary )

			if not results:
				st.info( 'No results.' )

			else:
				st.subheader( 'Results' )

				for idx, page in enumerate( results, start=1 ):
					title = page.get( 'title', '' ) or page.get( 'url', f'Page {idx}' )
					depth = page.get( 'depth', 0 )

					with st.expander( f'Page {idx} [Depth {depth}]: {title}',
							expanded=(idx == 1) ):
						meta_col1, meta_col2 = st.columns( 2 )

						with meta_col1:
							st.markdown( f"**URL:** {page.get( 'url', '' )}" )
							st.markdown( f"**Status Code:** {page.get( 'status_code', '' )}" )
							st.markdown( f"**Depth:** {page.get( 'depth', 0 )}" )
							st.markdown( f"**Bytes:** {page.get( 'content_bytes', 0 )}" )

						with meta_col2:
							st.markdown( f"**Encoding:** {page.get( 'encoding', '' )}" )
							st.markdown( f"**Title:** {page.get( 'title', '' )}" )
							st.markdown(
								f"**Links Discovered:** "
								f"{len( page.get( 'links_discovered', [ ] ) or [ ] )}" )
							st.markdown(
								f"**Truncated:** "
								f"{bool( page.get( 'truncated_by_max_bytes', False ) )}" )

						page_errors = page.get( 'errors', [ ] ) or [ ]
						if page_errors:
							st.warning( 'This page completed with one or more warnings/errors.' )
							st.json( page_errors )

						plain_text = page.get( 'plain_text', '' )
						if isinstance( plain_text, str ) and plain_text.strip( ):
							st.subheader( 'Basic Text' )
							st.text_area(
								label='',
								value=renderer.truncate_text( plain_text, limit=12000 ),
								height=280,
								key=f'webscrape_plain_text_{idx}' )

						raw_html = page.get( 'raw_html', '' )
						if isinstance( raw_html, str ) and raw_html.strip( ):
							st.subheader( 'Raw HTML' )
							st.text_area(
								label='',
								value=renderer.truncate_text( raw_html, limit=12000 ),
								height=240,
								key=f'webscrape_raw_html_{idx}' )

						discovered_links = page.get( 'links_discovered', [ ] ) or [ ]
						if discovered_links:
							with st.expander(
									f'Links Discovered ({len( discovered_links )})',
									expanded=False ):
								st.text_area(
									label='',
									value=renderer.truncate_text(
										'\n'.join( discovered_links ),
										limit=12000 ),
									height=240,
									key=f'webscrape_links_{idx}' )

						data = page.get( 'data', { } ) or { }
						if data:
							st.subheader( 'Structured Data' )

						for label, items in data.items( ):
							values = renderer.coerce_items( items )

							with st.expander( f'{label} ({len( values )})', expanded=False ):
								if not values:
									st.info( 'No results returned.' )
									continue

								st.text_area(
									label='',
									value=renderer.truncate_text(
										'\n'.join( values ),
										limit=12000 ),
									height=240,
									key=f'webscrape_{idx}_{label}' )

	render_web_document_processing( )

# ==============================================================================
# WEATHER MODE
# ==============================================================================
elif mode == 'Weather':
	left, center, right = st.columns( [ 0.05, 0.9, 0.05 ] )
	with center:
		st.subheader( 'Weather Data' )
		st.divider( )
		
		global_location = get_default_location( )
		global_latitude = get_default_latitude( )
		global_longitude = get_default_longitude( )
		
		location_c1, location_c2, location_c3 = st.columns( 3, border=True )
		location_c1.metric( 'Location', global_location )
		location_c2.metric( 'Latitude', f'{float( global_latitude ):.4f}' )
		location_c3.metric( 'Longitude', f'{float( global_longitude ):.4f}' )
		
		set_blue_divider( )
		
		weather_c1, weather_c2 = st.columns( [ 0.40, 0.60 ], border=True, gap='xsmall' )
		
		with weather_c1:
			# ------------------------------------------------------------------
			# GOOGLE WEATHER
			# ------------------------------------------------------------------
			with st.expander( '🌦️ Google Weather', expanded=True ):
				st.badge( label='About API', color='blue', help=cfg.GOOGLE_WEATHER )
				google_address = st.text_input( 'Address or Location', value=global_location,
					key='weather_google_address' )
				
				google_product = st.selectbox( 'Product',
					options=[
							'Current Conditions',
							'Hourly Forecast',
							'Daily Forecast',
							'Hourly History',
							'Alerts'
					],
					key='weather_google_product' )
				
				google_units = st.selectbox( 'Units System', options=[ 'METRIC', 'IMPERIAL' ],
					key='weather_google_units' )
				
				google_language = st.text_input( 'Language Code', value='en',
					key='weather_google_language' )
				
				if google_product == 'Hourly Forecast':
					google_hours = st.number_input( 'Hours', min_value=1, max_value=240,
						value=24, step=1, key='weather_google_hours' )
				else:
					google_hours = 24
				
				if google_product == 'Hourly History':
					google_history_hours = st.number_input( 'History Hours', min_value=1,
						max_value=24, value=24, step=1, key='weather_google_history_hours' )
				else:
					google_history_hours = 24
				
				if google_product == 'Daily Forecast':
					google_days = st.number_input( 'Days', min_value=1, max_value=10, value=5,
						step=1, key='weather_google_days' )
				else:
					google_days = 5
				
				google_timeout = st.number_input( 'Timeout', min_value=1, max_value=60,
					value=10, step=1, key='weather_google_timeout' )
				
				google_btn_c1, google_btn_c2 = st.columns( 2 )
				
				with google_btn_c1:
					if st.button( label='Run', icon='🏃', key='weather_google_run',
							use_container_width=True ):
						if not google_address:
							st.warning( 'Enter an address or location.' )
						else:
							try:
								weather = GoogleWeather( )
								
								if google_product == 'Current Conditions':
									result = weather.fetch_current(
										address=google_address,
										units_system=google_units,
										language_code=google_language,
										time=int( google_timeout ) )
								
								elif google_product == 'Hourly Forecast':
									result = weather.fetch_hourly_forecast(
										address=google_address,
										hours=int( google_hours ),
										units_system=google_units,
										language_code=google_language,
										time=int( google_timeout ) )
								
								elif google_product == 'Daily Forecast':
									result = weather.fetch_daily_forecast(
										address=google_address,
										days=int( google_days ),
										units_system=google_units,
										language_code=google_language,
										time=int( google_timeout ) )
								
								elif google_product == 'Hourly History':
									result = weather.fetch_hourly_history(
										address=google_address,
										hours=int( google_history_hours ),
										units_system=google_units,
										language_code=google_language,
										time=int( google_timeout ) )
								
								else:
									result = weather.fetch_alerts(
										address=google_address,
										language_code=google_language,
										time=int( google_timeout ) )
								
								weather_latitude = getattr( weather, 'latitude', None )
								weather_longitude = getattr( weather, 'longitude', None )
								
								st.session_state[ 'weather_last_source' ] = 'Google Weather'
								st.session_state[ 'weather_last_result' ] = result or { }
								st.session_state[ 'weather_last_latitude' ] = weather_latitude
								st.session_state[ 'weather_last_longitude' ] = weather_longitude
								
								set_global_coordinates_from_result(
									weather_latitude,
									weather_longitude,
									location=google_address,
									description='Google Weather result' )
								
								st.success( 'Google Weather request completed.' )
							
							except Error as ex:
								st.error( f'Google Weather request failed: {ex.exception}' )
							except Exception as ex:
								st.error( f'Google Weather request failed: {ex}' )
				
				with google_btn_c2:
					if st.button( label='Clear', icon='🧹', key='weather_google_clear',
							use_container_width=True ):
						st.session_state[ 'weather_last_source' ] = ''
						st.session_state[ 'weather_last_result' ] = { }
						st.session_state[ 'weather_last_latitude' ] = None
						st.session_state[ 'weather_last_longitude' ] = None
			
			# ------------------------------------------------------------------
			# OPENWEATHER / OPEN-METEO
			# ------------------------------------------------------------------
			with st.expander( '🌤️ OpenWeather / Open-Meteo', expanded=False ):
				st.badge( label='About API', color='blue', help=cfg.OPEN_WEATHER )
				open_location = st.text_input( 'Location', value=global_location,
					key='weather_open_location' )
				
				open_mode = st.selectbox( 'Mode', options=[ 'current', 'hourly', 'daily' ],
					key='weather_open_mode' )
				
				open_zone = st.text_input( 'Timezone',
					value='auto',
					key='weather_open_zone' )
				
				open_forecast_days = st.number_input( 'Forecast Days', min_value=1,
					max_value=16, value=7, step=1,
					key='weather_open_forecast_days' )
				
				open_past_days = st.number_input( 'Past Days', min_value=0, max_value=92,
					value=0, step=1, key='weather_open_past_days' )
				
				open_count = st.number_input( 'Geocoding Result Count', min_value=1, max_value=100,
					value=10, step=1, key='weather_open_count' )
				
				open_btn_c1, open_btn_c2 = st.columns( 2 )
				
				with open_btn_c1:
					if st.button( label='Run', icon='🏃', key='weather_open_run',
							use_container_width=True ):
						if not open_location:
							st.warning( 'Enter a location.' )
						else:
							try:
								weather = OpenWeather( )
								
								result = weather.fetch( location=open_location, mode=open_mode,
									zone=open_zone, forecast_days=int( open_forecast_days ),
									past_days=int( open_past_days ),
									count=int( open_count ) )
								
								weather_latitude = getattr( weather, 'latitude', None )
								weather_longitude = getattr( weather, 'longitude', None )
								
								st.session_state[
									'weather_last_source' ] = 'OpenWeather / Open-Meteo'
								st.session_state[ 'weather_last_result' ] = result or { }
								st.session_state[ 'weather_last_latitude' ] = weather_latitude
								st.session_state[ 'weather_last_longitude' ] = weather_longitude
								
								set_global_coordinates_from_result( weather_latitude,
									weather_longitude, location=open_location,
									description='OpenWeather / Open-Meteo result' )
								
								st.success( 'OpenWeather request completed.' )
							
							except Exception as ex:
								st.error( f'OpenWeather request failed: {ex}' )
				
				with open_btn_c2:
					if st.button( label='Clear', icon='🧹', key='weather_open_clear',
							use_container_width=True ):
						st.session_state[ 'weather_last_source' ] = ''
						st.session_state[ 'weather_last_result' ] = { }
						st.session_state[ 'weather_last_latitude' ] = None
						st.session_state[ 'weather_last_longitude' ] = None
			
			# ------------------------------------------------------------------
			# HISTORICAL WEATHER
			# ------------------------------------------------------------------
			with st.expander( '🕰️ Historical Weather', expanded=False ):
				st.badge( label='About API', color='blue', help=cfg.HISTORICAL_WEATHER )
				historical_location = st.text_input( 'Location', value=global_location,
					key='weather_historical_location' )
				
				historical_date = st.date_input(
					'Historical Date',
					value=dt.date.today( ) - dt.timedelta( days=7 ),
					key='weather_historical_date' )
				
				historical_zone = st.text_input(
					'Timezone',
					value='auto',
					key='weather_historical_zone' )
				
				historical_count = st.number_input(
					'Geocoding Result Count',
					min_value=1,
					max_value=100,
					value=10,
					step=1,
					key='weather_historical_count' )
				
				historical_btn_c1, historical_btn_c2 = st.columns( 2 )
				
				with historical_btn_c1:
					if st.button( label='Run', icon='🏃', key='weather_historical_run',
							use_container_width=True ):
						if not historical_location:
							st.warning( 'Enter a location.' )
						else:
							try:
								weather = HistoricalWeather( )
								
								result = weather.fetch(
									location=historical_location,
									date=historical_date,
									zone=historical_zone,
									count=int( historical_count ) )
								
								weather_latitude = getattr( weather, 'latitude', None )
								weather_longitude = getattr( weather, 'longitude', None )
								
								st.session_state[ 'weather_last_source' ] = 'Historical Weather'
								st.session_state[ 'weather_last_result' ] = result or { }
								st.session_state[ 'weather_last_latitude' ] = weather_latitude
								st.session_state[ 'weather_last_longitude' ] = weather_longitude
								
								set_global_coordinates_from_result(
									weather_latitude,
									weather_longitude,
									location=historical_location,
									description='Historical Weather result' )
								
								st.success( 'Historical Weather request completed.' )
							
							except Exception as ex:
								st.error( f'Historical Weather request failed: {ex}' )
				
				with historical_btn_c2:
					if st.button( label='Clear', icon='🧹', key='weather_historical_clear',
							use_container_width=True ):
						st.session_state[ 'weather_last_source' ] = ''
						st.session_state[ 'weather_last_result' ] = { }
						st.session_state[ 'weather_last_latitude' ] = None
						st.session_state[ 'weather_last_longitude' ] = None
			
			# ------------------------------------------------------------------
			# CLIMATE DATA
			# ------------------------------------------------------------------
			with st.expander( '🌡️ Climate Data', expanded=False ):
				st.badge( label='About API', color='blue', help=cfg.NOAA_CLIMATE_DATA )
				climate_mode = st.selectbox( 'Mode',
					options=[ 'datasets', 'data' ],
					key='weather_climate_mode' )
				
				climate_timeout = st.number_input(
					'Timeout',
					min_value=1,
					max_value=60,
					value=20,
					step=1,
					key='weather_climate_timeout' )
				
				if climate_mode == 'datasets':
					climate_keyword = st.text_input(
						'Keyword',
						value='daily',
						key='weather_climate_keyword' )
					
					climate_start_date_value = st.date_input(
						'Start Date',
						value=dt.date.today( ) - dt.timedelta( days=365 ),
						key='weather_climate_dataset_start_date' )
					
					climate_end_date_value = st.date_input(
						'End Date',
						value=dt.date.today( ),
						key='weather_climate_dataset_end_date' )
					
					climate_limit = st.number_input(
						'Limit',
						min_value=1,
						max_value=1000,
						value=25,
						step=1,
						key='weather_climate_dataset_limit' )
					
					climate_offset = st.number_input(
						'Offset',
						min_value=0,
						max_value=100000,
						value=0,
						step=1,
						key='weather_climate_dataset_offset' )
					
					climate_dataset = ''
					climate_stations = ''
					climate_data_types = ''
				
				else:
					climate_dataset = st.text_input(
						'Dataset',
						value='daily-summaries',
						help='Example: daily-summaries',
						key='weather_climate_dataset' )
					
					climate_data_c1, climate_data_c2 = st.columns( 2 )
					with climate_data_c1:
						climate_start_date_value = st.date_input(
							'Start Date',
							value=dt.date.today( ) - dt.timedelta( days=30 ),
							key='weather_climate_data_start_date' )
					
					with climate_data_c2:
						climate_end_date_value = st.date_input(
							'End Date',
							value=dt.date.today( ),
							key='weather_climate_data_end_date' )
					
					climate_stations = st.text_input(
						'Stations',
						value='',
						help='Optional comma-separated station identifiers.',
						key='weather_climate_stations' )
					
					climate_data_types = st.text_input(
						'Data Types',
						value='',
						help='Optional comma-separated data type identifiers.',
						key='weather_climate_data_types' )
					
					climate_limit = st.number_input(
						'Limit',
						min_value=1,
						max_value=1000,
						value=25,
						step=1,
						key='weather_climate_data_limit' )
					
					climate_offset = 0
					climate_keyword = ''
				
				climate_btn_c1, climate_btn_c2 = st.columns( 2 )
				
				with climate_btn_c1:
					if st.button( label='Run', icon='🏃', key='weather_climate_run',
							use_container_width=True ):
						try:
							service = ClimateData( )
							
							if climate_mode == 'datasets':
								result = service.fetch_datasets(
									keyword=climate_keyword,
									start_date=climate_start_date_value.isoformat( ),
									end_date=climate_end_date_value.isoformat( ),
									limit=int( climate_limit ),
									offset=int( climate_offset ),
									time=int( climate_timeout ) )
							
							else:
								if not climate_dataset:
									st.warning( 'Enter a dataset identifier.' )
									result = None
								else:
									result = service.fetch_data(
										dataset=climate_dataset,
										start_date=climate_start_date_value.isoformat( ),
										end_date=climate_end_date_value.isoformat( ),
										stations=climate_stations,
										data_types=climate_data_types,
										limit=int( climate_limit ),
										time=int( climate_timeout ) )
							
							if result is not None:
								st.session_state[ 'weather_last_source' ] = 'Climate Data'
								st.session_state[ 'weather_last_result' ] = result or { }
								st.session_state[ 'weather_last_latitude' ] = None
								st.session_state[ 'weather_last_longitude' ] = None
								st.success( 'Climate Data request completed.' )
						
						except Exception as ex:
							st.error( f'Climate Data request failed: {ex}' )
				
				with climate_btn_c2:
					if st.button( label='Clear', icon='🧹', key='weather_climate_clear',
							use_container_width=True ):
						st.session_state[ 'weather_last_source' ] = ''
						st.session_state[ 'weather_last_result' ] = { }
						st.session_state[ 'weather_last_latitude' ] = None
						st.session_state[ 'weather_last_longitude' ] = None
			
			# ------------------------------------------------------------------
			# TIDES AND CURRENTS
			# ------------------------------------------------------------------
			with st.expander( '🌊 Tides & Currents', expanded=False ):
				st.badge( label='About API', color='blue', help=cfg.NOAA_TIDES_CURRENTS )
				tides_mode = st.selectbox(
					'Mode',
					options=[ 'station', 'water-level', 'tide-predictions' ],
					key='weather_tides_mode' )
				
				tides_station_id = st.text_input(
					'Station ID',
					value='8594900',
					help='Example NOAA station: 8594900',
					key='weather_tides_station_id' )
				
				tides_timeout = st.number_input(
					'Timeout',
					min_value=1,
					max_value=60,
					value=20,
					step=1,
					key='weather_tides_timeout' )
				
				if tides_mode == 'station':
					tides_begin_date = ''
					tides_end_date = ''
					tides_datum = 'MLLW'
					tides_units = 'metric'
					tides_time_zone = 'gmt'
					tides_interval = 'hilo'
				
				else:
					tides_date_c1, tides_date_c2 = st.columns( 2 )
					with tides_date_c1:
						tides_begin = st.date_input(
							'Begin Date',
							value=dt.date.today( ) - dt.timedelta( days=1 ),
							key='weather_tides_begin_date' )
					
					with tides_date_c2:
						tides_end = st.date_input(
							'End Date',
							value=dt.date.today( ),
							key='weather_tides_end_date' )
					
					tides_begin_date = tides_begin.strftime( '%Y%m%d' )
					tides_end_date = tides_end.strftime( '%Y%m%d' )
					
					tides_datum = st.selectbox(
						'Datum',
						options=[ 'MLLW', 'MLW', 'MSL', 'MHW', 'MHHW', 'NAVD' ],
						key='weather_tides_datum' )
					
					tides_units = st.selectbox(
						'Units',
						options=[ 'metric', 'english' ],
						key='weather_tides_units' )
					
					tides_time_zone = st.selectbox(
						'Time Zone',
						options=[ 'gmt', 'lst', 'lst_ldt' ],
						key='weather_tides_time_zone' )
					
					if tides_mode == 'tide-predictions':
						tides_interval = st.selectbox(
							'Interval',
							options=[ 'hilo', 'h' ],
							key='weather_tides_interval' )
					else:
						tides_interval = 'hilo'
				
				tides_btn_c1, tides_btn_c2 = st.columns( 2 )
				
				with tides_btn_c1:
					if st.button( label='Run', icon='🏃', key='weather_tides_run',
							use_container_width=True ):
						try:
							service = TidesAndCurrents( )
							
							result = service.fetch(
								mode=tides_mode,
								station_id=tides_station_id,
								begin_date=tides_begin_date,
								end_date=tides_end_date,
								datum=tides_datum,
								units=tides_units,
								time_zone=tides_time_zone,
								interval=tides_interval,
								time=int( tides_timeout ) )
							
							st.session_state[ 'weather_last_source' ] = 'Tides & Currents'
							st.session_state[ 'weather_last_result' ] = result or { }
							st.session_state[ 'weather_last_latitude' ] = None
							st.session_state[ 'weather_last_longitude' ] = None
							st.success( 'Tides & Currents request completed.' )
						
						except Exception as ex:
							st.error( f'Tides & Currents request failed: {ex}' )
				
				with tides_btn_c2:
					if st.button( label='Clear', icon='🧹', key='weather_tides_clear',
							use_container_width=True ):
						st.session_state[ 'weather_last_source' ] = ''
						st.session_state[ 'weather_last_result' ] = { }
						st.session_state[ 'weather_last_latitude' ] = None
						st.session_state[ 'weather_last_longitude' ] = None

		with weather_c2:
			# ------------------------------------------------------------------
			# WEATHER RESULTS
			# ------------------------------------------------------------------
			st.markdown( '##### Weather Results' )

			weather_source = st.session_state.get( 'weather_last_source', '' )
			weather_result = st.session_state.get( 'weather_last_result', { } )
			weather_latitude = st.session_state.get( 'weather_last_latitude', None )
			weather_longitude = st.session_state.get( 'weather_last_longitude', None )

			if not weather_result:
				st.info( 'No weather results available. Run one of the Weather expanders.' )

			else:
				if weather_source:
					st.caption( f'Source: {weather_source}' )

				if weather_latitude is not None and weather_longitude is not None:
					try:
						lat_value = float( weather_latitude )
						lng_value = float( weather_longitude )

						lat_c, lng_c = st.columns( 2 )
						with lat_c:
							st.metric( 'Latitude', f'{lat_value:.6f}' )
						with lng_c:
							st.metric( 'Longitude', f'{lng_value:.6f}' )

						preview_url = static_maps.pin(
							lat=lat_value,
							lng=lng_value,
							zoom=8,
							size='600x400' )

						st.image( preview_url )

					except Exception as ex:
						st.warning( f'Static map preview failed: {ex}' )

				st.json( weather_result )

	with st.expander( label='Weather RAG', icon='🧠', expanded=False ):
		from processing import render_mode_processing_controls
		render_mode_processing_controls( 'weather', 'weather_last_result',
			'weather_last_source', 'weather_rag' )

# ==============================================================================
# ENVIRONMENTAL MODE
# ==============================================================================
elif mode == 'Environmental':
	left, center, right = st.columns( [ 0.05, 0.9, 0.05 ] )
	with center:
		st.subheader( 'Environmental Data' )
		st.divider( )
		
		global_location = get_default_location( )
		global_zipcode = get_default_zipcode( )
		global_latitude = get_default_latitude( )
		global_longitude = get_default_longitude( )
		global_box = create_bounding_box_from_center( global_latitude, global_longitude )
		
		location_c1, location_c2, location_c3, location_c4 = st.columns( 4, border=True )
		location_c1.metric( 'Location', global_location )
		location_c2.metric( 'ZIP Code', global_zipcode )
		location_c3.metric( 'Latitude', f'{float( global_latitude ):.4f}' )
		location_c4.metric( 'Longitude', f'{float( global_longitude ):.4f}' )
		
		set_blue_divider( )
		
		enviro_c1, enviro_c2 = st.columns( [ 0.40, 0.60 ], border=True, gap='xsmall' )
		with enviro_c1:
			# ------------------------------------------------------------------
			# AIRNOW AIR QUALITY
			# ------------------------------------------------------------------
			with st.expander( '🌫️ AirNow Air Quality', expanded=True ):
				st.badge( label='About API', color='blue', help=cfg.AIR_NOW )
				airnow_mode = st.selectbox(
					'Mode',
					options=[
							'Current by ZIP',
							'Current by Coordinates',
							'Forecast by ZIP',
							'Forecast by Coordinates'
					],
					key='env_airnow_mode' )
				
				airnow_distance = st.number_input( 'Distance', min_value=0, max_value=250,
					value=25, step=1, key='input_env_airnow_distance' )
				
				airnow_timeout = st.number_input( 'Timeout', min_value=1, max_value=60,
					value=20, step=1, key='input_env_airnow_timeout' )
				
				if 'ZIP' in airnow_mode:
					airnow_zip = st.text_input( 'ZIP Code', value=global_zipcode,
						key='input_env_airnow_zip' )
					
					airnow_latitude = None
					airnow_longitude = None
				
				else:
					airnow_zip = ''
					
					airnow_coord_c1, airnow_coord_c2 = st.columns( 2 )
					
					with airnow_coord_c1:
						airnow_latitude = st.number_input(
							'Latitude',
							value=float( global_latitude ),
							format='%.6f',
							key='input_env_airnow_latitude' )
					
					with airnow_coord_c2:
						airnow_longitude = st.number_input(
							'Longitude',
							value=float( global_longitude ),
							format='%.6f',
							key='input_env_airnow_longitude' )
				
				if 'Forecast' in airnow_mode:
					airnow_date = st.date_input(
						'Forecast Date',
						value=dt.date.today( ),
						key='input_env_airnow_date' )
				else:
					airnow_date = None
				
				airnow_btn_c1, airnow_btn_c2 = st.columns( 2 )
				
				with airnow_btn_c1:
					if st.button( label='Run', icon='🏃', key='input_env_airnow_run',
							use_container_width=True ):
						try:
							service = AirNow( )
							result = None
							
							if airnow_mode == 'Current by ZIP':
								if not airnow_zip:
									st.warning( 'Enter a ZIP code.' )
								else:
									result = service.fetch_current_zip(
										zip_code=airnow_zip,
										distance=int( airnow_distance ),
										time=int( airnow_timeout ) )
							
							elif airnow_mode == 'Current by Coordinates':
								if not has_valid_coordinates( airnow_latitude, airnow_longitude ):
									st.warning( 'Provide valid coordinates.' )
								else:
									result = service.fetch_current_latlon(
										latitude=float( airnow_latitude ),
										longitude=float( airnow_longitude ),
										distance=int( airnow_distance ),
										time=int( airnow_timeout ) )
							
							elif airnow_mode == 'Forecast by ZIP':
								if not airnow_zip:
									st.warning( 'Enter a ZIP code.' )
								else:
									result = service.fetch_forecast_zip(
										zip_code=airnow_zip,
										date=airnow_date.isoformat( ),
										distance=int( airnow_distance ),
										time=int( airnow_timeout ) )
							
							else:
								if not has_valid_coordinates( airnow_latitude, airnow_longitude ):
									st.warning( 'Provide valid coordinates.' )
								else:
									result = service.fetch_forecast_latlon(
										latitude=float( airnow_latitude ),
										longitude=float( airnow_longitude ),
										date=airnow_date.isoformat( ),
										distance=int( airnow_distance ),
										time=int( airnow_timeout ) )
							
							if result is not None:
								st.session_state[ 'env_last_source' ] = 'AirNow'
								st.session_state[ 'env_last_result' ] = result or { }
								st.session_state[ 'env_last_latitude' ] = airnow_latitude
								st.session_state[ 'env_last_longitude' ] = airnow_longitude
								
								set_global_coordinates_from_result(
									airnow_latitude,
									airnow_longitude,
									location=global_location,
									description='AirNow coordinate result' )
								
								if airnow_zip:
									st.session_state[ 'zipcode' ] = str( airnow_zip ).strip( )
								
								st.success( 'AirNow request completed.' )
						
						except Exception as ex:
							st.error( f'AirNow request failed: {ex}' )
				
				with airnow_btn_c2:
					if st.button( label='Clear', icon='🧹', key='env_airnow_clear',
							use_container_width=True ):
						st.session_state[ 'env_last_source' ] = ''
						st.session_state[ 'env_last_result' ] = { }
						st.session_state[ 'env_last_latitude' ] = None
						st.session_state[ 'env_last_longitude' ] = None
			
			# ------------------------------------------------------------------
			# UV INDEX
			# ------------------------------------------------------------------
			with st.expander( '☀️ UV Index', expanded=False ):
				st.badge( label='About API', color='blue', help=cfg.EPA_UV_INDEX )
				uv_mode = st.selectbox(
					'Mode',
					options=[
							'Daily by ZIP',
							'Daily by City / State',
							'Hourly by ZIP',
							'Hourly by City / State'
					],
					key='env_uv_mode' )
				
				uv_timeout = st.number_input(
					'Timeout',
					min_value=1,
					max_value=60,
					value=20,
					step=1,
					key='env_uv_timeout' )
				
				if 'ZIP' in uv_mode:
					uv_zip = st.text_input(
						'ZIP Code',
						value='20001',
						key='env_uv_zip' )
					
					uv_city = ''
					uv_state = ''
				
				else:
					uv_zip = ''
					uv_city = st.text_input(
						'City',
						value='Washington',
						key='env_uv_city' )
					
					uv_state = st.text_input(
						'State',
						value='DC',
						key='env_uv_state' )
				
				uv_btn_c1, uv_btn_c2 = st.columns( 2 )
				
				with uv_btn_c1:
					if st.button( label='Run', icon='🏃', key='env_uv_run',
							use_container_width=True ):
						try:
							service = UvIndex( )
							
							if uv_mode == 'Daily by ZIP':
								if not uv_zip:
									st.warning( 'Enter a ZIP code.' )
									result = None
								else:
									result = service.fetch_daily_zip(
										zip_code=uv_zip,
										time=int( uv_timeout ) )
							
							elif uv_mode == 'Daily by City / State':
								if not uv_city or not uv_state:
									st.warning( 'Enter both city and state.' )
									result = None
								else:
									result = service.fetch_daily_city_state(
										city=uv_city,
										state=uv_state,
										time=int( uv_timeout ) )
							
							elif uv_mode == 'Hourly by ZIP':
								if not uv_zip:
									st.warning( 'Enter a ZIP code.' )
									result = None
								else:
									result = service.fetch_hourly_zip(
										zip_code=uv_zip,
										time=int( uv_timeout ) )
							
							else:
								if not uv_city or not uv_state:
									st.warning( 'Enter both city and state.' )
									result = None
								else:
									result = service.fetch_hourly_city_state(
										city=uv_city,
										state=uv_state,
										time=int( uv_timeout ) )
							
							if result is not None:
								st.session_state[ 'env_last_source' ] = 'UV Index'
								st.session_state[ 'env_last_result' ] = result or { }
								st.session_state[ 'env_last_latitude' ] = None
								st.session_state[ 'env_last_longitude' ] = None
								st.success( 'UV Index request completed.' )
						
						except Exception as ex:
							st.error( f'UV Index request failed: {ex}' )
				
				with uv_btn_c2:
					if st.button( label='Clear', icon='🧹', key='env_uv_clear',
							use_container_width=True ):
						st.session_state[ 'env_last_source' ] = ''
						st.session_state[ 'env_last_result' ] = { }
						st.session_state[ 'env_last_latitude' ] = None
						st.session_state[ 'env_last_longitude' ] = None
			
			# ------------------------------------------------------------------
			# OPENAQ
			# ------------------------------------------------------------------
			with st.expander( '🧪 OpenAQ', expanded=False ):
				st.badge( label='About API', color='blue', help=cfg.OPEN_AQ )
				openaq_mode = st.selectbox(
					'Mode',
					options=[
							'Locations',
							'Latest Measurements by Location',
							'Latest Measurements by Parameter',
							'Countries',
							'Providers',
							'Parameters'
					],
					key='sb_openaq_mode' )
				
				openaq_timeout = st.number_input(
					'Timeout',
					min_value=1,
					max_value=60,
					value=20,
					step=1,
					key='ib_env_openaq_timeout' )
				
				openaq_limit = st.number_input(
					'Limit',
					min_value=1,
					max_value=1000,
					value=100 if openaq_mode in [ 'Countries', 'Providers', 'Parameters' ] else 25,
					step=1,
					key='env_openaq_limit' )
				
				openaq_page = st.number_input(
					'Page',
					min_value=1,
					max_value=10000,
					value=1,
					step=1,
					key='env_openaq_page' )
				
				openaq_country_id = 0
				openaq_coordinates = ''
				openaq_radius = 25000
				openaq_providers_id = ''
				openaq_parameters_id = ''
				openaq_location_id = None
				openaq_parameter_id = None
				
				if openaq_mode == 'Locations':
					openaq_country_id = st.number_input(
						'Country ID',
						min_value=0,
						value=0,
						step=1,
						help='Optional. Use Countries mode to discover country IDs. 0 disables this filter.',
						key='in_env_openaq_country_id' )
					
					openaq_coordinates = st.text_input(
						'Coordinates',
						value=f'{global_latitude:.6f},{global_longitude:.6f}',
						help='OpenAQ examples use latitude,longitude for radial location filtering.',
						key='env_openaq_coordinates' )
					
					openaq_radius = st.number_input(
						'Radius',
						min_value=1,
						max_value=100000,
						value=25000,
						step=1000,
						key='env_openaq_radius' )
					
					openaq_providers_id = st.text_input(
						'Providers ID',
						value='',
						help='Optional. Use Providers mode to discover IDs. Comma-separated values are supported by OpenAQ.',
						key='env_openaq_providers_id' )
					
					openaq_parameters_id = st.text_input(
						'Parameters ID',
						value='',
						help='Optional. Use Parameters mode to discover IDs. Example: 2 is commonly PM2.5.',
						key='env_openaq_parameters_id' )
				
				elif openaq_mode == 'Latest Measurements by Location':
					openaq_location_id = st.number_input(
						'Location ID',
						min_value=1,
						value=1,
						step=1,
						help='Use Locations mode first to discover location IDs.',
						key='env_openaq_location_id' )
				
				elif openaq_mode == 'Latest Measurements by Parameter':
					openaq_parameter_id = st.number_input(
						'Parameter ID',
						min_value=1,
						value=2,
						step=1,
						help='Use Parameters mode first to discover parameter IDs. OpenAQ examples commonly use 2 for PM2.5.',
						key='env_openaq_parameter_id' )
				
				elif openaq_mode == 'Countries':
					openaq_providers_id = st.text_input(
						'Providers ID',
						value='',
						help='Optional provider filter.',
						key='env_openaq_countries_providers_id' )
					
					openaq_parameters_id = st.text_input(
						'Parameters ID',
						value='',
						help='Optional parameter filter.',
						key='env_openaq_countries_parameters_id' )
				
				elif openaq_mode == 'Providers':
					st.caption(
						'Returns OpenAQ provider IDs and provider names for later filtering.' )
				
				else:
					st.caption( 'Returns OpenAQ parameter IDs, names, display names, and units.' )
				
				openaq_btn_c1, openaq_btn_c2 = st.columns( 2 )
				
				with openaq_btn_c1:
					if st.button( label='Run', icon='🏃', key='env_openaq_run',
							use_container_width=True ):
						try:
							service = OpenAQ( )
							lat_value = None
							lng_value = None
							
							if openaq_mode == 'Locations':
								country_id_value = None
								if int( openaq_country_id ) > 0:
									country_id_value = int( openaq_country_id )
								
								result = service.fetch_locations(
									country_id=country_id_value,
									coordinates=openaq_coordinates,
									radius=int( openaq_radius ),
									providers_id=openaq_providers_id,
									parameters_id=openaq_parameters_id,
									limit=int( openaq_limit ),
									page=int( openaq_page ),
									time=int( openaq_timeout ) )
								
								try:
									parts = [ p.strip( ) for p in openaq_coordinates.split( ',' ) ]
									if len( parts ) == 2:
										lat_value = float( parts[ 0 ] )
										lng_value = float( parts[ 1 ] )
								except Exception:
									lat_value = None
									lng_value = None
							
							elif openaq_mode == 'Latest Measurements by Location':
								result = service.fetch_latest(
									location_id=int( openaq_location_id ),
									time=int( openaq_timeout ) )
							
							elif openaq_mode == 'Latest Measurements by Parameter':
								result = service.fetch_parameter_latest(
									parameter_id=int( openaq_parameter_id ),
									limit=int( openaq_limit ),
									page=int( openaq_page ),
									time=int( openaq_timeout ) )
							
							elif openaq_mode == 'Countries':
								result = service.fetch_countries(
									providers_id=openaq_providers_id,
									parameters_id=openaq_parameters_id,
									limit=int( openaq_limit ),
									page=int( openaq_page ),
									time=int( openaq_timeout ) )
							
							elif openaq_mode == 'Providers':
								result = service.fetch_providers(
									limit=int( openaq_limit ),
									page=int( openaq_page ),
									time=int( openaq_timeout ) )
							
							else:
								result = service.fetch_parameters(
									limit=int( openaq_limit ),
									page=int( openaq_page ),
									time=int( openaq_timeout ) )
							
							st.session_state[ 'env_last_source' ] = 'OpenAQ'
							st.session_state[ 'env_last_result' ] = result or { }
							st.session_state[ 'env_last_latitude' ] = lat_value
							st.session_state[ 'env_last_longitude' ] = lng_value
							
							set_global_coordinates_from_result(
								lat_value,
								lng_value,
								location=global_location,
								description='OpenAQ coordinate result' )
							
							st.success( 'OpenAQ request completed.' )
						
						except Exception as ex:
							st.error( f'OpenAQ request failed: {ex}' )
				
				with openaq_btn_c2:
					if st.button( label='Clear', icon='🧹', key='env_openaq_clear',
							use_container_width=True ):
						st.session_state[ 'env_last_source' ] = ''
						st.session_state[ 'env_last_result' ] = { }
						st.session_state[ 'env_last_latitude' ] = None
						st.session_state[ 'env_last_longitude' ] = None
			
			# ------------------------------------------------------------------
			# PURPLEAIR SENSORS
			# ------------------------------------------------------------------
			with st.expander( '🟣 PurpleAir Sensors', expanded=False ):
				st.badge( label='About API', color='blue', help=cfg.PURPLE_AIR )
				purple_mode = st.selectbox( 'Mode',
					options=[ 'Sensors by Bounding Box', 'Single Sensor' ],
					key='env_purple_mode' )
				
				purple_timeout = st.number_input( 'Timeout', min_value=1, max_value=60,
					value=20, step=1, key='env_purple_timeout' )
				
				if purple_mode == 'Sensors by Bounding Box':
					purple_default_fields = (
							'name,pm2.5,temperature,humidity,latitude,longitude,last_seen,location_type'
					)
				else:
					purple_default_fields = (
							'name,model,hardware,pm2.5_cf_1_a,pm2.5_cf_1_b,temperature,'
							'humidity,pressure,latitude,longitude,last_seen,firmware_version,rssi'
					)
				
				purple_fields = st.text_area(
					'Fields',
					value=purple_default_fields,
					height=90,
					help='Comma-separated PurpleAir fields. Leave the default unless you need a custom API response.',
					key='env_purple_fields' )
				
				if purple_mode == 'Sensors by Bounding Box':
					st.caption(
						'Bounding box defaults are centered on the global latitude and longitude.' )
					
					purple_box_c1, purple_box_c2 = st.columns( 2 )
					
					with purple_box_c1:
						purple_nwlng = st.number_input(
							'NW Longitude',
							value=float( global_box[ 'nw_lng' ] ),
							format='%.6f',
							key='env_purple_nwlng' )
						
						purple_nwlat = st.number_input(
							'NW Latitude',
							value=float( global_box[ 'nw_lat' ] ),
							format='%.6f',
							key='env_purple_nwlat' )
					
					with purple_box_c2:
						purple_selng = st.number_input(
							'SE Longitude',
							value=float( global_box[ 'se_lng' ] ),
							format='%.6f',
							key='env_purple_selng' )
						
						purple_selat = st.number_input(
							'SE Latitude',
							value=float( global_box[ 'se_lat' ] ),
							format='%.6f',
							key='env_purple_selat' )
					
					purple_location_type = st.number_input(
						'Location Type',
						min_value=0,
						max_value=1,
						value=0,
						step=1,
						help='Public outdoor sensors are commonly 0.',
						key='env_purple_location_type' )
					
					purple_max_age = st.number_input(
						'Max Age',
						min_value=0,
						max_value=10080,
						value=0,
						step=10,
						help='Maximum sensor age in minutes. 0 keeps the broad/default behavior.',
						key='env_purple_max_age' )
					
					purple_modified_since = st.number_input(
						'Modified Since',
						min_value=0,
						max_value=4102444800,
						value=0,
						step=1,
						help='UNIX timestamp filter. 0 disables the filter.',
						key='env_purple_modified_since' )
					
					purple_sensor_index = 0
					purple_center_latitude = (float( purple_nwlat ) + float( purple_selat )) / 2.0
					purple_center_longitude = (float( purple_nwlng ) + float( purple_selng )) / 2.0
				
				else:
					purple_nwlng = 0.0
					purple_nwlat = 0.0
					purple_selng = 0.0
					purple_selat = 0.0
					purple_location_type = 0
					purple_max_age = 0
					purple_modified_since = 0
					purple_center_latitude = None
					purple_center_longitude = None
					
					purple_sensor_index = st.number_input(
						'Sensor Index',
						min_value=1,
						value=1,
						step=1,
						key='env_purple_sensor_index' )
				
				purple_btn_c1, purple_btn_c2 = st.columns( 2 )
				
				with purple_btn_c1:
					if st.button( label='Run', icon='🏃', key='env_purple_run',
							use_container_width=True ):
						try:
							service = PurpleAir( )
							
							if purple_mode == 'Sensors by Bounding Box':
								result = service.fetch_sensors(
									nwlng=float( purple_nwlng ),
									nwlat=float( purple_nwlat ),
									selng=float( purple_selng ),
									selat=float( purple_selat ),
									location_type=int( purple_location_type ),
									max_age=int( purple_max_age ),
									modified_since=int( purple_modified_since ),
									fields=purple_fields,
									time=int( purple_timeout ) )
							
							else:
								result = service.fetch_sensor(
									sensor_index=int( purple_sensor_index ),
									fields=purple_fields,
									time=int( purple_timeout ) )
							
							st.session_state[ 'env_last_source' ] = 'PurpleAir'
							st.session_state[ 'env_last_result' ] = result or { }
							st.session_state[ 'env_last_latitude' ] = purple_center_latitude
							st.session_state[ 'env_last_longitude' ] = purple_center_longitude
							
							set_global_coordinates_from_result(
								purple_center_latitude,
								purple_center_longitude,
								location=global_location,
								description='PurpleAir bounding-box center' )
							
							st.success( 'PurpleAir request completed.' )
						
						except Exception as ex:
							st.error( f'PurpleAir request failed: {ex}' )
				
				with purple_btn_c2:
					if st.button( label='Clear', icon='🧹', key='env_purple_clear',
							use_container_width=True ):
						st.session_state[ 'env_last_source' ] = ''
						st.session_state[ 'env_last_result' ] = { }
						st.session_state[ 'env_last_latitude' ] = None
						st.session_state[ 'env_last_longitude' ] = None
			
			# ------------------------------------------------------------------
			# ENVIROFACTS
			# ------------------------------------------------------------------
			with st.expander( '🏭 EPA EnviroFacts Facilities', expanded=False ):
				st.badge( label='About API', color='blue', help=cfg.EPA_ENVIROFACTS )
				envirofacts_table = st.selectbox(
					'Table',
					options=[ 'TRI_FACILITY', 'TRI_RELEASE', 'EF_W_EMISSIONS_SOURCE_GHG' ],
					key='env_envirofacts_table' )
				
				envirofacts_state = st.text_input(
					'State Code',
					value='',
					help='Optional two-letter state filter.',
					key='env_envirofacts_state' )
				
				envirofacts_facility = st.text_input(
					'Facility Name',
					value='',
					help='Optional facility-name prefix filter.',
					key='env_envirofacts_facility' )
				
				envirofacts_limit = st.number_input(
					'Limit',
					min_value=1,
					max_value=500,
					value=25,
					step=1,
					key='env_envirofacts_limit' )
				
				envirofacts_timeout = st.number_input(
					'Timeout',
					min_value=1,
					max_value=60,
					value=20,
					step=1,
					key='env_envirofacts_timeout' )
				
				envirofacts_btn_c1, envirofacts_btn_c2 = st.columns( 2 )
				
				with envirofacts_btn_c1:
					if st.button( label='Run', icon='🏃', key='env_envirofacts_run',
							use_container_width=True ):
						try:
							service = EnviroFacts( )
							result = service.fetch(
								table_name=envirofacts_table,
								state_code=envirofacts_state,
								facility_name=envirofacts_facility,
								limit=int( envirofacts_limit ),
								time=int( envirofacts_timeout ) )
							
							st.session_state[ 'env_last_source' ] = 'EnviroFacts'
							st.session_state[ 'env_last_result' ] = result or { }
							st.session_state[ 'env_last_latitude' ] = None
							st.session_state[ 'env_last_longitude' ] = None
							st.success( 'EnviroFacts request completed.' )
						
						except Exception as ex:
							st.error( f'EnviroFacts request failed: {ex}' )
				
				with envirofacts_btn_c2:
					if st.button( label='Clear', icon='🧹', key='env_envirofacts_clear',
							use_container_width=True ):
						st.session_state[ 'env_last_source' ] = ''
						st.session_state[ 'env_last_result' ] = { }
						st.session_state[ 'env_last_latitude' ] = None
						st.session_state[ 'env_last_longitude' ] = None
			
			# ------------------------------------------------------------------
			# FIRMS FIRE / THERMAL ANOMALIES
			# ------------------------------------------------------------------
			with st.expander( '🔥 NASA FIRMS', expanded=False ):
				st.badge( label='About API', color='blue', help=cfg.NASA_FIRMS )
				firms_source = st.selectbox( 'Source', options=[
						'MODIS_NRT',
						'MODIS_SP',
						'VIIRS_SNPP_NRT',
						'VIIRS_SNPP_SP',
						'VIIRS_NOAA20_NRT',
						'VIIRS_NOAA20_SP',
						'VIIRS_NOAA21_NRT',
						'LANDSAT_NRT'
				], key='env_firms_source' )
				
				firms_area_mode = st.selectbox( 'Area Mode', options=[ 'World', 'Bounding Box' ],
					key='env_firms_area_mode' )
				
				firms_day_range = st.number_input(
					'Day Range',
					min_value=1,
					max_value=5,
					value=1,
					step=1,
					key='env_firms_day_range' )
				
				firms_use_date = st.checkbox(
					'Use Start Date',
					value=False,
					key='env_firms_use_date' )
				
				if firms_use_date:
					firms_date_value = st.date_input(
						'Date',
						value=dt.date.today( ),
						key='env_firms_date' )
					firms_date = firms_date_value.isoformat( )
				else:
					firms_date = ''
				
				firms_timeout = st.number_input(
					'Timeout',
					min_value=1,
					max_value=60,
					value=20,
					step=1,
					key='env_firms_timeout' )
				
				if firms_area_mode == 'World':
					firms_area_coordinates = 'world'
					firms_center_latitude = None
					firms_center_longitude = None
					
					st.info(
						'World mode does not update global latitude and longitude because it '
						'does not represent a single geographic center.' )
				
				else:
					st.caption(
						'Bounding box defaults are centered on the global latitude and longitude.' )
					
					firms_box_c1, firms_box_c2 = st.columns( 2 )
					
					with firms_box_c1:
						firms_west = st.number_input(
							'West',
							value=float( global_box[ 'west' ] ),
							format='%.6f',
							key='env_firms_west' )
						
						firms_south = st.number_input(
							'South',
							value=float( global_box[ 'south' ] ),
							format='%.6f',
							key='env_firms_south' )
					
					with firms_box_c2:
						firms_east = st.number_input(
							'East',
							value=float( global_box[ 'east' ] ),
							format='%.6f',
							key='env_firms_east' )
						
						firms_north = st.number_input(
							'North',
							value=float( global_box[ 'north' ] ),
							format='%.6f',
							key='env_firms_north' )
					
					firms_area_coordinates = (
							f'{float( firms_west )},{float( firms_south )},'
							f'{float( firms_east )},{float( firms_north )}'
					)
					
					firms_center_latitude = (float( firms_south ) + float( firms_north )) / 2.0
					firms_center_longitude = (float( firms_west ) + float( firms_east )) / 2.0
				
				firms_btn_c1, firms_btn_c2 = st.columns( 2 )
				
				with firms_btn_c1:
					if st.button( label='Run', icon='🏃', key='btn_env_firms_run',
							use_container_width=True ):
						try:
							service = Firms( )
							
							result = service.fetch_area(
								source=firms_source,
								area_coordinates=firms_area_coordinates,
								day_range=int( firms_day_range ),
								date=firms_date,
								time=int( firms_timeout ) )
							
							st.session_state[ 'env_last_source' ] = 'FIRMS'
							st.session_state[ 'env_last_result' ] = result or { }
							st.session_state[ 'env_last_latitude' ] = firms_center_latitude
							st.session_state[ 'env_last_longitude' ] = firms_center_longitude
							
							set_global_coordinates_from_result(
								firms_center_latitude,
								firms_center_longitude,
								location=global_location,
								description='FIRMS bounding-box center' )
							
							st.success( 'FIRMS request completed.' )
						
						except Exception as ex:
							st.error( f'FIRMS request failed: {ex}' )
				
				with firms_btn_c2:
					if st.button( label='Clear', icon='🧹', key='btn_env_firms_clear',
							use_container_width=True ):
						st.session_state[ 'env_last_source' ] = ''
						st.session_state[ 'env_last_result' ] = { }
						st.session_state[ 'env_last_latitude' ] = None
						st.session_state[ 'env_last_longitude' ] = None
			
			# ------------------------------------------------------------------
			# EONET NATURAL EVENTS
			# ------------------------------------------------------------------
			with st.expander( '🌎 NASA Earth Observatory Natural Events', expanded=False ):
				st.badge( label='About API', color='blue', help=cfg.NASA_EONET )
				eonet_mode = st.selectbox(
					'Mode',
					options=[ 'events', 'categories' ],
					key='env_eonet_mode' )
				
				eonet_timeout = st.number_input(
					'Timeout',
					min_value=1,
					max_value=60,
					value=20,
					step=1,
					key='env_eonet_timeout' )
				
				if eonet_mode == 'events':
					eonet_source = st.text_input(
						'Source',
						value='',
						help='Optional EONET source identifier or comma-separated identifiers.',
						key='env_eonet_source' )
					
					eonet_category = st.text_input(
						'Category',
						value='',
						help='Optional EONET category identifier or comma-separated identifiers.',
						key='env_eonet_category' )
					
					eonet_status = st.selectbox(
						'Status',
						options=[ 'open', 'closed', 'all' ],
						key='env_eonet_status' )
					
					eonet_limit = st.number_input(
						'Limit',
						min_value=1,
						max_value=500,
						value=25,
						step=1,
						key='env_eonet_limit' )
					
					eonet_days = st.number_input(
						'Days',
						min_value=1,
						max_value=3650,
						value=30,
						step=1,
						key='env_eonet_days' )
					
					eonet_use_dates = st.checkbox(
						'Use Start / End Dates',
						value=False,
						key='env_eonet_use_dates' )
					
					if eonet_use_dates:
						eonet_date_c1, eonet_date_c2 = st.columns( 2 )
						
						with eonet_date_c1:
							eonet_start_value = st.date_input(
								'Start Date',
								value=dt.date.today( ) - dt.timedelta( days=30 ),
								key='env_eonet_start_date' )
						
						with eonet_date_c2:
							eonet_end_value = st.date_input(
								'End Date',
								value=dt.date.today( ),
								key='env_eonet_end_date' )
						
						eonet_start_date = eonet_start_value.isoformat( )
						eonet_end_date = eonet_end_value.isoformat( )
					
					else:
						eonet_start_date = ''
						eonet_end_date = ''
					
					eonet_use_bbox = st.checkbox(
						'Use Bounding Box',
						value=False,
						key='env_eonet_use_bbox' )
					
					if eonet_use_bbox:
						st.caption(
							'Bounding box defaults are centered on the global latitude and longitude.' )
						
						eonet_box_c1, eonet_box_c2 = st.columns( 2 )
						
						with eonet_box_c1:
							eonet_min_lon = st.number_input(
								'Min Longitude',
								value=float( global_box[ 'west' ] ),
								format='%.6f',
								key='env_eonet_min_lon' )
							
							eonet_max_lat = st.number_input(
								'Max Latitude',
								value=float( global_box[ 'north' ] ),
								format='%.6f',
								key='env_eonet_max_lat' )
						
						with eonet_box_c2:
							eonet_max_lon = st.number_input(
								'Max Longitude',
								value=float( global_box[ 'east' ] ),
								format='%.6f',
								key='env_eonet_max_lon' )
							
							eonet_min_lat = st.number_input(
								'Min Latitude',
								value=float( global_box[ 'south' ] ),
								format='%.6f',
								key='env_eonet_min_lat' )
						
						eonet_bbox = (
								f'{float( eonet_min_lon )},{float( eonet_max_lat )},'
								f'{float( eonet_max_lon )},{float( eonet_min_lat )}'
						)
						
						eonet_center_latitude = (
								                        float( eonet_min_lat ) + float(
							                        eonet_max_lat )
						                        ) / 2.0
						
						eonet_center_longitude = (
								                         float( eonet_min_lon ) + float(
							                         eonet_max_lon )
						                         ) / 2.0
					
					else:
						eonet_bbox = ''
						eonet_center_latitude = None
						eonet_center_longitude = None
				
				else:
					eonet_source = ''
					eonet_category = ''
					eonet_status = 'open'
					eonet_limit = 25
					eonet_days = 30
					eonet_start_date = ''
					eonet_end_date = ''
					eonet_bbox = ''
					eonet_center_latitude = None
					eonet_center_longitude = None
				
				eonet_btn_c1, eonet_btn_c2 = st.columns( 2 )
				
				with eonet_btn_c1:
					if st.button( label='Run', icon='🏃', key='env_eonet_run',
							use_container_width=True ):
						try:
							service = EoNet( )
							
							result = service.fetch(
								mode=eonet_mode,
								source=eonet_source,
								category=eonet_category,
								status=eonet_status,
								limit=int( eonet_limit ),
								days=int( eonet_days ),
								start_date=eonet_start_date,
								end_date=eonet_end_date,
								bbox=eonet_bbox,
								time=int( eonet_timeout ) )
							
							st.session_state[ 'env_last_source' ] = 'EONET'
							st.session_state[ 'env_last_result' ] = result or { }
							st.session_state[ 'env_last_latitude' ] = eonet_center_latitude
							st.session_state[ 'env_last_longitude' ] = eonet_center_longitude
							
							set_global_coordinates_from_result(
								eonet_center_latitude,
								eonet_center_longitude,
								location=global_location,
								description='EONET bounding-box center' )
							
							st.success( 'EONET request completed.' )
						
						except Exception as ex:
							st.error( f'EONET request failed: {ex}' )
				
				with eonet_btn_c2:
					if st.button( label='Clear', icon='🧹', key='env_eonet_clear',
							use_container_width=True ):
						st.session_state[ 'env_last_source' ] = ''
						st.session_state[ 'env_last_result' ] = { }
						st.session_state[ 'env_last_latitude' ] = None
						st.session_state[ 'env_last_longitude' ] = None

		with enviro_c2:
			# ------------------------------------------------------------------
			# ENVIRONMENTAL RESULTS
			# ------------------------------------------------------------------
			st.markdown( '##### Environmental Results' )
			env_source = st.session_state.get( 'env_last_source', '' )
			env_result = st.session_state.get( 'env_last_result', { } )
			env_latitude = st.session_state.get( 'env_last_latitude', None )
			env_longitude = st.session_state.get( 'env_last_longitude', None )
			if not env_result:
				st.info(
					'No environmental results available. Run one of the Environmental expanders.' )
			else:
				if env_source:
					st.caption( f'Source: {env_source}' )

				summary = env_result.get( 'summary', None ) if isinstance( env_result,
					dict ) else None
				rows = env_result.get( 'rows', None ) if isinstance( env_result, dict ) else None
				if isinstance( summary, dict ) and summary:
					st.markdown( '##### Summary' )
					st.data_editor( pd.DataFrame( [ summary ] ), key='env_summary_table',
						use_container_width=True, disabled=True )
				if env_latitude is not None and env_longitude is not None:
					try:
						lat_value = float( env_latitude )
						lng_value = float( env_longitude )

						lat_c, lng_c = st.columns( 2 )
						with lat_c:
							st.metric( 'Latitude', f'{lat_value:.6f}' )
						with lng_c:
							st.metric( 'Longitude', f'{lng_value:.6f}' )

						preview_url = static_maps.pin(
							lat=lat_value,
							lng=lng_value,
							zoom=8,
							size='600x400' )

						st.image( preview_url )

					except Exception as ex:
						st.warning( f'Static map preview failed: {ex}' )

				if isinstance( rows, list ) and rows:
					st.markdown( '##### Rows' )
					st.data_editor(
						pd.DataFrame( rows ),
						key='env_rows_table',
						use_container_width=True,
						disabled=True )

				st.markdown( '##### Raw Result' )
				st.json( env_result )

	with st.expander( label='Environmental RAG', icon='🧠', expanded=False ):
		from processing import render_mode_processing_controls
		render_mode_processing_controls( 'env', 'env_last_result', 'env_last_source',
			'environmental_rag' )

# ==============================================================================
# ASTRONOMICAL MODE
# ==============================================================================
elif mode == 'Astronomical':
	left, center, right = st.columns( [ 0.05, 0.9, 0.05 ] )
	with center:
		st.subheader( 'Astronomical Data' )
		st.divider( )
		
		global_location = get_default_location( )
		global_latitude = get_default_latitude( )
		global_longitude = get_default_longitude( )
		
		location_c1, location_c2, location_c3 = st.columns( 3, border=True )
		location_c1.metric( 'Observer Location', global_location )
		location_c2.metric( 'Observer Latitude', f'{float( global_latitude ):.4f}' )
		location_c3.metric( 'Observer Longitude', f'{float( global_longitude ):.4f}' )
		
		set_blue_divider( )
		
		astro_c1, astro_c2 = st.columns( [ 0.40, 0.60 ], border=True, gap='xsmall' )
		
		with astro_c1:
			# ------------------------------------------------------------------
			# NAVAL OBSERVATORY
			# ------------------------------------------------------------------
			with st.expander( '🧭 Naval Observatory', expanded=True ):
				st.badge( label='About API', color='blue', help=cfg.US_NAVAL_OBSERVATORY )
				st.caption(
					'Uses the U.S. Naval Observatory Celestial Navigation Data API. The endpoint '
					'accepts date, time, and assumed observer coordinates as latitude,longitude.' )
				
				naval_date = st.date_input(
					'Date',
					value=dt.date.today( ),
					key='astro_naval_date' )
				
				naval_time_choice = st.selectbox(
					'Time Preset',
					options=[
							'Current UTC Time',
							'00:00:00',
							'06:00:00',
							'12:00:00',
							'18:00:00',
							'Custom'
					],
					key='astro_naval_time_choice' )
				
				if naval_time_choice == 'Current UTC Time':
					naval_time_value = dt.datetime.utcnow( ).strftime( '%H:%M:%S' )
					st.caption( f'Using current UTC time: {naval_time_value}' )
				
				elif naval_time_choice == 'Custom':
					naval_time_value = st.text_input(
						'Custom Time',
						value='12:00:00',
						help='Use HH:MM, HH:MM:SS, or HH:MM:SS.S format.',
						key='astro_naval_time_value' )
				
				else:
					naval_time_value = naval_time_choice
				
				naval_location_preset = st.selectbox(
					'Observer Location Preset',
					options=[
							'Global Location',
							'Washington, DC',
							'New York Harbor',
							'Norfolk, VA',
							'Custom'
					],
					key='astro_naval_location_preset' )
				
				if naval_location_preset == 'Washington, DC':
					naval_default_latitude = 38.9072
					naval_default_longitude = -77.0369
					naval_default_label = 'Washington, DC'
				
				elif naval_location_preset == 'New York Harbor':
					naval_default_latitude = 40.7003
					naval_default_longitude = -74.0129
					naval_default_label = 'New York Harbor'
				
				elif naval_location_preset == 'Norfolk, VA':
					naval_default_latitude = 36.8508
					naval_default_longitude = -75.2859
					naval_default_label = 'Norfolk, VA'
				
				elif naval_location_preset == 'Custom':
					naval_default_latitude = float( global_latitude )
					naval_default_longitude = float( global_longitude )
					naval_default_label = global_location
				
				else:
					naval_default_latitude = float( global_latitude )
					naval_default_longitude = float( global_longitude )
					naval_default_label = global_location
				
				naval_c1, naval_c2 = st.columns( 2 )
				
				with naval_c1:
					naval_latitude = st.number_input(
						'Observer Latitude',
						min_value=-90.0,
						max_value=90.0,
						value=float( naval_default_latitude ),
						format='%.6f',
						key='astro_naval_latitude' )
				
				with naval_c2:
					naval_longitude = st.number_input(
						'Observer Longitude',
						min_value=-180.0,
						max_value=180.0,
						value=float( naval_default_longitude ),
						format='%.6f',
						key='astro_naval_longitude' )
				
				naval_location_label = st.text_input(
					'Location Label',
					value=naval_default_label,
					key='astro_naval_location_label' )
				
				naval_timeout = st.number_input(
					'Timeout',
					min_value=1,
					max_value=60,
					value=20,
					step=1,
					key='astro_naval_timeout' )
				
				naval_btn_c1, naval_btn_c2 = st.columns( 2 )
				
				with naval_btn_c1:
					if st.button( label='Run', icon='🏃', key='astro_naval_run',
							use_container_width=True ):
						if not has_valid_coordinates( naval_latitude, naval_longitude ):
							st.warning( 'Provide valid observer latitude and longitude.' )
						else:
							try:
								service = NavalObservatory( )
								result = service.fetch(
									mode='celnav',
									date_value=naval_date.isoformat( ),
									time_value=naval_time_value,
									latitude=float( naval_latitude ),
									longitude=float( naval_longitude ),
									location_label=naval_location_label,
									time=int( naval_timeout ) )
								
								st.session_state[ 'astro_last_source' ] = 'Naval Observatory'
								st.session_state[ 'astro_last_result' ] = result or { }
								st.session_state[ 'astro_last_latitude' ] = float( naval_latitude )
								st.session_state[ 'astro_last_longitude' ] = float(
									naval_longitude )
								st.session_state[ 'astro_last_url' ] = ''
								
								set_global_coordinates_from_result(
									naval_latitude,
									naval_longitude,
									location=naval_location_label,
									description='Naval Observatory observer location' )
								
								st.success( 'Naval Observatory request completed.' )
							
							except Exception as ex:
								st.error( f'Naval Observatory request failed: {ex}' )
				
				with naval_btn_c2:
					if st.button( label='Clear', icon='🧹', key='astro_naval_clear',
							use_container_width=True ):
						st.session_state[ 'astro_last_source' ] = ''
						st.session_state[ 'astro_last_result' ] = { }
						st.session_state[ 'astro_last_latitude' ] = None
						st.session_state[ 'astro_last_longitude' ] = None
						st.session_state[ 'astro_last_url' ] = ''
			
			# ------------------------------------------------------------------
			# SPACE WEATHER
			# ------------------------------------------------------------------
			with st.expander( '☀️ Space Weather', expanded=False ):
				st.badge( label='About API', color='blue', help=cfg.SPACE_WEATHER )
				st.caption(
					'Uses NASA DONKI. Controls are shown only when they apply to the selected '
					'DONKI endpoint.' )
				
				space_mode_labels = {
						'Coronal Mass Ejection': 'cme',
						'CME Analysis': 'cme_analysis',
						'Geomagnetic Storm': 'gst',
						'Interplanetary Shock': 'ips',
						'Solar Flare': 'flr',
						'Solar Energetic Particle': 'sep',
						'Magnetopause Crossing': 'mpc',
						'Radiation Belt Enhancement': 'rbe',
						'High Speed Stream': 'hss',
						'WSA-ENLIL Model': 'wsa_enlil',
						'Notifications': 'notifications'
				}
				
				space_mode_label = st.selectbox(
					'Mode',
					options=list( space_mode_labels.keys( ) ),
					key='astro_space_mode_label' )
				
				space_mode = space_mode_labels[ space_mode_label ]
				
				space_date_c1, space_date_c2 = st.columns( 2 )
				
				with space_date_c1:
					space_start = st.date_input(
						'Start Date',
						value=dt.date.today( ) - dt.timedelta( days=7 ),
						key='astro_space_start_date' )
				
				with space_date_c2:
					space_end = st.date_input(
						'End Date',
						value=dt.date.today( ),
						key='astro_space_end_date' )
				
				if space_start > space_end:
					st.warning(
						'Start Date is after End Date. The request will fail unless corrected.' )
				
				space_location = 'ALL'
				space_catalog = 'ALL'
				space_notification_type = 'all'
				space_most_accurate_only = True
				space_complete_entry_only = True
				space_speed = 0
				space_half_angle = 0
				space_keyword = ''
				
				if space_mode == 'cme_analysis':
					st.caption(
						'CME Analysis supports catalog, most-accurate-only, complete-entry-only, '
						'speed, half-angle, and keyword filters.' )
					
					space_catalog = st.selectbox(
						'Catalog',
						options=[ 'ALL', 'SWRC_CATALOG', 'JANG_ET_AL_CATALOG', 'M2M_CATALOG' ],
						key='astro_space_cme_analysis_catalog' )
					
					space_c1, space_c2 = st.columns( 2 )
					
					with space_c1:
						space_most_accurate_only = st.checkbox(
							'Most Accurate Only',
							value=True,
							key='astro_space_most_accurate_only' )
						
						space_complete_entry_only = st.checkbox(
							'Complete Entry Only',
							value=True,
							key='astro_space_complete_entry_only' )
					
					with space_c2:
						space_speed = st.number_input(
							'Minimum Speed',
							min_value=0,
							max_value=5000,
							value=0,
							step=10,
							help='Lower-bound CME speed filter.',
							key='astro_space_speed' )
						
						space_half_angle = st.number_input(
							'Minimum Half Angle',
							min_value=0,
							max_value=360,
							value=0,
							step=1,
							help='Lower-bound CME half-angle filter.',
							key='astro_space_half_angle' )
					
					space_keyword = st.text_input(
						'Keyword',
						value='',
						key='astro_space_keyword' )
				
				elif space_mode == 'ips':
					st.caption( 'Interplanetary Shock supports location and catalog filters.' )
					
					space_location = st.text_input(
						'Location',
						value='ALL',
						help='DONKI IPS location filter. Use ALL to avoid filtering.',
						key='astro_space_location' )
					
					space_catalog = st.text_input(
						'Catalog',
						value='ALL',
						help='DONKI IPS catalog filter. Use ALL to avoid filtering.',
						key='astro_space_catalog' )
				
				elif space_mode == 'notifications':
					st.caption(
						'Notifications supports the notification type filter. The wrapper preserves '
						'the selected date range.' )
					
					space_notification_type = st.selectbox(
						'Notification Type',
						options=[
								'all',
								'FLR',
								'SEP',
								'CME',
								'IPS',
								'MPC',
								'GST',
								'RBE',
								'HSS',
								'WSAEnlil',
								'Report'
						],
						key='astro_space_notification_type' )
				
				else:
					st.caption(
						'This DONKI endpoint uses the common startDate, endDate, and api_key '
						'parameters.' )
				
				space_timeout = st.number_input(
					'Timeout',
					min_value=1,
					max_value=60,
					value=20,
					step=1,
					key='astro_space_timeout' )
				
				space_btn_c1, space_btn_c2 = st.columns( 2 )
				
				with space_btn_c1:
					if st.button( label='Run', icon='🏃', key='astro_space_run',
							use_container_width=True ):
						try:
							service = SpaceWeather( )
							result = service.fetch(
								mode=space_mode,
								start_date=space_start.isoformat( ),
								end_date=space_end.isoformat( ),
								time=int( space_timeout ),
								location=space_location,
								catalog=space_catalog,
								notification_type=space_notification_type,
								most_accurate_only=bool( space_most_accurate_only ),
								complete_entry_only=bool( space_complete_entry_only ),
								speed=int( space_speed ),
								half_angle=int( space_half_angle ),
								keyword=space_keyword,
								api_key=getattr( cfg, 'NASA_API_KEY', None ) )
							
							st.session_state[ 'astro_last_source' ] = 'Space Weather'
							st.session_state[ 'astro_last_result' ] = result or { }
							st.session_state[ 'astro_last_latitude' ] = None
							st.session_state[ 'astro_last_longitude' ] = None
							st.session_state[ 'astro_last_url' ] = ''
							st.success( 'Space Weather request completed.' )
						
						except Exception as ex:
							st.error( f'Space Weather request failed: {ex}' )
				
				with space_btn_c2:
					if st.button( label='Clear', icon='🧹', key='astro_space_clear',
							use_container_width=True ):
						st.session_state[ 'astro_last_source' ] = ''
						st.session_state[ 'astro_last_result' ] = { }
						st.session_state[ 'astro_last_latitude' ] = None
						st.session_state[ 'astro_last_longitude' ] = None
						st.session_state[ 'astro_last_url' ] = ''
			
			# ------------------------------------------------------------------
			# STAR CHART
			# ------------------------------------------------------------------
			with st.expander( '✨ Star Chart', expanded=False ):
				st.badge( label='About API', color='blue', help=cfg.STAR_CHART )
				st.caption(
					'Uses SKY-MAP. Object Chart builds an object-centered link, Coordinate Chart '
					'builds a coordinate-centered link, and Static Chart Image builds a direct '
					'image-generator URL.' )
				
				chart_mode_labels = {
						'Object Chart': 'object_chart',
						'Coordinate Chart': 'coordinate_chart',
						'Static Chart Image': 'static_chart'
				}
				
				chart_mode_label = st.selectbox(
					'Mode',
					options=list( chart_mode_labels.keys( ) ),
					key='astro_chart_mode_label' )
				
				chart_mode = chart_mode_labels[ chart_mode_label ]
				
				chart_example = st.selectbox(
					'Coordinate Example',
					options=[
							'Andromeda Galaxy / M31',
							'Orion Nebula / M42',
							'Galactic Center',
							'Custom'
					],
					key='astro_chart_coordinate_example' )
				
				if chart_example == 'Andromeda Galaxy / M31':
					chart_default_object = 'M31'
					chart_default_ra = 0.7117
					chart_default_dec = 41.2670
				
				elif chart_example == 'Orion Nebula / M42':
					chart_default_object = 'M42'
					chart_default_ra = 5.5881
					chart_default_dec = -5.3911
				
				elif chart_example == 'Galactic Center':
					chart_default_object = 'Sgr A*'
					chart_default_ra = 17.7611
					chart_default_dec = -29.0078
				
				else:
					chart_default_object = 'M31'
					chart_default_ra = 0.7117
					chart_default_dec = 41.2670
				
				chart_zoom = st.number_input(
					'Zoom',
					min_value=1,
					max_value=20,
					value=5,
					step=1,
					key='astro_chart_zoom' )
				
				chart_image_source = st.selectbox(
					'Image Source',
					options=[ 'DSS2', 'SDSS', 'GALEX', 'IRAS', 'RASS', 'Custom' ],
					key='astro_chart_image_source_choice' )
				
				if chart_image_source == 'Custom':
					chart_image_source_value = st.text_input(
						'Custom Image Source',
						value='DSS2',
						help='Enter the SKY-MAP image source value accepted by the API.',
						key='astro_chart_image_source_custom' )
				else:
					chart_image_source_value = chart_image_source
				
				if chart_mode == 'object_chart':
					chart_object_name = st.text_input(
						'Object Name',
						value=chart_default_object,
						help='Object name or catalog identifier. Examples: M31, M42, Sirius.',
						key='astro_chart_object_name' )
					
					chart_ra = 0.0
					chart_dec = 0.0
					chart_width = 900
					chart_height = 450
					chart_magnitude = 7.5
					
					st.caption(
						'Object Chart uses SKY-MAP object lookup and ignores coordinate, width, '
						'height, and limiting magnitude controls.' )
				
				else:
					chart_object_name = ''
					chart_coord_c1, chart_coord_c2 = st.columns( 2 )
					
					with chart_coord_c1:
						chart_ra = st.number_input(
							'Right Ascension',
							value=float( chart_default_ra ),
							format='%.7f',
							help='Right ascension in decimal hours for SKY-MAP chart endpoints.',
							key='astro_chart_ra' )
					
					with chart_coord_c2:
						chart_dec = st.number_input(
							'Declination',
							value=float( chart_default_dec ),
							format='%.7f',
							help='Declination in decimal degrees.',
							key='astro_chart_dec' )
					
					if chart_mode == 'static_chart':
						chart_size_c1, chart_size_c2 = st.columns( 2 )
						
						with chart_size_c1:
							chart_width = st.number_input(
								'Width',
								min_value=128,
								max_value=4096,
								value=900,
								step=64,
								key='astro_chart_width' )
						
						with chart_size_c2:
							chart_height = st.number_input(
								'Height',
								min_value=128,
								max_value=4096,
								value=450,
								step=64,
								key='astro_chart_height' )
						
						chart_magnitude = st.number_input(
							'Limiting Magnitude',
							min_value=0.0,
							max_value=30.0,
							value=7.5,
							step=0.5,
							format='%.1f',
							key='astro_chart_magnitude' )
					
					else:
						chart_width = 900
						chart_height = 450
						chart_magnitude = 7.5
					
					st.caption(
						'Coordinate and Static Chart modes use right ascension and declination. '
						'Static Chart additionally uses width, height, and limiting magnitude.' )
				
				chart_box_color = st.selectbox(
					'Box Color',
					options=[ 'yellow', 'red', 'green', 'blue', 'white' ],
					key='astro_chart_box_color' )
				
				chart_options_c1, chart_options_c2 = st.columns( 2 )
				
				with chart_options_c1:
					chart_show_box = st.checkbox(
						'Show Box',
						value=True,
						key='astro_chart_show_box' )
					
					chart_show_grid = st.checkbox(
						'Show Grid',
						value=True,
						key='astro_chart_show_grid' )
				
				with chart_options_c2:
					chart_show_lines = st.checkbox(
						'Show Constellation Lines',
						value=True,
						key='astro_chart_show_lines' )
					
					chart_show_boundaries = st.checkbox(
						'Show Constellation Boundaries',
						value=True,
						key='astro_chart_show_boundaries' )
				
				chart_show_const_names = st.checkbox(
					'Show Constellation Names',
					value=False,
					key='astro_chart_show_const_names' )
				
				chart_timeout = st.number_input(
					'Timeout',
					min_value=1,
					max_value=60,
					value=20,
					step=1,
					key='astro_chart_timeout' )
				
				chart_btn_c1, chart_btn_c2 = st.columns( 2 )
				
				with chart_btn_c1:
					if st.button( label='Run', icon='🏃', key='astro_chart_run',
							use_container_width=True ):
						try:
							service = StarChart( )
							
							if chart_mode == 'object_chart':
								result = service.fetch_object_chart(
									name=chart_object_name,
									zoom=int( chart_zoom ),
									box_color=chart_box_color,
									show_box=bool( chart_show_box ),
									image_source=chart_image_source_value,
									time=int( chart_timeout ) )
							
							elif chart_mode == 'coordinate_chart':
								result = service.fetch_coordinate_chart(
									ra=float( chart_ra ),
									dec=float( chart_dec ),
									zoom=int( chart_zoom ),
									box_color=chart_box_color,
									show_box=bool( chart_show_box ),
									show_grid=bool( chart_show_grid ),
									show_lines=bool( chart_show_lines ),
									show_boundaries=bool( chart_show_boundaries ),
									image_source=chart_image_source_value )
							
							else:
								result = service.fetch_static_chart(
									ra=float( chart_ra ),
									dec=float( chart_dec ),
									zoom=int( chart_zoom ),
									image_source=chart_image_source_value,
									show_grid=bool( chart_show_grid ),
									show_lines=bool( chart_show_lines ),
									show_boundaries=bool( chart_show_boundaries ),
									show_const_names=bool( chart_show_const_names ),
									width=int( chart_width ),
									height=int( chart_height ),
									magnitude=float( chart_magnitude ) )
							
							result_url = ''
							if isinstance( result, dict ):
								result_url = (
										result.get( 'chart_url', '' )
										or result.get( 'image_url', '' )
										or result.get( 'static_chart_url', '' )
										or result.get( 'preferred_image_url', '' )
										or result.get( 'snapshot_page_url', '' )
										or result.get( 'url', '' )
								)
							
							st.session_state[ 'astro_last_source' ] = 'Star Chart'
							st.session_state[ 'astro_last_result' ] = normalize( result ) or { }
							st.session_state[ 'astro_last_latitude' ] = None
							st.session_state[ 'astro_last_longitude' ] = None
							st.session_state[ 'astro_last_url' ] = result_url
							st.success( 'Star Chart request completed.' )
						
						except Exception as ex:
							st.error( f'Star Chart request failed: {ex}' )
				
				with chart_btn_c2:
					if st.button( label='Clear', icon='🧹', key='astro_chart_clear',
							use_container_width=True ):
						st.session_state[ 'astro_last_source' ] = ''
						st.session_state[ 'astro_last_result' ] = { }
						st.session_state[ 'astro_last_latitude' ] = None
						st.session_state[ 'astro_last_longitude' ] = None
						st.session_state[ 'astro_last_url' ] = ''
			
			# ------------------------------------------------------------------
			# SATELLITE CENTER
			# ------------------------------------------------------------------
			with st.expander( '🛰️ Satellite Center', expanded=False ):
				st.badge( label='About API', color='blue', help=cfg.SATELLITE_CENTER )
				st.caption(
					'Uses NASA SSCWeb. Run Observatories first to discover valid observatory IDs, '
					'then use Locations to retrieve basic position data for selected spacecraft.' )
				
				satellite_mode_labels = {
						'Observatories': 'observatories',
						'Ground Stations': 'ground_stations',
						'Locations': 'locations'
				}
				
				satellite_mode_label = st.selectbox(
					'Mode',
					options=list( satellite_mode_labels.keys( ) ),
					key='astro_satellite_mode_label' )
				
				satellite_mode = satellite_mode_labels[ satellite_mode_label ]
				
				satellite_timeout = st.number_input(
					'Timeout',
					min_value=1,
					max_value=60,
					value=20,
					step=1,
					key='astro_satellite_timeout' )
				
				satellite_query = ''
				satellite_start_date = dt.date.today( )
				satellite_start_time = ''
				satellite_end_date = dt.date.today( )
				satellite_end_time = ''
				satellite_coordinate_systems = 'gse'
				satellite_resolution_factor = 1
				
				if satellite_mode == 'locations':
					satellite_query = st.text_input(
						'Observatories',
						value='iss',
						help='Comma-separated SSC observatory IDs. Examples: iss, mms1,mms2.',
						key='astro_satellite_query' )
					
					satellite_date_c1, satellite_date_c2 = st.columns( 2 )
					
					with satellite_date_c1:
						satellite_start_date = st.date_input(
							'Start Date',
							value=dt.date.today( ) - dt.timedelta( days=1 ),
							key='astro_satellite_start_date' )
						
						satellite_start_time = st.text_input(
							'Start Time',
							value='00:00:00Z',
							help='UTC time ending in Z. Example: 00:00:00Z.',
							key='astro_satellite_start_time' )
					
					with satellite_date_c2:
						satellite_end_date = st.date_input(
							'End Date',
							value=dt.date.today( ),
							key='astro_satellite_end_date' )
						
						satellite_end_time = st.text_input(
							'End Time',
							value='00:00:00Z',
							help='UTC time ending in Z. Example: 00:00:00Z.',
							key='astro_satellite_end_time' )
					
					satellite_coordinate_choice = st.selectbox(
						'Coordinate System Preset',
						options=[
								'GSE — Geocentric Solar Ecliptic',
								'GEO — Geographic',
								'GSM — Geocentric Solar Magnetospheric',
								'SM — Solar Magnetic',
								'GEI_TOD — Geocentric Equatorial Inertial True of Date',
								'GEI_J2000 — Geocentric Equatorial Inertial J2000',
								'Custom'
						],
						key='astro_satellite_coordinate_choice' )
					
					if satellite_coordinate_choice == 'GSE — Geocentric Solar Ecliptic':
						satellite_coordinate_systems = 'gse'
					
					elif satellite_coordinate_choice == 'GEO — Geographic':
						satellite_coordinate_systems = 'geo'
					
					elif satellite_coordinate_choice == 'GSM — Geocentric Solar Magnetospheric':
						satellite_coordinate_systems = 'gsm'
					
					elif satellite_coordinate_choice == 'SM — Solar Magnetic':
						satellite_coordinate_systems = 'sm'
					
					elif satellite_coordinate_choice == 'GEI_TOD — Geocentric Equatorial Inertial True of Date':
						satellite_coordinate_systems = 'gei_tod'
					
					elif satellite_coordinate_choice == 'GEI_J2000 — Geocentric Equatorial Inertial J2000':
						satellite_coordinate_systems = 'gei_j2000'
					
					else:
						satellite_coordinate_systems = st.text_input(
							'Custom Coordinate Systems',
							value='gse',
							help='Comma-separated coordinate systems accepted by SSCWeb.',
							key='astro_satellite_coordinate_systems_custom' )
					
					satellite_resolution_factor = st.number_input(
						'Resolution Factor',
						min_value=1,
						max_value=10000,
						value=1,
						step=1,
						help='Return one out of every N location values.',
						key='astro_satellite_resolution_factor' )
					
					if satellite_start_date > satellite_end_date:
						st.warning(
							'Start Date is after End Date. Correct the date range before running.' )
				
				elif satellite_mode == 'observatories':
					st.caption(
						'Returns SSC observatory IDs, names, and availability metadata. Use the Id '
						'values from this result in Locations mode.' )
				
				else:
					st.caption(
						'Returns SSC ground-station IDs, names, and geographic locations.' )
				
				satellite_btn_c1, satellite_btn_c2 = st.columns( 2 )
				
				with satellite_btn_c1:
					if st.button( label='Run', icon='🏃', key='astro_satellite_run',
							use_container_width=True ):
						try:
							service = SatelliteCenter( )
							
							if satellite_mode == 'locations':
								start_value = f'{satellite_start_date.isoformat( )}T{satellite_start_time}'
								end_value = f'{satellite_end_date.isoformat( )}T{satellite_end_time}'
							else:
								start_value = ''
								end_value = ''
							
							result = service.fetch(
								mode=satellite_mode,
								query=satellite_query,
								start_time=start_value,
								end_time=end_value,
								coordinate_systems=satellite_coordinate_systems,
								resolution_factor=int( satellite_resolution_factor ),
								time=int( satellite_timeout ) )
							
							st.session_state[ 'astro_last_source' ] = 'Satellite Center'
							st.session_state[ 'astro_last_result' ] = normalize( result ) or { }
							st.session_state[ 'astro_last_latitude' ] = None
							st.session_state[ 'astro_last_longitude' ] = None
							st.session_state[ 'astro_last_url' ] = ''
							
							st.success( 'Satellite Center request completed.' )
						
						except Exception as ex:
							st.error( f'Satellite Center request failed: {ex}' )
				
				with satellite_btn_c2:
					if st.button( label='Clear', icon='🧹', key='astro_satellite_clear',
							use_container_width=True ):
						st.session_state[ 'astro_last_source' ] = ''
						st.session_state[ 'astro_last_result' ] = { }
						st.session_state[ 'astro_last_latitude' ] = None
						st.session_state[ 'astro_last_longitude' ] = None
						st.session_state[ 'astro_last_url' ] = ''
			
			# ------------------------------------------------------------------
			# ASTRO CATALOG
			# ------------------------------------------------------------------
			with st.expander( '🔭 Astro Catalog', expanded=False ):
				st.badge( label='About API', color='blue', help=cfg.ASTRONOMY_CATALOG )
				st.caption(
					'Uses the Open Astronomy Catalog API. Object Query retrieves a named object; '
					'Cone Search retrieves objects around right ascension and declination.' )
				
				catalog_mode_labels = {
						'Object Query': 'object_query',
						'Cone Search': 'cone_search'
				}
				
				catalog_mode_label = st.selectbox(
					'Mode',
					options=list( catalog_mode_labels.keys( ) ),
					key='astro_catalog_mode_label' )
				
				catalog_mode = catalog_mode_labels[ catalog_mode_label ]
				
				catalog_quantity_presets = {
						'Default Object Record': '',
						'Photometry': 'photometry',
						'Spectra': 'spectra',
						'Radio': 'radio',
						'X-Ray': 'xray',
						'Host': 'host',
						'Redshift': 'redshift',
						'Luminosity Distance': 'lumdist',
						'Claimed Type': 'claimedtype',
						'Sources': 'sources',
						'Custom': 'custom'
				}
				
				catalog_quantity_choice = st.selectbox(
					'Quantity Preset',
					options=list( catalog_quantity_presets.keys( ) ),
					key='astro_catalog_quantity_preset' )
				
				if catalog_quantity_choice == 'Custom':
					catalog_quantity = st.text_input(
						'Custom Quantity',
						value='',
						help='Optional Open Astronomy Catalog quantity path segment.',
						key='astro_catalog_quantity_custom' )
				else:
					catalog_quantity = catalog_quantity_presets[ catalog_quantity_choice ]
				
				catalog_attributes = st.text_input(
					'Attributes',
					value='',
					help='Optional comma-separated attribute path segments.',
					key='astro_catalog_attributes' )
				
				catalog_arguments = st.text_area(
					'Arguments',
					value='',
					help='Optional comma-separated or newline-separated key=value arguments.',
					key='astro_catalog_arguments' )
				
				catalog_data_format = st.selectbox(
					'Data Format',
					options=[ 'json', 'csv' ],
					key='astro_catalog_data_format' )
				
				catalog_timeout = st.number_input(
					'Timeout',
					min_value=1,
					max_value=60,
					value=20,
					step=1,
					key='astro_catalog_timeout' )
				
				if catalog_mode == 'object_query':
					catalog_query = st.text_input(
						'Object Name',
						value='SN2011fe',
						help='Example transient object name in the Open Astronomy Catalogs.',
						key='astro_catalog_query' )
					
					catalog_ra = ''
					catalog_dec = ''
					catalog_radius = 2
					
					st.caption(
						'Object Query ignores right ascension, declination, and radius.' )
				
				else:
					catalog_query = ''
					
					catalog_coord_c1, catalog_coord_c2 = st.columns( 2 )
					
					with catalog_coord_c1:
						catalog_ra = st.text_input(
							'Right Ascension',
							value='10:00:00',
							help='Right ascension accepted by the OAC wrapper.',
							key='astro_catalog_ra' )
					
					with catalog_coord_c2:
						catalog_dec = st.text_input(
							'Declination',
							value='+10:00:00',
							help='Declination accepted by the OAC wrapper.',
							key='astro_catalog_dec' )
					
					catalog_radius = st.number_input(
						'Radius',
						min_value=1,
						max_value=360,
						value=2,
						step=1,
						help='Cone-search radius passed directly to the AstroCatalog wrapper.',
						key='astro_catalog_radius' )
					
					st.caption(
						'Cone Search ignores Object Name and uses right ascension, declination, '
						'and radius.' )
				
				catalog_btn_c1, catalog_btn_c2 = st.columns( 2 )
				
				with catalog_btn_c1:
					if st.button( label='Run', icon='🏃', key='astro_catalog_run',
							use_container_width=True ):
						try:
							service = AstroCatalog( )
							result = service.fetch(
								mode=catalog_mode,
								query=catalog_query,
								quantity=catalog_quantity,
								attributes=catalog_attributes,
								arguments=catalog_arguments,
								ra=catalog_ra,
								dec=catalog_dec,
								radius=int( catalog_radius ),
								data_format=catalog_data_format,
								time=int( catalog_timeout ) )
							
							st.session_state[ 'astro_last_source' ] = 'Astro Catalog'
							st.session_state[ 'astro_last_result' ] = normalize( result ) or { }
							st.session_state[ 'astro_last_latitude' ] = None
							st.session_state[ 'astro_last_longitude' ] = None
							st.session_state[ 'astro_last_url' ] = ''
							st.success( 'Astro Catalog request completed.' )
						
						except Exception as ex:
							st.error( f'Astro Catalog request failed: {ex}' )
				
				with catalog_btn_c2:
					if st.button( label='Clear', icon='🧹', key='astro_catalog_clear',
							use_container_width=True ):
						st.session_state[ 'astro_last_source' ] = ''
						st.session_state[ 'astro_last_result' ] = { }
						st.session_state[ 'astro_last_latitude' ] = None
						st.session_state[ 'astro_last_longitude' ] = None
						st.session_state[ 'astro_last_url' ] = ''
			
			# ------------------------------------------------------------------
			# ASTROQUERY / SIMBAD
			# ------------------------------------------------------------------
			with st.expander( '🌌 AstroQuery / SIMBAD', expanded=False ):
				st.badge( label='About API', color='blue', help=cfg.ASTRO_QUERY )
				astroquery_mode = st.selectbox(
					'Mode',
					options=[ 'object_search', 'object_ids', 'region_search' ],
					key='astro_astroquery_mode' )
				
				astroquery_row_limit = st.number_input(
					'Row Limit',
					min_value=1,
					max_value=10000,
					value=100,
					step=1,
					key='astro_astroquery_row_limit' )
				
				if astroquery_mode in [ 'object_search', 'object_ids' ]:
					astroquery_query = st.text_input(
						'Object Name',
						value='M31',
						key='astro_astroquery_query' )
					
					astroquery_ra = ''
					astroquery_dec = ''
					astroquery_radius = 0.5
					astroquery_radius_unit = 'deg'
				
				else:
					astroquery_query = ''
					astroquery_ra = st.text_input(
						'Right Ascension',
						value='10.6847083',
						key='astro_astroquery_ra' )
					
					astroquery_dec = st.text_input(
						'Declination',
						value='41.2687500',
						key='astro_astroquery_dec' )
					
					astroquery_radius = st.number_input(
						'Radius',
						min_value=0.001,
						max_value=180.0,
						value=0.5,
						step=0.1,
						format='%.3f',
						key='astro_astroquery_radius' )
					
					astroquery_radius_unit = st.selectbox(
						'Radius Unit',
						options=[ 'deg', 'arcmin', 'arcsec' ],
						key='astro_astroquery_radius_unit' )
				
				astroquery_btn_c1, astroquery_btn_c2 = st.columns( 2 )
				
				with astroquery_btn_c1:
					if st.button( label='Run', icon='🏃', key='astro_astroquery_run',
							use_container_width=True ):
						try:
							service = AstroQuery( )
							result = service.fetch(
								mode=astroquery_mode,
								query=astroquery_query,
								ra=astroquery_ra,
								dec=astroquery_dec,
								radius=float( astroquery_radius ),
								radius_unit=astroquery_radius_unit,
								row_limit=int( astroquery_row_limit ) )
							
							st.session_state[ 'astro_last_source' ] = 'AstroQuery / SIMBAD'
							st.session_state[ 'astro_last_result' ] = normalize( result ) or { }
							st.session_state[ 'astro_last_latitude' ] = None
							st.session_state[ 'astro_last_longitude' ] = None
							st.session_state[ 'astro_last_url' ] = ''
							st.success( 'AstroQuery request completed.' )
						
						except Exception as ex:
							st.error( f'AstroQuery request failed: {ex}' )
				
				with astroquery_btn_c2:
					if st.button( label='Clear', icon='🧹', key='astro_astroquery_clear',
							use_container_width=True ):
						st.session_state[ 'astro_last_source' ] = ''
						st.session_state[ 'astro_last_result' ] = { }
						st.session_state[ 'astro_last_latitude' ] = None
						st.session_state[ 'astro_last_longitude' ] = None
						st.session_state[ 'astro_last_url' ] = ''
			
			# ------------------------------------------------------------------
			# STAR MAP
			# ------------------------------------------------------------------
			with st.expander( '🗺️ Star Map', expanded=False ):
				st.badge( label='About API', color='blue', help=cfg.STAR_MAP )
				st.caption(
					'Uses SKY-MAP link and snapshot workflows. Object Link builds an '
					'object-centered page, Coordinate Link builds a coordinate-centered page, '
					'and Snapshot attempts to retrieve a SKY-MAP snapshot page plus available '
					'image links.' )
				
				starmap_mode_labels = {
						'Object Link': 'object_link',
						'Coordinate Link': 'coordinate_link',
						'Snapshot': 'snapshot'
				}
				
				starmap_mode_label = st.selectbox(
					'Mode',
					options=list( starmap_mode_labels.keys( ) ),
					key='astro_starmap_mode_label' )
				
				starmap_mode = starmap_mode_labels[ starmap_mode_label ]
				
				starmap_example = st.selectbox(
					'Coordinate Example',
					options=[
							'Andromeda Galaxy / M31',
							'Orion Nebula / M42',
							'Galactic Center',
							'Custom'
					],
					key='astro_starmap_coordinate_example' )
				
				if starmap_example == 'Andromeda Galaxy / M31':
					starmap_default_object = 'M31'
					starmap_default_ra = 0.7117
					starmap_default_dec = 41.2670
				
				elif starmap_example == 'Orion Nebula / M42':
					starmap_default_object = 'M42'
					starmap_default_ra = 5.5881
					starmap_default_dec = -5.3911
				
				elif starmap_example == 'Galactic Center':
					starmap_default_object = 'Sgr A*'
					starmap_default_ra = 17.7611
					starmap_default_dec = -29.0078
				
				else:
					starmap_default_object = 'M31'
					starmap_default_ra = 0.7117
					starmap_default_dec = 41.2670
				
				starmap_zoom = st.number_input(
					'Zoom',
					min_value=1,
					max_value=20,
					value=5,
					step=1,
					key='astro_starmap_zoom' )
				
				starmap_image_source_choice = st.selectbox(
					'Image Source',
					options=[ 'DSS2', 'SDSS', 'GALEX', 'IRAS', 'RASS', 'Custom' ],
					key='astro_starmap_image_source_choice' )
				
				if starmap_image_source_choice == 'Custom':
					starmap_image_source = st.text_input(
						'Custom Image Source',
						value='DSS2',
						help='Enter the SKY-MAP image source value accepted by the API.',
						key='astro_starmap_image_source_custom' )
				else:
					starmap_image_source = starmap_image_source_choice
				
				starmap_box_color = st.selectbox(
					'Box Color',
					options=[ 'yellow', 'red', 'green', 'blue', 'white' ],
					key='astro_starmap_box_color' )
				
				if starmap_mode == 'object_link':
					starmap_query = st.text_input(
						'Object Name',
						value=starmap_default_object,
						help='Object name or catalog identifier. Examples: M31, M42, Sirius.',
						key='astro_starmap_query' )
					
					starmap_ra = 0.0
					starmap_dec = 0.0
					
					st.caption(
						'Object Link uses the object name and ignores right ascension and declination.' )
				
				else:
					starmap_query = ''
					starmap_coord_c1, starmap_coord_c2 = st.columns( 2 )
					
					with starmap_coord_c1:
						starmap_ra = st.number_input(
							'Right Ascension',
							value=float( starmap_default_ra ),
							format='%.7f',
							help='Right ascension in decimal hours for SKY-MAP link/snapshot endpoints.',
							key='astro_starmap_ra' )
					
					with starmap_coord_c2:
						starmap_dec = st.number_input(
							'Declination',
							value=float( starmap_default_dec ),
							format='%.7f',
							help='Declination in decimal degrees.',
							key='astro_starmap_dec' )
					
					if starmap_mode == 'coordinate_link':
						st.caption(
							'Coordinate Link builds a SKY-MAP page centered on right ascension '
							'and declination.' )
					else:
						st.caption(
							'Snapshot requests the SKY-MAP snapshot endpoint and attempts to extract '
							'available save-as image links.' )
				
				starmap_options_c1, starmap_options_c2 = st.columns( 2 )
				
				with starmap_options_c1:
					starmap_show_box = st.checkbox(
						'Show Box',
						value=True,
						key='astro_starmap_show_box' )
					
					starmap_show_grid = st.checkbox(
						'Show Grid',
						value=True,
						key='astro_starmap_show_grid' )
				
				with starmap_options_c2:
					starmap_show_lines = st.checkbox(
						'Show Lines',
						value=True,
						key='astro_starmap_show_lines' )
					
					starmap_show_boundaries = st.checkbox(
						'Show Boundaries',
						value=True,
						key='astro_starmap_show_boundaries' )
				
				starmap_show_const_names = st.checkbox(
					'Show Constellation Names',
					value=False,
					key='astro_starmap_show_const_names' )
				
				starmap_timeout = st.number_input(
					'Timeout',
					min_value=1,
					max_value=60,
					value=20,
					step=1,
					key='astro_starmap_timeout' )
				
				starmap_btn_c1, starmap_btn_c2 = st.columns( 2 )
				
				with starmap_btn_c1:
					if st.button( label='Run', icon='🏃', key='astro_starmap_run',
							use_container_width=True ):
						try:
							service = StarMap( )
							result = service.fetch(
								mode=starmap_mode,
								query=starmap_query,
								ra=float( starmap_ra ),
								dec=float( starmap_dec ),
								zoom=int( starmap_zoom ),
								image_source=starmap_image_source,
								box_color=starmap_box_color,
								show_box=bool( starmap_show_box ),
								show_grid=bool( starmap_show_grid ),
								show_lines=bool( starmap_show_lines ),
								show_boundaries=bool( starmap_show_boundaries ),
								show_const_names=bool( starmap_show_const_names ),
								time=int( starmap_timeout ) )
							
							result_url = ''
							if isinstance( result, dict ):
								result_url = (
										result.get( 'preferred_image_url', '' )
										or result.get( 'snapshot_page_url', '' )
										or result.get( 'object_page_url', '' )
										or result.get( 'coordinate_page_url', '' )
										or result.get( 'url', '' )
								)
							
							st.session_state[ 'astro_last_source' ] = 'Star Map'
							st.session_state[ 'astro_last_result' ] = normalize( result ) or { }
							st.session_state[ 'astro_last_latitude' ] = None
							st.session_state[ 'astro_last_longitude' ] = None
							st.session_state[ 'astro_last_url' ] = result_url
							st.success( 'Star Map request completed.' )
						
						except Exception as ex:
							st.error( f'Star Map request failed: {ex}' )
				
				with starmap_btn_c2:
					if st.button( label='Clear', icon='🧹', key='astro_starmap_clear',
							use_container_width=True ):
						st.session_state[ 'astro_last_source' ] = ''
						st.session_state[ 'astro_last_result' ] = { }
						st.session_state[ 'astro_last_latitude' ] = None
						st.session_state[ 'astro_last_longitude' ] = None
						st.session_state[ 'astro_last_url' ] = ''

		with astro_c2:
			# ------------------------------------------------------------------
			# ASTRONOMICAL RESULTS
			# ------------------------------------------------------------------
			st.markdown( '##### Astronomical Results' )

			astro_source = st.session_state.get( 'astro_last_source', '' )
			astro_result = st.session_state.get( 'astro_last_result', { } )
			astro_latitude = st.session_state.get( 'astro_last_latitude', None )
			astro_longitude = st.session_state.get( 'astro_last_longitude', None )
			astro_url = st.session_state.get( 'astro_last_url', '' )

			if not astro_result:
				st.info( 'No astronomical results available.' )

			else:
				if astro_source:
					st.caption( f'Source: {astro_source}' )

				if astro_latitude is not None and astro_longitude is not None:
					try:
						lat_value = float( astro_latitude )
						lng_value = float( astro_longitude )

						lat_c, lng_c = st.columns( 2 )
						with lat_c:
							st.metric( 'Latitude', f'{lat_value:.6f}' )
						with lng_c:
							st.metric( 'Longitude', f'{lng_value:.6f}' )

						preview_url = static_maps.pin(
							lat=lat_value,
							lng=lng_value,
							zoom=6,
							size='600x400' )

						st.image( preview_url )

					except Exception as ex:
						st.warning( f'Static map preview failed: {ex}' )

				if astro_url:
					st.markdown( '##### Generated Link' )
					st.markdown( f'[Open Generated Astronomical Resource]({astro_url})' )

					try:
						ext = [ '.png', '.jpg', '.jpeg' ]
						if any( astro_url.lower( ).endswith( ext ) for ext in ext ):
							st.image( astro_url )
					except Exception:
						pass

				summary = astro_result.get( 'summary', None ) if isinstance( astro_result,
					dict ) else None

				if isinstance( summary, dict ) and summary:
					st.markdown( '##### Summary' )
					st.data_editor(
						pd.DataFrame( [ summary ] ),
						key='astro_summary_table',
						use_container_width=True,
						disabled=True )

				columns = astro_result.get( 'columns', None ) if isinstance( astro_result,
					dict ) else None
				rows = astro_result.get( 'rows', None ) if isinstance( astro_result,
					dict ) else None

				if isinstance( rows, list ) and rows:
					st.markdown( '##### Rows' )

					if isinstance( columns, list ) and columns:
						df_astro_rows = pd.DataFrame( rows, columns=columns )
					else:
						df_astro_rows = pd.DataFrame( rows )

					st.data_editor( df_astro_rows, key='astro_rows_table',
						use_container_width=True, disabled=True )

				st.markdown( '##### Raw Result' )
				st.json( astro_result )

	with st.expander( label='Astronomical RAG', icon='🧠', expanded=False ):
		from processing import render_mode_processing_controls
		render_mode_processing_controls( 'astro', 'astro_last_result', 'astro_last_source',
			'astronomical_rag' )

# ==============================================================================
# CELESTIAL MAP MODE
# ==============================================================================
elif mode == 'Celestial Map':
	left, center, right = st.columns( [ 0.10, 0.8, 0.10 ] )
	with center:
		st.subheader( 'Celestial Map' )
		st.divider( )
		
		global_location = get_default_location( )
		location_state = get_location_state( )
		has_global_coords = has_valid_global_coordinates( )
		
		status_c1, status_c2, status_c3 = st.columns( 3, border=True )
		status_c1.metric( 'Location', compose_location_from_state( ) or global_location )
		status_c2.metric( 'Latitude', f'{float( location_state[ "latitude" ] ):.4f}' )
		status_c3.metric( 'Longitude', f'{float( location_state[ "longitude" ] ):.4f}' )
		
		set_blue_divider( )
		
		control_c1, control_c2 = st.columns( [ 0.50, 0.50 ], border=True )
		
		with control_c1:
			use_global_coordinates = st.checkbox(
				'Use User-Location',
				value=has_global_coords,
				key='celestial_use_global_coordinates' )
			
			if use_global_coordinates:
				celestial_latitude = float( location_state[ 'latitude' ] )
				celestial_longitude = float( location_state[ 'longitude' ] )
				
				coord_c1, coord_c2 = st.columns( 2 )
				with coord_c1:
					st.number_input(
						'Latitude',
						value=celestial_latitude,
						format='%.6f',
						key='celestial_global_latitude_display',
						disabled=True )
				
				with coord_c2:
					st.number_input(
						'Longitude',
						value=celestial_longitude,
						format='%.6f',
						key='celestial_global_longitude_display',
						disabled=True )
			
			else:
				manual_default_latitude = (
						float( location_state[ 'latitude' ] )
						if has_global_coords
						else get_default_latitude( ))
				
				manual_default_longitude = (
						float( location_state[ 'longitude' ] )
						if has_global_coords
						else get_default_longitude( ))
				
				coord_c1, coord_c2 = st.columns( 2 )
				with coord_c1:
					celestial_latitude = st.number_input(
						'Latitude',
						value=manual_default_latitude,
						format='%.6f',
						key='celestial_manual_latitude' )
				
				with coord_c2:
					celestial_longitude = st.number_input(
						'Longitude',
						value=manual_default_longitude,
						format='%.6f',
						key='celestial_manual_longitude' )
		
		with control_c2:
			celestial_location = st.text_input(
				'Location Label',
				value=compose_location_from_state( ) or global_location,
				key='celestial_location_label' )
			
			celestial_zoom = st.slider(
				'Location Picker Zoom',
				min_value=1,
				max_value=18,
				value=int( st.session_state.get( 'zoom', 8 ) or 8 ),
				key='celestial_location_picker_zoom' )
			
			save_coordinates = st.checkbox(
				'Save Coordinates to Global State',
				value=True,
				key='celestial_save_coordinates' )
		
		if not has_valid_coordinates( celestial_latitude, celestial_longitude ):
			st.warning( 'Provide valid coordinates before rendering the Celestial Map.' )
			st.stop( )
		
		if save_coordinates:
			set_location_state(
				location=celestial_location,
				description='Celestial Map observer location',
				latitude=float( celestial_latitude ),
				longitude=float( celestial_longitude ) )
			st.session_state[ 'zoom' ] = int( celestial_zoom )
		
		set_blue_divider( )
		
		render_celestial_map(
			asset_root='assets/starmap',
			height=1400,
			latitude=float( celestial_latitude ),
			longitude=float( celestial_longitude ),
			location=celestial_location,
			zoom=int( celestial_zoom ) )

# ==============================================================================
# GEOLOGICAL MODE
# ==============================================================================
elif mode == 'Geological':
	left, center, right = st.columns( [ 0.05, 0.9, 0.05 ] )
	with center:
		st.subheader( 'Geological Data' )
		st.divider( )
		
		global_location = get_default_location( )
		global_latitude = get_default_latitude( )
		global_longitude = get_default_longitude( )
		global_box = create_bounding_box_from_center( global_latitude, global_longitude )
		
		location_c1, location_c2, location_c3 = st.columns( 3, border=True )
		location_c1.metric( 'Location', global_location )
		location_c2.metric( 'Latitude', f'{float( global_latitude ):.4f}' )
		location_c3.metric( 'Longitude', f'{float( global_longitude ):.4f}' )
		
		set_blue_divider( )
		
		geo_c1, geo_c2 = st.columns( [ 0.40, 0.60 ], border=True, gap='xsmall' )
		with geo_c1:
			# ------------------------------------------------------------------
			# USGS EARTHQUAKES
			# ------------------------------------------------------------------
			with st.expander( '🌎 USGS Earthquakes', expanded=True ):
				st.badge( label='About API', color='blue', help=cfg.USGS_EARTHQUAKES )
				quake_mode = st.selectbox( 'Mode', options=[ 'feed', 'search' ],
					key='geo_quake_mode' )
				
				quake_timeout = st.number_input( 'Timeout', min_value=1, max_value=60,
					value=20, step=1, key='geo_quake_timeout' )
				
				if quake_mode == 'feed':
					quake_feed = st.selectbox( 'Feed',
						options=[
								'all_hour.geojson',
								'all_day.geojson',
								'all_week.geojson',
								'all_month.geojson',
								'1.0_hour.geojson',
								'1.0_day.geojson',
								'1.0_week.geojson',
								'1.0_month.geojson',
								'2.5_hour.geojson',
								'2.5_day.geojson',
								'2.5_week.geojson',
								'2.5_month.geojson',
								'4.5_hour.geojson',
								'4.5_day.geojson',
								'4.5_week.geojson',
								'4.5_month.geojson',
								'significant_hour.geojson',
								'significant_day.geojson',
								'significant_week.geojson',
								'significant_month.geojson'
						], key='geo_quake_feed' )
					
					quake_start_date = ''
					quake_end_date = ''
					quake_min_magnitude = 1.0
					quake_max_magnitude = 10.0
					quake_limit = 25
					quake_order_by = 'time'
					quake_event_type = 'earthquake'
					quake_use_location = False
					quake_latitude = None
					quake_longitude = None
					quake_radius = None
				
				else:
					quake_feed = 'all_day.geojson'
					
					search_c1, search_c2 = st.columns( 2 )
					
					with search_c1:
						quake_start = st.date_input( 'Start Date',
							value=dt.date.today( ) - dt.timedelta( days=7 ),
							key='geo_quake_start_date' )
					
					with search_c2:
						quake_end = st.date_input( 'End Date', value=dt.date.today( ),
							key='geo_quake_end_date' )
					
					quake_start_date = quake_start.isoformat( )
					quake_end_date = quake_end.isoformat( )
					
					mag_c1, mag_c2 = st.columns( 2 )
					with mag_c1:
						quake_min_magnitude = st.number_input( 'Minimum Magnitude', min_value=0.0,
							max_value=10.0, value=1.0, step=0.1,
							format='%.1f', key='geo_quake_min_magnitude' )
					
					with mag_c2:
						quake_max_magnitude = st.number_input( 'Maximum Magnitude', min_value=0.0,
							max_value=10.0, value=10.0, step=0.1,
							format='%.1f', key='geo_quake_max_magnitude' )
					
					quake_limit = st.number_input( 'Limit', min_value=1, max_value=20000, value=25,
						step=1, key='geo_quake_limit' )
					
					quake_order_by = st.selectbox( 'Order By',
						options=[ 'time', 'time-asc', 'magnitude', 'magnitude-asc' ],
						key='geo_quake_order_by' )
					
					quake_event_type = st.text_input( 'Event Type', value='earthquake',
						key='geo_quake_event_type' )
					
					quake_use_location = st.checkbox( 'Use Location Radius Filter',
						value=False, key='geo_quake_use_location' )
					
					if quake_use_location:
						loc_c1, loc_c2 = st.columns( 2 )
						
						with loc_c1:
							quake_latitude = st.number_input( 'Latitude',
								value=float( global_latitude ), format='%.6f',
								key='geo_quake_latitude' )
						
						with loc_c2:
							quake_longitude = st.number_input( 'Longitude',
								value=float( global_longitude ), format='%.6f',
								key='geo_quake_longitude' )
						
						quake_radius = st.number_input( 'Maximum Radius KM',
							min_value=1.0,
							max_value=20000.0,
							value=float( st.session_state.get( 'radius', 500.0 ) or 500.0 ),
							step=10.0,
							format='%.1f',
							key='geo_quake_radius' )
					
					else:
						quake_latitude = None
						quake_longitude = None
						quake_radius = None
				
				quake_btn_c1, quake_btn_c2 = st.columns( 2 )
				with quake_btn_c1:
					if st.button( label='Run', icon='🏃', key='geo_quake_run',
							use_container_width=True ):
						try:
							service = USGSEarthquakes( )
							
							result = service.fetch( mode=quake_mode, feed=quake_feed,
								start_date=quake_start_date, end_date=quake_end_date,
								min_magnitude=float( quake_min_magnitude ),
								max_magnitude=float( quake_max_magnitude ),
								limit=int( quake_limit ), order_by=quake_order_by,
								event_type=quake_event_type, latitude=quake_latitude,
								longitude=quake_longitude, max_radius_km=quake_radius,
								time=int( quake_timeout ) )
							
							st.session_state[ 'geo_last_source' ] = 'USGS Earthquakes'
							st.session_state[ 'geo_last_result' ] = result or { }
							st.session_state[ 'geo_last_latitude' ] = quake_latitude
							st.session_state[ 'geo_last_longitude' ] = quake_longitude
							
							if quake_radius is not None:
								st.session_state[ 'radius' ] = float( quake_radius )
							
							set_global_coordinates_from_result( quake_latitude, quake_longitude,
								location=global_location,
								description='USGS Earthquake search center' )
							
							st.success( 'USGS Earthquake request completed.' )
						
						except Exception as ex:
							st.error( f'USGS Earthquake request failed: {ex}' )
				
				with quake_btn_c2:
					if st.button( label='Clear', icon='🧹', key='geo_quake_clear',
							use_container_width=True ):
						st.session_state[ 'geo_last_source' ] = ''
						st.session_state[ 'geo_last_result' ] = { }
						st.session_state[ 'geo_last_latitude' ] = None
						st.session_state[ 'geo_last_longitude' ] = None
						st.session_state[ 'geo_last_image_path' ] = ''
			
			# ------------------------------------------------------------------
			# GLOBAL IMAGERY
			# ------------------------------------------------------------------
			with st.expander( '🛰️ Global Imagery', expanded=False ):
				st.badge( label='About API', color='blue', help=cfg.NASA_GLOBAL_IMAGERY )
				st.caption(
					'Uses NASA GIBS WMS imagery. The default product preserves the original '
					'MODIS Terra corrected-reflectance request and output path.' )
				
				imagery_product = st.selectbox(
					'Product',
					options=[
							'NASA GIBS EPSG:4326 Default Map Service',
							'NASA GIBS Custom WMS Map',
							'NASA GIBS EPSG:3857 Legacy Mercator Map',
							'NASA GIBS GetCapabilities URL'
					],
					key='geo_imagery_product' )
				
				imagery_timeout = st.number_input(
					'Timeout',
					min_value=1,
					max_value=60,
					value=20,
					step=1,
					key='geo_imagery_timeout' )
				
				imagery_layer = 'MODIS_Terra_CorrectedReflectance_TrueColor'
				imagery_projection = 'epsg4326'
				imagery_quality = 'best'
				imagery_date_value = dt.date( 2021, 9, 21 )
				imagery_format = 'image/png'
				imagery_transparent = True
				imagery_width = 1200
				imagery_height = 600
				imagery_output_dir = 'python-examples'
				imagery_output_name = 'MODIS_Terra_CorrectedReflectance_TrueColor.png'
				imagery_west = -180.0
				imagery_south = -90.0
				imagery_east = 180.0
				imagery_north = 90.0
				imagery_center_latitude = None
				imagery_center_longitude = None
				
				if imagery_product == 'NASA GIBS Custom WMS Map':
					imagery_layer = st.text_input(
						'Layer',
						value='MODIS_Terra_CorrectedReflectance_TrueColor',
						help='NASA GIBS WMS layer identifier.',
						key='geo_imagery_layer' )
					
					imagery_date_value = st.date_input(
						'Image Date',
						value=dt.date.today( ) - dt.timedelta( days=1 ),
						key='geo_imagery_date' )
					
					imagery_projection = st.selectbox(
						'Projection',
						options=[ 'epsg4326', 'epsg3857' ],
						key='geo_imagery_projection' )
					
					imagery_quality = st.selectbox(
						'Quality',
						options=[ 'best', 'std' ],
						key='geo_imagery_quality' )
					
					imagery_format = st.selectbox(
						'Image Format',
						options=[ 'image/png', 'image/jpeg' ],
						key='geo_imagery_format' )
					
					imagery_transparent = st.checkbox(
						'Transparent No-Data Pixels',
						value=True,
						key='geo_imagery_transparent' )
					
					imagery_size_c1, imagery_size_c2 = st.columns( 2 )
					
					with imagery_size_c1:
						imagery_width = st.number_input(
							'Width',
							min_value=128,
							max_value=4096,
							value=1200,
							step=64,
							key='geo_imagery_width' )
					
					with imagery_size_c2:
						imagery_height = st.number_input(
							'Height',
							min_value=128,
							max_value=4096,
							value=600,
							step=64,
							key='geo_imagery_height' )
					
					st.caption(
						'Bounding box defaults are centered on the global latitude and longitude.' )
					
					imagery_box_c1, imagery_box_c2 = st.columns( 2 )
					
					with imagery_box_c1:
						imagery_west = st.number_input(
							'West Longitude',
							value=float( global_box[ 'west' ] ),
							format='%.6f',
							key='geo_imagery_west' )
						
						imagery_south = st.number_input(
							'South Latitude',
							value=float( global_box[ 'south' ] ),
							format='%.6f',
							key='geo_imagery_south' )
					
					with imagery_box_c2:
						imagery_east = st.number_input(
							'East Longitude',
							value=float( global_box[ 'east' ] ),
							format='%.6f',
							key='geo_imagery_east' )
						
						imagery_north = st.number_input(
							'North Latitude',
							value=float( global_box[ 'north' ] ),
							format='%.6f',
							key='geo_imagery_north' )
					
					imagery_output_dir = st.text_input(
						'Output Directory',
						value='python-examples',
						key='geo_imagery_output_dir' )
					
					imagery_output_name = st.text_input(
						'Output Filename',
						value='',
						help='Optional. Leave blank to let the wrapper generate a filename.',
						key='geo_imagery_output_name' )
					
					imagery_center_latitude = (
							                          float( imagery_south ) + float(
						                          imagery_north )
					                          ) / 2.0
					
					imagery_center_longitude = (
							                           float( imagery_west ) + float( imagery_east )
					                           ) / 2.0
				
				elif imagery_product == 'NASA GIBS EPSG:3857 Legacy Mercator Map':
					imagery_layer = 'Landsat_WELD_CorrectedReflectance_Bands157_Global_Annual'
					imagery_projection = 'epsg3857'
					imagery_quality = 'best'
					imagery_date_value = dt.date( 2000, 12, 1 )
					imagery_format = 'image/png'
					imagery_transparent = True
					imagery_width = 600
					imagery_height = 600
					imagery_output_dir = 'python-examples'
					imagery_output_name = (
							'Landsat_WELD_CorrectedReflectance_Bands157_Global_Annual.png'
					)
					imagery_west = -8000000.0
					imagery_south = -8000000.0
					imagery_east = 8000000.0
					imagery_north = 8000000.0
					imagery_center_latitude = None
					imagery_center_longitude = None
					
					st.caption(
						'Uses the preserved legacy EPSG:3857 WMS product through '
						'GlobalImagery.fetch_mercator_map().' )
				
				elif imagery_product == 'NASA GIBS GetCapabilities URL':
					imagery_projection = st.selectbox(
						'Projection',
						options=[ 'epsg4326', 'epsg3857' ],
						key='geo_imagery_capabilities_projection' )
					
					imagery_quality = st.selectbox(
						'Quality',
						options=[ 'best', 'std' ],
						key='geo_imagery_capabilities_quality' )
					
					st.caption(
						'Builds a NASA GIBS WMS GetCapabilities URL. It does not download an image.' )
				
				else:
					st.caption(
						'Runs the preserved default EPSG:4326 MODIS Terra corrected-reflectance '
						'image request.' )
				
				imagery_btn_c1, imagery_btn_c2 = st.columns( 2 )
				
				with imagery_btn_c1:
					if st.button( label='Run', icon='🏃', key='geo_imagery_run',
							use_container_width=True ):
						try:
							Path( imagery_output_dir ).mkdir( parents=True, exist_ok=True )
							service = GlobalImagery( )
							
							if imagery_product == 'NASA GIBS EPSG:4326 Default Map Service':
								result = service.fetch_map_services( )
								image_path = (
										'python-examples/'
										'MODIS_Terra_CorrectedReflectance_TrueColor.png'
								)
								result_payload = result or {
										'mode': 'fetch_map_services',
										'product': imagery_product,
										'image_path': image_path
								}
							
							elif imagery_product == 'NASA GIBS Custom WMS Map':
								result = service.fetch_wms_map(
									layer=imagery_layer,
									image_date=imagery_date_value.isoformat( ),
									bbox=(
											float( imagery_west ),
											float( imagery_south ),
											float( imagery_east ),
											float( imagery_north )
									),
									width=int( imagery_width ),
									height=int( imagery_height ),
									projection=imagery_projection,
									quality=imagery_quality,
									image_format=imagery_format,
									transparent=bool( imagery_transparent ),
									output_dir=imagery_output_dir,
									output_name=imagery_output_name,
									time=int( imagery_timeout ) )
								
								result_payload = result or { }
								image_path = str( result_payload.get( 'image_path', '' ) )
							
							elif imagery_product == 'NASA GIBS EPSG:3857 Legacy Mercator Map':
								result = service.fetch_mercator_map( )
								image_path = (
										'python-examples/'
										'Landsat_WELD_CorrectedReflectance_Bands157_Global_Annual.png'
								)
								result_payload = result or {
										'mode': 'fetch_mercator_map',
										'product': imagery_product,
										'image_path': image_path
								}
							
							else:
								capabilities_url = service.get_capabilities_url(
									projection=imagery_projection,
									quality=imagery_quality )
								
								image_path = ''
								result_payload = {
										'mode': 'get_capabilities_url',
										'product': imagery_product,
										'url': capabilities_url,
										'projection': imagery_projection,
										'quality': imagery_quality,
										'summary': {
												'rows': 1,
												'columns': 4,
												'description': 'NASA GIBS WMS GetCapabilities URL generated.'
										}
								}
							
							st.session_state[ 'geo_last_source' ] = 'Global Imagery'
							st.session_state[ 'geo_last_result' ] = result_payload
							st.session_state[ 'geo_last_latitude' ] = imagery_center_latitude
							st.session_state[ 'geo_last_longitude' ] = imagery_center_longitude
							st.session_state[ 'geo_last_image_path' ] = image_path
							
							st.success( 'Global Imagery request completed.' )
						
						except Exception as ex:
							st.error( f'Global Imagery request failed: {ex}' )
				
				with imagery_btn_c2:
					if st.button( label='Clear', icon='🧹', key='geo_imagery_clear',
							use_container_width=True ):
						st.session_state[ 'geo_last_source' ] = ''
						st.session_state[ 'geo_last_result' ] = { }
						st.session_state[ 'geo_last_latitude' ] = None
						st.session_state[ 'geo_last_longitude' ] = None
						st.session_state[ 'geo_last_image_path' ] = ''
			
			# ------------------------------------------------------------------
			# USGS WATER DATA
			# ------------------------------------------------------------------
			with st.expander( '💧 USGS Water Data', expanded=False ):
				st.badge( label='About API', color='blue', help=cfg.USGS_WATER )
				st.caption(
					'Uses the USGS Water Data API. Parameter presets are provided for common '
					'USGS five-character time-series parameter codes.' )
				
				water_mode = st.selectbox(
					'Mode',
					options=[
							'monitoring-locations',
							'time-series-metadata',
							'latest-continuous',
							'latest-daily'
					],
					key='geo_water_mode' )
				
				water_timeout = st.number_input(
					'Timeout',
					min_value=1,
					max_value=60,
					value=20,
					step=1,
					key='geo_water_timeout' )
				
				water_limit = st.number_input(
					'Limit',
					min_value=1,
					max_value=1000,
					value=25,
					step=1,
					key='geo_water_limit' )
				
				water_parameter_presets = {
						'No Parameter Filter': '',
						'Discharge, cubic feet per second — 00060': '00060',
						'Gage Height / Stage, feet — 00065': '00065',
						'Water Temperature, Celsius — 00010': '00010',
						'Specific Conductance — 00095': '00095',
						'Dissolved Oxygen — 00300': '00300',
						'pH — 00400': '00400',
						'Turbidity — 63680': '63680',
						'Custom': 'custom'
				}
				
				water_site_type_presets = {
						'No Site-Type Filter': '',
						'Stream': 'ST',
						'Lake / Reservoir': 'LK',
						'Well': 'GW',
						'Spring': 'SP',
						'Atmosphere': 'AT',
						'Custom': 'custom'
				}
				
				water_monitoring_location_id = ''
				water_state_code = ''
				water_county_code = ''
				water_site_type = ''
				water_parameter_code = ''
				
				if water_mode == 'monitoring-locations':
					water_monitoring_location_id = st.text_input(
						'Monitoring Location ID',
						value='',
						help='Optional. Example: USGS-01491000',
						key='geo_water_monitoring_location_id' )
					
					water_state_code = st.text_input(
						'State Code',
						value='',
						help='Optional state filter. Example: US:24 for Maryland in OGC APIs, or use the API-supported state code format required by your endpoint.',
						key='geo_water_state_code' )
					
					water_county_code = st.text_input(
						'County Code',
						value='',
						help='Optional county filter.',
						key='geo_water_county_code' )
					
					water_site_type_choice = st.selectbox(
						'Site Type Preset',
						options=list( water_site_type_presets.keys( ) ),
						key='geo_water_site_type_preset' )
					
					if water_site_type_choice == 'Custom':
						water_site_type = st.text_input(
							'Custom Site Type',
							value='',
							help='Enter an API-supported site type code.',
							key='geo_water_site_type_custom' )
					else:
						water_site_type = water_site_type_presets[ water_site_type_choice ]
				
				else:
					water_monitoring_location_id = st.text_input(
						'Monitoring Location ID',
						value='USGS-01491000',
						help='Example: USGS-01491000',
						key='geo_water_monitoring_location_id_value' )
					
					water_parameter_choice = st.selectbox(
						'Parameter Preset',
						options=list( water_parameter_presets.keys( ) ),
						key='geo_water_parameter_preset' )
					
					if water_parameter_choice == 'Custom':
						water_parameter_code = st.text_input(
							'Custom Parameter Code',
							value='',
							help='Enter a USGS five-character parameter code.',
							key='geo_water_parameter_code_custom' )
					else:
						water_parameter_code = water_parameter_presets[ water_parameter_choice ]
					
					st.caption(
						'Common time-series parameters include 00060 for discharge, 00065 for '
						'gage height, and 00010 for water temperature.' )
				
				water_btn_c1, water_btn_c2 = st.columns( 2 )
				
				with water_btn_c1:
					if st.button( label='Run', icon='🏃', key='geo_water_run',
							use_container_width=True ):
						try:
							service = USGSWaterData( )
							result = service.fetch(
								mode=water_mode,
								monitoring_location_id=water_monitoring_location_id,
								state_code=water_state_code,
								county_code=water_county_code,
								site_type=water_site_type,
								parameter_code=water_parameter_code,
								limit=int( water_limit ),
								time=int( water_timeout ) )
							
							st.session_state[ 'geo_last_source' ] = 'USGS Water Data'
							st.session_state[ 'geo_last_result' ] = result or { }
							st.session_state[ 'geo_last_latitude' ] = None
							st.session_state[ 'geo_last_longitude' ] = None
							st.session_state[ 'geo_last_image_path' ] = ''
							st.success( 'USGS Water Data request completed.' )
						
						except Exception as ex:
							st.error( f'USGS Water Data request failed: {ex}' )
				
				with water_btn_c2:
					if st.button( label='Clear', icon='🧹', key='geo_water_clear',
							use_container_width=True ):
						st.session_state[ 'geo_last_source' ] = ''
						st.session_state[ 'geo_last_result' ] = { }
						st.session_state[ 'geo_last_latitude' ] = None
						st.session_state[ 'geo_last_longitude' ] = None
						st.session_state[ 'geo_last_image_path' ] = ''
			
			# ------------------------------------------------------------------
			# USGS THE NATIONAL MAP
			# ------------------------------------------------------------------
			with st.expander( '🗺️ USGS The National Map', expanded=False ):
				st.badge( label='About API', color='blue', help=cfg.USGS_NATIONAL_MAP )
				st.caption(
					'Uses TNMAccess for dataset discovery and downloadable National Map product '
					'search. Presets are provided for common datasets and product formats, but '
					'manual entry is preserved.' )
				
				tnm_mode = st.selectbox(
					'Mode',
					options=[ 'datasets', 'products' ],
					key='geo_tnm_mode' )
				
				tnm_timeout = st.number_input(
					'Timeout',
					min_value=1,
					max_value=60,
					value=20,
					step=1,
					key='geo_tnm_timeout' )
				
				tnm_dataset_presets = {
						'No Dataset Filter': '',
						'3D Elevation Program': '3D Elevation Program',
						'National Elevation Dataset': 'National Elevation Dataset',
						'National Hydrography Dataset': 'National Hydrography Dataset',
						'Watershed Boundary Dataset': 'Watershed Boundary Dataset',
						'National Transportation Dataset': 'National Transportation Dataset',
						'National Structures Dataset': 'National Structures Dataset',
						'US Topo': 'US Topo',
						'Historical Topographic Map Collection': 'Historical Topographic Map Collection',
						'Custom': 'custom'
				}
				
				tnm_format_presets = {
						'No Format Filter': '',
						'GeoTIFF': 'GeoTIFF',
						'IMG': 'IMG',
						'LAS': 'LAS',
						'LAZ': 'LAZ',
						'GeoPackage': 'GeoPackage',
						'Shapefile': 'Shapefile',
						'PDF': 'PDF',
						'Custom': 'custom'
				}
				
				if tnm_mode == 'datasets':
					tnm_dataset = ''
					tnm_query = ''
					tnm_bbox = ''
					tnm_prod_formats = ''
					tnm_max_items = 25
					tnm_offset = 0
					tnm_center_latitude = None
					tnm_center_longitude = None
					
					st.caption(
						'Datasets mode lists available National Map datasets and does not use '
						'global coordinates.' )
				
				else:
					tnm_dataset_choice = st.selectbox(
						'Dataset Preset',
						options=list( tnm_dataset_presets.keys( ) ),
						key='geo_tnm_dataset_preset' )
					
					if tnm_dataset_choice == 'Custom':
						tnm_dataset = st.text_input(
							'Custom Dataset',
							value='',
							help='Optional TNM dataset filter.',
							key='geo_tnm_dataset_custom' )
					else:
						tnm_dataset = tnm_dataset_presets[ tnm_dataset_choice ]
					
					tnm_query = st.text_input(
						'Search Query',
						value='',
						help='Optional free-text product search.',
						key='geo_tnm_query' )
					
					tnm_format_choice = st.selectbox(
						'Product Format Preset',
						options=list( tnm_format_presets.keys( ) ),
						key='geo_tnm_format_preset' )
					
					if tnm_format_choice == 'Custom':
						tnm_prod_formats = st.text_input(
							'Custom Product Formats',
							value='',
							help='Optional format filter such as GeoTIFF, IMG, LAS, LAZ, or PDF.',
							key='geo_tnm_prod_formats_custom' )
					else:
						tnm_prod_formats = tnm_format_presets[ tnm_format_choice ]
					
					tnm_use_bbox = st.checkbox(
						'Use Bounding Box',
						value=False,
						key='geo_tnm_use_bbox' )
					
					if tnm_use_bbox:
						st.caption(
							'Bounding box defaults are centered on the global latitude and longitude.' )
						
						tnm_box_c1, tnm_box_c2 = st.columns( 2 )
						
						with tnm_box_c1:
							tnm_min_x = st.number_input(
								'Min X / West Longitude',
								value=float( global_box[ 'west' ] ),
								format='%.6f',
								key='geo_tnm_min_x' )
							
							tnm_min_y = st.number_input(
								'Min Y / South Latitude',
								value=float( global_box[ 'south' ] ),
								format='%.6f',
								key='geo_tnm_min_y' )
						
						with tnm_box_c2:
							tnm_max_x = st.number_input(
								'Max X / East Longitude',
								value=float( global_box[ 'east' ] ),
								format='%.6f',
								key='geo_tnm_max_x' )
							
							tnm_max_y = st.number_input(
								'Max Y / North Latitude',
								value=float( global_box[ 'north' ] ),
								format='%.6f',
								key='geo_tnm_max_y' )
						
						tnm_bbox = (
								f'{float( tnm_min_x )},{float( tnm_min_y )},'
								f'{float( tnm_max_x )},{float( tnm_max_y )}'
						)
						
						tnm_center_latitude = (float( tnm_min_y ) + float( tnm_max_y )) / 2.0
						tnm_center_longitude = (float( tnm_min_x ) + float( tnm_max_x )) / 2.0
					
					else:
						tnm_bbox = ''
						tnm_center_latitude = None
						tnm_center_longitude = None
					
					tnm_max_items = st.number_input(
						'Max Items',
						min_value=1,
						max_value=1000,
						value=25,
						step=1,
						key='geo_tnm_max_items' )
					
					tnm_offset = st.number_input(
						'Offset',
						min_value=0,
						max_value=100000,
						value=0,
						step=1,
						key='geo_tnm_offset' )
				
				tnm_btn_c1, tnm_btn_c2 = st.columns( 2 )
				
				with tnm_btn_c1:
					if st.button( label='Run', icon='🏃', key='geo_tnm_run',
							use_container_width=True ):
						try:
							service = USGSTheNationalMap( )
							
							result = service.fetch(
								mode=tnm_mode,
								dataset=tnm_dataset,
								q=tnm_query,
								bbox=tnm_bbox,
								prod_formats=tnm_prod_formats,
								max_items=int( tnm_max_items ),
								offset=int( tnm_offset ),
								time=int( tnm_timeout ) )
							
							st.session_state[ 'geo_last_source' ] = 'USGS The National Map'
							st.session_state[ 'geo_last_result' ] = result or { }
							st.session_state[ 'geo_last_latitude' ] = tnm_center_latitude
							st.session_state[ 'geo_last_longitude' ] = tnm_center_longitude
							st.session_state[ 'geo_last_image_path' ] = ''
							
							set_global_coordinates_from_result(
								tnm_center_latitude,
								tnm_center_longitude,
								location=global_location,
								description='USGS The National Map bounding-box center' )
							
							st.success( 'USGS The National Map request completed.' )
						
						except Exception as ex:
							st.error( f'USGS The National Map request failed: {ex}' )
				
				with tnm_btn_c2:
					if st.button( label='Clear', icon='🧹', key='geo_tnm_clear',
							use_container_width=True ):
						st.session_state[ 'geo_last_source' ] = ''
						st.session_state[ 'geo_last_result' ] = { }
						st.session_state[ 'geo_last_latitude' ] = None
						st.session_state[ 'geo_last_longitude' ] = None
						st.session_state[ 'geo_last_image_path' ] = ''

		with geo_c2:
			# ------------------------------------------------------------------
			# GEOLOGICAL RESULTS
			# ------------------------------------------------------------------
			st.markdown( '##### Geological Results' )

			geo_source = st.session_state.get( 'geo_last_source', '' )
			geo_result = st.session_state.get( 'geo_last_result', { } )
			geo_latitude = st.session_state.get( 'geo_last_latitude', None )
			geo_longitude = st.session_state.get( 'geo_last_longitude', None )
			geo_image_path = st.session_state.get( 'geo_last_image_path', '' )

			if not geo_result:
				st.info( 'No geological results available.' )

			else:
				if geo_source:
					st.caption( f'Source: {geo_source}' )

				if geo_image_path and os.path.exists( geo_image_path ):
					st.markdown( '##### Image Output' )
					st.image( geo_image_path )

				summary = geo_result.get( 'summary', None ) if isinstance( geo_result,
					dict ) else None
				rows = geo_result.get( 'rows', None ) if isinstance( geo_result, dict ) else None

				if isinstance( summary, dict ) and summary:
					st.markdown( '##### Summary' )
					st.data_editor( pd.DataFrame( [ summary ] ), key='geo_summary_table',
						use_container_width=True, disabled=True )

				if geo_latitude is not None and geo_longitude is not None:
					try:
						lat_value = float( geo_latitude )
						lng_value = float( geo_longitude )

						lat_c, lng_c = st.columns( 2 )
						with lat_c:
							st.metric( 'Latitude', f'{lat_value:.6f}' )
						with lng_c:
							st.metric( 'Longitude', f'{lng_value:.6f}' )

						preview_url = static_maps.pin( lat=lat_value, lng=lng_value, zoom=5,
							size='600x400' )

						st.image( preview_url )

					except Exception as ex:
						st.warning( f'Static map preview failed: {ex}' )

				if isinstance( rows, list ) and rows:
					st.markdown( '##### Rows' )
					df_geo_rows = pd.DataFrame( rows )
					st.data_editor( df_geo_rows, key='geo_rows_table', use_container_width=True,
						disabled=True )

				st.markdown( '##### Raw Result' )
				st.json( geo_result )

# ==============================================================================
# TEXT GENERATION MODE
# ==============================================================================
	with st.expander( label='Geological RAG', icon='🧠', expanded=False ):
		from processing import render_mode_processing_controls
		render_mode_processing_controls( 'geo', 'geo_last_result', 'geo_last_source',
			'geological_rag' )

elif mode == 'Generative':
	left, center, right = st.columns( [ 0.05, 0.9, 0.05 ] )
	with center:
		st.subheader( f'🧠  Generative AI' )
		st.divider( )
		
		# -------- ChatGPT
		with st.expander( label='ChatGPT', expanded=True ):
			CHAT_REASONING_EFFORTS = [ 'minimal', 'low', 'medium', 'high' ]
			
			def _clear_chat_state( ) -> None:
				"""Clear the chat state state.
				
				Purpose:
					Supports the Mappy Streamlit application by executing the clear chat state
					workflow. The function preserves the existing UI behavior, session-state
					interactions, dataframe handling, database access, and service integrations
					defined by the application code.
				"""
				st.session_state[ 'chat_clear_request' ] = True
			
			def _normalize_chat_domains( value: object ) -> list[ str ]:
				"""Normalize chat domains values.
				
				Purpose:
					Supports the Mappy Streamlit application by executing the normalize chat domains
					workflow. The function preserves the existing UI behavior, session-state
					interactions, dataframe handling, database access, and service integrations
					defined by the application code.
				
				Args:
					value: object value used by the `_normalize_chat_domains` workflow.
				
				Returns:
					list[str]: Result produced by the `_normalize_chat_domains` workflow.
				
				Raises:
					Exception: Propagates validation, UI, data, database, or provider errors
						raised by the existing implementation.
				"""
				text = str( value or '' ).strip( )
				
				if not text:
					return [ ]
				
				values: list[ str ] = [ ]
				entries = re.split( r'[\n,;]+', text )
				
				for entry in entries:
					raw_value = str( entry or '' ).strip( ).lower( )
					
					if not raw_value:
						continue
					
					if not raw_value.startswith( 'http://' ) and not raw_value.startswith(
							'https://' ):
						raw_value = f'https://{raw_value}'
					
					parsed = urlparse( raw_value )
					domain = (parsed.netloc or parsed.path or '').strip( ).lower( )
					domain = re.sub( r':\d+$', '', domain )
					domain = domain.lstrip( '.' )
					
					if domain.startswith( 'www.' ):
						domain = domain[ 4: ]
					
					if not domain:
						continue
					
					if not re.fullmatch( r'[a-z0-9][a-z0-9.-]*\.[a-z]{2,}', domain ):
						raise ValueError( f'Invalid search domain: {domain}' )
					
					if domain not in values:
						values.append( domain )
				
				return values
			
			if 'chat_clear_request' not in st.session_state:
				st.session_state[ 'chat_clear_request' ] = False
			
			if 'chat_prompt' not in st.session_state:
				st.session_state[ 'chat_prompt' ] = ''
			
			if 'chat_system' not in st.session_state:
				st.session_state[ 'chat_system' ] = ''
			
			if 'chat_domains' not in st.session_state:
				st.session_state[ 'chat_domains' ] = ''
			
			if 'chat_json_mode' not in st.session_state:
				st.session_state[ 'chat_json_mode' ] = False
			
			if 'chat_reasoning' not in st.session_state:
				st.session_state[ 'chat_reasoning' ] = False
			
			if 'chat_web_search' not in st.session_state:
				st.session_state[ 'chat_web_search' ] = False
			
			if 'chat_store' not in st.session_state:
				st.session_state[ 'chat_store' ] = True
			
			if 'chat_stream' not in st.session_state:
				st.session_state[ 'chat_stream' ] = False
			
			if 'chat_seed' not in st.session_state:
				st.session_state[ 'chat_seed' ] = 0
			
			if st.session_state.get( 'chat_reasoning_effort', 'low' ) not in CHAT_REASONING_EFFORTS:
				st.session_state[ 'chat_reasoning_effort' ] = 'low'
			
			if st.session_state.get( 'chat_clear_request', False ):
				st.session_state[ 'chat_prompt' ] = ''
				st.session_state[ 'chat_system' ] = ''
				st.session_state[ 'chat_domains' ] = ''
				st.session_state[ 'chat_json_mode' ] = False
				st.session_state[ 'chat_reasoning' ] = False
				st.session_state[ 'chat_web_search' ] = False
				st.session_state[ 'chat_store' ] = True
				st.session_state[ 'chat_stream' ] = False
				st.session_state[ 'chat_seed' ] = 0
				st.session_state[ 'chat_reasoning_effort' ] = 'low'
				st.session_state[ 'chat_clear_request' ] = False
			
			col_left, col_right = st.columns( [ 1, 2 ], border=True )
			
			with col_left:
				chat_prompt = st.text_area( 'Prompt',
					value=st.session_state.get( 'chat_prompt', '' ), height=120, key='chat_prompt' )
				
				p_row1 = st.columns( 2 )
				p_row2 = st.columns( 2 )
				p_row3 = st.columns( 2 )
				p_row4 = st.columns( 2 )
				p_row5 = st.columns( 2 )
				
				with p_row1[ 0 ]:
					_chat_models = (cfg.GPT_MODELS
					                if hasattr( cfg, 'GPT_MODELS' ) and cfg.GPT_MODELS
					                else [ 'gpt-5.4', 'gpt-5', 'gpt-5-mini', 'gpt-5-nano',
					                       'gpt-4.1' ])
					
					chat_model = _model_selector( key_prefix='chat', label='Model',
						options=_chat_models,
						default_model=(
							'gpt-5-mini' if 'gpt-5-mini' in _chat_models else _chat_models[ 0 ]), )
				
				with p_row1[ 1 ]:
					chat_temperature = st.slider( 'Temperature', min_value=0.0, max_value=2.0,
						value=0.7, step=0.05, key='chat_temperature' )
				
				with p_row2[ 0 ]:
					chat_max_tokens = st.number_input( 'Max Tokens', min_value=1, max_value=32768,
						value=2048, step=1, key='chat_max_tokens' )
				
				with p_row2[ 1 ]:
					chat_top_p = st.slider( 'Top-P', min_value=0.0, max_value=1.0, value=1.0,
						step=0.01, key='chat_top_p' )
				
				with p_row3[ 0 ]:
					chat_seed = st.number_input( 'Seed', min_value=0, max_value=2_147_483_647,
						value=int( st.session_state.get( 'chat_seed', 0 ) ), step=1,
						key='chat_seed', help='Use 0 to omit the seed parameter.' )
				
				with p_row3[ 1 ]:
					chat_json_mode = st.checkbox( 'JSON Mode',
						value=bool( st.session_state.get( 'chat_json_mode', False ) ),
						key='chat_json_mode',
						help=('Current wrapper behavior adds JSON-only instructions. '
						      'A later Chat class drop-in should wire this to Responses '
						      'API text.format.') )
				
				with p_row4[ 0 ]:
					chat_reasoning = st.checkbox( 'Reasoning',
						value=bool( st.session_state.get( 'chat_reasoning', False ) ),
						key='chat_reasoning' )
				
				with p_row4[ 1 ]:
					chat_web_search = st.checkbox( 'Web Search',
						value=bool( st.session_state.get( 'chat_web_search', False ) ),
						key='chat_web_search' )
				
				with p_row5[ 0 ]:
					chat_store = st.checkbox( 'Store',
						value=bool( st.session_state.get( 'chat_store', True ) ),
						key='chat_store' )
				
				with p_row5[ 1 ]:
					chat_stream = st.checkbox( 'Stream',
						value=bool( st.session_state.get( 'chat_stream', False ) ),
						key='chat_stream' )
				
				_chat_supports_reasoning = (
						str( chat_model ).strip( ).lower( ).startswith( 'gpt-5' )
						or str( chat_model ).strip( ).lower( ).startswith( 'o' ))
				
				if _chat_supports_reasoning and chat_reasoning:
					chat_reasoning_effort = st.selectbox( 'Reasoning Effort',
						options=CHAT_REASONING_EFFORTS,
						index=CHAT_REASONING_EFFORTS.index(
							st.session_state.get( 'chat_reasoning_effort', 'low' ) ),
						key='chat_reasoning_effort' )
				else:
					chat_reasoning_effort = None
				
				chat_system = st.text_area( 'System',
					value=st.session_state.get( 'chat_system', '' ),
					height=120, key='chat_system' )
				
				if chat_web_search:
					chat_domains = st.text_area(
						'Preferred Search Domains (one per line or comma-separated)',
						value=st.session_state.get( 'chat_domains', '' ),
						height=90, key='chat_domains',
						help='Examples: openai.com, platform.openai.com, arxiv.org' )
				else:
					chat_domains = ''
				
				btn_row = st.columns( 2 )
				with btn_row[ 0 ]:
					chat_submit = st.button( 'Submit', key='chat_submit' )
				
				with btn_row[ 1 ]:
					st.button( 'Clear', key='chat_clear', on_click=_clear_chat_state )
			
			with col_right:
				chat_output = st.empty( )
			
			# -----------------------------
			# Submit Button
			# -----------------------------
			if chat_submit:
				try:
					if not str( chat_prompt or '' ).strip( ):
						raise ValueError( 'Prompt cannot be empty.' )
					
					if chat_json_mode:
						has_json_instruction = (
								'json' in str( chat_prompt or '' ).lower( )
								or 'json' in str( chat_system or '' ).lower( )
						)
						
						if not has_json_instruction:
							chat_system = (
									str( chat_system or '' ).strip( )
									+ '\n\nReturn valid JSON only.'
							).strip( )
					
					chat_domains_list = (
							_normalize_chat_domains( chat_domains )
							if chat_web_search
							else [ ]
					)
					
					fetcher = Chat( )
					params = {
							'model': chat_model,
							'temperature': float( chat_temperature ),
							'max_tokens': int( chat_max_tokens ),
							'top_p': float( chat_top_p ),
							'seed': int( chat_seed ) if int( chat_seed ) > 0 else None,
							'system': chat_system if str( chat_system ).strip( ) else None,
							'response_format': 'json' if chat_json_mode else None,
							'reasoning_effort': (
									chat_reasoning_effort
									if _chat_supports_reasoning
									   and chat_reasoning
									   and chat_reasoning_effort
									else None
							),
							'web_search': bool( chat_web_search ),
							'search_domains': chat_domains_list if chat_domains_list else None,
							'store': bool( chat_store ),
							'stream': bool( chat_stream ),
							'parallel_tool_calls': True,
							'tool_choice': 'auto',
					}
					
					params = {
							key: value
							for key, value in params.items( )
							if value is not None
					}
					
					result = _invoke_provider( fetcher, chat_prompt, params )
					_render_output( chat_output, result )
				
				except Exception as exc:
					st.error( str( exc ) )
		
		# -------- Groq
		with st.expander( label='Grok', expanded=False ):
			GROK_REASONING_EFFORTS = [
					'none',
					'low',
					'medium',
					'high'
			]
			
			def _clear_grok_state( ) -> None:
				"""Clear the grok state state.
				
				Purpose:
					Supports the Mappy Streamlit application by executing the clear grok state
					workflow. The function preserves the existing UI behavior, session-state
					interactions, dataframe handling, database access, and service integrations
					defined by the application code.
				"""
				st.session_state[ 'grok_clear_request' ] = True
			
			def _normalize_grok_domains( value: object ) -> list[ str ]:
				"""Normalize grok domains values.
				
				Purpose:
					Supports the Mappy Streamlit application by executing the normalize grok domains
					workflow. The function preserves the existing UI behavior, session-state
					interactions, dataframe handling, database access, and service integrations
					defined by the application code.
				
				Args:
					value: object value used by the `_normalize_grok_domains` workflow.
				
				Returns:
					list[str]: Result produced by the `_normalize_grok_domains` workflow.
				
				Raises:
					Exception: Propagates validation, UI, data, database, or provider errors
						raised by the existing implementation.
				"""
				text = str( value or '' ).strip( )
				
				if not text:
					return [ ]
				
				values: list[ str ] = [ ]
				entries = re.split( r'[\n,;]+', text )
				
				for entry in entries:
					domain = str( entry or '' ).strip( ).lower( )
					
					if not domain:
						continue
					
					domain = re.sub( r'^https?://', '', domain )
					domain = domain.split( '/' )[ 0 ]
					domain = re.sub( r':\d+$', '', domain )
					domain = domain.lstrip( '.' )
					
					if domain.startswith( 'www.' ):
						domain = domain[ 4: ]
					
					if not re.fullmatch( r'[a-z0-9][a-z0-9.-]*\.[a-z]{2,}', domain ):
						raise ValueError( f'Invalid Grok web-search domain: {domain}' )
					
					if domain not in values:
						values.append( domain )
				
				if len( values ) > 5:
					raise ValueError(
						'xAI web-search allowed domains are limited to five domains.'
					)
				
				return values
			
			def _normalize_grok_stop_lines( value: object ) -> list[ str ]:
				"""Normalize grok stop lines values.
				
				Purpose:
					Supports the Mappy Streamlit application by executing the normalize grok stop
					lines workflow. The function preserves the existing UI behavior, session-state
					interactions, dataframe handling, database access, and service integrations
					defined by the application code.
				
				Args:
					value: object value used by the `_normalize_grok_stop_lines` workflow.
				
				Returns:
					list[str]: Result produced by the `_normalize_grok_stop_lines` workflow.
				"""
				text = str( value or '' )
				
				if not text.strip( ):
					return [ ]
				
				return [
						line.strip( )
						for line in text.splitlines( )
						if line.strip( )
				]
			
			if 'grok_clear_request' not in st.session_state:
				st.session_state[ 'grok_clear_request' ] = False
			
			if 'groq_prompt_chat' not in st.session_state:
				st.session_state[ 'groq_prompt_chat' ] = ''
			
			if 'groq_system_chat' not in st.session_state:
				st.session_state[ 'groq_system_chat' ] = ''
			
			if 'groq_domains_chat' not in st.session_state:
				st.session_state[ 'groq_domains_chat' ] = ''
			
			if 'groq_stop_chat' not in st.session_state:
				st.session_state[ 'groq_stop_chat' ] = ''
			
			if 'groq_json_mode_chat' not in st.session_state:
				st.session_state[ 'groq_json_mode_chat' ] = False
			
			if 'groq_reasoning_chat' not in st.session_state:
				st.session_state[ 'groq_reasoning_chat' ] = False
			
			if 'groq_web_search_chat' not in st.session_state:
				st.session_state[ 'groq_web_search_chat' ] = False
			
			if 'groq_store_chat' not in st.session_state:
				st.session_state[ 'groq_store_chat' ] = True
			
			if 'groq_stream_chat' not in st.session_state:
				st.session_state[ 'groq_stream_chat' ] = False
			
			if 'groq_seed_chat' not in st.session_state:
				st.session_state[ 'groq_seed_chat' ] = 0
			
			if st.session_state.get( 'groq_reasoning_effort_chat',
					'low' ) not in GROK_REASONING_EFFORTS:
				st.session_state[ 'groq_reasoning_effort_chat' ] = 'low'
			
			if st.session_state.get( 'grok_clear_request', False ):
				st.session_state[ 'groq_prompt_chat' ] = ''
				st.session_state[ 'groq_system_chat' ] = ''
				st.session_state[ 'groq_domains_chat' ] = ''
				st.session_state[ 'groq_stop_chat' ] = ''
				st.session_state[ 'groq_json_mode_chat' ] = False
				st.session_state[ 'groq_reasoning_chat' ] = False
				st.session_state[ 'groq_web_search_chat' ] = False
				st.session_state[ 'groq_store_chat' ] = True
				st.session_state[ 'groq_stream_chat' ] = False
				st.session_state[ 'groq_seed_chat' ] = 0
				st.session_state[ 'groq_reasoning_effort_chat' ] = 'low'
				st.session_state[ 'grok_clear_request' ] = False
			
			col_left, col_right = st.columns( [ 1, 2 ], border=True )
			
			with col_left:
				groq_prompt = st.text_area(
					'Prompt',
					value=st.session_state.get( 'groq_prompt_chat', '' ),
					height=120,
					key='groq_prompt_chat',
				)
				
				p_row1 = st.columns( 2 )
				p_row2 = st.columns( 2 )
				p_row3 = st.columns( 2 )
				p_row4 = st.columns( 2 )
				p_row5 = st.columns( 2 )
				
				with p_row1[ 0 ]:
					_grok_models = (
							cfg.GROK_MODELS
							if hasattr( cfg, 'GROK_MODELS' ) and cfg.GROK_MODELS
							else [
									'grok-4.3',
									'grok-4.20',
									'grok-4.20-reasoning',
									'grok-4.20-multi-agent',
									'grok-4-1-fast',
									'grok-4-fast-reasoning',
									'grok-4',
									'grok-code-fast-1',
									'grok-3-mini'
							]
					)
					
					groq_model = _model_selector(
						key_prefix='groq',
						label='Model',
						options=_grok_models,
						default_model=(
								'grok-4.3'
								if 'grok-4.3' in _grok_models
								else _grok_models[ 0 ]
						),
					)
				
				with p_row1[ 1 ]:
					groq_temperature = st.slider(
						'Temperature',
						min_value=0.0,
						max_value=2.0,
						value=0.7,
						step=0.05,
						key='groq_temperature_chat',
					)
				
				with p_row2[ 0 ]:
					groq_max_tokens = st.number_input(
						'Max Tokens',
						min_value=1,
						max_value=32768,
						value=2048,
						step=1,
						key='groq_max_tokens_chat',
					)
				
				with p_row2[ 1 ]:
					groq_top_p = st.slider(
						'Top-P',
						min_value=0.0,
						max_value=1.0,
						value=1.0,
						step=0.01,
						key='groq_top_p_chat',
					)
				
				with p_row3[ 0 ]:
					groq_seed = st.number_input(
						'Seed',
						min_value=0,
						max_value=2_147_483_647,
						value=int( st.session_state.get( 'groq_seed_chat', 0 ) ),
						step=1,
						key='groq_seed_chat',
						help='Use 0 to omit the seed parameter.'
					)
				
				with p_row3[ 1 ]:
					groq_json_mode = st.checkbox(
						'JSON Mode',
						value=bool( st.session_state.get( 'groq_json_mode_chat', False ) ),
						key='groq_json_mode_chat',
						help='Adds JSON-only instructions through the current Grok wrapper.'
					)
				
				with p_row4[ 0 ]:
					groq_reasoning = st.checkbox(
						'Reasoning',
						value=bool( st.session_state.get( 'groq_reasoning_chat', False ) ),
						key='groq_reasoning_chat'
					)
				
				with p_row4[ 1 ]:
					groq_web_search = st.checkbox(
						'Web Search',
						value=bool( st.session_state.get( 'groq_web_search_chat', False ) ),
						key='groq_web_search_chat'
					)
				
				with p_row5[ 0 ]:
					groq_store = st.checkbox(
						'Store',
						value=bool( st.session_state.get( 'groq_store_chat', True ) ),
						key='groq_store_chat'
					)
				
				with p_row5[ 1 ]:
					groq_stream = st.checkbox(
						'Stream',
						value=bool( st.session_state.get( 'groq_stream_chat', False ) ),
						key='groq_stream_chat'
					)
				
				_groq_model_name = str( groq_model or '' ).strip( ).lower( )
				_groq_is_reasoning_model = (
						'reasoning' in _groq_model_name
						or _groq_model_name.startswith( 'grok-4' )
						or _groq_model_name.startswith( 'grok-4.3' )
						or _groq_model_name.startswith( 'grok-4.20' )
				)
				
				_groq_supports_reasoning_effort = (
						_groq_model_name == 'grok-4.3'
						or _groq_model_name == 'grok-4.20-multi-agent'
				)
				
				if _groq_supports_reasoning_effort and groq_reasoning:
					groq_reasoning_effort = st.selectbox(
						'Reasoning Effort',
						options=GROK_REASONING_EFFORTS,
						index=GROK_REASONING_EFFORTS.index(
							st.session_state.get( 'groq_reasoning_effort_chat', 'low' )
						),
						key='groq_reasoning_effort_chat'
					)
				else:
					groq_reasoning_effort = None
				
				groq_system = st.text_area(
					'System',
					value=st.session_state.get( 'groq_system_chat', '' ),
					height=120,
					key='groq_system_chat'
				)
				
				if groq_web_search:
					groq_domains = st.text_area(
						'Allowed Search Domains',
						value=st.session_state.get( 'groq_domains_chat', '' ),
						height=90,
						key='groq_domains_chat',
						help='Optional. xAI allows up to five allowed domains.'
					)
				else:
					groq_domains = ''
				
				groq_stop = st.text_area(
					'Stop Sequences',
					value=st.session_state.get( 'groq_stop_chat', '' ),
					height=80,
					key='groq_stop_chat',
					disabled=_groq_is_reasoning_model,
					help='One stop sequence per line. Disabled for reasoning models.'
				)
				
				btn_row = st.columns( 2 )
				
				with btn_row[ 0 ]:
					groq_submit = st.button(
						'Submit',
						key='groq_submit'
					)
				
				with btn_row[ 1 ]:
					st.button(
						'Clear',
						key='groq_clear',
						on_click=_clear_grok_state
					)
			
			with col_right:
				groq_output = st.empty( )
			
			# -----------------------------
			# Submit Button
			# -----------------------------
			if groq_submit:
				try:
					if not str( groq_prompt or '' ).strip( ):
						raise ValueError( 'Prompt cannot be empty.' )
					
					if groq_json_mode:
						has_json_instruction = (
								'json' in str( groq_prompt or '' ).lower( )
								or 'json' in str( groq_system or '' ).lower( )
						)
						
						if not has_json_instruction:
							groq_system = (
									str( groq_system or '' ).strip( )
									+ '\n\nReturn valid JSON only.'
							).strip( )
					
					groq_domains_list = (
							_normalize_grok_domains( groq_domains )
							if groq_web_search
							else [ ]
					)
					
					stop_lines = _normalize_grok_stop_lines( groq_stop )
					
					if stop_lines and _groq_is_reasoning_model:
						stop_lines = [ ]
					
					fetcher = Grok( )
					params = {
							'model': groq_model,
							'temperature': float( groq_temperature ),
							'max_tokens': int( groq_max_tokens ),
							'top_p': float( groq_top_p ),
							'seed': int( groq_seed ) if int( groq_seed ) > 0 else None,
							'system': groq_system if str( groq_system ).strip( ) else None,
							'response_format': 'json' if groq_json_mode else None,
							'reasoning_effort': (
									groq_reasoning_effort
									if _groq_supports_reasoning_effort
									   and groq_reasoning
									   and groq_reasoning_effort
									else None
							),
							'web_search': bool( groq_web_search ),
							'search_domains': groq_domains_list if groq_domains_list else None,
							'stop': stop_lines if stop_lines else None,
							'stream': bool( groq_stream ),
							'store': bool( groq_store ),
							'parallel_tool_calls': True,
							'tool_choice': 'auto',
					}
					
					params = {
							key: value
							for key, value in params.items( )
							if value is not None
					}
					result = _invoke_provider( fetcher, groq_prompt, params )
					_render_output( groq_output, result )
				
				except Exception as exc:
					st.error( str( exc ) )
		
		# -------- CLAUDE
		with st.expander( label='Claude', expanded=False ):
			def _clear_claude_state( ) -> None:
				"""Clear the claude state state.
				
				Purpose:
					Supports the Mappy Streamlit application by executing the clear claude state
					workflow. The function preserves the existing UI behavior, session-state
					interactions, dataframe handling, database access, and service integrations
					defined by the application code.
				"""
				st.session_state[ 'claude_clear_request' ] = True
			
			def _normalize_claude_domains( value: object ) -> list[ str ]:
				"""Normalize claude domains values.
				
				Purpose:
					Supports the Mappy Streamlit application by executing the normalize claude domains
					workflow. The function preserves the existing UI behavior, session-state
					interactions, dataframe handling, database access, and service integrations
					defined by the application code.
				
				Args:
					value: object value used by the `_normalize_claude_domains` workflow.
				
				Returns:
					list[str]: Result produced by the `_normalize_claude_domains` workflow.
				
				Raises:
					Exception: Propagates validation, UI, data, database, or provider errors
						raised by the existing implementation.
				"""
				text = str( value or '' ).strip( )
				
				if not text:
					return [ ]
				
				values: list[ str ] = [ ]
				entries = re.split( r'[\n,;]+', text )
				
				for entry in entries:
					raw_value = str( entry or '' ).strip( ).lower( )
					
					if not raw_value:
						continue
					
					if not raw_value.startswith( 'http://' ) and not raw_value.startswith(
							'https://' ):
						raw_value = f'https://{raw_value}'
					
					parsed = urlparse( raw_value )
					domain = (parsed.netloc or parsed.path or '').strip( ).lower( )
					domain = re.sub( r':\d+$', '', domain )
					domain = domain.lstrip( '.' )
					
					if domain.startswith( 'www.' ):
						domain = domain[ 4: ]
					
					if not re.fullmatch( r'[a-z0-9][a-z0-9.-]*\.[a-z]{2,}', domain ):
						raise ValueError( f'Invalid Claude web-search domain: {domain}' )
					
					if domain not in values:
						values.append( domain )
				
				return values
			
			def _normalize_claude_stop_lines( value: object ) -> list[ str ]:
				"""Normalize claude stop lines values.
				
				Purpose:
					Supports the Mappy Streamlit application by executing the normalize claude stop
					lines workflow. The function preserves the existing UI behavior, session-state
					interactions, dataframe handling, database access, and service integrations
					defined by the application code.
				
				Args:
					value: object value used by the `_normalize_claude_stop_lines` workflow.
				
				Returns:
					list[str]: Result produced by the `_normalize_claude_stop_lines` workflow.
				"""
				text = str( value or '' )
				
				if not text.strip( ):
					return [ ]
				
				return [
						line.strip( )
						for line in text.splitlines( )
						if line.strip( )
				]
			
			if 'claude_clear_request' not in st.session_state:
				st.session_state[ 'claude_clear_request' ] = False
			
			if 'claude_prompt_chat' not in st.session_state:
				st.session_state[ 'claude_prompt_chat' ] = ''
			
			if 'claude_system_chat' not in st.session_state:
				st.session_state[ 'claude_system_chat' ] = ''
			
			if 'claude_stop_chat' not in st.session_state:
				st.session_state[ 'claude_stop_chat' ] = ''
			
			if 'claude_domains_chat' not in st.session_state:
				st.session_state[ 'claude_domains_chat' ] = ''
			
			if 'claude_blocked_domains_chat' not in st.session_state:
				st.session_state[ 'claude_blocked_domains_chat' ] = ''
			
			if 'claude_thinking_chat' not in st.session_state:
				st.session_state[ 'claude_thinking_chat' ] = False
			
			if 'claude_web_search_chat' not in st.session_state:
				st.session_state[ 'claude_web_search_chat' ] = False
			
			if 'claude_thinking_budget_chat' not in st.session_state:
				st.session_state[ 'claude_thinking_budget_chat' ] = 1024
			
			if st.session_state.get( 'claude_clear_request', False ):
				st.session_state[ 'claude_prompt_chat' ] = ''
				st.session_state[ 'claude_system_chat' ] = ''
				st.session_state[ 'claude_stop_chat' ] = ''
				st.session_state[ 'claude_domains_chat' ] = ''
				st.session_state[ 'claude_blocked_domains_chat' ] = ''
				st.session_state[ 'claude_thinking_chat' ] = False
				st.session_state[ 'claude_web_search_chat' ] = False
				st.session_state[ 'claude_thinking_budget_chat' ] = 1024
				st.session_state[ 'claude_clear_request' ] = False
			
			col_left, col_right = st.columns( [ 1, 2 ], border=True )
			
			with col_left:
				claude_prompt = st.text_area(
					'Prompt',
					value=st.session_state.get( 'claude_prompt_chat', '' ),
					height=140,
					key='claude_prompt_chat',
				)
				
				# -----------------------------
				# Model / Output Controls
				# -----------------------------
				model_row = st.columns( [ 0.55, 0.45 ] )
				
				with model_row[ 0 ]:
					_claude_models = (
							cfg.CLAUDE_MODELS
							if hasattr( cfg, 'CLAUDE_MODELS' ) and cfg.CLAUDE_MODELS
							else [
									'claude-opus-4-6',
									'claude-sonnet-4-6',
									'claude-haiku-4-5',
									'claude-3-5-haiku-latest',
							]
					)
					
					claude_model = _model_selector(
						key_prefix='claude',
						label='Model',
						options=_claude_models,
						default_model=(
								'claude-sonnet-4-6'
								if 'claude-sonnet-4-6' in _claude_models
								else _claude_models[ 0 ]
						),
					)
				
				with model_row[ 1 ]:
					claude_max_tokens = st.number_input(
						'Max Tokens',
						min_value=1,
						max_value=65536,
						value=2048,
						step=1,
						key='claude_max_tokens_chat',
					)
				
				# -----------------------------
				# Sampling Controls
				# -----------------------------
				sampling_row = st.columns( 3 )
				
				with sampling_row[ 0 ]:
					claude_temperature = st.slider(
						'Temperature',
						min_value=0.0,
						max_value=1.0,
						value=0.7,
						step=0.05,
						key='claude_temperature_chat',
					)
				
				with sampling_row[ 1 ]:
					claude_top_p = st.slider(
						'Top-P',
						min_value=0.0,
						max_value=1.0,
						value=1.0,
						step=0.01,
						key='claude_top_p_chat',
					)
				
				with sampling_row[ 2 ]:
					claude_top_k = st.number_input(
						'Top-k',
						min_value=0,
						max_value=500,
						value=0,
						step=1,
						key='claude_top_k_chat',
					)
				
				# -----------------------------
				# Feature Toggles
				# -----------------------------
				option_row = st.columns( 2 )
				
				with option_row[ 0 ]:
					claude_thinking = st.checkbox(
						'Reasoning',
						value=bool( st.session_state.get( 'claude_thinking_chat', False ) ),
						key='claude_thinking_chat',
						help='Anthropic exposes this as extended thinking with a token budget.',
					)
				
				with option_row[ 1 ]:
					claude_web_search = st.checkbox(
						'Web Search',
						value=bool( st.session_state.get( 'claude_web_search_chat', False ) ),
						key='claude_web_search_chat',
					)
				
				# -----------------------------
				# Reasoning Budget
				# -----------------------------
				if claude_thinking:
					claude_thinking_budget = st.number_input(
						'Thinking Budget',
						min_value=1024,
						max_value=max( 1024, int( claude_max_tokens ) - 1 ),
						value=min(
							int(
								st.session_state.get(
									'claude_thinking_budget_chat',
									1024
								)
							),
							max( 1024, int( claude_max_tokens ) - 1 )
						),
						step=1024,
						key='claude_thinking_budget_chat',
						help='Must be less than Max Tokens.'
					)
				else:
					claude_thinking_budget = None
				
				# -----------------------------
				# Instruction Controls
				# -----------------------------
				claude_system = st.text_area(
					'System',
					value=st.session_state.get( 'claude_system_chat', '' ),
					height=110,
					key='claude_system_chat',
				)
				
				claude_stop = st.text_area(
					'Stop Sequences (one per line)',
					value=st.session_state.get( 'claude_stop_chat', '' ),
					height=80,
					key='claude_stop_chat',
				)
				
				# -----------------------------
				# Web Search Controls
				# -----------------------------
				if claude_web_search:
					search_row = st.columns( 2 )
					
					with search_row[ 0 ]:
						claude_domains = st.text_area(
							'Allowed Search Domains',
							value=st.session_state.get( 'claude_domains_chat', '' ),
							height=90,
							key='claude_domains_chat',
							help='Optional allowlist, one domain per line or comma-separated.'
						)
					
					with search_row[ 1 ]:
						claude_blocked_domains = st.text_area(
							'Blocked Search Domains',
							value=st.session_state.get( 'claude_blocked_domains_chat', '' ),
							height=90,
							key='claude_blocked_domains_chat',
							help='Optional blocklist, one domain per line or comma-separated.'
						)
				else:
					claude_domains = ''
					claude_blocked_domains = ''
				
				# -----------------------------
				# Action Controls
				# -----------------------------
				btn_row = st.columns( 2 )
				
				with btn_row[ 0 ]:
					claude_submit = st.button(
						'Submit',
						key='claude_submit_chat',
						use_container_width=True
					)
				
				with btn_row[ 1 ]:
					st.button(
						'Clear',
						key='claude_clear_chat',
						on_click=_clear_claude_state,
						use_container_width=True
					)
		
		# -------- GEMINI
		with st.expander( label='Gemini', expanded=False ):
			GEMINI_THINKING_LEVELS = [
					'minimal',
					'low',
					'medium',
					'high'
			]
			
			def _clear_gemini_state( ) -> None:
				"""Clear the gemini state state.
				
				Purpose:
					Supports the Mappy Streamlit application by executing the clear gemini state
					workflow. The function preserves the existing UI behavior, session-state
					interactions, dataframe handling, database access, and service integrations
					defined by the application code.
				"""
				st.session_state[ 'gemini_clear_request' ] = True
			
			def _normalize_gemini_domains( value: object ) -> list[ str ]:
				"""Normalize gemini domains values.
				
				Purpose:
					Supports the Mappy Streamlit application by executing the normalize gemini domains
					workflow. The function preserves the existing UI behavior, session-state
					interactions, dataframe handling, database access, and service integrations
					defined by the application code.
				
				Args:
					value: object value used by the `_normalize_gemini_domains` workflow.
				
				Returns:
					list[str]: Result produced by the `_normalize_gemini_domains` workflow.
				
				Raises:
					Exception: Propagates validation, UI, data, database, or provider errors
						raised by the existing implementation.
				"""
				text = str( value or '' ).strip( )
				
				if not text:
					return [ ]
				
				values: list[ str ] = [ ]
				entries = re.split( r'[\n,;]+', text )
				
				for entry in entries:
					raw_value = str( entry or '' ).strip( ).lower( )
					
					if not raw_value:
						continue
					
					if not raw_value.startswith( 'http://' ) and not raw_value.startswith(
							'https://' ):
						raw_value = f'https://{raw_value}'
					
					parsed = urlparse( raw_value )
					domain = (parsed.netloc or parsed.path or '').strip( ).lower( )
					domain = re.sub( r':\d+$', '', domain )
					domain = domain.lstrip( '.' )
					
					if domain.startswith( 'www.' ):
						domain = domain[ 4: ]
					
					if not re.fullmatch( r'[a-z0-9][a-z0-9.-]*\.[a-z]{2,}', domain ):
						raise ValueError( f'Invalid Gemini grounding domain: {domain}' )
					
					if domain not in values:
						values.append( domain )
				
				return values
			
			def _normalize_gemini_stop_lines( value: object ) -> list[ str ]:
				"""Normalize gemini stop lines values.
				
				Purpose:
					Supports the Mappy Streamlit application by executing the normalize gemini stop
					lines workflow. The function preserves the existing UI behavior, session-state
					interactions, dataframe handling, database access, and service integrations
					defined by the application code.
				
				Args:
					value: object value used by the `_normalize_gemini_stop_lines` workflow.
				
				Returns:
					list[str]: Result produced by the `_normalize_gemini_stop_lines` workflow.
				"""
				text = str( value or '' )
				
				if not text.strip( ):
					return [ ]
				
				return [
						line.strip( )
						for line in text.splitlines( )
						if line.strip( )
				]
			
			if 'gemini_clear_request' not in st.session_state:
				st.session_state[ 'gemini_clear_request' ] = False
			
			if 'gemini_prompt_chat' not in st.session_state:
				st.session_state[ 'gemini_prompt_chat' ] = ''
			
			if 'gemini_system_chat' not in st.session_state:
				st.session_state[ 'gemini_system_chat' ] = ''
			
			if 'gemini_domains_chat' not in st.session_state:
				st.session_state[ 'gemini_domains_chat' ] = ''
			
			if 'gemini_stop_chat' not in st.session_state:
				st.session_state[ 'gemini_stop_chat' ] = ''
			
			if 'gemini_json_mode_chat' not in st.session_state:
				st.session_state[ 'gemini_json_mode_chat' ] = False
			
			if 'gemini_grounding_chat' not in st.session_state:
				st.session_state[ 'gemini_grounding_chat' ] = False
			
			if 'gemini_reasoning_chat' not in st.session_state:
				st.session_state[ 'gemini_reasoning_chat' ] = False
			
			if 'gemini_include_thoughts_chat' not in st.session_state:
				st.session_state[ 'gemini_include_thoughts_chat' ] = False
			
			if 'gemini_seed_chat' not in st.session_state:
				st.session_state[ 'gemini_seed_chat' ] = 0
			
			if st.session_state.get( 'gemini_thinking_level_chat',
					'low' ) not in GEMINI_THINKING_LEVELS:
				st.session_state[ 'gemini_thinking_level_chat' ] = 'low'
			
			if st.session_state.get( 'gemini_clear_request', False ):
				st.session_state[ 'gemini_prompt_chat' ] = ''
				st.session_state[ 'gemini_system_chat' ] = ''
				st.session_state[ 'gemini_domains_chat' ] = ''
				st.session_state[ 'gemini_stop_chat' ] = ''
				st.session_state[ 'gemini_json_mode_chat' ] = False
				st.session_state[ 'gemini_grounding_chat' ] = False
				st.session_state[ 'gemini_reasoning_chat' ] = False
				st.session_state[ 'gemini_include_thoughts_chat' ] = False
				st.session_state[ 'gemini_seed_chat' ] = 0
				st.session_state[ 'gemini_thinking_level_chat' ] = 'low'
				st.session_state[ 'gemini_clear_request' ] = False
			
			col_left, col_right = st.columns( [ 1, 2 ], border=True )
			
			with col_left:
				gemini_prompt = st.text_area(
					'Prompt',
					value=st.session_state.get( 'gemini_prompt_chat', '' ),
					height=160,
					key='gemini_prompt_chat',
				)
				
				p_row1 = st.columns( 2 )
				p_row2 = st.columns( 2 )
				p_row3 = st.columns( 2 )
				p_row4 = st.columns( 2 )
				p_row5 = st.columns( 2 )
				
				with p_row1[ 0 ]:
					_gemini_models = (
							cfg.GEMINI_MODELS
							if hasattr( cfg, 'GEMINI_MODELS' ) and cfg.GEMINI_MODELS
							else [
									'gemini-3-flash-preview',
									'gemini-2.5-pro',
									'gemini-2.5-flash',
									'gemini-2.5-flash-lite'
							]
					)
					
					gemini_model = _model_selector(
						key_prefix='gemini',
						label='Model',
						options=_gemini_models,
						default_model=(
								'gemini-2.5-flash'
								if 'gemini-2.5-flash' in _gemini_models
								else _gemini_models[ 0 ]
						),
					)
				
				with p_row1[ 1 ]:
					gemini_temperature = st.slider(
						'Temperature',
						min_value=0.0,
						max_value=2.0,
						value=0.7,
						step=0.05,
						key='gemini_temperature_chat',
					)
				
				with p_row2[ 0 ]:
					gemini_max_tokens = st.number_input(
						'Max Tokens',
						min_value=1,
						max_value=32768,
						value=2048,
						step=1,
						key='gemini_max_tokens_chat',
					)
				
				with p_row2[ 1 ]:
					gemini_top_p = st.slider(
						'Top-p',
						min_value=0.0,
						max_value=1.0,
						value=1.0,
						step=0.01,
						key='gemini_top_p_chat',
					)
				
				with p_row3[ 0 ]:
					gemini_top_k = st.number_input(
						'Top-k',
						min_value=0,
						max_value=500,
						value=0,
						step=1,
						key='gemini_top_k_chat',
					)
				
				with p_row3[ 1 ]:
					gemini_candidate_count = st.number_input(
						'Candidates',
						min_value=1,
						max_value=8,
						value=1,
						step=1,
						key='gemini_candidate_count_chat',
					)
				
				with p_row4[ 0 ]:
					gemini_seed = st.number_input(
						'Seed',
						min_value=0,
						max_value=2_147_483_647,
						value=int( st.session_state.get( 'gemini_seed_chat', 0 ) ),
						step=1,
						key='gemini_seed_chat',
						help='Use 0 to omit the seed parameter.'
					)
				
				with p_row4[ 1 ]:
					gemini_json_mode = st.checkbox(
						'JSON Mode',
						value=bool( st.session_state.get( 'gemini_json_mode_chat', False ) ),
						key='gemini_json_mode_chat',
						help='Requests JSON output through the current Gemini wrapper.'
					)
				
				with p_row5[ 0 ]:
					gemini_grounding = st.checkbox(
						'Grounding',
						value=bool( st.session_state.get( 'gemini_grounding_chat', False ) ),
						key='gemini_grounding_chat',
						help='Enable Google Search grounding for supported Gemini models.'
					)
				
				with p_row5[ 1 ]:
					gemini_reasoning = st.checkbox(
						'Reasoning',
						value=bool( st.session_state.get( 'gemini_reasoning_chat', False ) ),
						key='gemini_reasoning_chat',
						help='Uses Gemini thinking configuration where supported.'
					)
				
				_gemini_model_name = str( gemini_model or '' ).strip( ).lower( )
				_gemini_supports_thinking_level = _gemini_model_name.startswith( 'gemini-3' )
				_gemini_supports_thinking_budget = _gemini_model_name.startswith( 'gemini-2.5' )
				
				if _gemini_supports_thinking_level and gemini_reasoning:
					r_row = st.columns( 2 )
					
					with r_row[ 0 ]:
						gemini_thinking_level = st.selectbox(
							'Thinking Level',
							options=GEMINI_THINKING_LEVELS,
							index=GEMINI_THINKING_LEVELS.index(
								st.session_state.get( 'gemini_thinking_level_chat', 'low' )
							),
							key='gemini_thinking_level_chat',
						)
					
					with r_row[ 1 ]:
						gemini_include_thoughts = st.checkbox(
							'Include Thoughts',
							value=bool(
								st.session_state.get(
									'gemini_include_thoughts_chat',
									False
								)
							),
							key='gemini_include_thoughts_chat',
						)
				else:
					gemini_thinking_level = None
					gemini_include_thoughts = False
				
				if gemini_reasoning and _gemini_supports_thinking_budget:
					st.caption(
						'Gemini 2.5 models use thinking_budget, but the current Gemini '
						'generator only exposes thinking_level. This UI preserves the current '
						'wrapper contract until the Gemini class is updated.'
					)
				
				if gemini_reasoning and not (
						_gemini_supports_thinking_level or _gemini_supports_thinking_budget
				):
					st.caption(
						'Reasoning controls are only sent for Gemini 3 model names under '
						'the current wrapper contract.'
					)
				
				gemini_stop = st.text_area(
					'Stop Sequences (one per line)',
					value=st.session_state.get( 'gemini_stop_chat', '' ),
					height=80,
					key='gemini_stop_chat',
				)
				
				gemini_system = st.text_area(
					'System',
					value=st.session_state.get( 'gemini_system_chat', '' ),
					height=110,
					key='gemini_system_chat',
				)
				
				if gemini_grounding:
					gemini_domains = st.text_area(
						'Preferred Search Domains (one per line or comma-separated)',
						value=st.session_state.get( 'gemini_domains_chat', '' ),
						height=90,
						key='gemini_domains_chat',
						help='Used as preferred source guidance for grounded Gemini responses.'
					)
				else:
					gemini_domains = ''
				
				btn_row = st.columns( 2 )
				
				with btn_row[ 0 ]:
					gemini_submit = st.button(
						'Submit',
						key='gemini_submit_chat'
					)
				
				with btn_row[ 1 ]:
					st.button(
						'Clear',
						key='gemini_clear_chat',
						on_click=_clear_gemini_state
					)
			
			with col_right:
				gemini_output = st.empty( )
			
			# -----------------------------
			# Submit Button
			# -----------------------------
			if gemini_submit:
				try:
					if not str( gemini_prompt or '' ).strip( ):
						raise ValueError( 'Prompt cannot be empty.' )
					
					if gemini_json_mode:
						has_json_instruction = (
								'json' in str( gemini_prompt or '' ).lower( )
								or 'json' in str( gemini_system or '' ).lower( )
						)
						
						if not has_json_instruction:
							gemini_system = (
									str( gemini_system or '' ).strip( )
									+ '\n\nReturn valid JSON only.'
							).strip( )
					
					gemini_domains_list = (
							_normalize_gemini_domains( gemini_domains )
							if gemini_grounding
							else [ ]
					)
					
					stop_lines = _normalize_gemini_stop_lines( gemini_stop )
					
					fetcher = Gemini( )
					params = {
							'model': gemini_model,
							'temperature': float( gemini_temperature ),
							'max_tokens': int( gemini_max_tokens ),
							'top_p': float( gemini_top_p ),
							'top_k': int( gemini_top_k ) if int( gemini_top_k ) > 0 else None,
							'candidate_count': int( gemini_candidate_count ),
							'seed': int( gemini_seed ) if int( gemini_seed ) > 0 else None,
							'system': (
									gemini_system
									if str( gemini_system or '' ).strip( )
									else None
							),
							'response_format': 'json' if gemini_json_mode else None,
							'stop_sequences': stop_lines if stop_lines else None,
							'grounding': bool( gemini_grounding ),
							'search_domains': (
									gemini_domains_list
									if gemini_domains_list
									else None
							),
							'reasoning': bool(
								gemini_reasoning
								and _gemini_supports_thinking_level
							),
							'thinking_level': (
									gemini_thinking_level
									if _gemini_supports_thinking_level
									   and gemini_reasoning
									else None
							),
							'include_thoughts': bool(
								gemini_include_thoughts
							) if _gemini_supports_thinking_level and gemini_reasoning else False,
					}
					
					params = {
							key: value
							for key, value in params.items( )
							if value is not None
					}
					
					result = _invoke_provider( fetcher, gemini_prompt, params )
					_render_output( gemini_output, result )
				
				except Exception as exc:
					st.error( str( exc ) )
		
		# -------- Mistral
		with st.expander( label='Mistral', expanded=False ):
			def _clear_mistral_state( ) -> None:
				"""Clear the mistral state state.
				
				Purpose:
					Supports the Mappy Streamlit application by executing the clear mistral state
					workflow. The function preserves the existing UI behavior, session-state
					interactions, dataframe handling, database access, and service integrations
					defined by the application code.
				"""
				st.session_state[ 'mistral_clear_request' ] = True
			
			if 'mistral_clear_request' not in st.session_state:
				st.session_state[ 'mistral_clear_request' ] = False
			
			if 'mistral_prompt_chat' not in st.session_state:
				st.session_state[ 'mistral_prompt_chat' ] = ''
			
			if 'mistral_system_chat' not in st.session_state:
				st.session_state[ 'mistral_system_chat' ] = ''
			
			if 'mistral_safe_mode_chat' not in st.session_state:
				st.session_state[ 'mistral_safe_mode_chat' ] = False
			
			if 'mistral_seed_chat' not in st.session_state:
				st.session_state[ 'mistral_seed_chat' ] = 0
			
			if st.session_state.get( 'mistral_clear_request', False ):
				st.session_state[ 'mistral_prompt_chat' ] = ''
				st.session_state[ 'mistral_system_chat' ] = ''
				st.session_state[ 'mistral_safe_mode_chat' ] = False
				st.session_state[ 'mistral_seed_chat' ] = 0
				st.session_state[ 'mistral_clear_request' ] = False
			
			col_left, col_right = st.columns( [ 1, 2 ], border=True )
			
			with col_left:
				mistral_prompt = st.text_area(
					'Prompt',
					value=st.session_state.get( 'mistral_prompt_chat', '' ),
					height=120,
					key='mistral_prompt_chat'
				)
				
				p_row1 = st.columns( 2 )
				p_row2 = st.columns( 2 )
				p_row3 = st.columns( 2 )
				
				with p_row1[ 0 ]:
					_mistral_models = (
							cfg.MISTRAL_MODELS
							if hasattr( cfg, 'MISTRAL_MODELS' ) and cfg.MISTRAL_MODELS
							else [
									'mistral-large-latest',
									'mistral-medium-latest',
									'mistral-small-latest',
									'open-mistral-7b',
									'Custom...',
							]
					)
					
					mistral_model = _model_selector(
						key_prefix='mistral',
						label='Model',
						options=_mistral_models,
						default_model=(
								'mistral-large-latest'
								if 'mistral-large-latest' in _mistral_models
								else _mistral_models[ 0 ]
						),
					)
				
				with p_row1[ 1 ]:
					mistral_temperature = st.slider(
						'Temperature',
						min_value=0.0,
						max_value=2.0,
						value=0.7,
						step=0.05,
						key='mistral_temperature_chat',
						help='Mistral recommends tuning temperature or top-p, not both.'
					)
				
				with p_row2[ 0 ]:
					mistral_max_tokens = st.number_input(
						'Max Tokens',
						min_value=1,
						max_value=32768,
						value=1024,
						step=1,
						key='mistral_max_tokens_chat',
					)
				
				with p_row2[ 1 ]:
					mistral_top_p = st.slider(
						'Top-p',
						min_value=0.0,
						max_value=1.0,
						value=1.0,
						step=0.01,
						key='mistral_top_p_chat',
						help='Mistral recommends tuning temperature or top-p, not both.'
					)
				
				with p_row3[ 0 ]:
					mistral_seed = st.number_input(
						'Seed',
						min_value=0,
						max_value=2_147_483_647,
						value=int( st.session_state.get( 'mistral_seed_chat', 0 ) ),
						step=1,
						key='mistral_seed_chat',
						help='Use 0 to omit random_seed.'
					)
				
				with p_row3[ 1 ]:
					mistral_safe_mode = st.checkbox(
						'Safe Mode',
						value=bool(
							st.session_state.get(
								'mistral_safe_mode_chat',
								False
							)
						),
						key='mistral_safe_mode_chat',
						help='Maps to Mistral safe_prompt in the current wrapper.'
					)
				
				mistral_system = st.text_area(
					'System',
					value=st.session_state.get( 'mistral_system_chat', '' ),
					height=100,
					key='mistral_system_chat',
				)
				
				st.caption(
					'The current Mistral wrapper supports text output only. JSON mode and '
					'stop sequences require a later complete Mistral class replacement.'
				)
				
				btn_row = st.columns( 2 )
				
				with btn_row[ 0 ]:
					mistral_submit = st.button(
						'Submit',
						key='mistral_submit_chat'
					)
				
				with btn_row[ 1 ]:
					st.button(
						'Clear',
						key='mistral_clear_chat',
						on_click=_clear_mistral_state
					)
			
			with col_right:
				mistral_output = st.empty( )
			
			if mistral_submit:
				try:
					if not str( mistral_prompt or '' ).strip( ):
						raise ValueError( 'Prompt cannot be empty.' )
					
					if float( mistral_temperature ) > 0.0 and float( mistral_top_p ) < 1.0:
						st.warning(
							'Mistral recommends adjusting either temperature or top-p, '
							'but not both, for most use cases.'
						)
					
					fetcher = Mistral( )
					params = {
							'model': mistral_model,
							'temperature': float( mistral_temperature ),
							'max_tokens': int( mistral_max_tokens ),
							'top_p': float( mistral_top_p ),
							'seed': int( mistral_seed ) if int( mistral_seed ) > 0 else None,
							'safe_mode': bool( mistral_safe_mode ),
							'system': (
									mistral_system
									if str( mistral_system or '' ).strip( )
									else None
							),
					}
					
					params = {
							key: value
							for key, value in params.items( )
							if value is not None
					}
					
					result = _invoke_provider( fetcher, mistral_prompt, params )
					_render_output( mistral_output, result )
				
				except Exception as exc:
					st.error( str( exc ) )

# ==============================================================================
# DATA UPLOAD MODE
# ==============================================================================
elif mode == 'Data Upload':
	from processing import render_document_processing

	left, center, right = st.columns( [ 0.10, 0.8, 0.10 ] )
	with center:
		st.subheader( 'Excel / CSV' )
		st.divider( )

		uploaded = st.file_uploader( 'Upload CSV or XLSX', type=[ 'csv', 'xlsx' ],
			key='data_upload_file' )

		enrichment_mode = st.selectbox( 'Enrichment Mode',
			options=[ 'City / State / Country', 'Address Column' ],
			key='data_upload_enrichment_mode' )

		if enrichment_mode == 'City / State / Country':
			city_col = st.text_input( 'City Column', value='City', key='data_upload_city_col' )
			state_col = st.text_input( 'State Column', value='State', key='data_upload_state_col' )
			country_col = st.text_input( 'Country Column', value='Country',
				key='data_upload_country_col' )
			address_col = ''

		else:
			address_col = st.text_input( 'Address Column', value='Address',
				key='data_upload_address_col' )
			country_col = st.text_input(
				'Country Bias Column',
				value='Country',
				help='Optional. Leave as-is if the uploaded file has no country-bias column.',
				key='data_upload_address_country_col' )
			city_col = ''
			state_col = ''

		sheet_name = st.text_input( 'Worksheet', value='Sheet1',
			help='Used for Excel files. For CSV files this value is ignored.',
			key='data_upload_sheet_name' )

		if uploaded:
			input_path = f'_input_{uploaded.name}'
			output_path = f'_output_{uploaded.name}'

			with open( input_path, 'wb' ) as f:
				f.write( uploaded.read( ) )

			if st.button( 'Enrich File', key='data_upload_enrich' ):
				try:
					excel = Excel( api=cfg.GOOGLE_API_KEY, cache=cache )
					sheet_value = sheet_name if input_path.lower( ).endswith( '.xlsx' ) else None

					if enrichment_mode == 'City / State / Country':
						excel.enrich( inpath=input_path, outpath=output_path, city=city_col,
							state=state_col, cntry=country_col,
							sheet=sheet_value )

					else:
						excel.enrich_from_address( inpath=input_path, outpath=output_path,
							address=address_col, sheet=sheet_value,
							cntry=country_col )

					if output_path.lower( ).endswith( '.csv' ):
						df_output = pd.read_csv( output_path )
					else:
						df_output = pd.read_excel( output_path )

					st.data_editor( df_output, key='data_upload_enriched_preview',
						use_container_width=True, disabled=True )

					with open( output_path, 'rb' ) as f:
						output_bytes = f.read( )

					st.download_button(
						'Download Enriched File',
						data=output_bytes,
						file_name=Path( output_path ).name,
						key='data_upload_download' )

				except Exception as e:
					st.error( f'Enrichment failed: {e}' )

				finally:
					try:
						if os.path.exists( input_path ):
							os.remove( input_path )
						if os.path.exists( output_path ):
							os.remove( output_path )
					except Exception:
						pass

	render_document_processing( cache )

# ==============================================================================
# DATA MANAGEMENT MODE
# ==============================================================================
elif mode == 'Data Management':
	left, center, right = st.columns( [ 0.10, 0.8, 0.10 ] )
	with center:
		st.subheader( 'Data Management' )
		tabs = st.tabs( [ 'Import', 'Browse', 'CRUD', 'Explore', 'Filter',
		                  'Aggregate', 'Visualize', 'Geocode', 'Admin', 'SQL' ] )
		
		tables = list_tables( )
		if not tables:
			st.info( 'No tables available.' )
		
		# -------------- UPLOAD TAB
		with tabs[ 0 ]:
			upl_c1, upl_c2 = st.columns( [ 0.70, 0.30 ] )
			with upl_c1:
				uploaded_file = st.file_uploader( 'Upload Excel File', type=[ 'xlsx' ] )
			with upl_c2:
				overwrite = st.checkbox( 'Overwrite existing tables', value=True )
			
			if uploaded_file:
				try:
					sheets = pd.read_excel( uploaded_file, sheet_name=None )
					with create_connection( ) as conn:
						conn.execute( 'BEGIN' )
						for sheet_name, df in sheets.items( ):
							table_name = create_identifier( sheet_name )
							if overwrite:
								conn.execute( f'DROP TABLE IF EXISTS "{table_name}"' )
							
							# --- Create Table ---
							columns = [ ]
							df.columns = [ create_identifier( c ) for c in df.columns ]
							for col in df.columns:
								sql_type = get_sqlite_type( df[ col ].dtype )
								columns.append( f'"{col}" {sql_type}' )
							
							create_stmt = (f'CREATE TABLE "{table_name}" '
							               f'({", ".join( columns )});')
							
							conn.execute( create_stmt )
							
							# --- Insert Data ---
							placeholders = ", ".join( [ "?" ] * len( df.columns ) )
							insert_stmt = (
									f'INSERT INTO "{table_name}" '
									f'VALUES ({placeholders});')
							
							conn.executemany( insert_stmt,
								df.where( pd.notnull( df ), None ).values.tolist( ) )
						
						conn.commit( )
					
					st.success( 'Import completed successfully (transaction committed).' )
					st.rerun( )
				except Exception as e:
					try:
						conn.rollback( )
					except:
						pass
					st.error( f'Import failed — transaction rolled back.\n\n{e}' )
		
		# -------------- BROWSE TAB
		with tabs[ 1 ]:
			tables = list_tables( )
			if tables:
				table = st.selectbox( 'Table', tables, key='table_name' )
				
				set_blue_divider( )
				
				df = read_table( table )
				st.data_editor( df, key='dm_browse_key' )
			else:
				st.info( 'No tables available.' )
		
		# -------------- CRUD
		with tabs[ 2 ]:
			tables = list_tables( )
			if not tables:
				st.info( 'No tables available.' )
			else:
				crud_header_c1, crud_header_c2, crud_header_c3 = st.columns( [ 0.45, 0.25, 0.30 ],
					border=True )
				
				with crud_header_c1:
					table = st.selectbox( 'Select Table', tables, key='crud_table' )
				
				df = read_table( table )
				schema = create_schema( table )
				
				type_map = { col[ 1 ]: col[ 2 ].upper( ) for col in schema if col[ 1 ] != 'rowid' }
				
				with crud_header_c2:
					st.metric( 'Rows', len( df.index ) )
				
				with crud_header_c3:
					st.metric( 'Columns', len( type_map ) )
				
				set_blue_divider( )
				
				insert_col, update_col = st.columns( [ 0.50, 0.50 ], border=True )
				
				# ------------------------------------------------------------------
				# INSERT
				# ------------------------------------------------------------------
				with insert_col:
					st.markdown( '##### Insert Row' )
					insert_data = { }
					for column, col_type in type_map.items( ):
						if 'INT' in col_type:
							insert_data[ column ] = st.number_input( column, step=1,
								key=f'ins_{table}_{column}' )
						elif 'REAL' in col_type:
							insert_data[ column ] = st.number_input( column, format='%.6f',
								key=f'ins_{table}_{column}' )
						elif 'BOOL' in col_type:
							insert_data[ column ] = 1 if st.checkbox( column,
								key=f'ins_{table}_{column}' ) else 0
						else:
							insert_data[ column ] = st.text_input( column,
								key=f'ins_{table}_{column}' )
					
					if st.button( 'Insert Row', key=f'insert_row_{table}',
							use_container_width=True ):
						cols = list( insert_data.keys( ) )
						quoted_cols = [ f'"{c}"' for c in cols ]
						placeholders = ', '.join( [ '?' ] * len( cols ) )
						stmt = (f'INSERT INTO "{table}" ({", ".join( quoted_cols )}) '
						        f'VALUES ({placeholders});')
						
						with create_connection( ) as conn:
							conn.execute( stmt, list( insert_data.values( ) ) )
							conn.commit( )
						
						st.success( 'Row inserted.' )
						st.rerun( )
				
				# ------------------------------------------------------------------
				# UPDATE
				# ------------------------------------------------------------------
				with update_col:
					st.markdown( '##### Update Row' )
					rowid = st.number_input( 'Row ID', min_value=1, step=1,
						key=f'crud_update_rowid_{table}' )
					
					update_data = { }
					
					for column, col_type in type_map.items( ):
						if 'INT' in col_type:
							val = st.number_input( column, step=1, key=f'upd_{table}_{column}' )
							update_data[ column ] = val
						
						elif 'REAL' in col_type:
							val = st.number_input( column, format='%.6f',
								key=f'upd_{table}_{column}' )
							update_data[ column ] = val
						
						elif 'BOOL' in col_type:
							val = 1 if st.checkbox( column,
								key=f'upd_{table}_{column}' ) else 0
							update_data[ column ] = val
						
						else:
							val = st.text_input( column, key=f'upd_{table}_{column}' )
							update_data[ column ] = val
					
					if st.button( 'Update Row', key=f'update_row_{table}',
							use_container_width=True ):
						set_clause = ', '.join( [ f'"{c}"=?' for c in update_data ] )
						stmt = f'UPDATE "{table}" SET {set_clause} WHERE rowid=?;'
						
						with create_connection( ) as conn:
							conn.execute( stmt, list( update_data.values( ) ) + [ rowid ] )
							conn.commit( )
						
						st.success( 'Row updated.' )
						st.rerun( )
				
				set_blue_divider( )
				
				delete_col, preview_col = st.columns( [ 0.35, 0.65 ], border=True )
				
				# ------------------------------------------------------------------
				# DELETE
				# ------------------------------------------------------------------
				with delete_col:
					st.markdown( '##### Delete Row' )
					delete_id = st.number_input( 'Row ID to Delete', min_value=1, step=1,
						key=f'crud_delete_rowid_{table}' )
					
					if st.button( 'Delete Row', key=f'delete_row_{table}',
							use_container_width=True ):
						with create_connection( ) as conn:
							conn.execute( f'DELETE FROM "{table}" WHERE rowid=?;', (delete_id,) )
							conn.commit( )
						
						st.success( 'Row deleted.' )
						st.rerun( )
				
				# ------------------------------------------------------------------
				# PREVIEW
				# ------------------------------------------------------------------
				with preview_col:
					st.markdown( '##### Current Data Preview' )
					st.data_editor( df.head( 25 ), key=f'dm_crud_preview_{table}',
						use_container_width=True, disabled=True )
		
		# -------------- EXPLORE
		with tabs[ 3 ]:
			tables = list_tables( )
			if tables:
				exp_c1, exp_c2, exp_c3 = st.columns( [ 0.4, 0.4, 0.2 ], border=True )
				with exp_c1:
					table = st.selectbox( 'Table', tables, key='explore_table' )
				with exp_c2:
					page_size = st.slider( 'Rows per page', 10, 500, 50 )
				with exp_c3:
					page = st.number_input( 'Page', min_value=1, step=1 )
					offset = (page - 1) * page_size
					df_page = read_table( table, page_size, offset )
				
				set_blue_divider( )
				
				st.data_editor( data=df_page, num_rows='dynamic', hide_index=False )
		
		# -------------- FILTER
		with tabs[ 4 ]:
			tables = list_tables( )
			if tables:
				tbl_c1, tbl_c2, tbl_c3 = st.columns( [ 0.25, 0.25, 0.5 ], border=True )
				with tbl_c1:
					table = st.selectbox( 'Select Table', tables, key='filter_table' )
					df = read_table( table )
				
				with tbl_c2:
					column = st.selectbox( 'Select Field', df.columns, key='selected_column' )
				
				with tbl_c3:
					value = st.text_input( 'Contains', placeholder='Enter Text for Lookup' )
					if value:
						df = df[ df[ column ].astype( str ).str.contains( value ) ]
				
				set_blue_divider( )
				
				st.data_editor( df, key='dm_filter_key' )
		
		# -------------- AGGREGATE
		with tabs[ 5 ]:
			tables = list_tables( )
			if tables:
				agg_c1, agg_c2, agg_c3, agg_c4 = st.columns( [ 0.2, 0.2, 0.2, 0.4 ], border=True )
				with agg_c1:
					table = st.selectbox( 'Table', tables, key='agg_table' )
					df = read_table( table )
					numeric_cols = df.select_dtypes( include=[ 'number' ] ).columns.tolist( )
					with agg_c2:
						if numeric_cols:
							col = st.selectbox( 'Column', numeric_cols, key='selected_col' )
					with agg_c3:
						agg = st.selectbox( 'Function', [ 'SUM', 'AVG', 'COUNT' ] )
					with agg_c4:
						if agg == 'SUM':
							st.metric( 'Result', df[ col ].sum( ), width='stretch',
								format='accounting' )
						elif agg == 'AVG':
							st.metric( 'Result', df[ col ].mean( ), width='stretch',
								format='accounting' )
						elif agg == 'COUNT':
							st.metric( 'Result', df[ col ].count( ), width='stretch',
								format='accounting' )
		
		# -------------- VISUALIZE
		with tabs[ 6 ]:
			tables = list_tables( )
			if tables:
				table = st.selectbox( 'Table', tables, key='viz_table' )
				df = read_table( table )
				create_visualization( df )
		
		# -------------- GEOCODE
		with tabs[ 7 ]:
			st.markdown( '#### Geocode Missing Report Coordinates' )
			
			tables = list_tables( )
			
			if not tables:
				st.info( 'No tables available.' )
			else:
				default_table = resolve_table_name( cfg.DEFAULT_DATA, tables )
				if default_table is None:
					default_table = tables[ 0 ]
				
				default_index = tables.index( default_table )
				
				control_c1, control_c2, control_c3, control_c4 = st.columns(
					[ 0.25, 0.25, 0.25, 0.25 ], border=True )
				
				with control_c1:
					table = st.selectbox( 'Table', tables, index=default_index,
						key='reports_geocode_table' )
				
				with control_c2:
					use_places = st.checkbox( 'Use Places Fallback', value=True,
						key='reports_geocode_use_places' )
				
				with control_c3:
					limit_enabled = st.checkbox( 'Limit Locations', value=True,
						key='reports_geocode_limit_enabled' )
				
				with control_c4:
					limit = st.number_input( 'Location Limit', min_value=1, max_value=10000,
						value=100, step=25, key='reports_geocode_limit' )
				
				location_limit = int( limit ) if limit_enabled else None
				
				required_cols = [ 'City', 'State', 'Country', 'Latitude', 'Longitude' ]
				schema = create_schema( table )
				table_cols = [ row[ 1 ] for row in schema ]
				missing_cols = [ col for col in required_cols if col not in table_cols ]
				
				if missing_cols:
					st.warning(
						f'Table is missing required column(s): {", ".join( missing_cols )}' )
				else:
					missing_rows = count_missing_report_coordinate_rows( table )
					df_locations = read_missing_report_locations( table, location_limit )
					distinct_total = len( read_missing_report_locations( table, None ) )
					
					status_c1, status_c2, status_c3, status_c4 = st.columns( 4 )
					status_c1.metric( 'Rows Missing Coordinates', f'{missing_rows:,}' )
					status_c2.metric( 'Distinct Locations', f'{distinct_total:,}' )
					status_c3.metric( 'Preview Locations', f'{len( df_locations ):,}' )
					status_c4.metric( 'Fallback', 'Enabled' if use_places else 'Disabled' )
					
					with st.expander( 'Distinct Locations Missing Coordinates', expanded=False ):
						if df_locations.empty:
							st.info( 'No missing coordinate locations found.' )
						else:
							st.data_editor( df_locations, key='reports_geocode_locations',
								use_container_width=True, disabled=True )
					
					action_c1, action_c2, action_c3, action_c4 = st.columns(
						[ 0.25, 0.25, 0.25, 0.25 ] )
					
					with action_c1:
						if st.button( 'Preview Geocoding', key='reports_geocode_preview_button',
								width='stretch' ):
							df_preview = preview_report_coordinate_updates( table_name=table,
								geocoder=geocoder, places=places, use_places=use_places,
								limit=location_limit )
							
							st.session_state[ 'df_reports_geocode_preview' ] = df_preview
					
					with action_c2:
						if st.button( 'Clear', icon='🧹', key='reports_geocode_clear_button',
								width='stretch' ):
							st.session_state[ 'df_reports_geocode_preview' ] = pd.DataFrame( )
							st.session_state[ 'reports_geocode_last_update' ] = { }
					
					with action_c3:
						confirm_update_coordinates = st.checkbox(
							'Confirm Update Coordinates',
							value=False,
							help=(
									'When checked, the Update Coordinates button will geocode missing '
									'Reports locations and immediately write matched coordinates back '
									'to SQLite.'
							),
							key='reports_geocode_confirm_update_coordinates' )
					
					with action_c4:
						if st.button( 'Update Coordinates', icon='📍',
								key='reports_geocode_update_coordinates_button',
								width='stretch',
								disabled=not confirm_update_coordinates ):
							try:
								df_update_preview = preview_report_coordinate_updates(
									table_name=table,
									geocoder=geocoder, places=places, use_places=use_places,
									limit=location_limit )
								
								st.session_state[ 'df_reports_geocode_preview' ] = df_update_preview
								if df_update_preview is None or df_update_preview.empty:
									st.session_state[ 'reports_geocode_last_update' ] = {
											'Table': table,
											'Status': 'No Updates',
											'Message': 'No missing coordinate locations were found.',
											'MatchedLocations': 0,
											'FailedLocations': 0,
											'SkippedLocations': 0,
											'RowsUpdated': 0
									}
									st.rerun( )
								
								status_series = df_update_preview[ 'Status' ].astype(
									str ).str.lower( )
								matched_count = int( (status_series == 'matched').sum( ) )
								failed_count = int( (status_series == 'failed').sum( ) )
								skipped_count = int( (status_series == 'skipped').sum( ) )
								
								if matched_count == 0:
									st.session_state[ 'reports_geocode_last_update' ] = {
											'Table': table,
											'Status': 'No Matched Locations',
											'Message': 'Geocoding completed, but no matched coordinates were returned.',
											'MatchedLocations': matched_count,
											'FailedLocations': failed_count,
											'SkippedLocations': skipped_count,
											'RowsUpdated': 0
									}
									st.rerun( )
								
								updated_count = apply_report_coordinate_updates( table_name=table,
									df_updates=df_update_preview )
								
								st.session_state[ 'reports_geocode_last_update' ] = {
										'Table': table,
										'Status': 'Updated' if updated_count else 'No Rows Updated',
										'Message': (
												f'Updated {updated_count:,} row(s).' if updated_count
												else 'Matched coordinates were found, but no rows were updated.'
										),
										'MatchedLocations': matched_count,
										'FailedLocations': failed_count,
										'SkippedLocations': skipped_count,
										'RowsUpdated': int( updated_count )
								}
								
								if updated_count:
									st.session_state[
										'df_reports_geocode_preview' ] = pd.DataFrame( )
								
								st.rerun( )
							
							except Exception as ex:
								st.error( f'Update Coordinates failed: {ex}' )
					
					last_update = st.session_state.get( 'reports_geocode_last_update', { } )
					
					if isinstance( last_update, dict ) and last_update:
						st.markdown( '##### Last Coordinate Update' )
						
						update_c1, update_c2, update_c3, update_c4 = st.columns( 4 )
						update_c1.metric( 'Matched Locations',
							f"{int( last_update.get( 'MatchedLocations', 0 ) ):,}" )
						update_c2.metric( 'Failed Locations',
							f"{int( last_update.get( 'FailedLocations', 0 ) ):,}" )
						update_c3.metric( 'Skipped Locations',
							f"{int( last_update.get( 'SkippedLocations', 0 ) ):,}" )
						update_c4.metric( 'Rows Updated',
							f"{int( last_update.get( 'RowsUpdated', 0 ) ):,}" )
						
						if last_update.get( 'Status', '' ) == 'Updated':
							st.success( last_update.get( 'Message', '' ) )
						else:
							st.info( last_update.get( 'Message', '' ) )
					
					df_preview = st.session_state.get( 'df_reports_geocode_preview',
						pd.DataFrame( ) )
					
					if df_preview is not None and not df_preview.empty:
						status_series = df_preview[ 'Status' ].astype( str ).str.lower( )
						matched_count = int( (status_series == 'matched').sum( ) )
						failed_count = int( (status_series == 'failed').sum( ) )
						skipped_count = int( (status_series == 'skipped').sum( ) )
						
						matched_rows = int(
							df_preview.loc[ status_series == 'matched', 'RowCount' ].sum( ) )
						
						result_c1, result_c2, result_c3, result_c4 = st.columns( 4 )
						result_c1.metric( 'Matched Locations', f'{matched_count:,}' )
						result_c2.metric( 'Failed Locations', f'{failed_count:,}' )
						result_c3.metric( 'Skipped Locations', f'{skipped_count:,}' )
						result_c4.metric( 'Rows Eligible For Update', f'{matched_rows:,}' )
						
						st.data_editor( df_preview, key='reports_geocode_preview_table',
							use_container_width=True, disabled=True )
						
						st.warning(
							'Apply Updates writes Latitude and Longitude values back to SQLite '
							'for all missing-coordinate rows matching the previewed City, State, '
							'and Country combinations. Review the preview before applying.' )
						
						apply_c1, apply_c2 = st.columns( [ 0.25, 0.75 ] )
						
						with apply_c1:
							apply_updates = st.checkbox( 'Confirm Apply Updates',
								value=False, key='reports_geocode_confirm_apply' )
						
						with apply_c2:
							if st.button( 'Apply Updates', key='reports_geocode_apply_button',
									width='stretch', disabled=not apply_updates ):
								updated_count = apply_report_coordinate_updates( table, df_preview )
								
								st.session_state[ 'reports_geocode_last_update' ] = {
										'Table': table,
										'Status': 'Updated' if updated_count else 'No Rows Updated',
										'Message': (
												f'Updated {updated_count:,} report coordinate row(s).'
												if updated_count
												else 'No rows were updated.'
										),
										'MatchedLocations': matched_count,
										'FailedLocations': failed_count,
										'SkippedLocations': skipped_count,
										'RowsUpdated': int( updated_count )
								}
								
								if updated_count:
									st.session_state[
										'df_reports_geocode_preview' ] = pd.DataFrame( )
								
								st.rerun( )
		
		# -------------- ADMIN
		with tabs[ 8 ]:
			tables = list_tables( )
			if tables:
				table = st.selectbox( 'Table', tables, key='admin_table' )
			
			set_blue_divider( )
			
			st.markdown( '##### Data Profiling' )
			tables = list_tables( )
			if tables:
				table = st.selectbox( 'Select Table', tables, key='profile_table' )
				if st.button( 'Generate Profile' ):
					profile_df = create_profile_table( table )
					render_table( profile_df )
			
			st.markdown( '##### Drop Table' )
			
			tables = list_tables( )
			if tables:
				table = st.selectbox( 'Select Table to Drop', tables, key='admin_drop_table' )
				
				# Initialize confirmation state
				if 'dm_confirm_drop' not in st.session_state:
					st.session_state.dm_confirm_drop = False
				
				# Step 1: Initial Drop click
				if st.button( 'Drop Table', key='admin_drop_button' ):
					st.session_state.dm_confirm_drop = True
				
				# Step 2: Confirmation UI
				if st.session_state.dm_confirm_drop:
					st.warning( f'You are about to permanently delete table {table}. '
					            'This action cannot be undone.' )
					
					col1, col2 = st.columns( 2 )
					if col1.button( 'Confirm Drop', key='admin_confirm_drop' ):
						try:
							drop_table( table )
							st.success( f'Table {table} dropped successfully.' )
						except Exception as e:
							st.error( f'Drop failed: {e}' )
						
						st.session_state.dm_confirm_drop = False
						st.rerun( )
					
					if col2.button( 'Cancel', key='admin_cancel_drop' ):
						st.session_state.dm_confirm_drop = False
						st.rerun( )
				
				df = read_table( table )
				col = st.selectbox( 'Create Index On', df.columns, key='df_key' )
				
				if st.button( 'Create Index' ):
					create_index( table, col )
					st.success( 'Index created.' )
			
			set_blue_divider( )
			
			st.markdown( '##### Create Custom Table' )
			new_table_name = st.text_input( 'Table Name' )
			column_count = st.number_input( 'Number of Columns', min_value=1,
				max_value=20, value=1 )
			
			columns = [ ]
			for i in range( column_count ):
				st.markdown( f'##### Column {i + 1}' )
				col_name = st.text_input( 'Column Name', key=f'col_name_{i}' )
				col_type = st.selectbox( 'Column Type', [ 'INTEGER', 'REAL', 'TEXT' ],
					key=f'col_type_{i}' )
				
				not_null = st.checkbox( 'NOT NULL', key=f'not_null_{i}' )
				primary_key = st.checkbox( 'PRIMARY KEY', key=f'pk_{i}' )
				auto_inc = st.checkbox( 'AUTOINCREMENT (INTEGER only)', key=f'ai_{i}' )
				
				columns.append( {
						'name': col_name,
						'type': col_type,
						'not_null': not_null,
						'primary_key': primary_key,
						'auto_increment': auto_inc } )
			
			if st.button( 'Create Table' ):
				try:
					create_custom_table( new_table_name, columns )
					st.success( 'Table created successfully.' )
					st.rerun( )
				
				except Exception as e:
					st.error( f'Error: {e}' )
			
			set_blue_divider( )
			st.markdown( '##### Schema Viewer' )
			
			tables = list_tables( )
			if tables:
				table = st.selectbox( 'Select Table', tables, key='schema_view_table' )
				
				# Column schema
				schema = create_schema( table )
				schema_df = pd.DataFrame( schema,
					columns=[ 'cid', 'name', 'type', 'notnull', 'default', 'pk' ] )
				
				st.markdown( "##### Columns" )
				st.data_editor( make_display_safe( schema_df ), hide_index=True,
					use_container_width=True, disabled=True )
				
				# Row count
				with create_connection( ) as conn:
					count = conn.execute( f'SELECT COUNT(*) FROM "{table}"' ).fetchone( )[ 0 ]
				
				st.metric( "Row Count", f"{count:,}" )
				
				# Indexes
				indexes = get_indexes( table )
				if indexes:
					idx_df = pd.DataFrame( indexes,
						columns=[ 'seq', 'name', 'unique', 'origin', 'partial' ] )
					
					st.markdown( "##### Indexes" )
					st.data_editor( make_display_safe( idx_df ), hide_index=True,
						use_container_width=True, disabled=True )
				else:
					st.info( "No indexes defined." )
			
			set_blue_divider( )
			st.markdown( '##### ALTER TABLE Operations' )
			
			tables = list_tables( )
			if tables:
				table = st.selectbox( 'Select Table', tables, key='alter_table_select' )
				operation = st.selectbox( 'Operation',
					[ 'Add Column', 'Rename Column', 'Rename Table', 'Drop Column' ], key='op_key' )
				
				if operation == 'Add Column':
					new_col = st.text_input( 'Column Name' )
					col_type = st.selectbox( 'Column Type', [ 'INTEGER', 'REAL', 'TEXT' ],
						key='key_type' )
					
					if st.button( 'Add Column' ):
						add_column( table, new_col, col_type )
						st.success( 'Column added.' )
						st.rerun( )
				
				elif operation == 'Rename Column':
					schema = create_schema( table )
					col_names = [ col[ 1 ] for col in schema ]
					
					old_col = st.selectbox( 'Column to Rename', col_names, key='old_key' )
					new_col = st.text_input( 'New Column Name' )
					
					if st.button( 'Rename Column' ):
						rename_column( table, old_col, new_col )
						st.success( 'Column renamed.' )
						st.rerun( )
				
				elif operation == 'Rename Table':
					new_name = st.text_input( 'New Table Name' )
					
					if st.button( 'Rename Table' ):
						rename_table( table, new_name )
						st.success( 'Table renamed.' )
						st.rerun( )
				
				elif operation == 'Drop Column':
					schema = create_schema( table )
					col_names = [ col[ 1 ] for col in schema ]
					
					drop_col = st.selectbox( 'Column to Drop', col_names, key='drop_key' )
					
					if st.button( 'Drop Column' ):
						drop_column( table, drop_col )
						st.success( 'Column dropped.' )
						st.rerun( )
		
		# -------------- SQL
		with tabs[ 9 ]:
			st.markdown( '##### SQL Console' )
			query = st.text_area( 'Enter SQL Query' )
			if st.button( label='Run', icon='🏃', ):
				if not is_safe_query( query ):
					st.error( 'Query blocked: Only read-only SELECT statements are allowed.' )
				else:
					try:
						start_time = time.perf_counter( )
						with create_connection( ) as conn:
							result = pd.read_sql_query( query, conn )
						
						end_time = time.perf_counter( )
						elapsed = end_time - start_time
						
						# ----------------------------------------------------------
						# Display Results
						# ----------------------------------------------------------
						st.dataframe( result, use_container_width=True )
						row_count = len( result )
						
						# ----------------------------------------------------------
						# Execution Metrics
						# ----------------------------------------------------------
						col1, col2 = st.columns( 2 )
						col1.metric( 'Rows Returned', f'{row_count:,}' )
						col2.metric( 'Execution Time (seconds)', f'{elapsed:.6f}' )
						
						# Optional slow query warning
						if elapsed > 2.0:
							st.warning( 'Slow query detected (> 2 seconds). Consider indexing.' )
						
						# ----------------------------------------------------------
						# Download
						# ----------------------------------------------------------
						if not result.empty:
							csv = result.to_csv( index=False ).encode( 'utf-8' )
							st.download_button( 'Download CSV', csv,
								'query_results.csv', 'text/csv' )
					
					except Exception as e:
						st.error( f'Execution failed: {e}' )
