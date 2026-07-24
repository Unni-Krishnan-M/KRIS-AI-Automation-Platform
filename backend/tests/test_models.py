"""Tests for the ORM metadata and base mixins (no database required)."""

from __future__ import annotations

from app.db.base import Base
from app.models import User


def test_users_table_registered_on_metadata() -> None:
    assert "users" in Base.metadata.tables


def test_users_table_has_expected_columns() -> None:
    columns = set(Base.metadata.tables["users"].columns.keys())
    expected = {
        "id",
        "email",
        "hashed_password",
        "full_name",
        "is_active",
        "is_superuser",
        "deleted_at",
        "created_at",
        "updated_at",
    }
    assert expected <= columns


def test_email_column_is_unique_indexed() -> None:
    email = Base.metadata.tables["users"].columns["email"]
    assert email.index is True
    assert email.unique is True


def test_constraint_naming_convention_applied() -> None:
    # Primary key uses the pk_%(table_name)s convention.
    pk = Base.metadata.tables["users"].primary_key
    assert pk.name == "pk_users"


def test_user_repr() -> None:
    user = User(email="a@b.com", hashed_password="x")
    assert "a@b.com" in repr(user)
