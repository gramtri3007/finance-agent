import json
import os

EXPENSES_FILE = "expenses.json"

def get_summary():
    if not os.path.exists(EXPENSES_FILE):
        return "No expenses found."

    with open(EXPENSES_FILE, "r") as f:
        expenses = json.load(f)

    # Group by category
    totals = {}
    for e in expenses:
        category = e["category"]
        amount = abs(e["amount"])  # handle negative amounts
        totals[category] = totals.get(category, 0) + amount

    # Build summary string
    summary = "Your spending summary:\n"
    grand_total = 0
    for category, total in sorted(totals.items(), key=lambda x: x[1], reverse=True):
        summary += f"  {category}: €{total:.2f}\n"
        grand_total += total

    summary += f"\nTotal spent: €{grand_total:.2f}"
    return summary

# Test it
print(get_summary())