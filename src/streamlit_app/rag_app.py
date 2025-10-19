import streamlit as st
from src.code import rag_workflow
from utils.auth import authenticate

authenticate()
st.set_page_config(page_title="RAG Chat", layout="wide")

st.title("RAG Chat")
st.write("A chat interface that queries the repository's RAG workflow")
st.write("Please note that during first launch the backend may take a few moments to initialize, import models, etc.")

# Sidebar settings for secrets path and collection
with st.sidebar:
    st.header("Backend settings")
    secrets_path = st.text_input("secrets_path", value=st.session_state.get("secrets_path", ".streamlit/secrets.toml"))
    collection = st.text_input("collection", value=st.session_state.get("collection", "my_qdrant_collection"))
    # store back to session state
    st.session_state["secrets_path"] = secrets_path
    st.session_state["collection"] = collection


# Session state for chat
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are a helpful assistant with access to product manuals and support docs."}
    ]

def send_query(user_text: str):
    st.session_state.messages.append({"role": "user", "content": user_text})
    # Call the project RAG implementation `rag_workflow.rag(...)`.
    # The `secrets_path` and `collection` are stored in session state (set via sidebar).
    secrets_path = st.session_state.get("secrets_path", "./secrets.toml")
    collection = st.session_state.get("collection", "my_qdrant_collection")
    try:
        resp = rag_workflow.rag(user_text, secrets_path=secrets_path, collection=collection)
        st.session_state.messages.append({"role": "assistant", "content": resp})
        return resp
    except Exception as e:
        # Surface a helpful message to the user and log the exception details.
        st.error(f"rag_workflow.rag failed: {e}")
        tb = None
        try:
            import traceback
            tb = traceback.format_exc()
        except Exception:
            tb = str(e)
        # Add a short assistant message so the chat view shows the failure
        failure_msg = f"RAG backend error: {e}\n\nSee logs for details."
        st.session_state.messages.append({"role": "assistant", "content": failure_msg})
        # Optionally print the traceback to the Streamlit debug area
        st.text_area("RAG traceback (for debugging)", value=tb, height=200)
        return failure_msg

# Chat UI
chat_col, info_col = st.columns([3, 1])


with chat_col:
    for msg in st.session_state.messages:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    prompt = st.chat_input(placeholder="Ask a question about the manuals or system...")
    if prompt:
        with st.chat_message("user"):
            st.markdown(prompt)
        # send and display assistant reply
        reply = send_query(prompt)
        with st.chat_message("assistant"):
            st.markdown(reply)

