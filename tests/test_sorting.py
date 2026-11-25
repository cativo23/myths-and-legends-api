"""Tests for the shared list-sorting helper and its use by the base service."""
from fastapi_pagination import Params
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.common.sorting import apply_sort
from app.api.v1.domains.users.models.user import User
from app.api.v1.domains.users.services.user import user as user_service


def _add_users(db: Session, rows: list[tuple[str, str | None]]) -> None:
    for email, full_name in rows:
        db.add(User(email=email, hashed_password="x", full_name=full_name))
    db.commit()


def _emails(db: Session, order: str, sort: str = "full_name") -> list[str]:
    stmt = apply_sort(select(User), User, sort, order)
    return [u.email for u in db.execute(stmt).scalars().all()]


class TestApplySort:
    def test_should_order_ascending_and_descending(self, db: Session):
        _add_users(db, [("b@x.com", "B"), ("a@x.com", "A"), ("c@x.com", "C")])

        assert _emails(db, "asc") == ["a@x.com", "b@x.com", "c@x.com"]
        assert _emails(db, "desc") == ["c@x.com", "b@x.com", "a@x.com"]

    def test_should_break_ties_by_id(self, db: Session):
        # Same full_name: insertion (id) order must win in both directions.
        _add_users(db, [("z@x.com", "Same"), ("a@x.com", "Same"), ("m@x.com", "Same")])

        assert _emails(db, "asc") == ["z@x.com", "a@x.com", "m@x.com"]
        assert _emails(db, "desc") == ["z@x.com", "a@x.com", "m@x.com"]

    def test_should_list_nulls_last_in_both_directions(self, db: Session):
        # Postgres and SQLite disagree on NULL position by default; the helper
        # must make them agree (tests run on SQLite, production on Postgres).
        _add_users(db, [("n@x.com", None), ("b@x.com", "B"), ("a@x.com", "A")])

        assert _emails(db, "asc") == ["a@x.com", "b@x.com", "n@x.com"]
        assert _emails(db, "desc") == ["b@x.com", "a@x.com", "n@x.com"]


class TestBaseServiceOrdering:
    def test_should_keep_id_order_by_default(self, db: Session):
        _add_users(db, [("b@x.com", "B"), ("a@x.com", "A")])

        page = user_service.get_all(db, params=Params(page=1, size=50))
        assert [u.email for u in page.items] == ["b@x.com", "a@x.com"]

    def test_should_apply_requested_sort(self, db: Session):
        _add_users(db, [("b@x.com", "B"), ("a@x.com", "A")])

        page = user_service.get_all(
            db, params=Params(page=1, size=50), sort="email", order="asc"
        )
        assert [u.email for u in page.items] == ["a@x.com", "b@x.com"]
