import toml
import os

# Load credentials from the file
def authenticate(path: str = ".streamlit/secrets.toml"):
    """
    Authenticate the application by loading credentials from a TOML file.
    The credentials are stored in environment variables for use in the application.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"The secrets file '{path}' does not exist.")
    config = toml.load(path)

    os.environ["GOOGLE_API_KEY"] = config["gemini"]["GOOGLE_API_KEY"]
    os.environ["OPENAI_API_KEY"] = config["openai"]["OPENAI_API_KEY"]
    os.environ["LANGSMITH_TRACING"] = config["langchain"]["LANGSMITH_TRACING"]
    os.environ["LANGSMITH_API_KEY"] = config["langchain"]["LANGSMITH_API_KEY"]
    os.environ["LANGSMITH_PROJECT"] = config["langchain"]["LANGSMITH_PROJECT"]
    os.environ["LANGSMITH_ENDPOINT"] = config["langchain"]["LANGSMITH_ENDPOINT"]
if __name__ == "__main__":
    authenticate()
