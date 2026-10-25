# MCP notes

Working notes on the Model Context Protocol (MCP) as used in this project. They describe roles and design decisions, not specific tools or files, so they stay valid when further tools, documents or data sources are added. For the current tool list, read `mcp_server.py`.


## Lifecycle of one question

-- The client starts the server and they exchange capabilities (initialize).

-- The client asks the server for its tool list: names, descriptions, input schemas.

-- The agent passes those tool descriptions to the language model.

-- The model decides whether to call a tool and with which arguments.

-- The client sends the call to the server, which run it and returns the result.

-- The model reads the result and either calls another tool or answers.

Important think to note that, the model never runs code itself. It only proposes calls, and the server executes them.


## Advantage of using MCP here instead of plain function calls

- **Decoupling:** tool logic lives in the server, the reasoning loop lives in the agent. Either can change without touching the other.
- **Reuse:** the same server can be used by any MCP-capable host, not only this agent.
- **Process boundary:** the server is a separate process, which makes it easier to restrict what it can do.


## Transport

A server can talk to its client over standard input/output (a local sub-process) or over HTTP (a network service). Our project uses the local sub-process option, which needs no ports or authentication but only works on one machine. Moving to HTTP would be the step for sharing a server between users, and it would require authentication.


## Design decisions

- Tool descriptions are part of the prompt. Vague descriptions cause wrong tool choices, so they are written carefully and checked by the evaluation script.
- Calculations are done by deterministic code in a tool, not by the model.
- Graph queries are read-only. The SPARQL tool accepts SELECT queries only and rejects update keywords.


## Limitations and challenges

- Small local models can pick the wrong tool or they might over-generalize from a correct result. An evaluation script is the only reliable way to notice this.
- Tool output is untrusted text that goes back into the model's context. A tool that returns content from outside sources could carry instructions, so such tools need filtering before use.
- Each tool call costs model time. On CPU-only hardware, long conversations and large tool outputs slow everything down.
- In the client library version I used, each tool call could open a new server session, which adds startup overhead. This depends on the library and may probably change.
- Tools only: resources and prompts are not used yet.
