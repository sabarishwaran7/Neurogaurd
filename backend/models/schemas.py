
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

GroqModelId = Literal[
    "llama3-8b-8192",
    "llama3-70b-8192",
    "qwen-qwq-32b",
    "deepseek-r1-distill",
]


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    created_at: Optional[datetime] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    model_name: GroqModelId
    system_prompt: str = Field(default="You are a helpful assistant.", max_length=8000)
    memory_enabled: bool = True
    rag_enabled: bool = False


class AgentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    model_name: Optional[GroqModelId] = None
    system_prompt: Optional[str] = Field(default=None, max_length=8000)
    memory_enabled: Optional[bool] = None
    rag_enabled: Optional[bool] = None


class AgentOut(BaseModel):
    id: str
    name: str
    model_name: str
    system_prompt: str
    memory_enabled: bool
    rag_enabled: bool
    api_key: Optional[str] = None
    api_key_prefix: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    agent_id: str
    message: str = Field(min_length=1, max_length=32000)


class ChatResponse(BaseModel):
    reply: str
    agent_id: str
    used_rag: bool = False
    used_memory: bool = False


class ExternalAgentChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=32000)


class ExternalAgentChatResponse(BaseModel):
    reply: str
    agent_name: str
    used_rag: bool = False
    used_memory: bool = False


class DashboardStats(BaseModel):
    total_agents: int
    api_calls_today: int
    recent_chats: list[dict[str, Any]] = Field(default_factory=list)
