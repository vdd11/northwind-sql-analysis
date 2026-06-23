import os
from dotenv import load_dotenv

# Load the .env file explicitly
load_dotenv()

# Retrieve the database URL
db_url = os.getenv("NEON_DATABASE_URL")

if db_url:
    print("Success! Your Neon Database URL is:")
    # Masking the password part just in case, while showing it works
    print(db_url[:10] + "..." + db_url[-10:])
else:
    print("Could not find the database URL. Check your .env file path and settings.")