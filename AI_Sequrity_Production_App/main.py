"""Enterprise AI Security & Production RAG Application Launcher.

Usage:
    python main.py          # Starts both FastAPI Backend (8000) and Streamlit UI (8501)
    python main.py --api    # Starts only FastAPI Backend
    python main.py --ui     # Starts only Streamlit UI
"""

import argparse
import os
import subprocess
import sys
import time


def run_api(port: int = 8000, reload: bool = True):
    print(f"🚀 Starting FastAPI Backend on http://localhost:{port} ...")
    cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(port)]
    if reload:
        cmd.append("--reload")
    return subprocess.Popen(cmd)


def run_ui(port: int = 8501):
    print(f"🌐 Starting Streamlit UI on http://localhost:{port} ...")
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "ui/app.py",
        "--server.port",
        str(port),
        "--server.headless",
        "true",
    ]
    return subprocess.Popen(cmd)


def main():
    parser = argparse.ArgumentParser(description="AI Security & RAG Application Runner")
    parser.add_argument("--api", action="store_true", help="Launch FastAPI backend only")
    parser.add_argument("--ui", action="store_true", help="Launch Streamlit UI only")
    parser.add_argument("--port-api", type=int, default=8000, help="Port for FastAPI backend (default: 8000)")
    parser.add_argument("--port-ui", type=int, default=8501, help="Port for Streamlit UI (default: 8501)")
    parser.add_argument("--no-reload", action="store_true", help="Disable FastAPI auto-reload")
    args = parser.parse_args()

    # If neither flag specified, run both
    start_api = args.api or (not args.api and not args.ui)
    start_ui = args.ui or (not args.api and not args.ui)

    processes = []
    try:
        if start_api:
            p_api = run_api(port=args.port_api, reload=not args.no_reload)
            processes.append(p_api)
            time.sleep(1.5)  # Allow backend to bind port before UI connects

        if start_ui:
            p_ui = run_ui(port=args.port_ui)
            processes.append(p_ui)

        print("\n✨ Services running! Press Ctrl+C to terminate all services.")
        for p in processes:
            p.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down services...")
        for p in processes:
            p.terminate()
            p.wait()
        print("✅ All services stopped.")


if __name__ == "__main__":
    main()

