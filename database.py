from supabase import create_client
from dotenv import load_dotenv
import os
from datetime import date

load_dotenv()

def get_client(access_token=None):
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_ANON_KEY")
    )
    if access_token:
        supabase.postgrest.auth(access_token)
    return supabase

def save_expense_db(user_id, amount, category, description, access_token=None):
    supabase = get_client(access_token)
    data = {
        "user_id": user_id,
        "amount": float(amount),
        "category": category,
        "description": description,
        "date": str(date.today())
    }
    supabase.table("expenses").insert(data).execute()
    return f"Saved: €{amount} for {description} under {category}"

def get_expenses_db(user_id, access_token=None):
    supabase = get_client(access_token)
    result = supabase.table("expenses")\
        .select("*")\
        .eq("user_id", user_id)\
        .execute()
    return result.data

def get_summary_db(user_id, access_token=None):
    expenses = get_expenses_db(user_id, access_token)
    if not expenses:
        return "No expenses found."

    totals = {}
    for e in expenses:
        category = e["category"]
        amount = abs(e["amount"])
        totals[category] = totals.get(category, 0) + amount

    summary = "Your spending summary:\n"
    grand_total = 0
    for category, total in sorted(totals.items(), key=lambda x: x[1], reverse=True):
        summary += f"  {category}: €{total:.2f}\n"
        grand_total += total

    summary += f"\nTotal spent: €{grand_total:.2f}"
    return summary

def delete_expense_db(user_id, expense_id, access_token=None):
    supabase = get_client(access_token)
    supabase.table("expenses")\
        .delete()\
        .eq("id", expense_id)\
        .eq("user_id", user_id)\
        .execute()
    return "Expense deleted."