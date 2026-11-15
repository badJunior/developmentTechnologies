INSERT INTO seats (id, code, kind, capacity, opens_at, closes_at, max_minutes) VALUES
    ('11111111-1111-1111-1111-111111111111', 'desk-1',  'desk',         1, '08:00', '22:00', 480),
    ('11111111-1111-1111-1111-111111111112', 'desk-2',  'desk',         1, '08:00', '22:00', 480),
    ('22222222-2222-2222-2222-222222222221', 'room-a',  'meeting_room', 8, '09:00', '20:00', 180),
    ('33333333-3333-3333-3333-333333333331', 'booth-1', 'phone_booth',  1, '08:00', '22:00',  60)
ON CONFLICT (id) DO NOTHING;