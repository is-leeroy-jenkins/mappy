from pathlib import Path
import subprocess


def mode_bounds( source: str, mode: str, next_mode: str ) -> tuple[ int, int ]:
	start = source.index( f"elif mode == '{mode}':" )
	next_index = source.index( f"elif mode == '{next_mode}':", start )
	end = source.rfind( '# =============================================================================', start, next_index )
	return start, end if end > start else next_index


doc_path = Path( 'document_processing.py' )
doc = doc_path.read_text( encoding='utf-8' )
if 'import json\n' not in doc:
	doc = doc.replace( 'import math\n', 'import json\nimport math\n', 1 )

if 'def initialize_mode_document_state( prefix: str ) -> None:' not in doc:
	helpers = '''


def initialize_mode_document_state( prefix: str ) -> None:
\t"""Initialize per-mode document state."""
\tdefaults = {
\t\tf'{prefix}_documents': [ ], f'{prefix}_chunks': [ ], f'{prefix}_embeddings': [ ],
\t\tf'{prefix}_embedder': None, f'{prefix}_document_signature': '',
\t\tf'{prefix}_embedding_provider_used': '', f'{prefix}_embedding_model_used': '',
\t\tf'{prefix}_embedding_model_path_used': '',
\t}
\tfor key, value in defaults.items( ):
\t\tif key not in st.session_state:
\t\t\tst.session_state[ key ] = value


def serialize_mode_result( result: object ) -> str:
\t"""Serialize a structured API result as document text."""
\tif isinstance( result, pd.DataFrame ):
\t\treturn result.to_json( orient='records', indent=2, default_handler=str )
\tif isinstance( result, str ):
\t\treturn result
\treturn json.dumps( result, indent=2, sort_keys=True, default=str )


def sync_mode_document( prefix: str, result_key: str, source_key: str ) -> None:
\t"""Synchronize the latest API result into a LangChain Document."""
\tinitialize_mode_document_state( prefix )
\tresult = st.session_state.get( result_key )
\tif result is None or result == { } or result == [ ] or result == '':
\t\treturn
\ttext = serialize_mode_result( result )
\tsource = str( st.session_state.get( source_key, '' ) or prefix.title( ) )
\tsignature = f'{source}\\n{text}'
\tif signature == st.session_state[ f'{prefix}_document_signature' ]:
\t\treturn
\tst.session_state[ f'{prefix}_documents' ] = [
\t\tDocument( page_content=text, metadata={ 'source': source, 'mode': prefix } ) ]
\tst.session_state[ f'{prefix}_chunks' ] = [ ]
\tst.session_state[ f'{prefix}_embeddings' ] = [ ]
\tst.session_state[ f'{prefix}_embedder' ] = None
\tst.session_state[ f'{prefix}_document_signature' ] = signature


def render_mode_processing_controls( prefix: str, result_key: str, source_key: str ) -> None:
\t"""Render Foo-style chunking and embedding expanders for one API mode."""
\tsync_mode_document( prefix, result_key, source_key )
\tmodels = {
\t\t'OpenAI': [ 'text-embedding-3-small', 'text-embedding-3-large' ],
\t\t'Google Generative AI': [ 'gemini-embedding-2-preview' ],
\t\t'Mistral AI': [ 'mistral-embed' ],
\t\t'Hugging Face': [ 'sentence-transformers/all-MiniLM-L6-v2', 'sentence-transformers/all-mpnet-base-v2' ],
\t\t'Local GGUF': [ 'Local GGUF' ],
\t}
\twith st.expander( '✂️ Chunking', expanded=False ):
\t\tc1, c2 = st.columns( 2 )
\t\twith c1:
\t\t\tchunk_size = st.slider( 'Chunk Size', 100, 4000, 1000, 100,
\t\t\t\tkey=f'{prefix}_document_chunk_size' )
\t\twith c2:
\t\t\tchunk_overlap = st.slider( 'Chunk Overlap', 0, 1000, 200, 50,
\t\t\t\tkey=f'{prefix}_document_chunk_overlap' )
\t\tif st.button( 'Chunk', key=f'{prefix}_document_chunk_run', use_container_width=True ):
\t\t\tdocuments = st.session_state[ f'{prefix}_documents' ]
\t\t\tif not documents:
\t\t\t\tst.warning( 'Run a source request before chunking.' )
\t\t\telif chunk_overlap >= chunk_size:
\t\t\t\tst.error( 'Chunk Overlap must be smaller than Chunk Size.' )
\t\t\telse:
\t\t\t\tsplitter = RecursiveCharacterTextSplitter(
\t\t\t\t\tchunk_size=int( chunk_size ), chunk_overlap=int( chunk_overlap ) )
\t\t\t\tchunks = splitter.split_documents( documents )
\t\t\t\tfor index, document in enumerate( chunks, start=1 ):
\t\t\t\t\tdocument.metadata = dict( document.metadata or { } )
\t\t\t\t\tdocument.metadata[ 'chunk_id' ] = f'chunk-{index:06d}'
\t\t\t\tst.session_state[ f'{prefix}_chunks' ] = chunks
\t\t\t\tst.session_state[ f'{prefix}_embeddings' ] = [ ]
\t\t\t\tst.session_state[ f'{prefix}_embedder' ] = None
\twith st.expander( '🧠 Embeddings', expanded=False ):
\t\te1, e2 = st.columns( 2 )
\t\twith e1:
\t\t\tprovider = st.selectbox( 'Embedding Provider', list( models.keys( ) ),
\t\t\t\tindex=list( models.keys( ) ).index( 'Hugging Face' ),
\t\t\t\tkey=f'{prefix}_document_embedding_provider' )
\t\twith e2:
\t\t\tmodel = st.selectbox( 'Embedding Model', models[ provider ],
\t\t\t\tkey=f'{prefix}_document_embedding_model' )
\t\tmodel_path = ''
\t\tif provider == 'Local GGUF':
\t\t\tmodel_path = st.text_input( 'Local GGUF Model Path',
\t\t\t\tplaceholder=r'C:\\models\\embedding-model.gguf',
\t\t\t\tkey=f'{prefix}_document_embedding_model_path' )
\t\tif st.button( 'Embed', key=f'{prefix}_document_embed_run', use_container_width=True ):
\t\t\tchunks = st.session_state[ f'{prefix}_chunks' ]
\t\t\tif not chunks:
\t\t\t\tst.warning( 'Chunk the loaded result before embedding.' )
\t\t\telse:
\t\t\t\ttry:
\t\t\t\t\tembedder = EmbeddingFactory( ).create( provider, model, model_path )
\t\t\t\t\tvectors = embedder.embed_documents( [ d.page_content for d in chunks ] )
\t\t\t\t\tif len( vectors ) != len( chunks ):
\t\t\t\t\t\traise RuntimeError( 'Embedding count does not match the chunk count.' )
\t\t\t\t\tif len( { len( vector ) for vector in vectors } ) != 1:
\t\t\t\t\t\traise RuntimeError( 'Embedding vectors do not have a consistent dimension.' )
\t\t\t\t\tfor vector in vectors:
\t\t\t\t\t\tif not all( math.isfinite( float( value ) ) for value in vector ):
\t\t\t\t\t\t\traise RuntimeError( 'Embedding vectors contain non-finite values.' )
\t\t\t\t\tst.session_state[ f'{prefix}_embedder' ] = embedder
\t\t\t\t\tst.session_state[ f'{prefix}_embeddings' ] = vectors
\t\t\t\t\tst.session_state[ f'{prefix}_embedding_provider_used' ] = provider
\t\t\t\t\tst.session_state[ f'{prefix}_embedding_model_used' ] = model
\t\t\t\t\tst.session_state[ f'{prefix}_embedding_model_path_used' ] = model_path
\t\t\t\texcept Exception as exc:
\t\t\t\t\tst.error( str( exc ) )


def render_mode_document_tabs( prefix: str, loaded_label: str='📄 Loaded' ) -> None:
\t"""Render Loaded, Chunks, and Embeddings tabs for one API mode."""
\tinitialize_mode_document_state( prefix )
\tloaded_tab, chunks_tab, embeddings_tab = st.tabs(
\t\t[ loaded_label, '✂️ Chunks', '🧠 Embeddings' ] )
\twith loaded_tab:
\t\tdocuments = st.session_state[ f'{prefix}_documents' ]
\t\tif not documents:
\t\t\tst.info( 'Run a source request to load a document.' )
\t\telse:
\t\t\trows = [ {
\t\t\t\t'Document': index, 'Source': ( document.metadata or { } ).get( 'source', '' ),
\t\t\t\t'Characters': len( document.page_content ), 'Metadata': document.metadata or { },
\t\t\t\t'Text': document.page_content,
\t\t\t} for index, document in enumerate( documents, start=1 ) ]
\t\t\tst.dataframe( pd.DataFrame( rows ), use_container_width=True, hide_index=True )
\twith chunks_tab:
\t\tchunks = st.session_state[ f'{prefix}_chunks' ]
\t\tif not chunks:
\t\t\tst.info( 'Run Chunk to display document chunks.' )
\t\telse:
\t\t\trows = [ {
\t\t\t\t'Chunk': index, 'Chunk ID': ( document.metadata or { } ).get( 'chunk_id', '' ),
\t\t\t\t'Source': ( document.metadata or { } ).get( 'source', '' ),
\t\t\t\t'Characters': len( document.page_content ), 'Text': document.page_content,
\t\t\t} for index, document in enumerate( chunks, start=1 ) ]
\t\t\tst.dataframe( pd.DataFrame( rows ), use_container_width=True, hide_index=True )
\twith embeddings_tab:
\t\tvectors = st.session_state[ f'{prefix}_embeddings' ]
\t\tchunks = st.session_state[ f'{prefix}_chunks' ]
\t\tif not vectors:
\t\t\tst.info( 'Run Embed to display embedding vectors.' )
\t\telse:
\t\t\trows = [ ]
\t\t\tfor index, vector in enumerate( vectors ):
\t\t\t\tdocument = chunks[ index ]
\t\t\t\trows.append( {
\t\t\t\t\t'Chunk': index + 1,
\t\t\t\t\t'Provider': st.session_state[ f'{prefix}_embedding_provider_used' ],
\t\t\t\t\t'Model': st.session_state[ f'{prefix}_embedding_model_path_used' ] or st.session_state[ f'{prefix}_embedding_model_used' ],
\t\t\t\t\t'Dimensions': len( vector ),
\t\t\t\t\t'Source': ( document.metadata or { } ).get( 'source', '' ),
\t\t\t\t\t'Text': document.page_content, 'Vector': vector,
\t\t\t\t} )
\t\t\tst.dataframe( pd.DataFrame( rows ), use_container_width=True, hide_index=True )
'''
	doc = doc.rstrip( ) + '\n' + helpers

doc_path.write_text( doc, encoding='utf-8', newline='' )

app_path = Path( 'app.py' )
app = app_path.read_text( encoding='utf-8' )
old_import = 'from document_processing import render_document_processing, render_web_document_processing\n'
new_import = ( 'from document_processing import (\n'
	'\trender_web_document_processing,\n'
	'\trender_mode_processing_controls,\n'
	'\trender_mode_document_tabs )\n' )
if old_import not in app:
	raise RuntimeError( 'document_processing import anchor not found.' )
app = app.replace( old_import, new_import, 1 )

original = subprocess.check_output(
	[ 'git', 'show', '17999643f008d3ae48dd9fa8d44c39f67de15f9b:app.py' ], text=True )
old_start, old_end = mode_bounds( original, 'Data Upload', 'Data Management' )
new_start, new_end = mode_bounds( app, 'Data Upload', 'Data Management' )
app = app[ :new_start ] + original[ old_start:old_end ] + app[ new_end: ]

web_start, web_end = mode_bounds( app, 'Web Scraper', 'Weather' )
app = app[ :web_start ] + "elif mode == 'Web Scraper':\n\trender_web_document_processing( )\n\n" + app[ web_end: ]

specs = [
	('Weather', 'Environmental', 'weather_c2', 'weather', 'weather_last_result', 'weather_last_source'),
	('Environmental', 'Geological', 'enviro_c2', 'env', 'env_last_result', 'env_last_source'),
	('Geological', 'Astronomical', 'geo_c2', 'geo', 'geo_last_result', 'geo_last_source'),
	('Astronomical', 'Celestial Map', 'astro_c2', 'astro', 'astro_last_result', 'astro_last_source'),
]
for mode, next_mode, right_col, prefix, result_key, source_key in specs:
	start, end = mode_bounds( app, mode, next_mode )
	block = app[ start:end ]
	token = f'\t\twith {right_col}:'
	if block.count( token ) != 1:
		raise RuntimeError( f'Right-column anchor missing for {mode}.' )
	right_start = block.index( token )
	left = block[ :right_start ].rstrip( )
	block = ( left
		+ f"\n\t\t\trender_mode_processing_controls( '{prefix}', '{result_key}', '{source_key}' )\n\n"
		+ f"\t\twith {right_col}:\n"
		+ f"\t\t\trender_mode_document_tabs( '{prefix}', '📄 Loaded' )\n\n" )
	app = app[ :start ] + block + app[ end: ]

app_path.write_text( app, encoding='utf-8', newline='' )
