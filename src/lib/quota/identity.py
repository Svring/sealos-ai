from urllib.parse import unquote

import yaml
from kubernetes.config.kube_config import KubeConfigLoader

from src.lib.quota.types import DEFAULT_ASSISTANT_NAMESPACE_KEY

KUBECONFIG_DEFAULT_NAMESPACE = "default"
TRIAL_KUBECONFIG_MARKER = "trial-kubeconfig"


def decode_kubeconfig(encoded: str | None) -> str | None:
    if not encoded or not encoded.strip():
        return None
    try:
        return unquote(encoded.strip())
    except Exception:
        return None


def namespace_from_kubeconfig_text(kubeconfig_text: str) -> str | None:
    try:
        config_dict = yaml.safe_load(kubeconfig_text)
        if not isinstance(config_dict, dict):
            return None
        loader = KubeConfigLoader(config_dict=config_dict)
        contexts = loader.list_contexts()
        current_name = config_dict.get("current-context")
        if not isinstance(current_name, str) or not current_name.strip():
            return None
        active_context = next(
            (item for item in contexts if item.get("name") == current_name),
            None,
        )
    except Exception:
        return None

    if not active_context:
        return None

    namespace = active_context.get("context", {}).get("namespace")
    if isinstance(namespace, str):
        trimmed = namespace.strip()
        if trimmed:
            return trimmed
    return KUBECONFIG_DEFAULT_NAMESPACE


def normalize_assistant_namespace(namespace: str) -> str:
    trimmed = namespace.strip()
    return trimmed if trimmed else DEFAULT_ASSISTANT_NAMESPACE_KEY


def resolve_entitlement_key(
    *,
    kubeconfig_encoded: str | None,
    trial: bool = False,
    session_id: str | None = None,
) -> str | None:
    kubeconfig_text = decode_kubeconfig(kubeconfig_encoded)
    if kubeconfig_text and TRIAL_KUBECONFIG_MARKER not in kubeconfig_text:
        namespace = namespace_from_kubeconfig_text(kubeconfig_text)
        if namespace:
            return normalize_assistant_namespace(namespace)

    if trial:
        session = (session_id or "").strip()
        if session:
            return f"trial:{session}"
        return "trial:__default__"

    if kubeconfig_text:
        return DEFAULT_ASSISTANT_NAMESPACE_KEY

    return None
