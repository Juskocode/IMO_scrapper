# Templates

This directory contains the Jinja2 templates for the ImoDashboard frontend.

## Structure

The templates follow a modular pattern, with a base layout and reusable components (parts).

### Main Pages
- `_layout.html`: The base template containing shared HTML structure, including the navbar and necessary scripts/styles.
- `dashboard.html`: The primary dashboard view. Extends `_layout.html` and includes the various controls and results sections.
- `analytics.html`: A secondary view for deep dives into historical data and market trends.

### Reusable Components (`parts/`)
These files are included in `dashboard.html` to keep the code manageable.

- `_controls.html`: Main search controls (district, search type, typology, page count).
- `_sources.html`: Checkboxes for selecting which real estate portals to search.
- `_filters.html`: Advanced numeric filters (price, area, €/m²) and sorting options.
- `_charts.html`: Placeholders and containers for all Chart.js visualizations.
- `_table_controls.html`: Interactive elements for the results table (filtering within results).
- `_table.html`: The structure for the real estate listings table.

## Key Features
- **Responsive Design**: Uses Bootstrap 5's grid system and components to adapt to different screen sizes.
- **Dynamic Content**: Data is primarily fetched via AJAX from `app.py` and rendered using modular JavaScript, but the initial structure is defined by these Jinja2 templates.
- **Component Separation**: Each major UI section is isolated into its own file for easier maintenance.
