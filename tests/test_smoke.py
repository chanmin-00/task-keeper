from contextlib import contextmanager

from sqlalchemy import event
from sqlalchemy.engine import Engine


@contextmanager
def count_select_queries(engine: Engine):
    selects = []

    def listener(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            selects.append(statement)

    event.listen(engine, "before_cursor_execute", listener)
    try:
        yield selects
    finally:
        event.remove(engine, "before_cursor_execute", listener)


def test_create_and_list(client):
    res = client.post("/tasks", json={"title": "테스트 할 일", "tags": ["개인", "긴급"]})
    assert res.status_code == 201
    body = res.json()
    assert body["title"] == "테스트 할 일"
    assert {t["name"] for t in body["tags"]} == {"개인", "긴급"}

    res = client.get("/tasks")
    assert res.status_code == 200
    tasks = res.json()
    assert len(tasks) == 1
    assert tasks[0]["tags"]


def test_list_tasks_avoids_n_plus_one(client, db_session):
    for i in range(3):
        res = client.post(
            "/tasks", json={"title": f"할 일 {i}", "tags": [f"태그{i}", "공통"]}
        )
        assert res.status_code == 201

    with count_select_queries(db_session.get_bind()) as selects:
        res = client.get("/tasks")

    assert res.status_code == 200
    assert len(res.json()) == 3
    # selectinload: Task 1회 + Tag IN 1회 = 2회. 할 일 수와 무관하게 일정해야 함.
    assert len(selects) == 2, f"N+1 의심: SELECT {len(selects)}회 실행됨\n" + "\n".join(
        selects
    )
