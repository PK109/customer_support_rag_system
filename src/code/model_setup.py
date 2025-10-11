from sentence_transformers import SentenceTransformer
from openai import OpenAI
import toml, os

def setup_model(model_name='all-mpnet-base-v2', cache_folder="./models"):
    print(f"Loading model {model_name}...", end=" ")
    model = SentenceTransformer(
        model_name,
        trust_remote_code=True,
        cache_folder=cache_folder
    )
    print(f"DONE")
    return model

def setup_llm_client(secrets_path):
    config = toml.load(secrets_path)
    os.environ["OPENAI_API_KEY"] = config["openai"]["OPENAI_API_KEY"]
    return OpenAI()
