'''
  ******************************************************************************************
      Assembly:                Mappy
      Filename:                document_processing.py
      Author:                  Terry D. Eppler
      Created:                 09-08-2026
      Last Modified By:        Terry D. Eppler
      Last Modified On:        09-08-2026
  ******************************************************************************************
  <summary>
    Foo-style document loading, web scraping, chunking, embedding, and vector-storage UI.
  </summary>
  ******************************************************************************************
'''
from __future__ import annotations

import json
import math
import os
import tempfile
from pathlib import Path
from typing import Dict, List

import pandas as pd
import streamlit as st
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

import config as cfg
from embedders import EmbeddingFactory
from excel import Excel
from fetchers import WebFetcher
from loaders import DocumentLoaderFactory
from stores.vector import ChromaStore, PineconeStore


DOCUMENT_LOADERS: Dict[ str, Dict[ str, object ] ] = {
	'Text': { 'label': 'Text Loader', 'icon': '📝', 'types': [ 'txt', 'text', 'log' ], 'prefix': 'txt' },
	'CSV': { 'label': 'CSV Loader', 'icon': '📊', 'types': [ 'csv' ], 'prefix': 'csv' },
	'PDF': { 'label': 'PDF Loader', 'icon': '📕', 'types': [ 'pdf' ], 'prefix': 'pdf' },
	'Excel': { 'label': 'Excel Loader', 'icon': '📗', 'types': [ 'xlsx', 'xls' ], 'prefix': 'xlsx' },
	'Word': { 'label': 'Word Loader', 'icon': '📘', 'types': [ 'docx' ], 'prefix': 'docx' },
	'Markdown': { 'label': 'Markdown Loader', 'icon': '🧾', 'types': [ 'md', 'markdown' ], 'prefix': 'md' },
	'HTML': { 'label': 'HTML Loader', 'icon': '🌐', 'types': [ 'html', 'htm' ], 'prefix': 'html' },
	'JSON': { 'label': 'JSON Loader', 'icon': '🧩', 'types': [ 'json' ], 'prefix': 'json' },
	'PowerPoint': { 'label': 'PowerPoint Loader', 'icon': '📽️', 'types': [ 'pptx' ], 'prefix': 'pptx' },
}

EMBEDDING_MODELS: Dict[ str, List[ str ] ] = {
	'OpenAI': [ 'text-embedding-3-small', 'text-embedding-3-large' ],
	'Google Generative AI': [ 'gemini-embedding-2-preview' ],
	'Mistral AI': [ 'mistral-embed' ],
	'Hugging Face': [
		'sentence-transformers/all-MiniLM-L6-v2',
		'sentence-transformers/all-mpnet-base-v2',
	],
	'Local GGUF': [ 'Local GGUF' ],
}


def throw_if( name: str, value: object ) -> None:
	"""Validate a required value.

	Args:
		name: Argument name included in validation failures.
		value: Runtime value to validate.

	Returns:
		None: This function validates input only.
	"""
	if value is None:
		raise ValueError( f'Argument "{name}" cannot be empty!' )
	if isinstance( value, str ) and not value.strip( ):
		raise ValueError( f'Argument "{name}" cannot be empty!' )
	if isinstance( value, ( list, tuple, dict, set ) ) and len( value ) == 0:
		raise ValueError( f'Argument "{name}" cannot be empty!' )


def initialize_document_state( ) -> None:
	"""Initialize shared document-processing state."""
	defaults = {
		'document_documents': [ ],
		'document_chunks': [ ],
		'document_embeddings': [ ],
		'document_embedder': None,
		'document_vector_store': None,
		'document_active_loader': '',
		'document_file_name': '',
		'document_chunk_size_used': 0,
		'document_chunk_overlap_used': 0,
		'document_embedding_provider_used': '',
		'document_embedding_model_used': '',
		'document_embedding_model_path_used': '',
	}
	for key, value in defaults.items( ):
		if key not in st.session_state:
			st.session_state[ key ] = value


def initialize_web_state( ) -> None:
	"""Initialize shared web-document state."""
	defaults = {
		'web_documents': [ ],
		'web_document_url': '',
		'web_chunks': [ ],
		'web_embeddings': [ ],
		'web_embedder': None,
		'web_vector_store': None,
		'web_chunk_size_used': 0,
		'web_chunk_overlap_used': 0,
		'web_embedding_provider_used': '',
		'web_embedding_model_used': '',
		'web_embedding_model_path_used': '',
	}
	for key, value in defaults.items( ):
		if key not in st.session_state:
			st.session_state[ key ] = value


def clear_document_state( ) -> None:
	"""Clear loaded documents and all derived document state."""
	initialize_document_state( )
	st.session_state[ 'document_documents' ] = [ ]
	st.session_state[ 'document_chunks' ] = [ ]
	st.session_state[ 'document_embeddings' ] = [ ]
	st.session_state[ 'document_embedder' ] = None
	st.session_state[ 'document_vector_store' ] = None
	st.session_state[ 'document_active_loader' ] = ''
	st.session_state[ 'document_file_name' ] = ''
	st.session_state[ 'document_chunk_size_used' ] = 0
	st.session_state[ 'document_chunk_overlap_used' ] = 0
	st.session_state[ 'document_embedding_provider_used' ] = ''
	st.session_state[ 'document_embedding_model_used' ] = ''
	st.session_state[ 'document_embedding_model_path_used' ] = ''


def clear_web_state( ) -> None:
	"""Clear scraped documents and all derived web-document state."""
	initialize_web_state( )
	st.session_state[ 'web_documents' ] = [ ]
	st.session_state[ 'web_document_url' ] = ''
	st.session_state[ 'web_chunks' ] = [ ]
	st.session_state[ 'web_embeddings' ] = [ ]
	st.session_state[ 'web_embedder' ] = None
	st.session_state[ 'web_vector_store' ] = None
	st.session_state[ 'web_chunk_size_used' ] = 0
	st.session_state[ 'web_chunk_overlap_used' ] = 0
	st.session_state[ 'web_embedding_provider_used' ] = ''
	st.session_state[ 'web_embedding_model_used' ] = ''
	st.session_state[ 'web_embedding_model_path_used' ] = ''


def load_uploaded_document( loader_type: str, uploaded_file: object ) -> List[ Document ]:
	"""Load an uploaded file into LangChain documents."""
	throw_if( 'loader_type', loader_type )
	throw_if( 'uploaded_file', uploaded_file )
	factory = DocumentLoaderFactory( )
	loader = factory.create( loader_type )
	suffix = Path( uploaded_file.name ).suffix
	temporary_path = ''
	try:
		with tempfile.NamedTemporaryFile( delete=False, suffix=suffix ) as handle:
			handle.write( uploaded_file.getvalue( ) )
			temporary_path = handle.name
		documents = loader.load( temporary_path ) or [ ]
		for document in documents:
			document.metadata = dict( document.metadata or { } )
			document.metadata[ 'source' ] = uploaded_file.name
			document.metadata[ 'filename' ] = uploaded_file.name
			document.metadata[ 'loader' ] = loader.__class__.__name__
			document.metadata.pop( 'path', None )
		return documents
	finally:
		if temporary_path and os.path.exists( temporary_path ):
			os.remove( temporary_path )


def render_processing_inputs( key_prefix: str ) -> Dict[ str, object ]:
	"""Render Foo-style chunking, embedding, and vector-store controls."""
	throw_if( 'key_prefix', key_prefix )
	chunk_col, overlap_col = st.columns( 2 )
	with chunk_col:
		chunk_size = st.slider( 'Chunk Size', min_value=1, max_value=5000, value=1000,
			step=1, key=f'{key_prefix}_chunk_size' )
	with overlap_col:
		chunk_overlap = st.slider( 'Chunk Overlap', min_value=0,
			max_value=max( 0, int( chunk_size ) - 1 ), value=min( 200, max( 0, int( chunk_size ) - 1 ) ),
			step=1, key=f'{key_prefix}_chunk_overlap' )

	provider_col, model_col = st.columns( 2 )
	with provider_col:
		provider = st.selectbox( 'Embedding Provider', options=list( EMBEDDING_MODELS.keys( ) ),
			index=list( EMBEDDING_MODELS.keys( ) ).index( 'Hugging Face' ),
			key=f'{key_prefix}_embedding_provider' )
	with model_col:
		model = st.selectbox( 'Embedding Model', options=EMBEDDING_MODELS[ provider ],
			key=f'{key_prefix}_embedding_model' )

	model_path = ''
	if provider == 'Local GGUF':
		model_path = st.text_input( 'Local GGUF Model Path',
			placeholder=r'C:\models\embedding-model.gguf', key=f'{key_prefix}_embedding_model_path' )

	store_col, target_col = st.columns( 2 )
	with store_col:
		vector_backend = st.selectbox( 'Vector Store', options=[ 'Chroma', 'Pinecone' ],
			key=f'{key_prefix}_vector_backend' )
	with target_col:
		if vector_backend == 'Chroma':
			vector_target = st.text_input( 'Collection Name', value='mappy-documents',
				key=f'{key_prefix}_chroma_collection' )
		else:
			vector_target = st.text_input( 'Index Name', value='', key=f'{key_prefix}_pinecone_index' )

	if vector_backend == 'Chroma':
		persist_directory = st.text_input( 'Persistence Directory', value='stores/chroma',
			key=f'{key_prefix}_chroma_directory' )
		namespace = ''
	else:
		persist_directory = ''
		namespace = st.text_input( 'Namespace', value='', key=f'{key_prefix}_pinecone_namespace' )

	return {
		'chunk_size': int( chunk_size ),
		'chunk_overlap': int( chunk_overlap ),
		'provider': provider,
		'model': model,
		'model_path': model_path,
		'vector_backend': vector_backend,
		'vector_target': vector_target,
		'persist_directory': persist_directory,
		'namespace': namespace,
	}


def chunk_documents( documents: List[ Document ], chunk_size: int, chunk_overlap: int ) -> List[ Document ]:
	"""Split LangChain documents into retrieval chunks."""
	throw_if( 'documents', documents )
	if chunk_overlap >= chunk_size:
		raise ValueError( 'Chunk Overlap must be smaller than Chunk Size.' )
	splitter = RecursiveCharacterTextSplitter(
		chunk_size=int( chunk_size ), chunk_overlap=int( chunk_overlap ) )
	chunks = splitter.split_documents( documents )
	for index, document in enumerate( chunks, start=1 ):
		document.metadata = dict( document.metadata or { } )
		document.metadata[ 'chunk_id' ] = f'chunk-{index:06d}'
	return chunks


def create_embeddings( chunks: List[ Document ], provider: str, model: str,
	model_path: str ) -> tuple[ object, List[ List[ float ] ] ]:
	"""Create and validate embeddings for document chunks."""
	throw_if( 'chunks', chunks )
	factory = EmbeddingFactory( )
	embedder = factory.create( provider, model, model_path )
	vectors = embedder.embed_documents( [ document.page_content for document in chunks ] )
	if len( vectors ) != len( chunks ):
		raise RuntimeError( 'Embedding count does not match the chunk count.' )
	dimensions = { len( vector ) for vector in vectors }
	if len( dimensions ) != 1:
		raise RuntimeError( 'Embedding vectors do not have a consistent dimension.' )
	for vector in vectors:
		if not all( math.isfinite( float( value ) ) for value in vector ):
			raise RuntimeError( 'Embedding vectors contain non-finite values.' )
	return embedder, vectors


def store_documents( chunks: List[ Document ], embedder: object, vector_backend: str,
	vector_target: str, persist_directory: str, namespace: str ) -> object:
	"""Persist document chunks to Chroma or Pinecone."""
	throw_if( 'chunks', chunks )
	throw_if( 'embedder', embedder )
	throw_if( 'vector_backend', vector_backend )
	throw_if( 'vector_target', vector_target )
	if vector_backend == 'Chroma':
		store = ChromaStore( )
		return store.create( chunks, embedder, vector_target, persist_directory )
	api_key = getattr( cfg, 'PINECONE_API_KEY', '' ) or os.getenv( 'PINECONE_API_KEY', '' )
	store = PineconeStore( )
	return store.create( chunks, embedder, vector_target, namespace, api_key )


def render_document_actions( loader_type: str, key_prefix: str, settings: Dict[ str, object ] ) -> None:
	"""Render Chunk, Embed, and Store actions for one Foo-style loader expander."""
	throw_if( 'loader_type', loader_type )
	throw_if( 'key_prefix', key_prefix )
	throw_if( 'settings', settings )
	chunk_col, embed_col, store_col = st.columns( 3 )
	chunk_run = chunk_col.button( 'Chunk', key=f'{key_prefix}_chunk_run', use_container_width=True )
	embed_run = embed_col.button( 'Embed', key=f'{key_prefix}_embed_run', use_container_width=True )
	store_run = store_col.button( 'Store', key=f'{key_prefix}_store_run', use_container_width=True )

	if chunk_run:
		if st.session_state[ 'document_active_loader' ] != loader_type:
			st.warning( 'Load this document source before chunking.' )
		else:
			try:
				chunks = chunk_documents( st.session_state[ 'document_documents' ],
					settings[ 'chunk_size' ], settings[ 'chunk_overlap' ] )
				st.session_state[ 'document_chunks' ] = chunks
				st.session_state[ 'document_chunk_size_used' ] = settings[ 'chunk_size' ]
				st.session_state[ 'document_chunk_overlap_used' ] = settings[ 'chunk_overlap' ]
				st.session_state[ 'document_embeddings' ] = [ ]
				st.session_state[ 'document_embedder' ] = None
				st.session_state[ 'document_vector_store' ] = None
				st.success( f'Created {len( chunks ):,} chunk(s).' )
			except Exception as exc:
				st.error( str( exc ) )

	if embed_run:
		if not st.session_state[ 'document_chunks' ]:
			st.warning( 'Chunk the loaded document before embedding.' )
		elif settings[ 'chunk_size' ] != st.session_state[ 'document_chunk_size_used' ] or \
				settings[ 'chunk_overlap' ] != st.session_state[ 'document_chunk_overlap_used' ]:
			st.warning( 'Chunk settings changed. Run Chunk again before embedding.' )
		else:
			try:
				embedder, vectors = create_embeddings( st.session_state[ 'document_chunks' ],
					settings[ 'provider' ], settings[ 'model' ], settings[ 'model_path' ] )
				st.session_state[ 'document_embedder' ] = embedder
				st.session_state[ 'document_embeddings' ] = vectors
				st.session_state[ 'document_embedding_provider_used' ] = settings[ 'provider' ]
				st.session_state[ 'document_embedding_model_used' ] = settings[ 'model' ]
				st.session_state[ 'document_embedding_model_path_used' ] = settings[ 'model_path' ]
				st.session_state[ 'document_vector_store' ] = None
				st.success( f'Created {len( vectors ):,} embedding vector(s).' )
			except Exception as exc:
				st.error( str( exc ) )

	if store_run:
		if st.session_state[ 'document_embedder' ] is None or not st.session_state[ 'document_embeddings' ]:
			st.warning( 'Embed the current chunks before storage.' )
		elif settings[ 'provider' ] != st.session_state[ 'document_embedding_provider_used' ] or \
				settings[ 'model' ] != st.session_state[ 'document_embedding_model_used' ] or \
				settings[ 'model_path' ] != st.session_state[ 'document_embedding_model_path_used' ]:
			st.warning( 'Embedding settings changed. Run Embed again before storage.' )
		else:
			try:
				st.session_state[ 'document_vector_store' ] = store_documents(
					st.session_state[ 'document_chunks' ], st.session_state[ 'document_embedder' ],
					settings[ 'vector_backend' ], settings[ 'vector_target' ],
					settings[ 'persist_directory' ], settings[ 'namespace' ] )
				st.success( f'Stored {len( st.session_state[ "document_chunks" ] ):,} chunk(s).' )
			except Exception as exc:
				st.error( str( exc ) )


def render_loader_expander( loader_type: str, settings: Dict[ str, object ] ) -> None:
	"""Render one local Foo-style loader expander."""
	loader_settings = DOCUMENT_LOADERS[ loader_type ]
	key_prefix = str( loader_settings[ 'prefix' ] )
	with st.expander( label=str( loader_settings[ 'label' ] ), icon=str( loader_settings[ 'icon' ] ),
		expanded=False ):
		uploaded_file = st.file_uploader( 'Upload File', type=loader_settings[ 'types' ],
			key=f'{key_prefix}_upload' )
		processing = render_processing_inputs( key_prefix )
		load_col, clear_col, save_col = st.columns( 3 )
		load_run = load_col.button( 'Load', icon='📤', key=f'{key_prefix}_load', use_container_width=True )
		clear_run = clear_col.button( 'Clear', icon='🧹', key=f'{key_prefix}_clear', use_container_width=True )
		can_save = st.session_state.get( 'document_active_loader' ) == loader_type and \
			bool( st.session_state.get( 'document_documents' ) )
		if can_save:
			text = '\n\n'.join( document.page_content for document in st.session_state[ 'document_documents' ] )
			save_col.download_button( 'Save', data=text, file_name=f'{key_prefix}_loader_output.txt',
				mime='text/plain', icon='💾', key=f'{key_prefix}_save', use_container_width=True )
		else:
			save_col.button( 'Save', icon='💾', key=f'{key_prefix}_save_disabled', disabled=True,
				use_container_width=True )

		if clear_run and st.session_state.get( 'document_active_loader' ) == loader_type:
			clear_document_state( )
			st.rerun( )

		if load_run:
			try:
				documents = load_uploaded_document( loader_type, uploaded_file )
				throw_if( 'documents', documents )
				st.session_state[ 'document_documents' ] = documents
				st.session_state[ 'document_chunks' ] = [ ]
				st.session_state[ 'document_embeddings' ] = [ ]
				st.session_state[ 'document_embedder' ] = None
				st.session_state[ 'document_vector_store' ] = None
				st.session_state[ 'document_active_loader' ] = loader_type
				st.session_state[ 'document_file_name' ] = uploaded_file.name
				st.success( f'Loaded {len( documents ):,} LangChain document(s).' )
			except Exception as exc:
				st.error( str( exc ) )

		render_document_actions( loader_type, key_prefix, processing )


def render_enrichment_expander( cache: object ) -> None:
	"""Render Mappy's existing Excel/CSV geospatial enrichment workflow."""
	with st.expander( label='Excel / CSV Enrichment', icon='🌎', expanded=False ):
		uploaded = st.file_uploader( 'Upload CSV or XLSX', type=[ 'csv', 'xlsx' ],
			key='data_upload_file' )
		enrichment_mode = st.selectbox( 'Enrichment Mode',
			options=[ 'City / State / Country', 'Address Column' ], key='data_upload_enrichment_mode' )
		if enrichment_mode == 'City / State / Country':
			city_col, state_col = st.columns( 2 )
			with city_col:
				city = st.text_input( 'City Column', value='City', key='data_upload_city_col' )
			with state_col:
				state = st.text_input( 'State Column', value='State', key='data_upload_state_col' )
			country = st.text_input( 'Country Column', value='Country', key='data_upload_country_col' )
			address = ''
		else:
			address = st.text_input( 'Address Column', value='Address', key='data_upload_address_col' )
			country = st.text_input( 'Country Bias Column', value='Country',
				key='data_upload_address_country_col' )
			city = ''
			state = ''
		sheet_name = st.text_input( 'Worksheet', value='Sheet1', key='data_upload_sheet_name' )
		if uploaded and st.button( 'Enrich File', key='data_upload_enrich', use_container_width=True ):
			input_path = f'_input_{uploaded.name}'
			output_path = f'_output_{uploaded.name}'
			try:
				with open( input_path, 'wb' ) as handle:
					handle.write( uploaded.getvalue( ) )
				excel = Excel( api=cfg.GOOGLE_API_KEY, cache=cache )
				sheet_value = sheet_name if input_path.lower( ).endswith( '.xlsx' ) else None
				if enrichment_mode == 'City / State / Country':
					excel.enrich( inpath=input_path, outpath=output_path, city=city,
						state=state, cntry=country, sheet=sheet_value )
				else:
					excel.enrich_from_address( inpath=input_path, outpath=output_path,
						address=address, sheet=sheet_value, cntry=country )
				if output_path.lower( ).endswith( '.csv' ):
					frame = pd.read_csv( output_path )
				else:
					frame = pd.read_excel( output_path )
				st.dataframe( frame, use_container_width=True, hide_index=True )
				with open( output_path, 'rb' ) as handle:
					output_bytes = handle.read( )
				st.download_button( 'Download Enriched File', data=output_bytes,
					file_name=Path( output_path ).name, key='data_upload_download' )
			except Exception as exc:
				st.error( f'Enrichment failed: {exc}' )
			finally:
				for path in [ input_path, output_path ]:
					if os.path.exists( path ):
						os.remove( path )


def render_document_tabs( documents_key: str, chunks_key: str, embeddings_key: str,
	first_label: str ) -> None:
	"""Render loaded/scraped, chunk, and embedding tabs."""
	document_tab, chunks_tab, embeddings_tab = st.tabs( [ first_label, '✂️ Chunks', '🧠 Embeddings' ] )
	with document_tab:
		documents = st.session_state.get( documents_key ) or [ ]
		if not documents:
			st.info( 'No LangChain documents are loaded.' )
		else:
			rows = [ ]
			for index, document in enumerate( documents, start=1 ):
				rows.append( {
					'Document': index,
					'Source': ( document.metadata or { } ).get( 'source', '' ),
					'Loader': ( document.metadata or { } ).get( 'loader', '' ),
					'Characters': len( document.page_content or '' ),
					'Metadata': document.metadata or { },
					'Text': document.page_content or '',
				} )
			st.dataframe( pd.DataFrame( rows ), use_container_width=True, hide_index=True )
	with chunks_tab:
		chunks = st.session_state.get( chunks_key ) or [ ]
		if not chunks:
			st.info( 'No document chunks are available.' )
		else:
			rows = [ ]
			for index, document in enumerate( chunks, start=1 ):
				rows.append( {
					'Chunk': index,
					'Chunk ID': ( document.metadata or { } ).get( 'chunk_id', '' ),
					'Source': ( document.metadata or { } ).get( 'source', '' ),
					'Characters': len( document.page_content or '' ),
					'Text': document.page_content or '',
				} )
			st.dataframe( pd.DataFrame( rows ), use_container_width=True, hide_index=True )
	with embeddings_tab:
		vectors = st.session_state.get( embeddings_key ) or [ ]
		chunks = st.session_state.get( chunks_key ) or [ ]
		if not vectors:
			st.info( 'No embedding vectors are available.' )
		else:
			rows = [ ]
			for index, vector in enumerate( vectors ):
				document = chunks[ index ] if index < len( chunks ) else None
				rows.append( {
					'Chunk': index + 1,
					'Dimensions': len( vector ),
					'Source': ( document.metadata or { } ).get( 'source', '' ) if document else '',
					'Text': document.page_content if document else '',
					'Embedding': vector,
				} )
			st.dataframe( pd.DataFrame( rows ), use_container_width=True, hide_index=True )


def render_document_processing( cache: object = None ) -> None:
	"""Render Foo-style local document loading in Mappy Data Upload mode."""
	initialize_document_state( )
	st.subheader( '📤 Document Loading' )
	st.divider( )
	left, right = st.columns( [ 0.4, 0.6 ], gap='xxsmall', border=True )
	with left:
		with st.expander( label='Local Documents', icon='📁', expanded=True ):
			for loader_type in DOCUMENT_LOADERS:
				render_loader_expander( loader_type, DOCUMENT_LOADERS[ loader_type ] )
		render_enrichment_expander( cache )
	with right:
		render_document_tabs( 'document_documents', 'document_chunks', 'document_embeddings',
			'📄 Loaded' )


def render_web_document_processing( ) -> None:
	"""Render Foo-style web scraping and document processing in Mappy Web Scraper mode."""
	initialize_web_state( )
	st.subheader( '🕷️ Web Document Processing' )
	st.divider( )
	left, right = st.columns( [ 0.4, 0.6 ], gap='xxsmall', border=True )
	with left:
		with st.expander( label='Web Loader', icon='🌐', expanded=True ):
			target_url = st.text_input( 'Target URL', placeholder='https://example.com',
				key='web_document_url_input' )
			request_timeout = st.slider( 'Request Timeout', min_value=1, max_value=120,
				value=10, step=1, key='web_document_timeout' )
			fetch_col, clear_col = st.columns( 2 )
			fetch_run = fetch_col.button( 'Fetch', icon='🌐', key='web_document_fetch',
				use_container_width=True )
			clear_run = clear_col.button( 'Clear', icon='🧹', key='web_document_clear',
				use_container_width=True )
			if clear_run:
				clear_web_state( )
				st.rerun( )
			if fetch_run:
				try:
					throw_if( 'target_url', target_url )
					fetcher = WebFetcher( )
					documents = fetcher.fetch( target_url.strip( ), time=int( request_timeout ) )
					throw_if( 'documents', documents )
					st.session_state[ 'web_documents' ] = documents
					st.session_state[ 'web_document_url' ] = target_url.strip( )
					st.session_state[ 'web_chunks' ] = [ ]
					st.session_state[ 'web_embeddings' ] = [ ]
					st.session_state[ 'web_embedder' ] = None
					st.session_state[ 'web_vector_store' ] = None
					st.success( f'Scraped {len( documents ):,} LangChain document(s).' )
				except Exception as exc:
					st.error( str( exc ) )

		with st.expander( label='Chunking', icon='✂️', expanded=False ):
			chunk_col, overlap_col = st.columns( 2 )
			with chunk_col:
				chunk_size = st.slider( 'Chunk Size', min_value=1, max_value=5000, value=1000,
					step=1, key='web_chunk_size' )
			with overlap_col:
				chunk_overlap = st.slider( 'Chunk Overlap', min_value=0,
					max_value=max( 0, int( chunk_size ) - 1 ),
					value=min( 200, max( 0, int( chunk_size ) - 1 ) ), step=1,
					key='web_chunk_overlap' )
			if st.button( 'Chunk', key='web_chunk_run', use_container_width=True ):
				try:
					chunks = chunk_documents( st.session_state[ 'web_documents' ],
						int( chunk_size ), int( chunk_overlap ) )
					st.session_state[ 'web_chunks' ] = chunks
					st.session_state[ 'web_chunk_size_used' ] = int( chunk_size )
					st.session_state[ 'web_chunk_overlap_used' ] = int( chunk_overlap )
					st.session_state[ 'web_embeddings' ] = [ ]
					st.session_state[ 'web_embedder' ] = None
					st.session_state[ 'web_vector_store' ] = None
					st.success( f'Created {len( chunks ):,} chunk(s).' )
				except Exception as exc:
					st.error( str( exc ) )

		with st.expander( label='Embeddings', icon='🧠', expanded=False ):
			provider_col, model_col = st.columns( 2 )
			with provider_col:
				provider = st.selectbox( 'Embedding Provider', options=list( EMBEDDING_MODELS.keys( ) ),
					index=list( EMBEDDING_MODELS.keys( ) ).index( 'Hugging Face' ),
					key='web_embedding_provider' )
			with model_col:
				model = st.selectbox( 'Embedding Model', options=EMBEDDING_MODELS[ provider ],
					key='web_embedding_model' )
			model_path = ''
			if provider == 'Local GGUF':
				model_path = st.text_input( 'Local GGUF Model Path',
					placeholder=r'C:\models\embedding-model.gguf', key='web_embedding_model_path' )
			if st.button( 'Embed', key='web_embed_run', use_container_width=True ):
				if not st.session_state[ 'web_chunks' ]:
					st.warning( 'Chunk the scraped document before embedding.' )
				elif int( st.session_state.get( 'web_chunk_size', 1000 ) ) != st.session_state[ 'web_chunk_size_used' ] or \
						int( st.session_state.get( 'web_chunk_overlap', 200 ) ) != st.session_state[ 'web_chunk_overlap_used' ]:
					st.warning( 'Chunk settings changed. Run Chunk again before embedding.' )
				else:
					try:
						embedder, vectors = create_embeddings( st.session_state[ 'web_chunks' ],
							provider, model, model_path )
						st.session_state[ 'web_embedder' ] = embedder
						st.session_state[ 'web_embeddings' ] = vectors
						st.session_state[ 'web_embedding_provider_used' ] = provider
						st.session_state[ 'web_embedding_model_used' ] = model
						st.session_state[ 'web_embedding_model_path_used' ] = model_path
						st.session_state[ 'web_vector_store' ] = None
						st.success( f'Created {len( vectors ):,} embedding vector(s).' )
					except Exception as exc:
						st.error( str( exc ) )

		with st.expander( label='Vector Storage', icon='🗄️', expanded=False ):
			store_col, target_col = st.columns( 2 )
			with store_col:
				vector_backend = st.selectbox( 'Vector Store', options=[ 'Chroma', 'Pinecone' ],
					key='web_vector_backend' )
			with target_col:
				if vector_backend == 'Chroma':
					vector_target = st.text_input( 'Collection Name', value='mappy-web-documents',
						key='web_chroma_collection' )
				else:
					vector_target = st.text_input( 'Index Name', value='', key='web_pinecone_index' )
			if vector_backend == 'Chroma':
				persist_directory = st.text_input( 'Persistence Directory', value='stores/chroma',
					key='web_chroma_directory' )
				namespace = ''
			else:
				persist_directory = ''
				namespace = st.text_input( 'Namespace', value='', key='web_pinecone_namespace' )
			if st.button( 'Store', key='web_store_run', use_container_width=True ):
				if st.session_state[ 'web_embedder' ] is None or not st.session_state[ 'web_embeddings' ]:
					st.warning( 'Embed the current chunks before storage.' )
				elif provider != st.session_state[ 'web_embedding_provider_used' ] or \
						model != st.session_state[ 'web_embedding_model_used' ] or \
						model_path != st.session_state[ 'web_embedding_model_path_used' ]:
					st.warning( 'Embedding settings changed. Run Embed again before storage.' )
				else:
					try:
						st.session_state[ 'web_vector_store' ] = store_documents(
							st.session_state[ 'web_chunks' ], st.session_state[ 'web_embedder' ],
							vector_backend, vector_target, persist_directory, namespace )
						st.success( f'Stored {len( st.session_state[ "web_chunks" ] ):,} chunk(s).' )
					except Exception as exc:
						st.error( str( exc ) )
	with right:
		render_document_tabs( 'web_documents', 'web_chunks', 'web_embeddings', '🌐 Scraped' )



def initialize_mode_document_state( prefix: str ) -> None:
	"""Initialize per-mode document state."""
	defaults = {
		f'{prefix}_documents': [ ], f'{prefix}_chunks': [ ], f'{prefix}_embeddings': [ ],
		f'{prefix}_embedder': None, f'{prefix}_document_signature': '',
		f'{prefix}_embedding_provider_used': '', f'{prefix}_embedding_model_used': '',
		f'{prefix}_embedding_model_path_used': '',
	}
	for key, value in defaults.items( ):
		if key not in st.session_state:
			st.session_state[ key ] = value


def serialize_mode_result( result: object ) -> str:
	"""Serialize a structured API result as document text."""
	if isinstance( result, pd.DataFrame ):
		return result.to_json( orient='records', indent=2, default_handler=str )
	if isinstance( result, str ):
		return result
	return json.dumps( result, indent=2, sort_keys=True, default=str )


def sync_mode_document( prefix: str, result_key: str, source_key: str ) -> None:
	"""Synchronize the latest API result into a LangChain Document."""
	initialize_mode_document_state( prefix )
	result = st.session_state.get( result_key )
	if result is None or result == { } or result == [ ] or result == '':
		return
	text = serialize_mode_result( result )
	source = str( st.session_state.get( source_key, '' ) or prefix.title( ) )
	signature = f'{source}\n{text}'
	if signature == st.session_state[ f'{prefix}_document_signature' ]:
		return
	st.session_state[ f'{prefix}_documents' ] = [
		Document( page_content=text, metadata={ 'source': source, 'mode': prefix } ) ]
	st.session_state[ f'{prefix}_chunks' ] = [ ]
	st.session_state[ f'{prefix}_embeddings' ] = [ ]
	st.session_state[ f'{prefix}_embedder' ] = None
	st.session_state[ f'{prefix}_document_signature' ] = signature


def render_mode_processing_controls( prefix: str, result_key: str, source_key: str ) -> None:
	"""Render Foo-style chunking and embedding expanders for one API mode."""
	sync_mode_document( prefix, result_key, source_key )
	models = {
		'OpenAI': [ 'text-embedding-3-small', 'text-embedding-3-large' ],
		'Google Generative AI': [ 'gemini-embedding-2-preview' ],
		'Mistral AI': [ 'mistral-embed' ],
		'Hugging Face': [ 'sentence-transformers/all-MiniLM-L6-v2', 'sentence-transformers/all-mpnet-base-v2' ],
		'Local GGUF': [ 'Local GGUF' ],
	}
	with st.expander( '✂️ Chunking', expanded=False ):
		c1, c2 = st.columns( 2 )
		with c1:
			chunk_size = st.slider( 'Chunk Size', 100, 4000, 1000, 100,
				key=f'{prefix}_document_chunk_size' )
		with c2:
			chunk_overlap = st.slider( 'Chunk Overlap', 0, 1000, 200, 50,
				key=f'{prefix}_document_chunk_overlap' )
		if st.button( 'Chunk', key=f'{prefix}_document_chunk_run', use_container_width=True ):
			documents = st.session_state[ f'{prefix}_documents' ]
			if not documents:
				st.warning( 'Run a source request before chunking.' )
			elif chunk_overlap >= chunk_size:
				st.error( 'Chunk Overlap must be smaller than Chunk Size.' )
			else:
				splitter = RecursiveCharacterTextSplitter(
					chunk_size=int( chunk_size ), chunk_overlap=int( chunk_overlap ) )
				chunks = splitter.split_documents( documents )
				for index, document in enumerate( chunks, start=1 ):
					document.metadata = dict( document.metadata or { } )
					document.metadata[ 'chunk_id' ] = f'chunk-{index:06d}'
				st.session_state[ f'{prefix}_chunks' ] = chunks
				st.session_state[ f'{prefix}_embeddings' ] = [ ]
				st.session_state[ f'{prefix}_embedder' ] = None
	with st.expander( '🧠 Embeddings', expanded=False ):
		e1, e2 = st.columns( 2 )
		with e1:
			provider = st.selectbox( 'Embedding Provider', list( models.keys( ) ),
				index=list( models.keys( ) ).index( 'Hugging Face' ),
				key=f'{prefix}_document_embedding_provider' )
		with e2:
			model = st.selectbox( 'Embedding Model', models[ provider ],
				key=f'{prefix}_document_embedding_model' )
		model_path = ''
		if provider == 'Local GGUF':
			model_path = st.text_input( 'Local GGUF Model Path',
				placeholder=r'C:\models\embedding-model.gguf',
				key=f'{prefix}_document_embedding_model_path' )
		if st.button( 'Embed', key=f'{prefix}_document_embed_run', use_container_width=True ):
			chunks = st.session_state[ f'{prefix}_chunks' ]
			if not chunks:
				st.warning( 'Chunk the loaded result before embedding.' )
			else:
				try:
					embedder = EmbeddingFactory( ).create( provider, model, model_path )
					vectors = embedder.embed_documents( [ d.page_content for d in chunks ] )
					if len( vectors ) != len( chunks ):
						raise RuntimeError( 'Embedding count does not match the chunk count.' )
					if len( { len( vector ) for vector in vectors } ) != 1:
						raise RuntimeError( 'Embedding vectors do not have a consistent dimension.' )
					for vector in vectors:
						if not all( math.isfinite( float( value ) ) for value in vector ):
							raise RuntimeError( 'Embedding vectors contain non-finite values.' )
					st.session_state[ f'{prefix}_embedder' ] = embedder
					st.session_state[ f'{prefix}_embeddings' ] = vectors
					st.session_state[ f'{prefix}_embedding_provider_used' ] = provider
					st.session_state[ f'{prefix}_embedding_model_used' ] = model
					st.session_state[ f'{prefix}_embedding_model_path_used' ] = model_path
				except Exception as exc:
					st.error( str( exc ) )


def render_mode_document_tabs( prefix: str, loaded_label: str='📄 Loaded' ) -> None:
	"""Render Loaded, Chunks, and Embeddings tabs for one API mode."""
	initialize_mode_document_state( prefix )
	loaded_tab, chunks_tab, embeddings_tab = st.tabs(
		[ loaded_label, '✂️ Chunks', '🧠 Embeddings' ] )
	with loaded_tab:
		documents = st.session_state[ f'{prefix}_documents' ]
		if not documents:
			st.info( 'Run a source request to load a document.' )
		else:
			rows = [ {
				'Document': index, 'Source': ( document.metadata or { } ).get( 'source', '' ),
				'Characters': len( document.page_content ), 'Metadata': document.metadata or { },
				'Text': document.page_content,
			} for index, document in enumerate( documents, start=1 ) ]
			st.dataframe( pd.DataFrame( rows ), use_container_width=True, hide_index=True )
	with chunks_tab:
		chunks = st.session_state[ f'{prefix}_chunks' ]
		if not chunks:
			st.info( 'Run Chunk to display document chunks.' )
		else:
			rows = [ {
				'Chunk': index, 'Chunk ID': ( document.metadata or { } ).get( 'chunk_id', '' ),
				'Source': ( document.metadata or { } ).get( 'source', '' ),
				'Characters': len( document.page_content ), 'Text': document.page_content,
			} for index, document in enumerate( chunks, start=1 ) ]
			st.dataframe( pd.DataFrame( rows ), use_container_width=True, hide_index=True )
	with embeddings_tab:
		vectors = st.session_state[ f'{prefix}_embeddings' ]
		chunks = st.session_state[ f'{prefix}_chunks' ]
		if not vectors:
			st.info( 'Run Embed to display embedding vectors.' )
		else:
			rows = [ ]
			for index, vector in enumerate( vectors ):
				document = chunks[ index ]
				rows.append( {
					'Chunk': index + 1,
					'Provider': st.session_state[ f'{prefix}_embedding_provider_used' ],
					'Model': st.session_state[ f'{prefix}_embedding_model_path_used' ] or st.session_state[ f'{prefix}_embedding_model_used' ],
					'Dimensions': len( vector ),
					'Source': ( document.metadata or { } ).get( 'source', '' ),
					'Text': document.page_content, 'Vector': vector,
				} )
			st.dataframe( pd.DataFrame( rows ), use_container_width=True, hide_index=True )
