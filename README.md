# Building Reservation System

A comprehensive web application for managing building and room reservations with both client-facing and administrative interfaces.

## Deployment

This application is designed for **Azure App Service** with Python runtime and automated deployment via **GitHub Actions**.

### Quick Deploy to Azure

1. **Fork/Clone this repository**
2. **Create Azure App Service** (Python 3.12 runtime)
3. **Configure secrets** in GitHub repository
4. **Push to main branch** - automatic deployment!

**📖 See [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md) for complete step-by-step guide**

## Quick Start (Local Development)

```bash
# Clone and setup
git clone <repository-url>
cd building-rez

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# Create .env file
echo SECRET_KEY=your-generated-key > .env

# Run locally
python app.py

# Access
# Client: http://localhost:8000
# Admin:  http://localhost:8000/admin/login
# Login:  admin / admin123
```

## Features

### Client-Facing Web App
- 🔍 **Smart Search Interface**: Search rooms by building, floor, date, and time range
- 📱 **Responsive Design**: Mobile-friendly interface using Bootstrap 5
- 🏢 **Dynamic Filtering**: Building and floor dropdowns update based on selections
- ⏰ **12-Hour Time Display**: User-friendly time format throughout the application
- 📅 **Date/Time Validation**: Weekday bookings during business hours (7 AM - 5 PM)
- 💬 **Real-time Feedback**: Available rooms with capacity and accessibility info
- 📝 **Reservation Requests**: Submit reservations that go to admin for approval

### Admin Console
- 🔐 **Secure Login**: Bcrypt password hashing with session management
- 📊 **Dashboard**: Live statistics and pending reservations overview
- ✅ **Approval Workflow**: One-click approve/reject for pending reservations
- 📋 **Management Views**: 
  - View all reservations (filterable by status)
  - Browse buildings with accessibility info
  - Browse rooms with capacity and compliance details
  - Room-specific schedules with weekly calendar view
- 🔁 **Recurring Series**: Create and retire weekly patterns with automatic conflict detection
- 🎨 **Modern UI**: Sage green theme with intuitive navigation
- ⏰ **Time Range Display**: Shows full reservation time ranges in 12-hour format

## Technology Stack

- **Backend**: Python Flask 3.0.3
- **Database**: SQLite (file-based, persisted in Azure /home directory)
- **Frontend**: HTML5, CSS3, JavaScript ES6, Bootstrap 5
- **Icons**: Font Awesome
- **Authentication**: Bcrypt 4.2.1 password hashing with secure sessions
- **Security**: Environment-based configuration with python-dotenv
- **Web Server**: Gunicorn (production)
- **Hosting**: Azure App Service (Linux, Python 3.12 runtime)
- **CI/CD**: GitHub Actions

## Deployment Architecture

### Azure App Service Deployment

- **Runtime**: Python 3.12 on Linux
- **Web Server**: Gunicorn with 2 workers (configurable)
- **Port**: 8000 (Azure App Service standard)
- **Database**: SQLite stored in `/home` (persistent across deployments)
- **Environment**: Configuration via Azure App Settings
- **CI/CD**: Automated deployment via GitHub Actions on push to main
- **Monitoring**: Azure Application Insights (optional)
- **Scaling**: Vertical and horizontal scaling via Azure Portal

### Why Azure App Service?

- ✅ Fully managed platform (no server management)
- ✅ Automatic scaling and load balancing
- ✅ Built-in CI/CD with GitHub integration
- ✅ Free SSL certificates
- ✅ Easy deployment slots for staging/production
- ✅ Integrated monitoring and diagnostics
- ✅ Cost-effective for small to medium workloads

**For deployment instructions, see: [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md)**

## Installation

### Azure App Service (Production - Recommended)

**Complete guide:** [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md)

**Quick steps:**
1. Create Azure App Service with Python 3.12 runtime
2. Configure startup command: `gunicorn -w 2 -t 120 -b 0.0.0.0:8000 app:app`
3. Enable App Service Authentication (Entra ID) for perimeter protection
4. Set `SECRET_KEY` in Azure App Settings
5. Add `AZURE_WEBAPP_PUBLISH_PROFILE` to GitHub Secrets
6. Push to main branch → automatic deployment!

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd building-rez
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   # Generate SECRET_KEY
   python -c "import secrets; print(secrets.token_hex(32))"
   
   # Create .env file
   echo SECRET_KEY=your-generated-key > .env
   
   # Or on Windows PowerShell:
   # "SECRET_KEY=your-generated-key" | Out-File -FilePath .env -Encoding ASCII
   ```

4. **Run the application**
   ```bash
   python app.py
   ```
   Database (`building_rez.db`) is created automatically on first run using `schema.sql` and `seed.sql`.

5. **Access the application**
   - **Client Interface**: http://localhost:8000
   - **Admin Interface**: http://localhost:8000/admin/login
   - **Default Credentials**: `admin` / `admin123` ⚠️ **Change immediately in production!**

## Configuration

### Environment Variables

Set these in Azure App Settings (production) or `.env` file (local development):

```env
# Required - Flask session secret
SECRET_KEY=your-secret-key-here

# Optional - for local development only
# (Azure App Service automatically sets optimal values; do not set in production)
FLASK_DEBUG=false
# PORT is automatically injected by Azure; only set locally if overriding default
PORT=8000

# Optional - override database location; Azure defaults to /home/building_rez.db
# DATABASE_PATH=./building_rez.db
```

### Azure App Settings

Configure in Azure Portal → Your App Service → Configuration:

**Application Settings:**

| Name | Value | Required |
|------|-------|----------|
| `SECRET_KEY` | `[64-char random string]` | ✅ Yes |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` | ✅ Yes |

**General Settings:**

- **Startup Command**: `gunicorn -w 2 -t 120 -b 0.0.0.0:8000 app:app`
  - `-w 2`: 2 workers (optimal for Basic B1)
  - `-t 120`: 120-second timeout
  - `-b 0.0.0.0:8000`: Bind to port 8000

Enable App Service Authentication:
- Identity provider: Entra ID (Microsoft Identity)
- Action to take when request is not authenticated: `Log in with Microsoft`
- Keep internal admin login as secondary authorization layer

Generate SECRET_KEY:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Database Files

### Active Files (Required)
- **`schema.sql`**: SQLite database schema - defines all tables, indexes, and constraints
- **`seed.sql`**: Seed data - pre-populates database with sample buildings, rooms, recurring reservations, and default admin

### Database Location
- **Local development**: `building_rez.db` in project root
- **Azure App Service**: `/home/building_rez.db` (persistent across deployments)

### Recurring Reservations
The seed data creates an 8-week (2-month) rolling pattern of recurring reservations. For production, you'll want to implement automated maintenance to extend this pattern. See the "Recurring Reservations & Rolling Calendar" section below.

## Database Schema

### Buildings Table
```sql
building_id     INTEGER PRIMARY KEY AUTOINCREMENT
name            TEXT NOT NULL
address         TEXT
is_no_stair     INTEGER DEFAULT 0  -- 0=has stairs, 1=no stairs (fully accessible)
```

### Rooms Table
```sql
room_id           INTEGER PRIMARY KEY AUTOINCREMENT
building_id       INTEGER NOT NULL (FK -> Buildings)
room_num          TEXT NOT NULL
capacity          INTEGER DEFAULT 0
floor             INTEGER DEFAULT 0
is_aca_compliant  INTEGER DEFAULT 0  -- 0=not compliant, 1=ACA compliant
```

### Reservations Table
```sql
reservation_id  INTEGER PRIMARY KEY AUTOINCREMENT
room_id         INTEGER NOT NULL (FK -> Rooms)
reserved_by     TEXT NOT NULL
reserved_at     DATETIME DEFAULT CURRENT_TIMESTAMP
status          TEXT DEFAULT 'pending' CHECK IN ('pending','approved','rejected')
slot_date       DATE NOT NULL
slot_hour       INTEGER NOT NULL  -- 7-16 (7 AM - 4 PM start times)
UNIQUE(room_id, slot_date, slot_hour)  -- Prevents double-booking
```

### Admins Table
```sql
admin_id       INTEGER PRIMARY KEY AUTOINCREMENT
username       TEXT UNIQUE NOT NULL
password_hash  TEXT NOT NULL  -- Bcrypt hash
created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
```

**Note on Uniqueness**: The current constraint blocks ALL duplicate requests (pending + approved). To allow multiple pending reservations while blocking only approved ones, you can migrate to a partial index:

```sql
-- Drop the UNIQUE constraint and create partial index
CREATE UNIQUE INDEX IF NOT EXISTS uq_approved_room_slot 
ON Reservations(room_id, slot_date, slot_hour) 
WHERE status = 'approved';
```

## Admin Management

### Creating New Admin Users

1. **Generate password hash:**
   ```bash
   python generate_admin_hash.py
   # Enter desired password when prompted
   ```

2. **Insert into database:**
   ```bash
   sqlite3 building_rez.db
   ```
   ```sql
   INSERT INTO Admins (username, password_hash) 
   VALUES ('newadmin', 'hash_from_generator');
   ```

### Changing Admin Password

1. **Generate new hash:**
   ```bash
   python generate_admin_hash.py
   ```

2. **Update password:**
   ```bash
   sqlite3 building_rez.db
   ```
   ```sql
   UPDATE Admins 
   SET password_hash = 'new_hash_here'
   WHERE username = 'admin';
   ```

### List All Admins

```bash
sqlite3 building_rez.db "SELECT admin_id, username, created_at FROM Admins;"
```

### Delete Admin User

```bash
sqlite3 building_rez.db "DELETE FROM Admins WHERE username = 'oldadmin';"
```

### Reset to Default Admin

```bash
# Delete database (will be recreated with default admin on next run)
rm building_rez.db
python app.py
```

### Test Authentication

```bash
# Run test suite
python test_auth.py

# Or manually verify
python -c "from app import get_db_connection; import bcrypt; 
conn = get_db_connection(); 
cur = conn.cursor(); 
cur.execute('SELECT password_hash FROM Admins WHERE username = \"admin\"'); 
hash = cur.fetchone()['password_hash']; 
print('Valid:', bcrypt.checkpw('admin123'.encode('utf-8'), hash.encode('utf-8')))"
```

### Troubleshooting Admin Login

**Can't login:**
```bash
# Check if admin exists
sqlite3 building_rez.db "SELECT * FROM Admins WHERE username = 'admin';"

# Verify hash format (should start with $2b$12$)
sqlite3 building_rez.db "SELECT password_hash FROM Admins WHERE username = 'admin';"

# Regenerate and update
python generate_admin_hash.py
# Then UPDATE as shown above
```

**Table missing:**
```bash
# Check if Admins table exists
sqlite3 building_rez.db ".tables"

# If missing, delete DB and restart app
rm building_rez.db
python app.py
```

## JavaScript Architecture

All JavaScript has been refactored from inline scripts into external files following best practices.

### File Structure

```
static/
└── js/
    └── app.js  # All JavaScript (220+ lines)
        ├── General initialization (tooltips, alerts, forms)
        └── Index page functions (search, reservation)
```

### Key Functions

**Index Page Functions:**
- `initializeIndexPage()` - Main initialization for search page
- `validateTimeRange()` - Validates start/end time selection
- `loadBuildings()` - Fetches and populates building dropdown
- `loadFloors(buildingId)` - Dynamically loads floors based on building
- `searchRooms()` - Performs room search with loading state
- `displaySearchResults(rooms, searchData)` - Renders search results
- `showReservationModal()` - Opens reservation modal with 12-hour time format
- `submitReservation()` - Handles reservation submission with validation

### 12-Hour Time Format

The application converts military (24-hour) time to standard (12-hour) format throughout:

**Backend (Jinja2 Filters):**
```python
# In app.py
@app.template_filter('hour_to_12hr')
def hour_to_12hr_filter(hour):
    # Converts 7-16 to "7 AM" - "4 PM"
    
@app.template_filter('time_range_12hr')
def time_range_12hr_filter(start_hour):
    # Converts start hour to "7 AM - 8 AM" format
```

**Frontend (JavaScript):**
```javascript
// In app.js
function convertTo12Hour(hour) {
    const period = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour > 12 ? hour - 12 : (hour === 0 ? 12 : hour);
    return `${displayHour} ${period}`;
}
```

### Benefits of Refactoring

✅ **Separation of Concerns**: HTML, CSS, and JavaScript in proper files  
✅ **Browser Caching**: `app.js` cached for faster subsequent loads  
✅ **Code Reusability**: Functions available across all pages  
✅ **Better Development**: Syntax highlighting, linting, debugging support  
✅ **Maintainability**: Changes to JavaScript don't require touching HTML  
✅ **Clean Templates**: `index.html` reduced from 367 to 139 lines

## API Endpoints

### Client Endpoints
- `GET /` - Client search interface
- `GET /search` - Search available rooms (query params: date, building_id, floor, start_hour, end_hour)
- `GET /buildings` - List all buildings
- `GET /floors/<building_id>` - Get floors for a building
- `POST /reserve` - Submit reservation request

### Admin Endpoints
- `GET /admin/login` - Admin login page
- `POST /admin/login` - Process admin login
- `GET /admin/logout` - Admin logout
- `GET /admin` - Admin dashboard
- `GET /admin/reservations` - View all reservations
- `POST /admin/approve/<id>` - Approve reservation
- `POST /admin/reject/<id>` - Reject reservation
- `GET /admin/buildings` - View all buildings
- `GET /admin/rooms` - View all rooms
- `GET /admin/room/<id>/schedule` - View room schedule

## Security Features

The application includes several security features:

1. **Bcrypt Password Hashing**
   - Cost factor: 12 (2^12 = 4096 rounds)
   - Automatic salt generation
   - Timing-attack resistant

2. **Session Management**
   - Secure session cookies
   - Admin ID and username tracking
   - Proper logout handling

3. **Environment-Based Secrets**
   - No hardcoded credentials in code
   - Secret key from environment variables
   - Auto-detection of Azure environment

## Security Checklist (Production)

Before deploying to production, complete these steps:

- [ ] **Change default admin credentials** (username: admin, password: admin123)
- [ ] **Enable App Service Authentication (Entra ID)** for perimeter access control
- [ ] **Generate strong SECRET_KEY** and set in Azure App Settings
- [ ] **Enable HTTPS** (automatic with Azure App Service custom domains)
- [ ] **Configure custom domain** (optional, includes free SSL)
- [ ] **Enable Application Insights** for monitoring
- [ ] **Set up automated backups** for database
- [ ] **Configure auto-scaling** if needed
- [ ] **Review and test** all critical user flows
- [ ] **Implement rate limiting** (via Azure Front Door or API Management)

**📖 Complete checklist:** [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md)

## Business Rules

- **Weekdays Only**: Reservations limited to Monday-Friday (validated client and server-side)
- **Business Hours**: 7:00 AM - 5:00 PM (slot_hour values 7-16)
- **Admin Approval**: All reservations start as "pending" and require admin approval
- **No Double Booking**: UNIQUE constraint prevents duplicate room/date/time combinations
- **Time Ranges**: Reservations are hourly slots; time ranges specify start and end hours

## Development Tips

### Database Management

```bash
# View database schema
sqlite3 building_rez.db ".schema"

# View all tables
sqlite3 building_rez.db ".tables"

# Query data
sqlite3 building_rez.db "SELECT * FROM Reservations WHERE status = 'pending';"

# Reset database (delete and restart app)
rm building_rez.db
python app.py
```

### Modifying Seed Data

Edit `seed.sql` with your buildings, rooms, and sample reservations, then reset the database:

```bash
rm building_rez.db
python app.py
```

### Testing

```bash
# Test authentication
python test_auth.py

# Manual API testing
curl http://localhost:8000/buildings
curl http://localhost:8000/search?date=2024-01-15&building_id=1

# Check logs
# Logs appear in terminal when running app.py
```

### Debugging

```bash
# Enable debug mode
export FLASK_DEBUG=true
python app.py

# View SQL queries (add to app.py temporarily)
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

## Project Structure

```
building-rez/
├── .github/
│   └── workflows/
│       └── azure-deploy.yml        # GitHub Actions CI/CD pipeline
├── app.py                          # Main Flask application
├── schema.sql                      # SQLite database schema
├── seed.sql                        # Seed data with default admin and recurring reservations
├── requirements.txt                # Python dependencies
├── .deployment                     # Azure deployment configuration
├── generate_admin_hash.py          # Admin password hash generator
├── test_auth.py                    # Authentication test suite
├── README.md                        # This file
├── AZURE_DEPLOYMENT.md             # Complete Azure deployment guide
├── AZURE_MIGRATION_SUMMARY.md      # Migration details and benefits
├── AZURE_QUICK_REFERENCE.md        # Quick command reference
├── building_rez.db                 # SQLite database (created on first run, local only)
├── static/
│   ├── css/
│   │   └── style.css               # Custom styles (sage green theme)
│   └── js/
│       └── app.js                  # All JavaScript (externalized)
└── templates/
    ├── base.html                   # Base template with navigation
    ├── index.html                  # Client search interface
    └── admin/
        ├── login.html              # Admin login page
        ├── dashboard.html          # Admin dashboard
        ├── reservations.html       # Reservation management
        ├── buildings.html          # Building list
        ├── rooms.html              # Room list
        └── room_schedule.html      # Room schedule calendar
```

## Deployment Files

- **`.github/workflows/azure-deploy.yml`**: Automated deployment pipeline (Oryx build enabled)
- **`.deployment`**: Azure build configuration marker for App Service

## UI Theme

The application uses a custom sage green theme:

- **Primary Color**: Sage green (#8b9f6d)
- **Navigation Links**: Light sage (#e8f0dc)
- **Pending Badge**: Vibrant orange (#ff6b35)
- **Approved Badge**: Success green (Bootstrap default)
- **Rejected Badge**: Danger red (Bootstrap default)

Theme is defined in `static/css/style.css` and can be customized.

## Recurring Reservations & Rolling Calendar

### Current Implementation

The seed data (`seed.sql`) creates a **rolling 8-week (2 month) recurring reservation pattern**:

- Same reservations repeat every week (e.g., "Weekly: John Doe" has Room 1 every Monday 8-9 AM)
- Pattern extends 8 weeks from when the database is initialized
- Allows staff to schedule up to 2 months in advance
- Different patterns for each weekday (Monday-Friday)
- Admins can create or retire additional weekly series from the <code>Recurring</code> tab in the admin console

### Production TODO: Automated Rolling Window Maintenance

⚠️ **IMPORTANT FOR PRODUCTION DEPLOYMENT (Azure)**

To maintain a true "rolling" 2-month window, you need to implement a scheduled maintenance job that runs daily/weekly:

**What the job should do:**
1. **Delete expired reservations** - Remove reservations older than today
2. **Extend the window** - Add new recurring reservations to maintain the 2-month horizon
3. **Preserve user reservations** - Only manage the "Weekly: [name]" pattern reservations, not user-submitted ones

**Implementation Options:**

**Option 1: Azure Functions (Recommended for Azure App Service)**
```python
# maintenance_job.py - Azure Function (Timer Trigger)
import sqlite3
from datetime import date, timedelta

def extend_recurring_pattern():
    conn = sqlite3.connect('building_rez.db')
    cur = conn.cursor()
    
    # Delete old pattern reservations (older than today)
    cur.execute("""
        DELETE FROM Reservations 
        WHERE reserved_by LIKE 'Weekly:%' 
        AND slot_date < date('now')
    """)
    
    # Find the latest date in current pattern
    cur.execute("""
        SELECT MAX(slot_date) FROM Reservations 
        WHERE reserved_by LIKE 'Weekly:%'
    """)
    max_date = cur.fetchone()[0]
    
    # Calculate how many weeks to add to reach 8 weeks from today
    # ... (implement logic to add missing weeks)
    
    conn.commit()
    conn.close()
```

**Option 2: Azure Logic Apps**
- Schedule: Daily at 2 AM
- Action: HTTP POST to `/admin/maintenance` endpoint (create new endpoint)
- Endpoint implements the cleanup and extension logic

**Option 3: Azure WebJobs**
- Upload maintenance script as a WebJob
- Schedule: CRON expression (e.g., `0 0 2 * * *` for 2 AM daily)
- Script connects to database and performs cleanup

**Setup Steps for Azure:**
1. Create the maintenance script/function
2. Configure to access database at `/home/building_rez.db`
3. Set up Azure Function Timer Trigger or WebJob with CRON schedule
4. Test in deployment slot first
5. Monitor logs to ensure it runs successfully

**Reference Documentation:**
- [Azure Functions Timer Trigger](https://docs.microsoft.com/azure/azure-functions/functions-bindings-timer)
- [Azure WebJobs](https://docs.microsoft.com/azure/app-service/webjobs-create)
- [Azure Logic Apps Schedule Trigger](https://docs.microsoft.com/azure/logic-apps/concepts-schedule-automated-recurring-tasks-workflows)

## Monitoring and Logging

### Azure Application Insights

Enable Application Insights for comprehensive monitoring:

- Request rates and response times
- Failed requests and exceptions  
- Dependency tracking (database calls)
- Custom metrics and events
- User flow analytics

**Setup:** Azure Portal → Your App Service → Application Insights → Turn on

### Application Logs

View logs in real-time:

```bash
# Azure CLI
az webapp log tail --name building-rez-app --resource-group building-rez-rg

# Or via Azure Portal
# App Service → Log stream
```

## Future Enhancements

Potential improvements for future versions:

- 📧 **Email Notifications**: Notify users when reservations are approved/rejected
- 👥 **User Accounts**: Allow users to create accounts and view their reservation history
- 📅 **Recurring Reservations**: Support weekly/monthly recurring bookings
- 🔍 **Advanced Search**: Filter by capacity, accessibility, equipment
- 📊 **Analytics Dashboard**: Usage statistics, popular rooms, peak times
- 📱 **Mobile App**: Native iOS/Android apps using the existing API
- 🔌 **Equipment Tracking**: Add room equipment/amenity metadata
- 📥 **Calendar Export**: ICS file export for calendar integration
- 🔔 **SMS Notifications**: Text message alerts for reservation updates
- 💳 **Payment Integration**: Charge for room reservations
- 🌐 **Multi-language**: Internationalization support
- 🔄 **Deployment Slots**: Use Azure staging slots for zero-downtime deployments

## Support and Resources

### Documentation
- **Azure Deployment**: [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md)
- **GitHub Actions Workflow**: `.github/workflows/azure-deploy.yml`
- **API Endpoints**: See "API Endpoints" section above

### Useful Commands

```bash
# Local development
python app.py

# Deploy to Azure (automatic via GitHub Actions)
git push origin main

# View Azure logs
az webapp log tail --name building-rez-app --resource-group building-rez-rg

# SSH into Azure App Service
az webapp ssh --name building-rez-app --resource-group building-rez-rg

# Restart Azure App Service
az webapp restart --name building-rez-app --resource-group building-rez-rg
```

### Troubleshooting

See [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md) for detailed troubleshooting steps.

Common issues:
- **Database not found**: Check that `/home` directory is writable
- **SECRET_KEY error**: Set SECRET_KEY in Azure App Settings
- **Application won't start**: Check logs via Azure Portal or CLI

---

**Built with Flask, SQLite, and Bootstrap**  
**Deployed on Azure App Service**  
**CI/CD via GitHub Actions**

For deployment questions, see [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md)
