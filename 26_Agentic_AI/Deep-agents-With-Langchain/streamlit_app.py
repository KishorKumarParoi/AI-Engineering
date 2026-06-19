"""
Deep Agents Chatbot — Streamlit app
====================================
A conversational chatbot built on the `deepagents` library that demonstrates
EVERY feature covered in the deepagentsdemo notebooks:

1-basicsdeepagent.ipynb   -> create_deep_agent, custom model, custom system
                             prompt, custom tools (Tavily web search),
                             built-in planning (write_todos) + virtual files
2-contextengineering.ipynb -> AGENTS.md context file, memory=, checkpointer +
                             thread_id conversation memory, Skills (/skills/)
3-backends.ipynb          -> StateBackend / FilesystemBackend / StoreBackend
4-subagents.ipynb         -> custom subagents (research-agent) + structured
                             output subagent (Pydantic response_format)

Run with:  streamlit run streamlit_app.py
"""

import os
import uuid
from pathlib import Path
from typing import Literal

import streamlit as st
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Environment (notebook 1: load API keys from .env)
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).parent
DEMO_DIR = ROOT_DIR / "deepagentsdemo"

load_dotenv(ROOT_DIR / ".env")

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend, StateBackend, StoreBackend
from deepagents.backends.utils import create_file_data
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from tavily import TavilyClient

# ---------------------------------------------------------------------------
# Custom tool (notebook 1: Tavily internet search)
# ---------------------------------------------------------------------------
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """Run a web search"""
    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )


# ---------------------------------------------------------------------------
# Structured output schema (notebook 4: structured output with subagents)
# ---------------------------------------------------------------------------
class ResearchFindings(BaseModel):
    """Structured findings from a research task."""

    summary: str = Field(description="Summary of findings")
    confidence: float = Field(description="Confidence score from 0 to 1")
    sources: list[str] = Field(description="List of source URLs")


# ---------------------------------------------------------------------------
# Context engineering helpers (notebook 2: AGENTS.md + skills seeding)
# ---------------------------------------------------------------------------
def load_agents_md() -> str:
    path = DEMO_DIR / "projects" / "AGENTS.md"
    return path.read_text(encoding="utf-8") if path.exists() else ""


def load_skill_seed_files() -> dict:
    """Read every file under deepagentsdemo/skills/ and convert it to in-state
    file data so the StateBackend agent can discover and read skills."""
    files = {}
    skills_root = DEMO_DIR / "skills"
    if skills_root.exists():
        for f in skills_root.rglob("*.md"):
            virtual = "/skills/" + f.relative_to(skills_root).as_posix()
            files[virtual] = create_file_data(f.read_text(encoding="utf-8"))
    return files


# ---------------------------------------------------------------------------
# Agent factory — assembles ALL the features based on sidebar config
# ---------------------------------------------------------------------------
DEFAULT_SYSTEM_PROMPT = (
    "You are an expert AI assistant and researcher. You conduct thorough "
    "research using your internet_search tool when needed, plan multi-step "
    "work with write_todos, offload bulky content to files, use your skills "
    "when a query matches one, and delegate deep-dive research to your "
    "subagents. Always cite sources when research was involved."
)

SUBAGENT_DOC = """
- **research-agent** — in-depth research with web search (context quarantine)
- **structured-researcher** — returns `ResearchFindings` (summary, confidence, sources)
"""


def build_agent(cfg: dict):
    """Create a deep agent wired up according to the sidebar configuration."""
    seed_files = {}

    # --- backend selection (notebook 3) -----------------------------------
    if cfg["backend"] == "StateBackend (in-state, per thread)":
        backend = StateBackend()
        # StateBackend has no disk access -> seed AGENTS.md + skills into state
        if cfg["use_agents_md"]:
            seed_files["/projects/AGENTS.md"] = create_file_data(load_agents_md())
        if cfg["use_skills"]:
            seed_files.update(load_skill_seed_files())
        memory_paths = ["/projects/AGENTS.md"] if cfg["use_agents_md"] else None

    elif cfg["backend"] == "FilesystemBackend (real disk)":
        # virtual_mode=True confines the agent inside deepagentsdemo/
        backend = FilesystemBackend(root_dir=str(DEMO_DIR), virtual_mode=True)
        # AGENTS.md and skills/ already exist on disk — nothing to seed
        memory_paths = ["/projects/AGENTS.md"] if cfg["use_agents_md"] else None

    else:  # StoreBackend (cross-thread memory)
        store = st.session_state.store
        backend = StoreBackend(store=store, namespace=lambda rt: ("memories",))
        # Seed durable memory into the store once per session
        if not st.session_state.get("store_seeded"):
            if cfg["use_agents_md"]:
                store.put(("memories",), "/projects/AGENTS.md",
                          create_file_data(load_agents_md()))
            if cfg["use_skills"]:
                for path, data in load_skill_seed_files().items():
                    store.put(("memories",), path, data)
            st.session_state.store_seeded = True
        memory_paths = ["/projects/AGENTS.md"] if cfg["use_agents_md"] else None

    # --- subagents (notebook 4) --------------------------------------------
    subagents = []
    if cfg["use_subagents"]:
        subagents.append({
            "name": "research-agent",
            "description": "Used to research more in depth questions",
            "system_prompt": "You are a great researcher. Research thoroughly "
                             "and cite your sources.",
            "tools": [internet_search],
        })
        subagents.append({
            "name": "structured-researcher",
            "description": "Researches topics and returns structured findings "
                           "(summary, confidence score, source URLs)",
            "system_prompt": "Research the given topic thoroughly. "
                             "Return your findings.",
            "tools": [internet_search],
            "response_format": ResearchFindings,
        })

    # --- assemble the deep agent --------------------------------------------
    kwargs = dict(
        model=cfg["model"],
        tools=[internet_search],
        system_prompt=cfg["system_prompt"],
        backend=backend,
        checkpointer=st.session_state.checkpointer,  # notebook 2: thread memory
    )
    if subagents:
        kwargs["subagents"] = subagents
    if cfg["use_skills"]:
        kwargs["skills"] = ["/skills/"]  # notebook 2: Agent Skills
    if memory_paths:
        kwargs["memory"] = memory_paths  # notebook 2: memory= context loading
    if cfg["backend"].startswith("StoreBackend"):
        kwargs["store"] = st.session_state.store

    return create_deep_agent(**kwargs), seed_files


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------
def extract_text(content) -> str:
    """AIMessage.content may be a plain string or a list of content blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts)
    return str(content)


def render_steps(messages):
    """Show the agent's intermediate work: tool calls, todos, subagent tasks."""
    for msg in messages:
        msg_type = getattr(msg, "type", "")
        if msg_type == "ai" and getattr(msg, "tool_calls", None):
            for tc in msg.tool_calls:
                name, args = tc["name"], tc["args"]
                if name == "write_todos":
                    with st.expander("📋 Planning — write_todos", expanded=False):
                        for todo in args.get("todos", []):
                            icon = {"pending": "⬜", "in_progress": "🔄",
                                    "completed": "✅"}.get(todo.get("status"), "⬜")
                            st.markdown(f"{icon} {todo.get('content', todo)}")
                elif name == "task":
                    with st.expander(
                        f"🤖 Subagent — {args.get('subagent_type', 'task')}",
                        expanded=False,
                    ):
                        st.markdown(args.get("description", ""))
                elif name == "internet_search":
                    with st.expander(
                        f"🔎 Web search — “{args.get('query', '')}”", expanded=False
                    ):
                        st.json(args)
                elif name in ("write_file", "edit_file", "read_file", "ls",
                              "glob", "grep"):
                    label = args.get("file_path") or args.get("path") or ""
                    with st.expander(f"📁 File system — {name} {label}",
                                     expanded=False):
                        st.json(args)
                else:
                    with st.expander(f"🛠️ Tool — {name}", expanded=False):
                        st.json(args)
        elif msg_type == "tool":
            text = extract_text(msg.content)
            if len(text) > 700:
                text = text[:700] + " …(truncated)"
            with st.expander(f"↩️ Result — {getattr(msg, 'name', 'tool')}",
                             expanded=False):
                st.code(text)


def render_files(files: dict):
    if not files:
        return
    with st.expander(f"🗂️ Virtual files in state ({len(files)})", expanded=False):
        for path, data in files.items():
            content = data.get("content", "") if isinstance(data, dict) else str(data)
            st.markdown(f"**`{path}`**")
            st.code(content[:1500] + (" …(truncated)" if len(content) > 1500 else ""))


# ---------------------------------------------------------------------------
# Streamlit app
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Deep Agents Chatbot", page_icon="🧠", layout="wide")
st.title("🧠 Deep Agents Chatbot")
st.caption(
    "Planning • Virtual file system • Context engineering (AGENTS.md + memory) • "
    "Skills • Subagents (incl. structured output) • Swappable backends • "
    "Thread memory via checkpointer"
)

# --- session state init ------------------------------------------------------
if "checkpointer" not in st.session_state:
    st.session_state.checkpointer = MemorySaver()
if "store" not in st.session_state:
    st.session_state.store = InMemoryStore()
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "history" not in st.session_state:
    st.session_state.history = []  # [(role, text, steps_messages, files)]

# --- sidebar configuration ---------------------------------------------------
with st.sidebar:
    st.header("⚙️ Agent configuration")

    model = st.selectbox(
        "Model",
        [
            "openai:gpt-5.4",
            "openai:gpt-5.5",
            "openai:gpt-4.1",
            "groq:qwen/qwen3-32b",
        ],
        index=0,
        help="Notebook 1: customizing the deep agent's model "
             "(init_chat_model-style provider:model strings).",
    )

    backend = st.radio(
        "Backend (where files/memory live)",
        [
            "StateBackend (in-state, per thread)",
            "FilesystemBackend (real disk)",
            "StoreBackend (cross-thread store)",
        ],
        help="Notebook 3: StateBackend = ephemeral per-thread; "
             "FilesystemBackend = real files under deepagentsdemo/; "
             "StoreBackend = survives across threads via a LangGraph store.",
    )

    st.subheader("Features")
    use_agents_md = st.checkbox(
        "Load AGENTS.md context (memory=)", value=True,
        help="Notebook 2: durable 'who you are' context from projects/AGENTS.md",
    )
    use_skills = st.checkbox(
        "Skills (/skills/)", value=True,
        help="Notebook 2: langgraph, python, aws, report-writer skills",
    )
    use_subagents = st.checkbox(
        "Subagents", value=True,
        help="Notebook 4: research-agent + structured-output researcher",
    )
    if use_subagents:
        st.markdown(SUBAGENT_DOC)

    system_prompt = st.text_area(
        "System prompt", DEFAULT_SYSTEM_PROMPT, height=160,
        help="Notebook 1 & 2: custom system prompt layered on the built-in "
             "Claude-Code-style deep agent prompt.",
    )

    st.divider()
    st.caption(f"🧵 Thread: `{st.session_state.thread_id[:8]}…`")
    col1, col2 = st.columns(2)
    if col1.button("🆕 New thread", use_container_width=True,
                   help="Same agent + store, fresh conversation. With "
                        "StoreBackend, files written earlier are still there!"):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.history = []
        st.rerun()
    if col2.button("🗑️ Reset all", use_container_width=True,
                   help="Wipe checkpointer, store, and chat."):
        for k in ("checkpointer", "store", "store_seeded", "thread_id", "history"):
            st.session_state.pop(k, None)
        st.rerun()

    # missing-key warnings
    if model.startswith("groq") and not os.getenv("GROQ_API_KEY"):
        st.error("GROQ_API_KEY missing from .env")
    if model.startswith("openai") and not os.getenv("OPENAI_API_KEY"):
        st.error("OPENAI_API_KEY missing from .env")
    if not os.getenv("TAVILY_API_KEY"):
        st.warning("TAVILY_API_KEY missing — web search will fail")

cfg = {
    "model": model,
    "backend": backend,
    "use_agents_md": use_agents_md,
    "use_skills": use_skills,
    "use_subagents": use_subagents,
    "system_prompt": system_prompt,
}

# Rebuild the agent only when the configuration changes
cfg_key = str(sorted(cfg.items()))
if st.session_state.get("cfg_key") != cfg_key:
    st.session_state.agent, st.session_state.seed_files = build_agent(cfg)
    st.session_state.cfg_key = cfg_key

# --- replay chat history -----------------------------------------------------
for role, text, steps, files in st.session_state.history:
    with st.chat_message(role):
        if steps:
            render_steps(steps)
        st.markdown(text)
        if files:
            render_files(files)

# --- chat input / agent invocation -------------------------------------------
if prompt := st.chat_input("Ask me anything — research, code, AWS, LangGraph…"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.history.append(("user", prompt, None, None))

    payload = {"messages": [{"role": "user", "content": prompt}]}
    # StateBackend: seed AGENTS.md + skills into this thread's virtual FS
    if st.session_state.seed_files:
        payload["files"] = st.session_state.seed_files

    config = {"configurable": {"thread_id": st.session_state.thread_id},
              "recursion_limit": 100}

    with st.chat_message("assistant"):
        with st.spinner("🧠 Deep agent planning, researching, delegating…"):
            try:
                result = st.session_state.agent.invoke(payload, config=config)
            except Exception as e:
                st.error(f"Agent error: {e}")
                st.stop()

        # Only render the messages generated for THIS turn
        all_msgs = result["messages"]
        turn_start = max(
            (i for i, m in enumerate(all_msgs)
             if getattr(m, "type", "") == "human"),
            default=0,
        )
        new_msgs = all_msgs[turn_start + 1:]

        render_steps(new_msgs)
        answer = extract_text(all_msgs[-1].content) or "*(no text response)*"
        st.markdown(answer)

        # Virtual files (StateBackend) — notebook 3 backend check
        files = {
            p: d for p, d in result.get("files", {}).items()
            if p not in st.session_state.seed_files
        }
        render_files(files)

    st.session_state.history.append(("assistant", answer, new_msgs, files))
