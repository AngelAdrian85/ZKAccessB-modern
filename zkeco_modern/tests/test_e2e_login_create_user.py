import pytest
from django.test import Client
from django.contrib.auth import get_user_model


@pytest.mark.django_db
def test_admin_login_and_access_admin_site():
    """Create a superuser in the test database, log in and access /admin/"""
    User = get_user_model()
    # create a superuser in the test database
    User.objects.create_superuser('ci_admin', 'ci@example.com', 'AdminPass123')

    client = Client()
    assert client.login(username='ci_admin', password='AdminPass123')

    resp = client.get('/admin/')
    # After successful login the admin index should be accessible (200)
    assert resp.status_code == 200
