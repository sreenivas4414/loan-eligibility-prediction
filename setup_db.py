import sqlite3

def init_db():
    conn = sqlite3.connect('loan_db.sqlite')
    cursor = conn.cursor()
    # Create table with SQLite syntax (AUTOINCREMENT instead of AUTO_INCREMENT)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            age INTEGER,
            gender TEXT,
            education TEXT,
            house_type TEXT,
            loan_type TEXT,
            annual_income_inr REAL,
            co_applicant_name TEXT,
            co_applicant_annual_income REAL,
            loan_amount_inr REAL,
            cibil_score INTEGER,
            prediction TEXT,
            interest_rate REAL,
            emi_amount REAL,
            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ SQLite Database initialized successfully!")

if __name__ == "__main__":
    init_db()