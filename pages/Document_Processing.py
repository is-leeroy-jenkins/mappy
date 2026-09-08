'''
    ******************************************************************************************
      Assembly:                Mappy
      Filename:                Document_Processing.py
      Author:                  Terry D. Eppler
      Created:                 09-08-2026
      Last Modified By:        Terry D. Eppler
      Last Modified On:        09-08-2026
    ******************************************************************************************
    <summary>
        Streamlit document chunking, embedding, and vector-storage workflow.
    </summary>
    ******************************************************************************************
'''
from __future__ import annotations
import hashlib
import os
from typing import Dict, List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import pandas as pd
import streamlit as st

from documents import DocumentLoaderFactory
from embedders import EmbeddingFactory
from stores.vector import ChromaStore, PineconeStore


EMBEDDING_MODELS: Dict[ str, List[ str ] ] = {
	'OpenAI': [
		'text-embedding-3-small',
		'text-embedding-3-large',
	],
	'Google Generative AI': [
		'gemini-embedding-2-preview',
	],
	'Mistral AI': [
		'mistral-embed',
	],
	'Hugging Face': [
		'sentence-transformers/all-MiniLM-L6-v2',
		'sentence-transformers/all-mpnet-base-v2',
	],
	'Local GGUF': [
		'Local GGUF',
	],
}

LOADER_TYPES: Dict[ str, List[ str ] ] = {
	'Text Loader': [ 'txt' ],
	'CSV Loader': [ 'csv' ],
	'PDF Loader': [ 'pdf' ],
	'Excel Loader': [ 'xlsx', 'xls' ],
	'Word Document Loader': [ 'docx' ],
	'Markdown Loader': [ 'md', 'markdown' ],
	'HTML Loader': [ 'html', 'htm' ],
	'JSON Loader': [ 'json' ],
	'PowerPoint Loader': [ 'pptx' ],
}


def initialize_state( ) -> None:
	"""Initialize document-processing session state.

	Purpose:
		Creates the state containers required by loading, chunking, embedding, preview, and vector
		storage operations without overwriting values from the current document-processing session.

	Args:
		None.

	Returns:
		None: This function initializes Streamlit session state.
	"""
	defaults = {
		'document_signature': '',
		'documents': [ ],
		'chunked_documents': [ ],
		'embeddings': [ ],
		'embedder': None,
		'vector_store': None,
		'embedding_provider': 'Hugging Face',
		'embedding_model': 'sentence-transformers/all-MiniLM-L6-v2',
	}
	for key, value in defaults.items( ):
		if key not in st.session_state:
			st.session_state[ key ] = value


def clear_derived_state( ) -> None:
	"""Clear chunk, embedding, and vector-store outputs.

	Purpose:
		Prevents stale derived outputs from being reused when the active uploaded document changes.

	Args:
		None.

	Returns:
		None: This function clears derived Streamlit state.
	"""
	st.session_state.chunked_documents = [ ]
	st.session_state.embeddings = [ ]
	st.session_state.embedder = None
	st.session_state.vector_store = None


def create_signature( filename: str, content: bytes ) -> str:
	"""Create a deterministic uploaded-document signature.

	Purpose:
		Detects source changes so previously generated chunks and embeddings are not displayed or
		stored against a different file.

	Args:
		filename (str): Uploaded filename.
		content (bytes): Uploaded file content.

	Returns:
		str: SHA-256 source signature.
	"""
	value = filename.encode( 'utf-8' ) + b'|' + content
	return hashlib.sha256( value ).hexdigest( )


def create_document_frame( documents: List[ Document ] ) -> pd.DataFrame:
	"""Create the loaded-document preview dataframe.

	Purpose:
		Normalizes LangChain document content and metadata into a tabular preview for Streamlit.

	Args:
		documents (List[Document]): Loaded source documents.

	Returns:
		pd.DataFrame: Document preview rows.
	"""
	rows = [ ]
	for index, document in enumerate( documents, start=1 ):
		rows.append( {
			'Document': index,
			'Source': ( document.metadata or { } ).get( 'source', '' ),
			'Metadata': document.metadata or { },
			'Text': document.page_content,
		} )
	return pd.DataFrame( rows )


def create_chunk_frame( documents: List[ Document ] ) -> pd.DataFrame:
	"""Create the chunk preview dataframe.

	Purpose:
		Normalizes generated chunk text and metadata into a tabular Streamlit preview.

	Args:
		documents (List[Document]): Generated chunk documents.

	Returns:
		pd.DataFrame: Chunk preview rows.
	"""
	rows = [ ]
	for index, document in enumerate( documents, start=1 ):
		rows.append( {
			'Chunk': index,
			'Chunk ID': ( document.metadata or { } ).get( 'chunk_id', '' ),
			'Source': ( document.metadata or { } ).get( 'source', '' ),
			'Characters': len( document.page_content ),
			'Metadata': document.metadata or { },
			'Text': document.page_content,
		} )
	return pd.DataFrame( rows )


def create_embedding_frame( documents: List[ Document ], vectors: List[ List[ float ] ],
	provider: str, model: str ) -> pd.DataFrame:
	"""Create the embedding preview dataframe.

	Purpose:
		Pairs each chunk with its generated embedding while preserving provider, model, vector
		dimension, source text, and positional correspondence.

	Args:
		documents (List[Document]): Embedded chunk documents.
		vectors (List[List[float]]): Generated embedding vectors.
		provider (str): Selected embedding provider.
		model (str): Selected embedding model or local model identifier.

	Returns:
		pd.DataFrame: Embedding preview rows.
	"""
	rows = [ ]
	for index, vector in enumerate( vectors ):
		document = documents[ index ]
		rows.append( {
			'Chunk': index + 1,
			'Provider': provider,
			'Model': model,
			'Dimensions': len( vector ),
			'Source': ( document.metadata or { } ).get( 'source', '' ),
			'Text': document.page_content,
			'Vector': vector,
		} )
	return pd.DataFrame( rows )


st.set_page_config(
	page_title='Mappy | Document Processing',
	page_icon='🧩',
	layout='wide',
)
initialize_state( )

st.title( '🧩 Document Processing' )
st.caption( 'Load → Chunk → Embed → Store' )

left, right = st.columns( [ 0.42, 0.58 ], gap='large' )

with left:
	st.subheader( '📄 Source' )
	loader_name = st.selectbox(
		'Document Loader',
		options=list( LOADER_TYPES.keys( ) ),
		key='document_loader',
	)
	uploaded_file = st.file_uploader(
		'Upload Document',
		type=LOADER_TYPES[ loader_name ],
		key=f'document_upload_{loader_name}',
	)

	if uploaded_file is not None:
		content = uploaded_file.getvalue( )
		signature = create_signature( uploaded_file.name, content )
		if signature != st.session_state.document_signature:
			clear_derived_state( )
			st.session_state.documents = [ ]
			st.session_state.document_signature = signature

		if st.button( 'Load', use_container_width=True, key='load_document' ):
			try:
				loader = DocumentLoaderFactory( )
				st.session_state.documents = loader.load(
					uploaded_file.name,
					content,
					loader_name,
				)
				clear_derived_state( )
				st.success( f'Loaded {len( st.session_state.documents ):,} document record(s).' )
			except Exception as error:
				st.error( str( error ) )

	st.divider( )
	st.subheader( '✂️ Chunking' )
	chunk_left, chunk_right = st.columns( 2 )
	with chunk_left:
		chunk_size = st.slider(
			'Chunk Size',
			min_value=100,
			max_value=4000,
			value=1000,
			step=100,
			key='document_chunk_size',
		)
	with chunk_right:
		chunk_overlap = st.slider(
			'Chunk Overlap',
			min_value=0,
			max_value=1000,
			value=200,
			step=50,
			key='document_chunk_overlap',
		)

	if st.button( 'Chunk', use_container_width=True, key='chunk_document' ):
		if not st.session_state.documents:
			st.warning( 'Load a document before chunking.' )
		elif chunk_overlap >= chunk_size:
			st.error( 'Chunk Overlap must be smaller than Chunk Size.' )
		else:
			splitter = RecursiveCharacterTextSplitter(
				chunk_size=chunk_size,
				chunk_overlap=chunk_overlap,
			)
			chunks = splitter.split_documents( st.session_state.documents )
			for index, document in enumerate( chunks, start=1 ):
				document.metadata = dict( document.metadata or { } )
				document.metadata[ 'chunk_id' ] = f'chunk-{index:06d}'
			st.session_state.chunked_documents = chunks
			st.session_state.embeddings = [ ]
			st.session_state.embedder = None
			st.session_state.vector_store = None
			st.success( f'Created {len( chunks ):,} chunk(s).' )

	st.divider( )
	st.subheader( '🧠 Embeddings' )
	embed_left, embed_right = st.columns( 2 )
	with embed_left:
		provider = st.selectbox(
			'Embedding Provider',
			options=list( EMBEDDING_MODELS.keys( ) ),
			index=list( EMBEDDING_MODELS.keys( ) ).index( 'Hugging Face' ),
			key='document_embedding_provider',
		)
	with embed_right:
		model = st.selectbox(
			'Embedding Model',
			options=EMBEDDING_MODELS[ provider ],
			key='document_embedding_model',
		)

	model_path = ''
	if provider == 'Local GGUF':
		model_path = st.text_input(
			'Local GGUF Model Path',
			value='',
			key='document_local_gguf_path',
			placeholder=r'C:\models\embedding-model.gguf',
		)

	if st.button( 'Embed', use_container_width=True, key='embed_document' ):
		if not st.session_state.chunked_documents:
			st.warning( 'Chunk the loaded document before embedding.' )
		else:
			try:
				factory = EmbeddingFactory( )
				embedder = factory.create( provider, model, model_path )
				texts = [ document.page_content for document in st.session_state.chunked_documents ]
				vectors = embedder.embed_documents( texts )
				if len( vectors ) != len( st.session_state.chunked_documents ):
					raise RuntimeError( 'Embedding count does not match the chunk count.' )
				st.session_state.embedding_provider = provider
				st.session_state.embedding_model = model_path if provider == 'Local GGUF' else model
				st.session_state.embedder = embedder
				st.session_state.embeddings = vectors
				st.session_state.vector_store = None
				st.success( f'Created {len( vectors ):,} embedding vector(s).' )
			except Exception as error:
				st.error( str( error ) )

	st.divider( )
	st.subheader( '🗄️ Vector Storage' )
	storage_left, storage_right = st.columns( 2 )
	with storage_left:
		storage_backend = st.selectbox(
			'Vector Store',
			options=[ 'Chroma', 'Pinecone' ],
			key='document_vector_store',
		)
	with storage_right:
		if storage_backend == 'Chroma':
			collection_name = st.text_input(
				'Collection Name',
				value='mappy-documents',
				key='document_chroma_collection',
			)
		else:
			index_name = st.text_input(
				'Index Name',
				value='',
				key='document_pinecone_index',
			)

	if storage_backend == 'Chroma':
		persist_directory = st.text_input(
			'Persistence Directory',
			value='stores/chroma',
			key='document_chroma_directory',
		)
		namespace = ''
		index_name = ''
	else:
		namespace = st.text_input(
			'Namespace',
			value='',
			key='document_pinecone_namespace',
		)
		collection_name = ''
		persist_directory = ''

	if st.button( 'Store', use_container_width=True, key='store_document' ):
		if not st.session_state.chunked_documents:
			st.warning( 'Chunk the loaded document before storage.' )
		elif st.session_state.embedder is None or not st.session_state.embeddings:
			st.warning( 'Embed the current chunks before storage.' )
		else:
			try:
				if storage_backend == 'Chroma':
					store = ChromaStore( )
					st.session_state.vector_store = store.create(
						st.session_state.chunked_documents,
						st.session_state.embedder,
						collection_name,
						persist_directory,
					)
				else:
					api_key = os.getenv( 'PINECONE_API_KEY', '' )
					store = PineconeStore( )
					st.session_state.vector_store = store.create(
						st.session_state.chunked_documents,
						st.session_state.embedder,
						index_name,
						namespace,
						api_key,
					)
				st.success( f'Stored {len( st.session_state.chunked_documents ):,} chunk(s) in {storage_backend}.' )
			except Exception as error:
				st.error( str( error ) )

with right:
	document_tab, chunks_tab, embeddings_tab = st.tabs( [
		'📄 Document',
		'✂️ Chunks',
		'🧠 Embeddings',
	] )

	with document_tab:
		if st.session_state.documents:
			st.dataframe(
				create_document_frame( st.session_state.documents ),
				use_container_width=True,
				hide_index=True,
			)
		else:
			st.info( 'Load a document to view its extracted content.' )

	with chunks_tab:
		if st.session_state.chunked_documents:
			st.dataframe(
				create_chunk_frame( st.session_state.chunked_documents ),
				use_container_width=True,
				hide_index=True,
			)
		else:
			st.info( 'Chunk a loaded document to view chunk output.' )

	with embeddings_tab:
		if st.session_state.embeddings and st.session_state.chunked_documents:
			st.dataframe(
				create_embedding_frame(
					st.session_state.chunked_documents,
					st.session_state.embeddings,
					st.session_state.embedding_provider,
					st.session_state.embedding_model,
				),
				use_container_width=True,
				hide_index=True,
			)
		else:
			st.info( 'Embed the current chunks to view vector output.' )
