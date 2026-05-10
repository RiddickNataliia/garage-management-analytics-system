import os

import gradio as gr


API_BASE_URL = os.getenv("GARAGE_API_BASE_URL", "http://127.0.0.1:8000")
STUDENT_NAME = os.getenv("STUDENT_NAME", "Student")
FRONTEND_HOST = os.getenv("FRONTEND_HOST", "127.0.0.1")
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "7860"))


with gr.Blocks(title=f"Garage Management - {STUDENT_NAME}") as demo:
    gr.Markdown("# Garage Management")
    gr.Markdown(f"Student: **{STUDENT_NAME}**")
    gr.Markdown(f"Backend API: `{API_BASE_URL}`")


if __name__ == "__main__":
    demo.launch(server_name=FRONTEND_HOST, server_port=FRONTEND_PORT)
