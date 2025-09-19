from __future__ import annotations

from collections import defaultdict
from contextlib import contextmanager
from typing import Any, Dict, Iterable, List, Optional, Type, TypeVar

from app.models import (
    Assignment,
    CallRule,
    CoverageRequirement,
    FairnessTarget,
    Holiday,
    Provider,
    ScheduleBlock,
    SiteHospital,
    SiteOffice,
    VacationAllowance,
    VacationRequest,
    SolveRun,
)

T = TypeVar("T")


class InMemorySession:
    def __init__(self) -> None:
        self._store: Dict[Type[Any], List[Any]] = defaultdict(list)
        self._id_counters: Dict[Type[Any], int] = defaultdict(int)
        self._pending: List[Any] = []

    def add(self, instance: Any) -> None:
        if getattr(instance, "id", 0) in (0, None):
            self._id_counters[type(instance)] += 1
            instance.id = self._id_counters[type(instance)]
        self._store[type(instance)].append(instance)

    def add_all(self, instances: Iterable[Any]) -> None:
        for instance in instances:
            self.add(instance)

    def commit(self) -> None:
        return None

    def rollback(self) -> None:
        return None

    def close(self) -> None:
        return None

    def flush(self) -> None:
        return None

    def refresh(self, instance: Any) -> None:
        return None

    def get(self, model: Type[T], instance_id: int) -> Optional[T]:
        for obj in self._store.get(model, []):
            if getattr(obj, "id", None) == instance_id:
                return obj
        return None

    def all(self, model: Type[T]) -> List[T]:
        return list(self._store.get(model, []))

    def filter(self, model: Type[T], predicate) -> List[T]:
        return [obj for obj in self._store.get(model, []) if predicate(obj)]


@contextmanager
def get_session() -> Iterable[InMemorySession]:
    session = InMemorySession()
    try:
        yield session
    finally:
        session.close()


def init_db_sync() -> None:  # Compatibility placeholder
    return None