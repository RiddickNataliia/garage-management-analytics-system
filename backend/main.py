import os

from fastapi import FastAPI


STUDENT_NAME = os.getenv("STUDENT_NAME", "Student")

app = FastAPI(title=f"Garage Management API - {STUDENT_NAME}")


@app.get("/")
def root():
    return {
        "message": "Garage Management API is running.",
        "student_name": STUDENT_NAME,
    }
