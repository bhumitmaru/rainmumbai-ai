import os
import tempfile

_tmp = tempfile.mkdtemp(prefix="rainmumbai_test_")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["ENV"] = "test"
os.environ["SCHEDULER_ENABLED"] = "false"
os.environ["SECRET_KEY"] = "test-secret-not-for-production"
os.environ["SMTP_ENABLED"] = "false"
os.environ["ADMIN_EMAIL"] = "admin@test.local"
os.environ["ADMIN_PASSWORD"] = "admin-pass-123"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c
