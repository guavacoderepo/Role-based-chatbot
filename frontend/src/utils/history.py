import streamlit as st
import requests

# Function to retrieve chat history from backend
def retrieve_history():
    # Send GET request to backend `/history` endpoint with user credentials
    response = requests.get(
        "http://127.0.0.1:8000/api/v1/chat/history",
        headers={
            "Authorization": f"Bearer {st.session_state.token}"
        }
    )

    # Parse JSON response containing previous chat entries
    mesages = response.json()

    print(mesages)

    # Initialize the messages list in session state if not already present
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Loop through each entry and append user and assistant messages to the session state
    for entry in mesages:
        st.session_state.messages.append({
            "role": "user", 
            "content": entry["prompt"]
        })
        st.session_state.messages.append({
            "role": "assistant", 
            "content": entry["response"]
        })
