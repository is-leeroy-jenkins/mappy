'''
  ******************************************************************************************
      Assembly:                Mappy
      Filename:                exceptions.py
      Author:                  Terry D. Eppler
      Created:                 05-31-2022

      Last Modified By:        Terry D. Eppler
      Last Modified On:        05-01-2025
  ******************************************************************************************
  <copyright file="exceptions.py" company="Terry D. Eppler">

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
    exception.py
  </summary>
  ******************************************************************************************
  '''

class MappyError( Exception ):
	"""Provide the base exception type for the Mappy framework.

	Purpose:
		Defines the common parent for framework-specific exceptions raised by Mappy
		service wrappers, gateway operations, lookup routines, and Streamlit workflows.
		Callers can catch this type when they need to handle any known Mappy exception
		without catching unrelated Python runtime errors.
	"""

class GatewayError( MappyError ):
	"""Represent an unexpected Google Maps gateway failure.

	Purpose:
		Signals failures that occur while issuing requests to external Google Maps
		services or while interpreting gateway responses. The exception separates
		transport, status, retry, and response-normalization failures from ordinary
		not-found lookup outcomes.
	"""

class NotFound( MappyError ):
	"""Represent an unresolved location, place, route, or lookup result.

	Purpose:
		Signals that a requested geospatial lookup completed without producing a usable
		application result. Service wrappers use this exception to distinguish normal
		misses from gateway failures, parsing errors, and validation errors.
	"""