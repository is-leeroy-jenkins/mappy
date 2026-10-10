'''
  ******************************************************************************************
      Assembly:                Mappy
      Filename:                booger.py
      Author:                  Terry D. Eppler
      Created:                 05-31-2022

      Last Modified By:        Terry D. Eppler
      Last Modified On:        05-01-2025
  ******************************************************************************************
  <copyright file="booger.py" company="Terry D. Eppler">

	     Mathy Booger

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
    booger.py
  </summary>
  ******************************************************************************************
  '''
from __future__ import annotations

import os
import sqlite3
import traceback
from datetime import datetime
from pathlib import Path
from sys import exc_info
from typing import Any, List

if __package__:
	from . import config as cfg
else:
	import config as cfg

HEADLESS = ("STREAMLIT_SERVER_RUNNING" in os.environ
            or "streamlit" in os.environ.get( "PYTHONPATH", "" ).lower( ))

class Error( Exception ):
	"""Wrap an exception with application-specific diagnostic metadata.

	Purpose:
		Captures the original exception, traceback text, optional heading, cause, module name,
		and method signature used by Fonky exception handlers. The wrapper provides a stable
		object that can be raised by calling code and written by the Logger without requiring
		each caller to format traceback details manually.

	Attributes:
		exception (Exception): Original exception instance being wrapped.
		heading (str | None): Optional display heading associated with the error.
		cause (str | None): Logical component or class responsible for the failure.
		method (str | None): Stable method or function signature where the failure occurred.
		module (str | None): Source module where the failure occurred.
		type (type | None): Active exception type reported by ``sys.exc_info``.
		trace (str): Formatted traceback text captured at wrapper construction time.
		info (str): Combined exception type and formatted traceback text.
	"""
	
	def __init__( self, error: Exception, heading: str = None, cause: str = None,
			method: str = None, module: str = None ):
		"""Initialize the error wrapper.

		Purpose:
			Initializes the wrapper with the original exception and optional diagnostic metadata.
			The constructor captures traceback information immediately so downstream logging can
			persist the same failure context even after control has moved out of the original
			exception handler.

		Args:
			error (Exception): Original exception instance being wrapped.
			heading (str): Optional display heading associated with the error.
			cause (str): Logical component or class responsible for the failure.
			method (str): Stable method or function signature where the failure occurred.
			module (str): Source module where the failure occurred.
		"""
		super( ).__init__( )
		self.exception = error
		self.heading = heading
		self.cause = cause
		self.method = method
		self.module = module
		self.type = exc_info( )[ 0 ]
		self.trace = traceback.format_exc( )
		self.info = str( exc_info( )[ 0 ] ) + ': \r\n \r\n' + traceback.format_exc( )
	
	def __str__( self ) -> str | None:
		"""Return the captured diagnostic text.

		Purpose:
			Returns the formatted exception information captured when the wrapper was created.
			This representation supports direct display, logging, and debugging without requiring
			callers to inspect individual metadata fields.

		Returns:
			Captured exception information when available.
		"""
		if self.info is not None:
			return self.info
	
	def __dir__( self ) -> List[ str ] | None:
		"""Return the public diagnostic member names.

		Purpose:
			Provides a stable member list for inspectors, debuggers, user-interface tooling, and
			interactive sessions that need to display the important diagnostic fields carried by
			the wrapper.

		Returns:
			Ordered diagnostic member names exposed by the wrapper.
		"""
		return [ 'message', 'cause', 'method', 'module', 'scaler', 'stack_trace', 'info' ]

class Logger( ):
	"""Persist wrapped exception details to the configured SQLite logging database.

	Purpose:
		Provides a small application logger that writes Error metadata to the SQLite database
		identified by ``config.LOG_PATH`` and the table identified by ``config.LOG_FILE``. The
		class creates the logging directory and table as needed, then records exception cause,
		module, method, message, diagnostic information, traceback text, and creation time.

	Attributes:
		path (Path): Filesystem path to the SQLite logging database.
		table (str): SQLite table name used for persisted exception records.
		query (str | None): SQL statement prepared for the active logging operation.
		values (tuple[Any, ...] | None): Values prepared for the active logging operation.
	"""
	
	def __init__( self ) -> None:
		"""Initialize the logger.

		Purpose:
			Initializes the logger from the central Fonky configuration and prepares local state
			used by later write operations. The constructor does not open a persistent database
			connection; connections are created only for bounded setup and write operations.
		"""
		self.path = Path( cfg.LOG_PATH ).resolve( )
		self.table = str( cfg.LOG_FILE or 'Exceptions' )
		self.query = None
		self.values = None
	
	def __dir__( self ) -> List[ str ]:
		"""Return the public logger member names.

		Purpose:
			Provides a stable member list for inspection and debugging of logger configuration,
			including the configured path, table name, and write helper methods.

		Returns:
			Ordered logger member names.
		"""
		return [ 'path', 'table', 'query', 'values', 'create_table', 'write' ]
	
	def create_table( self ) -> None:
		"""Create the exception table when it does not already exist.

		Purpose:
			Ensures the logging directory and SQLite exception table exist before an exception
			record is written. The schema stores stable diagnostic fields used by Fonky modules
			and avoids raising setup failures back into application exception handlers.
		"""
		try:
			self.path.parent.mkdir( parents=True, exist_ok=True )
			self.query = f'''
				CREATE TABLE IF NOT EXISTS {self.table} (
					id INTEGER PRIMARY KEY AUTOINCREMENT,
					created TEXT,
					cause TEXT,
					module TEXT,
					method TEXT,
					message TEXT,
					info TEXT,
					trace TEXT
				)
			'''
			with sqlite3.connect( self.path ) as connection:
				connection.execute( self.query )
				connection.commit( )
		except Exception:
			return None
	
	def write( self, error: Error ) -> None:
		"""Write an error record to the logging database.

		Purpose:
			Persists a wrapped Error object to the configured SQLite database using the standard
			Fonky exception schema. Logging is intentionally failure-safe: a database or filesystem
			failure during logging is suppressed so it does not mask the original application error.

		Args:
			error (Error): Wrapped exception object containing diagnostic metadata to persist.
		"""
		try:
			self.create_table( )
			message = str( getattr( error, 'exception', '' ) )
			self.query = f'''
				INSERT INTO {self.table} (
					created,
					cause,
					module,
					method,
					message,
					info,
					trace
				)
				VALUES (?, ?, ?, ?, ?, ?, ?)
			'''
			self.values = (
					datetime.now( ).isoformat( timespec='seconds' ),
					getattr( error, 'cause', None ),
					getattr( error, 'module', None ),
					getattr( error, 'method', None ),
					message,
					getattr( error, 'info', None ),
					getattr( error, 'trace', None ),
			)
			with sqlite3.connect( self.path ) as connection:
				connection.execute( self.query, self.values )
				connection.commit( )
		except Exception:
			return None

