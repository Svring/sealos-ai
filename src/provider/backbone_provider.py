import os
from typing import Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


def get_sealos_model(
    model_name: Optional[str] = None,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
):
    return ChatOpenAI(
        model=model_name or "gpt-4.1",
        base_url=base_url or os.getenv("SEALOS_BASE_URL"),
        api_key=api_key or os.getenv("SEALOS_API_KEY"),
    )
