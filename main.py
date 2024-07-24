from fastapi import FastAPI, Body, status, Path
import uuid
import logging
from typing import Dict, List
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, String, Boolean
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class Base(DeclarativeBase):
    pass


class TasksBase(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True)
    header = Column(String)
    description = Column(String)
    done = Column(Boolean)
    is_deleted = Column(Boolean)


REGEX_UUID = r'[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}'


class Task(BaseModel):
    id: str
    header: str
    description: str


# база данных
SQLALCHEMY_DATABASE_URL = "sqlite:///././base/sql_app.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autoflush=False, bind=engine)


app = FastAPI()

# логирование
logging.basicConfig(
    level=logging.INFO,
    filename="logging.log",
    format="%(asctime)s %(levelname)s %(message)s"
)


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
    try:
        with SessionLocal() as db:
            # добавляем в бд
            task = TasksBase(
                id=str(uuid.uuid4()),
                header=header,
                description=description,
                done=False,
                is_deleted=False
            )
            logging.info(f"Создана задача {task.id}: {task.header}- {task.description}")
            db.add(task)
            db.commit()
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"detail": "Успешное создание"},
                media_type="application/json"
            )
    except Exception:
        logging.error(Exception)



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
    try:
        with SessionLocal() as db:
            # запрос в бд
            tasks = db.query(TasksBase).filter(TasksBase.is_deleted == False)
            logging.info(f"Получены задачи: {tasks}")

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

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=all_tasks,
                media_type="application/json"
            )
    except Exception:
        logging.error(Exception)


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
    try:
        with SessionLocal() as db:
            # получение одного объекта по id
            task = db.get(TasksBase, id)
            if not task:
                logging.warning(f"Не найдено задачи с id {id}")

                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"detail": "Не найдено задачи с таким id"},
                    media_type="application/json"
                )
            logging.info(f"Получена задача {task.id}: {task.header}- {task.description}")

            # изменениям значения
            task.header = header
            task.description = description
            db.commit()
            logging.info(f"Успешное изменение задачи по id {id}")

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"detail": "Успешное изменение"},
                media_type="application/json"
            )
    except Exception:
        logging.error(Exception)


@app.delete(
    "/api/tasks/{id}",
    tags=["Tasks"],
    summary="Удаление конкретной задачи по id"
)
def update_task(id: str = Path(pattern=REGEX_UUID)):
    """
    Получение по id задачи и удаление этой задачи
    """
    try:
        with SessionLocal() as db:
            # получение одного объекта по id
            task = db.query(TasksBase).filter(TasksBase.id == id).first()
            if not task:
                logging.warning(f"Не найдено задачи с id {id}")
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"detail": "Не найдено задачи с таким id"},
                    media_type="application/json"
                )
            logging.info(f"Получена задача {task.id}: {task.header}- {task.description}")

            # удаляем объект
            task.is_deleted = True
            db.commit()
            logging.info(f"Успешное удаление задачи по id {id}")

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"detail": "Успешное удаление"},
                media_type="application/json"
            )
    except Exception:
        logging.error(Exception)


@app.put(
    "/api/tasks/{id}/done",
    tags=["Tasks"],
    summary="Указание состояние выполнения задачи по id"
)
def is_done(
        id: str = Path(pattern=REGEX_UUID),
        is_done: bool = Body(embed=True)  # , pattern='true|false'
):
    """
    Получение по id задачи и изменение состояния выполненности этой задачи
    """
    try:
        with SessionLocal() as db:
            # получение одного объекта по id
            task = db.get(TasksBase, id)
            if not task:
                logging.warning(f"Не найдено задачи с id {id}")

                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"detail": "Не найдено задачи с таким id"},
                    media_type="application/json"
                )

            logging.info(f"Получена задача {task.id}: {task.header}- {task.description}")

            if is_done not in [True, False]:
                logging.warning("Значение не является булевым (True/False)")

                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "Значение не является булевым (True/False)"},
                    media_type="application/json"
                )

            # изменениям значения
            task.done = is_done
            db.commit()
            logging.info(f"Успешное изменение задачи по id {id}")

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"detail": "Успешное изменение"},
                media_type="application/json"
            )
    except Exception:
        logging.error(Exception)
