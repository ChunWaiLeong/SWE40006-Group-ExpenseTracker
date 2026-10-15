import os
from decimal import Decimal

from flask import Flask, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)

APP_NAME = os.getenv("APP_NAME", "Expense Tracker")
APP_ENV = os.getenv("APP_ENV", "development")
PORT = int(os.getenv("PORT", "5000"))

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Expense(db.Model):
    __tablename__ = "expenses"
    
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    category = db.Column(db.String(100), nullable=False)


@app.route("/")
def index():
    expenses = db.session.execute(
        db.select(Expense).order_by(Expense.id)
    ).scalars().all()
    
    total = sum(
        (expense.amount for expense in expenses),
        Decimal("0.00")
    )

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

    expense = Expense(
        description=description,
        amount=amount,
        category=category,
    )
    
    db.session.add(expense)
    db.session.commit()

    return redirect(url_for("index"))


@app.route("/delete/<int:expense_id>", methods=["POST"])
def delete_expense(expense_id):
    expense = db.session.get(Expense, expense_id)

    if expense:
        db.session.delete(expense)
        db.session.commit()

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)