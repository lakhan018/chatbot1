import os
import flask
from flask import Flask, request, jsonify
import google.generativeai as genai
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv() # Load variables from .env file

# --- Flask App Initialization ---
app = Flask(__name__)

# --- Gemini API Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("🔴 ERROR: GEMINI_API_KEY environment variable not found.")
    print("Please create a .env file with GEMINI_API_KEY=YOUR_API_KEY")
    # You might want to exit or handle this more gracefully in a real app
    gemini_configured = False
else:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_configured = True
        print("✅ Gemini API Key configured successfully.")
    except Exception as e:
        print(f"🔴 ERROR configuring Gemini API: {e}")
        gemini_configured = False

# --- Initialize the Gemini Model ---
# Use a model suitable for text generation. 'gemini-1.5-flash' is a good choice.
# You mentioned "flash 2.0" - 'gemini-1.5-flash' is the current identifier for the Flash model.
model = None
if gemini_configured:
    try:
        model = genai.GenerativeModel('gemini-1.5-flash') # Or 'gemini-pro' for the Pro model
        print(f"✅ Initialized Gemini Model: {model.model_name}")
    except Exception as e:
        print(f"🔴 ERROR initializing Gemini model: {e}")
        model = None # Ensure model is None if initialization fails
else:
    print("🟡 Skipping Gemini model initialization due to missing API key.")


# --- Helper Function for Prompt Construction ---
def create_privacy_policy_prompt(details):
    """Constructs a detailed prompt for the Gemini API."""

    # Basic validation or default values
    company_name = details.get('company_name', 'Your Company')
    website_url = details.get('website_url', 'Your Website/App URL')
    data_collected = details.get('data_collected', 'e.g., names, email addresses, IP addresses, cookies, usage data')
    data_usage = details.get('data_usage', 'e.g., service provision, personalization, analytics, marketing')
    data_sharing = details.get('data_sharing', 'Specify if data is shared and with whom (e.g., analytics providers, payment processors)')
    security_measures = details.get('security_measures', 'Describe general security practices (e.g., encryption, access controls)')
    user_rights = details.get('user_rights', 'Mention user rights like access, correction, deletion, opt-out')
    cookie_usage = details.get('cookie_usage', 'Explain if cookies are used and for what purpose')
    contact_email = details.get('contact_email', 'your privacy contact email')
    jurisdiction = details.get('jurisdiction', '') # Optional: e.g., California, EU

    prompt = f"""
    Act as a helpful assistant specialized in drafting website and application documents.
    Generate a comprehensive draft privacy policy based on the following details provided by the user.
    The policy should be clear, easy for end-users to understand, and cover common requirements.
    Include sections like: Introduction, Information We Collect, How We Use Your Information, Sharing Your Information, Data Security, Your Rights and Choices, Cookie Policy, Changes to This Policy, and Contact Us.
    Emphasize that this is a generated template and should be reviewed by a legal professional before publishing.

    **Service Details:**
    *   **Company/Service Name:** {company_name}
    *   **Website/App URL:** {website_url}
    *   **Types of Personal Data Collected:** {data_collected}
    *   **How Data is Used:** {data_usage}
    *   **Data Sharing Practices (Third Parties):** {data_sharing}
    *   **Data Security Measures:** {security_measures}
    *   **User Rights (e.g., access, deletion):** {user_rights}
    *   **Cookie Usage:** {cookie_usage}
    *   **Contact Email for Privacy Concerns:** {contact_email}
    """
    if jurisdiction:
        prompt += f"*   **Primary Jurisdiction (if specified):** {jurisdiction} (Consider mentioning relevant laws like GDPR or CCPA if applicable, but advise legal review)\n"

    prompt += """
    **Instructions for Generation:**
    1.  Generate only the text content of the privacy policy.
    2.  Use clear headings for each section.
    3.  Maintain a professional but understandable tone.
    4.  Include a prominent disclaimer stating this is a template and requires legal review for compliance and accuracy specific to the user's situation and jurisdiction.
    5.  Do not add any conversational text before or after the policy itself (like "Here is the policy:" or "I hope this helps!").
    """
    return prompt

# --- API Endpoint for Generating Policy ---
@app.route('/generate-policy', methods=['POST'])
def generate_policy():
    """API endpoint to receive details and return a generated privacy policy."""

    # Check if Gemini is ready
    if not model:
        return jsonify({"error": "Gemini model not initialized. Check API key and logs."}), 500

    # Get data from the POST request body (expecting JSON)
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()

    # Basic input validation (add more as needed)
    required_fields = ['company_name', 'website_url', 'data_collected', 'data_usage', 'contact_email']
    missing_fields = [field for field in required_fields if field not in data or not data[field]]
    if missing_fields:
        return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

    # Create the prompt for Gemini
    prompt = create_privacy_policy_prompt(data)
    print("\n--- Sending Prompt to Gemini ---")
    # print(prompt) # Uncomment to debug the prompt being sent
    print("-----------------------------\n")


    # Call the Gemini API
    try:
        # Configure safety settings if needed (optional)
        # safety_settings = [...]
        # response = model.generate_content(prompt, safety_settings=safety_settings)

        response = model.generate_content(prompt)

        # Extract the generated text
        # Check the structure of 'response' if needed (e.g., print(response))
        # It's usually in response.text or sometimes response.parts[0].text
        generated_policy = response.text

        print("✅ Policy generated successfully.")
        return jsonify({"privacy_policy": generated_policy})

    except Exception as e:
        print(f"🔴 ERROR calling Gemini API: {e}")
        # Try to provide more specific feedback if possible
        # Check 'response.prompt_feedback' if available for blocked prompts
        try:
            if response and response.prompt_feedback:
                 print(f"Prompt Feedback: {response.prompt_feedback}")
                 return jsonify({"error": f"Failed to generate policy. The prompt might have been blocked. Reason: {response.prompt_feedback}"}), 500
        except:
             pass # Ignore errors checking prompt_feedback
        return jsonify({"error": f"An error occurred while generating the policy: {e}"}), 500


# --- Basic Route for Testing ---
@app.route('/')
def index():
    return "Privacy Policy Generator API is running. Use the /generate-policy endpoint (POST)."

# --- Run the Flask App ---
if __name__ == '__main__':
    # Check if Gemini is configured before starting the server
    if not gemini_configured:
        print("🔴 Cannot start server: Gemini API is not configured. Check your .env file and API key.")
    elif not model:
        print("🔴 Cannot start server: Gemini model failed to initialize. Check logs.")
    else:
        # Use debug=True for development only. It enables auto-reloading and detailed errors.
        # Use debug=False for production.
        # host='0.0.0.0' makes it accessible on your network (use with caution)
        print("\n🚀 Starting Flask server...")
        print("   API Key Loaded: YES")
        print(f"   Gemini Model: {model.model_name}")
        print("   Send POST requests with JSON data to http://127.0.0.1:5000/generate-policy")
        app.run(debug=True, host='127.0.0.1', port=5000)