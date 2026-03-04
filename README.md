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

### Development (live reload, no rebuild needed)

```bash
docker compose -f docker-compose.dev.yml up --build -d
```

Your `app/` directory is bind-mounted into the container — code changes (templates, CSS, Python) are reflected instantly via `uvicorn --reload`. Only rebuild when you change `requirements.txt` or the `Dockerfile`.

```bash
# View logs
docker logs -f portfolio

# Stop
docker compose -f docker-compose.dev.yml down
```

### Production

```bash
docker build -t portfolio .
docker run -p 8000:8000 \
  -e SECRET_KEY=your-secret \
  -e ADMIN_EMAIL=admin@example.com \
  -e ADMIN_PASSWORD=YourPassword123! \
  -v portfolio_data:/data \
  portfolio
```

## Configuration

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Session signing secret | `change-me-to-a-random-string` |
| `ADMIN_EMAIL` | Admin login email | `admin@example.com` |
| `ADMIN_PASSWORD` | Admin login password | `ChangeMe123!` |
| `DATA_DIR` | SQLite & data directory | `./data` |
| `UPLOAD_DIR` | Uploaded media directory | `./data/uploads` |
| `WHATSAPP_NUMBER` | WhatsApp contact number (e.g. `201234567890`) | _(empty)_ |
| `SENTRY_DSN` | Optional Sentry error tracking | _(empty)_ |

Additional settings (site title, social links, theme colors, profile image) are configurable from the **Admin Panel → Settings**.

## Video Embeds

Projects support video embeds from:

- **YouTube**: Paste the embed URL (e.g. `https://youtube.com/embed/VIDEO_ID`)
- **Google Drive**: Paste the share link (e.g. `https://drive.google.com/file/d/FILE_ID/view`) — automatically converted to the embeddable format. Make sure sharing is set to "Anyone with the link".
- **Uploaded videos**: Upload `.mp4`/`.webm` files via the media library

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
