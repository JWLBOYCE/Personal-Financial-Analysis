# Personal Financial Analysis

Personal Financial Analysis is a desktop application for tracking and analysing personal finances. The project is written in Python using the PyQt5 toolkit and SQLite for data storage.

## Features

- Import bank statements in CSV or PDF format
- Automatically archive imported statements and log the import history
- Categorise transactions and mark recurring expenses or income
- Month-by-month views with income, expense and credit card tabs
- Summary dashboard with totals and a bar chart
- Basic admin tools for editing keyword mappings used during categorisation
- Simple password-protected login screen (configured via `.env`)


## Demo Mode

The project ships with a small set of safe example data in the `demo/` folder.
Set `DEMO_MODE=true` in the `.env` file to run the application using the demo
CSV and database. If `demo/demo_finance.db` is missing the application will
create it automatically from `demo/demo_finance.sql`.

## Installation

1. Create and activate a virtual environment (optional)
2. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python main.py
   ```
   The first run will prompt for a password and store its hash in `.env`. The default repository value corresponds to the password `test123`.

## Directory Layout

```
archived/      # Archived copies of imported statements
 data/         # SQLite database file
 gui/          # PyQt5 UI classes
 logic/        # Categorisation and month management helpers
 parser/       # CSV and PDF statement parsers
 schema.sql    # Database schema used on startup
 main.py       # Application entry point
```

## Database Schema
The schema defines tables for transactions, months, categories, keyword mappings and import logs. It is automatically created in `data/finance.db` on first run. See [`schema.sql`](schema.sql) for details.

## Usage Notes

- Imported files are moved to the `archived/` directory with the import date appended to the filename.
- The application currently loads sample months on startup. Transaction data can be added by importing statements or by entering transactions manually.
- Recurring transactions can be duplicated to a new month using utilities in `logic/month_manager.py`.

## Mobile Companion Server

The optional Flask server in `api/server.py` exposes your finance data over HTTPS.
Set `ACCESS_TOKEN` in `.env` and provide the token in the `Authorization` header
for all requests. By default the server uses `cert.pem` and `key.pem` for SSL.
If `USE_NGROK=true` is set, the server will create a temporary public HTTPS
tunnel using **pyngrok**. All access attempts are logged to `access.log` with the
client IP and request path.

## License

This project is released under the MIT License. See the [LICENSE](LICENSE) file for more information.

