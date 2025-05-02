import pandas as pd
import requests
import time
import json # Import json for pretty printing errors

# Configuration
API_URL = "http://127.0.0.1:8000/reply" # Your running FastAPI endpoint
EXCEL_FILE = "posts.xlsx" # Assumes the file is in the same directory
RETRY_DELAY_SECONDS = 2 # Wait time if API fails before potentially retrying (or just moving on)
REQUEST_DELAY_SECONDS = 1 # Wait time between requests to be nice to the API/LLM limits

def test_api_with_excel(api_url: str, excel_path: str):
    """
    Reads posts from an Excel file and sends requests to the /reply API endpoint.
    """
    print(f"Reading data from: {excel_path}")
    try:
        # Read the Excel file
        df = pd.read_excel(excel_path)
        # Ensure required columns are present
        if 'platform' not in df.columns or 'post_text' not in df.columns:
            print(f"Error: Excel file must contain 'platform' and 'post_text' columns.")
            return
        print(f"Found {len(df)} posts to test.")

    except FileNotFoundError:
        print(f"Error: Excel file not found at '{excel_path}'. Make sure it's in the correct directory.")
        return
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return

    results = []
    for index, row in df.iterrows():
        platform = row['platform']
        post_text = row['post_text']

        # Basic validation
        if pd.isna(platform) or pd.isna(post_text) or not post_text.strip():
            print(f"Skipping row {index + 2}: Invalid platform or empty post_text.")
            continue

        payload = {
            "platform": platform,
            "post_text": post_text
        }

        print(f"\n--- Sending Post {index + 1}/{len(df)} ---")
        print(f"Platform: {platform}")
        print(f"Post Text: {post_text[:100]}...") # Print truncated post

        try:
            response = requests.post(api_url, json=payload, timeout=60) # Add timeout

            # Check response status code
            if response.status_code == 201: # Status code for successful creation
                response_data = response.json()
                print(f"Success (201): Reply -> '{response_data.get('generated_reply', 'N/A')[:100]}...'")
                results.append({"status": "success", "input": payload, "output": response_data})
            else:
                # Handle API errors (like 5xx, 4xx)
                print(f"Failed ({response.status_code}): {response.text}")
                results.append({"status": "failed", "input": payload, "error": response.text, "code": response.status_code})
                time.sleep(RETRY_DELAY_SECONDS) # Wait a bit after an error

        except requests.exceptions.RequestException as e:
            # Handle connection errors, timeouts, etc.
            print(f"Request Error: Failed to connect to API at {api_url}. Is the server running? Details: {e}")
            results.append({"status": "error", "input": payload, "error": str(e)})
            # Optional: break the loop if connection fails repeatedly
            # break
            time.sleep(RETRY_DELAY_SECONDS) # Wait a bit after an error
        except Exception as e:
            # Catch any other unexpected errors during the request/response cycle
            print(f"Unexpected Error during request for row {index + 2}: {e}")
            results.append({"status": "error", "input": payload, "error": str(e)})
            time.sleep(RETRY_DELAY_SECONDS)

        # Add a small delay between requests
        print(f"Waiting {REQUEST_DELAY_SECONDS}s...")
        time.sleep(REQUEST_DELAY_SECONDS)

    print("\n--- Test Summary ---")
    success_count = sum(1 for r in results if r["status"] == "success")
    failed_count = sum(1 for r in results if r["status"] == "failed")
    error_count = sum(1 for r in results if r["status"] == "error")
    print(f"Total Posts Processed: {len(results)}")
    print(f"Successful Replies: {success_count}")
    print(f"Failed API Calls (Server Error): {failed_count}")
    print(f"Request Errors (Connection/Other): {error_count}")

    # Optional: Save results summary to a file
    # with open("test_results.json", "w") as f:
    #     json.dump(results, f, indent=2)
    # print("Detailed results saved to test_results.json")

if __name__ == "__main__":
    test_api_with_excel(API_URL, EXCEL_FILE)