# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CityLLM is a Vue.js 3 frontend application for an urban land use simulation system. It provides a chat-based interface that integrates with a Flask backend to visualize GIS data on an interactive map.

## Technology Stack

- **Vue 3.5** with Composition API (`<script setup>` syntax)
- **Vite 5.4** as the build tool
- **OpenLayers 10.7** for GIS map rendering and GeoTIFF support
- **Element Plus 2.13** for UI components
- **Axios** for HTTP requests

## Development Commands

```bash
# Start development server (port 3000)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

The dev server automatically opens the browser. The Flask backend must be running on `localhost:5000` for full functionality.

## Architecture

### Component Structure

The app follows a three-panel layout managed by `App.vue`:

1. **DataLayerPanel** (`src/components/DataLayerPanel.vue`): Left sidebar for managing GIS data layers with checkboxes
2. **MapView** (`src/components/MapView.vue`): Center panel rendering OpenLayers map with GeoTIFF overlay support
3. **ChatPanel** (`src/components/ChatPanel.vue`): Right panel providing chat interface with the LLM backend

### Communication Patterns

- **Component events**: Standard Vue `emit` pattern for parent-child communication (e.g., `@toggle-layer`, `@backend-response`)
- **Map controls**: Custom window events (`map-zoom-in`, `map-zoom-out`) for sibling component communication between App.vue and MapView
- **Backend API**: RESTful API via `src/api/chat.js` communicating with Flask backend at `localhost:5000`

Note: Map controls use window events rather than Vue emits because the controls are in App.vue while the map instance lives in MapView.vue (sibling relationship through slots/conditional rendering).

### Backend Integration

The backend returns `AlgorithmExeResult` objects with three task types:

- **task_type: 0** - Natural language conversation (no map update)
- **task_type: 1** - Data display tasks (show existing GIS data layers)
- **task_type: 2** - Simulation prediction tasks (generate and display new GIS data)

Response format includes `result_paths` (TIF file URLs), `result_names` (layer names), and optional `layerMapping` for name-path associations.

The Flask backend must be running on `localhost:5000` for full functionality. The frontend communicates with the backend via RESTful API endpoints defined in `src/api/chat.js`.

### State Management

- Uses Vue 3's native reactivity (`ref`, `computed`) - no Vuex/Pinia
- Layer state synchronized between DataLayerPanel and MapView via props/events
- `dataLayers` array holds layer objects with `name`, `path`, and `checked` properties
- First layer is auto-checked when added; unchecked layers trigger map hide if no others are checked
- Map visibility controlled by `shouldRenderMap` flag and `tifUrl` prop to MapView

### Map Implementation

- Base layer: OpenStreetMap tiles via XYZ source
- Overlay: GeoTIFF rendering via `plotty` library with canvas-based color mapping
- Default view centered on Beijing (116.4°E, 39.9°N) at zoom 10
- Custom controls dispatch window events for cross-component communication
- Mouse coordinate tracking emits `coordinate-change` events

**GeoTIFF Rendering Pipeline**: The MapView uses a three-step pipeline: (1) `geotiff.js` parses the TIF file, (2) `plotty` renders pixel data to a canvas with color scales (viridis), (3) OpenLayers `ImageStatic` displays the canvas as an overlay. NoData pixels are made transparent via canvas manipulation.

### Resizable Panels

Both horizontal (map/chat) and vertical (messages/input) resizers are implemented using mouse drag handlers that adjust flex values dynamically.

## Key Files

| File | Purpose |
|------|---------|
| `src/api/chat.js` | Backend API communication, response parsing by task_type |
| `src/components/MapView.vue` | OpenLayers initialization, GeoTIFF loading, map controls |
| `src/components/ChatPanel.vue` | Chat UI, message formatting, input handling |
| `src/components/DataLayerPanel.vue` | Layer list with checkboxes |
| `vite.config.js` | Dev server config (port 3000, auto-open) |

## UI Language

The interface is in Chinese (简体中文) while code uses English variable names.
