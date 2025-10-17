import os
from typing import Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


def get_sealos_model(
    model_name: Optional[str] = "gpt-4.1",
    base_url: Optional[str] = "https://aiproxy.usw.sealos.io/v1",
    api_key: Optional[str] = None,
):
    print(f"model_name: {model_name}")
    print(f"base_url: {base_url}")
    print(f"api_key: {api_key}")
    return ChatOpenAI(
        model=model_name,
        base_url=base_url,
        api_key=api_key,
    )
