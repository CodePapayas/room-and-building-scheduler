-- SQLite database schema for Building Reservation System

-- ---------- 1. BUILDINGS ----------
CREATE TABLE Buildings (
    building_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL,
    address      TEXT NOT NULL,
    is_no_stair  INTEGER NOT NULL DEFAULT 0  -- SQLite uses INTEGER for boolean
);

-- ---------- 2. ROOMS ----------
CREATE TABLE Rooms (
    room_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    building_id       INTEGER NOT NULL,
    room_num          TEXT NOT NULL,
    capacity          INTEGER NOT NULL,
    floor             INTEGER NOT NULL DEFAULT 0,
    is_aca_compliant  INTEGER NOT NULL DEFAULT 0,  -- SQLite uses INTEGER for boolean
    FOREIGN KEY (building_id) REFERENCES Buildings(building_id)
);

-- Index for better performance
CREATE INDEX idx_room_building_num ON Rooms(building_id, room_num);

-- ---------- 3. RESERVATIONS (1‑hour slots) ----------
CREATE TABLE Reservations (
    reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id        INTEGER NOT NULL,
    reserved_by    TEXT NOT NULL,
    reserved_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status         TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),

    slot_date      DATE     NOT NULL,  -- e.g., '2025-08-04'
    slot_hour      INTEGER  NOT NULL,  -- store 7-19 (represents 07:00-08:00 … 19:00-20:00)

    FOREIGN KEY (room_id) REFERENCES Rooms(room_id),

    -- Enforce business rules
    CHECK (slot_hour BETWEEN 7 AND 19),

    -- Prevent double-booking for approved reservations (partial unique index below) 
    -- NOTE: We'll add a partial index after table creation.
    
    UNIQUE(room_id, slot_date, slot_hour)  -- currently applies to all statuses; consider migrating to partial index
);

-- Indexes for performance
CREATE INDEX idx_room_date_hour ON Reservations(room_id, slot_date, slot_hour);
CREATE INDEX idx_status ON Reservations(status);
CREATE INDEX idx_slot_date ON Reservations(slot_date);

-- Optional: If you want only approved reservations to block slots in the future, you can:
-- 1. Remove the inline UNIQUE constraint (requires table rebuild in SQLite), and
-- 2. Add: CREATE UNIQUE INDEX uq_approved_room_slot ON Reservations(room_id, slot_date, slot_hour) WHERE status = 'approved';

-- ---------- 4. ADMINS ----------
CREATE TABLE Admins (
    admin_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username       TEXT NOT NULL UNIQUE,
    password_hash  TEXT NOT NULL,
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Index for faster username lookups
CREATE INDEX idx_admin_username ON Admins(username);
