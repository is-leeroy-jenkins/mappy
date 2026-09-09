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


def insert_source_processing( block: str, prefix: str, result_key: str,
	source_key: str ) -> tuple[ str, int ]:
	lines = block.splitlines( keepends=True )
	insertions: list[ tuple[ int, str ] ] = [ ]
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
			rf"st\.session_state\[ '{re.escape( source_key )}' \] = '([^']+)'", segment )
		if not source_match:
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
	return ''.join( lines ), len( insertions )


doc_path = Path( 'document_processing.py' )
doc = doc_path.read_text( encoding='utf-8' )

old_start = doc.index( 'def render_mode_processing_controls(' )
old_end = doc.index( 'def render_mode_document_tabs(', old_start )
helper = '''def render_source_processing_controls( prefix: str, result_key: str, source_key: str,
\tsource_name: str, key_prefix: str ) -> None:
\t"""Render Foo-style processing controls inside one source expander.

\tPurpose:
\t\tKeeps each API source, its processing configuration, and its Chunk/Embed/Store actions
\t\ttogether in the same expander while maintaining isolated document state per mode.

\tArgs:
\t\tprefix: Per-mode session-state prefix.
\t\tresult_key: Session-state key containing the latest structured API result.
\t\tsource_key: Session-state key identifying the latest API source.
\t\tsource_name: Source name represented by the containing expander.
\t\tkey_prefix: Unique Streamlit widget-key prefix for this source.

\tReturns:
\t\tNone: This function renders controls and updates session state.
\t"""
\tthrow_if( 'prefix', prefix )
\tthrow_if( 'result_key', result_key )
\tthrow_if( 'source_key', source_key )
\tthrow_if( 'source_name', source_name )
\tthrow_if( 'key_prefix', key_prefix )
\tinitialize_mode_document_state( prefix )
\tactive_source = str( st.session_state.get( source_key, '' ) or '' )
\tif active_source == source_name:
\t\tsync_mode_document( prefix, result_key, source_key )

\tsettings = render_processing_inputs( key_prefix )
\tchunk_col, embed_col, store_col = st.columns( 3 )
\tchunk_run = chunk_col.button( 'Chunk', icon='✂️', key=f'{key_prefix}_chunk_run',
\t\tuse_container_width=True )
\tembed_run = embed_col.button( 'Embed', icon='🧬', key=f'{key_prefix}_embed_run',
\t\tuse_container_width=True )
\tstore_run = store_col.button( 'Store', icon='🗄️', key=f'{key_prefix}_store_run',
\t\tuse_container_width=True )

\tif chunk_run:
\t\tif active_source != source_name:
\t\t\tst.warning( f'Run {source_name} before chunking.' )
\t\telse:
\t\t\ttry:
\t\t\t\tdocuments = st.session_state[ f'{prefix}_documents' ]
\t\t\t\tchunks = chunk_documents( documents, settings[ 'chunk_size' ],
\t\t\t\t\tsettings[ 'chunk_overlap' ] )
\t\t\t\tst.session_state[ f'{prefix}_chunks' ] = chunks
\t\t\t\tst.session_state[ f'{prefix}_chunk_size_used' ] = settings[ 'chunk_size' ]
\t\t\t\tst.session_state[ f'{prefix}_chunk_overlap_used' ] = settings[ 'chunk_overlap' ]
\t\t\t\tst.session_state[ f'{prefix}_embeddings' ] = [ ]
\t\t\t\tst.session_state[ f'{prefix}_embedder' ] = None
\t\t\t\tst.session_state[ f'{prefix}_vector_store' ] = None
\t\t\t\tst.success( f'Created {len( chunks ):,} chunk(s).' )
\t\t\texcept Exception as exc:
\t\t\t\tst.error( str( exc ) )

\tif embed_run:
\t\tchunks = st.session_state[ f'{prefix}_chunks' ]
\t\tif active_source != source_name:
\t\t\tst.warning( f'Run and chunk {source_name} before embedding.' )
\t\telif not chunks:
\t\t\tst.warning( 'Chunk the loaded result before embedding.' )
\t\telif settings[ 'chunk_size' ] != st.session_state[ f'{prefix}_chunk_size_used' ] or \\
\t\t\tsettings[ 'chunk_overlap' ] != st.session_state[ f'{prefix}_chunk_overlap_used' ]:
\t\t\tst.warning( 'Chunk settings changed. Run Chunk again before embedding.' )
\t\telse:
\t\t\ttry:
\t\t\t\tembedder, vectors = create_embeddings( chunks, settings[ 'provider' ],
\t\t\t\t\tsettings[ 'model' ], settings[ 'model_path' ] )
\t\t\t\tst.session_state[ f'{prefix}_embedder' ] = embedder
\t\t\t\tst.session_state[ f'{prefix}_embeddings' ] = vectors
\t\t\t\tst.session_state[ f'{prefix}_embedding_provider_used' ] = settings[ 'provider' ]
\t\t\t\tst.session_state[ f'{prefix}_embedding_model_used' ] = settings[ 'model' ]
\t\t\t\tst.session_state[ f'{prefix}_embedding_model_path_used' ] = settings[ 'model_path' ]
\t\t\t\tst.session_state[ f'{prefix}_vector_store' ] = None
\t\t\t\tst.success( f'Created {len( vectors ):,} embedding vector(s).' )
\t\t\texcept Exception as exc:
\t\t\t\tst.error( str( exc ) )

\tif store_run:
\t\tchunks = st.session_state[ f'{prefix}_chunks' ]
\t\tembedder = st.session_state[ f'{prefix}_embedder' ]
\t\tif active_source != source_name:
\t\t\tst.warning( f'Run, chunk, and embed {source_name} before storing.' )
\t\telif not chunks or embedder is None:
\t\t\tst.warning( 'Create embeddings before storing vectors.' )
\t\telif settings[ 'provider' ] != st.session_state[ f'{prefix}_embedding_provider_used' ] or \\
\t\t\tsettings[ 'model' ] != st.session_state[ f'{prefix}_embedding_model_used' ] or \\
\t\t\tsettings[ 'model_path' ] != st.session_state[ f'{prefix}_embedding_model_path_used' ]:
\t\t\tst.warning( 'Embedding settings changed. Run Embed again before storing.' )
\t\telse:
\t\t\ttry:
\t\t\t\tvector_store = store_documents( chunks, embedder, settings[ 'vector_backend' ],
\t\t\t\t\tsettings[ 'vector_target' ], settings[ 'persist_directory' ], settings[ 'namespace' ] )
\t\t\t\tst.session_state[ f'{prefix}_vector_store' ] = vector_store
\t\t\t\tst.success( f"Stored {len( chunks ):,} chunk(s) in {settings[ 'vector_backend' ]}." )
\t\t\texcept Exception as exc:
\t\t\t\tst.error( str( exc ) )


'''
doc = doc[ :old_start ] + helper + doc[ old_end: ]

state_anchor = "\t\t'document_signature': '',"
# Mode state uses dynamically generated keys; add derived-state defaults where its defaults dict is defined.
mode_defaults_anchor = "\t\tf'{prefix}_document_signature': '',"
if mode_defaults_anchor in doc:
	doc = doc.replace( mode_defaults_anchor,
		mode_defaults_anchor
		+ "\n\t\tf'{prefix}_vector_store': None,"
		+ "\n\t\tf'{prefix}_chunk_size_used': 0,"
		+ "\n\t\tf'{prefix}_chunk_overlap_used': 0,", 1 )

# Collapse Web Scraper processing controls into one expander while preserving all controls/actions.
doc = doc.replace(
	"\t\twith st.expander( label='Web Loader', icon='🌐', expanded=True ):",
	"\t\twith st.expander( label='Web Processing', icon='🌐', expanded=True ):", 1 )
for header in [
	"\n\t\twith st.expander( label='Chunking', icon='✂️', expanded=False ):",
	"\n\t\twith st.expander( label='Embeddings', icon='🧠', expanded=False ):",
	"\n\t\twith st.expander( label='Vector Storage', icon='🗄️', expanded=False ):",
]:
	if header not in doc:
		raise RuntimeError( f'Web expander anchor not found: {header}' )
	doc = doc.replace( header, '', 1 )

doc_path.write_text( doc, encoding='utf-8', newline='' )

app_path = Path( 'app.py' )
app = app_path.read_text( encoding='utf-8' )
app = app.replace( '\trender_mode_processing_controls,\n', '\trender_source_processing_controls,\n', 1 )

specs = [
	( 'Weather', 'Environmental', 'weather', 'weather_last_result', 'weather_last_source' ),
	( 'Environmental', 'Astronomical', 'env', 'env_last_result', 'env_last_source' ),
	( 'Astronomical', 'Celestial Map', 'astro', 'astro_last_result', 'astro_last_source' ),
	( 'Geological', 'Generative', 'geo', 'geo_last_result', 'geo_last_source' ),
]
counts: dict[ str, int ] = { }
for mode, next_mode, prefix, result_key, source_key in specs:
	start, end = mode_bounds( app, mode, next_mode )
	block = app[ start:end ]
	block = re.sub(
		rf"\n\t\t\trender_mode_processing_controls\( '{prefix}', '{result_key}', '{source_key}' \)\n",
		'\n', block, count=1 )
	block, count = insert_source_processing( block, prefix, result_key, source_key )
	if count == 0:
		raise RuntimeError( f'No source expanders were instrumented for {mode}.' )
	counts[ mode ] = count
	app = app[ :start ] + block + app[ end: ]

if 'render_mode_processing_controls(' in app:
	raise RuntimeError( 'Global mode-level processing controls remain in app.py.' )

app_path.write_text( app, encoding='utf-8', newline='' )
print( counts )
