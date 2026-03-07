# ImoDashboard

Simple Flask-based dashboard that aggregates real estate listings (rent and sale) in mainland Portugal, calculates €/m², and allows sorting/filtering of results.

## Features
- **Multi-source Aggregation**: Searches across multiple real estate portals simultaneously.
- **Rent or Buy**: Support for searching properties for rent or sale.
- **RAG & Context**: Integration with a RAG model (mcp) to understand the context of scraping rules defined in YAML.
- **Advanced Filters**: Filter by price, area, typology, and €/m².
- **Favorites and Rejections**: Mark listings as "loved" or "ignored" for a future recommendation system.
- **Charts and Statistics**: Quick visualization of price and area distributions, including regression analysis.

## Supported Sources
- Idealista (`idealista`)
- Imovirtual (`imovirtual`)
- SUPERCASA (`supercasa`)
- CASA SAPO (`casasapo`)
- RE/MAX (`remax`)
- OLX (`olx`)

## How to Run
1. Create a virtualenv and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the app:
   ```bash
   python app.py
   ```
   - Optional variables: `HOST` and `PORT` (defaults to `127.0.0.1:5000`).

3. Open in your browser: http://127.0.0.1:5000/

## Usage
- Choose the district, business type (Rent/Buy), typology, number of pages per source, and the sources (checkboxes).
- Define price/area filters and the desired sorting.
- Click "Update" to load the data.
- Summary and quick charts help you understand the distribution by source and the current median €/m².
- Use the heart or trash icons to train your future personal recommendation system.

## Scheduled Tasks (Cron)
To keep the database updated automatically and perform maintenance (fixing district mismatches and optimizing storage), a cron job can be set up to run daily.

### Example Crontab
```bash
# Run daily at 00:00
0 0 * * * cd /path/to/ImoDashboard && /path/to/python3 automation/cron_bulk_scrape.py >> cron_output.log 2>&1
```
*Note: Ensure you use the full path to the project and the python executable (e.g. from your virtualenv).*

## Technical Notes
- Scrapers implemented in `scrapers/` with a common base (`BaseScraper`).
- Aggregator service in `services/aggregator.py` provides lightweight caching (10 min), URL deduplication, and sorting/filtering.
- **District Validation**: Includes a heuristic to detect and fix listings that appear in the wrong district (fixing ~10% mismatch issues).
- **Database Maintenance**: Includes periodic storage optimization; all historical data is preserved indefinitely.
- Frontend uses Bootstrap and Chart.js; modularized JavaScript in `static/js/`.
- Respects "polite sleep" between pages to reduce load on the target sites.
- Includes basic data validation to filter out junk entries (e.g., zero prices or missing areas).

## Architecture and Data Flow

The project follows a modular architecture that connects several components to provide real-time data and historical analysis.

### Overall Scheme
1.  **Frontend**: Built with Bootstrap 5 and modular ES Modules (Chart.js, EventBus). Communicates with the backend via AJAX.
2.  **API (Flask)**: Handles client requests, manages user marks, and orchestrates the aggregation process.
3.  **Aggregator Service**: Logic for coordinating scrapers, database interactions, deduplication, and data cleaning.
4.  **Scrapers**: Specialized modules for each portal (Idealista, OLX, etc.) that extract raw data using BeautifulSoup.
5.  **Database (SQLite)**: Stores listing details, historical price changes, and daily market statistics.

### Data Life Cycle: Scraping to DB
- **Request**: When a user queries a district/typology combination not sufficiently present in the DB, a background scrape is triggered.
- **Extraction**: Multiple scrapers run in parallel via `ThreadPoolExecutor`, fetching and parsing search results.
- **Normalization**: Raw data is cleaned (removing outliers/suspicious listings) and typologies are normalized (e.g., "T2+1" -> "T2").
- **Persistence**: 
    - **`listings` table**: Stores current listing details (URL, price, area, source).
    - **`listing_history` table**: Captures every price change detected for a specific URL.
    - **`stats_daily` table**: Aggregates daily snapshots of median prices and listing counts.

## API Documentation

The dashboard interacts with the Flask backend through the following endpoints:

| Endpoint | Method | Description | Parameters |
| :--- | :--- | :--- | :--- |
| `/api/listings` | `GET` | Main data endpoint. Fetches, scrapes (if needed), filters, and returns listings. | `district`, `pages`, `typology`, `sources[]`, `search_type`, `min_price`, etc. |
| `/api/stats` | `GET` | Returns overall database statistics (total listings per source). | None |
| `/api/history` | `GET` | Returns historical median price trends for a specific search. | `district`, `search_type`, `typology`, `mode` (scrape/posted) |
| `/api/listing_history` | `GET` | Returns the price evolution of a single listing. | `url` |
| `/api/marks` | `GET` | Fetches the user's "loved" and "discarded" listing map. | None |
| `/api/marks` | `POST` | Saves a new mark for a listing. | Body: `{"url": "...", "state": "loved\|discarded"}` |
| `/api/bulk_scrape`| `POST` | Triggers a comprehensive background scrape for all districts. | `pages` |

### Example Query
`GET /api/listings?district=Lisboa&typology=T2&search_type=rent&limit=50`
This request will first check the local `data.db` for Lisbon T2 rentals. If not found, it will parallel-scrape the selected portals, store the new data, and return a JSON containing both the results and summary statistics.

## Project Structure
- `app.py`: Flask server and API endpoints.
- `scrapers/`: Data extraction logic for each site. See [scrapers/README.md](scrapers/README.md) for details.
- `services/`: Core logic for data aggregation and database management. See [services/README.md](services/README.md) for details.
- `static/`: Frontend assets (JS, CSS). See [static/README.md](static/README.md) for details.
- `templates/`: Jinja2 templates for the UI. See [templates/README.md](templates/README.md) for details.
- `marks.json`: Local persistence for your favorites/rejections.
- `data.db`: SQLite database for listings and history.

## Refactored UI Structure
- The main page is `templates/dashboard.html`, which extends `templates/_layout.html`.
- Jinja components in `templates/parts/`:
  - `_controls.html`, `_sources.html`, `_filters.html`, `_charts.html`, `_table_controls.html`, `_table.html`.
- Custom CSS in `static/css/app.css`.
- Modularized JavaScript (ES Modules) under `static/js/`:
  - `apiClient.js` (Facade), `eventBus.js` (Observer), `marksRepository.js` (Repository), `utils/format.js`, and renderers in `render/` (`table.js`, `charts.js`, `summary.js`).

