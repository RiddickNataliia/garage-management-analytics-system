from __future__ import annotations

import os
import signal
import subprocess
import sys
import time


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(ROOT_DIR, ".env")
ENV_EXAMPLE_PATH = os.path.join(ROOT_DIR, ".env.example")
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")


def _console_script(name: str) -> str:
    """Find CLI tools installed next to the current Python executable."""
    executable = os.path.join(os.path.dirname(sys.executable), name)
    if os.path.exists(executable):
        return executable
    return name


def _load_env_file(path: str) -> dict[str, str]:
    """Read simple KEY=value lines from the root .env file."""
    values: dict[str, str] = {}
    if not os.path.exists(path):
        return values

    with open(path, encoding="utf-8") as handle:
        lines = handle.read().splitlines()

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _build_env() -> dict[str, str]:
    """Merge the system environment, .env values, and safe defaults."""
    env = os.environ.copy()
    env.update(_load_env_file(ENV_PATH))

    env.setdefault("STUDENT_NAME", "Student")
    env.setdefault("BACKEND_HOST", "127.0.0.1")
    env.setdefault("BACKEND_PORT", "8000")
    env.setdefault("FRONTEND_HOST", "127.0.0.1")
    env.setdefault("FRONTEND_PORT", "7860")
    env.setdefault("POSTGRES_USER", "postgres")
    env.setdefault("POSTGRES_PASSWORD", "postgres")
    env.setdefault("POSTGRES_DB", "garage_management")
    env.setdefault("POSTGRES_HOST", "127.0.0.1")
    env.setdefault("POSTGRES_PORT", "5432")
    env.setdefault("ADMINER_PORT", "8080")
    env.setdefault("LAUNCH_POSTGRES_DOCKER", "true")
    env.setdefault(
        "GARAGE_API_BASE_URL",
        f"http://{env['BACKEND_HOST']}:{env['BACKEND_PORT']}",
    )
    env.setdefault("GRADIO_SERVER_NAME", env["FRONTEND_HOST"])
    env.setdefault("GRADIO_SERVER_PORT", env["FRONTEND_PORT"])
    return env


def _require_env_file():
    """Stop early if students forgot to create the required .env file."""
    if os.path.exists(ENV_PATH):
        return

    print("Missing .env file.")
    print("Create it from .env.example and set STUDENT_NAME plus the required ports.")
    sys.exit(1)


def _start_postgres(env: dict[str, str]) -> None:
    """Start the provided PostgreSQL container unless .env disables it."""
    if env.get("LAUNCH_POSTGRES_DOCKER", "true").lower() not in {"1", "true", "yes", "on"}:
        print("Skipping Docker PostgreSQL because LAUNCH_POSTGRES_DOCKER is false.")
        return

    command = [
        "docker",
        "compose",
        "--env-file",
        ENV_PATH,
        "-f",
        os.path.join(BACKEND_DIR, "compose.yaml"),
        "up",
        "-d",
        "db",
    ]
    print("Starting PostgreSQL 18 with Docker Compose...")
    subprocess.run(command, cwd=ROOT_DIR, env=env, check=True)


def _start_processes(env: dict[str, str]) -> list[subprocess.Popen]:
    """Start FastAPI and Gradio in reload mode using the configured ports."""
    backend_command = [
        _console_script("fastapi"),
        "dev",
        os.path.join(BACKEND_DIR, "main.py"),
        "--host",
        env["BACKEND_HOST"],
        "--port",
        env["BACKEND_PORT"],
        "--reload-dir",
        BACKEND_DIR,
    ]
    frontend_command = [
        _console_script("gradio"),
        os.path.join(FRONTEND_DIR, "main.py"),
        "--demo-name",
        "demo",
        "--watch-dirs",
        FRONTEND_DIR,
    ]

    print(f"Starting backend with reload on http://{env['BACKEND_HOST']}:{env['BACKEND_PORT']}")
    backend = subprocess.Popen(backend_command, cwd=ROOT_DIR, env=env)

    print(f"Starting frontend with reload on http://{env['FRONTEND_HOST']}:{env['FRONTEND_PORT']}")
    frontend = subprocess.Popen(frontend_command, cwd=ROOT_DIR, env=env)

    return [backend, frontend]


def _stop_processes(processes: list[subprocess.Popen]) -> None:
    """Stop backend and frontend when the launcher exits."""
    for process in processes:
        if process.poll() is None:
            process.send_signal(signal.SIGTERM)
    for process in processes:
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


def main():
    """Launch the complete local development stack."""
    _require_env_file()
    env = _build_env()
    _start_postgres(env)
    processes = _start_processes(env)

    print("Application is running. Press Ctrl+C to stop backend and frontend.")
    try:
        while True:
            for process in processes:
                if process.poll() is not None:
                    raise RuntimeError(f"A launched process exited with code {process.returncode}.")
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping application...")
    finally:
        _stop_processes(processes)


if __name__ == "__main__":
    main()
