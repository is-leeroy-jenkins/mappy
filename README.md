###### mappy

![](https://github.com/is-leeroy-jenkins/Mappy/blob/master/resources/images/project_mappy.png)

<p align="left">
  <a href="#-demo">Demo</a>
  &nbsp;&bull;&nbsp;
  <a href="#-features">Features</a>
  &nbsp;&bull;&nbsp;
  <a href="#-application-modes">Modes</a>
  &nbsp;&bull;&nbsp;
  <a href="#-installation">Installation</a>
  &nbsp;&bull;&nbsp;
  <a href="#-configuration">Configuration</a>
  &nbsp;&bull;&nbsp;
  <a href="#-running-the-streamlit-app">Run</a>
  &nbsp;&bull;&nbsp;
  <a href="#-quick-start-python-framework">Start</a>
  &nbsp;&bull;&nbsp;
  <a href="#-data-management">Data</a>
  &nbsp;&bull;&nbsp;
  <a href="#-api-key-references">API</a>
  &nbsp;&bull;&nbsp;
  <a href="#-license">License</a>
</p>

___


[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-0078FC?style=for-the-badge&logo=github)](https://is-leeroy-jenkins.github.io/mappy/)

`mappy` is a lightweight Python geospatial framework and Streamlit application for mapping,
location enrichment, environmental data retrieval, astronomical data access, web scraping, and
geospatial data management. It wraps core mapping services behind a simple Python interface while
also exposing the functionality through a wide Streamlit dashboard.

The project supports traditional mapping workflows such as geocoding, distance calculation,
static map generation, time-zone lookup, spreadsheet enrichment, and interactive map rendering.
It also extends into weather, environmental, astronomical, geological, and web data sources so the
same application can support location intelligence, situational awareness, and data pipeline
enrichment.


## 🎥 Demo

![](https://github.com/is-leeroy-jenkins/Mappy/blob/master/resources/images/mappy-demo.gif)

---

## ☁️ Cloud

<table>
<tr>
<td align="center">
<img width="190" height="1" alt=""><br>
<a href="https://mappy.wonderfulsand-c318f361.eastus.azurecontainerapps.io">
<img src="https://img.shields.io/badge/Docker-App-2496ED?logo=docker&logoColor=white" alt="Docker App">
</a>
</td>

<td align="center">
<img width="190" height="1" alt=""><br>
<a href="https://mappy-py.streamlit.app/">
<img src="https://img.shields.io/badge/Streamlit-App-FF4B4B?logo=streamlit&logoColor=white" alt="Streamlit App">
</a>
</td>

<td align="center">
<img width="190" height="1" alt=""><br>
<a href="https://dbc-a0c21f80-7bb3.cloud.databricks.com/browse/folders/3169291152437594?o=7474645703081351">
<img src="https://img.shields.io/badge/Databricks%20Repo-Mappy--Py-FF3621?logo=databricks&logoColor=white" alt="Databricks Notebook">
</a>
</td>

<td align="center">
<a href="https://leeroy.usw-16.palantirfoundry.com/shares/links/whekw4rty33cw">
<img width="190" height="1" alt=""><br>
<img src="https://img.shields.io/badge/Palantir%20Foundry-Repo-101113?logo=palantir&logoColor=white" alt="Palantir Repo">
</a>
</td>
</tr>
</table>

## ✨ Features

* 🔎 **Geocoding** – Convert free-form addresses or city, state, and country triples into
  coordinates.
* 🧭 **Places Fallback** – Use Places text search when geocoding does not resolve a location.
* 📏 **Distance Matrix** – Compute distance and travel time between origins and destinations.
* 🗺️ **Interactive Maps** – Render uploaded or geocoded coordinate data with map overlays.
* 🖼️ **Static Maps** – Generate static map previews and map image URLs for reporting.
* ⏱️ **Time Zones** – Resolve IANA time zones from latitude and longitude.
* 📊 **Excel and CSV Enrichment** – Upload spreadsheets and enrich records with geocoded coordinates.
* 🗄️ **SQLite Data Management** – Browse, insert, update, delete, geocode, profile, and query local
  tables.
* 🌦️ **Weather Data** – Query Google Weather, OpenWeather/Open-Meteo, historical weather, climate
  data,
  tides, and current data.
* 🌫️ **Environmental Data** – Query air quality, UV index, EPA EnviroFacts, PurpleAir, NASA FIRMS,
  and
  NASA EONET data.
* 🌌 **Astronomical Data** – Access naval observatory, space weather, star chart, satellite, catalog,
  AstroQuery/SIMBAD, and star map functionality.
* 🌎 **Geological Data** – Query USGS earthquakes, water data, national map data, and global imagery.
* 🕸️ **Web Scraper** – Fetch, crawl, parse, summarize, and extract structured data from web pages.
* ⚡ **Rate Limiting and Caching** – Control API usage with QPS limits and optional cache backends.
* 🛠️ **Explicit Error Handling** – Use clear exception paths for not-found, gateway, and framework
  errors.

## 🧭 Application Modes

The Streamlit application is organized around the following modes.

| Mode                | Purpose                                                                                | Primary Outputs                                                  |
| ------------------- | -------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| **Geocoding**       | Resolve addresses or city/state/country records into latitude and longitude.           | Coordinates, formatted address, geocoded map records.            |
| **Interactive Map** | Display coordinate-based records on an interactive map.                                | Map overlay, geocoded record preview.                            |
| **Distances**       | Calculate travel distance and estimated travel time between origin and destination.    | Distance text, duration text, raw response.                      |
| **Static Maps**     | Generate a static map URL centered on selected coordinates.                            | Static map preview/link.                                         |
| **Time Zones**      | Look up a time zone from coordinates and timestamp context.                            | Time-zone identifier and raw lookup response.                    |
| **Web Scraper**     | Fetch or crawl web content and extract text, links, metadata, and structured content.  | Summary, text, HTML, structured data, crawl JSON.                |
| **Weather**         | Query weather, historical weather, climate, and tides/current data.                    | Weather tables, summaries, and raw API responses.                |
| **Environmental**   | Query air quality, UV, sensor, facility, fire, and natural event data.                 | Environmental dataframes, summaries, raw results.                |
| **Astronomical**    | Query astronomy, satellite, space weather, star chart, and star map services.          | Astronomical dataframes, generated links, raw results.           |
| **Celestial Map**   | Render a sky/celestial map from the active location.                                   | Celestial map visualization.                                     |
| **Geological**      | Query earthquake, water, imagery, and national map services.                           | Geological result tables, imagery, raw results.                  |
| **Data Upload**     | Load Excel or CSV files into the application session.                                  | Working dataframe and preview.                                   |
| **Data Management** | Manage SQLite tables, geocode missing report coordinates, inspect schema, and run SQL. | Updated tables, coordinate updates, schema views, query results. |

## 🧩 Sidebar

The application sidebar provides the main operating controls.

| Section               | Purpose                                                                                                            |
| --------------------- | ------------------------------------------------------------------------------------------------------------------ |
| **🛰️ GIS Mapping**   | Select the active application mode.                                                                                |
| **🎚️ Configuration** | Configure location, browser geolocation, API keys, and application settings.                                       |
| **🏛️ Data**          | Load, inspect, and manage data sources used by the current mode.                                                   |
| **🔒 Credentials**    | Provide API keys for Google, Google Maps, Geocoding, NASA, AirNow, OpenAQ, FIRMS, PurpleAir, and related services. |

## 📦 Installation

Clone the repository and install dependencies.

```bash
git clone https://github.com/is-leeroy-jenkins/Mappy.git
cd Mappy
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

For Linux or macOS:

```bash
git clone https://github.com/is-leeroy-jenkins/Mappy.git
cd Mappy
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 🔑 Configuration

`mappy` can read configuration values from `config.py`, Streamlit session state, or environment
variables depending on how the application is deployed.

Common keys include:

| Key                       | Purpose                                 |
| ------------------------- | --------------------------------------- |
| `GOOGLE_API_KEY`          | General Google API access.              |
| `GOOGLE_CSE_ID`           | Google Custom Search Engine identifier. |
| `GOOGLEMAPS_API_KEY`      | Google Maps API access.                 |
| `GEOCODING_API_KEY`       | Geocoding API access.                   |
| `GOOGLE_CLOUD_PROJECT_ID` | Google Cloud project identifier.        |
| `GOOGLE_CLOUD_LOCATION`   | Google Cloud location/region.           |
| `GOOGLE_WEATHER_API_KEY`  | Google Weather API access.              |
| `GOVINFO_API_KEY`         | GovInfo API access.                     |
| `NASA_API_KEY`            | NASA API access.                        |
| `NASA_EARTHDATA_TOKEN`    | NASA Earthdata token.                   |
| `AIRNOW_API_KEY`          | AirNow API access.                      |
| `OPENAQ_API_KEY`          | OpenAQ API access.                      |
| `FIRMS_MAP_KEY`           | NASA FIRMS map key.                     |
| `OPENSKY_API_CLIENT_ID`   | OpenSky client identifier.              |
| `OPENSKY_API_CREDENTIALS` | OpenSky credential payload.             |
| `PURPLEAIR_API_KEY`       | PurpleAir API access.                   |

## 🚀 Running the Streamlit App

Start the application from the repository root.

```bash
streamlit run app.py
```

The app uses a wide layout and opens with the sidebar expanded. Select a mode from **🛰️ GIS Mapping
**
and then configure the relevant location, credentials, and data inputs from the sidebar and
mode-specific expanders.

## 🚀 Quick Start: Python Framework

### 1. Initialize Maps

```python
from mappy import Maps

maps = Maps(api_key="YOUR_API_KEY")
```

### 2. Geocode an address

```python
from mappy import Geocoder

geo = Geocoder(maps)
result = geo.freeform("Paris, France")
print(result["lat"], result["lng"], result["formatted_address"])
```

### 3. Calculate distance

```python
from mappy import DistanceMatrix

dist = DistanceMatrix(maps)
distance = dist.summary("New York, USA", "Los Angeles, USA", mode="driving")
print(distance["distance_text"], distance["duration_text"])
```

### 4. Get a static map URL

```python
from mappy import StaticMapURL

static_map = StaticMapURL(api_key="YOUR_API_KEY")
url = static_map.pin(lat=48.8584, lng=2.2945, zoom=14)
print(url)
```

### 5. Process Excel locations

```python
from mappy import Excel

excel = Excel(api_key="YOUR_API_KEY")
excel.enrich(
    input_path="locations.xlsx",
    output_path="locations_with_coords.xlsx",
    city_col="City",
    state_col="State",
    country_col="Country"
)
```

## 🗄️ Data Management

The application includes a SQLite management mode for local data workflows. It can:

* Preview the current table.
* Insert rows.
* Update rows.
* Delete rows.
* Profile table data.
* Drop selected tables.
* Create custom tables.
* Inspect table columns and indexes.
* Run SQL through the SQL console.
* Locate report rows missing coordinates.
* Geocode missing report coordinates and write latitude/longitude values back to the database.

This mode is especially useful for datasets with columns similar to:

| Column                     | Purpose                                              |
| -------------------------- | ---------------------------------------------------- |
| `ID`                       | Primary record identifier.                           |
| `Year`, `Month`, `Day`     | Date components.                                     |
| `CalendarDate`             | Full date value.                                     |
| `City`, `State`, `Country` | Location fields used for geocoding.                  |
| `Latitude`, `Longitude`    | Coordinate outputs.                                  |
| `Shape`                    | Optional observation or object shape classification. |
| `Summary`                  | Free-text record description.                        |

## 📂 Project Structure

```text
mappy/
 ├── app.py              # Streamlit application
 ├── config.py           # Application constants, paths, keys, and modes
 ├── maps.py             # Maps API gateway
 ├── geocode.py          # Address and location geocoding
 ├── places.py           # Places text-search fallback
 ├── distances.py        # Distance Matrix support
 ├── timezones.py        # Time-zone resolution
 ├── staticmaps.py       # Static map URL generation
 ├── excel.py            # Excel and CSV integration helpers
 ├── caches.py           # In-memory and SQLite cache backends
 ├── fetchers.py         # Weather, environmental, astronomical, geological, and web fetchers
 ├── exceptions.py       # Custom framework exceptions
 ├── requirements.txt    # Python dependencies
 └── resources/          # Images, setup documentation, and supporting assets
```

## ⚠️ Error Handling

* **NotFound** – Raised when a location cannot be resolved.
* **GatewayError** – Raised when HTTP or API communication fails.
* **MappyError** – Base class for framework-level exceptions.

By catching these explicitly, bulk geocoding, file enrichment, and API-backed workflows can fail
cleanly without losing the rest of the processing run.

## 💡 Design Philosophy

* **Simplicity first** – Each framework class has a single clear responsibility.
* **Composable services** – Geocoding, distance, maps, time zones, cache, and fetcher services can
  be used alone or together.
* **Streamlit-first operations** – The app exposes common workflows through mode-specific controls
  rather than forcing command-line use.
* **Cache-friendly design** – Optional in-memory and SQLite cache support reduces repeated API
  calls.
* **Rate-aware calls** – QPS controls help protect API quotas.
* **Spreadsheet-ready workflows** – Excel and CSV support is built into the application.
* **Data-management capable** – SQLite tooling supports local enrichment, auditing, and iterative
  cleanup.

## 🧪 Example Use Cases

* Enriching customer, facility, incident, or report datasets with GPS coordinates.
* Calculating travel distances for relocation, service coverage, logistics, or routing analysis.
* Creating static map thumbnails for reports, dashboards, or case summaries.
* Validating and normalizing international addresses.
* Auditing time-zone coverage for scheduling or distributed operations.
* Mapping weather, environmental, geological, or astronomical data around a selected location.
* Updating local SQLite tables with missing latitude and longitude values.
* Scraping web pages into structured text, links, and metadata for downstream analysis.

## 🔑 API Key References

### AI API Keys

* [OpenAI API Key](https://github.com/is-leeroy-jenkins/Buddy/blob/main/resources/setup/openai.md)
* [Grok API Key](https://github.com/is-leeroy-jenkins/Buddy/blob/main/resources/setup/xai.md)
* [Gemini API Key](https://github.com/is-leeroy-jenkins/Buddy/blob/main/resources/setup/gemini.md)

### Data Services

| Service      | Link                                                                              | Service        | Link                                                                                           |
| ------------ | --------------------------------------------------------------------------------- | -------------- | ---------------------------------------------------------------------------------------------- |
| Claude       | [API Keys](https://platform.claude.com/docs/en/api/admin/api_keys/retrieve)       | Mistral        | [Console](https://chat.mistral.ai/1)                                                           |
| NASA         | [NASA API](https://api.nasa.gov/)                                                 | Geolocation    | [Google Geolocation](https://developers.google.com/maps/documentation/geolocation/get-api-key) |
| Google Maps  | [Google Maps](https://developers.google.com/maps/documentation/embed/get-api-key) | GovInfo        | [GovInfo API](https://api.govinfo.gov/docs/)                                                   |
| The News API | [Register](https://www.thenewsapi.com/register)                                   | Google Weather | [Weather API](https://developers.google.com/maps/documentation/weather/get-api-key)            |
| Grokipedia   | [PyPI](https://pypi.org/project/grokipedia-api/)                                  | CDC            | [CDC Data](https://data.cdc.gov/login)                                                         |
| PurpleAir    | [Developer Portal](https://develop.purpleair.com/)                                | FIRMS          | [NASA FIRMS](https://firms.modaps.eosdis.nasa.gov/usfs/api/map_key/)                           |
| Census       | [API Key](https://api.census.gov/data/key_signup.html)                            | Wikipedia      | [Wikimedia APIs](https://www.mediawiki.org/wiki/Wikimedia_APIs/Get_started)                    |

## 📚 Dependencies

Core dependencies include:

| Dependency          | Purpose                                                    |
| ------------------- | ---------------------------------------------------------- |
| `streamlit`         | Application framework.                                     |
| `streamlit-js-eval` | Browser geolocation support.                               |
| `pandas`            | Tabular data processing.                                   |
| `openpyxl`          | Excel workbook I/O.                                        |
| `requests`          | HTTP client support.                                       |
| `beautifulsoup4`    | HTML parsing.                                              |
| `plotly`            | Interactive charts.                                        |
| `pydeck`            | Map rendering.                                             |
| `matplotlib`        | Supporting visualization backend.                          |
| `sqlite3`           | Local database access through the Python standard library. |

Additional dependencies may be required by optional fetchers or provider-specific workflows.

## 📜 License

Mappy is available under the MIT
License [here](https://github.com/is-leeroy-jenkins/mappy/blob/master/LICENSE.txt).

![License-MIT](https://img.shields.io/badge/License-MIT-blue.svg)
