import streamlit as st
from model import data_analyst_agent, handle_followup_question

st.title("Data Analyst Agent")

if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'file_path' not in st.session_state:
    st.session_state.file_path = None

uploaded_file = st.file_uploader("Upload a file", type=['csv', 'xlsx', 'txt', 'doc', 'pdf', 'png', 'jpg', 'jpeg'])
user_request = st.text_input("Enter your request (e.g., analyze data, visualize, ask a question)")

if uploaded_file and user_request:
    file_path = f"temp_{uploaded_file.name}"
    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())
    st.session_state.file_path = file_path
    st.session_state.conversation_history = []

    result, updated_history = data_analyst_agent(file_path, user_request, st.session_state.conversation_history)
    st.session_state.conversation_history = updated_history

    if isinstance(result, str) and result.endswith('.png'):
        st.image(result)
    else:
        st.write(result)

followup_question = st.text_input("Ask a follow-up question")
if followup_question and st.session_state.file_path:
    answer, updated_history = handle_followup_question(st.session_state.conversation_history, followup_question)
    st.session_state.conversation_history = updated_history
    st.write(answer)
elif followup_question and not st.session_state.file_path:
    st.write("Please upload a file and make an initial request first.")