from flask import Flask, render_template, request, make_response
import pickle
import numpy as np
import sqlite3
from fpdf import FPDF
import io
import os

app = Flask(__name__)

# --- 1. SQLITE DATABASE AUTO-SETUP ---
# This runs every time the app starts to ensure the table exists
def init_sqlite_db():
    conn = sqlite3.connect('loan_db.sqlite')
    cursor = conn.cursor()
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
    print("✅ SQLite Database & Table Verified.")

init_sqlite_db()

# --- 2. LOAD AI MODEL ---
# Ensure 'loan_model.pkl' is in the same folder as this script
try:
    model = pickle.load(open('loan_model.pkl', 'rb'))
except FileNotFoundError:
    print("⚠️ Warning: loan_model.pkl not found! Predictions will fail.")

def get_db_connection():
    conn = sqlite3.connect('loan_db.sqlite')
    conn.row_factory = sqlite3.Row  # This allows accessing columns by name
    return conn

# --- 3. ROUTES ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        f = request.form
        l_type = f['loan_type']
        annual_inc = float(f['annual_income'])
        co_annual_inc = float(f['co_applicant_annual_income'])
        loan_amt = float(f['loan_amount'])
        cibil = int(f['cibil'])
        
        # Scale for AI Model (Monthly calculation as per your logic)
        m_inc = annual_inc / 12
        m_co_inc = co_annual_inc / 12
        # Input features for your specific model
        ai_input = [1, 1, 0, 1, 0, m_inc, m_co_inc, (loan_amt/1000), 360, 1.0, 2]
        prediction = model.predict([np.array(ai_input)])[0]

        # Business Eligibility Logic
        if l_type == "Education Loan":
            eligible = (cibil >= 600) or (co_annual_inc >= 350000)
        else:
            eligible = (int(prediction) == 1 and cibil >= 680) or (cibil >= 750)

        status = "ELIGIBLE" if eligible else "NON-ELIGIBLE"
        rate, emi = (0.0, 0.0)
        
        if status == "ELIGIBLE":
            rates = {"Gold Loan": 7.2, "Car Loan": 8.5, "Education Loan": 8.0, "Home Loan": 7.8}
            rate = rates.get(l_type, 10.5)
            r = (rate / 12) / 100
            # EMI Formula
            emi = (loan_amt * r * (1 + r)**60) / ((1 + r)**60 - 1)

        # SQLite Database Insert (Using '?' as placeholders)
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """INSERT INTO applications (age, gender, education, house_type, loan_type, 
                   annual_income_inr, co_applicant_name, co_applicant_annual_income, 
                   loan_amount_inr, cibil_score, prediction, interest_rate, emi_amount) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        cursor.execute(query, (int(f['age']), f['gender'], f['education'], f['house_type'], 
                               l_type, annual_inc, f['co_applicant_name'], co_annual_inc, 
                               loan_amt, cibil, status, rate, emi))
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()

        return render_template('index.html', result=status, rate=rate, emi=emi, app_id=last_id)
    except Exception as e:
        return f"Operational Error: {str(e)}"

@app.route('/dashboard')
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch All Records
    cursor.execute("SELECT * FROM applications ORDER BY applied_at DESC")
    apps = [dict(row) for row in cursor.fetchall()]
    
    # Fetch KPI - Total and Average Rate
    cursor.execute("SELECT COUNT(*) as total, AVG(interest_rate) as avg_rate FROM applications")
    kpi_raw = cursor.fetchone()
    kpi = dict(kpi_raw) if kpi_raw else {"total": 0, "avg_rate": 0}
    
    # Fetch KPI - Approved Count
    cursor.execute("SELECT COUNT(*) as approved FROM applications WHERE prediction='ELIGIBLE'")
    approved_count = cursor.fetchone()['approved']
    
    # Data for Charts (Loan Type Distribution)
    cursor.execute("SELECT loan_type, COUNT(*) as count FROM applications GROUP BY loan_type")
    chart_data = cursor.fetchall()
    
    conn.close()
    
    # Process chart data for JavaScript/Chart.js
    labels = [row['loan_type'] for row in chart_data]
    counts = [row['count'] for row in chart_data]
    
    return render_template('dashboard.html', apps=apps, kpi=kpi, approved=approved_count, labels=labels, counts=counts)

@app.route('/download_cert/<int:app_id>')
def download_cert(app_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM applications WHERE id = ?", (app_id,))
    data = cursor.fetchone()
    conn.close()
    
    if not data:
        return "Application not found", 404
        
    row = dict(data)
    
    # Generate PDF using FPDF
    pdf = FPDF()
    pdf.add_page()
    
    # Header Banner
    pdf.set_fill_color(0, 40, 80)
    pdf.rect(0, 0, 210, 50, 'F')
    pdf.set_font("Arial", 'B', 24)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 30, "OFFICIAL LOAN APPROVAL", ln=True, align='C')
    
    # Body Content
    pdf.ln(20)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"Certificate Ref: SOV-CERT-{row['id']}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Borrower Name: {row['co_applicant_name']}", ln=True)
    pdf.cell(0, 10, f"Loan Category: {row['loan_type']}", ln=True)
    pdf.cell(0, 10, f"Approved Principal: INR {row['loan_amount_inr']:,.2f}", ln=True)
    pdf.cell(0, 10, f"Interest Rate: {row['interest_rate']}% Fixed per Annum", ln=True)
    pdf.cell(0, 10, f"Monthly EMI: INR {row['emi_amount']:,.2f}", ln=True)
    
    # Footer
    pdf.ln(20)
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 10, "This is a computer-generated document. No signature required.", align='C')
    pdf.cell(0, 10, "Digitally verified by Sovereign AI Analytics Engine.", ln=True, align='C')
    
    # Output PDF as a byte stream response
    pdf_out = pdf.output(dest='S').encode('latin-1')
    response = make_response(pdf_out)
    response.headers.set('Content-Disposition', 'attachment', filename=f'Loan_Approval_{app_id}.pdf')
    response.headers.set('Content-Type', 'application/pdf')
    return response

if __name__ == '__main__':
    app.run(debug=True)