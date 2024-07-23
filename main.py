from fastapi import FastAPI, Body, status, Path
import uuid
from typing import Dict, List
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, String, Boolean
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
    done = Column(Boolean)


REGEX_UUID = r'[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}'


class Task(BaseModel):
    id: str
    header: str
    description: str


# создаем таблицы
Base.metadata.create_all(bind=engine)

# создаем сессию подключения к бд
SessionLocal = sessionmaker(autoflush=False, bind=engine)
# db = SessionLocal()


app = FastAPI()


@app.post(
    "/api/tasks",
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
    with SessionLocal() as db:
        # добавляем в бд
        task = TasksBase(id=str(uuid.uuid4()), header=header, description=description, done=False)
        print(f"Создана задача {task.id}: {task.header}- {task.description}")
        db.add(task)
        db.commit()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"detail": "Успешное создание"},
            media_type="application/json"
        )


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
    with SessionLocal() as db:
        # запрос в бд
        tasks = db.query(TasksBase).all()
        print(tasks)
        # создание ответа
        all_tasks = {"tasks": []}
        for task in tasks:
            all_tasks["tasks"].append({
                "id": task.id,
                "header": task.header,
                "description": task.description,
                "is_done": task.done
                }
            )
        print(all_tasks)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=all_tasks,
            media_type="application/json"
        )


@app.put(
    "/api/tasks/{id}",
    tags=["Tasks"],
    summary="Изменение конкретной задачи по id"
)
def update_task(
        id: str = Path(pattern=REGEX_UUID),
        header: str = Body(embed=True, min_length=3),
        description: str = Body(embed=True, min_length=3)
):
    """
    Получение по id задачи и изменение данных этой задачи
    """
    with SessionLocal() as db:
        # получение одного объекта по id
        task = db.get(TasksBase, id)
        if not task:
            print("Не найдено задачи с таким id")
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "Не найдено задачи с таким id"},
                media_type="application/json"
            )
        print(f"Получена задача {task.id}: {task.header}- {task.description}")

        # изменениям значения
        task.header = header
        task.description = description

        db.commit()
        print("Успешное изменение")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"detail": "Успешное изменение"},
            media_type="application/json"
        )


@app.delete(
    "/api/tasks/{id}",
    tags=["Tasks"],
    summary="Удаление конкретной задачи по id"
)
def update_task(id: str = Path(pattern=REGEX_UUID)):
    """
    Получение по id задачи и удаление этой задачи
    """
    with SessionLocal() as db:
        # получение одного объекта по id
        task = db.query(TasksBase).filter(TasksBase.id == id).first()
        if not task:
            print("Не найдено задачи с таким id")
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "Не найдено задачи с таким id"},
                media_type="application/json"
            )
        print(f"Получена задача {task.id}: {task.header}- {task.description}")

        # удаляем объект
        db.delete(task)
        db.commit()
        print("Успешное удаление")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"detail": "Успешное удаление"},
            media_type="application/json"
        )
