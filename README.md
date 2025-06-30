# Personal Financial Analysis

This project is a desktop financial analysis tool built with PyQt and SQLite. It provides interfaces for importing statements, processing transactions and organizing financial data.

## Project Structure

- `gui/` - PyQt widgets and layouts
- `data/` - SQLite database and backups
- `parser/` - CSV and PDF parsers
- `logic/` - classification and transaction processing
- `archived/` - processed statement files
- `main.py` - application entry point

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
