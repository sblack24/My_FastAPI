from fastapi.testclient import TestClient
from main import app

authors = TestClient(app)

def test_get_autors():
    response = authors.get('http://localhost:8080/author/{id}?author_id=1')
    assert response.status_code == 200
    assert (response.json() ==
                [{"id": 1,
                 "name": "Лев",
                 "surname": "Толстой",
                 "birthday": "28.08.1828 г."
                 }]
            )


if not test_get_autors():
    print("Тест на запрос автора по id пройден")