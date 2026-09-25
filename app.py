import os

from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)

APP_NAME = os.getenv("APP_NAME", "Expense Tracker")
APP_ENV = os.getenv("APP_ENV", "development")
PORT = int(os.getenv("PORT", "5000"))

expenses = []


@app.route("/")
def index():
    total = sum(expense["amount"] for expense in expenses)

    return render_template(
        "index.html",
        app_name=APP_NAME,
        app_env=APP_ENV,
        expenses=expenses,
        total=total,
    )


@app.route("/add", methods=["POST"])
def add_expense():
    description = request.form["description"].strip()
    amount = float(request.form["amount"])
    category = request.form["category"]

    expenses.append(
        {
            "description": description,
            "amount": amount,
            "category": category,
        }
    )

    return redirect(url_for("index"))


@app.route("/delete/<int:index>", methods=["POST"])
def delete_expense(index):
    if 0 <= index < len(expenses):
        expenses.pop(index)

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)