from __future__ import annotations

from pathlib import Path
import re


def mode_bounds( source: str, mode: str, next_mode: str ) -> tuple[ int, int ]:
	start = source.index( f"elif mode == '{mode}':" )
	next_index = source.index( f"elif mode == '{next_mode}':", start )
	end = source.rfind( '# =============================================================================', start, next_index )
	return start, end if end > start else next_index


def source_slug( value: str ) -> str:
	return re.sub( r'[^a-z0-9]+', '_', value.lower( ) ).strip( '_' )


def ensure_source_processing( block: str, prefix: str, result_key: str,
	source_key: str ) -> tuple[ str, int, int ]:
	lines = block.splitlines( keepends=True )
	insertions: list[ tuple[ int, str ] ] = [ ]
	source_expanders = 0
	for index, line in enumerate( lines ):
		match = re.match( r'^(\t+)with st\.expander\(', line )
		if not match:
			continue
		indent = len( match.group( 1 ) )
		end = index + 1
		while end < len( lines ):
			candidate = lines[ end ]
			if candidate.strip( ):
				candidate_indent = len( candidate ) - len( candidate.lstrip( '\t' ) )
				if candidate_indent <= indent:
					break
			end += 1
		segment = ''.join( lines[ index:end ] )
		source_match = re.search(
			rf"st\.session_state\s*\[\s*'{re.escape( source_key )}'\s*\]\s*=\s*'([^']+)'",
			segment, flags=re.MULTILINE )
		if not source_match:
			continue
		source_expanders += 1
		if 'render_source_processing_controls(' in segment:
			continue
		source_name = source_match.group( 1 )
		key_prefix = f'{prefix}_{source_slug( source_name )}'
		call = (
			'\t' * ( indent + 1 ) + 'st.divider( )\n'
			+ '\t' * ( indent + 1 )
			+ f"render_source_processing_controls( '{prefix}', '{result_key}', '{source_key}', "
			+ f"'{source_name}', '{key_prefix}' )\n"
		)
		insertions.append( ( end, call ) )
	for end, call in reversed( insertions ):
		lines.insert( end, call )
	return ''.join( lines ), source_expanders, len( insertions )


app_path = Path( 'app.py' )
app = app_path.read_text( encoding='utf-8' )
specs = [
	( 'Weather', 'Environmental', 'weather', 'weather_last_result', 'weather_last_source' ),
	( 'Environmental', 'Astronomical', 'env', 'env_last_result', 'env_last_source' ),
	( 'Astronomical', 'Celestial Map', 'astro', 'astro_last_result', 'astro_last_source' ),
	( 'Geological', 'Generative', 'geo', 'geo_last_result', 'geo_last_source' ),
]
summary: dict[ str, tuple[ int, int ] ] = { }
for mode, next_mode, prefix, result_key, source_key in specs:
	start, end = mode_bounds( app, mode, next_mode )
	block = app[ start:end ]
	block, source_expanders, inserted = ensure_source_processing(
		block, prefix, result_key, source_key )
	summary[ mode ] = ( source_expanders, inserted )
	app = app[ :start ] + block + app[ end: ]

# Verify every source-producing expander has exactly one processing call.
for mode, next_mode, prefix, result_key, source_key in specs:
	start, end = mode_bounds( app, mode, next_mode )
	block = app[ start:end ]
	lines = block.splitlines( keepends=True )
	for index, line in enumerate( lines ):
		match = re.match( r'^(\t+)with st\.expander\(', line )
		if not match:
			continue
		indent = len( match.group( 1 ) )
		end_index = index + 1
		while end_index < len( lines ):
			candidate = lines[ end_index ]
			if candidate.strip( ):
				candidate_indent = len( candidate ) - len( candidate.lstrip( '\t' ) )
				if candidate_indent <= indent:
					break
			end_index += 1
		segment = ''.join( lines[ index:end_index ] )
		source_match = re.search(
			rf"st\.session_state\s*\[\s*'{re.escape( source_key )}'\s*\]\s*=\s*'([^']+)'",
			segment, flags=re.MULTILINE )
		if source_match and segment.count( 'render_source_processing_controls(' ) != 1:
			raise RuntimeError(
				f"{mode} source expander '{source_match.group( 1 )}' does not contain exactly one processing control block." )

app_path.write_text( app, encoding='utf-8', newline='' )
print( summary )
