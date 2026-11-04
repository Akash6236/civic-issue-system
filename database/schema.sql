-- Activate Foreign Key Constraints (execute on every SQLite connection)
PRAGMA foreign_keys = ON;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
    phone TEXT,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'citizen' CHECK (role IN ('citizen', 'admin')),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2. Complaints Table
CREATE TABLE IF NOT EXISTS complaints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    image_path TEXT,
    location_address TEXT NOT NULL,
    latitude REAL,
    longitude REAL,
    location_accuracy REAL CHECK (location_accuracy IS NULL OR location_accuracy >= 0.0),
    location_source TEXT CHECK (location_source IS NULL OR location_source IN ('GPS', 'EXIF', 'Manual')),
    location_confirmed INTEGER NOT NULL DEFAULT 0 CHECK (location_confirmed IN (0, 1)),
    ai_category TEXT,
    ai_confidence REAL CHECK (ai_confidence IS NULL OR (ai_confidence >= 0.0 AND ai_confidence <= 1.0)),
    status TEXT NOT NULL DEFAULT 'Submitted' CHECK (
        status IN ('Submitted', 'Under Review', 'Approved', 'In Progress', 'Resolved', 'Rejected')
    ),
    is_anonymous INTEGER NOT NULL DEFAULT 0 CHECK (is_anonymous IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (
        (latitude IS NULL AND longitude IS NULL)
        OR (
            latitude IS NOT NULL
            AND longitude IS NOT NULL
            AND latitude >= -90.0 AND latitude <= 90.0
            AND longitude >= -180.0 AND longitude <= 180.0
        )
    ),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE RESTRICT
);

-- 3. Complaint Status History Table
CREATE TABLE IF NOT EXISTS complaint_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    complaint_id INTEGER NOT NULL,
    changed_by_user_id INTEGER NOT NULL,
    old_status TEXT CHECK (
        old_status IS NULL OR old_status IN ('Submitted', 'Under Review', 'Approved', 'In Progress', 'Resolved', 'Rejected')
    ),
    new_status TEXT NOT NULL CHECK (
        new_status IN ('Submitted', 'Under Review', 'Approved', 'In Progress', 'Resolved', 'Rejected')
    ),
    remarks TEXT,
    changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (old_status IS NULL OR old_status != new_status),
    FOREIGN KEY (complaint_id) REFERENCES complaints (id) ON DELETE RESTRICT,
    FOREIGN KEY (changed_by_user_id) REFERENCES users (id) ON DELETE RESTRICT
);

-- 4. Resolution Table (1-to-1 with Complaints)
CREATE TABLE IF NOT EXISTS resolution (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    complaint_id INTEGER NOT NULL UNIQUE,
    resolved_by_admin_id INTEGER NOT NULL,
    resolution_notes TEXT NOT NULL,
    proof_image_path TEXT,
    resolved_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (complaint_id) REFERENCES complaints (id) ON DELETE RESTRICT,
    FOREIGN KEY (resolved_by_admin_id) REFERENCES users (id) ON DELETE RESTRICT
);

-- 5. Duplicate Matches Table
CREATE TABLE IF NOT EXISTS duplicate_matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_complaint_id INTEGER NOT NULL,
    duplicate_complaint_id INTEGER NOT NULL,
    similarity_score REAL NOT NULL CHECK (similarity_score >= 0.0 AND similarity_score <= 100.0),
    status TEXT NOT NULL DEFAULT 'Pending Review' CHECK (
        status IN ('Pending Review', 'Confirmed Duplicate', 'Marked Not Duplicate')
    ),
    reviewed_by_admin_id INTEGER,
    reviewed_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (original_complaint_id < duplicate_complaint_id),
    CHECK (
        (status = 'Pending Review' AND reviewed_by_admin_id IS NULL AND reviewed_at IS NULL)
        OR (status IN ('Confirmed Duplicate', 'Marked Not Duplicate') AND reviewed_by_admin_id IS NOT NULL AND reviewed_at IS NOT NULL)
    ),
    UNIQUE (original_complaint_id, duplicate_complaint_id),
    FOREIGN KEY (original_complaint_id) REFERENCES complaints (id) ON DELETE RESTRICT,
    FOREIGN KEY (duplicate_complaint_id) REFERENCES complaints (id) ON DELETE RESTRICT,
    FOREIGN KEY (reviewed_by_admin_id) REFERENCES users (id) ON DELETE RESTRICT
);

-- 6. Admin Actions Audit Log Table
CREATE TABLE IF NOT EXISTS admin_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id INTEGER NOT NULL,
    complaint_id INTEGER,
    action_type TEXT NOT NULL,
    action_details TEXT,
    action_timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES users (id) ON DELETE RESTRICT,
    FOREIGN KEY (complaint_id) REFERENCES complaints (id) ON DELETE RESTRICT
);

