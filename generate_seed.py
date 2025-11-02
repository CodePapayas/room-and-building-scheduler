"""
Generate seed.sql with employee schedules
This script generates the seed.sql file to avoid SQLite's 500-term UNION ALL limit
"""

# Employee schedule data (de-identified for Couch Connector Inc)
employees = [
  # Couch Connector HQ (building_id: 1)
  {'name': 'A Benson', 'room_id': 1, 'days': [0, 1, 2], 'hours': range(9, 13)},
  {'name': 'C Miles', 'room_id': 2, 'days': [0, 1, 2, 3, 4], 'hours': range(13, 17)},
  {'name': 'E Lyons', 'room_id': 3, 'days': [2, 4], 'hours': range(9, 12)},

  # Connector Collaboration Hub (building_id: 2)
  {'name': 'J Patel', 'room_id': 5, 'days': [1, 3], 'hours': range(8, 11)},
  {'name': 'K Shaw', 'room_id': 6, 'days': [0, 2, 4], 'hours': range(10, 14)},
  {'name': 'L Rivera', 'room_id': 8, 'days': [0, 2], 'hours': range(10, 13)},

  # Connector Logistics Annex (building_id: 3)
  {'name': 'R Singh', 'room_id': 9, 'days': [1, 3], 'hours': range(12, 16)},
  {'name': 'T Gomez', 'room_id': 10, 'days': [0, 2, 4], 'hours': range(8, 11)},

  # Couch Connector Support Center (building_id: 4)
  {'name': 'M Chen', 'room_id': 11, 'days': [0, 1, 2, 3, 4], 'hours': range(8, 10)},
  {'name': 'P Young', 'room_id': 12, 'days': [1, 3], 'hours': range(11, 14)},
  {'name': 'S Ward', 'room_id': 13, 'days': [2, 4], 'hours': range(11, 15)},
]

# Generate seed.sql content
with open('seed.sql', 'w', encoding='utf-8') as f:
    f.write("""-- Building and Scheduling Information (SQLite version)

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
""")
    
    # Insert employee schedules in batches
    batch_size = 100
    current_batch = []
    
    for emp in employees:
        for day in emp['days']:
            for hour in emp['hours']:
                # Escape single quotes in names
                name = emp['name'].replace("'", "''")
                current_batch.append(f"({emp['room_id']}, 'Recurring: {name}', {day}, {hour}, 'approved')")
                
                if len(current_batch) >= batch_size:
                    f.write("INSERT INTO weekly_pattern (room_id, reserved_by, day_offset, slot_hour, status) VALUES\n")
                    f.write(",\n".join(current_batch))
                    f.write(";\n\n")
                    current_batch = []
    
    # Write remaining batch
    if current_batch:
        f.write("INSERT INTO weekly_pattern (room_id, reserved_by, day_offset, slot_hour, status) VALUES\n")
        f.write(",\n".join(current_batch))
        f.write(";\n\n")
    
    # Generate dates and insert reservations
    f.write("""-- Generate dates for the next 8 weeks and insert reservations
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
""")

print("seed.sql generated successfully!")
print(f"Total employees: {len(set(emp['name'] for emp in employees))}")
print(f"Total schedule entries: {sum(len(emp['days']) * len(list(emp['hours'])) for emp in employees)}")
