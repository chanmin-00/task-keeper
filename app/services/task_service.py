from sqlalchemy.orm import Session, selectinload

from app.models import Tag, Task


def list_tasks(db: Session) -> list[Task]:
    # selectinload로 태그를 한 번에 즉시 로딩하여 N+1 쿼리를 방지합니다.
    # 각 할 일의 task.tags에 접근해도 추가 쿼리가 발생하지 않습니다.
    tasks = db.query(Task).options(selectinload(Task.tags)).all()
    return tasks


def get_task(db: Session, task_id: int) -> Task | None:
    return db.query(Task).filter(Task.id == task_id).first()


def create_task(db: Session, title: str, tag_names: list[str]) -> Task:
    tags: list[Tag] = []
    for name in tag_names:
        tag = db.query(Tag).filter(Tag.name == name).first()
        if tag is None:
            tag = Tag(name=name)
            db.add(tag)
        tags.append(tag)

    task = Task(title=title, tags=tags)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task
