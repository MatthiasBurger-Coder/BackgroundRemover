# Browser Workbench Frontend

This frontend replaces the former Streamlit GUI with a browser-based React + TypeScript + Vite application.

## Development

```bash
npm install
npm run dev
```

The Vite dev server proxies `/api` requests to `http://127.0.0.1:8010` by default.
Override the backend port with `BACKGROUND_REMOVER_API_PORT`.

## Build

```bash
npm run build
```

## Functional split

- `Source Panel` manages source registration and metadata display.
- `Preview Player` owns live playback state and the moving frame position.
- `Workbench` owns the fixed editing snapshot and prompt overlays.
- `Editor Controls` mutate prompt and mask settings for the fixed workbench frame only.
