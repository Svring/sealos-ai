import os
from typing import Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from src.lib.quota.quota_logging import log_quota_event, mask_secret

load_dotenv()


def get_sealos_model(
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    model_name: Optional[str] = "gpt-4.1",
    trial: bool = False,
):
    # ``trial=True`` is set by FreeQuotaStreamMiddleware for platform-funded turns.
    # Always use platform env creds so stale checkpoint user keys cannot win.
    if trial:
        base_url = (
            os.getenv("TRIAL_BASE_URL")
            or os.getenv("SYSTEM_OPENAI_API_BASE_URL")
            or base_url
        )
        api_key = (
            os.getenv("TRIAL_API_KEY")
            or os.getenv("SYSTEM_OPENAI_API_KEY")
            or api_key
        )

    log_quota_event(
        "llm_client_init",
        model_name=model_name,
        base_url=base_url,
        api_key=mask_secret(api_key),
        trial=trial,
    )
    return ChatOpenAI(
        model=model_name,
        base_url=base_url,
        api_key=api_key,
    )
