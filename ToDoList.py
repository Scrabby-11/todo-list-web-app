import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Get absolute path to the directory containing this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Database Configuration
# Vercel provides POSTGRES_URL. If not available, use local SQLite database.
DATABASE_URL = os.environ.get("POSTGRES_URL")

if DATABASE_URL:
    # SQLAlchemy requires postgresql:// instead of postgres://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(DATABASE_URL)
else:
    # Local fallback
    sqlite_path = os.path.join(BASE_DIR, "tasks.db")
    DATABASE_URL = f"sqlite:///{sqlite_path}"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Model
class TaskModel(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ToDo List API")

# Pydantic Model for validation
class Task(BaseModel):
    title: str

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/api/tasks")
def get_tasks(db: Session = Depends(get_db)):
    tasks = db.query(TaskModel).order_by(TaskModel.id).all()
    return {"tasks": [task.title for task in tasks]}

@app.post("/api/tasks")
def add_task(task: Task, db: Session = Depends(get_db)):
    new_task = TaskModel(title=task.title)
    db.add(new_task)
    db.commit()
    
    # Return updated list
    tasks = db.query(TaskModel).order_by(TaskModel.id).all()
    return {"message": "Task added successfully", "tasks": [t.title for t in tasks]}

@app.delete("/api/tasks/{task_index}")
def delete_task(task_index: int, db: Session = Depends(get_db)):
    # The frontend uses array index, so we delete by fetching ordered tasks
    tasks = db.query(TaskModel).order_by(TaskModel.id).all()
    if 0 <= task_index < len(tasks):
        task_to_delete = tasks[task_index]
        db.delete(task_to_delete)
        db.commit()
        
        updated_tasks = db.query(TaskModel).order_by(TaskModel.id).all()
        return {"message": "Task deleted", "tasks": [t.title for t in updated_tasks]}
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
    threading.Timer(1.5, lambda: webbrowser.open("http://127.0.0.1:8000")).start()
    uvicorn.run("ToDoList:app", host="127.0.0.1", port=8000, reload=True)
