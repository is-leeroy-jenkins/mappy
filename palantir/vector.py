'''
    ******************************************************************************************
      Assembly:                Mappy
      Filename:                vector.py
      Author:                  Terry D. Eppler
      Created:                 09-08-2026
      Last Modified By:        Terry D. Eppler
      Last Modified On:        09-09-2026
    ******************************************************************************************
    <summary>
        LangChain vector-storage implementations for Mappy document chunks.
    </summary>
    ******************************************************************************************
'''
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from boogr import Error, Logger


def throw_if( name: str, value: object ) -> None:
	"""Validate a required runtime value.

	Purpose:
		Ensures required vector-storage configuration is present before persistence or retrieval.

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


def create_document_ids( documents: List[ Document ] ) -> List[ str ]:
	"""Create stable identifiers for document chunks.

	Purpose:
		Creates content-derived identifiers that remain stable between application runs and do not
		collide merely because separate ingestions use the same chunk ordinal.

	Args:
		documents (List[Document]): Document chunks requiring persistent identifiers.

	Returns:
		List[str]: Stable SHA-256 identifiers in document order.
	"""
	try:
		throw_if( 'documents', documents )
		identifiers: List[ str ] = [ ]
		for document in documents:
			throw_if( 'document', document )
			metadata = json.dumps( document.metadata or { }, sort_keys=True, default=str )
			content = f'{metadata}\n{document.page_content or ""}'
			identifiers.append( hashlib.sha256( content.encode( 'utf-8' ) ).hexdigest( ) )
		return identifiers
	except Error:
		raise
	except Exception as e:
		exception = Error( e )
		exception.module = 'mappy'
		exception.cause = 'VectorStore'
		exception.method = 'create_document_ids( documents: List[ Document ] ) -> List[ str ]'
		Logger( ).write( exception )
		raise exception


class ChromaStore( ):
	"""Persistent local Chroma vector-store wrapper."""

	def __init__( self ) -> None:
		"""Initialize reusable Chroma state.

		Purpose:
			Initializes document, embedding, connection, query, and filter state.

		Returns:
			None: This method initializes instance state.
		"""
		self.documents: List[ Document ] = [ ]
		self.embeddings: List[ List[ float ] ] = [ ]
		self.ids: List[ str ] = [ ]
		self.embedder: Optional[ Embeddings ] = None
		self.collection_name = ''
		self.persist_directory = ''
		self.client: Any = None
		self.collection: Any = None
		self.vector_store: Any = None
		self.query = ''
		self.limit = 0
		self.metadata_filter: Dict[ str, Any ] = { }

	def connect( self, embedder: Embeddings, collection_name: str,
		persist_directory: str ) -> Any:
		"""Open or create a Chroma collection without deleting existing records.

		Args:
			embedder (Embeddings): Embedding implementation used by the collection.
			collection_name (str): Chroma collection name.
			persist_directory (str): Local persistence directory.

		Returns:
			Any: Connected LangChain Chroma vector store.
		"""
		try:
			throw_if( 'embedder', embedder )
			throw_if( 'collection_name', collection_name )
			throw_if( 'persist_directory', persist_directory )
			self.embedder = embedder
			self.collection_name = collection_name
			self.persist_directory = persist_directory
			Path( self.persist_directory ).mkdir( parents=True, exist_ok=True )
			import chromadb
			from langchain_chroma import Chroma
			self.client = chromadb.PersistentClient( path=self.persist_directory )
			self.collection = self.client.get_or_create_collection( name=self.collection_name )
			self.vector_store = Chroma( collection_name=self.collection_name,
				embedding_function=self.embedder, client=self.client )
			return self.vector_store
		except Error:
			raise
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'ChromaStore'
			exception.method = 'connect( self, **kwargs ) -> Any'
			Logger( ).write( exception )
			raise exception

	def create( self, documents: List[ Document ], embedder: Embeddings,
		collection_name: str, persist_directory: str ) -> Any:
		"""Connect to Chroma and add documents non-destructively.

		Args:
			documents (List[Document]): Documents to store.
			embedder (Embeddings): Embedding implementation used by the collection.
			collection_name (str): Chroma collection name.
			persist_directory (str): Local persistence directory.

		Returns:
			Any: Connected and populated Chroma vector store.
		"""
		try:
			throw_if( 'documents', documents )
			self.documents = list( documents )
			self.connect( embedder, collection_name, persist_directory )
			self.add_documents( self.documents )
			return self.vector_store
		except Error:
			raise
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'ChromaStore'
			exception.method = 'create( self, **kwargs ) -> Any'
			Logger( ).write( exception )
			raise exception

	def add_documents( self, documents: List[ Document ],
		ids: Optional[ List[ str ] ] = None ) -> List[ str ]:
		"""Add or update documents using stable identifiers.

		Args:
			documents (List[Document]): Documents to embed and store.
			ids (Optional[List[str]]): Optional identifiers matching the documents.

		Returns:
			List[str]: Identifiers written to the collection.
		"""
		try:
			throw_if( 'documents', documents )
			throw_if( 'vector_store', self.vector_store )
			self.documents = list( documents )
			self.ids = list( ids ) if ids else create_document_ids( self.documents )
			if len( self.ids ) != len( self.documents ):
				raise ValueError( 'Document and identifier counts must match.' )
			return self.vector_store.add_documents( documents=self.documents, ids=self.ids )
		except Error:
			raise
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'ChromaStore'
			exception.method = 'add_documents( self, **kwargs ) -> List[ str ]'
			Logger( ).write( exception )
			raise exception

	def add_embeddings( self, documents: List[ Document ], embeddings: List[ List[ float ] ],
		ids: Optional[ List[ str ] ] = None ) -> List[ str ]:
		"""Store precomputed embeddings without embedding the documents a second time.

		Args:
			documents (List[Document]): Documents represented by the embeddings.
			embeddings (List[List[float]]): Precomputed vectors in document order.
			ids (Optional[List[str]]): Optional identifiers matching the documents.

		Returns:
			List[str]: Identifiers written to the collection.
		"""
		try:
			throw_if( 'documents', documents )
			throw_if( 'embeddings', embeddings )
			throw_if( 'vector_store', self.vector_store )
			self.documents = list( documents )
			self.embeddings = list( embeddings )
			self.ids = list( ids ) if ids else create_document_ids( self.documents )
			if len( self.documents ) != len( self.embeddings ) or len( self.ids ) != len( self.documents ):
				raise ValueError( 'Document, embedding, and identifier counts must match.' )
			self.collection.upsert( ids=self.ids, embeddings=self.embeddings,
				documents=[ document.page_content for document in self.documents ],
				metadatas=[ document.metadata or { } for document in self.documents ] )
			return self.ids
		except Error:
			raise
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'ChromaStore'
			exception.method = 'add_embeddings( self, **kwargs ) -> List[ str ]'
			Logger( ).write( exception )
			raise exception

	def similarity_search( self, query: str, limit: int = 4,
		metadata_filter: Optional[ Dict[ str, Any ] ] = None ) -> List[ Document ]:
		"""Return documents similar to a natural-language query.

		Args:
			query (str): Natural-language retrieval query.
			limit (int): Maximum result count.
			metadata_filter (Optional[Dict[str, Any]]): Optional metadata filter.

		Returns:
			List[Document]: Similar documents ordered by relevance.
		"""
		try:
			throw_if( 'query', query )
			throw_if( 'limit', limit )
			throw_if( 'vector_store', self.vector_store )
			self.query = query
			self.limit = limit
			self.metadata_filter = metadata_filter or { }
			return self.vector_store.similarity_search( self.query, k=self.limit,
				filter=self.metadata_filter or None )
		except Error:
			raise
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'ChromaStore'
			exception.method = 'similarity_search( self, **kwargs ) -> List[ Document ]'
			Logger( ).write( exception )
			raise exception

	def similarity_search_with_score( self, query: str, limit: int = 4,
		metadata_filter: Optional[ Dict[ str, Any ] ] = None ) -> List[ Tuple[ Document, float ] ]:
		"""Return similar documents with backend scores.

		Args:
			query (str): Natural-language retrieval query.
			limit (int): Maximum result count.
			metadata_filter (Optional[Dict[str, Any]]): Optional metadata filter.

		Returns:
			List[Tuple[Document, float]]: Documents and backend distance scores.
		"""
		try:
			throw_if( 'query', query )
			throw_if( 'limit', limit )
			throw_if( 'vector_store', self.vector_store )
			self.query = query
			self.limit = limit
			self.metadata_filter = metadata_filter or { }
			return self.vector_store.similarity_search_with_score( self.query, k=self.limit,
				filter=self.metadata_filter or None )
		except Error:
			raise
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'ChromaStore'
			exception.method = 'similarity_search_with_score( self, **kwargs ) -> List[ Tuple[ Document, float ] ]'
			Logger( ).write( exception )
			raise exception

	def get( self, ids: Optional[ List[ str ] ] = None,
		metadata_filter: Optional[ Dict[ str, Any ] ] = None ) -> Dict[ str, Any ]:
		"""Get records by identifier or metadata filter.

		Args:
			ids (Optional[List[str]]): Optional record identifiers.
			metadata_filter (Optional[Dict[str, Any]]): Optional metadata filter.

		Returns:
			Dict[str, Any]: Chroma collection response.
		"""
		try:
			throw_if( 'vector_store', self.vector_store )
			self.ids = list( ids ) if ids else [ ]
			self.metadata_filter = metadata_filter or { }
			return self.vector_store.get( ids=self.ids or None, where=self.metadata_filter or None )
		except Error:
			raise
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'ChromaStore'
			exception.method = 'get( self, **kwargs ) -> Dict[ str, Any ]'
			Logger( ).write( exception )
			raise exception

	def delete( self, ids: List[ str ] ) -> None:
		"""Delete selected records.

		Args:
			ids (List[str]): Record identifiers to delete.

		Returns:
			None: This method deletes records through the backend.
		"""
		try:
			throw_if( 'ids', ids )
			throw_if( 'vector_store', self.vector_store )
			self.ids = list( ids )
			self.vector_store.delete( ids=self.ids )
		except Error:
			raise
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'ChromaStore'
			exception.method = 'delete( self, ids: List[ str ] ) -> None'
			Logger( ).write( exception )
			raise exception

	def clear( self ) -> None:
		"""Explicitly remove every record from the connected collection.

		Returns:
			None: This method resets the selected collection.
		"""
		try:
			throw_if( 'vector_store', self.vector_store )
			self.vector_store.reset_collection( )
		except Error:
			raise
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'ChromaStore'
			exception.method = 'clear( self ) -> None'
			Logger( ).write( exception )
			raise exception

	def count( self ) -> int:
		"""Return the number of records in the collection.

		Returns:
			int: Current collection record count.
		"""
		try:
			throw_if( 'vector_store', self.vector_store )
			return int( self.collection.count( ) )
		except Error:
			raise
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'ChromaStore'
			exception.method = 'count( self ) -> int'
			Logger( ).write( exception )
			raise exception

	def as_retriever( self, limit: int = 4,
		metadata_filter: Optional[ Dict[ str, Any ] ] = None ) -> Any:
		"""Create a LangChain retriever for the connected collection.

		Args:
			limit (int): Maximum result count.
			metadata_filter (Optional[Dict[str, Any]]): Optional metadata filter.

		Returns:
			Any: Configured LangChain retriever.
		"""
		try:
			throw_if( 'limit', limit )
			throw_if( 'vector_store', self.vector_store )
			self.limit = limit
			self.metadata_filter = metadata_filter or { }
			search_kwargs: Dict[ str, Any ] = { 'k': self.limit }
			if self.metadata_filter:
				search_kwargs[ 'filter' ] = self.metadata_filter
			return self.vector_store.as_retriever( search_kwargs=search_kwargs )
		except Error:
			raise
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'ChromaStore'
			exception.method = 'as_retriever( self, **kwargs ) -> Any'
			Logger( ).write( exception )
			raise exception

	def health( self ) -> Dict[ str, Any ]:
		"""Return connection and collection diagnostics.

		Returns:
			Dict[str, Any]: Connection, collection, directory, and record-count status.
		"""
		try:
			return { 'connected': self.vector_store is not None,
				'collection': self.collection_name, 'records': self.count( ) if self.vector_store else 0,
				'persist_directory': self.persist_directory }
		except Error:
			raise
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'ChromaStore'
			exception.method = 'health( self ) -> Dict[ str, Any ]'
			Logger( ).write( exception )
			raise exception


class PineconeStore( ):
	"""Managed Pinecone vector-store wrapper."""

	def __init__( self ) -> None:
		"""Initialize reusable Pinecone state."""
		self.documents: List[ Document ] = [ ]
		self.embeddings: List[ List[ float ] ] = [ ]
		self.ids: List[ str ] = [ ]
		self.embedder: Optional[ Embeddings ] = None
		self.index_name = ''
		self.namespace = ''
		self.api_key = ''
		self.client: Any = None
		self.index: Any = None
		self.vector_store: Any = None
		self.query = ''
		self.limit = 0
		self.metadata_filter: Dict[ str, Any ] = { }

	def create_index( self, index_name: str, dimension: int, api_key: str,
		metric: str = 'cosine', cloud: str = 'aws', region: str = 'us-east-1' ) -> None:
		"""Create a Pinecone serverless index when it does not exist."""
		try:
			throw_if( 'index_name', index_name )
			throw_if( 'dimension', dimension )
			throw_if( 'api_key', api_key )
			throw_if( 'metric', metric )
			throw_if( 'cloud', cloud )
			throw_if( 'region', region )
			self.index_name = index_name
			self.dimension = dimension
			self.api_key = api_key
			self.metric = metric
			self.cloud = cloud
			self.region = region
			from pinecone import Pinecone, ServerlessSpec
			self.client = Pinecone( api_key=self.api_key )
			if not self.client.has_index( self.index_name ):
				self.client.create_index( name=self.index_name, dimension=self.dimension,
					metric=self.metric, spec=ServerlessSpec( cloud=self.cloud, region=self.region ) )
			else:
				description = self.client.describe_index( self.index_name )
				if int( description.dimension ) != int( self.dimension ):
					raise ValueError( f'Pinecone index dimension {description.dimension} does not match '
						f'embedding dimension {self.dimension}.' )
				if str( description.metric ) != self.metric:
					raise ValueError( f'Pinecone index metric {description.metric} does not match '
						f'required metric {self.metric}.' )
		except Error:
			raise
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'PineconeStore'
			exception.method = 'create_index( self, **kwargs ) -> None'
			Logger( ).write( exception )
			raise exception

	def wait_until_ready( self, index_name: str, api_key: str, timeout: int = 120 ) -> None:
		"""Wait for a Pinecone index to report ready status."""
		try:
			throw_if( 'index_name', index_name )
			throw_if( 'api_key', api_key )
			throw_if( 'timeout', timeout )
			self.index_name = index_name
			self.api_key = api_key
			self.timeout = timeout
			from pinecone import Pinecone
			self.client = self.client or Pinecone( api_key=self.api_key )
			started = time.monotonic( )
			while time.monotonic( ) - started < self.timeout:
				description = self.client.describe_index( self.index_name )
				if bool( description.status.ready ):
					return
				time.sleep( 1 )
			raise TimeoutError( f'Pinecone index was not ready within {self.timeout} seconds.' )
		except Error:
			raise
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'PineconeStore'
			exception.method = 'wait_until_ready( self, **kwargs ) -> None'
			Logger( ).write( exception )
			raise exception

	def connect( self, embedder: Embeddings, index_name: str, namespace: str,
		api_key: str ) -> Any:
		"""Connect to an existing Pinecone index and namespace."""
		try:
			throw_if( 'embedder', embedder )
			throw_if( 'index_name', index_name )
			throw_if( 'api_key', api_key )
			self.embedder = embedder
			self.index_name = index_name
			self.namespace = namespace
			self.api_key = api_key
			from langchain_pinecone import PineconeVectorStore
			from pinecone import Pinecone
			self.client = Pinecone( api_key=self.api_key )
			if not self.client.has_index( self.index_name ):
				raise ValueError( f'Pinecone index does not exist: {self.index_name}' )
			description = self.client.describe_index( self.index_name )
			self.index = self.client.Index( host=description.host )
			self.vector_store = PineconeVectorStore( index=self.index, embedding=self.embedder,
				namespace=self.namespace or None )
			return self.vector_store
		except Error:
			raise
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'PineconeStore'
			exception.method = 'connect( self, **kwargs ) -> Any'
			Logger( ).write( exception )
			raise exception

	def create( self, documents: List[ Document ], embedder: Embeddings, index_name: str,
		namespace: str, api_key: str ) -> Any:
		"""Connect to Pinecone and add documents to an existing index."""
		try:
			throw_if( 'documents', documents )
			self.documents = list( documents )
			self.connect( embedder, index_name, namespace, api_key )
			self.add_documents( self.documents )
			return self.vector_store
		except Error:
			raise
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'PineconeStore'
			exception.method = 'create( self, **kwargs ) -> Any'
			Logger( ).write( exception )
			raise exception

	def add_documents( self, documents: List[ Document ],
		ids: Optional[ List[ str ] ] = None ) -> List[ str ]:
		"""Add or update documents using stable identifiers."""
		try:
			throw_if( 'documents', documents )
			throw_if( 'vector_store', self.vector_store )
			self.documents = list( documents )
			self.ids = list( ids ) if ids else create_document_ids( self.documents )
			if len( self.ids ) != len( self.documents ):
				raise ValueError( 'Document and identifier counts must match.' )
			return self.vector_store.add_documents( documents=self.documents, ids=self.ids )
		except Error:
			raise
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'PineconeStore'
			exception.method = 'add_documents( self, **kwargs ) -> List[ str ]'
			Logger( ).write( exception )
			raise exception

	def add_embeddings( self, documents: List[ Document ], embeddings: List[ List[ float ] ],
		ids: Optional[ List[ str ] ] = None ) -> List[ str ]:
		"""Upsert precomputed document embeddings without embedding a second time."""
		try:
			throw_if( 'documents', documents )
			throw_if( 'embeddings', embeddings )
			throw_if( 'index', self.index )
			self.documents = list( documents )
			self.embeddings = list( embeddings )
			self.ids = list( ids ) if ids else create_document_ids( self.documents )
			if len( self.documents ) != len( self.embeddings ) or len( self.ids ) != len( self.documents ):
				raise ValueError( 'Document, embedding, and identifier counts must match.' )
			vectors = [ ]
			for identifier, embedding, document in zip( self.ids, self.embeddings, self.documents ):
				metadata = dict( document.metadata or { } )
				metadata[ 'text' ] = document.page_content
				vectors.append( { 'id': identifier, 'values': embedding, 'metadata': metadata } )
			self.index.upsert( vectors=vectors, namespace=self.namespace or '' )
			return self.ids
		except Error:
			raise
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'PineconeStore'
			exception.method = 'add_embeddings( self, **kwargs ) -> List[ str ]'
			Logger( ).write( exception )
			raise exception

	def similarity_search( self, query: str, limit: int = 4,
		metadata_filter: Optional[ Dict[ str, Any ] ] = None ) -> List[ Document ]:
		"""Return documents similar to a natural-language query."""
		try:
			throw_if( 'query', query )
			throw_if( 'limit', limit )
			throw_if( 'vector_store', self.vector_store )
			self.query = query
			self.limit = limit
			self.metadata_filter = metadata_filter or { }
			return self.vector_store.similarity_search( self.query, k=self.limit,
				filter=self.metadata_filter or None )
		except Error:
			raise
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'PineconeStore'
			exception.method = 'similarity_search( self, **kwargs ) -> List[ Document ]'
			Logger( ).write( exception )
			raise exception

	def similarity_search_with_score( self, query: str, limit: int = 4,
		metadata_filter: Optional[ Dict[ str, Any ] ] = None ) -> List[ Tuple[ Document, float ] ]:
		"""Return similar documents with backend scores."""
		try:
			throw_if( 'query', query )
			throw_if( 'limit', limit )
			throw_if( 'vector_store', self.vector_store )
			self.query = query
			self.limit = limit
			self.metadata_filter = metadata_filter or { }
			return self.vector_store.similarity_search_with_score( self.query, k=self.limit,
				filter=self.metadata_filter or None )
		except Error:
			raise
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'PineconeStore'
			exception.method = 'similarity_search_with_score( self, **kwargs ) -> List[ Tuple[ Document, float ] ]'
			Logger( ).write( exception )
			raise exception

	def get( self, ids: List[ str ] ) -> Dict[ str, Any ]:
		"""Fetch records by identifier."""
		try:
			throw_if( 'ids', ids )
			throw_if( 'index', self.index )
			self.ids = list( ids )
			response = self.index.fetch( ids=self.ids, namespace=self.namespace or '' )
			return response.to_dict( ) if hasattr( response, 'to_dict' ) else dict( response )
		except Error:
			raise
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'PineconeStore'
			exception.method = 'get( self, ids: List[ str ] ) -> Dict[ str, Any ]'
			Logger( ).write( exception )
			raise exception

	def delete( self, ids: List[ str ] ) -> None:
		"""Delete selected records."""
		try:
			throw_if( 'ids', ids )
			throw_if( 'index', self.index )
			self.ids = list( ids )
			self.index.delete( ids=self.ids, namespace=self.namespace or '' )
		except Error:
			raise
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'PineconeStore'
			exception.method = 'delete( self, ids: List[ str ] ) -> None'
			Logger( ).write( exception )
			raise exception

	def delete_by_filter( self, metadata_filter: Dict[ str, Any ] ) -> None:
		"""Delete records matching a metadata filter."""
		try:
			throw_if( 'metadata_filter', metadata_filter )
			throw_if( 'index', self.index )
			self.metadata_filter = dict( metadata_filter )
			self.index.delete( filter=self.metadata_filter, namespace=self.namespace or '' )
		except Error:
			raise
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'PineconeStore'
			exception.method = 'delete_by_filter( self, **kwargs ) -> None'
			Logger( ).write( exception )
			raise exception

	def clear( self ) -> None:
		"""Explicitly remove every record from the connected namespace."""
		try:
			throw_if( 'index', self.index )
			self.index.delete( delete_all=True, namespace=self.namespace or '' )
		except Error:
			raise
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'PineconeStore'
			exception.method = 'clear( self ) -> None'
			Logger( ).write( exception )
			raise exception

	def count( self ) -> int:
		"""Return the number of records in the connected namespace."""
		try:
			throw_if( 'index', self.index )
			stats = self.index.describe_index_stats( )
			namespaces = stats.namespaces or { }
			namespace = namespaces.get( self.namespace or '', { } )
			return int( getattr( namespace, 'vector_count', 0 ) if not isinstance( namespace, dict )
				else namespace.get( 'vector_count', 0 ) )
		except Error:
			raise
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'PineconeStore'
			exception.method = 'count( self ) -> int'
			Logger( ).write( exception )
			raise exception

	def as_retriever( self, limit: int = 4,
		metadata_filter: Optional[ Dict[ str, Any ] ] = None ) -> Any:
		"""Create a LangChain retriever for the connected namespace."""
		try:
			throw_if( 'limit', limit )
			throw_if( 'vector_store', self.vector_store )
			self.limit = limit
			self.metadata_filter = metadata_filter or { }
			search_kwargs: Dict[ str, Any ] = { 'k': self.limit }
			if self.metadata_filter:
				search_kwargs[ 'filter' ] = self.metadata_filter
			return self.vector_store.as_retriever( search_kwargs=search_kwargs )
		except Error:
			raise
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'PineconeStore'
			exception.method = 'as_retriever( self, **kwargs ) -> Any'
			Logger( ).write( exception )
			raise exception

	def health( self ) -> Dict[ str, Any ]:
		"""Return connection and namespace diagnostics."""
		try:
			return { 'connected': self.vector_store is not None, 'index': self.index_name,
				'namespace': self.namespace, 'records': self.count( ) if self.index else 0 }
		except Error:
			raise
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'PineconeStore'
			exception.method = 'health( self ) -> Dict[ str, Any ]'
			Logger( ).write( exception )
			raise exception
