import os
import subprocess
import uvicorn
from dotenv import load_dotenv

load_dotenv()

def main():
    launch_docker = os.getenv("LAUNCH_POSTGRES_DOCKER", "false").lower() == "true"

    if launch_docker:
        compose_path = os.path.join("backend", "compose.yaml")
        subprocess.run(["docker", "compose", "-f", compose_path, "up", "-d"], check=True)

    backend_host = os.getenv("BACKEND_HOST", "127.0.0.1")
    backend_port = int(os.getenv("BACKEND_PORT", "8000"))

    uvicorn.run("backend.main:app", host=backend_host, port=backend_port, reload=True)

if __name__ == "__main__":
    main()