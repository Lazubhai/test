import pyodbc
from config import config

class DatabaseHandler:
    def __init__(self, telegram_id):
        self.telegram_id = int(telegram_id)
        
        self.conn_global = pyodbc.connect(
            f"DRIVER={{SQL Server}};"
            f"SERVER={config['sql_server']};"
            f"DATABASE={config['global_db']};"
            f"Trusted_Connection=yes;"
        )
        cursor = self.conn_global.cursor()
        
        cursor.execute("SELECT SHAUsername FROM TelegramUsers WHERE TelegramID = ?", (self.telegram_id,))
        row = cursor.fetchone()
        if row is None:
            print(f"DEBUG: No user found with TelegramID {self.telegram_id}")
            raise Exception("User not registered in Smart Habit Analyzer app.")
        self.sha_username = row[0]
        print(f"DEBUG: Found SHAUsername '{self.sha_username}' for TelegramID {self.telegram_id}")
        
        user_db_name = f"HabitTracker_{self.sha_username}"
        self.conn_user = pyodbc.connect(
            f"DRIVER={{SQL Server}};"
            f"SERVER={config['sql_server']};"
            f"DATABASE={user_db_name};"
            f"Trusted_Connection=yes;"
        )
        self.cursor_user = self.conn_user.cursor()
        
    def get_habits(self):
        self.cursor_user.execute("SELECT HabitID, [Name] FROM Habits")
        return self.cursor_user.fetchall()
    
    def get_routines_for_habit(self, habit_id):
        self.cursor_user.execute(
            "SELECT RoutineID, RoutineName FROM Routines WHERE HabitID = ?", (habit_id,)
        )
        return self.cursor_user.fetchall()
    
    def get_habit_cue(self, habit_id):
        self.cursor_user.execute(
            "SELECT Cue FROM Habits WHERE HabitID = ?", (habit_id,)
        )
        row = self.cursor_user.fetchone()
        return row[0] if row else None
    
    def insert_habit_log(self, habit_id, cue_status, reward_status, crave_points):
        # Insert HabitLog (LogDate is auto-generated)
        self.cursor_user.execute(
            "INSERT INTO HabitLogs (HabitID, CueStatus, RewardStatus, CravePoints) VALUES (?, ?, ?, ?)",
            (habit_id, cue_status, reward_status, crave_points)
        )
        self.conn_user.commit()
        self.cursor_user.execute("SELECT SCOPE_IDENTITY()")
        log_id = self.cursor_user.fetchone()[0]
        return log_id
    
    def insert_routine_log(self, log_id, routine_id, is_completed):
        self.cursor_user.execute(
            "INSERT INTO RoutineLogs (LogID, RoutineID, IsCompleted) VALUES (?, ?, ?)",
            (log_id, routine_id, is_completed)
        )
        self.conn_user.commit()
    
    def close_connections(self):
        self.cursor_user.close()
        self.conn_user.close()
        self.conn_global.close()
