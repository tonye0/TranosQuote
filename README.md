# AC Combiner Panel Quotation System

A full-stack web application that automates BOM and technical specification
generation for AC combiner panel quotations, allowing sales teams to produce
accurate quotes in minutes without engineering involvement.

---

## Architecture

```
quotation-app/
├── backend/                  FastAPI REST API
│   ├── app/
│   │   ├── main.py            App entrypoint, CORS, router registration
│   │   ├── data/
│   │   │   └── components.py  Seed data: breakers, accessories, customers, cable sizes
│   │   ├── models/
│   │   │   ├── db.py           SQLAlchemy models + SQLite setup + seeding
│   │   │   └── schemas.py       Pydantic request/response models
│   │   ├── routers/
│   │   │   ├── reference.py    Customers, breaker lookups, accessory listings
│   │   │   └── quotation.py    BOM preview + Excel/Word export endpoints
│   │   └── services/
│   │       ├── quotation_engine.py  Core BOM-building business logic
│   │       ├── excel_generator.py   BOM Excel file generation (openpyxl)
│   │       └── docx_generator.py    Technical spec Word doc generation (python-docx)
│   ├── test_api.py            Smoke tests (TestClient, no live server needed)
│   └── requirements.txt
│
└── frontend/                 React + Vite + Tailwind SPA
    ├── src/
    │   ├── App.jsx             Main page: customer/project, config, preview, export
    │   ├── api/client.js       Fetch wrapper for the backend API
    │   └── components/
    │       ├── BreakerSection.jsx     Incomer/outgoing config rows w/ live lookup
    │       ├── OptionalComponents.jsx Accessory checkboxes for "Others" customers
    │       └── BOMPreview.jsx          Live BOM table
    ├── vite.config.js          Dev server + API proxy to backend on :8000
    └── package.json
```

---

## How It Works

1. **Customer selection** determines the panel template:
   - **Daystar**: e-stop, shunt trip coil(s), power meter, cooling fan, and
     intake filter are **automatically** added to the BOM. Shunt trip coils
     are sized per incomer breaker frame (100A/250A/400A/630A frames).
   - **Others**: all of the above are optional, user-selectable checkboxes
     with quantity fields.

2. **Incomer / Outgoing configuration**: the sales rep enters quantity + kA
   rating + amperage for each circuit row. The frontend calls
   `GET /api/breakers/lookup?rating_kA=..&amperage=..` in real time to show
   the matched part number and cable size, so there's instant feedback if a
   combination doesn't exist in the catalog.

3. **Live BOM preview**: as any input changes, the frontend (debounced 400ms)
   calls `POST /api/quotation/preview`, which runs the same logic used for
   export, returning the full BOM array with line totals and a grand total.

4. **Export**:
   - `POST /api/quotation/export/excel` → downloads a formatted `.xlsx` BOM
     (S/N, Description, Qty, Part Number, Unit Price, Total Price, with a
     SUM formula for the grand total).
   - `POST /api/quotation/export/spec` → downloads a `.docx` technical
     specification covering panel configuration, electrical specs, incomer/
     outgoing breaker tables (with cable sizes), and accessory details.

---

## Component Database (seed data)

`backend/app/data/components.py` contains the initial catalog:

- **Breakers**: 10kA / 25kA / 36kA / 50kA frames across 63A–630A, each mapped
  to a part number, unit price, and cable size (16mm² – 2×150mm²).
- **Accessories**: e-stop button, shunt trip coils (sized by frame), digital
  power meter, cooling fan, intake filter — each with part numbers and prices.
- **Customers**: `daystar` (auto components) and `others` (selectable
  components). Add more customers by appending to `CUSTOMERS` and re-seeding.

This data is loaded into a local **SQLite** database (`backend/quotation.db`)
on first startup via `init_db()`. To reset/reseed, simply delete
`quotation.db` and restart the server — or edit the seed data and add a
migration for production use.

To extend the catalog (new breaker sizes, accessory types, or customers),
edit `components.py` and either delete `quotation.db` (dev) or write a small
script using the SQLAlchemy models in `app/models/db.py` to insert new rows
without wiping existing data.

---

## Setup & Running Locally

### Prerequisites
- Python 3.10+
- Node.js 18+

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`, with interactive docs
at `http://localhost:8000/docs`. SQLite database and seed data are created
automatically on first run.

**Run smoke tests:**
```bash
pip install pytest httpx
python -m pytest test_api.py -v
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The Vite dev server proxies all `/api/*`
requests to `http://localhost:8000` (configured in `vite.config.js`), so no
CORS issues during development.

---

## Production Deployment

### Backend
- Run with a production ASGI server, e.g.:
  ```bash
  uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
  ```
  or behind Gunicorn with `uvicorn.workers.UvicornWorker`.
- Replace SQLite with Postgres/MySQL for multi-user/concurrent use: change
  `DATABASE_URL` in `app/models/db.py` (SQLAlchemy handles the rest — no
  other code changes needed).
- Restrict `allow_origins` in `app/main.py` CORS middleware to your actual
  frontend domain instead of `"*"`.

### Frontend
```bash
cd frontend
npm run build
```
This outputs static files to `frontend/dist/`. Serve these via any static
host (Nginx, S3+CloudFront, Vercel, Netlify). Update the API base URL (or
reverse-proxy `/api` to the backend) so the built frontend can reach the
FastAPI service — e.g. an Nginx config:

```nginx
location /api/ {
    proxy_pass http://backend:8000/api/;
}
location / {
    root /var/www/quotation-frontend/dist;
    try_files $uri /index.html;
}
```

### Docker (optional quick-start)
A minimal approach: build the backend image with `requirements.txt`, build
the frontend with `npm run build` and serve the static `dist/` via Nginx
alongside the API container, using the Nginx config above to route `/api`.

---

## Validation & Error Handling

- **Pydantic models** validate all inputs (positive quantities, required
  fields, max limits on quantities/rows).
- **Unknown breaker rating/amperage combinations** return `404` from
  `/api/breakers/lookup` and `400` from quotation endpoints, with a clear
  message — the frontend surfaces this inline next to the offending row.
- **"Others" with no optional components selected** triggers a non-blocking
  warning in the BOM preview, prompting the sales rep to double-check before
  exporting.
- **Cable line items** are included with quantity but `$0.00` unit price
  (cable is typically priced per meter by procurement) — a warning note is
  added to both the Excel and BOM preview, and is also included in the Word
  spec's Notes section.

---

## Extending the System

| To add...                          | Edit...                                                   |
|-------------------------------------|------------------------------------------------------------|
| New breaker rating/amperage          | `app/data/components.py` → `BREAKERS` list                |
| New accessory type                   | `app/data/components.py` → `ACCESSORIES`, then wire into `quotation_engine.py` auto/selectable logic |
| New customer template                | `app/data/components.py` → `CUSTOMERS`, specifying `auto_components` / `selectable_components` |
| BOM Excel formatting/columns         | `app/services/excel_generator.py`                         |
| Technical spec doc sections          | `app/services/docx_generator.py`                          |
| Frontend styling/branding            | `frontend/tailwind.config.js`, `frontend/src/index.css`   |
