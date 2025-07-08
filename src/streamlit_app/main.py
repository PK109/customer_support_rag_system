import streamlit as st
from utils.auth import authenticate
authenticate()

from utils.llm_setup import llm
from utils.session_state import init_session_state

init_session_state()

st.title("Technical Support Chatbot")
st.write("This is a chat app using Streamlit and LangChain. It is designed to answer questions about hardware and programming topics in robotic field.")


# Display chat messages from history
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if prompt := st.chat_input(placeholder=st.session_state.placeholder, key="chat_input", max_chars=500):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display assistant response in chat message container
    messages = []
    messages.extend(st.session_state.messages)

    with st.chat_message("assistant"):
        stream = llm.stream(messages)
        response = st.write_stream(stream)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})