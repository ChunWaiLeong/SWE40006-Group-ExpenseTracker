
from decimal import Decimal

import pytest
import app as expense_app


@pytest.fixture(autouse=True)
def reset_expenses():
    """Ensure every test starts with an empty expenses table."""
    with expense_app.app.app_context():
        expense_app.db.session.query(expense_app.Expense).delete()
        expense_app.db.session.commit()

    yield

    with expense_app.app.app_context():
        expense_app.db.session.remove()
        expense_app.db.session.query(expense_app.Expense).delete()
        expense_app.db.session.commit()


@pytest.fixture
def client():
    """Create a Flask test client."""
    expense_app.app.config["TESTING"] = True

    with expense_app.app.test_client() as client:
        yield client


def create_expense(description, amount, category):
    """Insert an expense into the test database."""
    with expense_app.app.app_context():
        expense = expense_app.Expense(
            description=description,
            amount=Decimal(str(amount)),
            category=category,
        )
        expense_app.db.session.add(expense)
        expense_app.db.session.commit()
        return expense.id


def get_expenses():
    """Retrieve all expenses from the test database."""
    with expense_app.app.app_context():
        return expense_app.db.session.execute(
            expense_app.db.select(expense_app.Expense).order_by(
                expense_app.Expense.id
            )
        ).scalars().all()


def test_home_page_loads(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Expense Tracker" in response.data
    assert b"Environment:" in response.data


def test_empty_expense_list_shows_zero_total(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Total Expenses: $0.00" in response.data


def test_add_expense(client):
    response = client.post(
        "/add",
        data={
            "description": "Lunch",
            "amount": "15.50",
            "category": "Food",
        },
    )

    assert response.status_code == 302

    expenses = get_expenses()
    assert len(expenses) == 1
    assert expenses[0].description == "Lunch"
    assert expenses[0].amount == Decimal("15.50")
    assert expenses[0].category == "Food"


def test_added_expense_appears_on_home_page(client):
    client.post(
        "/add",
        data={
            "description": "Bus ticket",
            "amount": "4.20",
            "category": "Transport",
        },
    )

    response = client.get("/")

    assert response.status_code == 200
    assert b"Bus ticket" in response.data
    assert b"Transport" in response.data
    assert b"$4.20" in response.data


def test_total_calculates_multiple_expenses(client):
    client.post(
        "/add",
        data={
            "description": "Lunch",
            "amount": "12.50",
            "category": "Food",
        },
    )

    client.post(
        "/add",
        data={
            "description": "Bus",
            "amount": "3.50",
            "category": "Transport",
        },
    )

    response = client.get("/")

    assert response.status_code == 200
    assert b"Total Expenses: $16.00" in response.data


def test_delete_expense(client):
    lunch_id = create_expense("Lunch", "12.50", "Food")
    create_expense("Bus", "3.50", "Transport")

    response = client.post(f"/delete/{lunch_id}")

    assert response.status_code == 302

    expenses = get_expenses()
    assert len(expenses) == 1
    assert expenses[0].description == "Bus"


def test_total_updates_after_deleting_expense(client):
    lunch_id = create_expense("Lunch", "12.50", "Food")
    create_expense("Bus", "3.50", "Transport")

    client.post(f"/delete/{lunch_id}")
    response = client.get("/")

    assert response.status_code == 200
    assert b"Total Expenses: $3.50" in response.data
    assert b"Lunch" not in response.data
    assert b"Bus" in response.data


def test_delete_invalid_index_does_not_change_expenses(client):
    create_expense("Lunch", "12.50", "Food")

    response = client.post("/delete/999999")

    assert response.status_code == 302

    expenses = get_expenses()
    assert len(expenses) == 1
    assert expenses[0].description == "Lunch"


def test_add_expense_redirects_to_home_page(client):
    response = client.post(
        "/add",
        data={
            "description": "Coffee",
            "amount": "4.00",
            "category": "Food",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/"
