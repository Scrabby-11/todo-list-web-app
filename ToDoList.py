import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List

# Get absolute path to the directory containing this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="ToDo List API")

FILENAME = os.path.join(BASE_DIR, "tasks.txt")

class Task(BaseModel):
    title: str

def load_tasks() -> List[str]:
    try:
        with open(FILENAME, 'r') as file:
            tasks = [line.strip() for line in file.readlines() if line.strip()]
    except FileNotFoundError:
        tasks = []
    return tasks

def save_tasks(tasks: List[str]):
    with open(FILENAME, 'w') as file:
        for task in tasks:
            file.write(task + "\n")

@app.get("/api/tasks")
def get_tasks():
    tasks = load_tasks()
    return {"tasks": tasks}

@app.post("/api/tasks")
def add_task(task: Task):
    tasks = load_tasks()
    tasks.append(task.title)
    save_tasks(tasks)
    return {"message": "Task added successfully", "tasks": tasks}

@app.delete("/api/tasks/{task_index}")
def delete_task(task_index: int):
    tasks = load_tasks()
    if 0 <= task_index < len(tasks):
        removed_task = tasks.pop(task_index)
        save_tasks(tasks)
        return {"message": f"Task '{removed_task}' deleted", "tasks": tasks}
    else:
        raise HTTPException(status_code=404, detail="Invalid task index")

@app.get("/")
def read_root():
    index_path = os.path.join(BASE_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Frontend not found"}

@app.get("/{filename}")
def serve_file(filename: str):
    allowed_files = ["style.css", "script.js"]
    if filename in allowed_files:
        file_path = os.path.join(BASE_DIR, filename)
        if os.path.exists(file_path):
            return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="File not found")

if __name__ == "__main__":
    import uvicorn
    import webbrowser
    import threading

    # Change working directory to the script's directory so uvicorn can find the module
    os.chdir(BASE_DIR)
    
    print("Starting server at http://127.0.0.1:8000")
    # Automatically open the browser after a 1.5 second delay to let the server start
    threading.Timer(1.5, lambda: webbrowser.open("http://127.0.0.1:8000")).start()
    
    uvicorn.run("ToDoList:app", host="127.0.0.1", port=8000, reload=True)
