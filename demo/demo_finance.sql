PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE transactions (
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
INSERT INTO transactions VALUES(1,'2025-05-01','Waitrose Grocery',-35.7000000000000028,2,'expense',0,NULL,NULL);
INSERT INTO transactions VALUES(2,'2025-05-03','Salary - BA Pilot',4500.0,1,'income',0,NULL,NULL);
INSERT INTO transactions VALUES(3,'2025-05-05','Transfer to Investments',-1000.0,3,'expense',0,NULL,NULL);
CREATE TABLE months (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL
);
INSERT INTO months VALUES(1,'May 2025','2025-05-01','2025-05-31');
CREATE TABLE categories (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT CHECK(type IN ('income', 'expense')) NOT NULL
);
INSERT INTO categories VALUES(1,'Salary','income');
INSERT INTO categories VALUES(2,'Groceries','expense');
INSERT INTO categories VALUES(3,'Investments','expense');
CREATE TABLE mappings (
    id INTEGER PRIMARY KEY,
    keyword TEXT NOT NULL,
    min_amount REAL NOT NULL,
    max_amount REAL NOT NULL,
    category_id INTEGER,
    recurring_guess INTEGER DEFAULT 0,
    last_used TEXT,
    FOREIGN KEY(category_id) REFERENCES categories(id)
);
CREATE TABLE import_logs (
    id INTEGER PRIMARY KEY,
    file_name TEXT NOT NULL,
    date TEXT NOT NULL,
    type TEXT NOT NULL
);
COMMIT;
