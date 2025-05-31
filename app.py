import streamlit as st
from model import data_analyst_agent
import os
from dotenv import load_dotenv

load_dotenv()
TOGETHER_API_KEY = st.secrets.get("TOGETHER_API_KEY", os.getenv("TOGETHER_API_KEY"))

st.title("Intelligent Data Analyst Agent")

if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'file_path' not in st.session_state:
    st.session_state.file_path = None

uploaded_file = st.file_uploader("Upload a file", type=['csv', 'xlsx', 'txt', 'doc', 'pdf', 'png', 'jpg', 'jpeg'])
if uploaded_file:
    file_path = f"temp_{uploaded_file.name}"
    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())
    st.session_state.file_path = file_path
    st.session_state.conversation_history = []

with st.form(key='request_form'):
    user_request = st.text_input("Enter your request")
    submit_button = st.form_submit_button(label='Submit')

if submit_button and user_request and st.session_state.file_path:
    text_response, image_path, updated_history = data_analyst_agent(st.session_state.file_path, user_request, st.session_state.conversation_history)
    st.session_state.conversation_history = updated_history
    st.write(text_response)
    if image_path:
        st.image(image_path)

if st.session_state.conversation_history:
    st.subheader("Conversation History")
    for msg in st.session_state.conversation_history:
        st.write(f"{msg['role'].capitalize()}: {msg['content']}")
