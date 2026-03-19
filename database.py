import sqlite3
from datetime import datetime
import pickle

class AttendanceDB:
    def __init__(self, db_path='attendance.db'):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS persons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    encoding BLOB NOT NULL,
                    department TEXT,
                    employee_id TEXT
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    person_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    confidence REAL,
                    FOREIGN KEY (person_id) REFERENCES persons (id)
                )
            ''')
            conn.commit()

    def get_all_persons(self):
        with self.get_connection() as conn:
            rows = conn.execute('SELECT * FROM persons').fetchall()
            return [{'id': r['id'], 'name': r['name'], 'encoding': r['encoding'], 
                     'department': r['department'], 'employee_id': r['employee_id']} for r in rows]

    def get_person_by_name(self, name):
        with self.get_connection() as conn:
            row = conn.execute('SELECT * FROM persons WHERE name = ?', (name,)).fetchone()
            if row:
                return {'id': row['id'], 'name': row['name'], 'encoding': row['encoding'], 
                        'department': row['department'], 'employee_id': row['employee_id']}
            return None

    def add_person(self, name, encoding, department, employee_id):
        try:
            with self.get_connection() as conn:
                encoding_bytes = pickle.dumps(encoding)
                conn.execute('''
                    INSERT INTO persons (name, encoding, department, employee_id)
                    VALUES (?, ?, ?, ?)
                ''', (name, encoding_bytes, department, employee_id))
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def mark_attendance(self, person_id, confidence):
        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H:%M:%S')
        
        with self.get_connection() as conn:
            # Check if this person was already marked today
            # Assuming you only want to log their attendance once per day to prevent spam
            existing = conn.execute('''
                SELECT id FROM attendance 
                WHERE person_id = ? AND date = ?
            ''', (person_id, date_str)).fetchone()
            
            if existing:
                return False
                
            conn.execute('''
                INSERT INTO attendance (person_id, date, time, confidence)
                VALUES (?, ?, ?, ?)
            ''', (person_id, date_str, time_str, confidence))
            conn.commit()
            return True

    def get_today_attendance(self):
        date_str = datetime.now().strftime('%Y-%m-%d')
        with self.get_connection() as conn:
            rows = conn.execute('''
                SELECT p.name, p.department, p.employee_id, a.time, a.confidence
                FROM attendance a
                JOIN persons p ON a.person_id = p.id
                WHERE a.date = ?
                ORDER BY a.time DESC
            ''', (date_str,)).fetchall()
            return [tuple(r) for r in rows]

    def get_attendance_report(self, start_date, end_date):
        with self.get_connection() as conn:
            rows = conn.execute('''
                SELECT p.name, p.department, p.employee_id, a.date, a.time, a.confidence
                FROM attendance a
                JOIN persons p ON a.person_id = p.id
                WHERE a.date BETWEEN ? AND ?
                ORDER BY a.date DESC, a.time DESC
            ''', (start_date, end_date)).fetchall()
            return [tuple(r) for r in rows]
