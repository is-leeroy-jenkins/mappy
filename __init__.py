'''
	******************************************************************************************
	  Assembly:                Mappy
	  Filename:                places.py
	  Author:                  Terry D. Eppler
	  Created:                 05-31-2022
	
	  Last Modified By:        Terry D. Eppler
	  Last Modified On:        05-01-2025
	******************************************************************************************
	<copyright file="places.py" company="Terry D. Eppler">
	
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
	places.py
	</summary>
	******************************************************************************************
'''

from .exceptions import MappyError, GatewayError, NotFound  # noqa: F401
from .rates import RateLimiter  # noqa: F401
from .caches import BaseCache, InMemoryCache, SQLiteCache  # noqa: F401
from .maps import Maps  # noqa: F401
from .geocode import Geocoder  # noqa: F401
from .places import Places  # noqa: F401
from .distances import DistanceMatrix  # noqa: F401
from .timezones import Timezone  # noqa: F401
from .staticmaps import StaticMap  # noqa: F401
from .excel import Excel  # noqa: F401

__version__ = "0.2.0"












