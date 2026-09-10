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


if __name__ == '__main__':
	unittest.main( )
