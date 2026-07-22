# Development

## Setup

```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows
# source .venv/bin/activate   # macOS/Linux

# Install dev dependencies
pip install -e ".[dev]"
```

## Environment Variables

Copy `.env.example` to `.env` and fill in your ZipAssist credentials:

```ini
ZIPASSIST_BASE_URL=https://zipassist.zipindustries.com
ZIPASSIST_EMAIL=your-email@example.com
ZIPASSIST_PASSWORD=your-password
```

## Running Tests

```bash
pytest
pytest --cov=custom_components/zipassist   # with coverage
```

## Linting

```bash
ruff check .
```

## API Exploration

The `exploration/explore.py` script connects to the live ZipAssist CMMS API and
discovers available endpoints and data shapes. It requires valid credentials in
`.env`.

```bash
python exploration/explore.py
```

### CLI Options

```
--base-url URL     Override the API base URL
--email EMAIL      Override the email from .env
--password PASS    Override the password from .env
--endpoints-only   Print only the endpoint list (for doc validation)
```

### Validating API Endpoint Docs

```bash
python exploration/explore.py --endpoints-only
```

This outputs a machine-readable list of all discovered endpoints, which can be
compared against `docs/api-endpoints.md` to check for drift.

## Project Structure

See [Architecture](architecture.md) for the full file structure and design decisions.

## Frontend Card Development

The custom Lovelace card is at `custom_components/zipassist/frontend/zipassist-card.js`.
It uses vanilla JS with shadow DOM — no build step required. When making changes:

1. Edit `zipassist-card.js`
2. Bump the `version` in `manifest.json` (cache bust)
3. Restart Home Assistant or hard-refresh the dashboard (Ctrl+F5)