( function()
{
	window.StarMapApp = window.StarMapApp || {};
	const {
		StarData,
		CelestialMath,
		MapRenderer,
		LocationPicker,
		UIController,
		StarDetailsPanel,
		ImageExporter,
		CONSTELLATION_NAMES
	} = window.StarMapApp;
	
	class StarMapAppMain
	{
		constructor()
		{
			const defaultLocation = window.StarMapApp.DEFAULT_LOCATION || {};
			this.defaultLocation =
			{
				latitude: Number.isFinite( Number( defaultLocation.latitude ) )
				          ? Number( defaultLocation.latitude )
				          : 20,
				longitude: Number.isFinite( Number( defaultLocation.longitude ) )
				           ? Number( defaultLocation.longitude )
				           : 0,
				location: defaultLocation.location || '',
				zoom: Number.isFinite( Number( defaultLocation.zoom ) )
				      ? Number( defaultLocation.zoom )
				      : 8,
				tileUrl: defaultLocation.tileUrl ||
						'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
				tileAttribution: defaultLocation.tileAttribution ||
						'&copy; OpenStreetMap contributors &copy; CARTO',
				tileSubdomains: defaultLocation.tileSubdomains || 'abcd'
			};
			
			this.starData = new StarData();
			this.renderer = new MapRenderer( 'map' );
			this.selectedCoords =
			{
				lat: this.defaultLocation.latitude,
				lon: this.defaultLocation.longitude
			};
			
			this.zoomScale = 1.0;
			this.starAppearance =
			{
				brightness: 1,
				sizeScale: 1.5
			};
			
			this.labelLanguage = 'en';
			this.customColors =
			{
				constellations: 'rgba(255, 255, 255, 0.6)',
				dsos: '#4DA3FF',
				background: '#05070B',
				planets: '#FFD700',
				graticule: 'rgba(0, 120, 252, 0.28)'
			};
			
			this.animationInterval = null;
			this.debouncedHandleSubmit = this.debounce( ( ) =>
					this.handleSubmit(), 300 );
			
			this.locationPicker = new LocationPicker( 'locationPicker',
			{
				initialLat: this.defaultLocation.latitude,
				initialLon: this.defaultLocation.longitude,
				initialZoom: this.defaultLocation.zoom,
				tileUrl: this.defaultLocation.tileUrl,
				tileAttribution: this.defaultLocation.tileAttribution,
				tileSubdomains: this.defaultLocation.tileSubdomains,
				onLocationChange: ( lat, lon ) => this.handleLocationChange( lat, lon )
			} );
			
			this.ui = new UIController(
			{
				onSubmit: () => this.handleSubmit(),
				onInputChange: () => this.debouncedHandleSubmit(),
				onSliderChange: ( id, value ) =>
				{
					this.handleSliderChange( id, value );
				},
				onLanguageChange: ( lang ) => this.handleLanguageChange( lang ),
				onWhatUpTonight: () => this.setWhatUpTonight(),
				onPlayAnimation: () => this.startAnimation(),
				onPauseAnimation: () => this.stopAnimation()
			} );
			
			this.detailsPanel = new StarDetailsPanel(
			{
				getStarNames: ( id ) => this.starData.data.starnames[ id ],
				getTranslatedName: ( id, type ) =>
						this.starData.getTranslatedName( id, type, this.labelLanguage, this.starData.data )
			} );
			
			this.exporter = new ImageExporter(
			{
				getDateTime: () => this.ui.getDateTime(),
				getBackgroundColor: () => this.customColors.background
			} );
			
			this.init();
		}
		
		debounce( func, wait )
		{
			let timeout;
			return ( ...args ) =>
			{
				clearTimeout( timeout );
				timeout = setTimeout( () => func.apply( this, args ), wait );
			};
		}
		
		async init()
		{
			this.ui.setDateTime( new Date() );
			this.ui.updateLocationDisplay( this.selectedCoords.lat, this.selectedCoords.lon );
			try
			{
				this.ui.toggleLoading( true );
				await this.starData.load();
				this.initColorPickers();
				this.locationPicker.setView( this.selectedCoords.lat, this.selectedCoords.lon,
						this.defaultLocation.zoom, false );
				
				this.ui.updateLocationDisplay( this.selectedCoords.lat, this.selectedCoords.lon );
				this.handleSubmit();
			}
			catch( error )
			{
				console.error( error );
				this.ui.showError( 'Failed to load star data.' );
			}
			finally
			{
				this.ui.toggleLoading( false );
			}
		}
		
		initColorPickers( )
		{
			const container = document.querySelector( '.color-pickers' );
			if( !container )
			{
				return;
			}
			const createPicker = ( label, targetColor ) =>
			{
				const wrapper = document.createElement( 'div' );
				wrapper.className = 'picker-wrapper';
				wrapper.innerHTML = `<label>${ label }</label>`;
				const pickerEl = document.createElement( 'div' );
				wrapper.appendChild( pickerEl );
				container.appendChild( wrapper );
				const pickr = Pickr.create(
				{
					el: pickerEl,
					theme: 'nano',
					default: this.customColors[ targetColor ],
					components:
					{
						preview: true,
						opacity: true,
						hue: true,
						interaction:
						{
							input: true,
							save: true
						}
					}
				} );
				
				pickr.on( 'save', ( color ) =>
				{
					this.customColors[ targetColor ] = color.toRGBA().toString();
					this.debouncedHandleSubmit();
					pickr.hide();
				} );
			};
			
			createPicker( 'Constellations', 'constellations' );
			createPicker( 'DSOs', 'dsos' );
			createPicker( 'Planets', 'planets' );
			createPicker( 'Background', 'background' );
			createPicker( 'Grid', 'graticule' );
		}
		
		handleLocationChange( lat, lon )
		{
			this.selectedCoords =
			{
				lat,
				lon
			};
			
			this.ui.updateLocationDisplay( lat, lon );
			this.debouncedHandleSubmit();
		}
		
		handleSliderChange( id, value )
		{
			if( id === 'starBrightness' )
			{
				this.starAppearance.brightness = value;
			}
			if( id === 'starSize' )
			{
				this.starAppearance.sizeScale = value;
			}
			if( id === 'zoomScale' )
			{
				this.zoomScale = value;
			}
			this.debouncedHandleSubmit();
		}
		
		handleLanguageChange( lang )
		{
			this.labelLanguage = lang || 'en';
			this.debouncedHandleSubmit();
		}
		
		async handleSubmit( isAnimation = false )
		{
			try
			{
				if( !isAnimation )
				{
					this.ui.toggleLoading( true );
				}
				const date = this.ui.getDateTime();
				const { lat, lon } = this.selectedCoords;
				const options = this.ui.getFormData( );
				const projection = this.renderer.createProjection( lat, lon, date, this.zoomScale );
				this.renderer.clearMap( this.customColors.background );
				if( options.graticule )
				{
					this.renderer.renderGraticule( projection, this.customColors.graticule );
				}
				if( options.milkyWay )
				{
					this.renderer.renderMilkyWay( projection, this.starData.data.mw );
				}
				
				this.renderer.renderStars( projection, this.starData.data.stars,
						this.starAppearance,
						{
							onMouseOver: ( e, star ) => this.showStarTooltip( e, star ),
							onMouseOut: () => this.hideTooltip(),
							onClick: ( star ) => this.detailsPanel.show( star, this.labelLanguage )
						} );
				
				if( options.constellations )
				{
					this.renderer.renderConstellations( projection, this.starData.data.lines,
							this.customColors.constellations );
				}
				
				if( options.constellationBorders )
				{
					this.renderer.renderConstellationBorders( projection,
							this.starData.data.constellationBorders );
				}
				
				if( options.labels )
				{
					this.renderer.renderLabels( projection, this.starData.data,
					{
						labelLanguage: this.labelLanguage,
						constellationColor: this.customColors.constellations,
						planetsColor: this.customColors.planets,
						showPlanets: options.planets,
						date: date
					} );
				}
				
				if( options.dsos )
				{
					this.renderer.renderDSOs( projection, this.starData.data.dsos,
							this.customColors.dsos,
							{
								onMouseOver: ( e, dso ) => this.showDSOTooltip( e, dso ),
								onMouseOut: () => this.hideTooltip()
							} );
				}
				
				if( options.planets )
				{
					this.renderer.renderPlanets( projection, this.starData.data.planets, date,
							this.customColors.planets,
							{
								onMouseOver: ( e, planet ) => this.showPlanetTooltip( e, planet ),
								onMouseOut: () => this.hideTooltip()
							} );
				}
				
				const jd = CelestialMath.dateToJD( date );
				const lst = CelestialMath.jdToLST( jd, lon ) / 15;
				this.ui.updateLSTDisplay( lst );
				this.ui.updateLocationDisplay( lat, lon );
				const downloadBtn = document.getElementById( 'downloadBtn' );
				if( downloadBtn )
				{
					downloadBtn.classList.remove( 'hidden' );
				}
			}
			catch( error )
			{
				console.error( error );
				this.ui.showError( error.message );
			}
			finally
			{
				if( !isAnimation )
				{
					this.ui.toggleLoading( false );
				}
			}
		}
		
		setWhatUpTonight()
		{
			this.locationPicker.getCurrentPosition().then( coords =>
			{
				this.handleLocationChange( coords.latitude, coords.longitude );
				this.locationPicker.setView( coords.latitude, coords.longitude, 8, false );
				this.ui.setDateTime( new Date() );
				this.handleSubmit();
			} ).catch( err =>
			{
				this.ui.showError( err.message );
			} );
		}
		
		startAnimation( )
		{
			if( this.animationInterval )
			{
				return;
			}
			
			this.ui.setAnimationState( true );
			const timeStep = this.ui.getTimeStep( );
			this.animationInterval = setInterval( ( ) =>
			{
				const date = this.ui.getDateTime( );
				if( timeStep === 'minute' )
				{
					date.setMinutes( date.getMinutes() + 1 );
				}
				else if( timeStep === 'hour' )
				{
					date.setHours( date.getHours() + 1 );
				}
				else if( timeStep === 'day' )
				{
					date.setDate( date.getDate() + 1 );
				}
				
				this.ui.setDateTime( date );
				this.handleSubmit( true );
			}, 100 );
		}
		
		stopAnimation()
		{
			clearInterval( this.animationInterval );
			this.animationInterval = null;
			this.ui.setAnimationState( false );
		}
		
		hideTooltip()
		{
			document.querySelectorAll( '.tooltip' ).forEach( t => t.remove() );
		}
		
		showStarTooltip( event, star )
		{
			const hip = star.properties?.hip || star.id;
			const name = this.starData.getTranslatedName( hip, 'star', this.labelLanguage,
					this.starData.data ) || star.properties?.desig || `HIP ${ hip }`;
			const content = `<strong>${ name }</strong><br>Magnitude: ${ star.properties.mag.toFixed(
					2 ) }<br>Constellation: ${ CONSTELLATION_NAMES[ star.properties.con ] ||
			star.properties.con || '' }`;
			this.createTooltip( event, content );
		}
		
		showDSOTooltip( event, dso )
		{
			const props = dso.properties;
			const commonName = this.starData.data.dsonames[ props.id ]?.name || '';
			const nameDisplay = commonName
			                    ? `<strong>${ commonName }</strong><br>(${ props.id })`
			                    : `<strong>${ props.id }</strong>`;
			
			const content = `${ nameDisplay }<br>Type: ${ props.type }<br>Magnitude: ${ props.mag
			                                                                            ? props.mag.toFixed( 2 )
			                                                                            : 'N/A' }`;
			this.createTooltip( event, content );
		}
		
		showPlanetTooltip( event, planet )
		{
			const name = this.starData.getTranslatedName( planet.id || planet.name, 'planet',
					this.labelLanguage, this.starData.data );
			
			const content = `<strong>${ name }</strong><br>Type: Planet`;
			this.createTooltip( event, content );
		}
		
		createTooltip( event, content )
		{
			this.hideTooltip();
			const tooltip = document.createElement( 'div' );
			tooltip.className = 'tooltip';
			tooltip.style.left = `${ event.pageX + 15 }px`;
			tooltip.style.top = `${ event.pageY + 15 }px`;
			tooltip.innerHTML = content;
			document.body.appendChild( tooltip );
		}
	}
	
	window.addEventListener( 'load', ( ) =>
	{
		new StarMapAppMain();
	} );
} )();