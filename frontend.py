import streamlit as st
import requests
from datetime import datetime

# Configuration
# Configuration
BACKEND_URL_REPLY = "https://social-reply-generator.onrender.com/reply"
BACKEND_URL_GET_REPLIES = "https://social-reply-generator.onrender.com/replies"

# Helper function to format timestamp from backend (which is likely string via JSON)
def format_timestamp(ts_data):
    if not ts_data:
        return "N/A"
    # Check if timestamp is nested under '$date' (from json_util)
    if isinstance(ts_data, dict) and '$date' in ts_data:
        ts_str = ts_data['$date']
        # Handle different possible MongoDB datetime formats from json_util
        try:
            # Format with milliseconds and Z (UTC)
            dt_obj = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
            return dt_obj.strftime('%Y-%m-%d %H:%M:%S %Z')
        except ValueError:
            try:
                # Format without milliseconds
                 dt_obj = datetime.strptime(ts_str, '%Y-%m-%dT%H:%M:%SZ')
                 return dt_obj.strftime('%Y-%m-%d %H:%M:%S %Z')
            except ValueError:
                return ts_str # Return raw string if parsing fails
    elif isinstance(ts_data, str): # Handle ISO strings directly if not nested
         try:
            dt_obj = datetime.fromisoformat(ts_data.replace('Z', '+00:00'))
            return dt_obj.strftime('%Y-%m-%d %H:%M:%S %Z')
         except ValueError:
              return ts_data
    return str(ts_data) # Fallback

# --- Streamlit App Layout ---

st.set_page_config(layout="wide") # Use wider layout
st.title("🤖 Human-like Social Media Reply Generator")
st.markdown("Enter a social media post and platform, and get an AI-generated reply!")

# --- Section 1: Generate New Reply ---
st.header("Generate a New Reply")

# Use columns for layout
col1, col2 = st.columns([1, 2]) # Platform selector smaller than text area

with col1:
    platform = st.selectbox(
        "Select Platform:",
        ("Twitter", "LinkedIn", "Instagram", "Other"), # Add more if needed
        key="platform_select" # Add unique key
    )

with col2:
    post_text = st.text_area(
        "Enter Post Text:",
        height=100,
        key="post_text_input" # Add unique key
    )

submit_button = st.button("✨ Generate Reply", key="generate_button") # Add unique key

if submit_button:
    if platform and post_text.strip():
        payload = {"platform": platform, "post_text": post_text}
        st.write("Sending request to API...")
        try:
            # Make POST request to the backend /reply endpoint
            response = requests.post(BACKEND_URL_REPLY, json=payload, timeout=60)

            if response.status_code == 201:
                result = response.json()
                st.success("Reply Generated Successfully!")
                st.markdown(f"""
                **Platform:** {result.get('platform')}
                **Original Post:** {result.get('post_text')}
                **Generated Reply:**
                > {result.get('generated_reply')}
                """)
                # We don't display the timestamp from the reply directly here
                # It's mainly for the database record
            else:
                st.error(f"Error from API ({response.status_code}): {response.text}")

        except requests.exceptions.RequestException as e:
            st.error(f"Could not connect to the backend API at {BACKEND_URL_REPLY}. Is it running? Error: {e}")
        except Exception as e:
             st.error(f"An unexpected error occurred: {e}")

    else:
        st.warning("Please select a platform and enter some post text.")

st.divider() # Visual separator

# --- Section 2: View Saved Replies ---
st.header("📜 Previously Generated Replies")

# Add a button to refresh the list
if st.button("🔄 Refresh List", key="refresh_button"): # Add unique key
    # Clear cache if you implement caching later, for now just rerun
    pass # Streamlit reruns the script automatically on button press

try:
    # Make GET request to the backend /replies endpoint
    response = requests.get(BACKEND_URL_GET_REPLIES, timeout=30)

    if response.status_code == 200:
        data = response.json()
        replies = data.get("replies", [])

        if replies:
            st.write(f"Showing {len(replies)} saved replies (newest first):")
            # Display replies using expanders
            for i, item in enumerate(replies):
                with st.expander(f"**{item.get('platform', 'N/A')} Post** (Saved: {format_timestamp(item.get('timestamp'))})"):
                    st.markdown(f"**Original Post:**")
                    st.markdown(f"> {item.get('post_text', 'N/A')}")
                    st.markdown(f"**Generated Reply:**")
                    st.markdown(f"> {item.get('generated_reply', 'N/A')}")
                    # st.write(item) # Optional: Show raw data for debugging
        else:
            st.info("No replies found in the database yet.")
    else:
        st.error(f"Error fetching replies from API ({response.status_code}): {response.text}")

except requests.exceptions.RequestException as e:
    st.error(f"Could not connect to the backend API at {BACKEND_URL_GET_REPLIES} to fetch replies. Is it running? Error: {e}")
except Exception as e:
    st.error(f"An unexpected error occurred while fetching replies: {e}")