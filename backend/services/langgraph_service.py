

from pathlib import Path
from typing import Any, Dict, List, Optional

from langgraph.graph import END, START, StateGraph

from services.groq_service import get_chat_model, invoke_text
from services.rag_service import retrieve_context


def _format_history(history: Optional[List[dict[str, str]]]) -> str:
    if not history:
        return ""
    lines: List[str] = []
    for m in history[-12:]:
        role = m.get("role", "user")
        content = m.get("content", "")
        lines.append(f"{role.upper()}: {content}")
    return "\n".join(lines)


def build_agent_app() -> Any:
    """Compile a LangGraph workflow (vector path supplied per invoke in state)."""
    graph = StateGraph(dict)

    def planner(state: Dict[str, Any]) -> Dict[str, Any]:

        model = state["model_name"]

        q = state["query"]

        plan_prompt = (
            "You are a concise planner. "
            "Output a short bullet plan (max 5 bullets) "
            "for how to answer the user. "
            "Do not answer the user yet."
        )

        plan = invoke_text(
            model,
            plan_prompt,
            f"User request:\n{q}",
            temperature=0.1,
        )

        # Preserve existing state
        state["plan"] = plan

        return state

    def rag(state: Dict[str, Any]) -> Dict[str, Any]:

        if not state.get("rag_enabled"):

            state["context"] = ""

            return state

        agent_id = state["agent_id"]

        vr = Path(state["vector_root"])

        ctx = retrieve_context(
            agent_id,
            state["query"],
            vr,
            k=4
        )

        state["context"] = ctx

        return state

    def reason(state: Dict[str, Any]) -> Dict[str, Any]:

        system = state["system_prompt"]

        ctx = state.get("context") or ""

        plan = state.get("plan") or ""

        hist = _format_history(state.get("history"))

        rag_block = ""

        if state.get("rag_enabled"):

            rag_block = (
                "\n\nRetrieved context "
                "(may be empty if no documents match):\n"
                f"{ctx}\n"
            )

        memory_block = ""

        if state.get("memory_enabled") and hist:

            memory_block = (
                "\n\nRecent conversation:\n"
                + hist
                + "\n"
            )

        augmented_system = (
            f"{system}\n\n"
            f"Internal plan "
            f"(follow, do not reveal verbatim):\n"
            f"{plan}"
            f"{rag_block}"
            f"{memory_block}"
        )

        llm = get_chat_model(
            state["model_name"],
            temperature=0.3
        )

        messages = [
            ("system", augmented_system),
            ("human", state["query"]),
        ]

        resp = llm.invoke(messages)

        content = getattr(resp, "content", None)

        if isinstance(content, str):

            text = content

        elif isinstance(content, list):

            text = "".join(str(b) for b in content)

        else:

            text = str(resp)

        state["response"] = text

        return state

    graph.add_node("planner", planner)
    graph.add_node("rag", rag)
    graph.add_node("reason", reason)

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "rag")
    graph.add_edge("rag", "reason")
    graph.add_edge("reason", END)

    return graph.compile()
