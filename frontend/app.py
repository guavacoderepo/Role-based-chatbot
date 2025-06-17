import streamlit as st
from src.pages.auth import login_page, registration_page 
from src.pages.chat import chat_ui

if 'is_login' not in st.session_state:
    st.session_state.is_login = True 

# Initialize session state variables if not already set
if 'token' not in st.session_state:
    st.session_state.token = None

if 'user' not in st.session_state:
    st.session_state.user = {} 

# Show login page if not authenticated
if not st.session_state.token:
    if st.session_state.is_login:
        login_page()
    else:
        registration_page()

# If user is logged in, show chat interface
if st.session_state.token:
    chat_ui()
