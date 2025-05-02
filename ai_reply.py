import os
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv
import sys

# Load environment variables (API key)
load_dotenv()

# Configure the Gemini client
# Make sure GEMINI_API_KEY is set in your .env file
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not found in environment variables.", file=sys.stderr)
    # Set model to None or handle error appropriately
    model = None
else:
    try:
        genai.configure(api_key=api_key)
        # Initialize the Gemini model
        # 'gemini-1.5-flash-latest' is often a good balance of speed, capability, and free tier availability
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        print("Gemini AI client configured successfully.")
    except Exception as e:
        print(f"Error configuring Gemini AI client: {e}", file=sys.stderr)
        model = None

# Define safety settings to block potentially harmful content
# Adjust these thresholds as needed (BLOCK_NONE, BLOCK_LOW_AND_ABOVE, BLOCK_MEDIUM_AND_ABOVE, BLOCK_ONLY_HIGH)
safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
}

def generate_human_like_reply(platform: str, post_text: str) -> str:
    """
    Generates a reply using Google Gemini, attempting to match platform tone and style.
    Focuses on sounding authentic and avoiding AI giveaways.
    """
    if not model:
        return "Error: Gemini AI model not initialized. Check API key and configuration."

    try:
        # --- Prompting Workflow ---
        # Keep the prompt similar, focusing on instructions for the desired output style.
        generation_prompt = f"""
        Act as a social media user commenting on a post.
        Analyze the following post from the platform '{platform}':
        Post: "{post_text}"

        Now, generate a short, authentic, human-like reply suitable for {platform}.

        Guidelines for the reply:
        - **Sound Natural:** Use informal language, contractions (like "it's", "don't"), and common slang if appropriate for the platform and context, but avoid overdoing it.
        - **Match Platform:** Twitter replies are often short, quippy, use hashtags. LinkedIn replies are more professional but can still be conversational. Instagram replies often use emojis and are visually focused (though we only handle text).
        - **Contextual Relevance:** Directly address the post's content. If it's a question, offer a brief answer or relevant thought. If it's an opinion, react genuinely (agree, disagree respectfully, add a point). If it's news, show appropriate reaction (excitement, curiosity).
        - **Avoid AI Tropes:** Do NOT use phrases like "As an AI language model...", "It's great that...", "That's an interesting perspective.". Avoid excessive formality, overly perfect grammar, generic praise ("Great post!"), or bullet points.
        - **Conciseness:** Keep the reply relatively short, like a real user would write.
        - **Persona (Implicit):** Reply as a peer or interested individual, not as an official bot or assistant.

        Generate ONLY the reply text itself, without any extra explanations or labels like "Reply:".
        """

        # Use generate_content with the prompt and safety settings
        response = model.generate_content(
            generation_prompt,
            safety_settings=safety_settings,
            # You can also configure generation parameters like temperature, top_p, top_k, max_output_tokens here if needed
            # generation_config=genai.types.GenerationConfig(
            #     temperature=0.75,
            #     max_output_tokens=80,
            #     top_p=0.9
            # )
            )

        # Check if the response was blocked due to safety concerns
        if not response.candidates:
             # Try accessing prompt_feedback if available
            block_reason = "Unknown safety block"
            try:
                block_reason = response.prompt_feedback.block_reason.name
            except Exception:
                 pass # Ignore if feedback isn't available
            print(f"Warning: AI response blocked due to safety settings. Reason: {block_reason}", file=sys.stderr)
            return f"Couldn't generate a reply due to safety filters ({block_reason})."

        # Extract the text from the first candidate
        reply = response.text.strip()

        # Basic check for empty or placeholder replies
        if not reply or reply.lower() == "reply:":
            print("Warning: AI returned an empty or invalid reply.", file=sys.stderr)
            return "Hmm, not sure how to reply to that!" # More human-like error

        return reply

    except Exception as e:
        print(f"Error during Gemini API call: {e}", file=sys.stderr)
        # Consider specific error handling for Google API errors if needed
        # from google.api_core import exceptions as google_exceptions
        # if isinstance(e, google_exceptions.GoogleAPIError): ...
        return "Oops, couldn't generate a reply right now (Gemini). Try again?"

# --- Optional: Simple test block ---
if __name__ == '__main__':
    print("Testing AI reply generation using Gemini...")
    # Ensure you have GEMINI_API_KEY in your .env file for this test
    if not api_key:
        print("Skipping test: GEMINI_API_KEY not found.")
    elif not model:
         print("Skipping test: Gemini model not initialized.")
    else:
        test_platform = "Twitter"
        test_post = "Just released my new open-source library for data validation! 🎉 Check it out on GitHub. #python #opensource"
        print(f"\nPlatform: {test_platform}")
        print(f"Post: {test_post}")
        generated_reply = generate_human_like_reply(test_platform, test_post)
        print(f"Generated Reply: {generated_reply}")

        print("-" * 20)

        test_platform_2 = "LinkedIn"
        test_post_2 = "Reflecting on the key trends shaping the future of AI in business process automation. Collaboration between humans and AI seems crucial."
        print(f"Platform: {test_platform_2}")
        print(f"Post: {test_post_2}")
        generated_reply_2 = generate_human_like_reply(test_platform_2, test_post_2)
        print(f"Generated Reply 2: {generated_reply_2}")