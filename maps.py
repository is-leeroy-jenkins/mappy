'''
  ******************************************************************************************
      Assembly:                Mappy
      Filename:                maps.py
      Author:                  Terry D. Eppler
      Created:                 05-31-2022

      Last Modified By:        Terry D. Eppler
      Last Modified On:        05-01-2025
  ******************************************************************************************
  <copyright file="maps.py" company="Terry D. Eppler">

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
    maps.py
  </summary>
  ******************************************************************************************
'''
import time
from typing import Dict, Optional
import requests
if __package__:
	from .exceptions import GatewayError
else:
	from exceptions import GatewayError
if __package__:
	from .rates import RateLimiter
else:
	from rates import RateLimiter
if __package__:
	from .boogr import Error, Logger
else:
	from boogr import Error, Logger
if __package__:
	from . import config as cfg
else:
	import config as cfg

def throw_if( name: str, value: object ) -> None:
	"""Validate that a required gateway value is present.

	Purpose:
		Provides a lightweight guard for required Google Maps gateway inputs. The
		function prevents missing endpoints, empty parameter dictionaries, and blank
		string values from reaching outbound request construction.

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

class Maps( ):
	"""Provide the central Google Maps Web Services gateway.

	Purpose:
		Wraps Google Maps HTTP request execution behind a shared gateway used by
		geocoding, Places, Distance Matrix, Static Maps, Time Zone, spreadsheet
		enrichment, and Streamlit workflows. The class stores request configuration,
		applies process-local rate limiting, injects the configured API key, retries
		transient failures with exponential backoff, and records response diagnostics
		for downstream inspection.

	Attributes:
		base_url: Base Google Maps API URL.
		endpoint: Endpoint path used for the active request.
		params: Query parameters supplied by the caller before API-key injection.
		api_key: Google Maps Platform API key read from configuration.
		query_per_second: Optional request-rate ceiling.
		retries: Maximum retry attempts for transient failures.
		min: Initial retry backoff in seconds.
		max: Maximum retry backoff in seconds.
		timeout: HTTP request timeout in seconds.
		url: Fully qualified request URL for the active endpoint.
		session: Requests session used for outbound HTTP calls.
		limiter: Rate limiter invoked before outbound requests.
		query: Final query parameters sent with the active request.
		response: Most recent HTTP response object.
		last_url: Most recent request URL.
		last_query: Most recent query parameters after API-key injection.
		last_status: Most recent HTTP status code.
		last_elapsed_ms: Most recent request duration in milliseconds.
		last_payload_status: Most recent Google payload status value.
		last_payload_error: Most recent Google payload error message.
	"""
	base_url: Optional[ str ]
	endpoint: Optional[ str ]
	params: Optional[ Dict[ str, str ] ]
	api_key: str
	query_per_second: Optional[ float ]
	retries: Optional[ int ]
	min: Optional[ float ]
	max: Optional[ float ]
	timeout: Optional[ float ]
	url: Optional[ str ]
	session: Optional[ requests.Session ]
	limiter: Optional[ RateLimiter ]
	query: Optional[ Dict[ str, str ] ]
	response: Optional[ requests.Response ]
	last_url: Optional[ str ]
	last_query: Optional[ Dict[ str, str ] ]
	last_status: Optional[ int ]
	last_elapsed_ms: Optional[ float ]
	last_payload_status: Optional[ str ]
	last_payload_error: Optional[ str ]
	
	BASE = 'https://maps.googleapis.com/maps/api'
	
	def __init__( self, qps: Optional[ float ] = 5.0, retries: int = 5,
			min: float = 1.0, max: float = 30.0, timeout: float = 15.0 ) -> None:
		"""Initialize the Google Maps gateway.

		Purpose:
			Creates the shared HTTP session, rate limiter, retry settings, timeout
			settings, and diagnostic fields used by later gateway requests. The
			constructor reads the Google Maps API key from configuration and prepares
			the instance for reuse by Mappy service wrappers.

		Args:
			qps: Maximum queries per second. ``None`` or non-positive values disable
				throttling.
			retries: Maximum number of retry attempts for transient HTTP or Google
				payload failures.
			min: Initial exponential-backoff delay in seconds.
			max: Maximum exponential-backoff delay in seconds.
			timeout: HTTP request timeout in seconds.
		"""
		self.api_key = cfg.GOOGLEMAPS_API_KEY
		self.limiter = RateLimiter( qps )
		self.retries = retries
		self.min = min
		self.max = max
		self.timeout = timeout
		self.session = requests.Session( )
		self.base_url = self.BASE
		self.endpoint = None
		self.params = None
		self.url = None
		self.query = None
		self.response = None
		self.last_url = None
		self.last_query = None
		self.last_status = None
		self.last_elapsed_ms = None
		self.last_payload_status = None
		self.last_payload_error = None
	
	def request( self, endpoint: str, params: Dict[ str, str ] ) -> Dict | None:
		"""Execute a Google Maps API GET request.

		Purpose:
			Builds and sends a request to the selected Google Maps Web Services
			endpoint using caller-supplied query parameters plus the configured API
			key. The method rate-limits outbound calls, records request and response
			diagnostics, retries transient HTTP and Google payload failures with
			exponential backoff, normalizes hard Google API status failures into
			``GatewayError``, and returns the parsed JSON payload on success.

		Args:
			endpoint: Endpoint path such as ``geocode/json`` or
				``distancematrix/json``.
			params: Query parameters for the request before API-key injection.

		Returns:
			Dict | None: Parsed JSON response payload on success.

		Raises:
			Error: Raised after the exception is wrapped and written to the
				application logger.
		"""
		try:
			throw_if( 'endpoint', endpoint )
			throw_if( 'params', params )
			self.endpoint = endpoint
			self.params = params
			self.url = f'{self.base_url}/{self.endpoint}'
			self.last_url = self.url
			attempt = 0
			backoff = self.min
			while True:
				self.limiter.wait( )
				try:
					self.query = dict( self.params or { } )
					self.query[ 'key' ] = self.api_key
					self.last_query = dict( self.query )
					start = time.perf_counter( )
					self.response = self.session.get( self.url, params=self.query,
						timeout=self.timeout )
					elapsed = time.perf_counter( ) - start
					self.last_elapsed_ms = round( elapsed * 1000.0, 3 )
					self.last_status = self.response.status_code
					if self.last_status != 200:
						if self.last_status in (408, 429, 500, 502, 503, 504):
							raise GatewayError( f'Transient HTTP {self.last_status}: '
							                    f'{self.response.text[ :200 ]}' )
						
						raise GatewayError(
							f'HTTP {self.last_status}: {self.response.text[ :200 ]}' )
					
					payload = self.response.json( )
					self.last_payload_status = None
					self.last_payload_error = None
					if isinstance( payload, dict ):
						payload_status = str( payload.get( 'status', '' ) or '' ).strip( )
						payload_error = str( payload.get( 'error_message', '' ) or '' ).strip( )
						self.last_payload_status = payload_status
						self.last_payload_error = payload_error
						hard_failures = {
								'REQUEST_DENIED',
								'OVER_DAILY_LIMIT',
								'OVER_QUERY_LIMIT',
								'INVALID_REQUEST',
								'MAX_ELEMENTS_EXCEEDED',
								'MAX_DIMENSIONS_EXCEEDED',
								'UNKNOWN_ERROR'
						}
						if payload_status in hard_failures:
							message = payload_error or f'Google API status: {payload_status}'
							if payload_status in ('OVER_QUERY_LIMIT', 'UNKNOWN_ERROR'):
								raise GatewayError(
									f'Transient Google API status {payload_status}: {message}' )
							
							raise GatewayError( f'Google API status {payload_status}: {message}' )
					
					return payload
				except (requests.Timeout, requests.ConnectionError, GatewayError) as ex:
					attempt += 1
					if attempt > self.retries:
						raise GatewayError( f'Exceeded retries: {ex}' ) from ex
					
					time.sleep( backoff )
					backoff = min( backoff * 2, self.max )
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'Maps'
			exception.method = 'request( self, endpoint: str, params: Dict[ str, str ] ) -> Dict | None'
			Logger( ).write( exception )
			raise exception