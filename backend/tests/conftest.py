from __future__ import annotations

import pytest

from app.db.session import InMemorySession


@pytest.fixture
def session() -> InMemorySession:
    return InMemorySession()