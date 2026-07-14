"""
LangGraph agent that powers the HCP conversational Log Interaction flow.

The graph is a simple ReAct-style loop:
  START -> agent (LLM decides whether to call a tool) -> tools (if any) -> agent -> ... -> END

The LLM is bound with the 5 tools defined in tools.py. It decides, based on
the rep's chat message and conversation so far, which tool(s) to invoke
(e.g. search_hcp_profile to find the HCP, then log_interaction to save the
note, or edit_interaction if the rep is correcting a previous entry).
"""
import os
from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from app.agent.tools import ALL_TOOLS

GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

SYSTEM_PROMPT = """You are an AI assistant embedded in a pharma CRM, helping
field representatives log and manage their interactions with Healthcare
Professionals (HCPs) via natural conversation.

You have access to tools to search HCP profiles, log new interactions,
edit existing interactions, schedule follow-ups, and generate call-prep
summaries. Always use search_hcp_profile first if you don't already know
the HCP's id. When the rep describes an interaction in free text, call
log_interaction with the full raw text so the tool's own LLM extraction
can structure it. Be concise and confirm back to the rep what was saved.

Formatting rules: reply in short, plain conversational sentences or a
simple dash-bulleted list. Never use markdown tables, headers (#), or bold
(**text**) — this chat UI displays plain text only, so that markdown syntax
would show up as literal symbols instead of formatting. Keep replies under
~80 words unless the rep asks for more detail."""


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


def build_agent_graph():
    llm = ChatGroq(model=GROQ_MODEL, temperature=0)
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    def agent_node(state: AgentState):
        messages = state["messages"]
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(ALL_TOOLS))

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()


agent_executor = build_agent_graph()
