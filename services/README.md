# Services

This directory contains the core application services for data processing, aggregation, and database interaction.

## Components

### `aggregator.py`

Orchestrates the data collection and merging process. It coordinates between scrapers, the database, and the data processor.

- **`get_listings`**: Orchestrates fetching results for a given query.
  - Checks the database first.
  - If results are insufficient, triggers selected scrapers in parallel using `ThreadPoolExecutor`.
  - Deduplicates by URL.
  - Clean and saves results via `services/processor.py` and `services/db/`.
  - Applies filters/typology logic and returns results with statistics.
- **`bulk_scrape`**: Iteratively populates the database for all districts and typical typologies.
- **`run_maintenance`**: Scans the database for district mismatches and fixes them.
- **Caching**: Uses `TTLCache` to store query results for 10 minutes.

### `db/`

Handles all interactions with the SQLite database (`data.db`). Split into:
- `connection.py`: Manages the database connection and path.
- `repository.py`: Core CRUD operations for listings and history. Implements an `is_active` status for listings.
- `stats.py`: Aggregation logic for daily and historical statistics.

### `processor.py`

New service that encapsulates data transformation and evaluation logic.

- **`clean_data`**: Removes junk entries (e.g., zero prices or missing areas).
- **`apply_filters`**: Filters results based on user-defined price/area ranges and specific keywords.
- **`apply_sort`**: Sorts items based on price or price per m².
- **`calculate_stats`**: Generates source-based distributions and median price per m².
- **`DISTRICTS`**: Centralized list of supported Portuguese districts.

### `property_matcher.py`

Specialized logic for property typology management.

- **`normalize_typology`**: Ensures a consistent format (e.g., "T1", "T2+1") for all processing.
- **`typology_regex`**: Generates complex regular expressions for accurate matching in raw text descriptions.
- **`match_property_typology`**: Filters a list of items using typology regex matching.
