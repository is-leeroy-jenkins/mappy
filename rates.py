'''
  ******************************************************************************************
      Assembly:                Mappy
      Filename:                rates.py
      Author:                  Terry D. Eppler
      Created:                 05-31-2022

      Last Modified By:        Terry D. Eppler
      Last Modified On:        05-01-2025
  ******************************************************************************************
  <copyright file="rates.py" company="Terry D. Eppler">

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
    rates.py
  </summary>
  ******************************************************************************************
  '''
import time
from typing import Optional
if __package__:
	from .boogr import Error, Logger
else:
	from boogr import Error, Logger

def throw_if( name: str, value: object ) -> None:
	"""Validate that a required value is present.

	Purpose:
		Provides a lightweight guard for required runtime values used by Mappy
		utility classes. The function raises clear validation errors for missing
		objects and empty strings before downstream timing, gateway, or service logic
		uses those values.

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

class RateLimiter:
	"""Enforce a process-local query-per-second ceiling.

	Purpose:
		Provides lightweight request throttling for Google Maps and related API
		wrappers. The limiter tracks call count, last request time, elapsed time
		between calls, and total sleep time so service gateways can pause between
		outbound requests without depending on a heavier scheduler.

	Attributes:
		query_per_second: Maximum allowed query rate for the current process.
		interval: Minimum seconds required between successive requests.
		last: Timestamp of the previous completed wait operation.
		now: Timestamp captured during the current wait operation.
		delta: Elapsed seconds since the prior wait operation.
		calls: Number of times the limiter has been invoked.
		total_sleep: Total seconds slept across all wait operations.
		last_sleep: Seconds slept during the most recent wait operation.
	"""
	query_per_second: Optional[ float ]
	interval: Optional[ float ]
	last: Optional[ float ]
	now: Optional[ float ]
	delta: Optional[ float ]
	calls: Optional[ int ]
	total_sleep: Optional[ float ]
	last_sleep: Optional[ float ]
	
	def __init__( self, max: Optional[ float ] ) -> None:
		"""Initialize the rate limiter.

		Purpose:
			Stores the requested query-per-second limit and derives the minimum
			interval between outbound calls. Runtime counters are initialized so later
			``wait`` calls can track throttling behavior and accumulated sleep time.

		Args:
			max: Maximum queries per second. ``None`` or values less than or equal to
				zero disable throttling.
		"""
		self.query_per_second = float( max ) if max is not None else None
		self.interval = (1.0 / self.query_per_second
		                 if self.query_per_second and self.query_per_second > 0 else 0.0)
		self.last = 0.0
		self.now = 0.0
		self.delta = 0.0
		self.calls = 0
		self.total_sleep = 0.0
		self.last_sleep = 0.0
	
	def wait( self ) -> None:
		"""Pause long enough to remain under the configured request rate.

		Purpose:
			Updates rate-limiter counters and sleeps only when the elapsed time since
			the previous call is less than the configured interval. This method is
			called immediately before outbound API requests to reduce avoidable quota,
			throttling, and burst-rate errors.

		Raises:
			Error: Raised after logging when timing or sleep handling fails.
		"""
		try:
			self.calls += 1
			self.last_sleep = 0.0
			if self.interval is None or self.interval <= 0:
				return
			self.now = time.time( )
			self.delta = self.now - self.last
			if self.last > 0.0 and self.delta < self.interval:
				self.last_sleep = self.interval - self.delta
				time.sleep( self.last_sleep )
				self.total_sleep += self.last_sleep
			self.last = time.time( )
		except Exception as e:
			exception = Error( e )
			exception.module = 'mappy'
			exception.cause = 'RateLimiter'
			exception.method = 'wait( self ) -> None'
			Logger( ).write( exception )
			raise exception