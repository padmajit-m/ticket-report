import streamlit as st
import json
import datetime

# Title of the Streamlit app
st.title("Public Webhook Receiver")

# Create a text file to store webhook data
WEBHOOK_FILE = "webhook_requests.txt"

# Function to save webhook data to a file
def save_webhook_data(data):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(WEBHOOK_FILE, "a") as f:
        f.write(f"Timestamp: {timestamp}\n")
        f.write(json.dumps(data, indent=2))
        f.write("\n" + "-" * 50 + "\n")

# Display webhook instructions
st.write("Use this app as a webhook URL to receive POST requests.")

# Check if there's an incoming webhook request
if st.experimental_get_query_params():  # For testing GET requests
    st.write("Webhook URL is active. Send a POST request to this URL.")

# Handle webhook requests
request = st.experimental_get_query_params()  # For debugging in Streamlit

if st.button("Simulate Webhook"):
    # Simulate webhook data for testing
    test_data = {"message": "This is a test webhook", "status": "success"}
    save_webhook_data(test_data)
    st.success("Test webhook received!")

# Display received webhook data
st.subheader("Received Webhook Data:")
try:
    with open(WEBHOOK_FILE, "r") as f:
        st.text(f.read())  # Show the saved webhook requests
except FileNotFoundError:
    st.write("No webhooks received yet.")

# Instructions for using as a webhook
st.write("Send a POST request to this URL with JSON data, and it will be saved.")
