'''
    ******************************************************************************************
      Assembly:                Mappy
      Filename:                vector.py
      Author:                  Terry D. Eppler
      Created:                 09-08-2026
      Last Modified By:        Terry D. Eppler
      Last Modified On:        09-08-2026
    ******************************************************************************************
    <summary>
        LangChain vector-storage implementations for Mappy document chunks.
    </summary>
    ******************************************************************************************
'''
from __future__ import annotations
from pathlib import Path
from typing import List

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone


def throw_if( name: str, value: object ) -> None:
	"""Validate a required runtime value.

	Purpose:
		Ensures required vector-storage configuration is present before local or managed
		persistence work begins.

	Args:
		name (str): Argument name included in validation errors.
		value (object): Runtime value to validate.

	Returns:
		None: This function validates input and does not return a value.
	"""
	if value is None:
		raise ValueError( f'Argument "{name}" cannot be empty!' )

	if isinstance( value, str ) and not value.strip( ):
		raise ValueError( f'Argument "{name}" cannot be empty!' )

	if isinstance( value, ( list, tuple, dict, set ) ) and len( value ) == 0:
		raise ValueError( f'Argument "{name}" cannot be empty!' )


class ChromaStore( ):
	"""Persistent local Chroma vector-store wrapper."""

	documents: List[ Document ]
	embedder: Embeddings | None
	collection_name: str
	persist_directory: str
	vector_store: Chroma | None

	def __init__( self ) -> None:
		"""Initialize Chroma storage state.

		Purpose:
			Initializes reusable Chroma storage state.

		Args:
			None.

		Returns:
			None: This method initializes instance state.
		"""
		self.documents = [ ]
		self.embedder = None
		self.collection_name = ''
		self.persist_directory = ''
		self.vector_store = None

	def create( self, documents: List[ Document ], embedder: Embeddings,
		collection_name: str, persist_directory: str ) -> Chroma:
		"""Create or replace a persistent Chroma collection.

		Purpose:
			Replaces the selected Chroma collection and stores the current chunk documents using
			the embedding implementation selected in Mappy.

		Args:
			documents (List[Document]): Chunk documents to persist.
			embedder (Embeddings): LangChain embedding implementation used by Chroma.
			collection_name (str): Chroma collection name.
			persist_directory (str): Local persistence directory.

		Returns:
			Chroma: Populated Chroma vector store.
		"""
		throw_if( 'documents', documents )
		throw_if( 'embedder', embedder )
		throw_if( 'collection_name', collection_name )
		throw_if( 'persist_directory', persist_directory )
		self.documents = list( documents )
		self.embedder = embedder
		self.collection_name = collection_name
		self.persist_directory = persist_directory
		Path( self.persist_directory ).mkdir( parents=True, exist_ok=True )

		self.vector_store = Chroma(
			collection_name=self.collection_name,
			embedding_function=self.embedder,
			persist_directory=self.persist_directory,
		)
		self.vector_store.reset_collection( )
		ids = [
			str( ( document.metadata or { } ).get( 'chunk_id', f'chunk-{index:06d}' ) )
			for index, document in enumerate( self.documents, start=1 )
		]
		self.vector_store.add_documents( documents=self.documents, ids=ids )
		return self.vector_store


class PineconeStore( ):
	"""Managed Pinecone vector-store wrapper."""

	documents: List[ Document ]
	embedder: Embeddings | None
	index_name: str
	namespace: str
	api_key: str
	client: Pinecone | None
	vector_store: PineconeVectorStore | None

	def __init__( self ) -> None:
		"""Initialize Pinecone storage state.

		Purpose:
			Initializes reusable Pinecone storage state.

		Args:
			None.

		Returns:
			None: This method initializes instance state.
		"""
		self.documents = [ ]
		self.embedder = None
		self.index_name = ''
		self.namespace = ''
		self.api_key = ''
		self.client = None
		self.vector_store = None

	def create( self, documents: List[ Document ], embedder: Embeddings, index_name: str,
		namespace: str, api_key: str ) -> PineconeVectorStore:
		"""Populate an existing Pinecone index.

		Purpose:
			Validates the configured Pinecone index and stores the current chunk documents using
			the same LangChain embedding implementation used by Mappy's embedding step.

		Args:
			documents (List[Document]): Chunk documents to persist.
			embedder (Embeddings): LangChain embedding implementation used by Pinecone.
			index_name (str): Existing Pinecone index name.
			namespace (str): Optional Pinecone namespace used for the documents.
			api_key (str): Pinecone API key from environment configuration.

		Returns:
			PineconeVectorStore: Populated LangChain Pinecone vector store.
		"""
		throw_if( 'documents', documents )
		throw_if( 'embedder', embedder )
		throw_if( 'index_name', index_name )
		throw_if( 'api_key', api_key )
		self.documents = list( documents )
		self.embedder = embedder
		self.index_name = index_name
		self.namespace = namespace
		self.api_key = api_key
		self.client = Pinecone( api_key=self.api_key )

		if not self.client.indexes.exists( self.index_name ):
			raise ValueError( f'Pinecone index does not exist: {self.index_name}' )

		index = self.client.index( name=self.index_name )
		self.vector_store = PineconeVectorStore(
			index=index,
			embedding=self.embedder,
			namespace=self.namespace or None,
		)
		ids = [
			str( ( document.metadata or { } ).get( 'chunk_id', f'chunk-{index:06d}' ) )
			for index, document in enumerate( self.documents, start=1 )
		]
		self.vector_store.add_documents( documents=self.documents, ids=ids )
		return self.vector_store
