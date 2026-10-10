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

from importlib import import_module

__version__ = '0.2.0'
PUBLIC_INTERFACES = {
    'MappyError': ('exceptions', 'MappyError'),
    'GatewayError': ('exceptions', 'GatewayError'),
    'NotFound': ('exceptions', 'NotFound'),
    'RateLimiter': ('rates', 'RateLimiter'),
    'BaseCache': ('caches', 'BaseCache'),
    'InMemoryCache': ('caches', 'InMemoryCache'),
    'SQLiteCache': ('caches', 'SQLiteCache'),
    'Maps': ('maps', 'Maps'),
    'Geocoder': ('geocode', 'Geocoder'),
    'Place': ('places', 'Place'),
    'Places': ('places', 'Place'),
    'DistanceMatrix': ('distances', 'DistanceMatrix'),
    'Timezone': ('timezones', 'Timezone'),
    'StaticMap': ('staticmaps', 'StaticMap'),
    'Excel': ('excel', 'Excel'),
}
__all__ = list( PUBLIC_INTERFACES )


def __getattr__( name: str ) -> object:
    """Resolve a public framework interface without initializing unused providers.

    Args:
        name (str): Requested public class name.

    Returns:
        object: Framework class, including the legacy Places alias.

    Raises:
        AttributeError: The name is not a public framework interface.
    """
    if name in PUBLIC_INTERFACES:
        module_name, member_name = PUBLIC_INTERFACES[ name ]
        module = import_module( '.' + module_name, __name__ )
        return getattr( module, member_name )
    raise AttributeError( f'Module {__name__} has no attribute {name}' )
