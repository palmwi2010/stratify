import sqlite3
from sqlite3 import Error

class SQL(sqlite3.Connection):
    def __init__(self, path):
        super().__init__(path)

    def execute(self, query, params = (), fetch = False):
        """Execute a sql query"""
        results = None
        try:
            cursor = self.cursor()
            cursor.execute(query, params)
            if fetch:
                results = cursor.fetchall()
            else:
                self.commit()
        except sqlite3.Error as e:
            print(f"An error occured connecting to database: {e}")
        finally:
            cursor.close()
        
        return results

    
    def table_exists(self, table):
        """Check if a table exists in the schema"""
        tables = self.execute("SELECT name FROM sqlite_master WHERE type='table';", fetch=True)
        table_names = [row[0] for row in tables]
        return table in table_names

db = SQL('strava_app.db')

# Create users table if it doesn't exist already
def create_user_table():
    if not db.table_exists("users"):
        db.execute("""CREATE TABLE users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT NOT NULL UNIQUE,
                            email TEXT NOT NULL UNIQUE,
                            password_hash TEXT NOT NULL,
                            access_key TEXT,
                            refresh_key TEXT,
                            key_expires INT);""")

# Initialization of activities
def create_activity_table():

    FIELDS = [('id', "INT PRIMARY KEY"),
    ('athlete_id', 'REAL'),
    ('name', "TEXT"),
    ('distance', "REAL"),
    ('moving_time', "INT"),
    ('elapsed_time', "INT"),
    ('total_elevation_gain', "REAL"),
    ('type', "TEXT"),
    ('achievement_count', "INT"),
    ('kudos_count', 'INT'),
    ('average_speed', 'REAL'),
    ('max_speed', 'REAL'),
    ('average_cadence', 'REAL'), 
    ('average_watts', 'REAL'),
    ('max_watts', 'REAL'),
    ('weighted_average_watts', 'REAL'),
    ('kilojoules', 'REAL'),
    ('device_watts', 'INT'),
    ('has_heartrate', 'INT'),
    ('average_heartrate', 'REAL'),
    ('max_heartrate', 'REAL'),
    ('average_heartrate_sort', 'INT'),
    ('max_heartrate_sort', 'INT'),
    ('elev_high', 'REAL'),
    ('elev_low', 'REAL'),
    ('pr_count', 'INT'),
    ('suffer_score', 'REAL'),
    ('date', 'TEXT'),
    ('date_sort', 'INT'),
    ('time', 'TEXT'),
    ('distance_f', 'TEXT'), 
    ('moving_time_f', 'TEXT'),
    ('pace', 'TEXT'),
    ('start_lat', 'REAL'),
    ('start_lng', 'REAL')]

    field_definitions = ", ".join([f"{name} {data_type}" for name, data_type in FIELDS])
    if not db.table_exists("activities"):
        db.execute(f"CREATE TABLE activities ({field_definitions});")

# Create tables
create_user_table()
#create_activity_table()