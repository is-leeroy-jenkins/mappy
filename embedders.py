'''
    ******************************************************************************************
      Assembly:                Mappy
      Filename:                embedders.py
      Author:                  Terry D. Eppler
      Created:                 09-08-2026
      Last Modified By:        Terry D. Eppler
      Last Modified On:        09-08-2026
    ******************************************************************************************
    <copyright file="embedders.py" company="Terry D. Eppler">

         Mappy is a Python framework for geospatial and data workflows.

     Permission is hereby granted, free of charge, to any person obtaining a copy
     of this software and associated documentation files (the “Software”),
     to deal in the Software without restriction,
     including without limitation the rights to use, copy, modify, merge, publish,
     distribute, sublicense, and/or sell copies of the Software, and to permit persons
     to whom the Software is furnished to do so, subject to the following conditions:

     The above copyright notice and this permission notice shall be included in all
     copies or substantial portions of the Software.

     THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
     INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
     PARTICULAR PURPOSE AND NON-INFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
     HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
     CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
     OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    </copyright>
    <summary>
        LangChain embedding implementations used by Mappy document workflows.
    </summary>
    ******************************************************************************************
'''
from __future__ import annotations
from pathlib import Path
from typing import Any, List

from langchain_core.embeddings import Embeddings


def throw_if( name: str, value: object ) -> None:
	"""Validate a required runtime value.

	Purpose:
		Ensures required embedding configuration and input values are present before provider or
		local-model work begins.

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


class LocalGGUFEmbeddings( Embeddings ):
	"""LangChain-compatible local GGUF embedding implementation."""

	model_path: str
	client: Any
	response: object | None

	def __init__( self, model_path: str ) -> None:
		"""Initialize the local GGUF embedding implementation.

		Purpose:
			Stores the configured model path and initializes lazy llama.cpp client state.

		Args:
			model_path (str): Filesystem path to a local GGUF embedding model.

		Returns:
			None: This method initializes instance state.
		"""
		throw_if( 'model_path', model_path )
		self.model_path = model_path
		self.client = None
		self.response = None

	def load( self ) -> None:
		"""Load the configured local GGUF model once.

		Purpose:
			Verifies the model path and lazily creates a llama.cpp client configured for embedding
			generation. Repeated calls reuse the loaded client.

		Args:
			None.

		Returns:
			None: This method initializes the local model client when needed.
		"""
		if self.client is not None:
			return

		path = Path( self.model_path )
		if not path.is_file( ):
			raise FileNotFoundError( f'Local GGUF model not found: {self.model_path}' )

		from llama_cpp import Llama

		self.client = Llama(
			model_path=self.model_path,
			embedding=True,
			verbose=False,
		)

	def embed_documents( self, texts: List[ str ] ) -> List[ List[ float ] ]:
		"""Create embeddings for document text.

		Purpose:
			Generates one local embedding vector for every supplied text value while preserving
			positional correspondence between source chunks and returned vectors.

		Args:
			texts (List[str]): Chunk text values to embed.

		Returns:
			List[List[float]]: One numeric vector for each supplied text value.
		"""
		throw_if( 'texts', texts )
		values: List[ str ] = [ ]

		for text in texts:
			throw_if( 'text', text )
			if not isinstance( text, str ):
				raise TypeError( 'Argument "texts" must contain only strings.' )
			values.append( text.strip( ) )

		self.load( )
		self.response = self.client.create_embedding( values )

		if isinstance( self.response, dict ) and 'data' in self.response:
			vectors = [ item[ 'embedding' ] for item in self.response[ 'data' ] ]
		else:
			vectors = self.response

		if not isinstance( vectors, list ) or len( vectors ) != len( values ):
			raise RuntimeError( 'Local GGUF embedding count does not match the input count.' )

		return vectors

	def embed_query( self, text: str ) -> List[ float ]:
		"""Create an embedding for query text.

		Purpose:
			Implements the LangChain query-embedding contract using the same local GGUF model used
			for document embeddings.

		Args:
			text (str): Query text to embed.

		Returns:
			List[float]: Numeric embedding vector for the supplied query.
		"""
		throw_if( 'text', text )
		if not isinstance( text, str ):
			raise TypeError( 'Argument "text" must be a string.' )

		return self.embed_documents( [ text ] )[ 0 ]


class EmbeddingFactory( ):
	"""Factory for Mappy's supported LangChain embedding implementations."""

	provider: str
	model: str
	model_path: str

	def __init__( self ) -> None:
		"""Initialize embedding provider state.

		Purpose:
			Initializes reusable provider and model state without importing optional provider SDKs.

		Args:
			None.

		Returns:
			None: This method initializes instance state.
		"""
		self.provider = ''
		self.model = ''
		self.model_path = ''

	def create( self, provider: str, model: str, model_path: str = '' ) -> Embeddings:
		"""Create the selected LangChain embedding implementation.

		Purpose:
			Lazily resolves hosted OpenAI, Google Generative AI, Mistral AI, Hugging Face, or local
			GGUF embeddings behind one common LangChain Embeddings interface.

		Args:
			provider (str): Embedding provider selected by the user.
			model (str): Hosted or Hugging Face embedding model name.
			model_path (str): Local GGUF model path used only by the Local GGUF provider.

		Returns:
			Embeddings: Configured LangChain embedding implementation.
		"""
		throw_if( 'provider', provider )
		self.provider = provider
		self.model = model
		self.model_path = model_path

		if self.provider == 'OpenAI':
			throw_if( 'model', self.model )
			from langchain_openai import OpenAIEmbeddings
			return OpenAIEmbeddings( model=self.model )

		if self.provider == 'Google Generative AI':
			throw_if( 'model', self.model )
			from langchain_google_genai import GoogleGenerativeAIEmbeddings
			return GoogleGenerativeAIEmbeddings( model=self.model )

		if self.provider == 'Mistral AI':
			throw_if( 'model', self.model )
			from langchain_mistralai import MistralAIEmbeddings
			return MistralAIEmbeddings( model=self.model )

		if self.provider == 'Hugging Face':
			throw_if( 'model', self.model )
			from langchain_huggingface import HuggingFaceEmbeddings
			return HuggingFaceEmbeddings( model_name=self.model )

		if self.provider == 'Local GGUF':
			throw_if( 'model_path', self.model_path )
			return LocalGGUFEmbeddings( model_path=self.model_path )

		raise ValueError( f'Unsupported embedding provider: {self.provider}' )
