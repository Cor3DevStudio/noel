# Installation Guide

## System Requirements

- **OS:** Windows 10/11, macOS 10.15+, or Linux
- **Python:** 3.10 or higher
- **MySQL:** 8.0 or higher
- **RAM:** 4 GB minimum
- **Storage:** 500 MB free space

## Step-by-Step Installation

### 1. Install Python

Download and install Python from [python.org](https://www.python.org/downloads/). Enable "Add Python to PATH" during installation.

Verify:
```bash
python --version
```

### 2. Install MySQL

Download MySQL Community Server from [mysql.com](https://dev.mysql.com/downloads/mysql/).

During installation:
- Set root password (remember this for configuration)
- Enable MySQL as a Windows service

Verify:
```bash
mysql --version
```

### 3. Clone or Extract Project

Place the project folder at your desired location, e.g. `D:\PROJECTS\noel`.

### 4. Create Virtual Environment (Recommended)

```bash
cd D:\PROJECTS\noel
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
```

### 5. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure Database Connection

Open `config/settings.py` and update:

```python
DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWORD = "YOUR_MYSQL_PASSWORD"
DB_NAME = "clinic_management"
```

The `DATABASE_URL` is built automatically from these values.

### 7. Create the Database

**Option A — SQL file:**
```bash
mysql -u root -p < database/schema.sql
```

**Option B — Automatic (on first run):**
The application creates tables automatically via SQLAlchemy when MySQL is reachable.

### 8. Run the Application

```bash
python main.py
```

On first launch:
- Roles are created automatically
- Default admin account is created (`admin` / `admin123`)
- Default PhilHealth case rates are seeded
- Clinic settings record is initialized

### 9. Load Sample Data (Optional)

```bash
python -m database.seed_data
```

This adds sample users, patients, and medicines for testing.

## Troubleshooting

### "Can't connect to MySQL server"
- Ensure MySQL service is running
- Verify host, port, username, and password in `config/settings.py`
- Check firewall settings

### "Access denied for user"
- Confirm MySQL user has privileges: `GRANT ALL ON clinic_management.* TO 'root'@'localhost';`

### "Module not found"
- Activate virtual environment
- Run `pip install -r requirements.txt`

### Backup/Restore not working
- Install MySQL client tools (`mysqldump` and `mysql` must be in PATH)

## Post-Installation

1. Log in as `admin` / `admin123`
2. Go to **Settings → Clinic Info** and enter clinic details
3. Go to **Settings → Users** and create staff accounts
4. Change the default admin password under **Settings → My Account**
