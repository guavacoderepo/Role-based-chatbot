import streamlit as st
import requests
from .auth import logout
from ..schemas.schemas import User

# Main chat UI function
def chat_ui():
    st.title("FinSolve Technologies Chatbot")

    user:User = st.session_state.user

    # Sidebar section for user info and logout button
    with st.sidebar:
        st.write(f"Welcome: {user.username}")
        st.write(user.role.value.capitalize())
        
        # Logout button
        if st.button("🔒 Logout"):
            logout()

    # Display existing chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Prompt user for new chat input
    if prompt := st.chat_input("What is up?"):
        # Store user input in session state
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user input in the chat interface
        with st.chat_message("user"):
            st.markdown(prompt)

        # Make POST request to backend API
        try:
            response = requests.post(
                "http://127.0.0.1:8000/api/v1/chat/start",
                json={"prompt": prompt},
                headers={
                    "Authorization": f"Bearer {st.session_state.token}"
                }
            )
            response.raise_for_status()

            # Check the response content type
            content_type = response.headers.get("content-type", "")

            # If it's a PDF, show download button
            if "application/pdf" in content_type:
                st.success("📄 PDF is ready to download!")
                st.download_button(
                    label="📥 Click to download PDF",
                    data=response.content,
                    file_name=f"{user.username}_{user.role.value}_summary.pdf",
                    mime="application/pdf"
                )
                assistant_text = "✅ I've generated a PDF summary for you!"
            else:
                # If it's text response, parse and display
                assistant_reply = response.json()
                assistant_text = assistant_reply.get('response', 'No response received.')

        except Exception as e:
            # Handle any errors during request
            assistant_text = f"❌ Error: {str(e)}"

        # Display assistant response
        with st.chat_message("assistant"):
            st.markdown(assistant_text)

        # Save assistant response to session
        st.session_state.messages.append({"role": "assistant", "content": assistant_text})
