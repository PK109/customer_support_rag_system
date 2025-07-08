import random
import streamlit as st
from st_files_connection import FilesConnection
import os

def init_session_state():
    # Create connection object and retrieve file contents.
    # Specify input format is a txt and to cache the result for 600 seconds.
    try:
        conn = st.connection('gcs', type=FilesConnection, ttl=600)
    except Exception as e:
        st.error(f"Error connecting to GCS: {e}")
        st.write("Using local files instead.")
        conn = None
    BUCKET_URL = os.getenv('BUCKET_URL') 
    if BUCKET_URL is None:
        raise EnvironmentError("Missing required environment variable: BUCKET_URL")

    if "messages" not in st.session_state:
        system_message = "Be concise in your answers. Highly rely on the information provided in the documents. Try to respond in user's language. If you don't know the answer, say that you don't know."
        init_message = "Hello! I am a technical support chatbot.\nFeel free to ask me about some technical stuff!"
        st.session_state.messages = []
        st.session_state.messages.append({"role": "system", "content": system_message})
        st.session_state.messages.append({"role": "assistant", "content": init_message})
    
    if "placeholder" not in st.session_state:
        content = ""
        if conn is not None:
            file = f'gs://{BUCKET_URL}/general/faq.txt'
            if conn.fs.isfile(file):
                content=conn.read(file, input_format='text', ttl=600)
        else:
            with open("./docs/faq.txt", "r") as f:
                content = f.read()
        lines = content.split("\n")
        st.session_state.placeholder = random.choice(lines)