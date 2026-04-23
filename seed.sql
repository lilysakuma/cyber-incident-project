INSERT INTO users (name, email, role) VALUES
('Alice Reporter', 'alice@example.com', 'reporter'),
('Bob Analyst', 'bob@example.com', 'analyst'),
('Carol Admin', 'carol@example.com', 'admin');

INSERT INTO incidents (title, description, incident_type, status, severity, reporter_id, assignee_id) VALUES
('Phishing Email Report', 'User received a fake Microsoft login email.', 'phishing', 'new', 3, 1, 2),
('MOVEit Exploit Investigation', 'Suspicious activity related to a known vulnerability.', 'vulnerability', 'investigating', 5, 1, 2);

INSERT INTO assets (asset_type, identifier, owner) VALUES
('device', 'LAPTOP-001', 'Alice Reporter'),
('account', 'alice@example.com', 'Alice Reporter'),
('server', 'web-server-01', 'IT Team');

INSERT INTO incident_asset (incident_id, asset_id) VALUES
(1, 1),
(1, 2),
(2, 3);

INSERT INTO tags (name) VALUES
('phishing'),
('credential theft'),
('vulnerability'),
('critical');

INSERT INTO incident_tag (incident_id, tag_id) VALUES
(1, 1),
(1, 2),
(2, 3),
(2, 4);

INSERT INTO vulnerabilities (cve_id, vendor, product, vulnerability_name, date_added) VALUES
('CVE-2023-34362', 'Progress', 'MOVEit Transfer', 'SQL Injection', '2023-06-02'),
('CVE-2022-1388', 'F5', 'BIG-IP', 'Authentication Bypass', '2022-05-04');

INSERT INTO evidence (incident_id, evidence_type, value, added_by) VALUES
(1, 'url', 'http://fake-login.example.com', 2),
(1, 'domain', 'fake-login.example.com', 2),
(2, 'cve', 'CVE-2023-34362', 2);

INSERT INTO tasks (incident_id, created_by, task_type, status, due_date, notes) VALUES
(1, 2, 'triage', 'doing', '2026-04-18', 'Review suspicious email headers and notify user.'),
(2, 2, 'contain', 'todo', '2026-04-19', 'Check affected server and isolate if needed.');