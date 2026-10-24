# Home Energy Agent

### Home Energy Planning Agent a PoC

For planning residential energy systems, this acts as Local-first LLM agent.
Example:- rooftop PV, battery storage, heat pump.


Retrieval, a knowledge graph and a calculation tool are exposed through a Model Context Protocol (MCP) server.
Later a LangGraph agent running on Ollama discovers and calls the tools.

    question
        |
    LangGraph agent (ChatOllama)
        |
    MCP client 
        |
    MCP server (stdio)
                                       
    | search_knowledge  (Chroma + Ollama embeddings)
    | kg_neighbors / kg_sparql (rdflib knowledge graph)
    ` estimate_pv_yield_kwh (simplified yield model)

## Run
    pip install -r requirements.txt
    ollama pull qwen2.5:3b && ollama pull nomic-embed-text
    LLM_MODEL=qwen2.5:3b python agent.py

Offline smoke test of retrieval without Ollama: `EMBED_BACKEND=hash`.

## Key Infomation
- Data in `data/` is illustrative placeholder content and the yield model is a simplification, not a design tool.

