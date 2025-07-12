-- SQLite schema for Personal Financial Analysis

-- Table for storing transactions
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY,
    date TEXT NOT NULL,
    description TEXT,
    amount REAL NOT NULL,
    category INTEGER,
    type TEXT CHECK(type IN ('income', 'expense')) NOT NULL,
    is_recurring INTEGER DEFAULT 0,
    source_account TEXT,
    notes TEXT,
    FOREIGN KEY(category) REFERENCES categories(id)
);

-- Table for tracking months
CREATE TABLE IF NOT EXISTS months (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL
);

-- Table for available categories
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT CHECK(type IN ('income', 'expense')) NOT NULL
);

-- Table for keyword mappings
CREATE TABLE IF NOT EXISTS mappings (
    id INTEGER PRIMARY KEY,
    keyword TEXT NOT NULL,
    category_id INTEGER,
    recurring_guess INTEGER DEFAULT 0,
    last_used TEXT,
    FOREIGN KEY(category_id) REFERENCES categories(id)
);

-- Table for archived import logs
CREATE TABLE IF NOT EXISTS import_logs (
    id INTEGER PRIMARY KEY,
    file_name TEXT NOT NULL,
    date TEXT NOT NULL,
    type TEXT NOT NULL
);

-- Table for saving widget order within a month
CREATE TABLE IF NOT EXISTS layout_order (
    month_id INTEGER NOT NULL,
    table_id TEXT NOT NULL,
    position INTEGER NOT NULL,
    PRIMARY KEY (month_id, table_id)
);

