# Scrapers

This directory contains the logic for extracting data from various real estate portals.

## Overview

All scrapers inherit from a common `BaseScraper` class, which provides shared functionality for HTTP requests, cookie management, and error handling.

## Components

- `base.py`: Contains the `BaseScraper` class.
  - Implements a robust `fetch` method with retries and rotating User-Agents.
  - Handles initial "origin" visits to bypass common bot-detection mechanisms for sites like Idealista, Supercasa, and Remax.
  - Implements `polite_sleep` to respect site rate limits.
- `utils.py`: Common utility functions for scrapers.
  - `slugify_pt`: Normalizes Portuguese district names for URLs.
  - `parse_typology`: Extracts property typology (e.g., T2) from text.
- Individual Scrapers:
  - `idealista.py`: Scraper for Idealista.pt.
  - `imovirtual.py`: Scraper for Imovirtual.com.
  - `supercasa.py`: Scraper for Supercasa.pt.
  - `casasapo.py`: Scraper for Casasapo.pt.
  - `remax.py`: Scraper for Remax.pt.
  - `olx.py`: Scraper for OLX.pt (Imobiliário).

## Adding a New Scraper

1. Create a new file `yourportal.py`.
2. Inherit from `BaseScraper`.
3. Implement the `scrape(self, district_name, district_slug, pages, typology, search_type)` method.
4. Return a list of dictionaries with the following keys:
   - `title`: Property title.
   - `price_eur`: Price as an integer.
   - `area_m2`: Area as an integer.
   - `url`: Full URL to the listing.
   - `source`: Name of the portal.
   - `snippet`: Brief description or location.
   - `typology`: Normalized typology (e.g., "T2").
5. Register the new scraper in `services/aggregator.py`.
