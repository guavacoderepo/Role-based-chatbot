import streamlit as st
import requests
from ..utils.history import retrieve_history  
from ..schemas.schemas import UserModel

# List of possible user roles for registration dropdown
roles = ["engineering", "marketing", "finance", "hr", "general", "executives"] 


# Login page UI and logic
def login_page():
    st.title("Login Page")

    # User inputs for credentials
    username = st.text_input("Username") 
    password = st.text_input("Password", type="password")
    api_key = st.text_input("Openai API Key", type="password") 

    # Center the buttons using three columns
    col1, _, _ = st.columns([2, 2, 1])

    # Place both buttons in the left column (col1)
    with col1:
        login_clicked = st.button("Login")
        register_clicked = st.button("Don't have an account? Register")

    if login_clicked:
        try:
            # Send POST request to FastAPI login endpoint with credentials
            response = requests.post(
                "http://127.0.0.1:8000/api/v1/auth/login",
                json={"username": username, "password": password, "api_key": api_key}
            )

            if response.status_code == 200:
                # Parse response JSON into UserModel pydantic model

                user_resp = response.json()
                role = "employee" if user_resp['user']['role'] == "general" else user_resp['user']['role']
                user_resp['user']['role'] = role
                user_model = UserModel(**user_resp)

                # Show success message with user info
                st.success(f"✅ Login successful, Welcome, {user_model.user.username}, (Role: {user_model.user.role})")

                # Store token and user info in session state
                st.session_state.token = user_model.token
                st.session_state.user = user_model.user

                # Retrieve and load previous conversation history after login
                retrieve_history()

                # Refresh the app to switch to chat UI or main app page
                st.rerun()

            else:
                # Show API error message if login fails
                st.error(f"❌ Login failed: {response.json().get('msg', 'Invalid credentials')}")

        except Exception as e:
            # Handle connection or unexpected errors gracefully
            st.error(f"⚠️ Error connecting to server: {e}")

    if register_clicked:
        # Switch UI to registration page and rerun app
        st.session_state.is_login = False
        st.rerun()


# Registration page UI and logic
def registration_page():
    st.title("Registration Page")

    # User inputs for new account creation
    username = st.text_input("Username")
    role = st.selectbox("Select Role", roles) 
    password = st.text_input("Password", type="password")

    role = "general" if role == "employee" else role

    # Center the buttons using three columns
    col1, _, _ = st.columns([2, 2, 1])

    # Place both buttons in the left column (col1)
    with col1:
        register_clicked = st.button("Register")
        login_clicked = st.button("Already have an account? Login")

    if register_clicked:
        try:
            # Send POST request to FastAPI registration endpoint with user data
            response = requests.post(
                "http://127.0.0.1:8000/api/v1/auth/register",
                json={"username": username, "password": password, "role": role}
            )

            if response.status_code == 200:

                # Switch UI back to login page
                st.session_state.is_login = True

                # Refresh app to show login UI
                st.rerun()

                # Show success message on successful registration
                st.success(f"✅ Registration of {username} successful!")

            else:
                # Show API error message on failure
                st.error(f"❌ Registration failed: {response.json().get('msg', 'Unknown error')}")

        except Exception as e:
            # Handle unexpected errors gracefully
            st.error(f"⚠️ Error connecting to server: {e}")
    
    if login_clicked:
        # Switch UI back to login page and rerun
        st.session_state.is_login = True
        st.rerun()


# Function to handle user logout
def logout():
    # Clear session data such as auth token and messages
    st.session_state.token = None 
    st.session_state.messages = []

    # Refresh app to redirect to login page
    st.rerun()