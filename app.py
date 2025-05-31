import streamlit as st
from model import data_analyst_agent
import os

st.title("Intelligent Data Analyst Agent")

# Initialize session state
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'file_path' not in st.session_state:
    st.session_state.file_path = None

# File uploader
uploaded_file = st.file_uploader("Upload a file", type=['csv', 'xlsx', 'txt', 'doc', 'pdf', 'png', 'jpg', 'jpeg'])
if uploaded_file:
    file_path = f"temp_{uploaded_file.name}"
    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())
    st.session_state.file_path = file_path
    st.session_state.conversation_history = []  # Reset history for new file

# User request input
with st.form(key='request_form'):
    user_request = st.text_input("Enter your request (e.g., 'Analyze trends in the data', 'Create a scatter plot of age vs. income')")
    submit_button = st.form_submit_button(label='Submit')

if submit_button and user_request and st.session_state.file_path:
    try:
        text_response, image_path, updated_history = data_analyst_agent(st.session_state.file_path, user_request, st.session_state.conversation_history)
        st.session_state.conversation_history = updated_history
        st.write(text_response)
        if image_path:
            st.image(image_path)
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

# Display conversation history
if st.session_state.conversation_history:
    st.subheader("Conversation History")
    for msg in st.session_state.conversation_history:
        role = msg['role'].capitalize()
        content = msg['content']
        if isinstance(content, list):  # Handle image-based messages
            content = content[0]['text'] if content and isinstance(content[0], dict) and 'text' in content[0] else str(content)
        st.write(f"{role}: {content}")

# Clean up temporary files
if st.session_state.file_path and os.path.exists(st.session_state.file_path):
    os.remove(st.session_state.file_path)