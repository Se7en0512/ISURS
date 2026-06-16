# ISURS - Item Shortage & Unavailability Reporting System

A self-hosted web app for tracking item shortages and unavailability across hospital stores, units, wards, and sections. Replaces the manual Excel-based reporting system.

## Features

### Dashboard (`/`)
- Summary cards: Total Items, Shortages, Not Available, Total Reports
- Bar chart: Reports by Store
- Line chart: Reports trend per Week
- Recent reports table
- **Export Excel** — download full reports as `.xlsx`
- **Print** button

### Items / Master List (`/items`)
- **Add / Edit / Delete** — manage item codes, names, and stores
- **Import from Excel** — upload Excel with "Master List2" sheet (Code, Item, Store columns)
- **Search** — find items via sidebar search bar

### New Report (`/report/new`)
- Form: Item, Week, Unit, Ward (auto-loads based on selected Unit), Section, Status
- Status options: Shortage / Not Available

### Reports (`/reports`)
- Table ng lahat ng reports with filters: By Store, Status, Week
- Pagination (50 per page)
- **Import from Excel** — upload Excel with "Report" sheet
- **Export Excel** — download filtered report data
- **Print** button

### Shortage Summary (`/shortage`)
- Items ranked by most reported shortages
- Filter by Store
- **Export Excel** / **Print**

### Not Available Summary (`/una`)
- Items ranked by most reported unavailability
- Filter by Store
- **Export Excel** / **Print**

### Settings (`/settings`)
- **Stores** — add/delete (Surgical Store, Medical Store, etc.)
- **Units** — add (Medical Cardiac Unit, ICU, etc.)
- **Wards** — add per Unit
- **Sections** — add (Nursing Administration, Clinical Support, etc.)
- **Weeks** — manage week numbers with date ranges
- **Seed from Excel** — import reference data from "Droplist" sheet
- **Download README** — download this documentation

## Excel Functions Replaced

| Excel Function | Web App Equivalent |
|---|---|
| Dropdown validation (Status) | Form dropdown |
| VLOOKUP (auto-fill Item/Store) | Auto via database relationships |
| COUNTIFS (Shortage count) | Shortage page — real-time query |
| COUNTIFS (UNA count) | Not Available page — real-time query |
| Dashboard manual counts | Charts & cards — auto-update |
| Droplist reference table | Settings page — managed in DB |

## How to Run Locally

```powershell
cd ISURS
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`

## Deploy on Render

1. Push this repo to GitHub
2. Go to https://dashboard.render.com → New → Web Service
3. Connect your GitHub repo
4. Set:
   - **Name:** `isurs`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Plan:** Free
5. Click **Deploy**
6. Your app will be live at `https://isurs.onrender.com`

## Importing Data from Excel

1. **Settings → Seed from Excel** — import reference data (Stores, Units, Wards, Sections, Weeks)
2. **Items → Import from Excel** — import Master List of items
3. **Reports → Import from Excel** — import Shortage/UNA reports

## Tech Stack

- **Backend:** Python, Flask, SQLAlchemy, SQLite
- **Frontend:** Bootstrap 5, Chart.js
- **Data:** openpyxl (Excel import/export)
