from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from datetime import datetime, timezone
from pathlib import Path
import hashlib, hmac, base64, json, os, re, secrets, shutil

ROOT = Path(__file__).resolve().parent
UPLOAD_DIR = ROOT / 'uploads'
UPLOAD_DIR.mkdir(exist_ok=True)
DATABASE_URL = os.getenv('DATABASE_URL', f"sqlite:///{ROOT / 'civic_issues.db'}")
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False} if DATABASE_URL.startswith('sqlite') else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()
SECRET_KEY = os.getenv('CIVIC_SECRET_KEY', '')

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(180), unique=True, index=True, nullable=False)
    password_hash = Column(String(300), nullable=False)
    role = Column(String(20), default='citizen', nullable=False)

class Report(Base):
    __tablename__ = 'reports'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    title = Column(String(160), nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String(240), nullable=False)
    category = Column(String(60), nullable=False)
    severity = Column(String(30), nullable=False)
    status = Column(String(30), default='Submitted', nullable=False)
    image_name = Column(String(240), nullable=True)
    suspicious = Column(String(10), default='No')
    duplicate_of = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    action = Column(String(100), nullable=False)
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

Base.metadata.create_all(bind=engine)
app = FastAPI(title='Civic Issue Reporting API', version='1.0.0', description='College prototype for secure civic issue reporting')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=False, allow_methods=['*'], allow_headers=['*'])
app.mount('/uploads', StaticFiles(directory=str(UPLOAD_DIR)), name='uploads')

class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=180)
    password: str = Field(min_length=8, max_length=128)
class LoginIn(BaseModel):
    email: str
    password: str
class StatusIn(BaseModel):
    status: str


def db_session():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 240000)
    return base64.b64encode(salt).decode() + '$' + base64.b64encode(digest).decode()

def verify_password(password: str, stored: str) -> bool:
    try:
        salt_s, digest_s = stored.split('$', 1)
        salt = base64.b64decode(salt_s); expected = base64.b64decode(digest_s)
        actual = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 240000)
        return hmac.compare_digest(actual, expected)
    except Exception: return False

def make_token(user: User) -> str:
    payload = {'id': user.id, 'role': user.role, 'exp': int(datetime.now(timezone.utc).timestamp()) + 60*60*12}
    raw = base64.urlsafe_b64encode(json.dumps(payload, separators=(',', ':')).encode()).decode().rstrip('=')
    sig = hmac.new(SECRET_KEY.encode(), raw.encode(), hashlib.sha256).hexdigest()
    return raw + '.' + sig

def current_user(authorization: str | None = Header(default=None), db: Session = Depends(db_session)):
    if not authorization or not authorization.startswith('Bearer '): raise HTTPException(401, 'Please log in first')
    token = authorization[7:]
    try:
        raw, sig = token.rsplit('.', 1)
        expected = hmac.new(SECRET_KEY.encode(), raw.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected): raise ValueError()
        payload = json.loads(base64.urlsafe_b64decode(raw + '=' * (-len(raw) % 4)))
        if payload.get('exp', 0) < int(datetime.now(timezone.utc).timestamp()): raise ValueError()
        user = db.query(User).filter(User.id == payload['id']).first()
        if not user: raise ValueError()
        return user
    except Exception: raise HTTPException(401, 'Session invalid or expired; please log in again')

def admin_user(user: User = Depends(current_user)):
    if user.role != 'admin': raise HTTPException(403, 'Administrator access required')
    return user

def log_action(db: Session, user_id: int, action: str, detail: str = ''):
    db.add(AuditLog(user_id=user_id, action=action, detail=detail[:500])); db.commit()

def analyze_report(title: str, description: str, db: Session):
    text = (title + ' ' + description).lower()
    categories = {
        'Road/Pothole': ['pothole', 'road', 'asphalt', 'crack', 'street damage'],
        'Garbage/Waste': ['garbage', 'waste', 'rubbish', 'litter', 'dump', 'trash'],
        'Drainage': ['drain', 'sewage', 'waterlogging', 'blocked pipe', 'flood'],
        'Footpath': ['footpath', 'sidewalk', 'pavement', 'pedestrian'],
        'Streetlight': ['streetlight', 'street light', 'lamp', 'dark road', 'light not working'],
        'Water Supply': ['water leak', 'water supply', 'pipe leak', 'no water'],
    }
    scores = {cat: sum(1 for term in terms if term in text) for cat, terms in categories.items()}
    category = max(scores, key=scores.get) if max(scores.values(), default=0) else 'Other Infrastructure'
    urgent_terms = ['accident', 'dangerous', 'open manhole', 'exposed wire', 'collapsed', 'injury', 'severe', 'emergency']
    severity = 'High' if any(term in text for term in urgent_terms) else ('Medium' if any(term in text for term in ['blocked', 'large', 'broken', 'overflow', 'deep']) else 'Low')
    suspicious = 'Yes' if len(re.sub(r'\W', '', description)) < 8 or len(description) > 1800 or len(set(description.lower().split())) <= 2 else 'No'
    # Prototype duplicate matching: compare normalized title/description tokens with recent reports.
    tokens = set(re.findall(r'[a-z]{4,}', text))
    duplicate_of = None
    for old in db.query(Report).order_by(Report.id.desc()).limit(100).all():
        old_tokens = set(re.findall(r'[a-z]{4,}', (old.title + ' ' + old.description).lower()))
        if tokens and old_tokens and len(tokens & old_tokens) / max(1, len(tokens | old_tokens)) >= 0.65:
            duplicate_of = old.id; break
    return category, severity, suspicious, duplicate_of

def report_dict(r: Report, db: Session):
    user = db.query(User).filter(User.id == r.user_id).first()
    return {'id': r.id, 'title': r.title, 'description': r.description, 'location': r.location, 'category': r.category, 'severity': r.severity, 'status': r.status, 'image_url': f'/uploads/{r.image_name}' if r.image_name else None, 'suspicious': r.suspicious, 'duplicate_of': r.duplicate_of, 'created_at': r.created_at.isoformat(), 'reported_by': user.name if user else 'Unknown'}

@app.on_event('startup')
def seed_admin():
    if len(SECRET_KEY) < 32:
        raise RuntimeError('CIVIC_SECRET_KEY must be configured with at least 32 characters')
    admin_email = os.getenv('CIVIC_ADMIN_EMAIL', '').strip().lower()
    admin_password = os.getenv('CIVIC_ADMIN_PASSWORD', '')
    if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', admin_email):
        raise RuntimeError('CIVIC_ADMIN_EMAIL must be configured with a valid email address')
    if len(admin_password) < 12:
        raise RuntimeError('CIVIC_ADMIN_PASSWORD must be configured with at least 12 characters')

    db = SessionLocal()
    try:
        legacy_admin = db.query(User).filter(User.email == 'admin@civic.local').first()
        if legacy_admin and legacy_admin.email != admin_email and legacy_admin.role == 'admin':
            legacy_admin.role = 'citizen'
            legacy_admin.password_hash = hash_password(secrets.token_urlsafe(48))

        admin = db.query(User).filter(User.email == admin_email).first()
        if admin:
            admin.role = 'admin'
            admin.password_hash = hash_password(admin_password)
        else:
            db.add(User(name='Administrator', email=admin_email, password_hash=hash_password(admin_password), role='admin'))
        db.commit()
    finally: db.close()

@app.get('/')
def root(): return {'message': 'Civic Issue Reporting API is running', 'docs': '/docs'}
@app.get('/api/health')
def health(): return {'status': 'ok', 'time': datetime.now(timezone.utc).isoformat()}

@app.post('/api/register')
def register(data: RegisterIn, db: Session = Depends(db_session)):
    email = data.email.strip().lower()
    if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email): raise HTTPException(400, 'Enter a valid email address')
    if db.query(User).filter(User.email == email).first(): raise HTTPException(409, 'Email already registered')
    user = User(name=data.name.strip(), email=email, password_hash=hash_password(data.password), role='citizen')
    db.add(user); db.commit(); db.refresh(user); log_action(db, user.id, 'REGISTER', 'Citizen account created')
    return {'token': make_token(user), 'user': {'id': user.id, 'name': user.name, 'email': user.email, 'role': user.role}}

@app.post('/api/login')
def login(data: LoginIn, db: Session = Depends(db_session)):
    user = db.query(User).filter(User.email == data.email.strip().lower()).first()
    if not user or not verify_password(data.password, user.password_hash): raise HTTPException(401, 'Incorrect email or password')
    log_action(db, user.id, 'LOGIN', 'Successful login')
    return {'token': make_token(user), 'user': {'id': user.id, 'name': user.name, 'email': user.email, 'role': user.role}}

@app.get('/api/me')
def me(user: User = Depends(current_user)):
    return {'id': user.id, 'name': user.name, 'email': user.email, 'role': user.role}

@app.post('/api/reports')
def create_report(title: str = Form(...), description: str = Form(...), location: str = Form(...), image: UploadFile | None = File(default=None), user: User = Depends(current_user), db: Session = Depends(db_session)):
    title, description, location = title.strip(), description.strip(), location.strip()
    if not title or len(title) > 160: raise HTTPException(400, 'Title is required and must be at most 160 characters')
    if len(description) < 10 or len(description) > 2000: raise HTTPException(400, 'Description must be 10–2000 characters')
    if not location or len(location) > 240: raise HTTPException(400, 'A valid location is required')
    image_name = None
    if image and image.filename:
        if image.content_type not in ('image/jpeg', 'image/png', 'image/webp'): raise HTTPException(400, 'Only JPG, PNG, and WEBP images are accepted')
        content = image.file.read(5 * 1024 * 1024 + 1)
        if len(content) > 5 * 1024 * 1024: raise HTTPException(413, 'Image must be 5 MB or smaller')
        ext = {'image/jpeg': '.jpg', 'image/png': '.png', 'image/webp': '.webp'}[image.content_type]
        image_name = secrets.token_hex(16) + ext
        with open(UPLOAD_DIR / image_name, 'wb') as f: f.write(content)
    category, severity, suspicious, duplicate_of = analyze_report(title, description, db)
    report = Report(user_id=user.id, title=title, description=description, location=location, category=category, severity=severity, image_name=image_name, suspicious=suspicious, duplicate_of=duplicate_of)
    db.add(report); db.commit(); db.refresh(report)
    log_action(db, user.id, 'REPORT_CREATED', f'Report #{report.id} submitted')
    return report_dict(report, db)

@app.get('/api/reports')
def list_reports(user: User = Depends(current_user), db: Session = Depends(db_session)):
    query = db.query(Report)
    if user.role != 'admin': query = query.filter(Report.user_id == user.id)
    return [report_dict(r, db) for r in query.order_by(Report.id.desc()).all()]

@app.patch('/api/reports/{report_id}/status')
def update_status(report_id: int, data: StatusIn, user: User = Depends(admin_user), db: Session = Depends(db_session)):
    allowed = {'Submitted', 'Under Review', 'In Progress', 'Resolved', 'Rejected'}
    if data.status not in allowed: raise HTTPException(400, 'Invalid status')
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report: raise HTTPException(404, 'Report not found')
    report.status = data.status; db.commit(); log_action(db, user.id, 'STATUS_UPDATED', f'Report #{report.id} changed to {data.status}')
    return report_dict(report, db)

@app.get('/api/stats')
def stats(user: User = Depends(current_user), db: Session = Depends(db_session)):
    q = db.query(Report)
    if user.role != 'admin': q = q.filter(Report.user_id == user.id)
    reports = q.all()
    return {'total': len(reports), 'open': sum(r.status not in ('Resolved', 'Rejected') for r in reports), 'resolved': sum(r.status == 'Resolved' for r in reports), 'high_priority': sum(r.severity == 'High' for r in reports)}

@app.get('/api/audit-logs')
def audit_logs(user: User = Depends(admin_user), db: Session = Depends(db_session)):
    return [{'id': x.id, 'user_id': x.user_id, 'action': x.action, 'detail': x.detail, 'created_at': x.created_at.isoformat()} for x in db.query(AuditLog).order_by(AuditLog.id.desc()).limit(200).all()]
