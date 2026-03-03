# Portfolio — FastAPI + SQLite

A single-container, admin-driven portfolio application built with FastAPI, SQLite (WAL mode), Jinja2, HTMX, and Alpine.js. Optimized for Fly.io deployment.

## Features

- **Public Site**: Dynamic home page with block-based layout, project showcase with filtering, project detail pages with video embeds
- **Admin Panel**: Full CRUD for projects, media library with drag-drop upload, page builder, theme editor, activity log
- **Media**: Image thumbnails via Pillow, video thumbnails via ffmpeg
- **Deployment**: Single Docker container, Fly.io volume for persistence

## Quick Start

```bash
# Clone and install
pip install -r requirements.txt

# Set environment
cp .env.example .env
# Edit .env with your values

# Run
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000` for the public site and `http://localhost:8000/admin` for the admin panel.

## Docker

```bash
docker build -t portfolio .
docker run -p 8000:8000 \
  -e SECRET_KEY=your-secret \
  -e ADMIN_EMAIL=admin@example.com \
  -e ADMIN_PASSWORD=YourPassword123! \
  -v portfolio_data:/data \
  portfolio
```

## Deploy to Fly.io

```bash
fly launch
fly volumes create portfolio_data --size 3
fly secrets set SECRET_KEY="..." ADMIN_EMAIL="..." ADMIN_PASSWORD="..."
fly deploy
```

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy (async), SQLite (WAL mode)
- **Frontend**: Jinja2, HTMX, Alpine.js
- **Media**: Pillow, ffmpeg
- **Deploy**: Docker, Fly.io
