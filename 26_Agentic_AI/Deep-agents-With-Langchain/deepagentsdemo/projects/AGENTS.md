# Agents.md — Deep Agents Context File

> This file is loaded into the deep agent's context (via its file system tools)
> whenever the agent is invoked. It gives the agent background knowledge about
> its own architecture, the project conventions, and how it should operate.

---

## 1. What is a Deep Agent?

A **deep agent** is an agent designed for complex, multi-step, long-horizon
tasks. Unlike a simple tool-calling loop (LLM → tool → LLM → answer), a deep
agent is built on **LangGraph** and ships with four architectural pillars,
inspired by applications like Claude Code, Deep Research, and Manus:

1. **Planning** — an explicit todo-list tool the agent uses to break a task
   into steps and track progress.
2. **File System (Context Offloading)** — virtual file tools so the agent can
   store large intermediate results outside the chat context window.
3. **Subagents** — the ability to spawn specialized child agents with their
   own isolated context, tools, and prompts.
4. **Detailed System Prompt** — a long, carefully engineered prompt that
   teaches the agent *when* and *how* to use the capabilities above.

---

## 2. Architecture Overview

```
                    ┌─────────────────────────────┐
                    │        Deep Agent           │
                    │  (create_deep_agent, on     │
                    │   top of LangGraph)         │
                    └──────────┬──────────────────┘
                               │
        ┌──────────────┬───────┴───────┬──────────────────┐
        ▼              ▼               ▼                  ▼
  ┌───────────┐  ┌───────────┐  ┌─────────────┐   ┌─────────────┐
  │ Planning  │  │ File      │  │ Subagents   │   │ Custom      │
  │ tool      │  │ system    │  │ (task tool) │   │ tools       │
  │ write_    │  │ ls, read_ │  │ isolated    │   │ e.g. web    │
  │ todos     │  │ file,     │  │ context per │   │ search      │
  │           │  │ write_    │  │ subagent    │   │ (Tavily)    │
  │           │  │ file,     │  │             │   │             │
  │           │  │ edit_file │  │             │   │             │
  └───────────┘  └───────────┘  └─────────────┘   └─────────────┘
```

### 2.1 Planning (`write_todos`)

- The agent maintains a structured todo list: each item has a status
  (`pending`, `in_progress`, `completed`).
- Plans are written **before** starting multi-step work and updated as steps
  finish. This keeps the agent on track over long horizons and makes its
  progress visible.

### 2.2 File System Tools (`ls`, `read_file`, `write_file`, `edit_file`)

- These operate on a **virtual file system stored in the LangGraph state**
  (not necessarily the real disk), so large tool outputs, research notes, and
  drafts can be *offloaded* out of the context window.
- **Context engineering rule:** anything bulky (search results, scraped
  pages, long drafts) should be written to a file and only summarized in the
  conversation. Re-read files when details are needed again.
- Files like this one (`Agents.md`) can be pre-loaded into state at
  invocation time to give the agent standing instructions and domain context.

### 2.3 Subagents (`task` tool)

- The main agent can delegate a self-contained chunk of work to a subagent.
- Each subagent gets a **fresh, isolated context window** — this prevents
  context pollution of the parent and enables parallel exploration.
- Subagents are defined with: `name`, `description` (used by the parent to
  decide when to delegate), `prompt`, and an optional restricted `tools` list.
- Only the subagent's **final answer** flows back to the parent.

### 2.4 System Prompt

- The default deep-agent system prompt is long and detailed, modeled after
  Claude Code's prompt. It contains instructions for planning, file usage,
  and delegation.
- Project-specific behavior is added via the `system_prompt` parameter of
  `create_deep_agent` and via context files like this one.

---

## 3. How This Project Builds Deep Agents

```python
from langchain.chat_models import init_chat_model
from deepagents import create_deep_agent

model = init_chat_model(...)          # e.g. an Anthropic / OpenAI chat model

agent = create_deep_agent(
    model=model,
    tools=[internet_search],          # custom tools (e.g. Tavily web search)
    system_prompt="...",              # project-specific instructions
    subagents=[...],                  # optional specialized subagents
)

result = agent.invoke({"messages": [{"role": "user", "content": "..."}]})
```

- Environment/config (API keys for the model provider, Tavily, etc.) is
  loaded from `.env` via `python-dotenv`.
- Web research is done with the **Tavily** client wrapped as a custom tool.

---

## 4. Operating Guidelines for the Agent

When you (the deep agent) are invoked and this file is in your context:

1. **Plan first.** For any task with more than ~2 steps, call `write_todos`
   before doing work, and keep statuses updated.
2. **Offload aggressively.** Write raw research output and long drafts to
   files; keep the conversation lean.
3. **Delegate wisely.** Use subagents for deep-dive research or independent
   subtasks; give them a crisp, self-contained instruction.
4. **One source of truth.** Treat this `Agents.md` as the authoritative
   description of your own architecture and conventions — prefer it over
   assumptions.
5. **Final answers** should synthesize from your files/notes, cite sources
   when research was involved, and be concise.
