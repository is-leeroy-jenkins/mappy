'''
	******************************************************************************************
	  Assembly:                Mappy
	  Filename:                core.py
	  Author:                  Terry D. Eppler (adapted by Bro)
	  Created:                 05-31-2022
	  Last Modified By:        Terry D. Eppler
	  Last Modified On:        08-25-2025
	******************************************************************************************
	<copyright file="core.py" company="Terry D. Eppler">
	
	     Mappy is a GIS Toolkit written in python
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
	
	 THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
	 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
	 FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT.
	 IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
	 DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
	 ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
	 DEALINGS IN THE SOFTWARE.
	
	 You can contact me at:  terryeppler@gmail.com or eppler.terry@epa.gov
	
	</copyright>
	<summary>
	    core.py — lightweight immutable result container and small core helpers
	</summary>
	******************************************************************************************
'''
from __future__ import annotations
from typing import Dict, Optional, Any
from requests import Response

def throw_if( name: str, value: object ) -> None:
	"""Validate that a required value is not ``None``.

	Purpose:
		Provides a lightweight guard for required arguments used by Mappy core
		objects and service wrappers. The function raises a clear validation error
		before downstream response, gateway, or result-container logic attempts to
		use a missing value.

	Args:
		name: Human-readable argument name used in the raised message.
		value: Runtime value to validate.

	Raises:
		ValueError: Raised when ``value`` is ``None``.
	"""
	if value is None:
		raise ValueError( f'Argument "{name}" cannot be None' )

class Result( ):
	"""Represent an HTTP response as a lightweight Mappy result object.

	Purpose:
		Captures the canonical URL, HTTP status code, response text, response
		encoding, headers, and original ``requests.Response`` object produced by
		fetcher and generator workflows. The container provides a stable shape for
		serialization, diagnostics, UI display, and downstream extraction routines.

	Attributes:
		url: Canonical response URL.
		status_code: HTTP response status code.
		text: Response body text.
		encoding: Response encoding reported by the HTTP client.
		headers: Response headers captured from the HTTP response.
		response: Original ``requests.Response`` object.
	"""
	url: Optional[ str ]
	status_code: Optional[ int ]
	text: Optional[ str ]
	encoding: Optional[ str ]
	headers: Optional[ str ]
	response: Optional[ Response ]
	
	def __init__( self, response: Response ) -> None:
		"""Initialize the response result container.

		Purpose:
			Copies response metadata and body content from a ``requests.Response``
			instance into stable instance attributes used by fetchers, crawlers,
			generators, Streamlit display logic, and serialization helpers.

		Args:
			response: HTTP response object returned by ``requests``.
		"""
		self.response = response
		self.url = response.url
		self.status_code = response.status_code
		self.text = response.text
		self.encoding = response.encoding
		self.headers = response.headers
	
	def __dir__( self ) -> list[ str ]:
		"""Return a stable public member ordering.

		Purpose:
			Provides predictable member ordering for interactive inspection,
			Streamlit display helpers, debugger views, and documentation tools that
			use ``dir`` to expose object capabilities.

		Returns:
			list[str]: Ordered public attribute and method names.
		"""
		return [ 'url',
		         'status_code',
		         'text',
		         'encoding',
		         'headers',
		         'has_html',
		         'to_dict',
		         'from_response' ]
	
	def to_dict( self ) -> Dict[ str, Any ]:
		"""Serialize the result container to a dictionary.

		Purpose:
			Produces a plain dictionary representation of the captured HTTP response
			metadata and body text. The output supports Streamlit inspection, tests,
			cache serialization, diagnostics, and downstream JSON-friendly processing.

		Returns:
			Dict[str, Any]: Dictionary containing URL, status code, text, encoding,
				and copied headers.
		"""
		return \
			{
					'url': self.url,
					'status_code': self.status_code,
					'text': self.text,
					'encoding': self.encoding,
					'headers': dict( self.headers ),
			}
	
	@property
	def has_html( self ) -> bool:
		"""Indicate whether response text is available.

		Purpose:
			Provides a simple Boolean indicator used by fetchers, crawlers, display
			logic, and diagnostics to determine whether the result carries text
			content that can be parsed, rendered, or serialized.

		Returns:
			bool: ``True`` when ``text`` is a string; otherwise ``False``.
		"""
		return isinstance( self.text, str )