# Personal Financial Analysis

This project is a desktop financial analysis tool built with PyQt and SQLite. It provides interfaces for importing statements, processing transactions and organizing financial data.

## Project Structure

- `gui/` - PyQt widgets and layouts
- `data/` - SQLite database and backups
- `parser/` - CSV and PDF parsers
- `logic/` - classification and transaction processing
- `archived/` - processed statement files
- `import_logs` table tracks archived imports
- `main.py` - application entry point

## Demo Mode

The project ships with a small set of safe example data in the `demo/` folder.
Set `DEMO_MODE=true` in the `.env` file to run the application using the demo
CSV and database. If `demo/demo_finance.db` is missing the application will
create it automatically from `demo/demo_finance.sql`.

## Login

The application starts with a simple login window. The password hash is stored
in a local `.env` file under the variable `PASSWORD_HASH`. By default the hash
in this repository corresponds to the password `test123`. You can update the
hash using your preferred hashing method (e.g. SHA-256) and modifying the value
in `.env`.

## Setup

Install the required dependencies and run the application:

```bash
pip install -r requirements.txt
python main.py
```

When a CSV or PDF statement is imported, the original file is moved to the
`archived/` directory and renamed with the import date, for example
`statement_Starling_2023-03-01.csv`. Each archived import is recorded in the
`import_logs` table.
