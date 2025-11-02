-- Building and Scheduling Information (SQLite version)

-- =====================================================
-- INSERT SEED DATA
-- =====================================================
-- Note: Schema is created separately in schema.sql
-- This file only contains data inserts for Couch Connector Inc sample data

-- Insert buildings
INSERT INTO Buildings (name, address, is_no_stair) VALUES
('Couch Connector HQ', '100 Sofa Way', 1),
('Connector Collaboration Hub', '200 Cushion Blvd', 0),
('Connector Logistics Annex', '210 Cushion Blvd', 1),
('Couch Connector Support Center', '300 Ottoman Ave', 1);

-- Insert sample rooms
INSERT INTO Rooms (building_id, room_num, capacity, floor, is_aca_compliant) VALUES
-- Couch Connector HQ (building_id: 1)
(1, '101', 6, 1, 1),
(1, '102', 8, 1, 1),
(1, '201', 12, 2, 1),
(1, '202', 4, 2, 0),
-- Connector Collaboration Hub (building_id: 2)
(2, 'A1', 10, 1, 1),
(2, 'A2', 6, 1, 1),
(2, 'B1', 8, 2, 0),
(2, 'B2', 6, 2, 0),
-- Connector Logistics Annex (building_id: 3)
(3, 'L1', 8, 1, 1),
(3, 'L2', 8, 1, 1),
-- Couch Connector Support Center (building_id: 4)
(4, 'S1', 4, 1, 1),
(4, 'S2', 4, 1, 1),
(4, 'S3', 6, 2, 0);

-- =====================================================
-- COUCH CONNECTOR INC RECURRING SCHEDULES
-- =====================================================
-- This generates recurring reservations based on anonymized employee assignments
-- Pattern extends 8 weeks (2 months) from today

-- Create temporary table for weekly patterns
CREATE TEMP TABLE IF NOT EXISTS weekly_pattern (
    room_id INTEGER,
    reserved_by TEXT,
    day_offset INTEGER,
    slot_hour INTEGER,
    status TEXT
);

-- Insert weekly patterns in batches
INSERT INTO weekly_pattern (room_id, reserved_by, day_offset, slot_hour, status) VALUES
(1, 'Recurring: A Benson', 0, 9, 'approved'),
(1, 'Recurring: A Benson', 0, 10, 'approved'),
(1, 'Recurring: A Benson', 0, 11, 'approved'),
(1, 'Recurring: A Benson', 0, 12, 'approved'),
(1, 'Recurring: A Benson', 1, 9, 'approved'),
(1, 'Recurring: A Benson', 1, 10, 'approved'),
(1, 'Recurring: A Benson', 1, 11, 'approved'),
(1, 'Recurring: A Benson', 1, 12, 'approved'),
(1, 'Recurring: A Benson', 2, 9, 'approved'),
(1, 'Recurring: A Benson', 2, 10, 'approved'),
(1, 'Recurring: A Benson', 2, 11, 'approved'),
(1, 'Recurring: A Benson', 2, 12, 'approved'),
(2, 'Recurring: C Miles', 0, 13, 'approved'),
(2, 'Recurring: C Miles', 0, 14, 'approved'),
(2, 'Recurring: C Miles', 0, 15, 'approved'),
(2, 'Recurring: C Miles', 0, 16, 'approved'),
(2, 'Recurring: C Miles', 1, 13, 'approved'),
(2, 'Recurring: C Miles', 1, 14, 'approved'),
(2, 'Recurring: C Miles', 1, 15, 'approved'),
(2, 'Recurring: C Miles', 1, 16, 'approved'),
(2, 'Recurring: C Miles', 2, 13, 'approved'),
(2, 'Recurring: C Miles', 2, 14, 'approved'),
(2, 'Recurring: C Miles', 2, 15, 'approved'),
(2, 'Recurring: C Miles', 2, 16, 'approved'),
(2, 'Recurring: C Miles', 3, 13, 'approved'),
(2, 'Recurring: C Miles', 3, 14, 'approved'),
(2, 'Recurring: C Miles', 3, 15, 'approved'),
(2, 'Recurring: C Miles', 3, 16, 'approved'),
(2, 'Recurring: C Miles', 4, 13, 'approved'),
(2, 'Recurring: C Miles', 4, 14, 'approved'),
(2, 'Recurring: C Miles', 4, 15, 'approved'),
(2, 'Recurring: C Miles', 4, 16, 'approved'),
(3, 'Recurring: E Lyons', 2, 9, 'approved'),
(3, 'Recurring: E Lyons', 2, 10, 'approved'),
(3, 'Recurring: E Lyons', 2, 11, 'approved'),
(3, 'Recurring: E Lyons', 4, 9, 'approved'),
(3, 'Recurring: E Lyons', 4, 10, 'approved'),
(3, 'Recurring: E Lyons', 4, 11, 'approved'),
(5, 'Recurring: J Patel', 1, 8, 'approved'),
(5, 'Recurring: J Patel', 1, 9, 'approved'),
(5, 'Recurring: J Patel', 1, 10, 'approved'),
(5, 'Recurring: J Patel', 3, 8, 'approved'),
(5, 'Recurring: J Patel', 3, 9, 'approved'),
(5, 'Recurring: J Patel', 3, 10, 'approved'),
(6, 'Recurring: K Shaw', 0, 10, 'approved'),
(6, 'Recurring: K Shaw', 0, 11, 'approved'),
(6, 'Recurring: K Shaw', 0, 12, 'approved'),
(6, 'Recurring: K Shaw', 0, 13, 'approved'),
(6, 'Recurring: K Shaw', 2, 10, 'approved'),
(6, 'Recurring: K Shaw', 2, 11, 'approved'),
(6, 'Recurring: K Shaw', 2, 12, 'approved'),
(6, 'Recurring: K Shaw', 2, 13, 'approved'),
(6, 'Recurring: K Shaw', 4, 10, 'approved'),
(6, 'Recurring: K Shaw', 4, 11, 'approved'),
(6, 'Recurring: K Shaw', 4, 12, 'approved'),
(6, 'Recurring: K Shaw', 4, 13, 'approved'),
(8, 'Recurring: L Rivera', 0, 10, 'approved'),
(8, 'Recurring: L Rivera', 0, 11, 'approved'),
(8, 'Recurring: L Rivera', 0, 12, 'approved'),
(8, 'Recurring: L Rivera', 2, 10, 'approved'),
(8, 'Recurring: L Rivera', 2, 11, 'approved'),
(8, 'Recurring: L Rivera', 2, 12, 'approved'),
(9, 'Recurring: R Singh', 1, 12, 'approved'),
(9, 'Recurring: R Singh', 1, 13, 'approved'),
(9, 'Recurring: R Singh', 1, 14, 'approved'),
(9, 'Recurring: R Singh', 1, 15, 'approved'),
(9, 'Recurring: R Singh', 3, 12, 'approved'),
(9, 'Recurring: R Singh', 3, 13, 'approved'),
(9, 'Recurring: R Singh', 3, 14, 'approved'),
(9, 'Recurring: R Singh', 3, 15, 'approved'),
(10, 'Recurring: T Gomez', 0, 8, 'approved'),
(10, 'Recurring: T Gomez', 0, 9, 'approved'),
(10, 'Recurring: T Gomez', 0, 10, 'approved'),
(10, 'Recurring: T Gomez', 2, 8, 'approved'),
(10, 'Recurring: T Gomez', 2, 9, 'approved'),
(10, 'Recurring: T Gomez', 2, 10, 'approved'),
(10, 'Recurring: T Gomez', 4, 8, 'approved'),
(10, 'Recurring: T Gomez', 4, 9, 'approved'),
(10, 'Recurring: T Gomez', 4, 10, 'approved'),
(11, 'Recurring: M Chen', 0, 8, 'approved'),
(11, 'Recurring: M Chen', 0, 9, 'approved'),
(11, 'Recurring: M Chen', 1, 8, 'approved'),
(11, 'Recurring: M Chen', 1, 9, 'approved'),
(11, 'Recurring: M Chen', 2, 8, 'approved'),
(11, 'Recurring: M Chen', 2, 9, 'approved'),
(11, 'Recurring: M Chen', 3, 8, 'approved'),
(11, 'Recurring: M Chen', 3, 9, 'approved'),
(11, 'Recurring: M Chen', 4, 8, 'approved'),
(11, 'Recurring: M Chen', 4, 9, 'approved'),
(12, 'Recurring: P Young', 1, 11, 'approved'),
(12, 'Recurring: P Young', 1, 12, 'approved'),
(12, 'Recurring: P Young', 1, 13, 'approved'),
(12, 'Recurring: P Young', 3, 11, 'approved'),
(12, 'Recurring: P Young', 3, 12, 'approved'),
(12, 'Recurring: P Young', 3, 13, 'approved'),
(13, 'Recurring: S Ward', 2, 11, 'approved'),
(13, 'Recurring: S Ward', 2, 12, 'approved'),
(13, 'Recurring: S Ward', 2, 13, 'approved'),
(13, 'Recurring: S Ward', 2, 14, 'approved'),
(13, 'Recurring: S Ward', 4, 11, 'approved');

INSERT INTO weekly_pattern (room_id, reserved_by, day_offset, slot_hour, status) VALUES
(13, 'Recurring: S Ward', 4, 12, 'approved'),
(13, 'Recurring: S Ward', 4, 13, 'approved'),
(13, 'Recurring: S Ward', 4, 14, 'approved');

-- Generate dates for the next 8 weeks and insert reservations
WITH RECURSIVE
  -- Generate week offsets (0 to 7 weeks = 8 weeks total)
  week_numbers(week_offset) AS (
    SELECT 0
    UNION ALL
    SELECT week_offset + 1 FROM week_numbers WHERE week_offset < 7
  ),
  -- Generate weekday patterns (0=Monday through 4=Friday)
  weekdays(day_offset, day_name) AS (
    VALUES 
      (0, 'Monday'),
      (1, 'Tuesday'),
      (2, 'Wednesday'),
      (3, 'Thursday'),
      (4, 'Friday')
  ),
  -- Calculate all actual dates
  all_dates AS (
    SELECT 
      date('now', 'start of day', 'weekday 1', '+' || (week_numbers.week_offset * 7 + weekdays.day_offset) || ' days') as slot_date,
      weekdays.day_name,
      weekdays.day_offset
    FROM week_numbers
    CROSS JOIN weekdays
  )
-- Insert the recurring pattern for all dates
INSERT INTO Reservations (room_id, reserved_by, slot_date, slot_hour, status)
SELECT 
  wp.room_id,
  wp.reserved_by,
  ad.slot_date,
  wp.slot_hour,
  wp.status
FROM all_dates ad
JOIN weekly_pattern wp ON ad.day_offset = wp.day_offset
ORDER BY ad.slot_date, wp.slot_hour;

-- Drop temporary table
DROP TABLE weekly_pattern;

-- Note: Time slots are 7-19 (7am to 7pm start times, last slot ends at 8pm)
-- This seed data creates recurring reservations for Couch Connector Inc sample staff assignments
-- - Recurring reservations are approved automatically
-- - Pattern extends 8 weeks (2 months) from database initialization
-- - Admins can create/modify additional recurring series via the admin panel

-- Insert default admin user
-- Default credentials: username='admin', password='admin123'
-- Password hash generated using bcrypt with cost factor 12
INSERT INTO Admins (username, password_hash) VALUES
('admin', '$2b$12$tKISoYNiu9b1cWaV2S4bnOqobX74P2rk2YJeQcrlxkCci5Zmu6jgy');
