import fitz
import json
import os
from groq import Groq
from dotenv import load_dotenv
from storage import save_expense

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Step 1 — Extract text from PDF
def extract_text_from_pdf(filename):
    doc = fitz.open(filename)
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    return full_text

# Step 2 — Send to AI and extract transactions
def parse_transactions(text):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": """You are a bank statement parser. 
                Extract all transactions and return ONLY a JSON array like this:
                [{"amount": 45.00, "category": "food", "description": "Tesco"}, ...]
                Categories must be one of: food, transport, rent, entertainment, health, shopping, utilities, other.
                Only include money going OUT (expenses). Ignore income/credits.
                Return ONLY the JSON array, nothing else."""
            },
            {
                "role": "user",
                "content": text
            }
        ]
    )
    return response.choices[0].message.content

# Step 3 — Run everything
print("Reading PDF...")
text = extract_text_from_pdf("statement.pdf")

print("Sending to AI to parse transactions...")
result = parse_transactions(text)

print("Saving expenses...")
transactions = json.loads(result)

for t in transactions:
    outcome = save_expense(t["amount"], t["category"], t["description"])
    print(f"  ✓ {outcome}")

print(f"\nDone! {len(transactions)} expenses saved to expenses.json")