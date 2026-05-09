import json
import os
from datetime import date

EXPENSES_FILE = "expenses.json"

def save_expense(amount, category, description):
    # Load existing expenses or start fresh
    if os.path.exists(EXPENSES_FILE):
        with open(EXPENSES_FILE, "r") as f:
            expenses = json.load(f)
    else:
        expenses = []

    # Add the new one
    expense = {
        "amount": amount,
        "category": category,
        "description": description,
        "date": str(date.today())
    }
    expenses.append(expense)

    # Save back to file
    with open(EXPENSES_FILE, "w") as f:
        json.dump(expenses, f, indent=2)

    return f"Saved: €{amount} for {description} under {category}"