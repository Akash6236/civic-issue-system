# Fix My Civic Issue (CivicPulse)

Fix My Civic Issue is a civic issue reporting and management project. Citizens can submit local infrastructure reports and follow their status. Municipal administrators can triage reports, review potential duplicates, manage statuses, and view operational analytics.

The primary application is a **Streamlit** app in `app.py`. The repository also contains a separate FastAPI prototype in `backend/` and static files in `frontend/`; these are separate components and are not started by the Streamlit command.

## What has changed

### Citizen portal functionality

- Exercised the main citizen flows: registration, sign-in/sign-out, reporting an issue, selecting a location, report history and search, report details, editing and withdrawing reports, map and activity views, profile, and dashboard shortcuts.
- Fixed dashboard quick-action navigation and the empty-state report action.
- Synchronized map/address selections with the address input.
- Kept citizen-entered report fields authoritative over AI suggestions.
- Cleared report form state after successful submission.
- Set the advertised image-upload limit to 5 MB.

### Citizen and administrator UI

- Replaced the initial earthy styling with a consistent blue-and-white civic design system:
  - Primary blue: `#1E40AF`
  - Secondary blue: `#3B82F6`
  - Background: `#F8FAFC`
  - Cards: `#FFFFFF`
  - Success: `#16A34A`
  - Warning: `#F59E0B`
  - Error: `#DC2626`
  - Text: `#1E293B`
- Applied the shared styling to citizen and administrator views, including navigation, page headers, buttons, forms, cards, status badges, maps, and analytics charts.
- Added an administrator dashboard hero, consistent empty states, visible keyboard focus, reduced-motion support, and a responsive CivicPulse footer.
- Changed the sidebar to Streamlit's responsive `auto` behavior.

The redesign is presentation-only; it does not intentionally change application workflows, authentication, report processing, or database schemas.

## Application features

### Citizen

- Register and sign in.
- Submit an issue with a category, description, location, and optional photo.
- Review AI category suggestions without replacing the citizen's entered information.
- View, search, track, edit, or withdraw eligible reports.
- View report activity, maps, and profile information.

### Administrator

- View operational counts and recent activity.
- Triage and filter complaints, inspect report details, and update statuses.
- Review suspected duplicate reports.
- View complaint maps, analytics, and audit history.

### Prototype analysis and security features

- Rule-based issue categorization and severity suggestions.
- Text similarity checks for possible duplicate submissions.
- Suspicious-pattern flags intended for human review, not as fraud determinations.
- Bcrypt password hashing in the Streamlit application.
- SQLite persistence for the Streamlit application by default.

The analysis features are prototypes and can make mistakes. They should not be treated as final decisions.

## Project layout

```text
app.py                         Main Streamlit application
modules/
  authentication/              Streamlit login and account operations
  citizen/                     Citizen report and location flows
  admin/                       Administrator complaint operations
  analytics/                   Dashboard metrics, charts, and maps
  ui/theme.py                  Shared visual design system and components
database/
  schema.sql                   Streamlit SQLite schema
backend/
  main.py                      Separate FastAPI API prototype
  requirements.txt             FastAPI dependencies
frontend/
  index.html, app.js, style.css Static frontend files; not launched by app.py
utils/
  seed_db.py                   Local demo database seeding helper
uploads/                       Local uploaded report images
.streamlit/config.toml         Streamlit theme and server configuration
requirements.txt               Main Streamlit application dependencies
```

The main Streamlit app stores data in `database/civic_streamlit.db` and uploaded images under `uploads/`. The FastAPI prototype has separate models, dependencies, and database configuration. Running or deploying one does not automatically run, connect, or share data with the other.

## Requirements

- Python 3.10 or newer.
- A modern browser.
- Git for cloning or deploying from a repository.

Install the main app's dependencies from the repository root using `requirements.txt`.

## Run locally on Windows

Open PowerShell in the repository folder:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.port 8501 --server.headless true
```

Open <http://localhost:8501>.

The database tables are initialized when the Streamlit app starts. The local SQLite database and uploaded images are runtime data and are excluded from Git.

### Run locally on macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.port 8501 --server.headless true
```

## Accounts and credentials

- Citizens can register from the **Create Citizen Account** tab.
- Administrator account creation is restricted by a setup code.
- **Do not use the repository's demo administrator setup for a public deployment.** The current administrator setup value and local seeding helper are present in source code. Before exposing the app publicly, replace this demo setup with a secure provisioning method and rotate any credentials that may have been used.
- The previous README contained fixed demo administrator credentials. They have been removed from this document, but editing this README does not erase those values from Git history or other source files. Treat them as compromised if they were ever pushed to a remote repository.
- Never commit real passwords, setup codes, API keys, `.env` files, SQLite databases, or citizen uploads.

## Deploy the Streamlit app for a demo

Streamlit Community Cloud is a straightforward option for a **non-sensitive demonstration**:

1. Push the project to a GitHub repository. Do not include `.venv/`, `.env` files, database files, or uploaded images.
2. Sign in to Streamlit Community Cloud and choose **Create app**.
3. Select the repository and branch, and set the main file path to `app.py`.
4. Deploy. Streamlit installs the main dependencies from the root `requirements.txt`.
5. Open the generated app URL and verify registration and the intended demo flows.

### Important hosting limitations

The current Streamlit app writes to local SQLite and local upload directories. On many hosted app platforms, the local filesystem is temporary and can be replaced during a restart, rebuild, or redeploy. Therefore:

- Do not use a basic ephemeral deployment to store important reports or user-uploaded images.
- Do not enter real personal or sensitive information into a public demo.
- Do not expose administrator registration while its setup code is embedded in the application source.
- A public, production deployment needs persistent database and file storage, a secure administrator provisioning process, and a privacy/security review. The current Streamlit SQLite path is fixed in `modules/database.py`; setting the FastAPI `DATABASE_URL` does **not** configure the Streamlit app.

For production, choose a host and storage architecture that provide durable backups and persistent data. Add a supported database and managed image storage to the Streamlit application before relying on hosted data. Those changes require application work and are not achieved by changing the Streamlit theme or deployment settings alone.

## Optional: run the separate FastAPI prototype

The API in `backend/main.py` is a separate application. Its database and reports are not shared with the Streamlit app or the static files in `frontend/`.

From the repository root, create a Python environment, then install the API's separate dependencies:

```powershell
python -m pip install -r backend/requirements.txt
```

Configure these environment variables before starting the API:

- `CIVIC_SECRET_KEY`: a randomly generated secret with at least 32 characters.
- `CIVIC_ADMIN_EMAIL`: the administrator email address.
- `CIVIC_ADMIN_PASSWORD`: an administrator password with at least 12 characters.
- `DATABASE_URL`: optional SQLAlchemy database URL; the API otherwise uses its own SQLite database.

For a local PowerShell session, generate a secret and set your values without saving them in the repository:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
$env:CIVIC_SECRET_KEY = "<paste-generated-secret>"
$env:CIVIC_ADMIN_EMAIL = "<administrator-email>"
$env:CIVIC_ADMIN_PASSWORD = "<strong-unique-password>"
python -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000/docs> for the local API documentation. The sample `backend/.env.example` is a template only; the API does not automatically load it. Set environment variables in the shell or through the chosen hosting provider's secret manager.

The API is also a prototype. Before public production use, review and restrict its CORS policy, protect uploaded files, configure HTTPS, use persistent database and file storage, and add appropriate rate limits and authorization/security tests. Deploying this API alone does not deploy the Streamlit user interface.

## Validation performed during the UI work

- Tested the key citizen portal workflows, including report submission, location selection, history, editing, withdrawal, dashboard navigation, and sign-out.
- Checked Python syntax for the changed application, theme, chart, and map modules.
- Parsed the Streamlit TOML configuration and exercised populated and empty analytics chart builders.
- Checked the redesigned authentication page at a 390 px viewport; it had no horizontal page overflow.
- Ran `git diff --check`.

## Suggested project presentation

> CivicPulse is a civic issue reporting and management prototype. Citizens submit a description, location, and optional photo, then follow the report as it moves through the review process. Municipal administrators can triage reports, review possible duplicates, update statuses, and inspect operational summaries. The current categorization and duplicate checks are prototype heuristics; they support the workflow but do not replace human judgment.
