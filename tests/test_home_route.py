from main import app


def test_home_route():
    response = app.test_client().get("/")
    assert response.status_code == 200
    assert 'Index.html' in response.data



# test_home_route()