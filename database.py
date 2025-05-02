import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ConfigurationError, OperationFailure
from dotenv import load_dotenv
from datetime import datetime
import sys # Import sys for error printing
from bson import json_util
import json # To parse the json_util output

# Load environment variables (DB connection string), overriding system vars if present
load_dotenv(override=True)
MONGO_URI = os.getenv("MONGO_DB_CONNECTION_STRING")

client: MongoClient | None = None
db = None # Represents the database object

def connect_to_db():
    """Establishes connection to MongoDB Atlas."""
    global client, db
    if client and db: # Already connected
        try:
            client.admin.command('ping') # Check connection health
            return True
        except ConnectionFailure:
            print("Warning: Existing DB connection lost. Attempting to reconnect.", file=sys.stderr)
            client = None
            db = None
            # Fall through to reconnect logic

    if not MONGO_URI:
        print("Error: MONGO_DB_CONNECTION_STRING not found in environment variables or is empty.", file=sys.stderr)
        return False

    print("Attempting to connect to MongoDB Atlas using string from .env...")
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000) # 5 second timeout
        client.admin.command('ping') # Verify connection
        db = client.social_reply_db # Use your desired database name here
        print("Successfully connected to MongoDB Atlas.")
        return True

    except ConfigurationError as e:
        print(f"MongoDB Configuration Error: Check connection string format in .env. Details: {e}", file=sys.stderr)
        client = None
        db = None
        return False
    except ConnectionFailure as e:
        print(f"MongoDB Connection/Auth Failure: Could not connect. Check network access/credentials in .env. Details: {e}", file=sys.stderr)
        client = None
        db = None
        return False
    except Exception as e:
         print(f"An unexpected error occurred during MongoDB connection: {e}", file=sys.stderr)
         client = None
         db = None
         return False
     
def get_all_replies() -> list:
    """Fetches all saved post-reply pairs from the database."""
    global db
    if db is None:
        print("Database not connected. Attempting to reconnect...", file=sys.stderr)
        if not connect_to_db():
             print("Failed to reconnect to database. Cannot fetch replies.", file=sys.stderr)
             return [] # Return empty list on failure

    replies_list = []
    try:
        replies_collection = db.replies
        # Find all documents, sort by timestamp descending (newest first)
        # Add a limit if you expect a huge number of replies, e.g., .limit(100)
        cursor = replies_collection.find().sort("timestamp", -1)

        # Use bson.json_util to handle ObjectId and datetime serialization
        # Convert cursor to list, then dump/parse to get serializable dicts
        replies_list = json.loads(json_util.dumps(list(cursor)))

        print(f"Fetched {len(replies_list)} replies from database.")
        return replies_list
    except Exception as e:
        print(f"Error fetching replies from database: {e}", file=sys.stderr)
        return [] # Return empty list on error

def save_reply(platform: str, post_text: str, generated_reply: str) -> bool:
    """Saves the post-reply pair to the database."""
    global db
    # CORRECTED CHECK: Compare db object directly with None
    if db is None:
        print("Database not connected. Attempting to reconnect...", file=sys.stderr)
        if not connect_to_db():
             print("Failed to reconnect to database. Cannot save reply.", file=sys.stderr)
             return False
        # If connect_to_db succeeded, db will be set

    try:
        replies_collection = db.replies # Collection name
        document = {
            "platform": platform,
            "post_text": post_text,
            "generated_reply": generated_reply,
            "timestamp": datetime.utcnow()
        }
        result = replies_collection.insert_one(document)
        print(f"Successfully saved reply with id: {result.inserted_id}")
        return True
    except OperationFailure as e:
         print(f"MongoDB Operation Failure (e.g., permissions): {e}", file=sys.stderr)
         return False
    except Exception as e:
        print(f"Error saving reply to database: {e}", file=sys.stderr)
        return False

# --- Optional: Simple test block ---
if __name__ == '__main__':
    print("\nTesting Database Connection and Save...")
    if not MONGO_URI:
        print("Skipping DB test: MONGO_DB_CONNECTION_STRING not found or empty in .env.")
    else:
        if connect_to_db():
            print("\nAttempting to save a test reply...")
            saved = save_reply("TestPlatform", "This is a test post.", "This is a test reply.")
            if saved:
                print("Test reply saved successfully.")
            else:
                print("Failed to save test reply.")
            # Clean up connection after test
            if client:
                client.close()
                print("MongoDB connection closed.")
        else:
             print("Failed to connect to MongoDB for testing.")