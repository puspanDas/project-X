"""
PhoneTracer — Start both backend and frontend with one command.
Usage: python run_app.py
"""

import subprocess
import sys
import os
import signal
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT, "backend")
FRONTEND_DIR = os.path.join(ROOT, "frontend")

def main():
    processes = []

    try:
        print("\n🚀 Starting PhoneTracer...\n")

        # Start backend
        print("⚙️  Starting backend (FastAPI) on http://localhost:8000 ...")
        backend = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--port", "8000"],
            cwd=BACKEND_DIR,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
        )
        processes.append(backend)

        time.sleep(1)

        # Start frontend
        print("🖥️  Starting frontend (Vite)  on http://localhost:5173 ...")
        frontend = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=FRONTEND_DIR,
            shell=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
        )
        processes.append(frontend)

        print("\n✅ Both servers running!")
        print("   Frontend → http://localhost:5173")
        print("   Backend  → http://localhost:8000")
        print("\n   Press Ctrl+C to stop both.\n")

        # Wait for either to exit
        while all(p.poll() is None for p in processes):
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")

    finally:
        for p in processes:
            try:
                if os.name == "nt":
                    p.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    p.terminate()
                p.wait(timeout=5)
            except Exception:
                p.kill()

        print("👋 PhoneTracer stopped.\n")


if __name__ == "__main__":
    main()
