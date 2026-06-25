import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import uuid
import crud
import schemas
from datetime import date


def _make_category(session, name_prefix="Bgt"):
    suffix = uuid.uuid4().hex[:8]
    return crud.create_category(schemas.CategoryCreate(name=f"{name_prefix} {suffix}"), session)


# ── create / upsert ──

def test_upsert_budget_creates_new(session):
    cat = _make_category(session)
    b = crud.upsert_budget(session, cat.id, 200.0)
    assert b.id is not None
    assert b.category_id == cat.id
    assert float(b.amount) == 200.0

def test_upsert_budget_updates_existing(session):
    cat = _make_category(session)
    b1 = crud.upsert_budget(session, cat.id, 100.0)
    b2 = crud.upsert_budget(session, cat.id, 300.0)
    assert b1.id == b2.id
    assert float(b2.amount) == 300.0

def test_upsert_budget_amount_stored_correctly(session):
    cat = _make_category(session)
    crud.upsert_budget(session, cat.id, 49.99)
    session.expire_all()
    budgets = crud.get_budgets(session)
    match = next((b for b in budgets if b.category_id == cat.id), None)
    assert match is not None
    assert abs(float(match.amount) - 49.99) < 0.001


# ── get ──

def test_get_budgets_includes_created(session):
    cat = _make_category(session)
    crud.upsert_budget(session, cat.id, 150.0)
    budgets = crud.get_budgets(session)
    assert any(b.category_id == cat.id for b in budgets)

def test_get_budgets_returns_list(session):
    result = crud.get_budgets(session)
    assert isinstance(result, list)

def test_get_budgets_multiple_categories(session):
    cat_a = _make_category(session, "BgtMulti A")
    cat_b = _make_category(session, "BgtMulti B")
    crud.upsert_budget(session, cat_a.id, 100.0)
    crud.upsert_budget(session, cat_b.id, 200.0)
    budgets = crud.get_budgets(session)
    cat_ids = [b.category_id for b in budgets]
    assert cat_a.id in cat_ids
    assert cat_b.id in cat_ids


# ── delete ──

def test_delete_budget_returns_1(session):
    cat = _make_category(session)
    b = crud.upsert_budget(session, cat.id, 100.0)
    result = crud.delete_budget(session, b.id)
    assert result == 1

def test_delete_budget_removes_from_list(session):
    cat = _make_category(session)
    b = crud.upsert_budget(session, cat.id, 100.0)
    crud.delete_budget(session, b.id)
    budgets = crud.get_budgets(session)
    assert not any(b2.category_id == cat.id for b2 in budgets)

def test_delete_budget_nonexistent_returns_0(session):
    result = crud.delete_budget(session, 999999)
    assert result == 0

def test_delete_budget_does_not_affect_others(session):
    cat_a = _make_category(session, "BgtDel Keep")
    cat_b = _make_category(session, "BgtDel Gone")
    crud.upsert_budget(session, cat_a.id, 100.0)
    b2 = crud.upsert_budget(session, cat_b.id, 200.0)
    crud.delete_budget(session, b2.id)
    budgets = crud.get_budgets(session)
    assert any(b.category_id == cat_a.id for b in budgets)
    assert not any(b.category_id == cat_b.id for b in budgets)


# ── cascade on category delete ──

def test_budget_deleted_when_category_deleted(session):
    cat = _make_category(session, "BgtCascade")
    b = crud.upsert_budget(session, cat.id, 500.0)
    budget_id = b.id
    crud.delete_category(cat.id, session)
    session.expire_all()
    budgets = crud.get_budgets(session)
    assert not any(b2.id == budget_id for b2 in budgets)
