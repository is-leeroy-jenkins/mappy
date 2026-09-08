'''
  ******************************************************************************************
      Assembly:                Mappy
      Filename:                loaders.py
      Author:                  Terry D. Eppler
      Created:                 09-08-2026
      Last Modified By:        Terry D. Eppler
      Last Modified On:        09-08-2026
  ******************************************************************************************
  <copyright file="loaders.py" company="Terry D. Eppler">

       Mappy is a Python framework for geospatial and data workflows.

   Permission is hereby granted, free of charge, to any person obtaining a copy
   of this software and associated documentation files (the "Software"),
   to deal in the Software without restriction,
   including without limitation the rights to use,
   copy, modify, merge, publish, distribute, sublicense,
   and/or sell copies of the Software,
   and to permit persons to whom the Software is furnished to do so,
   subject to the following conditions:

   The above copyright notice and this permission notice shall be included in all
   copies or substantial portions of the Software.

   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
   INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT.
   IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
   DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
   ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
   DEALINGS IN THE SOFTWARE.

  </copyright>
  <summary>
    LangChain document loaders used by Mappy document-processing workflows.
  </summary>
  ******************************************************************************************
'''
from __future__ import annotations

from pathlib import Path
from typing import List

from langchain_core.documents import Document


def throw_if( name: str, value: object ) -> None:
	"""Validate a required runtime value.

	Purpose:
		Ensures required loader configuration is present before filesystem or parser work begins.

	Args:
		name: Argument name included in validation errors.
		value: Runtime value to validate.

	Returns:
		None: This function validates input and does not return a value.
	"""
	if value is None:
		raise ValueError( f'Argument "{name}" cannot be empty!' )

	if isinstance( value, str ) and not value.strip( ):
		raise ValueError( f'Argument "{name}" cannot be empty!' )

	if isinstance( value, ( list, tuple, dict, set ) ) and len( value ) == 0:
		raise ValueError( f'Argument "{name}" cannot be empty!' )


class Loader( ):
	"""Base local-document loader."""

	file_path: str
	documents: List[ Document ]

	def __init__( self ) -> None:
		"""Initialize loader state.

		Purpose:
			Initializes the current source path and LangChain document collection.

		Returns:
			None: This method initializes instance state.
		"""
		self.file_path = ''
		self.documents = [ ]

	def verify_exists( self, file_path: str ) -> str:
		"""Validate the selected source path.

		Purpose:
			Ensures the local source exists before constructing a LangChain loader.

		Args:
			file_path: Local document path.

		Returns:
			str: Validated local document path.
		"""
		throw_if( 'file_path', file_path )
		self.file_path = file_path
		if not Path( self.file_path ).is_file( ):
			raise FileNotFoundError( f'File not found: {self.file_path}' )
		return self.file_path

	def set_metadata( self, loader_name: str ) -> List[ Document ]:
		"""Apply consistent source metadata.

		Purpose:
			Preserves source path, source filename, and Mappy loader identity on returned documents.

		Args:
			loader_name: Public Mappy loader class name.

		Returns:
			List[Document]: Loaded LangChain documents with normalized metadata.
		"""
		throw_if( 'loader_name', loader_name )
		for document in self.documents:
			document.metadata = dict( document.metadata or { } )
			document.metadata[ 'source' ] = document.metadata.get(
				'source', Path( self.file_path ).name )
			document.metadata[ 'path' ] = self.file_path
			document.metadata[ 'loader' ] = loader_name
		return self.documents


class TextLoader( Loader ):
	"""Load UTF-8 text into LangChain documents."""

	def load( self, file_path: str ) -> List[ Document ]:
		"""Load a text document.

		Purpose:
			Reads UTF-8 text and returns one LangChain document preserving source metadata.

		Args:
			file_path: Local text-file path.

		Returns:
			List[Document]: Loaded text document.
		"""
		self.file_path = self.verify_exists( file_path )
		text = Path( self.file_path ).read_text( encoding='utf-8', errors='ignore' )
		self.documents = [ Document( page_content=text, metadata={
			'source': Path( self.file_path ).name,
			'path': self.file_path,
			'loader': 'TextLoader' } ) ]
		return self.documents


class CsvLoader( Loader ):
	"""Load CSV records into LangChain documents."""

	def load( self, file_path: str ) -> List[ Document ]:
		"""Load a CSV document.

		Purpose:
			Uses LangChain CSVLoader to convert delimited rows into LangChain documents.

		Args:
			file_path: Local CSV-file path.

		Returns:
			List[Document]: Loaded CSV row documents.
		"""
		from langchain_community.document_loaders import CSVLoader as LangChainCsvLoader

		self.file_path = self.verify_exists( file_path )
		self.documents = LangChainCsvLoader( file_path=self.file_path ).load( )
		return self.set_metadata( 'CsvLoader' )


class PdfLoader( Loader ):
	"""Load PDF pages into LangChain documents."""

	def load( self, file_path: str ) -> List[ Document ]:
		"""Load a PDF document.

		Purpose:
			Uses LangChain PyPDFLoader to convert PDF pages into LangChain documents.

		Args:
			file_path: Local PDF-file path.

		Returns:
			List[Document]: Loaded PDF page documents.
		"""
		from langchain_community.document_loaders import PyPDFLoader

		self.file_path = self.verify_exists( file_path )
		self.documents = PyPDFLoader( file_path=self.file_path ).load( )
		return self.set_metadata( 'PdfLoader' )


class ExcelLoader( Loader ):
	"""Load Excel workbooks into LangChain documents."""

	def load( self, file_path: str ) -> List[ Document ]:
		"""Load an Excel workbook.

		Purpose:
			Uses LangChain UnstructuredExcelLoader to convert workbook content into documents.

		Args:
			file_path: Local Excel-workbook path.

		Returns:
			List[Document]: Loaded workbook documents.
		"""
		from langchain_community.document_loaders import UnstructuredExcelLoader

		self.file_path = self.verify_exists( file_path )
		self.documents = UnstructuredExcelLoader( self.file_path, mode='single' ).load( )
		return self.set_metadata( 'ExcelLoader' )


class WordLoader( Loader ):
	"""Load Word documents into LangChain documents."""

	def load( self, file_path: str ) -> List[ Document ]:
		"""Load a Word document.

		Purpose:
			Uses LangChain Docx2txtLoader to convert DOCX content into documents.

		Args:
			file_path: Local Word-document path.

		Returns:
			List[Document]: Loaded Word documents.
		"""
		from langchain_community.document_loaders import Docx2txtLoader

		self.file_path = self.verify_exists( file_path )
		self.documents = Docx2txtLoader( self.file_path ).load( )
		return self.set_metadata( 'WordLoader' )


class MarkdownLoader( Loader ):
	"""Load Markdown into LangChain documents."""

	def load( self, file_path: str ) -> List[ Document ]:
		"""Load a Markdown document.

		Purpose:
			Uses LangChain UnstructuredMarkdownLoader to convert Markdown content into documents.

		Args:
			file_path: Local Markdown-file path.

		Returns:
			List[Document]: Loaded Markdown documents.
		"""
		from langchain_community.document_loaders import UnstructuredMarkdownLoader

		self.file_path = self.verify_exists( file_path )
		self.documents = UnstructuredMarkdownLoader( self.file_path, mode='single' ).load( )
		return self.set_metadata( 'MarkdownLoader' )


class HtmlLoader( Loader ):
	"""Load HTML into LangChain documents."""

	def load( self, file_path: str ) -> List[ Document ]:
		"""Load an HTML document.

		Purpose:
			Uses LangChain UnstructuredHTMLLoader to convert HTML content into documents.

		Args:
			file_path: Local HTML-file path.

		Returns:
			List[Document]: Loaded HTML documents.
		"""
		from langchain_community.document_loaders import UnstructuredHTMLLoader

		self.file_path = self.verify_exists( file_path )
		self.documents = UnstructuredHTMLLoader( self.file_path, mode='single' ).load( )
		return self.set_metadata( 'HtmlLoader' )


class JsonLoader( Loader ):
	"""Load JSON into LangChain documents."""

	def load( self, file_path: str ) -> List[ Document ]:
		"""Load a JSON document.

		Purpose:
			Uses LangChain JSONLoader to convert JSON content into LangChain documents.

		Args:
			file_path: Local JSON-file path.

		Returns:
			List[Document]: Loaded JSON documents.
		"""
		from langchain_community.document_loaders import JSONLoader as LangChainJsonLoader

		self.file_path = self.verify_exists( file_path )
		self.documents = LangChainJsonLoader(
			file_path=self.file_path,
			jq_schema='.',
			text_content=False ).load( )
		return self.set_metadata( 'JsonLoader' )


class PowerPointLoader( Loader ):
	"""Load PowerPoint presentations into LangChain documents."""

	def load( self, file_path: str ) -> List[ Document ]:
		"""Load a PowerPoint presentation.

		Purpose:
			Uses LangChain UnstructuredPowerPointLoader to convert slides into documents.

		Args:
			file_path: Local PowerPoint-file path.

		Returns:
			List[Document]: Loaded presentation documents.
		"""
		from langchain_community.document_loaders import UnstructuredPowerPointLoader

		self.file_path = self.verify_exists( file_path )
		self.documents = UnstructuredPowerPointLoader( self.file_path, mode='single' ).load( )
		return self.set_metadata( 'PowerPointLoader' )


class DocumentLoaderFactory( ):
	"""Create Mappy's supported local document loaders."""

	loader_type: str

	def __init__( self ) -> None:
		"""Initialize loader-factory state.

		Purpose:
			Initializes the selected local loader type.

		Returns:
			None: This method initializes instance state.
		"""
		self.loader_type = ''

	def create( self, loader_type: str ) -> Loader:
		"""Create the selected local loader.

		Purpose:
			Maps the finite document-source selection to the corresponding Mappy loader wrapper.

		Args:
			loader_type: Selected document-source type.

		Returns:
			Loader: Configured local-document loader instance.
		"""
		throw_if( 'loader_type', loader_type )
		self.loader_type = loader_type
		loaders = {
			'Text': TextLoader,
			'CSV': CsvLoader,
			'PDF': PdfLoader,
			'Excel': ExcelLoader,
			'Word': WordLoader,
			'Markdown': MarkdownLoader,
			'HTML': HtmlLoader,
			'JSON': JsonLoader,
			'PowerPoint': PowerPointLoader,
		}
		if self.loader_type not in loaders:
			raise ValueError( f'Unsupported document loader: {self.loader_type}' )
		return loaders[ self.loader_type ]( )
