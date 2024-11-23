import pytest
from fastapi.testclient import TestClient
from main import app  # assuming your FastAPI app is in main.py


client = TestClient(app)


# Test for user registration
# def test_register_user():
#     response = client.post(
#         "/tasks/register_user", 
#         data={"name": "Noel", "email": "giosdfs@1234", "password": "password123", "mobile_no": "9510175265"}
#     )
#     assert response.status_code == 200
#     assert "User registered successfully" in response.json()["message"]

headers = {
        "authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxOH0.hpX6F0AT41zRqPg08lAOEdFOw2RiFVUZZdpsJuGqEc8"
    }

# Test for task creation
def test_create_task():
    response = client.post(
        "/tasks/create_task", 
        data={"title": "Test Task", "description": "This is a test task", "status": "To Do", "due_date": "24-11-24"}, headers= headers
    )
    assert response.status_code == 201
    assert "Task created successfully" in response.json()["message"]


# Test for listing tasks
def test_list_tasks():
    response = client.get("tasks/task_list", params= {"status" : "To Do"}, headers= headers)
    assert response.status_code == 200
    assert "Tasks retrieved successfully" in response.json()["message"]


# # Test for task update
# def test_update_task():
#     response = client.patch(
#         "tasks/update_task", 
#         data={"task_id": 8, "title": "Life of pie", "description" : 'finally done', "status": "Done", "due_date": "25-11-24"}, headers= headers
#     )
#     assert response.status_code == 200
#     assert "Task updated successfully" in response.json()["message"]


# Test for task deletion
# def test_delete_task():
#     response = client.delete("tasks/delete_task" , params= {"task_id" : 10}, headers= headers)
#     assert response.status_code == 200
#     assert "Task deleted successfully" in response.json()["message"]
