# 💰 Personal Finance Agent

An AI-powered personal finance tracker that reads your bank statements, scans receipts, categorises expenses, and answers questions about your spending in plain English.

Built from scratch in a single day as a learning project to understand LLMs, RAG, and MCP.

🔗 **Live app:** https://finance-agent-tjnrylhk6i5qnrlda5z5es.streamlit.app

---

## What it does

- 📄 **Upload your bank statement** (PDF) and automatically import all transactions
- 🧾 **Scan receipts** by uploading a photo — AI extracts the amount and merchant
- 💬 **Chat with your finances** — ask "how much did I spend on food?" in plain English
- 📊 **Visual spending summary** — pie chart and totals by category
- ✏️ **Edit and delete transactions** — fix miscategorised expenses
- 🔐 **Personal accounts** — each user sees only their own data
- ☁️ **Persistent storage** — data survives across sessions and devices

---

## Key concepts used

### LLM — Large Language Model
The AI brain of the agent. This project uses **Llama 3.3 70b** (via Groq) as the reasoning engine. The LLM understands natural language — so when you type "I spent €45 on groceries at Tesco", it knows what that means, extracts the structured data, and decides what action to take. It also powers receipt scanning (using Llama 4 Scout with vision) and bank statement parsing.

### RAG — Retrieval Augmented Generation
RAG is the technique of giving an LLM access to external knowledge at query time, rather than relying only on what it was trained on. In this project, `expenses.json` (and later Supabase) is the knowledge base. When you ask "how much did I spend this month?", the agent retrieves your expense data from the database and feeds it into the LLM so it can answer accurately with your real numbers — not a guess.

### MCP — Model Context Protocol
MCP is the system that lets the LLM use tools — real Python functions it can call when needed. In this project, the agent has access to:
- `save_expense()` — called when you mention spending money
- `get_summary()` — called when you ask about your spending

You don't tell the agent which function to call — it reads the tool descriptions and decides itself. That's the core of how agents work. MCP in production systems can connect to databases, APIs, calendars, email — anything.

### Agent Loop
The think → act → observe cycle that powers every AI agent:
1. User sends a message
2. LLM reads it and decides to call a tool
3. Your code executes the tool
4. Result goes back to the LLM
5. LLM replies to the user

---

## Tech stack

| Layer | Technology |
|---|---|
| AI model | Llama 3.3 70b via Groq (free) |
| Vision model | Llama 4 Scout via Groq (free) |
| Frontend | Streamlit |
| Database | Supabase (PostgreSQL) |
| Authentication | Supabase Auth |
| PDF parsing | PyMuPDF (fitz) |
| Deployment | Streamlit Community Cloud |
| Version control | GitHub |

---

---

## How to run locally

**1. Clone the repo**
```bash
git clone https://github.com/gramtri3007/finance-agent.git
cd finance-agent
```

**2. Create a virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Set up your `.env` file**

**5. Run the app**
```bash
streamlit run app.py
```

---

## Features built

- [x] AI chat with tool use (MCP)
- [x] PDF bank statement parser
- [x] Receipt photo scanning
- [x] User authentication
- [x] Per-user Supabase database
- [x] Spending pie chart
- [x] Edit and delete transactions
- [x] Deployed on Streamlit Cloud
- [ ] Budget limits per category
- [ ] Date filtering
- [ ] Recurring expenses
- [ ] Revolut API integration
- [ ] Export to CSV

---

## What I learned

- How to make API calls to an LLM from Python
- What RAG is and how to implement it with a real database
- How MCP/tool use works — giving an AI the ability to call your code
- How to build and deploy a full-stack AI app from scratch
- Supabase authentication and Row Level Security
- Streamlit for rapid UI development

---

## Privacy

Your bank statement PDF and receipt photos are **never stored**. They are read in memory, parsed for transaction details only, then discarded. Only the following is stored per expense: amount, category, description, and date. Your IBAN, account number, balance, and personal details are never saved.

---

