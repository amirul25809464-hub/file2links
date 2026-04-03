import sqlite3
from datetime import date
import os

class Database:
    def __init__(self):
        # This will create a local file named bot_db.sqlite
        self.conn = sqlite3.connect("bot_db.sqlite", check_same_thread=False)
        self.create_table()

    def create_table(self):
        with self.conn:
            # Table for user tracking and advanced limits
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    count INTEGER DEFAULT 0,
                    last_date TEXT,
                    extra_limit INTEGER DEFAULT 0,
                    referred_by INTEGER,
                    total_referrals INTEGER DEFAULT 0,
                    is_joined INTEGER DEFAULT 0
                )
            """)
            # New table for dynamic settings (like ads)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

    def set_setting(self, key, value):
        with self.conn:
            self.conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))

    def get_setting(self, key, default=None):
        with self.conn:
            cursor = self.conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else default

    def add_user(self, user_id):
        today = str(date.today())
        with self.conn:
            cursor = self.conn.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
            if not cursor.fetchone():
                self.conn.execute("INSERT INTO users (user_id, last_date) VALUES (?, ?)", (user_id, today))
                return True
            return False

    def increment_global_stat(self, key, amount=1):
        with self.conn:
            current = int(self.get_setting(key, 0))
            self.set_setting(key, str(current + amount))
            return current + amount

    def get_global_stats(self):
        total_files = int(self.get_setting("total_files", 0))
        total_bytes = int(self.get_setting("total_bytes", 0))
        return total_files, total_bytes

    def check_user(self, user_id, daily_limit):
        today = str(date.today())
        with self.conn:
            cursor = self.conn.execute("SELECT count, last_date, extra_limit FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            
            if not row:
                self.conn.execute("INSERT INTO users (user_id, count, last_date) VALUES (?, 1, ?)", (user_id, today))
                return True, 1, daily_limit, 0 # success, used, total, extra
            
            count, last_date, extra_limit = row
            current_total_limit = daily_limit + extra_limit

            if last_date != today:
                self.conn.execute("UPDATE users SET count = 1, last_date = ? WHERE user_id = ?", (today, user_id))
                return True, 1, current_total_limit, extra_limit
            
            if count >= current_total_limit:
                # Calculate time until midnight
                from datetime import datetime, timedelta
                now = datetime.now()
                tomorrow = datetime.combine(now.date() + timedelta(days=1), datetime.min.time())
                seconds_left = (tomorrow - now).seconds
                hours, remainder = divmod(seconds_left, 3600)
                minutes, _ = divmod(remainder, 60)
                return False, count, current_total_limit, f"{hours}h {minutes}m"
            
            new_count = count + 1
            self.conn.execute("UPDATE users SET count = ? WHERE user_id = ?", (new_count, user_id))
            return True, new_count, current_total_limit, extra_limit

    def add_referral(self, new_user_id, referrer_id):
        with self.conn:
            # Check if user already exists
            cursor = self.conn.execute("SELECT user_id FROM users WHERE user_id = ?", (new_user_id,))
            if cursor.fetchone():
                return False, None # Old user
            
            # Get referrer name/ID for info
            self.conn.execute("INSERT INTO users (user_id, referred_by) VALUES (?, ?)", (new_user_id, referrer_id))
            # Update referrer: +15 bonus limit (as requested)
            self.conn.execute("UPDATE users SET extra_limit = extra_limit + 15, total_referrals = total_referrals + 1 WHERE user_id = ?", (referrer_id,))
            return True, referrer_id

    def get_user_data(self, user_id):
        with self.conn:
            cursor = self.conn.execute("SELECT extra_limit, total_referrals, referred_by, count FROM users WHERE user_id = ?", (user_id,))
            return cursor.fetchone()

    def get_admin_stats(self):
        with self.conn:
            cursor = self.conn.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            cursor = self.conn.execute("SELECT SUM(total_referrals) FROM users")
            total_refs = cursor.fetchone()[0] or 0
            return total_users, total_refs

    def get_all_users(self):
        with self.conn:
            cursor = self.conn.execute("SELECT user_id FROM users")
            return [row[0] for row in cursor.fetchall()]

db = Database()
