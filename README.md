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
2. Open a terminal, move into `backend`, and configure a signing key and initial administrator credentials:

   ```powershell
   cd backend
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   $env:CIVIC_SECRET_KEY = py -c "import secrets; print(secrets.token_urlsafe(48))"
   $env:CIVIC_ADMIN_EMAIL = Read-Host "Initial administrator email"
   $env:CIVIC_ADMIN_PASSWORD = Read-Host "Initial administrator password (at least 12 characters)"
   python -m uvicorn main:app --reload
   ```

   If PowerShell blocks activation, run `python -m pip install -r requirements.txt` without activating, then set the same environment variables and run `python -m uvicorn main:app --reload` from the backend folder. These values are required; the server will refuse to start if they are missing or too short. The administrator password configured here is applied whenever the server starts, so change it through `CIVIC_ADMIN_PASSWORD` and restart to rotate it.
3. Open `frontend/index.html` in a browser, or use the VS Code Live Server extension. Keep the backend running at `http://127.0.0.1:8000`.
4. The API docs are at `http://127.0.0.1:8000/docs`.

For repeat runs, you can copy `backend/.env.example` to `backend/.env`, fill in all required values, then start with `python -m uvicorn main:app --env-file .env --reload`. Do not commit `.env`. Existing databases created by an earlier version have the known demo administrator disabled unless its email is explicitly configured as the initial administrator.

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
