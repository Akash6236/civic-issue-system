# CivicPulse — AI-Powered Secure Civic Issue Reporting & Verification System

A college mini-project prototype aligned with the supplied project presentation. Citizens can report potholes, garbage, drainage and other infrastructure issues; a rule-based AI-style analysis estimates category and severity, compares text for possible duplicates, and flags suspicious-looking submissions for human review. Administrators can review all reports and update statuses.

## Features
- Citizen registration and login
- Administrator role and separate views
- Complaint form with optional image upload (JPG/PNG/WEBP, up to 5 MB)
- Rule-based category and severity prediction
- Basic text similarity duplicate detection
- Basic suspicious-pattern flagging (not a fraud verdict)
- Report status workflow: Submitted → Under Review → In Progress → Resolved / Rejected
- Dashboard counts and administrator audit log endpoint
- PBKDF2 password hashing, signed expiring bearer tokens, server-side validation
- SQLite by default for easy demo; can be configured for MySQL

## Requirements
- Python 3.10+
- A modern browser
- VS Code recommended

## Run on Windows (PowerShell)
1. Extract the ZIP, then open the `civic-issue-system` folder in VS Code.
2. Open a terminal and run the Streamlit app:

   ```powershell
   python -m streamlit run app.py --server.port 8501 --server.headless true
   ```

3. Open your browser to `http://localhost:8501`.

## Administrator Credentials
A single administrator account is pre-configured for this project:

| Field | Value |
|-------|-------|
| Name | Rudraksh |
| Email | `1nt25mc103691.akash@nmit.ac.in` |
| Password | `Rudraksh@nmit2026` |
| Setup code | `nmit2026` |

This account has full administrator access. Use it to review complaints, update statuses, manage reports, and access analytics.

To create additional administrators or reset passwords, use the "Create Admin Account" and "Forgot Password" tabs in the app.


## Optional MySQL configuration
SQLite is the default so the project can run locally without database setup. For MySQL, create a database named `civic_issues`, install a MySQL driver (`python -m pip install pymysql`), and set the environment variable before starting the API:

```powershell
$env:DATABASE_URL="mysql+pymysql://<user>:<password>@localhost/civic_issues"
# Keep CIVIC_SECRET_KEY, CIVIC_ADMIN_EMAIL, and CIVIC_ADMIN_PASSWORD configured as above.
python -m uvicorn main:app --reload
```

## Important project limitations
- The current classifier, severity predictor, duplicate detector and suspicious-pattern detector are transparent rule-based prototype methods, not a trained computer-vision model. They are useful for demonstrating the workflow but can make mistakes.
- Uploaded images are served as static files, so do not treat their URLs as private. Before real deployment, protect image access with authorization and use managed storage.
- Before real deployment, restrict CORS, configure HTTPS, rotate secrets, add rate limiting and stronger token/session management, verify image content beyond MIME type, add authorization tests, and review privacy/data-retention rules.
- Do not claim that a report is fraudulent solely because it was flagged. Human review is required.

## Suggested viva explanation
"CivicPulse is a secure civic complaint prototype. Citizens submit an issue with a description, location and optional photo. The backend validates the data, stores the report, and runs a rule-based analysis to suggest the issue category and priority. It also checks for textually similar reports and flags unusual submissions for review. Administrators can view all complaints, change status, and use audit logs to trace important actions. The current AI logic is a baseline and can later be replaced with a trained image classifier and more robust similarity model."
