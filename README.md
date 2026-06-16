# ISURS - Item Shortage & Unavailability Reporting System

## Overview
Web-based replacement for the "Item Shortage & Unavailability Reporting System" Excel template. Automated tracking ng shortages at unavailable items per store, unit, ward, at section.

## New Features Added

### Search (`/search`)
- Search bar sa sidebar — nagse-search ng Items (code o name)
- Results page: items + related reports

### Export to Excel
- **Dashboard / Reports** → `Export Excel` — downloads filtered reports as `.xlsx`
- **Shortage** → `Export Excel` — downloads shortage summary
- **Not Available** → `Export Excel` — downloads UNA summary
- Compatible with current filters (export only what you see)

## Pages & Functionality

### Dashboard (`/`)
- Summary cards: Total Items, Shortages, Not Available, Total Reports
- Bar chart: Reports by Store
- Line chart: Reports trend per Week
- Recent reports table
- **Print** button

### Items / Master List (`/items`)
- **Add Item** — manually mag-enter ng Code, Item Name, Store
- **Edit / Delete** — modify or remove items
- **Import from Excel** — upload Excel na may "Master List2" sheet (columns: Code, Item, Store)

### New Report (`/report/new`)
- Form: Item, Week, Unit, Ward (auto-loads based on selected Unit), Section, Status
- Status options: Shortage / Not Available

### Reports (`/reports`)
- Table ng lahat ng reports with filters:
  - By Store
  - By Status (Shortage / Not Available)
  - By Week
- Pagination (50 per page)
- **Import from Excel** — upload Excel na may "Report" sheet
- **Print** button

### Shortage Summary (`/shortage`)
- Items ranked by most reported shortages
- Filter by Store
- **Print** button

### Not Available Summary (`/una`)
- Items ranked by most reported unavailability
- Filter by Store
- **Print** button

### Settings (`/settings`)
- **Stores** — add/delete (e.g. Surgical Store, Medical Store)
- **Units** — add (e.g. Medical Cardiac Unit, ICU)
- **Wards** — add per Unit (e.g. Cardiac Outpatient Department)
- **Sections** — add (e.g. Nursing Administration, Clinical Support)
- **Weeks** — add week number with date range
- **Seed from Excel** — import lahat ng reference data mula sa "Droplist" sheet ng Excel

## Excel Functions Replaced

| Excel Function | Web App Equivalent |
|---|---|
| Dropdown validation (Status) | Form dropdown |
| VLOOKUP (auto-fill Item/Store) | Auto via database relationships |
| COUNTIFS (Shortage count) | Shortage page - real-time query |
| COUNTIFS (UNA count) | Not Available page - real-time query |
| Dashboard manual counts | Charts & cards - auto-update |
| Droplist reference table | Settings page - managed in DB |

## How to Run

```powershell
cd ISURS
python app.py
```

Open `http://127.0.0.1:5000`

## Importing Data from Excel
1. **Settings → Seed from Excel** — reference data (Stores, Units, Wards, Sections, Weeks)
2. **Items → Import from Excel** — Master List ng items
3. **Reports → Import from Excel** — Shortage/UNA reports
