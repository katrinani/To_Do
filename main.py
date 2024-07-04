"""
To-Do приложение:
   Создайте простое веб-приложение для управления задачами.
   Пользователи смогут добавлять, удалять и отмечать задачи как выполненные.

Задачи:
    - Добавление в базу данных задач
    - Удалять задачи из базы данных
    - Редактировать задачи в базе данных
    - Верифицировать поступающие данные
    - Помечать как выполненные задачи
    - Логирование
    - При отметке как выполненные safe-delete

uvicorn main:app --reload
"""
from fastapi import FastAPI, Body, status
import uuid
from typing import Dict, List
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, String
from fastapi.responses import JSONResponse
from pydantic import BaseModel


SQLALCHEMY_DATABASE_URL = "sqlite:///././base/sql_app.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})


class Base(DeclarativeBase):
    pass


class TasksBase(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True)
    header = Column(String)
    description = Column(String)


# создаем таблицы
Base.metadata.create_all(bind=engine)

# создаем сессию подключения к бд
SessionLocal = sessionmaker(autoflush=False, bind=engine)
db = SessionLocal()


app = FastAPI()


@app.post(
    "/api/tasks/new",
    status_code=status.HTTP_201_CREATED,
    tags=["Tasks"],
    summary="Создание новых задач"
)
def create_task(
        header: str = Body(embed=True, min_length=3),
        description: str = Body(embed=True, min_length=3)
):
    """
    Создает задачи, валидирует и закидывает в базу данных
    """
    # добавляем в бд
    task = TasksBase(id=str(uuid.uuid4()), header=header, description=description)
    print(f"Создана задача {task.id}: {task.header}- {task.description}")
    db.add(task)
    db.commit()


class Task(BaseModel):
    id: str
    header: str
    description: str


@app.get(
    "/api/tasks",
    response_model=Dict[str, List[Task]],
    tags=["Tasks"],
    summary="Получение всех актуальных задач",
    response_description="Список всех задач"
)
def get_all_tasks() -> JSONResponse:
    """
    Импорт всех актуальных задач из базы данных
    """
    # запрос в бд
    tasks = db.query(TasksBase).all()
    # создание ответа
    all_tasks = {"tasks": []}
    for task in tasks:
        all_tasks["tasks"].append({
            "id": task.id,
            "header": task.header,
            "description": task.description
            }
        )
    print(all_tasks)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=all_tasks,
        media_type="application/json"
    )
