"""LangGraph agent runtime.

A minimal but real two-node reasoning graph:

    START -> think -> respond -> END

``think`` reasons about the task; ``respond`` produces the final answer using
that reasoning. Each node records a step so runs are fully traceable. The LLM is
injected (any object exposing an async ``chat(messages, model)`` method), which
keeps the runtime testable without a live model server.
"""

from __future__ import annotations

from typing import Any, Protocol, TypedDict

from langgraph.graph import END, START, StateGraph


class ChatModel(Protocol):
    """Anything that can produce a chat completion."""

    async def chat(self, messages: list[dict[str, str]], model: str | None = None) -> str: ...


class AgentState(TypedDict):
    """State threaded through the graph."""

    task: str
    thought: str
    answer: str
    steps: list[dict[str, Any]]


class AgentRuntime:
    """Compiles and executes the reasoning graph."""

    def __init__(self, llm: ChatModel, model: str | None = None) -> None:
        self._llm = llm
        self._model = model
        self._graph = self._build()

    def _build(self) -> Any:
        graph: StateGraph[AgentState] = StateGraph(AgentState)
        graph.add_node("think", self._think)
        graph.add_node("respond", self._respond)
        graph.add_edge(START, "think")
        graph.add_edge("think", "respond")
        graph.add_edge("respond", END)
        return graph.compile()

    async def _think(self, state: AgentState) -> dict[str, Any]:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a reasoning assistant. Think step by step about how "
                    "to best answer the user's task. Return only your reasoning."
                ),
            },
            {"role": "user", "content": state["task"]},
        ]
        thought = await self._llm.chat(messages, self._model)
        return {
            "thought": thought,
            "steps": [*state["steps"], {"node": "think", "output": thought}],
        }

    async def _respond(self, state: AgentState) -> dict[str, Any]:
        messages = [
            {
                "role": "system",
                "content": "Give a clear, concise final answer to the task.",
            },
            {
                "role": "user",
                "content": (f"Task: {state['task']}\nReasoning: {state['thought']}\nFinal answer:"),
            },
        ]
        answer = await self._llm.chat(messages, self._model)
        return {
            "answer": answer,
            "steps": [*state["steps"], {"node": "respond", "output": answer}],
        }

    async def run(self, task: str) -> AgentState:
        """Execute the graph for ``task`` and return the final state."""
        initial: AgentState = {"task": task, "thought": "", "answer": "", "steps": []}
        result: AgentState = await self._graph.ainvoke(initial)
        return result
