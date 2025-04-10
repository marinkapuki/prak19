from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from fastapi.testclient import TestClient
import pytest

app = FastAPI()

db = []  # простая бд 

class User(BaseModel):
    id: int
    name: str

@app.post("/register/", response_model=User)
def register_user(user: User):
    if any(u.id == user.id for u in db):
        raise HTTPException(status_code=400, detail="User ID already exists")
    db.append(user)
    return user

@app.get("/users/", response_model=List[User])
def get_users():
    return db

@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    global db
    db = [u for u in db if u.id != user_id]
    return {"message": "User deleted"}

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_and_teardown():
    global db
    db.clear()
    yield

# тест регистрации 
def test_register_user():
    response = client.post("/register/", json={"id": 1, "name": "Alice"})
    assert response.status_code == 200
    assert response.json() == {"id": 1, "name": "Alice"}

# тест получения
def test_get_users():
    client.post("/register/", json={"id": 1, "name": "Alice"})
    response = client.get("/users/")
    assert response.status_code == 200
    assert len(response.json()) == 1

# тест удаления 
def test_delete_user():
    client.post("/register/", json={"id": 1, "name": "Alice"})
    response = client.delete("/users/1")
    assert response.status_code == 200
    assert response.json() == {"message": "User deleted"}
    response = client.get("/users/")
    assert len(response.json()) == 0

# тест на попытку регистрации пользователя с существующим ID
def test_register_existing_user():
    client.post("/register/", json={"id": 1, "name": "Alice"})
    response = client.post("/register/", json={"id": 1, "name": "Bob"})
    assert response.status_code == 400
    assert response.json()["detail"] == "User ID already exists"