'''
  ******************************************************************************************
      Assembly:                Mappy
      Filename:                caches.py
      Author:                  Terry D. Eppler
      Created:                 05-31-2022

      Last Modified By:        Terry D. Eppler
      Last Modified On:        05-01-2025
  ******************************************************************************************
  <copyright file="caches.py" company="Terry D. Eppler">

	     Mappy is a python framework encapsulating the Google Maps functionality.
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
    caches.py
  </summary>
  ******************************************************************************************
  '''
import json
import os
import sqlite3
import time
from typing import Any, Dict, Optional
if __package__:
	from .boogr import Error, Logger
else:
	from boogr import Error, Logger

def throw_if( name: str, value: object ) -> None:
	"""Validate that a required cache value is present.

	Purpose:
		Provides a lightweight guard used by cache backends before keys, namespaces,
		records, and payloads are read or persisted. The function raises clear
		validation errors for missing objects and blank strings so cache callers fail
		before corrupt or ambiguous keys are created.

	Args:
		name: Name of the argument being validated.
		value: Runtime value to validate.

	Raises:
		ValueError: Raised when ``value`` is ``None`` or an empty string.
	"""
	if value is None:
		raise ValueError( f'Argument "{name}" cannot be None.' )
	
	if isinstance( value, str ) and not value.strip( ):
		raise ValueError( f'Argument "{name}" cannot be empty.' )

class BaseCache:
	"""Define the common cache interface used by Mappy services.

	Purpose:
		Provides the shared contract for cache backends that map string keys to
		JSON-serializable dictionary values. Geocoding, Places, weather, fetcher, and
		spreadsheet-enrichment workflows can use this interface without depending on
		a specific in-memory or SQLite implementation.

	Notes:
		Subclasses implement storage-specific behavior for ``get``, ``set``,
		``delete``, ``clear``, and ``stats``.
	"""
	
	def get( self, key: str ) -> Optional[ Dict[ str, Any ] ]:
		"""Return a cached value by key.

		Purpose:
			Defines the read contract implemented by cache backends. Concrete
			implementations should return cached dictionary payloads only when the
			key exists and the record has not expired.

		Args:
			key: Cache key to read.

		Returns:
			Optional[Dict[str, Any]]: Cached dictionary payload, or ``None`` when no
				usable record exists.

		Raises:
			NotImplementedError: Raised when the base interface is called directly.
		"""
		raise NotImplementedError
	
	def set( self, key: str, value: Dict[ str, Any ], ttl: Optional[ int ] = None ) -> None:
		"""Persist a value by cache key.

		Purpose:
			Defines the write contract implemented by cache backends. Concrete
			implementations should store JSON-serializable dictionary payloads and
			apply the optional time-to-live value when provided.

		Args:
			key: Cache key to write.
			value: JSON-serializable dictionary payload.
			ttl: Optional time-to-live in seconds.

		Raises:
			NotImplementedError: Raised when the base interface is called directly.
		"""
		raise NotImplementedError
	
	def delete( self, key: str ) -> None:
		"""Delete a cache record by key.

		Purpose:
			Defines the deletion contract implemented by cache backends. Concrete
			implementations should remove the matching record without affecting
			unrelated keys or namespaces.

		Args:
			key: Cache key to delete.

		Raises:
			NotImplementedError: Raised when the base interface is called directly.
		"""
		raise NotImplementedError
	
	def clear( self, namespace: Optional[ str ] = None ) -> None:
		"""Clear cache records.

		Purpose:
			Defines the cache-clearing contract implemented by cache backends.
			Concrete implementations should remove all records when no namespace is
			supplied, or only namespace-prefixed records when a namespace is supplied.

		Args:
			namespace: Optional namespace prefix to clear.

		Raises:
			NotImplementedError: Raised when the base interface is called directly.
		"""
		raise NotImplementedError
	
	def contains( self, key: str ) -> bool:
		"""Determine whether a key resolves to a usable cached value.

		Purpose:
			Provides a common implementation that validates the key and delegates to
			``get``. Backends can override this method for optimized lookups, but the
			default behavior preserves TTL-aware semantics by relying on ``get``.

		Args:
			key: Cache key to test.

		Returns:
			bool: ``True`` when the key resolves to a non-expired cached value.

		Raises:
			Error: Raised after logging when key validation or backend lookup fails.
		"""
		try:
			throw_if( 'key', key )
			return self.get( key ) is not None
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'BaseCache'
			exception.method = 'contains( self, key: str ) -> bool'
			Logger( ).write( exception )
			raise exception
	
	def namespace_key( self, namespace: str, key: str ) -> str:
		"""Create a namespace-qualified cache key.

		Purpose:
			Builds a stable cache key that separates values by workflow or service
			area. Geocoding, places, weather, distance, and fetcher workflows can use
			namespaces to avoid collisions when raw keys overlap.

		Args:
			namespace: Logical cache namespace, such as ``geocode`` or ``places``.
			key: Raw cache key.

		Returns:
			str: Namespace-qualified cache key.

		Raises:
			Error: Raised after logging when validation or key construction fails.
		"""
		try:
			throw_if( 'namespace', namespace )
			throw_if( 'key', key )
			return f'{namespace}::{key}'
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'BaseCache'
			exception.method = 'namespace_key( self, namespace: str, key: str ) -> str'
			Logger( ).write( exception )
			raise exception
	
	def stats( self ) -> Dict[ str, Any ]:
		"""Return cache diagnostics.

		Purpose:
			Defines the diagnostics contract implemented by cache backends. Concrete
			implementations should return backend name, entry counts, expiration
			counts, and available hit or mutation counters.

		Returns:
			Dict[str, Any]: Cache diagnostics.

		Raises:
			NotImplementedError: Raised when the base interface is called directly.
		"""
		raise NotImplementedError

class InMemoryCache( BaseCache ):
	"""Provide a process-local dictionary cache.

	Purpose:
		Implements the Mappy cache contract using an in-memory dictionary with
		optional TTL handling and runtime diagnostics. This backend supports fast
		lookups during a single Streamlit or Python process and is useful for
		geocoding, Places, fetcher, and enrichment workflows that do not require
		durable cache persistence.

	Attributes:
		_store: Dictionary containing cache metadata records by key.
		_hits: Number of successful cache reads.
		_misses: Number of cache misses or expired reads.
		_sets: Number of cache writes.
		_deletes: Number of cache deletions.
	"""
	_store: Dict[ str, Dict[ str, Any ] ]
	_hits: int
	_misses: int
	_sets: int
	_deletes: int
	
	def __init__( self ) -> None:
		"""Initialize the in-memory cache backend.

		Purpose:
			Creates the backing dictionary and resets runtime diagnostics used by
			``get``, ``set``, ``delete``, ``clear``, and ``stats``. The cache starts
			empty and remains available for the lifetime of the current Python
			process.
		"""
		self._store = { }
		self._hits = 0
		self._misses = 0
		self._sets = 0
		self._deletes = 0
	
	def now( self ) -> float:
		"""Return the current Unix timestamp.

		Purpose:
			Provides a single timestamp source for cache record creation, TTL
			expiration checks, last-access tracking, and diagnostics.

		Returns:
			float: Current Unix timestamp.

		Raises:
			Error: Raised after logging when timestamp retrieval fails.
		"""
		try:
			return time.time( )
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'InMemoryCache'
			exception.method = 'now( self ) -> float'
			Logger( ).write( exception )
			raise exception
	
	def make_record( self, key: str, value: Dict[ str, Any ],
			ttl: Optional[ int ] = None ) -> Dict[ str, Any ]:
		"""Create a cache metadata record.

		Purpose:
			Packages a cache key, JSON-serializable payload, timestamps, optional
			expiration time, hit counter, and last-access marker into the internal
			record shape used by ``InMemoryCache``.

		Args:
			key: Cache key.
			value: JSON-serializable dictionary payload.
			ttl: Optional time-to-live in seconds.

		Returns:
			Dict[str, Any]: Cache metadata record.

		Raises:
			Error: Raised after logging when validation or record construction fails.
		"""
		try:
			throw_if( 'key', key )
			throw_if( 'value', value )
			
			now_value = self.now( )
			ttl_value = int( ttl ) if ttl is not None and int( ttl ) > 0 else None
			expires_value = now_value + ttl_value if ttl_value else None
			
			return {
					'key': key,
					'value': value,
					'created_at': now_value,
					'updated_at': now_value,
					'expires_at': expires_value,
					'hit_count': 0,
					'last_accessed': None
			}
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'InMemoryCache'
			exception.method = 'make_record( self, *args ) -> Dict[ str, Any ]'
			Logger( ).write( exception )
			raise exception
	
	def is_expired( self, record: Dict[ str, Any ] ) -> bool:
		"""Determine whether an in-memory record has expired.

		Purpose:
			Reads the record's ``expires_at`` metadata and compares it with the
			current timestamp. The method keeps TTL handling centralized for reads,
			statistics, and cleanup behavior.

		Args:
			record: Cache metadata record.

		Returns:
			bool: ``True`` when the record has expired; otherwise ``False``.

		Raises:
			Error: Raised after logging when validation or timestamp comparison fails.
		"""
		try:
			throw_if( 'record', record )
			expires_at = record.get( 'expires_at' )
			if expires_at is None:
				return False
			
			return float( expires_at ) <= self.now( )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'InMemoryCache'
			exception.method = 'is_expired( self, record: Dict[ str, Any ] ) -> bool'
			Logger( ).write( exception )
			raise exception
	
	def get( self, key: str ) -> Optional[ Dict[ str, Any ] ]:
		"""Return a cached value by key.

		Purpose:
			Looks up an in-memory cache record, removes expired records, updates
			hit and last-access metadata for successful reads, and returns only the
			stored payload to callers.

		Args:
			key: Cache key.

		Returns:
			Optional[Dict[str, Any]]: Cached payload, or ``None`` when the key is
				missing or expired.

		Raises:
			Error: Raised after logging when validation or lookup fails.
		"""
		try:
			throw_if( 'key', key )
			record = self._store.get( key )
			if not record:
				self._misses += 1
				return None
			
			if self.is_expired( record ):
				self.delete( key )
				self._misses += 1
				return None
			
			record[ 'hit_count' ] = int( record.get( 'hit_count', 0 ) or 0 ) + 1
			record[ 'last_accessed' ] = self.now( )
			self._hits += 1
			return record.get( 'value' )
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'InMemoryCache'
			exception.method = 'get( self, key: str ) -> Optional[ Dict[ str, Any ] ]'
			Logger( ).write( exception )
			raise exception
	
	def set( self, key: str, value: Dict[ str, Any ], ttl: Optional[ int ] = None ) -> None:
		"""Set a cache value by key.

		Purpose:
			Stores a JSON-serializable dictionary payload using the in-memory record
			shape and optional TTL metadata. The method increments set diagnostics
			after a successful write.

		Args:
			key: Cache key.
			value: JSON-serializable dictionary payload.
			ttl: Optional time-to-live in seconds.

		Raises:
			Error: Raised after logging when validation or write handling fails.
		"""
		try:
			throw_if( 'key', key )
			throw_if( 'value', value )
			self._store[ key ] = self.make_record( key, value, ttl )
			self._sets += 1
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'InMemoryCache'
			exception.method = 'set( self, *args ) -> None'
			Logger( ).write( exception )
			raise exception
	
	def delete( self, key: str ) -> None:
		"""Delete a cache entry by key.

		Purpose:
			Removes an in-memory cache record when the key exists and updates the
			delete counter. Missing keys are ignored so cleanup paths can call this
			method safely.

		Args:
			key: Cache key.

		Raises:
			Error: Raised after logging when validation or deletion fails.
		"""
		try:
			throw_if( 'key', key )
			if key in self._store:
				del self._store[ key ]
				self._deletes += 1
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'InMemoryCache'
			exception.method = 'delete( self, key: str ) -> None'
			Logger( ).write( exception )
			raise exception
	
	def clear( self, namespace: Optional[ str ] = None ) -> None:
		"""Clear all cache entries or a namespace subset.

		Purpose:
			Deletes every in-memory record when no namespace is supplied, or deletes
			only keys beginning with the namespace prefix when a namespace is supplied.
			This supports targeted cache resets for service-specific workflows.

		Args:
			namespace: Optional namespace prefix.

		Raises:
			Error: Raised after logging when clear handling fails.
		"""
		try:
			if namespace:
				prefix = f'{namespace}::'
				keys = [ key for key in self._store if key.startswith( prefix ) ]
				for key in keys:
					self.delete( key )
			else:
				deleted = len( self._store )
				self._store.clear( )
				self._deletes += deleted
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'InMemoryCache'
			exception.method = 'clear( self, namespace: Optional[ str ]=None ) -> None'
			Logger( ).write( exception )
			raise exception
	
	def contains( self, key: str ) -> bool:
		"""Determine whether a key exists and is not expired.

		Purpose:
			Delegates to ``get`` so the containment check honors TTL expiration,
			deletes expired records, and returns the same result a read operation
			would observe.

		Args:
			key: Cache key.

		Returns:
			bool: ``True`` when the key resolves to a non-expired cached value.

		Raises:
			Error: Raised after logging when validation or lookup fails.
		"""
		try:
			return self.get( key ) is not None
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'InMemoryCache'
			exception.method = 'contains( self, key: str ) -> bool'
			Logger( ).write( exception )
			raise exception
	
	def stats( self ) -> Dict[ str, Any ]:
		"""Return in-memory cache diagnostics.

		Purpose:
			Reports backend type, active entry count, expired entry count, hit count,
			miss count, write count, and deletion count for UI display, debugging,
			and operational inspection.

		Returns:
			Dict[str, Any]: Cache diagnostics.

		Raises:
			Error: Raised after logging when diagnostics generation fails.
		"""
		try:
			expired = 0
			for record in self._store.values( ):
				if self.is_expired( record ):
					expired += 1
			return {
					'backend': 'memory',
					'entries': len( self._store ),
					'expired_entries': expired,
					'hits': self._hits,
					'misses': self._misses,
					'sets': self._sets,
					'deletes': self._deletes
			}
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'InMemoryCache'
			exception.method = 'stats( self ) -> Dict[ str, Any ]'
			Logger( ).write( exception )
			raise exception

class SQLiteCache( BaseCache ):
	"""Persist cache records in a SQLite database.

	Purpose:
		Implements the Mappy cache contract using a local SQLite key-value table.
		Values are stored as JSON strings with creation, update, expiration,
		hit-count, and last-access metadata so cache state can survive application
		restarts and support diagnostics.

	Attributes:
		path: SQLite database file path.
		_conn: Active SQLite connection used by cache operations.
	"""
	path: Optional[ str ]
	_conn: sqlite3.Connection
	
	def __init__( self, path: str = 'mappy_cache.sqlite' ) -> None:
		"""Initialize the SQLite cache backend.

		Purpose:
			Stores the database path, creates the containing directory when needed,
			opens the SQLite connection, and initializes or migrates the cache table
			used by durable cache operations.

		Args:
			path: SQLite database file path.
		"""
		self.path = path
		d = os.path.dirname( self.path )
		if d:
			os.makedirs( d, exist_ok=True )
		self._conn = sqlite3.connect( self.path )
		self.initialize( )
	
	def initialize( self ) -> None:
		"""Create the SQLite cache table when needed.

		Purpose:
			Ensures the durable key-value table exists with payload, timestamp,
			expiration, hit-count, and last-access columns. The method also invokes
			migration logic so older cache tables remain compatible with current
			diagnostics and TTL behavior.

		Raises:
			Error: Raised after logging when table creation, migration, or commit
				handling fails.
		"""
		try:
			self._conn.execute( '''
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
                                )
			                    ''' )
			self.migrate( )
			self._conn.commit( )
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'SQLiteCache'
			exception.method = 'initialize( self ) -> None'
			Logger( ).write( exception )
			raise exception
	
	def migrate( self ) -> None:
		"""Add missing metadata columns to older SQLite cache tables.

		Purpose:
			Reads the current ``kv`` schema and adds metadata columns that may be
			missing from legacy tables. This keeps existing cache databases usable
			after upgrades without requiring users to delete local cache files.

		Raises:
			Error: Raised after logging when schema inspection or migration fails.
		"""
		try:
			cursor = self._conn.execute( 'PRAGMA table_info(kv)' )
			columns = { row[ 1 ] for row in cursor.fetchall( ) }
			additions = {
					'created_at': 'ALTER TABLE kv ADD COLUMN created_at REAL',
					'updated_at': 'ALTER TABLE kv ADD COLUMN updated_at REAL',
					'expires_at': 'ALTER TABLE kv ADD COLUMN expires_at REAL',
					'hit_count': 'ALTER TABLE kv ADD COLUMN hit_count INTEGER DEFAULT 0',
					'last_accessed': 'ALTER TABLE kv ADD COLUMN last_accessed REAL'
			}
			
			for column, sql in additions.items( ):
				if column not in columns:
					self._conn.execute( sql )
		
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'SQLiteCache'
			exception.method = 'migrate( self ) -> None'
			Logger( ).write( exception )
			raise exception
	
	def now( self ) -> float:
		"""Return the current Unix timestamp.

		Purpose:
			Provides a single timestamp source for SQLite cache creation,
			expiration, last-access updates, purge operations, and diagnostics.

		Returns:
			float: Current Unix timestamp.

		Raises:
			Error: Raised after logging when timestamp retrieval fails.
		"""
		try:
			return time.time( )
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'SQLiteCache'
			exception.method = 'now( self ) -> float'
			Logger( ).write( exception )
			raise exception
	
	def get( self, key: str ) -> Optional[ Dict[ str, Any ] ]:
		"""Return a cached SQLite value by key.

		Purpose:
			Reads a JSON payload from the SQLite cache, deletes expired rows, updates
			hit-count and last-access metadata for successful reads, and returns the
			decoded dictionary payload.

		Args:
			key: Cache key.

		Returns:
			Optional[Dict[str, Any]]: Cached payload, or ``None`` when the key is
				missing or expired.

		Raises:
			Error: Raised after logging when validation, SQL execution, or JSON
				decoding fails.
		"""
		try:
			throw_if( 'key', key )
			cursor = self._conn.execute( 'SELECT v, expires_at, hit_count FROM kv WHERE k = ?',
				(key,) )
			row = cursor.fetchone( )
			if not row:
				return None
			
			payload = row[ 0 ]
			expires_at = row[ 1 ]
			hit_count = int( row[ 2 ] or 0 )
			if expires_at is not None and float( expires_at ) <= self.now( ):
				self.delete( key )
				return None
			
			self._conn.execute(
				'UPDATE kv SET hit_count = ?, last_accessed = ? WHERE k = ?',
				(hit_count + 1, self.now( ), key) )
			self._conn.commit( )
			return json.loads( payload )
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'SQLiteCache'
			exception.method = 'get( self, key: str ) -> Optional[ Dict[ str, Any ] ]'
			Logger( ).write( exception )
			raise exception
	
	def set( self, key: str, value: Dict[ str, Any ], ttl: Optional[ int ] = None ) -> None:
		"""Set a SQLite cache value by key.

		Purpose:
			Serializes a dictionary payload to JSON and upserts it into the SQLite
			cache table with creation, update, and optional expiration metadata. The
			method preserves durable cache behavior across application sessions.

		Args:
			key: Cache key.
			value: JSON-serializable dictionary payload.
			ttl: Optional time-to-live in seconds.

		Raises:
			Error: Raised after logging when validation, JSON serialization, SQL
				execution, or commit handling fails.
		"""
		try:
			throw_if( 'key', key )
			throw_if( 'value', value )
			now_value = self.now( )
			ttl_value = int( ttl ) if ttl is not None and int( ttl ) > 0 else None
			expires_value = now_value + ttl_value if ttl_value else None
			payload = json.dumps( value, ensure_ascii=False )
			self._conn.execute( '''
                                INSERT INTO kv
                                (k,
                                 v,
                                 created_at,
                                 updated_at,
                                 expires_at,
                                 hit_count,
                                 last_accessed)
                                VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(k) DO
                                UPDATE SET
                                    v = excluded.v,
                                    updated_at = excluded.updated_at,
                                    expires_at = excluded.expires_at
			                    ''', (key, payload, now_value,
			                          now_value, expires_value, 0, None) )
			self._conn.commit( )
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'SQLiteCache'
			exception.method = 'set( self, *args ) -> None'
			Logger( ).write( exception )
			raise exception
	
	def delete( self, key: str ) -> None:
		"""Delete a SQLite cache entry by key.

		Purpose:
			Removes a durable cache record from the SQLite key-value table and
			commits the change. Missing keys are ignored by SQLite so cleanup paths
			can safely call this method.

		Args:
			key: Cache key.

		Raises:
			Error: Raised after logging when validation, SQL execution, or commit
				handling fails.
		"""
		try:
			throw_if( 'key', key )
			self._conn.execute( 'DELETE FROM kv WHERE k = ?', (key,) )
			self._conn.commit( )
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'SQLiteCache'
			exception.method = 'delete( self, key: str ) -> None'
			Logger( ).write( exception )
			raise exception
	
	def clear( self, namespace: Optional[ str ] = None ) -> None:
		"""Clear all SQLite cache entries or a namespace subset.

		Purpose:
			Deletes every durable cache row when no namespace is supplied, or deletes
			only rows with keys matching the namespace prefix when a namespace is
			supplied. This supports targeted cleanup for service-specific workflows.

		Args:
			namespace: Optional namespace prefix.

		Raises:
			Error: Raised after logging when SQL execution or commit handling fails.
		"""
		try:
			if namespace:
				prefix = f'{namespace}::%'
				self._conn.execute( 'DELETE FROM kv WHERE k LIKE ?', (prefix,) )
			else:
				self._conn.execute( 'DELETE FROM kv' )
			
			self._conn.commit( )
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'SQLiteCache'
			exception.method = 'clear( self, namespace: Optional[ str ]=None ) -> None'
			Logger( ).write( exception )
			raise exception
	
	def contains( self, key: str ) -> bool:
		"""Determine whether a SQLite cache key exists and is not expired.

		Purpose:
			Validates the supplied key and delegates to ``get`` so containment checks
			honor TTL expiration and produce the same result a read operation would
			observe.

		Args:
			key: Cache key.

		Returns:
			bool: ``True`` when the key resolves to a non-expired cached value.

		Raises:
			Error: Raised after logging when validation or lookup fails.
		"""
		try:
			throw_if( 'key', key )
			return self.get( key ) is not None
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'SQLiteCache'
			exception.method = 'contains( self, key: str ) -> bool'
			Logger( ).write( exception )
			raise exception
	
	def purge_expired( self ) -> int:
		"""Delete expired SQLite cache entries.

		Purpose:
			Counts and removes rows whose expiration timestamp has passed. The method
			supports manual cache maintenance and diagnostics for durable cache
			backends.

		Returns:
			int: Number of expired rows deleted.

		Raises:
			Error: Raised after logging when SQL execution or commit handling fails.
		"""
		try:
			cursor = self._conn.execute(
				'SELECT COUNT(*) FROM kv WHERE expires_at IS NOT NULL AND expires_at <= ?',
				(self.now( ),) )
			count = int( cursor.fetchone( )[ 0 ] or 0 )
			self._conn.execute(
				'DELETE FROM kv WHERE expires_at IS NOT NULL AND expires_at <= ?',
				(self.now( ),) )
			self._conn.commit( )
			return count
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'SQLiteCache'
			exception.method = 'purge_expired( self ) -> int'
			Logger( ).write( exception )
			raise exception
	
	def stats( self ) -> Dict[ str, Any ]:
		"""Return SQLite cache diagnostics.

		Purpose:
			Reports backend type, database path, total row count, expired row count,
			and accumulated hit count for UI display, debugging, and operational
			inspection.

		Returns:
			Dict[str, Any]: SQLite cache diagnostics.

		Raises:
			Error: Raised after logging when diagnostics queries fail.
		"""
		try:
			total = self._conn.execute( 'SELECT COUNT(*) FROM kv' ).fetchone( )[ 0 ]
			expired = self._conn.execute(
				'SELECT COUNT(*) FROM kv WHERE expires_at IS NOT NULL AND expires_at <= ?',
				(self.now( ),) ).fetchone( )[ 0 ]
			hits = self._conn.execute(
				'SELECT COALESCE(SUM(hit_count), 0) FROM kv' ).fetchone( )[ 0 ]
			return {
					'backend': 'sqlite',
					'path': self.path,
					'entries': int( total or 0 ),
					'expired_entries': int( expired or 0 ),
					'hits': int( hits or 0 )
			}
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'SQLiteCache'
			exception.method = 'stats( self ) -> Dict[ str, Any ]'
			Logger( ).write( exception )
			raise exception
	
	def close( self ) -> None:
		"""Close the SQLite cache connection.

		Purpose:
			Closes the active SQLite connection used by the durable cache backend.
			This supports explicit cleanup in scripts, tests, and long-running
			application workflows that need deterministic connection shutdown.

		Raises:
			Error: Raised after logging when connection close handling fails.
		"""
		try:
			self._conn.close( )
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'SQLiteCache'
			exception.method = 'close( self ) -> None'
			Logger( ).write( exception )
			raise exception