def test_login_success(client):
    response = client.post('/login', data={
        'username': 'user1',
        'password': 'userpass'
    })
    # Should redirect to dashboard on success
    assert response.status_code == 302
    assert b'/dashboard' in response.data

def test_login_failure(client):
    response = client.post('/login', data={
        'username': 'user1',
        'password': 'wrongpassword'
    })
    # Should not redirect, and should show error
    assert response.status_code == 200
    assert b'Invalid username or password' in response.data

def test_register_success(client):
    response = client.post('/register', data={
        'username': 'newuser',
        'password': 'newpassword',
        'role': 'user'
    })
    # Redirects to login
    assert response.status_code == 302
    
def test_register_duplicate(client):
    response = client.post('/register', data={
        'username': 'user1', # already exists in fixture
        'password': 'somepassword',
        'role': 'user'
    })
    # Should fail and stay on register page
    assert response.status_code == 200
    assert b'Username already exists' in response.data
