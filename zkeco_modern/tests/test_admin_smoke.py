from django.contrib.auth import get_user_model


def test_admin_login_page(client, db):
    """Create a superuser, log in and verify admin index is reachable."""
    User = get_user_model()
    # create superuser for test
    User.objects.create_superuser(username='admin', email='admin@example.com', password='adminpass')

    login = client.login(username='admin', password='adminpass')
    assert login is True

    response = client.get('/admin/')
    # After login, admin index should be reachable (HTTP 200)
    assert response.status_code == 200
