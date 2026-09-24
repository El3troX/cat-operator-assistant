import json
import subprocess
import time
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PYTHON_EXE = BASE_DIR / "venv" / "Scripts" / "python.exe"

def test_live_uvicorn():
    print("=" * 60)
    print("Starting live Uvicorn server test on port 8000...")
    print("=" * 60)

    # Start uvicorn process
    proc = subprocess.Popen(
        [str(PYTHON_EXE), "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=str(BASE_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        # Give server time to bind and start
        print("Waiting for server to become responsive...")
        server_ready = False
        for _ in range(10):
            time.sleep(1.0)
            try:
                with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=2) as resp:
                    if resp.status == 200:
                        server_ready = True
                        break
            except Exception:
                pass

        assert server_ready, "Server failed to start or respond within 10 seconds!"
        print("[PASS] Server successfully bound to http://127.0.0.1:8000")

        # 1. Test GET /health over real TCP HTTP
        with urllib.request.urlopen("http://127.0.0.1:8000/health") as resp:
            status = resp.status
            data = json.loads(resp.read().decode())
            print(f"[PASS] Real HTTP GET /health: status={status}, body={data}")
            assert status == 200
            assert data["status"] == "ok"

        # 2. Test GET /tasks/today
        with urllib.request.urlopen("http://127.0.0.1:8000/tasks/today") as resp:
            status = resp.status
            data = json.loads(resp.read().decode())
            print(f"[PASS] Real HTTP GET /tasks/today: status={status}, returned {len(data)} tasks")
            assert status == 200
            assert len(data) >= 14

        # 3. Test GET /safety/alerts
        with urllib.request.urlopen("http://127.0.0.1:8000/safety/alerts") as resp:
            status = resp.status
            data = json.loads(resp.read().decode())
            print(f"[PASS] Real HTTP GET /safety/alerts: status={status}, returned {len(data)} alerts")
            assert status == 200
            assert len(data) >= 200

        # 4. Test CORS preflight OPTIONS request from React/Vite origin (http://localhost:5173)
        req = urllib.request.Request(
            "http://127.0.0.1:8000/tasks/today",
            method="OPTIONS",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )
        with urllib.request.urlopen(req) as resp:
            status = resp.status
            headers = dict(resp.headers)
            print(f"[PASS] Real HTTP OPTIONS (CORS preflight) status={status}")
            allow_origin = headers.get("access-control-allow-origin") or headers.get("Access-Control-Allow-Origin")
            print(f"[PASS] Access-Control-Allow-Origin header returned: {allow_origin}")
            assert allow_origin in ("*", "http://localhost:5173"), f"Unexpected allow-origin: {allow_origin}"

        print("=" * 60)
        print("LIVE SERVER AND CORS PREFLIGHT VERIFICATION PASSED 100%!")
        print("=" * 60)

    finally:
        print("Shutting down live uvicorn server...")
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
        print("Live server stopped.")

if __name__ == "__main__":
    test_live_uvicorn()
