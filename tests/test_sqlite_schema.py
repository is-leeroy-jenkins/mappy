"""SQLite compatibility regressions for the root Mappy application."""
from __future__ import annotations

import ast
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
from typing import List, Tuple, Optional
import unittest

import pandas as pd


ROOT = Path( __file__ ).resolve( ).parents[ 1 ]


class SQLiteSchemaTests( unittest.TestCase ):
	"""Exercise actual application SQL without starting Streamlit or external providers."""

	def setUp( self ) -> None:
		"""Load database functions and create an isolated SQLite fixture."""
		self.directory = tempfile.TemporaryDirectory( )
		self.addCleanup( self.directory.cleanup )
		self.path = Path( self.directory.name ) / 'data.db'
		source = ast.parse( (ROOT / 'app.py').read_text( encoding='utf-8' ) )
		names = { 'throw_if', 'initialize_database', 'ManagedConnection', 'create_connection',
			'list_tables', 'create_schema', 'list_spatial_tables', 'get_geocode_expressions',
			'count_missing_report_coordinate_rows', 'read_missing_report_locations',
			'apply_report_coordinate_updates', 'insert_data' }
		nodes = [ node for node in source.body if isinstance( node, (ast.FunctionDef, ast.ClassDef) )
			and node.name in names ]
		self.assertEqual( { node.name for node in nodes }, names )
		self.scope = { 'sqlite3': sqlite3, 'Path': Path, 'pd': pd, 'List': List,
			'Tuple': Tuple, 'Optional': Optional, 'cfg': SimpleNamespace( DB_PATH=str( self.path ) ),
			'st': SimpleNamespace( error=self.fail ) }
		exec( compile( ast.Module( body=nodes, type_ignores=[ ] ), 'app.py', 'exec' ), self.scope )
		self.scope[ 'initialize_database' ]( )
		with sqlite3.connect( self.path ) as conn:
			conn.executescript( """
				CREATE TABLE UAP (ID INTEGER PRIMARY KEY, City TEXT, State TEXT,
					CountryName TEXT, CountryCode TEXT, Location TEXT, Latitude REAL, Longitude REAL);
				CREATE TABLE Pollution (ID INTEGER PRIMARY KEY, Name TEXT, City TEXT, State TEXT,
					Latitude REAL, Longitude REAL);
				CREATE TABLE Military (ID INTEGER PRIMARY KEY, Name TEXT, StateCode TEXT,
					Component TEXT, Latitude REAL, Longitude REAL);
				CREATE TABLE Nuclear (ID INTEGER PRIMARY KEY, Name TEXT, City TEXT,
					"State/Region" TEXT, Country TEXT, Latitude REAL, Longitude REAL,
					"GeneratingCapacity(MW)" INTEGER);
				CREATE TABLE Airports (ID INTEGER PRIMARY KEY, Name TEXT, Identifier TEXT,
					City TEXT, State TEXT, Country TEXT, Longitude REAL, Latitude REAL);
				CREATE TABLE Country (ID INTEGER PRIMARY KEY, Name TEXT, Code TEXT);
				CREATE TABLE States ("\ufeffStatesId" INTEGER, Name TEXT, Code TEXT);
				INSERT INTO UAP VALUES (1, ' Paris ', '', 'France', 'FR', '', NULL, NULL);
				INSERT INTO UAP VALUES (2, 'Paris', '', 'France', 'FR', '', 0, 12);
				INSERT INTO UAP VALUES (3, 'Paris', '', 'France', 'FR', '', 100, 12);
				INSERT INTO Pollution VALUES (1, 'Test site', 'Town', 'VA', NULL, NULL);
				INSERT INTO Military VALUES (1, 'Test base', 'VA', 'Army', NULL, NULL);
				INSERT INTO Nuclear VALUES (1, 'Test plant', 'Town', 'Region', 'France', NULL, NULL, 100);
				INSERT INTO Airports VALUES (1, 'Test airport', 'TEST', 'Town', 'VA', 'US', NULL, NULL);
			""" )

	def test_table_selection_and_initialization( self ) -> None:
		"""Keep support tables intact and select only spatial tables."""
		self.assertEqual( set( self.scope[ 'list_spatial_tables' ]( ) ),
			{ 'Airports', 'Military', 'Nuclear', 'Pollution', 'UAP' } )
		self.assertEqual( len( self.scope[ 'list_tables' ]( ) ), 10 )
		with sqlite3.connect( self.path ) as conn:
			conn.execute( 'INSERT INTO Embeddings (chunk, vector) VALUES (?, ?)', ( 'test', b'\x00\xff' ) )
		self.scope[ 'initialize_database' ]( )
		with sqlite3.connect( self.path ) as conn:
			self.assertEqual( conn.execute( 'SELECT vector FROM Embeddings' ).fetchone( )[ 0 ],
				b'\x00\xff' )
			self.assertEqual( [ row[ 1 ] for row in conn.execute( 'PRAGMA table_info(Instructions)' ) ],
				[ 'PromptsId', 'Caption', 'Name', 'Text' ] )

	def test_geocode_preview_and_update( self ) -> None:
		"""Use matching SQL for every spatial schema and preserve valid coordinates."""
		for table, count in ( ('UAP', 2), ('Pollution', 1), ('Military', 1),
				('Nuclear', 1), ('Airports', 1) ):
			with self.subTest( table=table ):
				self.assertEqual( self.scope[ 'count_missing_report_coordinate_rows' ]( table ), count )
				df_preview = self.scope[ 'read_missing_report_locations' ]( table )
				self.assertEqual( int( df_preview[ 'RowCount' ].sum( ) ), count )
				df_preview[ 'Latitude' ] = 45.0
				df_preview[ 'Longitude' ] = 12.0
				df_preview[ 'Status' ] = 'Matched'
				self.assertEqual( self.scope[ 'apply_report_coordinate_updates' ]( table, df_preview ), count )
				self.assertEqual( self.scope[ 'count_missing_report_coordinate_rows' ]( table ), 0 )
		with sqlite3.connect( self.path ) as conn:
			self.assertEqual( conn.execute( 'SELECT Latitude, Longitude FROM UAP WHERE ID=2' ).fetchone( ),
				(0.0, 12.0) )

	def test_exact_column_names_and_insert_order( self ) -> None:
		"""Preserve punctuation, Unicode identifiers, and explicit column ordering."""
		self.scope[ 'insert_data' ]( 'Nuclear', pd.DataFrame( {
			'GeneratingCapacity(MW)': [ 200 ], 'Name': [ 'New plant' ], 'State/Region': [ 'New region' ] } ) )
		self.scope[ 'insert_data' ]( 'States', pd.DataFrame( {
			'Code': [ 'VA' ], '\ufeffStatesId': [ 1 ], 'Name': [ 'Virginia' ] } ) )
		with sqlite3.connect( self.path ) as conn:
			self.assertEqual( conn.execute( 'SELECT "GeneratingCapacity(MW)", "State/Region" FROM Nuclear WHERE Name=?',
				( 'New plant', ) ).fetchone( ), (200, 'New region') )
			self.assertEqual( conn.execute( 'SELECT "\ufeffStatesId", Code FROM States' ).fetchone( ),
				(1, 'VA') )


if __name__ == '__main__':
	unittest.main( )
