# Loan Eligibility Prediction

## Project Overview
A machine learning web application that predicts loan eligibility based on applicant information. The application uses Python, Flask, a saved machine learning model, and SQLite for storing application records.

## Features
- Loan eligibility prediction using a trained model
- Web interface built with HTML and CSS
- Applicant record storage using SQLite
- Dashboard for viewing application records
- PDF generation for loan-related results

## Technologies Used
- Python
- Pandas
- NumPy
- Scikit-learn
- Flask
- SQLite
- HTML and CSS
- Jupyter Notebook
- FPDF

## Project Structure
```text
loan-eligibility-prediction/
├── app.py
├── setup_db.py
├── loan_model.pkl
├── model.ipynb
├── requirements.txt
├── README.md
└── templates/
    ├── index.html
    └── dashboard.html
```

## Installation and Setup

### 1. Clone the repository
```bash
git clone https://github.com/sreenivas4414/loan-eligibility-prediction.git
cd loan-eligibility-prediction
```

### 2. Create a virtual environment
```bash
python -m venv venv
```

Activate it on Windows:
```bash
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the application
```bash
python app.py
```

Open the local address displayed in your terminal, usually http://127.0.0.1:5000.

## Important Notes
- Keep `loan_model.pkl` in the project root directory alongside `app.py`.
- The saved model must be compatible with the input features expected by the application.
- Database records are stored locally in SQLite.
- This project is for educational purposes and does not replace an actual bank's loan approval process.

## Author
Sreenivas

## License
No license has been specified yet.
