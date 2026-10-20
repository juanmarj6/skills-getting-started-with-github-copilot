from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture(autouse=True)
def activities(monkeypatch):
    isolated_activities = deepcopy(app_module.activities)
    monkeypatch.setattr(app_module, "activities", isolated_activities)
    return isolated_activities


@pytest.fixture
def client(activities):
    with TestClient(app_module.app) as test_client:
        yield test_client