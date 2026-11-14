INSERT INTO visitors (id, email, display_name, role) VALUES
    ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1', 'alice@example.com', 'Alice', 'visitor'),
    ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa2', 'bob@example.com',   'Bob',   'visitor'),
    ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa3', 'admin@example.com', 'Admin', 'admin')
ON CONFLICT (id) DO NOTHING;