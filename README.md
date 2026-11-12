# BTag CF

A Flask-based control panel for Gorilla Tag / PlayFab-compatible backend projects.

## Current status

The first control-panel stage includes username registration/login, a dashboard, and project creation with a Gorilla Tag full-backend template selection or a clean Flask starter. Project creation is metadata only: **backend execution and public API hosting are not enabled yet**.

## URL structure

A user's eventual backend base URL is:

`https://btag-cf.com/<username>/`

API routes will be exposed below that prefix, for example:

- `/<username>/api/PlayFabAuthentication`
- `/<username>/api/CachePlayfabId`
- `/<username>/api/TitleData`

The current Flask app deliberately returns a placeholder for public backend paths until a reverse proxy and isolated worker manager are deployed.

## Development

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

Open http://127.0.0.1:5000.

Set a long, random `SECRET_KEY` before deployment. Do not commit real PlayFab keys, Oculus tokens, Discord webhooks, or user backend files.

## Hosting architecture

GitHub Pages is static hosting and cannot run Flask. The custom domain `btag-cf.com` needs DNS pointed at a Python-capable host. Production also requires persistent database storage, HTTPS, a reverse proxy that maps each username prefix to its worker, and a container/process manager.

Uploaded or template Python must never execute in the main Flask web process. Each backend needs an isolated worker with resource limits, restricted filesystem/network access, non-root execution, and controlled dependencies. Both hosting modes can be offered without user fees, but free server hosting still requires infrastructure and fair-use limits.

## Backend template

The previously supplied Gorilla Tag backend is the selected full template. It needs a cleanup/configuration pass before it can be run: unresolved quest/certificate/package configuration must remain explicitly unconfigured rather than fabricated, external calls need timeouts and validation, and credentials must be injected privately at runtime. The source should not be executed in the web process.

## Run the Python web server

For local development:

```bash
pip install -r requirements.txt
python app.py
```

For a production container:

```bash
docker build -t btag-cf .
docker run -d --name btag-cf \
  -p 8000:8000 \
  -v btag-cf-data:/data \
  -e SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')" \
  -e COOKIE_SECURE=1 \
  btag-cf
```

Put HTTPS in front of the container using a reverse proxy (an example Nginx site is in `deploy/nginx.conf`). Configure the domain's DNS at your hosting provider to point to that server, and enable TLS. Keep the `/data` volume persistent so accounts and projects survive container restarts.

The Docker image runs as a non-root user and starts Flask through Gunicorn. This container currently runs the **control panel only**, not customers' uploaded backend code. Do not publish it without setting a strong private `SECRET_KEY`, HTTPS, persistent storage, backups, and an operational plan for updates and abuse prevention.
