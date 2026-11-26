"""Regression coverage for native Google Static Maps image resolution."""
from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, Optional
from urllib.parse import parse_qs, urlencode, urlsplit
import unittest
from unittest.mock import Mock


ROOT = Path( __file__ ).resolve( ).parents[ 1 ]


class StaticMapResolutionTests( unittest.TestCase ):
	"""Verify URL construction without making billable Google API calls."""

	def setUp( self ) -> None:
		"""Load the actual StaticMap class using isolated provider configuration."""
		tree = ast.parse( (ROOT / 'mapping.py').read_text( encoding='utf-8' ) )
		nodes = [ node for node in tree.body if
			(isinstance( node, ast.ClassDef ) and node.name == 'StaticMap') or
			(isinstance( node, ast.FunctionDef ) and node.name == 'throw_if') ]
		logger = Mock( )
		scope = { 'cfg': SimpleNamespace( GOOGLEMAPS_API_KEY='test-key' ),
			'Optional': Optional, 'Dict': Dict, 'urlencode': urlencode,
			'Error': RuntimeError, 'Logger': logger }
		exec( compile( ast.Module( body=nodes, type_ignores=[ ] ), 'mapping.py', 'exec' ), scope )
		self.static_map = scope[ 'StaticMap' ]( )

	def test_high_resolution_default( self ) -> None:
		"""Request native 1280 by 960 PNG pixels by default."""
		url = self.static_map.pin( 38.86, -77.06 )
		query = parse_qs( urlsplit( url ).query )
		self.assertEqual( query[ 'size' ], [ '640x480' ] )
		self.assertEqual( query[ 'scale' ], [ '2' ] )
		self.assertEqual( query[ 'format' ], [ 'png32' ] )
		self.assertEqual( query[ 'center' ], [ '38.86,-77.06' ] )

	def test_standard_resolution_preserves_map_coverage( self ) -> None:
		"""Changing scale leaves center, zoom, size and markers unchanged."""
		standard = parse_qs( urlsplit( self.static_map.pin( 38.86, -77.06,
			zoom=8, size='640x360', scale=1 ) ).query )
		high = parse_qs( urlsplit( self.static_map.pin( 38.86, -77.06,
			zoom=8, size='640x360', scale=2 ) ).query )
		self.assertEqual( standard.pop( 'scale' ), [ '1' ] )
		self.assertEqual( high.pop( 'scale' ), [ '2' ] )
		self.assertEqual( standard, high )

	def test_invalid_image_parameters( self ) -> None:
		"""Reject unsupported dimensions, scales, formats and zoom values."""
		for size in ( '800x600', '640x641', '0x480', 'invalid' ):
			with self.subTest( size=size ), self.assertRaises( RuntimeError ):
				self.static_map.pin( 38.86, -77.06, size=size )
		for scale in ( 0, 3, True ):
			with self.subTest( scale=scale ), self.assertRaises( RuntimeError ):
				self.static_map.pin( 38.86, -77.06, scale=scale )
		with self.assertRaises( RuntimeError ):
			self.static_map.pin( 38.86, -77.06, image_format='invalid' )
		with self.assertRaises( RuntimeError ):
			self.static_map.pin( 38.86, -77.06, zoom=21 )

	def test_application_requests_native_resolution( self ) -> None:
		"""Keep the resolution control and full-width rendering connected."""
		source = (ROOT / 'app.py').read_text( encoding='utf-8' )
		self.assertIn( "size=size, scale=scale, image_format='png32'", source )
		self.assertIn( "st.image( map_url, width='stretch' )", source )
		self.assertIn( "key='maps_scale'", source )


if __name__ == '__main__':
	unittest.main( )
