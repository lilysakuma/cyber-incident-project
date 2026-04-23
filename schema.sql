PRAGMA foreign_keys = ON;

CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL CHECK(role IN ('reporter', 'analyst', 'admin'))
);

CREATE TABLE incidents (
    incident_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    incident_type TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('new', 'triaged', 'investigating', 'resolved', 'closed')),
    severity INTEGER NOT NULL CHECK(severity BETWEEN 1 AND 5),
    reporter_id INTEGER NOT NULL,
    assignee_id INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reporter_id) REFERENCES users(user_id),
    FOREIGN KEY (assignee_id) REFERENCES users(user_id)
);

CREATE TABLE assets (
    asset_id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_type TEXT NOT NULL CHECK(asset_type IN ('device', 'account', 'server')),
    identifier TEXT NOT NULL,
    owner TEXT,
    UNIQUE(asset_type, identifier)
);

CREATE TABLE evidence (
    evidence_id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id INTEGER NOT NULL,
    evidence_type TEXT NOT NULL CHECK(evidence_type IN ('url', 'domain', 'hash', 'cve', 'email_header', 'file')),
    value TEXT NOT NULL,
    file_path TEXT,
    added_at TEXT DEFAULT CURRENT_TIMESTAMP,
    added_by INTEGER,
    FOREIGN KEY (incident_id) REFERENCES incidents(incident_id),
    FOREIGN KEY (added_by) REFERENCES users(user_id),
    UNIQUE(incident_id, evidence_type, value)
);

CREATE TABLE tasks (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id INTEGER NOT NULL,
    created_by INTEGER NOT NULL,
    task_type TEXT NOT NULL CHECK(task_type IN ('triage', 'contain', 'eradicate', 'recover', 'postmortem')),
    status TEXT NOT NULL CHECK(status IN ('todo', 'doing', 'done')),
    due_date TEXT,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (incident_id) REFERENCES incidents(incident_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

CREATE TABLE tags (
    tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE incident_tag (
    incident_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (incident_id, tag_id),
    FOREIGN KEY (incident_id) REFERENCES incidents(incident_id),
    FOREIGN KEY (tag_id) REFERENCES tags(tag_id)
);

CREATE TABLE incident_asset (
    incident_id INTEGER NOT NULL,
    asset_id INTEGER NOT NULL,
    PRIMARY KEY (incident_id, asset_id),
    FOREIGN KEY (incident_id) REFERENCES incidents(incident_id),
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
);

CREATE TABLE vulnerabilities (
    cve_id TEXT PRIMARY KEY,
    vendor TEXT,
    product TEXT,
    vulnerability_name TEXT,
    date_added TEXT
);

CREATE INDEX idx_evidence_value ON evidence(value);
CREATE INDEX idx_incident_status ON incidents(status);
CREATE INDEX idx_incident_severity ON incidents(severity);