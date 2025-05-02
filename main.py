from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, validator # Keep validator if you uncomment the example
from datetime import datetime, timezone
from fastapi.middleware.cors import CORSMiddleware # Import CORS

# Import your custom modules
try:
    from ai_reply import generate_human_like_reply
    # Import the new function and MongoClient for closing connection cleanly
    from database import (
        save_reply,
        get_all_replies,
        db as mongo_db,
        client as mongo_client, # Import client
        connect_to_db as try_connect_db
    )
except ImportError as e:
    print(f"Error importing modules: {e}. Make sure ai_reply.py and database.py are present.")
    exit()

# Initialize FastAPI app
app = FastAPI(
    title="Social Media Reply Generator API",
    description="Generates human-like replies to social media posts using Gemini and stores interactions in MongoDB.",
    version="1.0.0",
)

# --- CORS Configuration ---
# Allow requests from your Streamlit frontend (typically runs on port 8501)
# Adjust origins if your frontend runs elsewhere
origins = [
    "http://localhost",
    "http://localhost:8501", # Default Streamlit port
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allow all methods (GET, POST, etc.)
    allow_headers=["*"], # Allow all headers
)

# --- Pydantic Models (keep as before) ---
class PostRequest(BaseModel):
    platform: str = Field(..., examples=["Twitter", "LinkedIn", "Instagram"], description="The source social media platform.")
    post_text: str = Field(..., min_length=5, examples=["Just launched my new project!", "What are your thoughts on the future of AI?"], description="The text content of the original post.")

class ReplyResponse(BaseModel):
    platform: str
    post_text: str
    generated_reply: str
    timestamp: datetime # This expects a datetime object

# Model for returning list of replies (adjust if needed based on get_all_replies output)
# Using dict here for simplicity as json_util handles serialization
class ReplyListResponse(BaseModel):
    replies: list[dict]


# --- API Endpoints ---

@app.on_event("startup")
async def startup_db_client():
    if not try_connect_db():
        print("Warning: Failed to connect to MongoDB on startup.")

@app.on_event("shutdown")
async def shutdown_db_client():
    # Cleanly close DB connection on shutdown
    if mongo_client:
        mongo_client.close()
        print("MongoDB connection closed.")

# --- NEW ENDPOINT TO GET REPLIES ---
@app.get(
    "/replies",
    # response_model=ReplyListResponse, # Using dict, so skip strict model for now
    tags=["Social Replies"],
    summary="Get all stored post-reply interactions",
    description="Retrieves all saved post-reply pairs from the database, sorted by newest first."
)
async def get_replies_endpoint():
    try:
        all_replies = get_all_replies()
        # json_util in get_all_replies already made this JSON serializable
        return {"replies": all_replies}
    except Exception as e:
        print(f"Error in /replies endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch replies from database."
        )

# --- EXISTING /reply ENDPOINT (keep as before) ---
@app.post(
    "/reply",
    response_model=ReplyResponse, # Keep this strict model
    status_code=status.HTTP_201_CREATED,
    tags=["Social Replies"],
    summary="Generate and store a social media reply",
    description="Receives a platform and post text, generates a human-like reply using Gemini, stores the interaction in MongoDB, and returns the result."
)
async def create_reply_endpoint(request: PostRequest):
    platform = request.platform
    post_text = request.post_text
    print(f"Received request for platform: {platform}, post: '{post_text[:50]}...'")

    try:
        generated_reply = generate_human_like_reply(platform, post_text)
        if "Error:" in generated_reply or "Oops," in generated_reply or "Couldn't generate" in generated_reply:
            print(f"AI module indicated failure: {generated_reply}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"AI service failed to generate reply: {generated_reply}"
            )
    except Exception as e:
        print(f"Unexpected error during AI generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error during AI reply generation."
        )

    print(f"Generated reply: '{generated_reply[:50]}...'")
    current_timestamp = datetime.now(timezone.utc) # Use timezone-aware

    try:
        saved_successfully = save_reply(
            platform=platform,
            post_text=post_text,
            generated_reply=generated_reply
        )
        if not saved_successfully:
            print(f"Warning: Failed to save interaction to database for post: '{post_text[:50]}...'")
    except Exception as e:
        print(f"Unexpected error during database save: {e}")
        pass

    # Return response using the strict Pydantic model
    response_data = ReplyResponse(
        platform=platform,
        post_text=post_text,
        generated_reply=generated_reply,
        timestamp=current_timestamp # Pass the generated datetime object
    )
    return response_data


# --- EXISTING /health ENDPOINT (keep as before) ---
@app.get(
    "/health",
    tags=["Health"],
    summary="Check API health",
    description="Returns the status of the API and its database connection."
)
async def health_check():
    api_status = "ok"
    db_status = "disconnected"
    if mongo_db:
        try:
            mongo_db.client.admin.command('ping')
            db_status = "connected"
        except Exception:
            db_status = "disconnected (ping failed)"
    return {"api_status": api_status, "database_status": db_status}


# --- Run the App (keep as before) ---
if __name__ == "__main__":
    import uvicorn
    print("Starting FastAPI server using Uvicorn...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)