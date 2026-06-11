import pytest 
import sys 
import os 
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) 
from app import app, db 
@pytest.fixture 
def client(): 
    app.config['TESTING'] = True 
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' 
    with app.test_client() as client: 
        with app.app_context(): 
            db.create_all() 
        yield client 

 
def test_health(client):
    """Health endpoint should return 200."""
    response = client.get('/health')
    assert response.status_code == 200

def test_index_loads(client): 
    """Home page should return 200.""" 
    response = client.get('/') 
    assert response.status_code == 200 
 
def test_add_todo(client): 
    """Adding a todo should redirect back to index.""" 
    response = client.post('/add', data={ 
        'title': 'Test Task', 
        'description': 'A test description', 
        'priority': 'high' 
    }) 
    assert response.status_code == 302  # redirect 
 
def test_add_todo_empty_title(client): 
    """Adding a todo with empty title should not crash.""" 
    response = client.post('/add', data={'title': ''}) 
    assert response.status_code == 302