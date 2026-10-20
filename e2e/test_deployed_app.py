"""End to end acceptance tests.

These drive a real browser against a deployed environment, unlike the
tests in tests/ which call the app in memory with no server running.

Target environment is set with the BASE_URL environment variable.
"""

import os
import time
import uuid

import pytest
import requests

BASE_URL = os.environ.get("BASE_URL", "http://3.104.55.176").rstrip("/")
EXPECTED_ENV = os.environ.get("EXPECTED_ENV", "")


def read_total(page):
    """Pull the number out of 'Total Expenses: $16.00'."""
    text = page.locator(".total").inner_text()
    return float(text.split("$")[1].strip())


def add_expense(page, description, amount, category="Food"):
    page.goto(BASE_URL + "/")
    page.fill("input[name='description']", description)
    page.fill("input[name='amount']", str(amount))
    page.select_option("select[name='category']", category)
    page.click("button:has-text('Add Expense')")
    page.wait_for_load_state()


def delete_expense(page, description):
    page.goto(BASE_URL + "/")
    row = page.locator("tr").filter(has_text=description)
    row.locator("button:has-text('Delete')").click()
    page.wait_for_load_state()


@pytest.fixture(scope="session", autouse=True)
def environment_is_up():
    """Fail with a clear message if the environment never comes up."""
    deadline = time.time() + 60
    last = "no response"

    while time.time() < deadline:
        try:
            response = requests.get(BASE_URL + "/health", timeout=5)
            if response.status_code == 200:
                return
            last = "status %s, body %s" % (
                response.status_code, response.text[:200]
            )
        except Exception as error:
            last = str(error)

        time.sleep(5)

    pytest.fail(
        "%s/health never became healthy within 60s. Last result: %s"
        % (BASE_URL, last)
    )


@pytest.fixture
def description():
    """Unique per test so concurrent runs never collide in the database."""
    return "e2e-" + uuid.uuid4().hex[:8]


def test_health_endpoint_reports_database_connected():
    response = requests.get(BASE_URL + "/health", timeout=10)

    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "connected"


def test_home_page_loads(page):
    page.goto(BASE_URL + "/")

    assert page.locator("h1").inner_text() == "Expense Tracker"
    assert "Environment:" in page.locator(".environment").inner_text()


def test_environment_label_matches_expected(page):
    if not EXPECTED_ENV:
        pytest.skip("EXPECTED_ENV not set")

    page.goto(BASE_URL + "/")

    assert EXPECTED_ENV in page.locator(".environment").inner_text()


def test_adding_an_expense_shows_it_and_updates_the_total(page, description):
    page.goto(BASE_URL + "/")
    before = read_total(page)

    add_expense(page, description, "12.50", "Food")

    assert page.locator("tr").filter(has_text=description).count() == 1
    assert read_total(page) == pytest.approx(before + 12.50, abs=0.01)

    delete_expense(page, description)


def test_deleting_an_expense_removes_it_and_updates_the_total(page, description):
    page.goto(BASE_URL + "/")
    before = read_total(page)

    add_expense(page, description, "7.25", "Transport")
    assert read_total(page) == pytest.approx(before + 7.25, abs=0.01)

    delete_expense(page, description)

    assert page.locator("tr").filter(has_text=description).count() == 0
    assert read_total(page) == pytest.approx(before, abs=0.01)


def test_category_is_saved_with_the_expense(page, description):
    add_expense(page, description, "3.00", "Entertainment")

    row = page.locator("tr").filter(has_text=description)
    assert "Entertainment" in row.inner_text()

    delete_expense(page, description)
