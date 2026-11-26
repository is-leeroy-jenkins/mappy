'''
  ******************************************************************************************
      Assembly:                Iyrin
      Filename:                storage.py
      Author:                  Terry D. Eppler
      Created:                 05-31-2022

      Last Modified By:        Terry D. Eppler
      Last Modified On:        05-01-2025
  ******************************************************************************************
  <copyright file="storage.py" company="Terry D. Eppler">

	     Iyrin is a python framework encapsulating the Google Maps functionality.
	     Copyright ©  2022  Terry Eppler

     Permission is hereby granted, free of charge, to any person obtaining a copy
     of this software and associated documentation files (the “Software”),
     to deal in the Software without restriction,
     including without limitation the rights to use,
     copy, modify, merge, publish, distribute, sublicense,
     and/or sell copies of the Software,
     and to permit persons to whom the Software is furnished to do so,
     subject to the following conditions:

     The above copyright notice and this permission notice shall be included in all
     copies or substantial portions of the Software.

     THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
     INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
     FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT.
     IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
     DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
     ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
     DEALINGS IN THE SOFTWARE.

     You can contact me at:  terryeppler@gmail.com or eppler.terry@epa.gov

  </copyright>
  <summary>
    storage.py
  </summary>
  ******************************************************************************************
  '''
import json
import os
import sqlite3
import time
import config as cfg
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import re
from pathlib import Path
from typing import Any, List, Dict, Optional, Tuple
from boogr import Error, Logger
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

def throw_if( name: str, value: object ) -> None:
	"""
		Validate that a required value is not empty.

	Purpose:
		Validate that a required value is not empty.

	Args:
		name (str): Name of the argument being validated.
		value (object): Value to validate.

	Returns:
		None: Validates the required argument and raises for empty values.
		"""
	if value is None:
		raise ValueError( f'Argument "{name}" cannot be empty!' )
	if isinstance( value, str ) and not value.strip( ):
		raise ValueError( f'Argument "{name}" cannot be empty!' )
	if isinstance( value, (list, tuple, dict, set) ) and len( value ) == 0:
		raise ValueError( f'Argument "{name}" cannot be empty!' )

def normalize( obj: Any ) -> Any:
	"""Convert an external payload into JSON-compatible Python values.

	Purpose:
		Preserves scalar values and recursively converts collections, while supporting
		objects exposing a model_dump method at the external data boundary.

	Args:
		obj (Any): Object returned by a loader, API, or provider.

	Returns:
		Any: Scalar, collection, or text representation suitable for serialization.
	"""
	if obj is None or isinstance( obj, (str, int, float, bool) ):
		return obj
	if isinstance( obj, dict ):
		return { k: normalize( v ) for k, v in obj.items( ) }
	if isinstance( obj, (list, tuple, set) ):
		return [ normalize( v ) for v in obj ]
	try:
		return obj.model_dump( )
	except AttributeError:
		return str( obj )
	except Exception:
		return str( obj )

def blue_divider( ) -> None:
	"""Render the configured Streamlit divider.

	Purpose:
		Displays the application divider without altering any persisted data.

	Returns:
		None: Renders a divider in the active Streamlit container.
	"""
	st.markdown( cfg.BLUE_DIVIDER, unsafe_allow_html=True )

class BaseCache( ):
	"""BaseCache persistence interface.

	Purpose:
		Defines the cache interface for dictionaries, expiration, and namespace keys.

	Attributes:
		None: The abstract interface has no declared instance attributes.
	"""
	
	def get( self, key: str ) -> Optional[ Dict[ str, Any ] ]:
		"""Retrieve an entry by its cache key.

		Purpose:
			Retrieve an entry by its cache key.

		Args:
			key (str): Cache key identifying the record.

		Returns:
			Optional[ Dict[ str, Any ] ]: Result of the get operation.
		"""
		raise NotImplementedError
	
	def set( self, key: str, value: Dict[ str, Any ], ttl: Optional[ int ] = None ) -> None:
		"""Store a key/value pair with an optional time-to-live.

		Purpose:
			Store a key/value pair with an optional time-to-live.

		Args:
			key (str): Cache key identifying the record.
			value (Dict[ str, Any ]): Value or user-entered filter value.
			ttl (Optional[ int ]): Optional time-to-live in seconds.

		Returns:
			None: Completes the operation through side effects.
		"""
		raise NotImplementedError
	
	def delete( self, key: str ) -> None:
		"""Remove a cache entry.

		Purpose:
			Remove a cache entry.

		Args:
			key (str): Cache key identifying the record.

		Returns:
			None: Completes the operation through side effects.
		"""
		raise NotImplementedError
	
	def clear( self, namespace: Optional[ str ] = None ) -> None:
		"""Clear entries matching an optional namespace.

		Purpose:
			Clear entries matching an optional namespace.

		Args:
			namespace (Optional[ str ]): Optional cache namespace.

		Returns:
			None: Completes the operation through side effects.
		"""
		raise NotImplementedError
	
	def contains( self, key: str ) -> bool:
		"""Determine whether a cache entry exists.

		Purpose:
			Determine whether a cache entry exists.

		Args:
			key (str): Cache key identifying the record.

		Returns:
			bool: Result of the contains operation.
		"""
		try:
			throw_if( 'key', key )
			return self.get( key ) is not None
		except Exception as e:
			exception = Error( e )
			exception.module = 'storage'
			exception.cause = 'BaseCache'
			exception.method = "contains( self, key: str ) -> bool"
			Logger( ).write( exception )
			raise exception
	
	def namespace_key( self, namespace: str, key: str ) -> str:
		"""
			Create a cache key prefixed by a namespace.

		Purpose:
			Create a cache key prefixed by a namespace.

		Args:
			namespace (str): Logical cache namespace, such as geocode, places, weather,
				distance, or fetcher.

			key (str): Raw cache key.

		Returns:
			str: Namespace-qualified cache key.
		"""
		try:
			throw_if( 'namespace', namespace )
			throw_if( 'key', key )
			return f'{namespace}::{key}'
		except Exception as e:
			exception = Error( e )
			exception.module = 'storage'
			exception.cause = 'BaseCache'
			exception.method = "namespace_key( self, namespace: str, key: str ) -> str"
			Logger( ).write( exception )
			raise exception
	
	def stats( self ) -> Dict[ str, Any ]:
		"""Return cache usage and diagnostic statistics.

		Purpose:
			Return cache usage and diagnostic statistics.

		Returns:
			Dict[ str, Any ]: Result of the stats operation.
		"""
		raise NotImplementedError

class InMemoryCache( BaseCache ):
	"""InMemoryCache persistence interface.

	Purpose:
		Caches records in memory and tracks cache use, writes, and deletions.

	Attributes:
		store (Dict[str, Dict[str, Any]]): Internal cache record dictionary.
		hits (int): Successful cache reads.
		misses (int): Unsuccessful cache reads.
		sets (int): Cache writes.
		deletes (int): Deleted cache entries.
	"""
	store: Dict[ str, Dict[ str, Any ] ]
	hits: int
	misses: int
	sets: int
	deletes: int
	
	def __init__( self ) -> None:
		"""Initialize empty cache records and operation counters.

		Purpose:
			Initialize empty cache records and operation counters.

		Returns:
			None: Completes the operation through side effects.
		"""
		self.store = { }
		self.hits = 0
		self.misses = 0
		self.sets = 0
		self.deletes = 0
	
	def now( self ) -> float:
		"""
			Return the current Unix timestamp.

		Purpose:
			Return the current Unix timestamp.

		Returns:
			float: Current Unix timestamp.
		"""
		try:
			return time.time( )
		except Exception as e:
			exception = Error( e )
			exception.module = 'storage'
			exception.cause = 'InMemoryCache'
			exception.method = "now( self ) -> float"
			Logger( ).write( exception )
			raise exception
	
	def make_record( self, key: str, value: Dict[ str, Any ], ttl: Optional[ int ] = None ) -> Dict[
		str, Any ]:
		"""
			Create a cache metadata record for the supplied key and value.

		Purpose:
			Create a cache metadata record for the supplied key and value.

		Args:
			key (str): Cache key.

			value (Dict[str, Any]): JSON-serializable cache value.

			ttl (Optional[int]): Optional time-to-live in seconds.

		Returns:
			Dict[str, Any]: Cache metadata record.
		"""
		try:
			throw_if( 'key', key )
			throw_if( 'value', value )
			now_value = self.now( )
			ttl_value = int( ttl ) if ttl is not None and int( ttl ) > 0 else None
			expires_value = now_value + ttl_value if ttl_value else None
			return { 'key': key, 'value': value, 'created_at': now_value, 'updated_at': now_value,
				'expires_at': expires_value, 'hit_count': 0, 'last_accessed': None }
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'storage'
			exception.cause = 'InMemoryCache'
			exception.method = (
				"make_record( self, key: str, value: Dict[ str, Any ], ttl: Optional[ int ] = None ) "
				"-> Dict[ str, Any ]:")
			Logger( ).write( exception )
			raise exception
	
	def is_expired( self, record: Dict[ str, Any ] ) -> bool:
		"""
			Determine whether an in-memory cache record has expired.

		Purpose:
			Determine whether an in-memory cache record has expired.

		Args:
			record (Dict[str, Any]): Cache metadata record.

		Returns:
			bool: True if expired; otherwise False.
		"""
		try:
			throw_if( 'record', record )
			expires_at = record.get( 'expires_at' )
			if expires_at is None:
				return False
			return float( expires_at ) <= self.now( )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'storage'
			exception.cause = 'InMemoryCache'
			exception.method = "is_expired( self, record: Dict[ str, Any ] ) -> bool"
			Logger( ).write( exception )
			raise exception
	
	def get( self, key: str ) -> Optional[ Dict[ str, Any ] ]:
		"""
			Return a cached value by key when present and not expired.

		Purpose:
			Return a cached value by key when present and not expired.

		Args:
			key (str): Cache key.

		Returns:
			Optional[Dict[str, Any]]: Cached value or None.
		"""
		try:
			throw_if( 'key', key )
			record = self.store.get( key )
			if not record:
				self.misses += 1
				return None
			if self.is_expired( record ):
				self.delete( key )
				self.misses += 1
				return None
			record[ 'hit_count' ] = int( record.get( 'hit_count', 0 ) or 0 ) + 1
			record[ 'last_accessed' ] = self.now( )
			self.hits += 1
			return record.get( 'value' )
		except Exception as e:
			exception = Error( e )
			exception.module = 'storage'
			exception.cause = 'InMemoryCache'
			exception.method = "get( self, key: str ) -> Optional[ Dict[ str, Any ] ]"
			Logger( ).write( exception )
			raise exception
	
	def set( self, key: str, value: Dict[ str, Any ], ttl: Optional[ int ] = None ) -> None:
		"""
			Set a cache value by key.

		Purpose:
			Set a cache value by key.

		Args:
			key (str): Cache key.

			value (Dict[str, Any]): JSON-serializable cache value.

			ttl (Optional[int]): Optional time-to-live in seconds.

		Returns:
			None.
		"""
		try:
			throw_if( 'key', key )
			throw_if( 'value', value )
			self.store[ key ] = self.make_record( key, value, ttl )
			self.sets += 1
		except Exception as e:
			exception = Error( e )
			exception.module = 'storage'
			exception.cause = 'InMemoryCache'
			exception.method = "set( self, key: str, value: Dict[ str, Any ], ttl: Optional[ int ] = None ) -> None"
			Logger( ).write( exception )
			raise exception
	
	def delete( self, key: str ) -> None:
		"""
			Delete a cache entry by key.

		Purpose:
			Delete a cache entry by key.

		Args:
			key (str): Cache key.

		Returns:
			None.
		"""
		try:
			throw_if( 'key', key )
			if key in self.store:
				del self.store[ key ]
				self.deletes += 1
		except Exception as e:
			exception = Error( e )
			exception.module = 'storage'
			exception.cause = 'InMemoryCache'
			exception.method = "delete( self, key: str ) -> None"
			Logger( ).write( exception )
			raise exception
	
	def clear( self, namespace: Optional[ str ] = None ) -> None:
		"""
			Clear all cache entries or only entries under a namespace prefix.

		Purpose:
			Clear all cache entries or only entries under a namespace prefix.

		Args:
			namespace (Optional[str]): Optional namespace prefix.

		Returns:
			None.
		"""
		try:
			if namespace:
				prefix = f'{namespace}::'
				keys = [ key for key in self.store if key.startswith( prefix ) ]
				for key in keys:
					self.delete( key )
			else:
				deleted = len( self.store )
				self.store.clear( )
				self.deletes += deleted
		except Exception as e:
			exception = Error( e )
			exception.module = 'storage'
			exception.cause = 'InMemoryCache'
			exception.method = "clear( self, namespace: Optional[ str ] = None ) -> None"
			Logger( ).write( exception )
			raise exception
	
	def contains( self, key: str ) -> bool:
		"""
			Determine whether a cache key exists and is not expired.

		Purpose:
			Determine whether a cache key exists and is not expired.

		Args:
			key (str): Cache key.

		Returns:
			bool: True if the key exists and is not expired.
		"""
		try:
			throw_if( 'key', key )
			return self.get( key ) is not None
		except Exception as e:
			exception = Error( e )
			exception.module = 'storage'
			exception.cause = 'InMemoryCache'
			exception.method = "contains( self, key: str ) -> bool"
			Logger( ).write( exception )
			raise exception
	
	def stats( self ) -> Dict[ str, Any ]:
		"""
			Return cache diagnostics.

		Purpose:
			Return cache diagnostics.

		Returns:
			Dict[str, Any]: Cache diagnostics.
		"""
		try:
			expired = 0
			for record in self.store.values( ):
				if self.is_expired( record ):
					expired += 1
			return { 'backend': 'memory', 'entries': len( self.store ), 'expired_entries': expired,
				'hits': self.hits, 'misses': self.misses, 'sets': self.sets,
				'deletes': self.deletes }
		except Exception as e:
			exception = Error( e )
			exception.module = 'storage'
			exception.cause = 'InMemoryCache'
			exception.method = "stats( self ) -> Dict[ str, Any ]"
			Logger( ).write( exception )
			raise exception

class SQLiteCache( BaseCache ):
	"""SQLiteCache persistence interface.

	Purpose:
		Persists cache records and time-to-live metadata in an on-disk SQLite database.

	Attributes:
		path (Optional[str]): SQLite cache file path.
		connection (sqlite3.Connection): Active SQLite cache connection.
	"""
	path: Optional[ str ]
	connection: sqlite3.Connection
	
	def __init__( self, path: str = 'mappy_cache.sqlite' ) -> None:
		"""Open the SQLite cache file and initialize its schema.

		Purpose:
			Open the SQLite cache file and initialize its schema.

		Args:
			path (str): SQLite database filename.

		Returns:
			None: Completes the operation through side effects.
		"""
		self.path = path
		d = os.path.dirname( self.path )
		if d:
			os.makedirs( d, exist_ok=True )
		self.connection = sqlite3.connect( self.path )
		self.initialize( )
	
	def initialize( self ) -> None:
		"""
			Create the SQLite cache table when it does not already exist.

		Purpose:
			Create the SQLite cache table when it does not already exist.

		Returns:
			None.
		"""
		try:
			self.connection.execute( '''
                                     CREATE TABLE IF NOT EXISTS kv
                                     (
                                         k
                                         TEXT
                                         PRIMARY
                                         KEY,
                                         v
                                         TEXT
                                         NOT
                                         NULL,
                                         created_at
                                         REAL,
                                         updated_at
                                         REAL,
                                         expires_at
                                         REAL,
                                         hit_count
                                         INTEGER
                                         DEFAULT
                                         0,
                                         last_accessed
                                         REAL
                                     ) ''' )
			self.migrate( )
			self.connection.commit( )
		except Exception as e:
			exception = Error( e )
			exception.module = 'storage'
			exception.cause = 'SQLiteCache'
			exception.method = "initialize( self ) -> None"
			Logger( ).write( exception )
			raise exception
	
	def migrate( self ) -> None:
		"""
			Add metadata columns to older kv tables that only contain k and v.

		Purpose:
			Add metadata columns to older kv tables that only contain k and v.

		Returns:
			None.
		"""
		try:
			cursor = self.connection.execute( 'PRAGMA table_info(kv)' )
			columns = { row[ 1 ] for row in cursor.fetchall( ) }
			additions = { 'created_at': 'ALTER TABLE kv ADD COLUMN created_at REAL',
				'updated_at': 'ALTER TABLE kv ADD COLUMN updated_at REAL',
				'expires_at': 'ALTER TABLE kv ADD COLUMN expires_at REAL',
				'hit_count': 'ALTER TABLE kv ADD COLUMN hit_count INTEGER DEFAULT 0',
				'last_accessed': 'ALTER TABLE kv ADD COLUMN last_accessed REAL' }
			for column, sql in additions.items( ):
				if column not in columns:
					self.connection.execute( sql )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'storage'
			exception.cause = 'SQLiteCache'
			exception.method = "migrate( self ) -> None"
			Logger( ).write( exception )
			raise exception
	
	def now( self ) -> float:
		"""
			Return the current Unix timestamp.

		Purpose:
			Return the current Unix timestamp.

		Returns:
			float: Current Unix timestamp.
		"""
		try:
			return time.time( )
		except Exception as e:
			exception = Error( e )
			exception.module = 'storage'
			exception.cause = 'SQLiteCache'
			exception.method = "now( self ) -> float"
			Logger( ).write( exception )
			raise exception
	
	def get( self, key: str ) -> Optional[ Dict[ str, Any ] ]:
		"""
			Return a cached value by key when present and not expired.

		Purpose:
			Return a cached value by key when present and not expired.

		Args:
			key (str): Cached value or None.

		Returns:
			Optional[ Dict[ str, Any ] ]: Result of the get operation.
		"""
		try:
			throw_if( 'key', key )
			statement = 'SELECT v, expires_at, hit_count FROM kv WHERE k = ?'
			cursor = self.connection.execute( statement, (key,) )
			row = cursor.fetchone( )
			if not row:
				return None
			payload = row[ 0 ]
			expires_at = row[ 1 ]
			hit_count = int( row[ 2 ] or 0 )
			if expires_at is not None and float( expires_at ) <= self.now( ):
				self.delete( key )
				return None
			self.connection.execute( 'UPDATE kv SET hit_count = ?, last_accessed = ? WHERE k = ?', (
				hit_count + 1, self.now( ), key) )
			self.connection.commit( )
			return json.loads( payload )
		except Exception as e:
			exception = Error( e )
			exception.module = 'storage'
			exception.cause = 'SQLiteCache'
			exception.method = "get( self, key: str ) -> Optional[ Dict[ str, Any ] ]"
			Logger( ).write( exception )
			raise exception
	
	def set( self, key: str, value: Dict[ str, Any ], ttl: Optional[ int ] = None ) -> None:
		"""
			Set a cache value by key.

		Purpose:
			Set a cache value by key.

		Args:
			key (str): Cache key.
			value (Dict[str, Any]): JSON-serializable cache value.
			ttl (Optional[int]): Optional time-to-live in seconds.

		Returns:
			None.
		"""
		try:
			throw_if( 'key', key )
			throw_if( 'value', value )
			now_value = self.now( )
			ttl_value = int( ttl ) if ttl is not None and int( ttl ) > 0 else None
			expires_value = now_value + ttl_value if ttl_value else None
			payload = json.dumps( value, ensure_ascii=False )
			self.connection.execute( ''' INSERT INTO kv
                                         (k, v, created_at, updated_at, expires_at, hit_count,
                                          last_accessed)
                                         VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(k) DO
            UPDATE SET
                v = excluded.v,
                updated_at = excluded.updated_at,
                expires_at = excluded.expires_at
			                         ''', (key, payload, now_value, now_value, expires_value, 0,
				None) )
			self.connection.commit( )
		except Exception as e:
			exception = Error( e )
			exception.module = 'storage'
			exception.cause = 'SQLiteCache'
			exception.method = "set( self, key: str, value: Dict[ str, Any ], ttl: Optional[ int ]=None ) -> None"
			Logger( ).write( exception )
			raise exception
	
	def delete( self, key: str ) -> None:
		"""
			Delete a cache entry by key.

		Purpose:
			Delete a cache entry by key.

		Args:
			key (str): Cache key.

		Returns:
			None.
		"""
		try:
			throw_if( 'key', key )
			self.connection.execute( 'DELETE FROM kv WHERE k = ?', (key,) )
			self.connection.commit( )
		except Exception as e:
			exception = Error( e )
			exception.module = 'storage'
			exception.cause = 'SQLiteCache'
			exception.method = "delete( self, key: str ) -> None"
			Logger( ).write( exception )
			raise exception
	
	def clear( self, namespace: Optional[ str ] = None ) -> None:
		"""
			Clear all cache entries or only entries under a namespace prefix.

		Purpose:
			Clear all cache entries or only entries under a namespace prefix.

		Args:
			namespace (Optional[str]): Optional namespace prefix.

		Returns:
			None.
		"""
		try:
			if namespace:
				prefix = f'{namespace}::%'
				self.connection.execute( 'DELETE FROM kv WHERE k LIKE ?', (prefix,) )
			else:
				self.connection.execute( 'DELETE FROM kv' )
			self.connection.commit( )
		except Exception as e:
			exception = Error( e )
			exception.module = 'storage'
			exception.cause = 'SQLiteCache'
			exception.method = "clear( self, namespace: Optional[ str ]=None ) -> None"
			Logger( ).write( exception )
			raise exception
	
	def contains( self, key: str ) -> bool:
		"""
			Determine whether a cache key exists and is not expired.

		Purpose:
			Determine whether a cache key exists and is not expired.

		Args:
			key (str): Cache key.

		Returns:
			bool: True if the key exists and is not expired.
		"""
		try:
			throw_if( 'key', key )
			return self.get( key ) is not None
		except Exception as e:
			exception = Error( e )
			exception.module = 'storage'
			exception.cause = 'SQLiteCache'
			exception.method = "contains( self, key: str ) -> bool"
			Logger( ).write( exception )
			raise exception
	
	def purge_expired( self ) -> int:
		"""
			Delete expired cache entries.

		Purpose:
			Delete expired cache entries.

		Returns:
			int: Number of rows deleted.
		"""
		try:
			cursor = self.connection.execute( 'SELECT COUNT(*) FROM kv WHERE expires_at IS NOT NULL AND expires_at <= ?', (
				self.now( ),) )
			count = int( cursor.fetchone( )[ 0 ] or 0 )
			self.connection.execute( 'DELETE FROM kv WHERE expires_at IS NOT NULL AND expires_at <= ?', (
				self.now( ),) )
			self.connection.commit( )
			return count
		except Exception as e:
			exception = Error( e )
			exception.module = 'storage'
			exception.cause = 'SQLiteCache'
			exception.method = "purge_expired( self ) -> int"
			Logger( ).write( exception )
			raise exception
	
	def stats( self ) -> Dict[ str, Any ]:
		"""
			Return SQLite cache diagnostics.

		Purpose:
			Return SQLite cache diagnostics.

		Returns:
			Dict[str, Any]: Cache diagnostics.
		"""
		try:
			total = self.connection.execute( 'SELECT COUNT(*) FROM kv' ).fetchone( )[ 0 ]
			expired = \
			self.connection.execute( 'SELECT COUNT(*) FROM kv WHERE expires_at IS NOT NULL AND expires_at <= ?', (
				self.now( ),) ).fetchone( )[ 0 ]
			hits = \
			self.connection.execute( 'SELECT COALESCE(SUM(hit_count), 0) FROM kv' ).fetchone( )[ 0 ]
			return { 'backend': 'sqlite', 'path': self.path, 'entries': int( total or 0 ),
				'expired_entries': int( expired or 0 ), 'hits': int( hits or 0 ) }
		except Exception as e:
			exception = Error( e )
			exception.module = 'storage'
			exception.cause = 'SQLiteCache'
			exception.method = "stats( self ) -> Dict[ str, Any ]"
			Logger( ).write( exception )
			raise exception
	
	def close( self ) -> None:
		"""
			Close the SQLite connection.

		Purpose:
			Close the SQLite connection.

		Returns:
			None.
		"""
		try:
			self.connection.close( )
		except Exception as e:
			exception = Error( e )
			exception.module = 'storage'
			exception.cause = 'SQLiteCache'
			exception.method = "close( self ) -> None"
			Logger( ).write( exception )
			raise exception

class SQLiteDatabase( ):
	"""SQLite database management and DataFrame persistence.

	Purpose:
		Provides Data Management table operations, DataFrame transformations,
		interactive visualizations, and SQLite persistence.

	Attributes:
		db_path (str): Current SQLite database file path from configuration.
		table (str): Current table used by a database utility operation.
		table_name (str): Current table name for DataFrame persistence.
		column (str): Current column for database schema operations.
		col_type (str): Column type for schema updates.
		limit (Optional[int]): Maximum number of rows in the latest table read.
		offset (int): Starting row offset in the latest table read.
		df_input (Optional[pd.DataFrame]): Input DataFrame for persistence operations.
	"""
	
	def __init__( self ) -> None:
		"""Initialize the configured SQLite database path.

		Purpose:
			Initialize the configured SQLite database path.

		Returns:
			None: Completes the operation through side effects.
		"""
		self.db_path = cfg.DB_PATH
		self.table = ''
		self.table_name = ''
		self.column = ''
		self.col_type = ''
		self.limit = None
		self.offset = 0
		self.df_input: Optional[ pd.DataFrame ] = None
	
	def validate_database_file( self ) -> Path:
		"""Validate the required pre-hydrated SQLite database.

		Purpose:
			Reject missing, invalid, or unhydrated Git LFS files before opening SQLite.

		Returns:
			Path: Validated absolute SQLite database path.

		Raises:
			FileNotFoundError: When the database file is missing.
			ValueError: When the file does not have a SQLite header.
		"""
		self.db_path = cfg.DB_PATH
		path = Path( self.db_path ).resolve( )
		if not path.is_file( ):
			raise FileNotFoundError( f'Pre-hydrated SQLite database missing: {path}. '
			                         'Install it with git lfs pull when using Git LFS.' )
		with path.open( 'rb' ) as source:
			header = source.read( 16 )
		if header != b'SQLite format 3\x00':
			raise ValueError( f'Invalid SQLite database (possibly Git LFS pointer): {path}. '
			                  'Install its contents with git lfs pull.' )
		return path
	
	def create_connection( self ) -> sqlite3.Connection:
		"""Connect to an existing database for explicit Data Management writes.

		Purpose:
			Preserve intentional writes but reject a missing pre-hydrated database.

		Returns:
			sqlite3.Connection: Read-write connection to the existing database.
		"""
		path = self.validate_database_file( )
		return sqlite3.connect( path.as_uri( ) + '?mode=rw', uri=True )
	
	def create_read_connection( self ) -> sqlite3.Connection:
		"""Connect to the operational SQLite database without write privileges.

		Purpose:
			Use read-only connections for map queries and metadata inspection.

		Returns:
			sqlite3.Connection: Read-only connection to the existing database.
		"""
		path = self.validate_database_file( )
		return sqlite3.connect( path.as_uri( ) + '?mode=ro', uri=True )
	
	def list_tables( self ) -> List[ str ]:
		"""List the tables present in the configured SQLite database.

		Purpose:
			List the tables present in the configured SQLite database.

		Returns:
			List[ str ]: Result of the list tables operation.
		"""
		with self.create_read_connection( ) as conn:
			_query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
			rows = conn.execute( _query ).fetchall( )
			return [ r[ 0 ] for r in rows ]
	
	def create_schema( self, table: str ) -> List[ Tuple ]:
		"""Read the column metadata of a SQLite table.

		Purpose:
			Read the column metadata of a SQLite table.

		Args:
			table (str): SQLite table name.

		Returns:
			List[ Tuple ]: Result of the create schema operation.
		"""
		try:
			throw_if( 'table', table )
			if not isinstance( table, str ):
				raise TypeError( 'table must be a string.' )
			self.table = table
			with self.create_read_connection( ) as conn:
				return conn.execute( f'PRAGMA table_info("{self.table}");' ).fetchall( )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'storage'
			exception.cause = 'SQLiteDatabase'
			exception.method = "create_schema( self, table: str ) -> List[ Tuple ]"
			Logger( ).write( exception )
			raise exception from e
	
	def read_selected_columns( self, table: str, columns: List[ str ] ) -> pd.DataFrame:
		"""Load only the requested columns of an existing SQLite table.

		Purpose:
			Support schema-aware interactive mapping without loading unrelated large
			text and binary fields. Validate identifiers against live SQLite metadata.

		Args:
			table (str): Existing SQLite table name.
			columns (List[str]): Nonempty column list drawn from the table schema.

		Returns:
			pd.DataFrame: Selected database records in their original column order.

		Raises:
			ValueError: When required arguments are missing or unknown identifiers occur.
			TypeError: When argument types are invalid.
			Error: When database retrieval fails.
		"""
		try:
			throw_if( 'table', table )
			throw_if( 'columns', columns )
			if not isinstance( table, str ):
				raise TypeError( 'table must be a string.' )
			if not isinstance( columns, list ) or any(
					not isinstance( column, str ) for column in columns ):
				raise TypeError( 'columns must be a list of strings.' )
			self.table = table
			self.columns = columns
			if self.table not in self.list_tables( ):
				raise ValueError( f'Unknown table: {self.table}' )
			self.available_columns = { column[ 1 ] for column in self.create_schema( self.table ) }
			if any( column not in self.available_columns for column in self.columns ):
				raise ValueError( 'Requested columns are not present in the table schema.' )
			self.quoted_columns = ', '.join(
				'"' + column.replace( '"', '""' ) + '"' for column in self.columns )
			self.quoted_table = '"' + self.table.replace( '"', '""' ) + '"'
			self.query = f'SELECT {self.quoted_columns} FROM {self.quoted_table}'
			with self.create_read_connection( ) as conn:
				cursor = conn.execute( self.query )
				rows = cursor.fetchall( )
			result_columns = [ item[ 0 ] for item in cursor.description ]
			normalized_rows: List[ Dict[ str, Any ] ] = [ ]
			for row in rows:
				record: Dict[ str, Any ] = { }
				for index, column in enumerate( result_columns ):
					value = row[ index ]
					if isinstance( value, bytes ):
						try:
							value = value.decode( 'utf-8' )
						except Exception:
							value = value.hex( )
					elif value is not None and not isinstance( value, (str, int, float, bool) ):
						value = str( value )
					record[ column ] = value
				normalized_rows.append( record )
			return pd.DataFrame( normalized_rows, columns=result_columns )
		except Exception as e:
			exception = Error( e )
			exception.module = 'storage'
			exception.cause = 'SQLiteDatabase'
			exception.method = (
				'read_selected_columns( self, table: str, columns: List[str] ) -> pd.DataFrame')
			Logger( ).write( exception )
			raise exception from e
	
	def read_table( self, table: str, limit: Optional[ int ] = None,
		offset: int = 0 ) -> pd.DataFrame:
		"""
			Read a SQLite table into a pandas DataFrame using a normalized scalar-only path.

		Purpose:
			Read a SQLite table into a pandas DataFrame using a normalized scalar-only path.

		Args:
			table (str): Table name.
			limit (Optional[int]): Maximum rows to retrieve; None selects all rows.
			offset (int): Number of rows to skip, starting at zero.

		Returns:
			pd.DataFrame: DataFrame of plain Python scalar values.
			"""
		try:
			throw_if( 'table', table )
			if not isinstance( table, str ):
				raise TypeError( 'table must be a string.' )
			if limit is not None and (type( limit ) is not int or limit <= 0):
				raise ValueError( 'limit must be a positive integer when provided.' )
			if type( offset ) is not int or offset < 0:
				raise ValueError( 'offset must be a nonnegative integer.' )
			self.table = table
			self.limit = limit
			self.offset = offset
			query = f'SELECT * FROM "{self.table}"'
			if self.limit is not None:
				query += f' LIMIT {self.limit} OFFSET {self.offset}'
			with self.create_read_connection( ) as conn:
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
			
			def scalarize( value: Any ) -> Any:
				"""Prepare SQLite result values for tabular presentation.

				Purpose:
					Decodes binary values and converts unsupported payloads at the display boundary.

				Args:
					value (Any): Value returned from SQLite.

				Returns:
					Any: Scalar or serialized representation of the database value.
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
				try:
					return str( value.model_dump( ) )
				except AttributeError:
					return str( value )
				except Exception:
					return str( value )
			
			normalized_rows: List[ Dict[ str, Any ] ] = [ ]
			for row in rows:
				record: Dict[ str, Any ] = { }
				for idx, col in enumerate( columns ):
					record[ col ] = scalarize( row[ idx ] )
				normalized_rows.append( record )
			return pd.DataFrame( normalized_rows, columns=columns )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'storage'
			exception.cause = 'SQLiteDatabase'
			exception.method = (
				"read_table( self, table: str, limit: Optional[ int ] = None, offset: int = 0 ) -> "
				"pd.DataFrame:")
			Logger( ).write( exception )
			raise exception from e
	
	def render_table( self, df: pd.DataFrame | None ) -> None:
		"""
			Render a DataFrame safely in Streamlit. Use the normal interactive dataframe.

		Purpose:
			Render a DataFrame safely in Streamlit. Use the normal interactive dataframe
			first, and fall back to HTML rendering if Streamlit/PyArrow serialization fails.

		Args:
			df (pd.DataFrame): The DataFrame to render.

		Returns:
			None: Renders the selected database table in Streamlit.
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
			fallback_df[ col ] = fallback_df[ col ].map( lambda x: x if isinstance( x, (str, int,
				float, bool) ) or x == '' else str( x ) )
		st.markdown( fallback_df.to_html( index=False, escape=True ), unsafe_allow_html=True )
	
	def make_display_safe( self, df: pd.DataFrame ) -> pd.DataFrame:
		"""Return a DataFrame with values suitable for Streamlit rendering.

		Purpose:
			Return a DataFrame with values suitable for Streamlit rendering.

		Args:
			df (pd.DataFrame): Input pandas DataFrame.

		Returns:
			pd.DataFrame: Result of the make display safe operation.
		"""
		throw_if( 'df', df )
		if not isinstance( df, pd.DataFrame ):
			raise TypeError( 'df must be a DataFrame.' )
		display_df = df.copy( )
		for col in display_df.columns:
			display_df[ col ] = display_df[ col ].map( lambda x: '' if x is None else str( x ) )
		return display_df
	
	def drop_table( self, table: str ) -> None:
		"""
			Safely drop a table if it exists.

		Purpose:
			Safely drop a table if it exists.

		Args:
			table (str): Table name.

		Returns:
			None: Completes the operation through side effects.
		"""
		try:
			throw_if( 'table', table )
			if not isinstance( table, str ):
				raise TypeError( 'table must be a string.' )
			self.table = table
			with self.create_connection( ) as conn:
				conn.execute( f'DROP TABLE IF EXISTS "{self.table}";' )
				conn.commit( )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'storage'
			exception.cause = 'SQLiteDatabase'
			exception.method = "drop_table( self, table: str ) -> None"
			Logger( ).write( exception )
			raise exception from e
	
	def create_index( self, table: str, column: str ) -> None:
		"""
			Create a safe SQLite index on a specified table column.

		Purpose:
			Create a safe SQLite index on a specified table column.

			Handles:
			- Spaces in column names
			- Special characters
			- Reserved words
			- Duplicate index names
			- Validation against actual table schema

		Args:
			table (str): Table name.
			column (str): Column name to index.

		Returns:
			None: Completes the operation through side effects.
		"""
		try:
			throw_if( 'table', table )
			throw_if( 'column', column )
			if not isinstance( table, str ) or not isinstance( column, str ):
				raise TypeError( 'table and column must be strings.' )
			self.table = table
			self.column = column
			# ------------------------------------------------------------------
			# Validate table exists
			# ------------------------------------------------------------------
			tables = self.list_tables( )
			if self.table not in tables:
				raise ValueError( 'Invalid table name.' )
			# ------------------------------------------------------------------
			# Validate column exists
			# ------------------------------------------------------------------
			schema = self.create_schema( self.table )
			valid_columns = [ col[ 1 ] for col in schema ]
			if self.column not in valid_columns:
				raise ValueError( 'Invalid column name.' )
			# ------------------------------------------------------------------
			# Sanitize index name (identifier only)
			# ------------------------------------------------------------------
			safe_index_name = re.sub( r"[^0-9a-zA-Z_]+", "_", f"idx_{self.table}_{self.column}" )
			# ------------------------------------------------------------------
			# Create index safely (quote identifiers)
			# ------------------------------------------------------------------
			sql = f'CREATE INDEX IF NOT EXISTS "{safe_index_name}" ON "{self.table}"("{self.column}");'
			with self.create_connection( ) as conn:
				conn.execute( sql )
				conn.commit( )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'storage'
			exception.cause = 'SQLiteDatabase'
			exception.method = "create_index( self, table: str, column: str ) -> None"
			Logger( ).write( exception )
			raise exception from e
	
	def apply_filters( self, df: pd.DataFrame ) -> pd.DataFrame:
		"""Render advanced DataFrame filters and return the filtered rows.

		Purpose:
			Render advanced DataFrame filters and return the filtered rows.

		Args:
			df (pd.DataFrame): Input pandas DataFrame.

		Returns:
			pd.DataFrame: Result of the apply filters operation.
		"""
		throw_if( 'df', df )
		if not isinstance( df, pd.DataFrame ):
			raise TypeError( 'df must be a DataFrame.' )
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
	
	def create_aggregation( self, df: pd.DataFrame ) -> None:
		"""Calculate and display a selected numeric aggregation.

		Purpose:
			Calculate and display a selected numeric aggregation.

		Args:
			df (pd.DataFrame): Input pandas DataFrame.

		Returns:
			None: Displays the selected aggregation result in Streamlit, or an informational message when no numeric column exists.
		"""
		throw_if( 'df', df )
		if not isinstance( df, pd.DataFrame ):
			raise TypeError( 'df must be a DataFrame.' )
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
	
	def create_visualization( self, df: pd.DataFrame ) -> None:
		"""
			Render data visualizations without passing pandas objects directly into.

		Purpose:
			Render data visualizations without passing pandas objects directly into
			Plotly/Narwhals.

		Args:
			df (pd.DataFrame): The input DataFrame.

		Returns:
			None: Renders a visualization in the Streamlit interface.
			"""
		throw_if( 'df', df )
		if not isinstance( df, pd.DataFrame ):
			raise TypeError( 'df must be a DataFrame.' )
		blue_divider( )
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
		categorical_cols: List[ str ] = [ col for col in df_plot.columns if
			col not in numeric_cols ]
		chart = st.selectbox( 'Chart Type', [ 'Histogram', 'Bar', 'Line', 'Scatter', 'Box', 'Pie',
			'Correlation' ] )
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
			fig = go.Figure( data=[
				go.Pie( labels=counts.index.tolist( ), values=counts.values.tolist( ) ) ] )
			st.plotly_chart( fig, use_container_width=True )
		
		elif chart == 'Correlation':
			if len( numeric_cols ) < 2:
				st.info( 'At least two numeric columns are required.' )
				return
			corr_df = pd.DataFrame( )
			for col in numeric_cols:
				corr_df[ col ] = pd.to_numeric( df_plot[ col ], errors='coerce' )
			corr = corr_df.corr( )
			fig = go.Figure( data=[
				go.Heatmap( z=corr.values.tolist( ), x=corr.columns.tolist( ), y=corr.index.tolist( ) ) ] )
			st.plotly_chart( fig, use_container_width=True )
	
	def convert_dataframe( self, table_name: str, df: pd.DataFrame ) -> None:
		"""Create a SQLite table from the DataFrame's column types.

		Purpose:
			Create a SQLite table from the DataFrame's column types.

		Args:
			table_name (str): SQLite table name.
			df (pd.DataFrame): Input pandas DataFrame.

		Returns:
			None: Creates a SQLite table using the input DataFrame's inferred column types.
		"""
		try:
			throw_if( 'table_name', table_name )
			throw_if( 'df', df )
			if not isinstance( table_name, str ) or not isinstance( df, pd.DataFrame ):
				raise TypeError( 'Expected a table name string and a pandas DataFrame.' )
			self.table_name = table_name
			self.df_input = df
			columns = [ ]
			for col in self.df_input.columns:
				sql_type = self.get_sqlite_type( self.df_input[ col ].dtype )
				safe_col = col.replace( ' ', '_' )
				columns.append( f'{safe_col} {sql_type}' )
			create_stmt = f'CREATE TABLE IF NOT EXISTS {self.table_name} ({", ".join( columns )});'
			with self.create_connection( ) as conn:
				conn.execute( create_stmt )
				conn.commit( )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'storage'
			exception.cause = 'SQLiteDatabase'
			exception.method = "convert_dataframe( self, table_name: str, df: pd.DataFrame ) -> None"
			Logger( ).write( exception )
			raise exception from e
	
	def insert_data( self, table_name: str, df: pd.DataFrame ) -> None:
		"""Insert a DataFrame's rows into a SQLite table.

		Purpose:
			Insert a DataFrame's rows into a SQLite table.

		Args:
			table_name (str): SQLite table name.
			df (pd.DataFrame): Input pandas DataFrame.

		Returns:
			None: Inserts the DataFrame rows into the selected SQLite table.
		"""
		try:
			throw_if( 'table_name', table_name )
			throw_if( 'df', df )
			if not isinstance( table_name, str ) or not isinstance( df, pd.DataFrame ):
				raise TypeError( 'Expected a table name string and a pandas DataFrame.' )
			self.table_name = table_name
			self.df_input = df
			df = self.df_input.copy( )
			df.columns = [ c.replace( ' ', '_' ) for c in df.columns ]
			placeholders = ', '.join( [ '?' ] * len( df.columns ) )
			stmt = f'INSERT INTO {self.table_name} VALUES ({placeholders});'
			with self.create_connection( ) as conn:
				conn.executemany( stmt, df.values.tolist( ) )
				conn.commit( )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'storage'
			exception.cause = 'SQLiteDatabase'
			exception.method = "insert_data( self, table_name: str, df: pd.DataFrame ) -> None"
			Logger( ).write( exception )
			raise exception from e
	
	def get_sqlite_type( self, dtype: Any ) -> str:
		"""
			Map a pandas dtype to an appropriate SQLite column type.

		Purpose:
			Map a pandas dtype to an appropriate SQLite column type.

		Args:
			dtype (pandas dtype): The dtype of a pandas Series.

		Returns:
			str: SQLite column type.
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
	
	def create_custom_table( self, table_name: str, columns: list ) -> None:
		"""
			Create a custom SQLite table from column definitions.

		Purpose:
			Create a custom SQLite table from column definitions.

		Args:
			table_name (str): Name of table.

			columns (list of dict): [
				{
				"name": str,
				"type": str,
				"not_null": bool,
				"primary_key": bool,
				"auto_increment": bool
				}
				]

		Returns:
			None: Completes the operation through side effects.
		"""
		throw_if( 'table_name', table_name )
		throw_if( 'columns', columns )
		if not isinstance( table_name, str ) or not isinstance( columns, list ):
			raise TypeError( 'table_name must be a string and columns a list.' )
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
		with self.create_connection( ) as conn:
			conn.execute( sql )
			conn.commit( )
	
	def is_safe_query( self, query: str ) -> bool:
		"""
			Determine whether a SQL query is read-only and safe to execute.

		Purpose:
			Determine whether a SQL query is read-only and safe to execute.

			Allows:
			SELECT
			WITH (CTE returning SELECT)
			EXPLAIN SELECT
			PRAGMA (read-only)

			Blocks:
			INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, ATTACH,
			DETACH, VACUUM, REPLACE, TRIGGER, and multiple statements.

		Args:
			query (str): SQL query or identifier to inspect.

		Returns:
			bool: Result of the is safe query operation.
		"""
		if query is None:
			throw_if( 'query', query )
		if not isinstance( query, str ) or not query.strip( ):
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
		# Explicitly allow only read-only PRAGMA inspection names. PRAGMA assignments,
		# parenthesized setters, checkpoints, and other state changes are rejected.
		if q.startswith( 'pragma' ):
			pragma_name = re.match( r'^pragma\s+(?:[a-z_][a-z0-9_]*\.)?([a-z_][a-z0-9_]*)', q )
			allowed_pragmas = { 'table_info', 'table_xinfo', 'table_list', 'index_list',
				'index_info', 'index_xinfo', 'foreign_key_list', 'database_list', 'compile_options',
				'collation_list' }
			if (pragma_name is None or pragma_name.group( 1 ) not in allowed_pragmas or '=' in q):
				return False
		# ------------------------------------------------------------------
		# Block dangerous keywords anywhere
		# ------------------------------------------------------------------
		blocked_keywords = ('insert ', 'update ', 'delete ', 'drop ', 'alter ', 'create ',
			'attach ', 'detach ', 'vacuum ', 'replace ', 'trigger ')
		for keyword in blocked_keywords:
			if keyword in q:
				return False
		return True
	
	def create_identifier( self, name: str ) -> str:
		"""
			Sanitize a string into a safe SQLite identifier.

		Purpose:
			Sanitize a string into a safe SQLite identifier.

			- Replaces invalid characters with underscores
			- Ensures it starts with a letter or underscore
			- Prevents empty names

		Args:
			name (str): Original identifier to sanitize.

		Returns:
			str: Result of the create identifier operation.
		"""
		throw_if( 'name', name )
		if not isinstance( name, str ):
			raise TypeError( 'name must be a string.' )
		safe = re.sub( r'[^0-9a-zA-Z_]', '_', name.strip( ) )
		if not re.match( r'^[A-Za-z_]', safe ):
			safe = f'_{safe}'
		if not safe:
			raise ValueError( 'Invalid identifier after sanitization.' )
		return safe
	
	def get_indexes( self, table: str ) -> List[ Tuple ]:
		"""Return index metadata for a SQLite table.

		Purpose:
			Return index metadata for a SQLite table.

		Args:
			table (str): SQLite table name.

		Returns:
			List[Tuple]: SQLite index metadata rows returned by PRAGMA index_list.
		"""
		try:
			throw_if( 'table', table )
			if not isinstance( table, str ):
				raise TypeError( 'table must be a string.' )
			self.table = table
			with self.create_connection( ) as conn:
				rows = conn.execute( f'PRAGMA index_list("{self.table}");' ).fetchall( )
				return rows
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'storage'
			exception.cause = 'SQLiteDatabase'
			exception.method = "get_indexes( self, table: str ) -> List[ Tuple ]"
			Logger( ).write( exception )
			raise exception from e
	
	def add_column( self, table: str, column: str, col_type: str ) -> None:
		"""Add a typed column to an existing SQLite table.

		Purpose:
			Add a typed column to an existing SQLite table.

		Args:
			table (str): SQLite table name.
			column (str): SQLite column name.
			col_type (str): SQLite column type.

		Returns:
			None: Adds the specified column to the existing SQLite table.
		"""
		try:
			throw_if( 'table', table )
			throw_if( 'column', column )
			throw_if( 'col_type', col_type )
			if not all( isinstance( item, str ) for item in (table, column, col_type) ):
				raise TypeError( 'table, column, and col_type must be strings.' )
			self.table = table
			self.column = self.create_identifier( column )
			self.col_type = col_type.upper( )
			with self.create_connection( ) as conn:
				conn.execute( f'ALTER TABLE "{self.table}" ADD COLUMN "{self.column}" {self.col_type};' )
				conn.commit( )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'storage'
			exception.cause = 'SQLiteDatabase'
			exception.method = "add_column( self, table: str, column: str, col_type: str ) -> None"
			Logger( ).write( exception )
			raise exception from e
	
	def rename_column( self, table_name: str, old_name: str, new_name: str ) -> None:
		"""
			Rename a column within an existing SQLite table. Attempts native ALTER TABLE rename.

		Purpose:
			Rename a column within an existing SQLite table. Attempts native ALTER TABLE rename
			first; if it fails, falls back to a schema-safe rebuild preserving column order, data,
			and indexes.

		Args:
			table_name (str): Table containing the column.

			old_name (str): Existing column name.

			new_name (str): New column name.

		Returns:
			None: Renames the selected SQLite column.
			"""
		try:
			throw_if( 'table_name', table_name )
			throw_if( 'old_name', old_name )
			throw_if( 'new_name', new_name )
			with self.create_connection( ) as conn:
				try:
					conn.execute( f'ALTER TABLE "{table_name}" RENAME COLUMN "{old_name}" TO "{new_name}";' )
					conn.commit( )
					return
				except Exception:
					pass
				row = conn.execute( """
                                    SELECT sql
                                    FROM sqlite_master
                                    WHERE type ='table' AND name =?
				                    """, (table_name,) ).fetchone( )
				if not row or not row[ 0 ]:
					raise ValueError( "Table definition not found." )
				create_sql = row[ 0 ]
				indexes = conn.execute( """
                                        SELECT sql
                                        FROM sqlite_master
                                        WHERE type ='index' AND tbl_name=? AND sql IS NOT NULL
				                        """, (table_name,) ).fetchall( )
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
				conn.execute( f'INSERT INTO "{temp_table}" ({new_insert}) SELECT {old_select} FROM "{table_name}";' )
				conn.execute( f'DROP TABLE "{table_name}";' )
				conn.execute( f'ALTER TABLE "{temp_table}" RENAME TO "{table_name}";' )
				for idx in indexes:
					idx_sql = idx[ 0 ]
					if idx_sql:
						idx_sql = idx_sql.replace( f'"{old_name}"', f'"{new_name}"' )
						conn.execute( idx_sql )
				conn.commit( )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'storage'
			exception.cause = 'SQLiteDatabase'
			exception.method = "rename_column( self, table_name: str, old_name: str, new_name: str ) -> None"
			Logger( ).write( exception )
			raise exception from e
	
	def create_profile_table( self, table: str ) -> pd.DataFrame:
		"""Build column-level descriptive statistics for a table.

		Purpose:
			Build column-level descriptive statistics for a table.

		Args:
			table (str): SQLite table name.

		Returns:
			pd.DataFrame: Per-column statistics including null counts, distinct counts, and numeric summaries.
		"""
		try:
			throw_if( 'table', table )
			if not isinstance( table, str ):
				raise TypeError( 'table must be a string.' )
			self.table = table
			df = self.read_table( self.table )
			profile_rows = [ ]
			total_rows = len( df )
			for col in df.columns:
				series = df[ col ]
				null_count = series.isna( ).sum( )
				distinct_count = series.nunique( dropna=True )
				row = { 'column': col, 'dtype': str( series.dtype ),
					'null_%': round( (null_count / total_rows) * 100, 2 ) if total_rows else 0,
					'distinct_%': round( (
								                     distinct_count / total_rows) * 100, 2 ) if total_rows else 0, }
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
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'storage'
			exception.cause = 'SQLiteDatabase'
			exception.method = "create_profile_table( self, table: str ) -> pd.DataFrame"
			Logger( ).write( exception )
			raise exception from e
	
	def drop_column( self, table: str, column: str ) -> None:
		"""Remove a column while rebuilding the table and restoring indexes.

		Purpose:
			Remove a column while rebuilding the table and restoring indexes.

		Args:
			table (str): SQLite table name.
			column (str): SQLite column name.

		Returns:
			None: Rebuilds the table without the selected column and restores indexes.
		"""
		try:
			throw_if( 'table', table )
			throw_if( 'column', column )
			with self.create_connection( ) as conn:
				# ------------------------------------------------------------
				# Fetch original CREATE TABLE statement
				# ------------------------------------------------------------
				row = conn.execute( """
                                    SELECT sql
                                    FROM sqlite_master
                                    WHERE type ='table' AND name =?
				                    """, (table,) ).fetchone( )
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
				new_create_sql = (f'CREATE TABLE "{temp_table}" (' + ", ".join( new_defs ) + ");")
				# ------------------------------------------------------------
				# Begin transaction
				# ------------------------------------------------------------
				conn.execute( "BEGIN" )
				conn.execute( new_create_sql )
				remaining_cols = [ c.split( )[ 0 ].strip( '"' ) for c in new_defs ]
				col_list = ", ".join( [ f'"{c}"' for c in remaining_cols ] )
				conn.execute( f'INSERT INTO "{temp_table}" ({col_list}) '
				              f'SELECT {col_list} FROM "{table}";' )
				# Preserve indexes
				indexes = conn.execute( """
                                        SELECT sql
                                        FROM sqlite_master
                                        WHERE type ='index' AND tbl_name=? AND sql IS NOT NULL
				                        """, (table,) ).fetchall( )
				conn.execute( f'DROP TABLE "{table}";' )
				conn.execute( f'ALTER TABLE "{temp_table}" RENAME TO "{table}";' )
				# Recreate indexes
				for idx in indexes:
					idx_sql = idx[ 0 ]
					if column not in idx_sql:
						conn.execute( idx_sql )
				conn.commit( )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'storage'
			exception.cause = 'SQLiteDatabase'
			exception.method = "drop_column( self, table: str, column: str ) -> None"
			Logger( ).write( exception )
			raise exception from e
	
	def rename_table( self, old_name: str, new_name: str ) -> None:
		"""
			Rename an existing SQLite table. Attempts native ALTER TABLE rename first; if it fails,.

		Purpose:
			Rename an existing SQLite table. Attempts native ALTER TABLE rename first; if it fails,
			falls back to a schema-safe rebuild using the original CREATE TABLE statement and
			preserves indexes.

		Args:
			old_name (str): Existing table name.

			new_name (str): New table name.

		Returns:
			None: Renames the selected SQLite table.
			"""
		try:
			throw_if( 'old_name', old_name )
			throw_if( 'new_name', new_name )
			with self.create_connection( ) as conn:
				try:
					conn.execute( f'ALTER TABLE "{old_name}" RENAME TO "{new_name}";' )
					conn.commit( )
					return
				except Exception:
					pass
				row = conn.execute( """
                                    SELECT sql
                                    FROM sqlite_master
                                    WHERE type ='table' AND name =?
				                    """, (old_name,) ).fetchone( )
				if not row or not row[ 0 ]:
					raise ValueError( "Table definition not found." )
				create_sql = row[ 0 ]
				indexes = conn.execute( """
                                        SELECT sql
                                        FROM sqlite_master
                                        WHERE type ='index' AND tbl_name=? AND sql IS NOT NULL
				                        """, (old_name,) ).fetchall( )
				open_paren = create_sql.find( "(" )
				if open_paren == -1:
					raise ValueError( "Malformed CREATE TABLE statement." )
				temp_name = f"{new_name}__rebuild_temp"
				conn.execute( "BEGIN" )
				conn.execute( f'CREATE TABLE "{temp_name}" {create_sql[ open_paren: ]}' )
				cols = [ r[ 1 ] for r in
					conn.execute( f'PRAGMA table_info("{old_name}");' ).fetchall( ) ]
				col_list = ", ".join( [ f'"{c}"' for c in cols ] )
				conn.execute( f'INSERT INTO "{temp_name}" ({col_list}) SELECT {col_list} FROM "{old_name}";' )
				conn.execute( f'DROP TABLE "{old_name}";' )
				conn.execute( f'ALTER TABLE "{temp_name}" RENAME TO "{new_name}";' )
				for idx in indexes:
					idx_sql = idx[ 0 ]
					if idx_sql:
						idx_sql = idx_sql.replace( f'ON "{old_name}"', f'ON "{new_name}"' )
						conn.execute( idx_sql )
				conn.commit( )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'storage'
			exception.cause = 'SQLiteDatabase'
			exception.method = "rename_table( self, old_name: str, new_name: str ) -> None"
			Logger( ).write( exception )
			raise exception from e

class ChromaStore( ):
	"""ChromaStore persistence interface.

	Purpose:
		Adds LangChain documents to a persistent Chroma vector collection.

	Attributes:
		documents (List[Document]): Documents for the current write.
		embedder (Embeddings | None): Embedding adapter.
		collection_name (str): Chroma collection name.
		persist_directory (str): Persistent collection directory.
		vector_store (Chroma | None): Active Chroma vector-store instance.
	"""
	
	def __init__( self ) -> None:
		"""Initialize Chroma vector storage state without connecting to a provider.

		Purpose:
			Initialize Chroma vector storage state without connecting to a provider.

		Returns:
			None: Completes the operation through side effects.
		"""
		self.documents: List[ Document ] = [ ]
		self.embedder: Embeddings | None = None
		self.collection_name = ''
		self.persist_directory = ''
		self.vector_store: Chroma | None = None
	
	def create( self, documents: List[ Document ], embedder: Embeddings, collection_name: str,
		persist_directory: str ) -> Chroma:
		"""Store LangChain document chunks in a persistent Chroma collection.

		Purpose:
			Store LangChain document chunks in a persistent Chroma collection.

		Args:
			documents (List[ Document ]): LangChain documents for vector storage.
			embedder (Embeddings): LangChain embedding implementation.
			collection_name (str): Chroma collection name.
			persist_directory (str): Chroma persistence directory.

		Returns:
			Chroma: Result of the create operation.
		"""
		try:
			throw_if( 'documents', documents )
			throw_if( 'embedder', embedder )
			throw_if( 'collection_name', collection_name )
			throw_if( 'persist_directory', persist_directory )
			if not isinstance( documents, list ) or not all(
					isinstance( document, Document ) for document in documents ):
				raise TypeError( 'documents must be a list of LangChain Documents.' )
			if not isinstance( embedder, Embeddings ):
				raise TypeError( 'embedder must implement LangChain Embeddings.' )
			if not isinstance( collection_name, str ) or not isinstance( persist_directory, str ):
				raise TypeError( 'collection_name and persist_directory must be strings.' )
			self.documents = documents
			self.embedder = embedder
			self.collection_name = collection_name
			self.persist_directory = persist_directory
			ids = vector_document_ids( self.documents )
			Path( self.persist_directory ).mkdir( parents=True, exist_ok=True )
			store = Chroma( collection_name=self.collection_name, embedding_function=self.embedder,
				persist_directory=self.persist_directory )
			store.add_documents( documents=self.documents, ids=ids )
			self.vector_store = store
			return self.vector_store
		except Exception as e:
			exception = Error( e )
			exception.module = 'storage'
			exception.cause = 'ChromaStore'
			exception.method = "create( self, **args ) -> Chroma"
			Logger( ).write( exception )
			raise exception from e

class PineconeStore( ):
	"""PineconeStore persistence interface.

	Purpose:
		Adds LangChain documents to an existing managed Pinecone index.

	Attributes:
		documents (List[Document]): Documents for the current write.
		embedder (Embeddings | None): Embedding adapter.
		index_name (str): Pinecone index name.
		namespace (str): Pinecone namespace.
		api_key (str): Pinecone credential.
		client (Any): Pinecone client.
		vector_store (Any): Active Pinecone vector-store adapter.
	"""
	
	def __init__( self ) -> None:
		"""Initialize Pinecone vector storage state without connecting to a provider.

		Purpose:
			Initialize Pinecone vector storage state without connecting to a provider.

		Returns:
			None: Completes the operation through side effects.
		"""
		self.documents: List[ Document ] = [ ]
		self.embedder: Embeddings | None = None
		self.index_name = ''
		self.namespace = ''
		self.api_key = ''
		self.client: Any = None
		self.vector_store: Any = None
	
	def create( self, documents: List[ Document ], embedder: Embeddings, index_name: str,
		namespace: str, api_key: str ) -> Any:
		"""Store LangChain document chunks in an existing Pinecone index.

		Purpose:
			Store LangChain document chunks in an existing Pinecone index.

		Args:
			documents (List[ Document ]): LangChain documents for vector storage.
			embedder (Embeddings): LangChain embedding implementation.
			index_name (str): Existing Pinecone index name.
			namespace (str): Optional cache namespace.
			api_key (str): Pinecone API credential.

		Returns:
			Any: Result of the create operation.
		"""
		try:
			throw_if( 'documents', documents )
			throw_if( 'embedder', embedder )
			throw_if( 'index_name', index_name )
			throw_if( 'api_key', api_key )
			if not isinstance( documents, list ) or not all(
					isinstance( document, Document ) for document in documents ):
				raise TypeError( 'documents must be a list of LangChain Documents.' )
			if not isinstance( embedder, Embeddings ):
				raise TypeError( 'embedder must implement LangChain Embeddings.' )
			if not isinstance( index_name, str ) or not isinstance( api_key, str ):
				raise TypeError( 'index_name and api_key must be strings.' )
			if namespace is None:
				throw_if( 'namespace', namespace )
			if not isinstance( namespace, str ):
				raise TypeError( 'namespace must be a string; empty is allowed.' )
			self.documents = documents
			self.embedder = embedder
			self.index_name = index_name
			self.namespace = namespace
			self.api_key = api_key
			ids = vector_document_ids( self.documents )
			from langchain_pinecone import PineconeVectorStore
			from pinecone import Pinecone
			client = Pinecone( api_key=self.api_key )
			if not client.indexes.exists( self.index_name ):
				raise ValueError( f'Pinecone index does not exist: {self.index_name}' )
			index = client.index( name=self.index_name )
			store = PineconeVectorStore( index=index, embedding=self.embedder, namespace=self.namespace or None )
			store.add_documents( documents=self.documents, ids=ids )
			self.client = client
			self.vector_store = store
			return self.vector_store
		except Exception as e:
			exception = Error( e )
			exception.module = 'storage'
			exception.cause = 'PineconeStore'
			exception.method = "create( self, **args ) -> Any"
			Logger( ).write( exception )
			raise exception from e
