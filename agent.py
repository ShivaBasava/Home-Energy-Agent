"""Interactive LangChain agent that discovers its tools from an MCP server and runs on a local Ollama model."""
import asyncio, os, sys
from pathlib import Path
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_ollama import ChatOllama

SYSTEM = ("You plan residential energy systems (rooftop PV, battery storage, heat pumps). "
          "Always use the tools: kg_influencers or kg_neighbors for relations in the knowledge graph, "
          "search_knowledge for background notes, estimate_pv_yield_kwh for yield numbers. "
          "Only state facts that appear in tool results. If a tool does not list a relation, say it is not in the graph. "
          "Do not invent numbers. Mention which tool each fact came from.")

def build_client() -> MultiServerMCPClient:
    env = {k: v for k, v in os.environ.items() if k != "PS1"}
    env["FASTMCP_LOG_LEVEL"] = "WARNING"
    return MultiServerMCPClient({"energy": {
        "command": sys.executable, "args": [str(Path(__file__).parent / "mcp_server.py")],
        "transport": "stdio", "env": env}})

async def build_agent():
    tools = await build_client().get_tools()
    llm = ChatOllama(model=os.getenv("LLM_MODEL", "qwen2.5:3b"), temperature=0,
                     num_ctx=int(os.getenv("NUM_CTX", "2048")))
    return create_agent(llm, tools, system_prompt=SYSTEM)

def tool_calls(messages):
    return [m for m in messages if m.type == "tool"]

async def main(first_question: str | None = None):
    agent = await build_agent()
    history, question = [], first_question
    while True:
        if question is None:
            question = input("\nQuestion (empty or 'exit' to quit): ").strip()
        if question.lower() in ("", "exit", "quit"):
            break
        history.append(("user", question))
        result = await agent.ainvoke({"messages": history})
        for m in tool_calls(result["messages"][len(history):]):
            print(f"[tool:{m.name}] {str(m.content)[:160]!r}")
        print("\nANSWER:", result["messages"][-1].content)
        history, question = result["messages"], None

if __name__ == "__main__":
    asyncio.run(main(" ".join(sys.argv[1:]) or None))
