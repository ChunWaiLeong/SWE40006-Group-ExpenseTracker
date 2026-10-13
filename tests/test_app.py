
import pytest

import app as expense_app


@pytest.fixture(autouse=True)
def reset_expenses():
    """Start every test with an empty expense list."""
    expense_app.expenses.clear()
    yield
    expense_app.expenses.clear()


@pytest.fixture
def client():
    """Create a Flask test client."""
    expense_app.app.config["TESTING"] = True

    with expense_app.app.test_client() as client:
        yield client


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
    assert len(expense_app.expenses) == 1
    assert expense_app.expenses[0] == {
        "description": "Lunch",
        "amount": 15.50,
        "category": "Food",
    }


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
    expense_app.expenses.extend([
        {
            "description": "Lunch",
            "amount": 12.50,
            "category": "Food",
        },
        {
            "description": "Bus",
            "amount": 3.50,
            "category": "Transport",
        },
    ])

    response = client.post("/delete/0")

    assert response.status_code == 302
    assert len(expense_app.expenses) == 1
    assert expense_app.expenses[0]["description"] == "Bus"


def test_total_updates_after_deleting_expense(client):
    expense_app.expenses.extend([
        {
            "description": "Lunch",
            "amount": 12.50,
            "category": "Food",
        },
        {
            "description": "Bus",
            "amount": 3.50,
            "category": "Transport",
        },
    ])

    client.post("/delete/0")
    response = client.get("/")

    assert b"Total Expenses: $3.50" in response.data
    assert b"Lunch" not in response.data
    assert b"Bus" in response.data


def test_delete_invalid_index_does_not_change_expenses(client):
    expense_app.expenses.append({
        "description": "Lunch",
        "amount": 12.50,
        "category": "Food",
    })

    response = client.post("/delete/99")

    assert response.status_code == 302
    assert len(expense_app.expenses) == 1
    assert expense_app.expenses[0]["description"] == "Lunch"


def test_add_expense_redirects_to_home_page(client):
    response = client.post(
        "/add",
        data={
            "description": "Coffee",
            "amount": "4.00",
            "category": "Food",
        },
    )

    assert response.headers["Location"] == "/"
