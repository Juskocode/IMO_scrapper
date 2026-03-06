# Static Assets

This directory contains the CSS and JavaScript files used in the ImoDashboard frontend.

## Structure

### `css/app.css`

Custom styles for the dashboard UI, supplementing Bootstrap with:
- Modern typography using the Inter font.
- Card-based layouts for listings and controls.
- Custom status indicators for "loved" or "discarded" listings.
- Improved responsiveness for tables and charts.

### `js/` (Modular JavaScript)

The frontend logic is written using ES Modules (ESM) to ensure clean separation of concerns.

#### Core Modules
- `main.js`: The application entry point. Initializes the UI components and sets up global event listeners.
- `apiClient.js`: A Facade for API calls, providing a clean interface for fetching listings, statistics, and updating marks.
- `eventBus.js`: An Observer pattern implementation to facilitate communication between different UI components without direct dependencies.
- `marksRepository.js`: Manages the state and persistence of "loved" and "discarded" listings.

#### Utilities
- `utils/format.js`: Common functions for formatting currency, numbers, and dates. Includes mathematical helpers like `median`, `linearRegression`, and `cleanOutliers`.

#### Renderers
- `render/table.js`: Logic for rendering the results table, including sorting and formatting of listing rows.
- `render/charts.js`: Handles all data visualization using Chart.js.
  - Distribution by source.
  - Median price per m².
  - Price vs. Area scatter plots with trend lines (regression formula).
  - Yield insights per district.
- `render/summary.js`: Renders the quick stats summary card.

## Technologies
- **Bootstrap 5**: CSS framework for structure and components.
- **Chart.js**: Library for all data visualizations.
- **Inter Font**: Modern, readable typography.
- **Phosphor Icons**: Lightweight, clean icon set.
