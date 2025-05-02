# Human-like Social Media Reply Generator

## Overview

This project implements a system designed to generate authentic, human-like replies to social media posts using generative AI. It features a REST API backend built with FastAPI, utilizes the Google Gemini API for reply generation, stores post-reply interactions in MongoDB Atlas, and includes an optional simple web frontend built with Streamlit.

This project was developed as part of a technical assignment.

## Features

* **AI-Powered Replies:** Generates context-aware, human-like replies using Google Gemini.
* **Platform Awareness:** Attempts to match the tone and style suitable for different platforms (e.g., Twitter, LinkedIn).
* **FastAPI Backend:** Provides a robust REST API (`/reply`) to generate and store replies.
* **MongoDB Integration:** Stores original posts, generated replies, platform info, and timestamps in MongoDB Atlas.
* **Async Operations:** Leverages FastAPI's asynchronous capabilities.
* **(Optional) Streamlit Frontend:** A simple web UI (`frontend.py`) to interact with the API visually (generate new replies, view history).
* **Environment Variable Configuration:** Securely manages API keys and connection strings via a `.env` file.

## Architecture

The system consists of the following components:

1.  **FastAPI Backend (`main.py`):** Handles incoming API requests, orchestrates the workflow, manages database interactions, and serves responses. Uses Uvicorn as the ASGI server.
2.  **AI Reply Module (`ai_reply.py`):** Interfaces with the Google Gemini API, including prompt construction and handling the generation process.
3.  **Database Module (`database.py`):** Manages the connection to MongoDB Atlas and provides functions for saving and retrieving reply data using PyMongo.
4.  **Streamlit Frontend (`frontend.py`) (Optional):** Provides a user interface using Streamlit, communicating with the FastAPI backend via HTTP requests (using the `requests` library).
5.  **Configuration (`.env`):** Stores sensitive keys (Gemini API Key, MongoDB Connection String).
6.  **Dependencies (`requirements.txt`):** Lists all necessary Python packages.

## Project Structure

social-reply-generator/├── venv/                  # Virtual environment (ignored by Git)├── .env                   # Environment variables (API Keys, DB URI - DO NOT COMMIT)├── .gitignore             # Specifies intentionally untracked files that Git should ignore├── ai_reply.py            # Handles AI interaction (Gemini)├── database.py            # Handles MongoDB connection and operations├── main.py                # FastAPI application definition and endpoints├── frontend.py            # (Optional) Streamlit frontend application├── test_api.py            # (Optional) Script to test the API using posts.xlsx├── posts.xlsx             # (Optional) Sample data provided with the assignment├── requirements.txt       # Project dependencies└── README.md              # This file
## Setup and Installation

Follow these steps to set up and run the project locally.

**Prerequisites:**

* Python 3.8 or higher
* Git
* Access to Google AI Studio (for Gemini API Key)
* Access to MongoDB Atlas (for Connection String)

**Steps:**

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/social-reply-generator.git](https://github.com/YOUR_USERNAME/social-reply-generator.git)
    cd social-reply-generator
    ```
    *(Replace `YOUR_USERNAME` with your actual GitHub username)*

2.  **Create and Activate Virtual Environment:**
    * **Windows (Command Prompt):**
        ```bash
        python -m venv venv
        venv\Scripts\activate
        ```
    * **Windows (PowerShell):**
        ```bash
        python -m venv venv
        .\venv\Scripts\Activate.ps1
        ```
    * **macOS / Linux (Bash):**
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Create Environment Variables File (`.env`):**
    * Create a file named `.env` in the root directory (`social-reply-generator/`).
    * Add the following lines, replacing the placeholder values with your actual credentials:

        ```dotenv
        GEMINI_API_KEY=YOUR_GOOGLE_GEMINI_API_KEY_HERE
        MONGO_DB_CONNECTION_STRING=mongodb+srv://YOUR_USERNAME:YOUR_PASSWORD@YOUR_CLUSTER_ADDRESS...
        ```
    * **`GEMINI_API_KEY`**: Obtain this key from [Google AI Studio](https://aistudio.google.com/).
    * **`MONGO_DB_CONNECTION_STRING`**: Obtain this from your MongoDB Atlas cluster (ensure the username/password in the string are correct and Network Access is configured, e.g., allowing `0.0.0.0/0` for development).

## Running the Application

You need to run the backend and frontend separately (if using the frontend).

1.  **Run the FastAPI Backend:**
    * Open a terminal, navigate to the project directory, and ensure your virtual environment is active.
    * Run the Uvicorn server:
        ```bash
        uvicorn main:app --reload --host 127.0.0.1 --port 8000
        ```
    * The API will be running at `http://127.0.0.1:8000`.

2.  **Run the Streamlit Frontend (Optional):**
    * Open a **second** terminal, navigate to the project directory, and ensure your virtual environment is active.
    * Run the Streamlit app:
        ```bash
        streamlit run frontend.py
        ```
    * Streamlit will typically open the app in your browser at `http://localhost:8501`.

## API Usage

The main API endpoint is `/reply`. You can interact with it using the automatically generated documentation or tools like `curl`.

**Interactive Documentation (Swagger UI):**

* While the backend server is running, open your browser and navigate to: `http://127.0.0.1:8000/docs`

**Example Request (`curl`):**

```bash
curl -X 'POST' \
  '[http://127.0.0.1:8000/reply](http://127.0.0.1:8000/reply)' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "platform": "LinkedIn",
  "post_text": "What are the key challenges in scaling AI projects?"
}'
Example Success Response (201 Created):{
  "platform": "LinkedIn",
  "post_text": "What are the key challenges in scaling AI projects?",
  "generated_reply": "Great question! From my experience, data quality/availability and managing stakeholder expectations are often the biggest hurdles. Finding the right talent can also be tricky. What have you seen?",
  "timestamp": "2025-05-02T10:30:00.123456Z"
}
Other Endpoints:GET /health: Checks the status of the API and database connection. Returns {"api_status": "ok", "database_status": "connected"} or "disconnected".GET /replies: Retrieves all previously saved post-reply interactions from the database (used by the frontend).Human-like Reply StrategyThe goal was to generate replies that feel authentic and avoid common AI patterns. The strategy implemented in ai_reply.py involves:Model Choice: Google Gemini (gemini-1.5-flash-latest) was selected for its strong natural language capabilities and accessible free tier, overcoming initial quota issues with OpenAI.Prompt Engineering: Instead of simple templates, a detailed prompt guides the LLM:Persona: Instructs the AI to "Act as a social media user".Context Analysis: Explicitly asks the AI to analyze the input platform and post_text.Tone and Style: Provides guidelines to use informal language, contractions, and match the typical style of the target platform (e.g., short/quippy for Twitter, professional/conversational for LinkedIn).Avoiding AI Giveaways: Explicitly forbids common AI phrases ("As an AI...", "It's great that..."), generic statements ("Great post!"), excessive formality, and instructs it to be concise.Relevance: Guides the AI to react appropriately based on the post's likely intent (question, opinion, news).Output Format: Instructs the AI to generate only the reply text.Safety Settings: Basic safety filters are configured in the Gemini API call to block potentially harmful content generation.This multi-faceted prompt aims to constrain the LLM's output towards more natural, platform-appropriate, and less robotic responses. Further refinement could involve more complex prompt chaining (e.g., separate analysis step) or fine-tuning models if needed.Database SchemaInteractions are stored in MongoDB Atlas in the social_reply_db database and replies collection with the following schema:platform (String): The source platform (e.g., "Twitter", "LinkedIn").post_text (String): The original content of the post.generated_reply (String): The reply generated by the AI.timestamp (ISODate): The UTC timestamp when the reply was generated/saved.Architecture Decisions & Trade-offsFastAPI: Chosen for its high performance, asynchronous support (suitable for I/O-bound tasks like API calls and DB interactions), automatic data validation with Pydantic, and excellent automatic API documentation (Swagger UI).Google Gemini: Selected as the LLM due to its strong performance, multimodal capabilities (though only text used here), and accessible free tier, overcoming initial quota issues with OpenAI.MongoDB Atlas: Used for its flexible NoSQL document structure (good for evolving data), ease of setup with the free tier, and good integration with Python via PyMongo. It automatically creates the database and collection on first write.Streamlit (for Frontend): Chosen for rapid UI development purely in Python, avoiding the need for separate JavaScript framework setup, making it easy to visualize results quickly. Trade-off is less UI customization compared to frameworks like React/Vue..env for Configuration: Standard practice for managing sensitive credentials securely without hardcoding them. python-dotenv used for loading.Future ImprovementsMore sophisticated prompt chaining (e.g., separate calls for sentiment/intent analysis).Enhanced error handling and logging.Implementing user feedback loop to improve replies.Adding more robust testing (unit,
