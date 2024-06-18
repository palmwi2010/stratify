import sqlite3
from sqlite3 import Error
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
DB_PATH = os.getenv('DB_PATH')


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

    
    def create_user_table(self):
        """Create users table"""

        if not self.table_exists("users"):
            self.execute("""CREATE TABLE users (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                username TEXT NOT NULL UNIQUE,
                                email TEXT NOT NULL UNIQUE,
                                password_hash TEXT NOT NULL,
                                access_key TEXT,
                                refresh_key TEXT,
                                key_expires INT);""")
    # Initialization of activities
    def create_activity_table(self):
        """Create activities table"""

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
        if not self.table_exists("activities"):
            self.execute(f"CREATE TABLE activities ({field_definitions});")


def db_init():
    """Script to initialize activity and user tables"""

    # Initialize connection and create table if they don't exist already
    db = SQL(DB_PATH)
    db.create_user_table()
    db.create_activity_table()


def db_execute(path, query, params = ()):
    """Script to communicate with SQL database"""

    # Establish connection
    with sqlite3.connect(path) as conn:

        # Open cursor
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # Execute query
            cursor.execute(query, params)
            
            # Check if it is a SELECT
            results = None
            if query.strip().lower().startswith("select"):
                results = [dict(row) for row in cursor.fetchall()]
            else:
                conn.commit()
        except sqlite3.Error as e:
            print(f"An error reading db occurred: {e}")
            raise e
        
        # Close the connection
        cursor.close()

        return results