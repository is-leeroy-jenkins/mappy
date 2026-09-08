from pathlib import Path

FETCHERS = Path('fetchers.py')
APP = Path('app.py')


def update_fetchers() -> None:
    source = FETCHERS.read_text(encoding='utf-8')

    import_line = 'from langchain_community.document_loaders import UnstructuredURLLoader\n'
    anchor = 'from langchain_community.retrievers import ArxivRetriever, WikipediaRetriever\n'
    if import_line not in source:
        if anchor not in source:
            raise RuntimeError('Unable to locate fetchers import anchor.')
        source = source.replace(anchor, import_line + anchor, 1)

    start = source.index('\tdef fetch( self, url: str, time: int = 10 ) -> Result | None:', source.index('class WebFetcher'))
    end = source.index('\n\tdef html_to_text(', start)

    replacement = '''\tdef fetch( self, url: str, time: int = 10 ) -> List[ Document ]:
\t\t"""Load a web resource into LangChain documents.
\t\t
\t\tPurpose:
\t\t\tLoads the requested URL with LangChain's UnstructuredURLLoader and returns document
\t\t\tobjects that can flow directly into chunking, embedding, and vector storage.
\t\t
\t\tArgs:
\t\t\turl: Web resource URL to load.
\t\t\ttime: Retained request-timeout setting for WebFetcher API compatibility.
\t\t
\t\tReturns:
\t\t\tList[Document]: LangChain documents produced from the requested URL.
\t\t
\t\tRaises:
\t\t\tError: Raised after validation or document loading fails.
\t\t"""
\t\ttry:
\t\t\tself.url = self.validate_required_string( 'url', url )
\t\t\tself.timeout = self.validate_positive_integer( 'time', time )
\t\t\tloader = UnstructuredURLLoader(
\t\t\t\turls=[ self.url ],
\t\t\t\tcontinue_on_failure=False,
\t\t\t\tmode='single',
\t\t\t\tshow_progress_bar=False,
\t\t\t)
\t\t\tdocuments = loader.load( )
\t\t\tif not documents:
\t\t\t\traise ValueError( f'No document content was returned for URL: {self.url}' )
\t\t\t
\t\t\tfor document in documents:
\t\t\t\tdocument.metadata = dict( document.metadata or { } )
\t\t\t\tdocument.metadata[ 'source' ] = document.metadata.get( 'source', self.url )
\t\t\t\tdocument.metadata[ 'url' ] = document.metadata.get( 'url', self.url )
\t\t\t
\t\t\treturn documents
\t\t
\t\texcept Exception as exc:
\t\t\texception = Error( exc )
\t\t\texception.module = 'fetchers'
\t\t\texception.cause = 'WebFetcher'
\t\t\texception.method = 'fetch( self, url: str, time: int=10 ) -> List[ Document ]'
\t\t\tLogger( ).write( exception )
\t\t\traise exception
'''

    source = source[:start] + replacement + source[end:]
    FETCHERS.write_text(source, encoding='utf-8')


def update_app() -> None:
    source = APP.read_text(encoding='utf-8')

    if 'import math\n' not in source:
        source = source.replace('import json\n', 'import json\nimport math\n', 1)

    integration_imports = (
        'from langchain_text_splitters import RecursiveCharacterTextSplitter\n'
        'from embedders import EmbeddingFactory\n'
        'from stores.vector import ChromaStore, PineconeStore\n'
    )
    anchor = 'from generators import Chat, Claude, Grok, Mistral, Gemini\n'
    if integration_imports not in source:
        if anchor not in source:
            raise RuntimeError('Unable to locate app import anchor.')
        source = source.replace(anchor, anchor + integration_imports, 1)

    start = source.index("elif mode == 'Web Scraper':")
    weather_marker = '# ==============================================================================\n# WEATHER MODE\n# =============================================================================='
    end = source.index(weather_marker, start)

    block = '''elif mode == 'Web Scraper':
\tleft, center, right = st.columns( [ 0.05, 0.9, 0.05 ] )
\twith center:
\t\tst.subheader( '🕷️ Web Document Processing' )
\t\tst.divider( )
\t\t
\t\tdefaults = {
\t\t\t'web_documents': [ ],
\t\t\t'web_document_url': '',
\t\t\t'web_chunks': [ ],
\t\t\t'web_embeddings': [ ],
\t\t\t'web_embedder': None,
\t\t\t'web_vector_store': None,
\t\t\t'web_chunk_size_used': 0,
\t\t\t'web_chunk_overlap_used': 0,
\t\t\t'web_embedding_provider_used': '',
\t\t\t'web_embedding_model_used': '',
\t\t\t'web_embedding_model_path_used': '',
\t\t}
\t\tfor key, value in defaults.items( ):
\t\t\tif key not in st.session_state:
\t\t\t\tst.session_state[ key ] = value
\t\t
\t\tembedding_models = {
\t\t\t'OpenAI': [ 'text-embedding-3-small', 'text-embedding-3-large' ],
\t\t\t'Google Generative AI': [ 'gemini-embedding-2-preview' ],
\t\t\t'Mistral AI': [ 'mistral-embed' ],
\t\t\t'Hugging Face': [
\t\t\t\t'sentence-transformers/all-MiniLM-L6-v2',
\t\t\t\t'sentence-transformers/all-mpnet-base-v2',
\t\t\t],
\t\t\t'Local GGUF': [ 'Local GGUF' ],
\t\t}
\t\t
\t\tcontrol_col, output_col = st.columns( [ 0.42, 0.58 ], border=True, gap='small' )
\t\t
\t\twith control_col:
\t\t\tst.markdown( '##### Source' )
\t\t\ttarget_url = st.text_input(
\t\t\t\t'Target URL',
\t\t\t\tplaceholder='https://example.com',
\t\t\t\tkey='web_document_url_input' )
\t\t\trequest_timeout = st.slider(
\t\t\t\t'Request Timeout',
\t\t\t\tmin_value=1,
\t\t\t\tmax_value=120,
\t\t\t\tvalue=10,
\t\t\t\tstep=1,
\t\t\t\tkey='web_document_timeout' )
\t\t\t
\t\t\tfetch_col, clear_col = st.columns( 2 )
\t\t\twith fetch_col:
\t\t\t\tfetch_document = st.button(
\t\t\t\t\t'Fetch',
\t\t\t\t\ticon='🌐',
\t\t\t\t\tkey='web_document_fetch',
\t\t\t\t\tuse_container_width=True )
\t\t\twith clear_col:
\t\t\t\tclear_document = st.button(
\t\t\t\t\t'Clear',
\t\t\t\t\tkey='web_document_clear',
\t\t\t\t\tuse_container_width=True )
\t\t\t
\t\t\tif clear_document:
\t\t\t\tfor key, value in defaults.items( ):
\t\t\t\t\tst.session_state[ key ] = value
\t\t\t\tst.rerun( )
\t\t\t
\t\t\tif fetch_document:
\t\t\t\ttry:
\t\t\t\t\tif not target_url or not target_url.strip( ):
\t\t\t\t\t\traise ValueError( 'A target URL is required.' )
\t\t\t\t\tfetcher = WebFetcher( )
\t\t\t\t\tdocuments = fetcher.fetch(
\t\t\t\t\t\ttarget_url.strip( ),
\t\t\t\t\t\ttime=int( request_timeout ) )
\t\t\t\t\tst.session_state.web_documents = documents
\t\t\t\t\tst.session_state.web_document_url = target_url.strip( )
\t\t\t\t\tst.session_state.web_chunks = [ ]
\t\t\t\t\tst.session_state.web_embeddings = [ ]
\t\t\t\t\tst.session_state.web_embedder = None
\t\t\t\t\tst.session_state.web_vector_store = None
\t\t\t\t\tst.success( f'Loaded {len( documents ):,} LangChain document(s).' )
\t\t\t\texcept Exception as exc:
\t\t\t\t\tst.error( str( exc ) )
\t\t\t
\t\t\tset_blue_divider( )
\t\t\tst.markdown( '##### Chunking' )
\t\t\tchunk_col1, chunk_col2 = st.columns( 2 )
\t\t\twith chunk_col1:
\t\t\t\tchunk_size = st.slider(
\t\t\t\t\t'Chunk Size',
\t\t\t\t\tmin_value=100,
\t\t\t\t\tmax_value=4000,
\t\t\t\t\tvalue=1000,
\t\t\t\t\tstep=100,
\t\t\t\t\tkey='web_chunk_size' )
\t\t\twith chunk_col2:
\t\t\t\tchunk_overlap = st.slider(
\t\t\t\t\t'Chunk Overlap',
\t\t\t\t\tmin_value=0,
\t\t\t\t\tmax_value=1000,
\t\t\t\t\tvalue=200,
\t\t\t\t\tstep=50,
\t\t\t\t\tkey='web_chunk_overlap' )
\t\t\t
\t\t\tif st.button( 'Chunk', key='web_chunk_run', use_container_width=True ):
\t\t\t\tif not st.session_state.web_documents:
\t\t\t\t\tst.warning( 'Fetch a web document before chunking.' )
\t\t\t\telif chunk_overlap >= chunk_size:
\t\t\t\t\tst.error( 'Chunk Overlap must be smaller than Chunk Size.' )
\t\t\t\telse:
\t\t\t\t\tsplitter = RecursiveCharacterTextSplitter(
\t\t\t\t\t\tchunk_size=int( chunk_size ),
\t\t\t\t\t\tchunk_overlap=int( chunk_overlap ) )
\t\t\t\t\tchunks = splitter.split_documents( st.session_state.web_documents )
\t\t\t\t\tfor index, document in enumerate( chunks, start=1 ):
\t\t\t\t\t\tdocument.metadata = dict( document.metadata or { } )
\t\t\t\t\t\tdocument.metadata[ 'chunk_id' ] = f'chunk-{index:06d}'
\t\t\t\t\tst.session_state.web_chunks = chunks
\t\t\t\t\tst.session_state.web_chunk_size_used = int( chunk_size )
\t\t\t\t\tst.session_state.web_chunk_overlap_used = int( chunk_overlap )
\t\t\t\t\tst.session_state.web_embeddings = [ ]
\t\t\t\t\tst.session_state.web_embedder = None
\t\t\t\t\tst.session_state.web_vector_store = None
\t\t\t\t\tst.success( f'Created {len( chunks ):,} chunk(s).' )
\t\t\t
\t\t\tset_blue_divider( )
\t\t\tst.markdown( '##### Embeddings' )
\t\t\tembed_col1, embed_col2 = st.columns( 2 )
\t\t\twith embed_col1:
\t\t\t\tprovider = st.selectbox(
\t\t\t\t\t'Embedding Provider',
\t\t\t\t\toptions=list( embedding_models.keys( ) ),
\t\t\t\t\tindex=list( embedding_models.keys( ) ).index( 'Hugging Face' ),
\t\t\t\t\tkey='web_embedding_provider' )
\t\t\twith embed_col2:
\t\t\t\tmodel = st.selectbox(
\t\t\t\t\t'Embedding Model',
\t\t\t\t\toptions=embedding_models[ provider ],
\t\t\t\t\tkey='web_embedding_model' )
\t\t\t
\t\t\tmodel_path = ''
\t\t\tif provider == 'Local GGUF':
\t\t\t\tmodel_path = st.text_input(
\t\t\t\t\t'Local GGUF Model Path',
\t\t\t\t\tvalue='',
\t\t\t\t\tplaceholder=r'C:\\models\\embedding-model.gguf',
\t\t\t\t\tkey='web_embedding_model_path' )
\t\t\t
\t\t\tif st.button( 'Embed', key='web_embed_run', use_container_width=True ):
\t\t\t\tif not st.session_state.web_chunks:
\t\t\t\t\tst.warning( 'Chunk the web document before embedding.' )
\t\t\t\telif (
\t\t\t\t\tint( chunk_size ) != st.session_state.web_chunk_size_used
\t\t\t\t\tor int( chunk_overlap ) != st.session_state.web_chunk_overlap_used
\t\t\t\t):
\t\t\t\t\tst.warning( 'Chunk settings changed. Run Chunk again before embedding.' )
\t\t\t\telse:
\t\t\t\t\ttry:
\t\t\t\t\t\tfactory = EmbeddingFactory( )
\t\t\t\t\t\tembedder = factory.create( provider, model, model_path )
\t\t\t\t\t\ttexts = [ document.page_content for document in st.session_state.web_chunks ]
\t\t\t\t\t\tvectors = embedder.embed_documents( texts )
\t\t\t\t\t\tif len( vectors ) != len( st.session_state.web_chunks ):
\t\t\t\t\t\t\traise RuntimeError( 'Embedding count does not match the chunk count.' )
\t\t\t\t\t\tdimensions = { len( vector ) for vector in vectors }
\t\t\t\t\t\tif len( dimensions ) != 1:
\t\t\t\t\t\t\traise RuntimeError( 'Embedding vectors do not have a consistent dimension.' )
\t\t\t\t\t\tfor vector in vectors:
\t\t\t\t\t\t\tif not all( math.isfinite( float( value ) ) for value in vector ):
\t\t\t\t\t\t\t\traise RuntimeError( 'Embedding vectors contain non-finite values.' )
\t\t\t\t\t\tst.session_state.web_embedder = embedder
\t\t\t\t\t\tst.session_state.web_embeddings = vectors
\t\t\t\t\t\tst.session_state.web_embedding_provider_used = provider
\t\t\t\t\t\tst.session_state.web_embedding_model_used = model
\t\t\t\t\t\tst.session_state.web_embedding_model_path_used = model_path
\t\t\t\t\t\tst.session_state.web_vector_store = None
\t\t\t\t\t\tst.success( f'Created {len( vectors ):,} embedding vector(s).' )
\t\t\t\t\texcept Exception as exc:
\t\t\t\t\t\tst.error( str( exc ) )
\t\t\t
\t\t\tset_blue_divider( )
\t\t\tst.markdown( '##### Vector Storage' )
\t\t\tstore_col1, store_col2 = st.columns( 2 )
\t\t\twith store_col1:
\t\t\t\tvector_backend = st.selectbox(
\t\t\t\t\t'Vector Store',
\t\t\t\t\toptions=[ 'Chroma', 'Pinecone' ],
\t\t\t\t\tkey='web_vector_backend' )
\t\t\twith store_col2:
\t\t\t\tif vector_backend == 'Chroma':
\t\t\t\t\tvector_target = st.text_input(
\t\t\t\t\t\t'Collection Name',
\t\t\t\t\t\tvalue='mappy-web-documents',
\t\t\t\t\t\tkey='web_chroma_collection' )
\t\t\t\telse:
\t\t\t\t\tvector_target = st.text_input(
\t\t\t\t\t\t'Index Name',
\t\t\t\t\t\tvalue='',
\t\t\t\t\t\tkey='web_pinecone_index' )
\t\t\t
\t\t\tif vector_backend == 'Chroma':
\t\t\t\tpersist_directory = st.text_input(
\t\t\t\t\t'Persistence Directory',
\t\t\t\t\tvalue='stores/chroma',
\t\t\t\t\tkey='web_chroma_directory' )
\t\t\t\tnamespace = ''
\t\t\telse:
\t\t\t\tpersist_directory = ''
\t\t\t\tnamespace = st.text_input(
\t\t\t\t\t'Namespace',
\t\t\t\t\tvalue='',
\t\t\t\t\tkey='web_pinecone_namespace' )
\t\t\t
\t\t\tif st.button( 'Store', key='web_store_run', use_container_width=True ):
\t\t\t\tcurrent_model_path = model_path if provider == 'Local GGUF' else ''
\t\t\t\tif not st.session_state.web_chunks:
\t\t\t\t\tst.warning( 'Chunk the web document before storage.' )
\t\t\t\telif st.session_state.web_embedder is None or not st.session_state.web_embeddings:
\t\t\t\t\tst.warning( 'Embed the current chunks before storage.' )
\t\t\t\telif (
\t\t\t\t\tprovider != st.session_state.web_embedding_provider_used
\t\t\t\t\tor model != st.session_state.web_embedding_model_used
\t\t\t\t\tor current_model_path != st.session_state.web_embedding_model_path_used
\t\t\t\t):
\t\t\t\t\tst.warning( 'Embedding settings changed. Run Embed again before storage.' )
\t\t\t\telse:
\t\t\t\t\ttry:
\t\t\t\t\t\tif vector_backend == 'Chroma':
\t\t\t\t\t\t\tstore = ChromaStore( )
\t\t\t\t\t\t\tst.session_state.web_vector_store = store.create(
\t\t\t\t\t\t\t\tst.session_state.web_chunks,
\t\t\t\t\t\t\t\tst.session_state.web_embedder,
\t\t\t\t\t\t\t\tvector_target,
\t\t\t\t\t\t\t\tpersist_directory )
\t\t\t\t\t\telse:
\t\t\t\t\t\t\tapi_key = getattr( cfg, 'PINECONE_API_KEY', '' ) or os.getenv( 'PINECONE_API_KEY', '' )
\t\t\t\t\t\t\tstore = PineconeStore( )
\t\t\t\t\t\t\tst.session_state.web_vector_store = store.create(
\t\t\t\t\t\t\t\tst.session_state.web_chunks,
\t\t\t\t\t\t\t\tst.session_state.web_embedder,
\t\t\t\t\t\t\t\tvector_target,
\t\t\t\t\t\t\t\tnamespace,
\t\t\t\t\t\t\t\tapi_key )
\t\t\t\t\t\tst.success( f'Stored {len( st.session_state.web_chunks ):,} chunk(s) in {vector_backend}.' )
\t\t\t\t\texcept Exception as exc:
\t\t\t\t\t\tst.error( str( exc ) )
\t\t
\t\twith output_col:
\t\t\tdocument_tab, chunks_tab, embeddings_tab = st.tabs( [
\t\t\t\t'📄 Document',
\t\t\t\t'✂️ Chunks',
\t\t\t\t'🧠 Embeddings',
\t\t\t] )
\t\t\t
\t\t\twith document_tab:
\t\t\t\tif not st.session_state.web_documents:
\t\t\t\t\tst.info( 'Fetch a URL to display LangChain documents.' )
\t\t\t\telse:
\t\t\t\t\tdocument_rows = [ ]
\t\t\t\t\tfor index, document in enumerate( st.session_state.web_documents, start=1 ):
\t\t\t\t\t\tdocument_rows.append( {
\t\t\t\t\t\t\t'Document': index,
\t\t\t\t\t\t\t'Source': ( document.metadata or { } ).get( 'source', '' ),
\t\t\t\t\t\t\t'Characters': len( document.page_content ),
\t\t\t\t\t\t\t'Metadata': document.metadata or { },
\t\t\t\t\t\t\t'Text': document.page_content,
\t\t\t\t\t\t} )
\t\t\t\t\tst.dataframe( pd.DataFrame( document_rows ), use_container_width=True, hide_index=True )
\t\t\t
\t\t\twith chunks_tab:
\t\t\t\tif not st.session_state.web_chunks:
\t\t\t\t\tst.info( 'Run Chunk to display document chunks.' )
\t\t\t\telse:
\t\t\t\t\tchunk_rows = [ ]
\t\t\t\t\tfor index, document in enumerate( st.session_state.web_chunks, start=1 ):
\t\t\t\t\t\tchunk_rows.append( {
\t\t\t\t\t\t\t'Chunk': index,
\t\t\t\t\t\t\t'Chunk ID': ( document.metadata or { } ).get( 'chunk_id', '' ),
\t\t\t\t\t\t\t'Source': ( document.metadata or { } ).get( 'source', '' ),
\t\t\t\t\t\t\t'Characters': len( document.page_content ),
\t\t\t\t\t\t\t'Text': document.page_content,
\t\t\t\t\t\t} )
\t\t\t\t\tst.dataframe( pd.DataFrame( chunk_rows ), use_container_width=True, hide_index=True )
\t\t\t
\t\t\twith embeddings_tab:
\t\t\t\tif not st.session_state.web_embeddings:
\t\t\t\t\tst.info( 'Run Embed to display embedding vectors.' )
\t\t\t\telse:
\t\t\t\t\tembedding_rows = [ ]
\t\t\t\t\tfor index, vector in enumerate( st.session_state.web_embeddings ):
\t\t\t\t\t\tdocument = st.session_state.web_chunks[ index ]
\t\t\t\t\t\tembedding_rows.append( {
\t\t\t\t\t\t\t'Chunk': index + 1,
\t\t\t\t\t\t\t'Provider': st.session_state.web_embedding_provider_used,
\t\t\t\t\t\t\t'Model': st.session_state.web_embedding_model_path_used or st.session_state.web_embedding_model_used,
\t\t\t\t\t\t\t'Dimensions': len( vector ),
\t\t\t\t\t\t\t'Source': ( document.metadata or { } ).get( 'source', '' ),
\t\t\t\t\t\t\t'Text': document.page_content,
\t\t\t\t\t\t\t'Vector': vector,
\t\t\t\t\t\t} )
\t\t\t\t\tst.dataframe( pd.DataFrame( embedding_rows ), use_container_width=True, hide_index=True )

'''

    source = source[:start] + block + source[end:]
    APP.write_text(source, encoding='utf-8')


update_fetchers()
update_app()
