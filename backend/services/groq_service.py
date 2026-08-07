import os
from typing import Optional

from langchain_groq import ChatGroq

GROQ_MODEL_MAP = {
    "deepseek-r1-distill": os.getenv("GROQ_MODEL_DEEPSEEK", "deepseek-r1-distill-llama-70b"),
}


def resolve_groq_model(model_name: str) -> str:
    return GROQ_MODEL_MAP.get(model_name, model_name)


def get_chat_model(model_name: str, temperature: float = 0.2) -> ChatGroq:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set in the environment.")
    resolved = resolve_groq_model(model_name)
    return ChatGroq(
        api_key=api_key,
        model_name=resolved,
        temperature=temperature,
    )


def invoke_text(model_name: str, system_prompt: str, user_content: str, temperature: float = 0.2) -> str:
    llm = get_chat_model(model_name, temperature=temperature)
    messages = [
        ("system", system_prompt),
        ("human", user_content),
    ]
    resp = llm.invoke(messages)
    content = getattr(resp, "content", None)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and "text" in block:
                parts.append(str(block["text"]))
            else:
                parts.append(str(block))
        return "".join(parts)
    return str(resp)
