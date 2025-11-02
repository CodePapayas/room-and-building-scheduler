from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import sqlite3
from functools import wraps
from datetime import datetime, date, timedelta
import os
from dotenv import load_dotenv
import bcrypt

load_dotenv()

app = Flask(__name__)

# Get secret key from environment (Azure App Settings)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24).hex())

# Database configuration - use /home for Azure App Service persistence
# Azure App Service persists /home directory across deployments
if os.environ.get("WEBSITE_SITE_NAME"):  # Running in Azure
    DATABASE = os.environ.get("DATABASE_PATH", os.path.join("/home", "building_rez.db"))
else:  # Running locally
    DATABASE = os.environ.get("DATABASE_PATH", "building_rez.db")

# Ensure database directory exists
db_dir = os.path.dirname(DATABASE)
if db_dir and not os.path.exists(db_dir):
    os.makedirs(db_dir, exist_ok=True)

# Weekday helpers for recurring reservation management (Monday=0)
WEEKDAY_OPTIONS = [
    (0, "Monday"),
    (1, "Tuesday"),
    (2, "Wednesday"),
    (3, "Thursday"),
    (4, "Friday"),
]

# Lookup list for SQLite weekday values (Sunday=0)
SQL_WEEKDAY_NAMES = [
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
]


def align_to_weekday(start: date, target_weekday: int) -> date:
    """Return the next occurrence of target_weekday on or after start."""
    if target_weekday < 0 or target_weekday > 6:
        raise ValueError("Weekday must be between 0 (Monday) and 6 (Sunday)")
    days_ahead = (target_weekday - start.weekday()) % 7
    return start + timedelta(days=days_ahead)

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # This allows dict-like access to rows
    return conn

def init_db():
    """Initialize the database with schema and sample data."""
    # Always recreate database on init to ensure fresh data
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
        print("Existing database removed for fresh initialization.")
    
    conn = sqlite3.connect(DATABASE)
    
    # Read and execute schema
    with open('schema.sql', 'r') as f:
        conn.executescript(f.read())
    
    # Read and execute sample data
    try:
        with open('seed.sql', 'r') as f:
            conn.executescript(f.read())
        print("Database initialized with sample data!")
    except FileNotFoundError:
        print("Database schema created. Sample data file not found.")
    
    conn.close()
    return True

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            flash('Admin access required')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Custom Jinja2 filters
@app.template_filter('hour_to_12hr')
def hour_to_12hr(hour):
    """Convert 24-hour format to 12-hour format with AM/PM"""
    if hour == 0:
        return "12:00 AM"
    elif hour < 12:
        return f"{hour}:00 AM"
    elif hour == 12:
        return "12:00 PM"
    else:
        return f"{hour - 12}:00 PM"

@app.template_filter('time_range_12hr')
def time_range_12hr(start_hour):
    """Convert hour range to 12-hour format (e.g., 9:00 AM - 10:00 AM)"""
    return f"{hour_to_12hr(start_hour)} - {hour_to_12hr(start_hour + 1)}"

# Client-facing routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search')
def search():
    slot_date = request.args.get("slot_date")   # e.g. '2025-08-04'
    building = request.args.get("building_id")  # may be blank
    start_hour = request.args.get("start_hour")   # required
    end_hour = request.args.get("end_hour")       # required
    floor = request.args.get("floor")           # optional

    # Coerce empty strings to None
    if building == '':
        building = None
    if floor == '':
        floor = None
    
    # Validate time range
    if not start_hour or not end_hour:
        return jsonify({"error": "Start and end times are required"}), 400
    
    try:
        start_hour = int(start_hour)
        end_hour = int(end_hour)
        if not (7 <= start_hour < end_hour <= 20):
            return jsonify({"error": "Invalid time range"}), 400
    except ValueError:
        return jsonify({"error": "Invalid time format"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    # Find rooms that are available for ALL hours in the requested range
    # A room is available only if it has no approved reservations for ANY hour in the range
    sql = """
        SELECT DISTINCT r.room_id, r.room_num, r.capacity, r.floor, b.name AS building_name, b.building_id
        FROM   Rooms r
        JOIN   Buildings b ON b.building_id = r.building_id
        WHERE  (? IS NULL OR r.building_id = ?)
          AND  (? IS NULL OR r.floor = ?)
          AND  r.room_id NOT IN (
              SELECT room_id 
              FROM Reservations 
              WHERE slot_date = ? 
                AND slot_hour >= ? 
                AND slot_hour < ?
                AND status = 'approved'
          )
        ORDER  BY b.name, r.floor, r.room_num
    """
    params = (building, building, floor, floor, slot_date, start_hour, end_hour)
    cur.execute(sql, params)
    rooms = [dict(row) for row in cur.fetchall()]
    cur.close()
    conn.close()

    return jsonify({"rooms": rooms})

@app.route('/buildings')
def get_buildings():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT building_id, name FROM Buildings ORDER BY name")
    buildings = [dict(row) for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return jsonify({"buildings": buildings})

@app.route('/floors/<int:building_id>')
def get_floors(building_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT DISTINCT floor FROM Rooms WHERE building_id = ? ORDER BY floor", (building_id,))
    floors = [row[0] for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return jsonify({"floors": floors})

@app.route('/reserve', methods=['POST'])
def make_reservation():
    data = request.json
    room_id = data.get('room_id')
    reserved_by = data.get('reserved_by')
    slot_date = data.get('slot_date')
    start_hour = data.get('start_hour')
    end_hour = data.get('end_hour')

    if not all([room_id, reserved_by, slot_date, start_hour, end_hour]):
        return jsonify({"error": "Missing required fields"}), 400

    # Validate weekday (Monday=0, Sunday=6)
    try:
        reservation_date = datetime.strptime(slot_date, '%Y-%m-%d').date()
        if reservation_date.weekday() > 4:  # Saturday=5, Sunday=6
            return jsonify({"error": "Reservations are only allowed on weekdays"}), 400
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400

    # Validate time range
    try:
        start_hour = int(start_hour)
        end_hour = int(end_hour)
        if not (7 <= start_hour < end_hour <= 20):
            return jsonify({"error": "Time range must be between 07:00 and 20:00, with end after start"}), 400
    except ValueError:
        return jsonify({"error": "Invalid time format"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Check if ANY hour in the range is already reserved
        cur.execute("""
            SELECT slot_hour FROM Reservations 
            WHERE room_id = ? 
              AND slot_date = ? 
              AND slot_hour >= ? 
              AND slot_hour < ?
              AND status IN ('pending', 'approved')
            LIMIT 1
        """, (room_id, slot_date, start_hour, end_hour))
        
        conflict = cur.fetchone()
        if conflict:
            cur.close()
            conn.close()
            return jsonify({"error": f"Time slot {conflict[0]}:00 is already reserved or pending"}), 409
        
        # Create individual hourly reservations for each hour in the range
        reservation_ids = []
        for hour in range(start_hour, end_hour):
            cur.execute("""
                INSERT INTO Reservations (room_id, reserved_by, slot_date, slot_hour, status)
                VALUES (?, ?, ?, ?, 'pending')
            """, (room_id, reserved_by, slot_date, hour))
            reservation_ids.append(cur.lastrowid)
        
        conn.commit()
        cur.close()
        conn.close()
        
        hours_count = end_hour - start_hour
        return jsonify({
            "message": f"Reservation submitted for approval ({hours_count} hour{'s' if hours_count > 1 else ''})",
            "reservation_ids": reservation_ids,
            "hours_reserved": hours_count
        })
    
    except sqlite3.IntegrityError:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"error": "One or more time slots already reserved"}), 409
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"error": str(e)}), 500

# Admin routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username and password are required')
            return render_template('admin/login.html')
        
        # Query database for admin user
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT admin_id, username, password_hash FROM Admins WHERE username = ?", (username,))
        admin = cur.fetchone()
        cur.close()
        conn.close()
        
        # Verify password using bcrypt
        if admin and bcrypt.checkpw(password.encode('utf-8'), admin['password_hash'].encode('utf-8')):
            session['is_admin'] = True
            session['admin_username'] = admin['username']
            session['admin_id'] = admin['admin_id']
            flash('Successfully logged in', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    session.pop('admin_username', None)
    return redirect(url_for('index'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get pending reservations
    cur.execute("""
        SELECT r.reservation_id, r.reserved_by, r.slot_date, r.slot_hour, r.reserved_at,
               rm.room_id, rm.room_num, rm.capacity, rm.floor, b.name as building_name
        FROM Reservations r
        JOIN Rooms rm ON r.room_id = rm.room_id
        JOIN Buildings b ON rm.building_id = b.building_id
        WHERE r.status = 'pending'
        ORDER BY r.reserved_by, r.slot_date, r.slot_hour
    """)
    pending_reservations = [dict(row) for row in cur.fetchall()]
    
    # Group reservations into blocks (consecutive hours for same person, room, date)
    grouped_reservations = []
    current_block = []
    
    for res in pending_reservations:
        if not current_block:
            current_block = [res]
        else:
            last_res = current_block[-1]
            # Check if this reservation is consecutive (same person, room, date, and hour is consecutive)
            if (res['reserved_by'] == last_res['reserved_by'] and
                res['room_id'] == last_res['room_id'] and
                res['slot_date'] == last_res['slot_date'] and
                res['slot_hour'] == last_res['slot_hour'] + 1):
                current_block.append(res)
            else:
                # Save the current block and start a new one
                grouped_reservations.append(current_block)
                current_block = [res]
    
    # Don't forget the last block
    if current_block:
        grouped_reservations.append(current_block)
    
    # Get statistics
    cur.execute("SELECT COUNT(*) as total FROM Reservations WHERE status = 'pending'")
    pending_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) as total FROM Reservations WHERE status = 'approved'")
    approved_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) as total FROM Buildings")
    building_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) as total FROM Rooms")
    room_count = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    
    stats = {
        'pending': pending_count,
        'approved': approved_count,
        'buildings': building_count,
        'rooms': room_count
    }
    
    return render_template('admin/dashboard.html', 
                         reservation_blocks=grouped_reservations, 
                         stats=stats)

@app.route('/admin/reservations')
@admin_required
def admin_reservations():
    status_filter = request.args.get('status', 'all')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    if status_filter == 'all':
        cur.execute("""
            SELECT r.reservation_id, r.reserved_by, r.slot_date, r.slot_hour, r.reserved_at, r.status,
                   rm.room_num, rm.capacity, rm.floor, b.name as building_name
            FROM Reservations r
            JOIN Rooms rm ON r.room_id = rm.room_id
            JOIN Buildings b ON rm.building_id = b.building_id
            ORDER BY r.reserved_at DESC
        """)
    else:
        cur.execute("""
            SELECT r.reservation_id, r.reserved_by, r.slot_date, r.slot_hour, r.reserved_at, r.status,
                   rm.room_num, rm.capacity, rm.floor, b.name as building_name
            FROM Reservations r
            JOIN Rooms rm ON r.room_id = rm.room_id
            JOIN Buildings b ON rm.building_id = b.building_id
            WHERE r.status = ?
            ORDER BY r.reserved_at DESC
        """, (status_filter,))
    
    reservations = [dict(row) for row in cur.fetchall()]
    cur.close()
    conn.close()
    
    return render_template('admin/reservations.html', 
                         reservations=reservations, 
                         status_filter=status_filter)

@app.route('/admin/approve/<int:reservation_id>', methods=['POST'])
@admin_required
def approve_reservation(reservation_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("UPDATE Reservations SET status = 'approved' WHERE reservation_id = ?", 
                (reservation_id,))
    conn.commit()
    
    cur.close()
    conn.close()
    
    flash('Reservation approved successfully')
    # Redirect back to the page the user came from (dashboard, reservations, or room schedule)
    return redirect(request.referrer or url_for('admin_dashboard'))

@app.route('/admin/approve-block', methods=['POST'])
@admin_required
def approve_block():
    reservation_ids = request.form.get('reservation_ids', '')
    if not reservation_ids:
        flash('No reservations specified', 'error')
        return redirect(request.referrer or url_for('admin_dashboard'))
    
    # Convert comma-separated string to list of integers
    try:
        ids = [int(rid) for rid in reservation_ids.split(',')]
    except ValueError:
        flash('Invalid reservation IDs', 'error')
        return redirect(request.referrer or url_for('admin_dashboard'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Approve all reservations in the block
    placeholders = ','.join('?' * len(ids))
    cur.execute(f"UPDATE Reservations SET status = 'approved' WHERE reservation_id IN ({placeholders})", 
                ids)
    conn.commit()
    
    count = cur.rowcount
    cur.close()
    conn.close()
    
    flash(f'Successfully approved {count} reservation(s) in block')
    # Redirect back to the page the user came from
    return redirect(request.referrer or url_for('admin_dashboard'))

@app.route('/admin/reject-block', methods=['POST'])
@admin_required
def reject_block():
    reservation_ids = request.form.get('reservation_ids', '')
    if not reservation_ids:
        flash('No reservations specified', 'error')
        return redirect(request.referrer or url_for('admin_dashboard'))
    
    # Convert comma-separated string to list of integers
    try:
        ids = [int(rid) for rid in reservation_ids.split(',')]
    except ValueError:
        flash('Invalid reservation IDs', 'error')
        return redirect(request.referrer or url_for('admin_dashboard'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # reject all reservations in the block
    placeholders = ','.join('?' * len(ids))
    cur.execute(f"UPDATE Reservations SET status = 'rejected' WHERE reservation_id IN ({placeholders})", 
                ids)
    conn.commit()
    
    count = cur.rowcount
    cur.close()
    conn.close()
    
    flash(f'Successfully rejected {count} reservation(s) in block')
    # Redirect back to the page the user came from
    return redirect(request.referrer or url_for('admin_dashboard'))

@app.route('/admin/reject/<int:reservation_id>', methods=['POST'])
@admin_required
def reject_reservation(reservation_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("UPDATE Reservations SET status = 'rejected' WHERE reservation_id = ?", 
                (reservation_id,))
    conn.commit()
    
    cur.close()
    conn.close()
    
    flash('Reservation rejected')
    # Redirect back to the page the user came from (dashboard, reservations, or room schedule)
    return redirect(request.referrer or url_for('admin_dashboard'))

@app.route('/admin/cancel/<int:reservation_id>', methods=['POST'])
@admin_required
def cancel_reservation(reservation_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Delete the reservation to free up the time slot
    cur.execute("DELETE FROM Reservations WHERE reservation_id = ?", 
                (reservation_id,))
    conn.commit()
    
    cur.close()
    conn.close()
    
    flash('Reservation released - time slot is now available')
    return redirect(request.referrer or url_for('admin_reservations'))

@app.route('/admin/buildings')
@admin_required
def admin_buildings():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT b.*, COUNT(r.room_id) as room_count
        FROM Buildings b
        LEFT JOIN Rooms r ON b.building_id = r.building_id
        GROUP BY b.building_id
        ORDER BY b.name
    """)
    buildings = [dict(row) for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return render_template('admin/buildings.html', buildings=buildings)

@app.route('/admin/rooms')
@admin_required
def admin_rooms():
    building_id = request.args.get('building_id')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    if building_id:
        cur.execute("""
            SELECT r.*, b.name as building_name
            FROM Rooms r
            JOIN Buildings b ON r.building_id = b.building_id
            WHERE r.building_id = ?
            ORDER BY r.floor, r.room_num
        """, (building_id,))
    else:
        cur.execute("""
            SELECT r.*, b.name as building_name
            FROM Rooms r
            JOIN Buildings b ON r.building_id = b.building_id
            ORDER BY b.name, r.floor, r.room_num
        """)
    
    rooms = [dict(row) for row in cur.fetchall()]
    
    # Get buildings for filter
    cur.execute("SELECT building_id, name FROM Buildings ORDER BY name")
    buildings = [dict(row) for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return render_template('admin/rooms.html', 
                         rooms=rooms, 
                         buildings=buildings, 
                         selected_building=building_id)


@app.route('/admin/recurring', methods=['GET', 'POST'])
@admin_required
def admin_recurring():
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        reserved_by = request.form.get('reserved_by', '').strip()
        building_id = request.form.get('building_id')
        room_id = request.form.get('room_id')
        weekday = request.form.get('weekday')
        start_hour = request.form.get('start_hour')
        end_hour = request.form.get('end_hour')
        weeks = request.form.get('weeks', '8')
        start_date_str = request.form.get('start_date')
        status = request.form.get('status', 'approved')

        error = None

        try:
            if not reserved_by:
                raise ValueError('Series label is required.')

            if status not in ('pending', 'approved'):
                raise ValueError('Status must be pending or approved.')

            if not building_id:
                raise ValueError('Building selection is required.')

            if not room_id:
                raise ValueError('Room selection is required.')

            if weekday is None:
                raise ValueError('Weekday selection is required.')

            if start_hour is None or end_hour is None:
                raise ValueError('Start and end times are required.')

            room_id = int(room_id)
            weekday = int(weekday)
            start_hour = int(start_hour)
            end_hour = int(end_hour)
            weeks = max(1, min(int(weeks), 52))  # Bound loop length for safety

            if weekday < 0 or weekday > 6:
                raise ValueError('Invalid weekday selection.')

            if start_hour < 7 or start_hour > 19:
                raise ValueError('Start hour must be between 7 AM and 7 PM.')

            if end_hour <= start_hour or end_hour > 20:
                raise ValueError('End hour must be after start hour and no later than 8 PM.')

            if start_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            else:
                start_date = date.today()

            aligned_start = align_to_weekday(start_date, weekday)

            # Confirm room belongs to the selected building
            cur.execute(
                """
                SELECT Rooms.room_id, Rooms.room_num, Rooms.floor, Rooms.building_id, Buildings.name AS building_name
                FROM Rooms
                JOIN Buildings ON Buildings.building_id = Rooms.building_id
                WHERE Rooms.room_id = ?
                """,
                (room_id,)
            )
            room_record = cur.fetchone()

            if not room_record:
                raise ValueError('Selected room could not be found.')

            if building_id and str(room_record['building_id']) != building_id:
                raise ValueError('Selected room does not belong to the chosen building.')

            total_inserted = 0
            conflicts = []

            for week_index in range(weeks):
                slot_date = aligned_start + timedelta(weeks=week_index)

                for hour in range(start_hour, end_hour):
                    try:
                        cur.execute(
                            """
                            INSERT INTO Reservations (room_id, reserved_by, slot_date, slot_hour, status)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (room_id, reserved_by, slot_date.isoformat(), hour, status)
                        )
                        total_inserted += 1
                    except sqlite3.IntegrityError:
                        conflicts.append((slot_date, hour))

            conn.commit()

            if conflicts:
                unique_conflicts = sorted({(d.isoformat(), h) for d, h in conflicts})
                conflict_summary = ', '.join(f"{d} {hour_to_12hr(h)}" for d, h in unique_conflicts[:5])
                more_conflicts = len(unique_conflicts) - 5
                if more_conflicts > 0:
                    conflict_summary += f" … (+{more_conflicts} more)"
                flash(f"Added {total_inserted} slot(s). Skipped {len(conflicts)} conflict(s): {conflict_summary}.")
            else:
                flash(f"Added {total_inserted} slot(s) for {reserved_by} starting {aligned_start}.")

        except ValueError as exc:
            error = str(exc)
        except Exception as exc:
            error = f"Unable to create recurring series: {exc}"

        if error:
            conn.rollback()
            flash(error)

        conn.close()
        return redirect(url_for('admin_recurring'))

    # Data for form selections
    cur.execute("SELECT building_id, name FROM Buildings ORDER BY name")
    buildings = [dict(row) for row in cur.fetchall()]

    cur.execute(
        """
        SELECT Rooms.room_id, Rooms.room_num, Rooms.floor, Rooms.building_id, Buildings.name AS building_name
        FROM Rooms
        JOIN Buildings ON Buildings.building_id = Rooms.building_id
        ORDER BY Buildings.name, Rooms.floor, Rooms.room_num
        """
    )
    rooms = [dict(row) for row in cur.fetchall()]

    cur.execute(
        """
        SELECT 
            Reservations.reserved_by,
            Reservations.room_id,
            Rooms.room_num,
            Buildings.name AS building_name,
            MIN(Reservations.slot_date) AS first_date,
            MAX(Reservations.slot_date) AS last_date,
            COUNT(*) AS total_slots,
            MIN(Reservations.slot_hour) AS start_hour,
            MAX(Reservations.slot_hour) AS end_hour,
            CAST(strftime('%w', Reservations.slot_date) AS INTEGER) AS sql_weekday,
            MIN(Reservations.status) AS status
        FROM Reservations
        JOIN Rooms ON Rooms.room_id = Reservations.room_id
        JOIN Buildings ON Buildings.building_id = Rooms.building_id
        WHERE Reservations.slot_date >= date('now')
          AND (Reservations.reserved_by LIKE 'Weekly:%' OR Reservations.reserved_by LIKE 'Recurring:%')
        GROUP BY Reservations.reserved_by, Reservations.room_id, sql_weekday, Reservations.status
        HAVING COUNT(*) >= 1
        ORDER BY Reservations.reserved_by, sql_weekday, Rooms.room_num
        """
    )

    recurring_series = []
    for row in cur.fetchall():
        series = dict(row)
        weekday_index = series.get('sql_weekday')
        if weekday_index is not None and 0 <= weekday_index < len(SQL_WEEKDAY_NAMES):
            series['weekday_name'] = SQL_WEEKDAY_NAMES[weekday_index]
        else:
            series['weekday_name'] = 'Unknown'
        if series.get('end_hour') is not None:
            series['display_end_hour'] = series['end_hour'] + 1
        else:
            series['display_end_hour'] = None
        recurring_series.append(series)

    conn.close()

    hour_choices = list(range(7, 20))
    end_hour_choices = list(range(8, 21))
    default_start_date = align_to_weekday(date.today(), 0).isoformat()

    return render_template(
        'admin/recurring.html',
        buildings=buildings,
        rooms=rooms,
        weekday_options=WEEKDAY_OPTIONS,
        recurring_series=recurring_series,
        hour_choices=hour_choices,
        end_hour_choices=end_hour_choices,
        default_start_date=default_start_date
    )


@app.route('/admin/recurring/delete', methods=['POST'])
@admin_required
def delete_recurring():
    reserved_by = request.form.get('reserved_by')
    room_id = request.form.get('room_id')
    sql_weekday = request.form.get('weekday')
    from_date = request.form.get('from_date') or date.today().isoformat()
    status = request.form.get('status')

    if not (reserved_by and room_id and sql_weekday is not None):
        flash('Missing series information for removal.')
        return redirect(url_for('admin_recurring'))

    try:
        room_id = int(room_id)
        sql_weekday = int(sql_weekday)
    except ValueError:
        flash('Invalid series identifiers.')
        return redirect(url_for('admin_recurring'))

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        params = [reserved_by, room_id, sql_weekday, from_date]
        status_clause = ''
        if status:
            status_clause = ' AND status = ?'
            params.append(status)

        cur.execute(
            f"""
            DELETE FROM Reservations
            WHERE reserved_by = ?
              AND room_id = ?
              AND CAST(strftime('%w', slot_date) AS INTEGER) = ?
              AND slot_date >= ?
              {status_clause}
            """,
            params
        )

        deleted_count = cur.rowcount
        conn.commit()

        weekday_label = SQL_WEEKDAY_NAMES[sql_weekday] if 0 <= sql_weekday < len(SQL_WEEKDAY_NAMES) else 'selected day'
        if deleted_count:
            flash(f"Removed {deleted_count} slot(s) for {reserved_by} on {weekday_label} starting {from_date}.")
        else:
            flash('No matching recurring slots found to remove.')

    except Exception as exc:
        conn.rollback()
        flash(f'Unable to remove recurring series: {exc}')
    finally:
        conn.close()

    return redirect(url_for('admin_recurring'))

@app.route('/admin/room/<int:room_id>/schedule')
@admin_required
def room_schedule(room_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get room details
    cur.execute("""
        SELECT r.*, b.name as building_name
        FROM Rooms r
        JOIN Buildings b ON r.building_id = b.building_id
        WHERE r.room_id = ?
    """, (room_id,))
    room = cur.fetchone()
    
    if not room:
        flash('Room not found')
        return redirect(url_for('admin_rooms'))
    
    room = dict(room)
    
    # Get today's date and calculate 3 weeks from now
    today = date.today()
    end_date = today + timedelta(weeks=3)
    
    # Get all reservations for this room in the next 3 weeks (excluding rejected)
    cur.execute("""
        SELECT reservation_id, reserved_by, slot_date, slot_hour, reserved_at, status
        FROM Reservations
        WHERE room_id = ?
          AND slot_date >= ?
          AND slot_date <= ?
          AND status != 'rejected'
        ORDER BY slot_date, slot_hour
    """, (room_id, today, end_date))
    
    reservations = [dict(row) for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    # Group reservations by date
    from collections import defaultdict
    reservations_by_date_dict = defaultdict(list)
    
    for res in reservations:
        reservations_by_date_dict[res['slot_date']].append(res)
    
    # Create a list of all dates in the range with their reservations
    reservations_by_date = []
    current_date = today
    while current_date <= end_date:
        # Only include weekdays (Monday=0 to Friday=4)
        if current_date.weekday() < 5:
            date_str = current_date.strftime('%Y-%m-%d')
            reservations_by_date.append({
                'date': date_str,
                'date_formatted': current_date.strftime('%B %d, %Y'),
                'day_name': current_date.strftime('%A'),
                'reservations': reservations_by_date_dict.get(date_str, [])
            })
        current_date += timedelta(days=1)
    
    return render_template('admin/room_schedule.html',
                         room=room,
                         reservations_by_date=reservations_by_date)

# Initialize database when module is loaded (not just when running directly)
# This ensures database is created when Gunicorn imports the module
init_db()

if __name__ == '__main__':
    # This block is for local development only
    # Azure App Service uses Gunicorn with startup command configured in App Settings
    debug_mode = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
    port = int(os.environ.get('PORT', 8000))
    
    app.run(debug=debug_mode, port=port, host='0.0.0.0')
