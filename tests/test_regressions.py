"""Regression tests for restored Mappy document and GIS execution contracts."""
from __future__ import annotations

import ast
from pathlib import Path
import unittest


ROOT = Path( __file__ ).resolve( ).parents[ 1 ]


class SourceContractTests( unittest.TestCase ):
	"""Verify critical source contracts without requiring optional provider packages."""

	def test_vector_module_is_top_level( self ) -> None:
		"""Verify the implementation moved out of the data-store directory."""
		self.assertTrue( (ROOT / 'vector.py').is_file( ) )
		self.assertFalse( (ROOT / 'stores' / 'vector.py').exists( ) )
		processing = (ROOT / 'processing.py').read_text( encoding='utf-8' )
		self.assertIn( 'from vector import ChromaStore, PineconeStore', processing )

	def test_vector_classes_expose_complete_lifecycle( self ) -> None:
		"""Verify both vector wrappers support persistence and retrieval operations."""
		tree = ast.parse( (ROOT / 'vector.py').read_text( encoding='utf-8' ) )
		classes = { node.name: node for node in tree.body if isinstance( node, ast.ClassDef ) }
		required = { 'connect', 'create', 'add_documents', 'add_embeddings',
			'similarity_search', 'similarity_search_with_score', 'get', 'delete', 'clear',
			'count', 'as_retriever', 'health' }
		for name in ( 'ChromaStore', 'PineconeStore' ):
			methods = { node.name for node in classes[ name ].body if isinstance( node, ast.FunctionDef ) }
			self.assertTrue( required.issubset( methods ), f'{name} is missing {required - methods}' )
		pinecone_methods = { node.name for node in classes[ 'PineconeStore' ].body
			if isinstance( node, ast.FunctionDef ) }
		self.assertTrue( { 'create_index', 'wait_until_ready', 'delete_by_filter' }.issubset(
			pinecone_methods ) )

	def test_chroma_storage_is_non_destructive( self ) -> None:
		"""Verify normal Chroma creation and writes do not reset the collection."""
		tree = ast.parse( (ROOT / 'vector.py').read_text( encoding='utf-8' ) )
		chroma = next( node for node in tree.body
			if isinstance( node, ast.ClassDef ) and node.name == 'ChromaStore' )
		for method_name in ( 'create', 'add_documents', 'add_embeddings' ):
			method = next( node for node in chroma.body
				if isinstance( node, ast.FunctionDef ) and node.name == method_name )
			self.assertNotIn( 'reset_collection', ast.unparse( method ) )

	def test_web_fetch_and_document_loading_are_separate( self ) -> None:
		"""Verify LangChain ingestion does not replace the scraper fetch contract."""
		source = (ROOT / 'fetchers.py').read_text( encoding='utf-8' )
		tree = ast.parse( source )
		web = next( node for node in tree.body
			if isinstance( node, ast.ClassDef ) and node.name == 'WebFetcher' )
		methods = { node.name: ast.unparse( node ) for node in web.body
			if isinstance( node, ast.FunctionDef ) }
		self.assertIn( 'requests.get', methods[ 'fetch' ] )
		self.assertIn( 'self.html', methods[ 'fetch' ] )
		self.assertNotIn( 'UnstructuredURLLoader', methods[ 'fetch' ] )
		self.assertIn( 'UnstructuredURLLoader', methods[ 'load_documents' ] )

	def test_google_geocoder_validates_provider_status( self ) -> None:
		"""Verify empty Google results cannot become an IndexError."""
		source = (ROOT / 'fetchers.py').read_text( encoding='utf-8' )
		self.assertIn( "_status != 'OK' or not _results", source )
		self.assertIn( 'Google Geocoding failed:', source )
		self.assertNotIn( "{ 'address': self.address, 'key': self.api_key, 'headers': self.headers }",
			source )
		application = (ROOT / 'app.py').read_text( encoding='utf-8' )
		self.assertIn( "Google Weather request failed: {ex.exception}", application )

	def test_legacy_gis_outputs_remain_present( self ) -> None:
		"""Verify the restored application retains specialized GIS result components."""
		source = (ROOT / 'app.py').read_text( encoding='utf-8' )
		for marker in ( 'Run Scraper', 'Crawl Summary JSON', '##### Weather Results',
			'##### Environmental Results', '##### Astronomical Results',
			'##### Geological Results' ):
			self.assertIn( marker, source )
		self.assertIn( 'render_document_processing( cache )', source )

	def test_source_expanders_include_processing_controls( self ) -> None:
		"""Verify every Web and GIS source exposes combined processing controls."""
		source = (ROOT / 'app.py').read_text( encoding='utf-8' )
		expected = {
			"'webscrape_source', 'Web Scraper', 'webscrape_processing'",
			"'weather_last_source', 'Google Weather', 'weather_google_processing'",
			"'weather_last_source', 'OpenWeather / Open-Meteo',",
			"'weather_last_source', 'Historical Weather',",
			"'weather_last_source', 'Climate Data', 'weather_climate_processing'",
			"'weather_last_source', 'Tides & Currents', 'weather_tides_processing'",
			"'env_last_source',\n\t\t\t\t\t'AirNow', 'env_airnow_processing'",
			"'env_last_source',\n\t\t\t\t\t'UV Index', 'env_uv_processing'",
			"'env_last_source',\n\t\t\t\t\t'OpenAQ', 'env_openaq_processing'",
			"'env_last_source',\n\t\t\t\t\t'PurpleAir', 'env_purple_processing'",
			"'env_last_source',\n\t\t\t\t\t'EnviroFacts', 'env_envirofacts_processing'",
			"'env_last_source',\n\t\t\t\t\t'FIRMS', 'env_firms_processing'",
			"'env_last_source',\n\t\t\t\t\t'EONET', 'env_eonet_processing'",
			"'astro_last_source', 'Naval Observatory', 'astro_naval_processing'",
			"'astro_last_source', 'Space Weather', 'astro_space_processing'",
			"'astro_last_source', 'Star Chart', 'astro_chart_processing'",
			"'astro_last_source', 'Satellite Center', 'astro_satellite_processing'",
			"'astro_last_source', 'Astro Catalog', 'astro_catalog_processing'",
			"'astro_last_source', 'AstroQuery / SIMBAD',",
			"'astro_last_source', 'Star Map', 'astro_starmap_processing'",
			"'geo_last_source',\n\t\t\t\t\t'USGS Earthquakes', 'geo_quake_processing'",
			"'geo_last_source',\n\t\t\t\t\t'Global Imagery', 'geo_imagery_processing'",
			"'geo_last_source',\n\t\t\t\t\t'USGS Water Data', 'geo_water_processing'",
			"'geo_last_source',\n\t\t\t\t\t'USGS The National Map', 'geo_tnm_processing'",
		}
		for marker in expected:
			self.assertIn( marker, source )
		self.assertEqual( source.count( 'render_source_processing_controls(' ), 24 )

	def test_processing_tabs_and_tokenization_contract( self ) -> None:
		"""Verify the right-side tabs and intermediate tokenization workflow are implemented."""
		application = (ROOT / 'app.py').read_text( encoding='utf-8' )
		processing = (ROOT / 'processing.py').read_text( encoding='utf-8' )
		for prefix in ( 'webscrape', 'weather', 'env', 'astro', 'geo' ):
			self.assertIn( f"render_mode_document_tabs( '{prefix}', '📄 Source Document' )",
				application )
		self.assertIn( "tokenize_run = tokenize_col.button( 'Tokenize'", processing )
		self.assertIn( 'def tokenize_documents(', processing )
		self.assertIn( "f'{prefix}_tokens'", processing )
		self.assertIn( "key=f'{prefix}_embeddings_editor'", processing )
		self.assertIn( 'st.data_editor(', processing )
		for label in ( 'Weather RAG', 'Environmental RAG', 'Astronomical RAG', 'Geological RAG' ):
			self.assertNotIn( label, application )


if __name__ == '__main__':
	unittest.main( )
