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
    Streamlit document-processing workflow shared by Mappy local document sources.
  </summary>
  ******************************************************************************************
'''
from __future__ import annotations

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
from loaders import DocumentLoaderFactory
from stores.vector import ChromaStore, PineconeStore


DOCUMENT_EXTENSIONS: Dict[ str, List[ str ] ] = {
	'Text': [ 'txt' ],
	'CSV': [ 'csv' ],
	'PDF': [ 'pdf' ],
	'Excel': [ 'xlsx', 'xls' ],
	'Word': [ 'docx' ],
	'Markdown': [ 'md', 'markdown' ],
	'HTML': [ 'html', 'htm' ],
	'JSON': [ 'json' ],
	'PowerPoint': [ 'pptx' ],
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


def initialize_document_state( ) -> None:
	"""Initialize local document-processing state.

	Purpose:
		Creates the Streamlit state required by loading, chunking, embedding, and storage.

	Returns:
		None: This function initializes session state.
	"""
	defaults = {
		'document_documents': [ ],
		'document_chunks': [ ],
		'document_embeddings': [ ],
		'document_embedder': None,
		'document_vector_store': None,
		'document_file_name': '',
		'document_loader_used': '',
		'document_chunk_size_used': 0,
		'document_chunk_overlap_used': 0,
		'document_embedding_provider_used': '',
		'document_embedding_model_used': '',
		'document_embedding_model_path_used': '',
	}
	for key, value in defaults.items( ):
		if key not in st.session_state:
			st.session_state[ key ] = value


def clear_document_state( ) -> None:
	"""Clear local document-processing state.

	Purpose:
		Clears loaded documents and all derived chunk, embedding, and vector-store state.

	Returns:
		None: This function updates session state.
	"""
	for key in [
		'document_documents',
		'document_chunks',
		'document_embeddings',
	]:
		st.session_state[ key ] = [ ]
	st.session_state[ 'document_embedder' ] = None
	st.session_state[ 'document_vector_store' ] = None
	st.session_state[ 'document_file_name' ] = ''
	st.session_state[ 'document_loader_used' ] = ''
	st.session_state[ 'document_chunk_size_used' ] = 0
	st.session_state[ 'document_chunk_overlap_used' ] = 0
	st.session_state[ 'document_embedding_provider_used' ] = ''
	st.session_state[ 'document_embedding_model_used' ] = ''
	st.session_state[ 'document_embedding_model_path_used' ] = ''


def load_uploaded_document( loader_type: str, uploaded_file: object ) -> List[ Document ]:
	"""Load an uploaded local document.

	Purpose:
		Writes the Streamlit upload to a temporary source file and routes it through the selected
		Mappy LangChain loader while preserving the original filename as source metadata.

	Args:
		loader_type: Selected document source type.
		uploaded_file: Streamlit UploadedFile instance.

	Returns:
		List[Document]: Loaded LangChain documents.
	"""
	if uploaded_file is None:
		raise ValueError( 'Select a document before loading.' )
	factory = DocumentLoaderFactory( )
	loader = factory.create( loader_type )
	suffix = Path( uploaded_file.name ).suffix
	temporary_path = ''
	try:
		with tempfile.NamedTemporaryFile( delete=False, suffix=suffix ) as handle:
			handle.write( uploaded_file.getvalue( ) )
			temporary_path = handle.name
		documents = loader.load( temporary_path )
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


def render_document_processing( ) -> None:
	"""Render Mappy's local document-processing workflow.

	Purpose:
		Provides Foo-parity local document loading for nine formats and sends the resulting
		LangChain documents through chunking, embedding, and Chroma/Pinecone storage.

	Returns:
		None: This function renders Streamlit controls and results.
	"""
	initialize_document_state( )
	st.markdown( '### 📄 Document Processing' )

	control_col, output_col = st.columns( [ 0.42, 0.58 ], border=True, gap='small' )
	with control_col:
		st.markdown( '##### Source' )
		source_col1, source_col2 = st.columns( 2 )
		with source_col1:
			loader_type = st.selectbox(
				'Document Type',
				options=list( DOCUMENT_EXTENSIONS.keys( ) ),
				key='document_loader_type' )
		with source_col2:
			uploaded_file = st.file_uploader(
				'Document',
				type=DOCUMENT_EXTENSIONS[ loader_type ],
				key='document_uploaded_file' )

		load_col, clear_col = st.columns( 2 )
		with load_col:
			load_document = st.button(
				'Load', icon='📄', key='document_load', use_container_width=True )
		with clear_col:
			clear_document = st.button(
				'Clear', icon='🧹', key='document_clear', use_container_width=True )

		if clear_document:
			clear_document_state( )
			st.rerun( )

		if load_document:
			try:
				documents = load_uploaded_document( loader_type, uploaded_file )
				if not documents:
					raise ValueError( 'The selected loader returned no documents.' )
				st.session_state[ 'document_documents' ] = documents
				st.session_state[ 'document_file_name' ] = uploaded_file.name
				st.session_state[ 'document_loader_used' ] = loader_type
				st.session_state[ 'document_chunks' ] = [ ]
				st.session_state[ 'document_embeddings' ] = [ ]
				st.session_state[ 'document_embedder' ] = None
				st.session_state[ 'document_vector_store' ] = None
				st.success( f'Loaded {len( documents ):,} LangChain document(s).' )
			except Exception as exc:
				st.error( str( exc ) )

		st.markdown( '##### Chunking' )
		chunk_col1, chunk_col2 = st.columns( 2 )
		with chunk_col1:
			chunk_size = st.slider(
				'Chunk Size', min_value=100, max_value=4000, value=1000, step=100,
				key='document_chunk_size' )
		with chunk_col2:
			chunk_overlap = st.slider(
				'Chunk Overlap', min_value=0, max_value=1000, value=200, step=50,
				key='document_chunk_overlap' )

		if st.button( 'Chunk', key='document_chunk', use_container_width=True ):
			if not st.session_state[ 'document_documents' ]:
				st.warning( 'Load a document before chunking.' )
			elif chunk_overlap >= chunk_size:
				st.error( 'Chunk Overlap must be smaller than Chunk Size.' )
			else:
				splitter = RecursiveCharacterTextSplitter(
					chunk_size=int( chunk_size ), chunk_overlap=int( chunk_overlap ) )
				chunks = splitter.split_documents( st.session_state[ 'document_documents' ] )
				for index, document in enumerate( chunks, start=1 ):
					document.metadata = dict( document.metadata or { } )
					document.metadata[ 'chunk_id' ] = f'chunk-{index:06d}'
				st.session_state[ 'document_chunks' ] = chunks
				st.session_state[ 'document_chunk_size_used' ] = int( chunk_size )
				st.session_state[ 'document_chunk_overlap_used' ] = int( chunk_overlap )
				st.session_state[ 'document_embeddings' ] = [ ]
				st.session_state[ 'document_embedder' ] = None
				st.session_state[ 'document_vector_store' ] = None
				st.success( f'Created {len( chunks ):,} chunk(s).' )

		st.markdown( '##### Embeddings' )
		embed_col1, embed_col2 = st.columns( 2 )
		with embed_col1:
			provider = st.selectbox(
				'Embedding Provider', options=list( EMBEDDING_MODELS.keys( ) ),
				index=list( EMBEDDING_MODELS.keys( ) ).index( 'Hugging Face' ),
				key='document_embedding_provider' )
		with embed_col2:
			model = st.selectbox(
				'Embedding Model', options=EMBEDDING_MODELS[ provider ],
				key='document_embedding_model' )

		model_path = ''
		if provider == 'Local GGUF':
			model_path = st.text_input(
				'Local GGUF Model Path', placeholder=r'C:\models\embedding-model.gguf',
				key='document_embedding_model_path' )

		if st.button( 'Embed', key='document_embed', use_container_width=True ):
			if not st.session_state[ 'document_chunks' ]:
				st.warning( 'Chunk the document before embedding.' )
			elif (
				int( chunk_size ) != st.session_state[ 'document_chunk_size_used' ]
				or int( chunk_overlap ) != st.session_state[ 'document_chunk_overlap_used' ]
			):
				st.warning( 'Chunk settings changed. Run Chunk again before embedding.' )
			else:
				try:
					factory = EmbeddingFactory( )
					embedder = factory.create( provider, model, model_path )
					texts = [ document.page_content for document in st.session_state[ 'document_chunks' ] ]
					vectors = embedder.embed_documents( texts )
					if len( vectors ) != len( st.session_state[ 'document_chunks' ] ):
						raise RuntimeError( 'Embedding count does not match the chunk count.' )
					dimensions = { len( vector ) for vector in vectors }
					if len( dimensions ) != 1:
						raise RuntimeError( 'Embedding vectors do not have a consistent dimension.' )
					for vector in vectors:
						if not all( math.isfinite( float( value ) ) for value in vector ):
							raise RuntimeError( 'Embedding vectors contain non-finite values.' )
					st.session_state[ 'document_embedder' ] = embedder
					st.session_state[ 'document_embeddings' ] = vectors
					st.session_state[ 'document_embedding_provider_used' ] = provider
					st.session_state[ 'document_embedding_model_used' ] = model
					st.session_state[ 'document_embedding_model_path_used' ] = model_path
					st.session_state[ 'document_vector_store' ] = None
					st.success( f'Created {len( vectors ):,} embedding vector(s).' )
				except Exception as exc:
					st.error( str( exc ) )

		st.markdown( '##### Vector Storage' )
		store_col1, store_col2 = st.columns( 2 )
		with store_col1:
			vector_backend = st.selectbox(
				'Vector Store', options=[ 'Chroma', 'Pinecone' ],
				key='document_vector_backend' )
		with store_col2:
			if vector_backend == 'Chroma':
				vector_target = st.text_input(
					'Collection Name', value='mappy-documents', key='document_chroma_collection' )
			else:
				vector_target = st.text_input(
					'Index Name', value='', key='document_pinecone_index' )

		if vector_backend == 'Chroma':
			persist_directory = st.text_input(
				'Persistence Directory', value='stores/chroma', key='document_chroma_directory' )
			namespace = ''
		else:
			persist_directory = ''
			namespace = st.text_input(
				'Namespace', value='', key='document_pinecone_namespace' )

		if st.button( 'Store', key='document_store', use_container_width=True ):
			current_model_path = model_path if provider == 'Local GGUF' else ''
			if not st.session_state[ 'document_chunks' ]:
				st.warning( 'Chunk the document before storage.' )
			elif st.session_state[ 'document_embedder' ] is None or not st.session_state[ 'document_embeddings' ]:
				st.warning( 'Embed the current chunks before storage.' )
			elif (
				provider != st.session_state[ 'document_embedding_provider_used' ]
				or model != st.session_state[ 'document_embedding_model_used' ]
				or current_model_path != st.session_state[ 'document_embedding_model_path_used' ]
			):
				st.warning( 'Embedding settings changed. Run Embed again before storage.' )
			else:
				try:
					if vector_backend == 'Chroma':
						store = ChromaStore( )
						st.session_state[ 'document_vector_store' ] = store.create(
							st.session_state[ 'document_chunks' ],
							st.session_state[ 'document_embedder' ],
							vector_target,
							persist_directory )
					else:
						api_key = getattr( cfg, 'PINECONE_API_KEY', '' ) or os.getenv( 'PINECONE_API_KEY', '' )
						store = PineconeStore( )
						st.session_state[ 'document_vector_store' ] = store.create(
							st.session_state[ 'document_chunks' ],
							st.session_state[ 'document_embedder' ],
							vector_target,
							namespace,
							api_key )
					st.success(
						f'Stored {len( st.session_state[ "document_chunks" ] ):,} chunk(s) in {vector_backend}.' )
				except Exception as exc:
					st.error( str( exc ) )

	with output_col:
		document_tab, chunks_tab, embeddings_tab = st.tabs( [
			'📄 Document', '✂️ Chunks', '🧠 Embeddings' ] )
		with document_tab:
			if not st.session_state[ 'document_documents' ]:
				st.info( 'Load a document to display LangChain documents.' )
			else:
				rows = [ ]
				for index, document in enumerate( st.session_state[ 'document_documents' ], start=1 ):
					rows.append( {
						'Document': index,
						'Source': ( document.metadata or { } ).get( 'source', '' ),
						'Loader': ( document.metadata or { } ).get( 'loader', '' ),
						'Characters': len( document.page_content ),
						'Metadata': document.metadata or { },
						'Text': document.page_content,
					} )
				st.dataframe( pd.DataFrame( rows ), use_container_width=True, hide_index=True )

		with chunks_tab:
			if not st.session_state[ 'document_chunks' ]:
				st.info( 'Run Chunk to display document chunks.' )
			else:
				rows = [ ]
				for index, document in enumerate( st.session_state[ 'document_chunks' ], start=1 ):
					rows.append( {
						'Chunk': index,
						'Chunk ID': ( document.metadata or { } ).get( 'chunk_id', '' ),
						'Source': ( document.metadata or { } ).get( 'source', '' ),
						'Characters': len( document.page_content ),
						'Text': document.page_content,
					} )
				st.dataframe( pd.DataFrame( rows ), use_container_width=True, hide_index=True )

		with embeddings_tab:
			if not st.session_state[ 'document_embeddings' ]:
				st.info( 'Run Embed to display embedding vectors.' )
			else:
				rows = [ ]
				for index, vector in enumerate( st.session_state[ 'document_embeddings' ], start=1 ):
					rows.append( {
						'Chunk': index,
						'Dimensions': len( vector ),
						'Embedding': vector,
					} )
				st.dataframe( pd.DataFrame( rows ), use_container_width=True, hide_index=True )
