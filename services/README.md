# Services

This directory contains the core application services for data processing, aggregation, and database interaction.

## Components

### `aggregator.py`

This service is responsible for orchestrating the various scrapers and processing the results.

- **`get_listings`**: The main entry point for fetching data.
  - Checks the database for existing results first.
  - If results are missing or insufficient, triggers the appropriate scrapers in parallel using a `ThreadPoolExecutor`.
  - Deduplicates listings by URL.
  - Cleans data to remove suspicious listings (outliers, zero prices, etc.).
  - Applies user-specified filters and sorting.
  - Returns processed items and basic statistics.
- **`bulk_scrape`**: Iterates over all district/typology/business type combinations to populate the database in the background.
- **Caching**:
  - `CACHE` (TTLCache): Stores full query results for 10 minutes.
  - `LISTINGS_CACHE` (LRUCache): Stores individual listing details for quick access.

### `database.py`

Handles all interactions with the SQLite database (`data.db`).

- **Database Schema**:
  - `listings`: Stores details for each real estate listing, including price, area, and first/last seen dates.
  - `listing_history`: Tracks price changes over time for individual listings.
  - `stats_daily`: Stores aggregated daily statistics (median price, count) per district, typology, and business type.
- **Key Functions**:
  - `save_listings`: Bulk inserts or updates listings and their history.
  - `get_listings_from_db`: Retrieves stored listings with filtering.
  - `update_daily_stats`: Aggregates current data into daily snapshots for historical analysis.
  - `get_historical_stats`: Provides data for trend charts.
  - `get_posted_stats`: Analyzes when listings were first seen.
