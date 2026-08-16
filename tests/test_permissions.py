import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from core.models import Profile,Project,Role

@pytest.mark.django_db
def test_analyst_can_create_project(client):
    user=User.objects.create_user("analyst",password="pw"); Profile.objects.create(user=user,role=Role.ANALYST); client.force_login(user)
    response=client.post(reverse("project_create"),{"name":"Demo","description":"test"})
    assert response.status_code==302; assert Project.objects.filter(name="Demo").exists()

@pytest.mark.django_db
def test_reviewer_cannot_create_project(client):
    user=User.objects.create_user("reviewer",password="pw"); Profile.objects.create(user=user,role=Role.REVIEWER); client.force_login(user)
    assert client.get(reverse("project_create")).status_code==403

@pytest.mark.django_db
def test_anonymous_redirected(client):
    assert client.get(reverse("dashboard")).status_code==302

