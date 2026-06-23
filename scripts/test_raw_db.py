import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
db_url = os.getenv("NEON_DATABASE_URL")

print("Attempting to connect to Neon directly...")
try:
    # Connect directly using the psycopg2 driver
    conn = psycopg2.connect(db_url)
    print("SUCCESS! Connected to the database using psycopg2.")
    
    # Open a cursor and test a basic query
    cur = conn.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
    tables = cur.fetchall()
    print("Tables found in database:", [t[0] for t in tables])
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"FAILED to connect. Error details: {e}")