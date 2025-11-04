import os
from typing import Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


def get_sealos_model(
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    model_name: Optional[str] = "gpt-4.1",
):
    return ChatOpenAI(
        model=model_name,
        base_url=base_url,
        api_key=api_key,
    )
