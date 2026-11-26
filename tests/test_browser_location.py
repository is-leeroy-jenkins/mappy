"""Regression tests for browser and active location state."""
from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, Optional
import unittest
from unittest.mock import Mock


ROOT = Path( __file__ ).resolve( ).parents[ 1 ]


class BrowserLocationTests( unittest.TestCase ):
	"""Verify location utilities without starting Streamlit or contacting Google."""

	def setUp( self ) -> None:
		"""Load the actual application functions into an isolated session."""
		tree = ast.parse( (ROOT / 'app.py').read_text( encoding='utf-8' ) )
		names = { 'throw_if', 'has_valid_coordinates', 'has_valid_global_coordinates',
			'set_coordinates', 'set_location_state', 'compose_location_from_state',
			'get_default_location', 'get_default_zipcode', 'get_default_latitude',
			'get_default_longitude', 'get_geolocation_error_message',
			'update_location_from_browser', 'bootstrap_browser_geolocation',
			'resolve_active_location' }
		nodes = [ node for node in tree.body if isinstance( node, ast.FunctionDef )
			and node.name in names ]
		self.assertEqual( { node.name for node in nodes }, names )
		self.state = { 'latitude': 0.0, 'longitude': 0.0, 'coordinates': ( ),
			'browser_geolocation_enabled': True }
		self.payload = { 'coords': { 'latitude': 51.5, 'longitude': -0.12, 'accuracy': 10 } }
		self.provider = Mock( )
		self.provider.reverse.return_value = { 'locality': 'London',
			'admin_level_1': 'England', 'country_code': 'GB', 'postal_code': 'SW1A' }
		self.scope = { 'st': SimpleNamespace( session_state=self.state, rerun=Mock( ) ),
			'get_geolocation': Mock( return_value=self.payload ), 'Geocoder': object,
			'Dict': Dict, 'Optional': Optional }
		exec( compile( ast.Module( body=nodes, type_ignores=[ ] ), 'app.py', 'exec' ), self.scope )

	def test_browser_coordinates_and_name( self ) -> None:
		"""Use reverse geocoding and preserve the initial physical location."""
		self.scope[ 'bootstrap_browser_geolocation' ]( self.provider )
		self.provider.reverse.assert_called_once_with( 51.5, -0.12 )
		self.assertEqual( self.scope[ 'get_default_location' ]( ), 'London, England, GB' )
		self.assertEqual( self.scope[ 'get_default_zipcode' ]( ), 'SW1A' )
		self.assertEqual( self.scope[ 'get_default_latitude' ]( ), 51.5 )
		self.assertEqual( self.scope[ 'get_default_longitude' ]( ), -0.12 )
		self.scope[ 'set_location_state' ]( location='Paris', latitude=48.85, longitude=2.35 )
		self.assertEqual( self.state[ 'browser_location_state' ][ 'location' ], 'London, England, GB' )
		self.assertEqual( self.scope[ 'get_default_location' ]( ), 'Paris' )
		self.assertEqual( self.scope[ 'get_default_zipcode' ]( ), '' )
		self.scope[ 'bootstrap_browser_geolocation' ]( self.provider )
		self.provider.reverse.assert_called_once_with( 51.5, -0.12 )

	def test_reverse_lookup_failure( self ) -> None:
		"""Retain valid browser coordinates when address lookup is unavailable."""
		self.provider.reverse.side_effect = RuntimeError( 'Unavailable' )
		self.scope[ 'bootstrap_browser_geolocation' ]( self.provider )
		self.assertTrue( self.state[ 'browser_geolocation_loaded' ] )
		self.assertEqual( self.scope[ 'get_default_location' ]( ), '51.500000,-0.120000' )
		self.assertEqual( self.scope[ 'get_default_zipcode' ]( ), '' )

	def test_denied_browser_location( self ) -> None:
		"""Do not report fallback coordinates as a successful browser location."""
		self.scope[ 'get_geolocation' ].return_value = {
			'error': { 'code': 1, 'message': 'Denied' } }
		self.scope[ 'bootstrap_browser_geolocation' ]( self.provider )
		self.assertTrue( self.state[ 'browser_geolocation_permission_denied' ] )
		self.assertFalse( self.state[ 'browser_geolocation_loaded' ] )
		self.assertEqual( self.scope[ 'get_default_latitude' ]( ), 38.9072 )
		self.assertEqual( self.scope[ 'get_default_zipcode' ]( ), '' )
		self.provider.reverse.assert_not_called( )

	def test_manual_coordinate_resolution( self ) -> None:
		"""Resolve new working coordinates without changing the browser snapshot."""
		self.scope[ 'bootstrap_browser_geolocation' ]( self.provider )
		self.provider.reverse.return_value = { 'locality': 'Paris', 'country_code': 'FR' }
		self.scope[ 'resolve_active_location' ]( 48.85, 2.35, self.provider )
		self.assertEqual( self.scope[ 'get_default_location' ]( ), 'Paris, FR' )
		self.assertEqual( self.state[ 'browser_location_state' ][ 'latitude' ], 51.5 )
		self.assertEqual( self.scope[ 'get_default_zipcode' ]( ), '' )

	def test_map_theme_and_width( self ) -> None:
		"""Preserve the matched celestial palette and responsive map presentation."""
		source = (ROOT / 'app.py').read_text( encoding='utf-8' )
		self.assertIn( "st.image( map_url, width='stretch' )", source )
		self.assertIn( "Center on User Location", source )
		css = (ROOT / 'assets/starmap/style.css').read_text( encoding='utf-8' )
		script = (ROOT / 'assets/starmap/js/main.js').read_text( encoding='utf-8' )
		self.assertIn( '--background: #0E1117', css )
		self.assertIn( "background: '#05070B'", script )
		self.assertIn( "dsos: '#4DA3FF'", script )
		self.assertIn( "planets: '#FFD700'", script )


if __name__ == '__main__':
	unittest.main( )
