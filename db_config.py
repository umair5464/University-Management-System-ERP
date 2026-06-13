import mysql.connector
from mysql.connector import Error

def get_db_connection():
    """Establishes and returns a connection to the MySQL database."""
    try:
        connection = mysql.connector.connect(
            host='localhost',          # Usually 'localhost' if running on your own machine (XAMPP/WAMP)
            user='root',               # Default MySQL username is usually 'root'
            password='1234',  # Enter your MySQL password here (leave blank '' if using default XAMPP)
            database='ums'    # The exact name of your database
        )
        
        if connection.is_connected():
            return connection
            
    except Error as e:
        print(f"❌ Error connecting to MySQL: {e}")
        return None

# --- Quick Test ---
# If you run this file directly, it will test the connection.
if __name__ == "__main__":
    conn = get_db_connection()
    if conn:
        print("✅ Success! Python is securely connected to your MySQL Database.")
        conn.close()