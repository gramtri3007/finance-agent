import streamlit as st
import plotly.express as px
import pandas as pd
import json
from dotenv import load_dotenv
from groq import Groq
import os
from auth import sign_in, sign_up, sign_out
from database import save_expense_db, get_expenses_db, get_summary_db, delete_expense_db, update_expense_db

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

st.set_page_config(page_title="Finance Agent", page_icon="💰", layout="wide")

# ── Auth state ────────────────────────────────────────────
if "user" not in st.session_state:
    st.session_state.user = None
if "session" not in st.session_state:
    st.session_state.session = None

# ── Login / Signup page ───────────────────────────────────
if st.session_state.user is None:
    st.title("💰 Personal Finance Agent")
    st.subheader("Your AI-powered finance tracker")
    st.info("🔒 Your data is private and secure. Each user only sees their own expenses.")

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        st.subheader("Welcome back!")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login", use_container_width=True):
            if email and password:
                user, session, error = sign_in(email, password)
                if error:
                    st.error(f"Login failed: {error}")
                else:
                    st.session_state.user = user
                    st.session_state.session = session
                    st.rerun()
            else:
                st.warning("Please enter your email and password.")

    with tab2:
        st.subheader("Create your account")
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password (min 6 characters)", type="password", key="signup_password")
        if st.button("Sign Up", use_container_width=True):
            if new_email and new_password:
                user, error = sign_up(new_email, new_password)
                if error:
                    st.error(f"Signup failed: {error}")
                else:
                    st.success("Account created! Please log in.")
            else:
                st.warning("Please fill in all fields.")

# ── Main app (logged in) ──────────────────────────────────
else:
    user_id = st.session_state.user.id
    user_email = st.session_state.user.email
    access_token = st.session_state.session.access_token

    def run_tool(tool_name, arguments):
        if tool_name == "save_expense":
            arguments["amount"] = float(arguments["amount"])
            return save_expense_db(
                user_id,
                arguments["amount"],
                arguments["category"],
                arguments["description"],
                access_token
            )
        elif tool_name == "get_summary":
            return get_summary_db(user_id, access_token)

    tools = [
        {
            "type": "function",
            "function": {
                "name": "save_expense",
                "description": "Save a new expense. Use when user mentions spending money.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "amount": {"type": "number", "description": "Amount spent"},
                        "category": {"type": "string", "description": "One of: food, transport, rent, health, entertainment, shopping, utilities, other"},
                        "description": {"type": "string", "description": "Short description"}
                    },
                    "required": ["amount", "category", "description"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_summary",
                "description": "Get spending summary by category.",
                "parameters": {"type": "object", "properties": {}, "required": []}
            }
        }
    ]

    # ── Sidebar ───────────────────────────────────────────
    with st.sidebar:
        st.write(f"👤 {user_email}")
        if st.button("Logout", use_container_width=True):
            sign_out()
            st.session_state.user = None
            st.session_state.session = None
            st.session_state.messages = []
            st.session_state.chat_history = []
            st.rerun()

        st.divider()
        st.header("📊 Spending Summary")
        expenses = get_expenses_db(user_id, access_token)

        if expenses:
            df = pd.DataFrame(expenses)
            df["amount"] = df["amount"].abs()
            totals = df.groupby("category")["amount"].sum().reset_index()
            totals.columns = ["Category", "Amount"]
            fig = px.pie(totals, values="Amount", names="Category", title="By Category")
            st.plotly_chart(fig, use_container_width=True)
            st.metric("Total Spent", f"€{df['amount'].sum():.2f}")
        else:
            st.info("No expenses yet!")

    # ── Main area ─────────────────────────────────────────
    st.title("💰 Personal Finance Agent")

    # ── Upload tabs ───────────────────────────────────────
    tab_pdf, tab_receipt = st.tabs(["📄 Upload Bank Statement", "🧾 Scan Receipt"])

    with tab_pdf:
        st.info("""
        🔒 **Privacy notice:** Your PDF is never saved to our servers.
        We extract text from it in memory, send only the transaction
        details to our AI parser, and store only: amount, category,
        and description. Your IBAN, account number, balance, and
        personal details are never stored.
        """)

        uploaded_file = st.file_uploader(
            "Upload your PDF bank statement",
            type="pdf",
            help="Supports Revolut, AIB, Bank of Ireland and most Irish banks"
        )

        if uploaded_file:
            if st.button("Parse & Import Transactions", type="primary"):
                with st.spinner("Reading your statement..."):
                    import fitz
                    import tempfile

                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(uploaded_file.read())
                        tmp_path = tmp.name

                    doc = fitz.open(tmp_path)
                    full_text = ""
                    for page in doc:
                        full_text += page.get_text()
                    os.unlink(tmp_path)

                with st.spinner("AI is parsing transactions..."):
                    try:
                        parse_response = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[
                                {
                                    "role": "system",
                                    "content": """You are a bank statement parser.
                                    Extract all expense transactions and return ONLY a JSON array like this:
                                    [{"amount": 45.00, "category": "food", "description": "Tesco"}, ...]
                                    Categories must be one of: food, transport, rent, entertainment, health, shopping, utilities, other.
                                    Only include money going OUT (expenses). Ignore income and transfers in.
                                    Return ONLY the JSON array, nothing else, no markdown, no backticks."""
                                },
                                {
                                    "role": "user",
                                    "content": full_text
                                }
                            ]
                        )

                        raw = parse_response.choices[0].message.content.strip()
                        if raw.startswith("```"):
                            raw = raw.split("```")[1]
                            if raw.startswith("json"):
                                raw = raw[4:]
                        raw = raw.strip()
                        transactions = json.loads(raw)

                        with st.spinner(f"Saving {len(transactions)} transactions..."):
                            for t in transactions:
                                save_expense_db(
                                    user_id,
                                    float(t["amount"]),
                                    t["category"],
                                    t["description"],
                                    access_token
                                )

                        st.success(f"✅ Imported {len(transactions)} transactions successfully!")
                        st.rerun()

                    except Exception as e:
                        st.error(f"Error parsing statement: {str(e)}")

    with tab_receipt:
        st.info("""
        🔒 **Privacy notice:** Your receipt photo is never saved.
        It is read in memory, sent to AI to extract the amount and
        merchant only, then immediately discarded.
        """)

        receipt_file = st.file_uploader(
            "Upload a receipt photo",
            type=["jpg", "jpeg", "png", "webp"],
            help="Take a clear photo of your receipt in good lighting"
        )

        if "scanned_expense" not in st.session_state:
            st.session_state.scanned_expense = None

        if receipt_file:
            st.image(receipt_file, caption="Your receipt", width=300)

            if st.button("Scan & Save Expense", type="primary"):
                with st.spinner("AI is reading your receipt..."):
                    try:
                        import base64

                        image_bytes = receipt_file.getvalue()
                        base64_image = base64.b64encode(image_bytes).decode("utf-8")
                        media_type = receipt_file.type

                        response = client.chat.completions.create(
                            model="meta-llama/llama-4-scout-17b-16e-instruct",
                            messages=[
                                {
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": """Look at this receipt and extract the expense details.
                                            Return ONLY a JSON object like this:
                                            {"amount": 12.50, "category": "food", "description": "Cafe Nero coffee"}
                                            Categories must be one of: food, transport, rent, entertainment, health, shopping, utilities, other.
                                            Use the merchant name and items to determine category.
                                            Return ONLY the JSON object, no markdown, no backticks."""
                                        },
                                        {
                                            "type": "image_url",
                                            "image_url": {
                                                "url": f"data:{media_type};base64,{base64_image}"
                                            }
                                        }
                                    ]
                                }
                            ]
                        )

                        raw = response.choices[0].message.content.strip()
                        if raw.startswith("```"):
                            raw = raw.split("```")[1]
                            if raw.startswith("json"):
                                raw = raw[4:]
                        raw = raw.strip()

                        st.session_state.scanned_expense = json.loads(raw)

                    except Exception as e:
                        st.error(f"Error scanning receipt: {str(e)}")

        if st.session_state.scanned_expense:
            expense = st.session_state.scanned_expense
            st.success("Receipt scanned successfully!")
            st.write(f"**Merchant:** {expense['description']}")
            st.write(f"**Amount:** €{expense['amount']}")
            st.write(f"**Category:** {expense['category']}")

            if st.button("✅ Confirm & Save", type="primary"):
                save_expense_db(
                    user_id,
                    float(expense["amount"]),
                    expense["category"],
                    expense["description"],
                    access_token
                )
                st.session_state.scanned_expense = None
                st.success("Expense saved!")
                st.rerun()

            if st.button("❌ Cancel"):
                st.session_state.scanned_expense = None
                st.rerun()

    st.divider()

    col1, col2 = st.columns([1, 1])

    # ── Chat ──────────────────────────────────────────────
    with col1:
        st.subheader("💬 Chat with your agent")

        if "messages" not in st.session_state:
            st.session_state.messages = [
                {"role": "system", "content": """You are a personal finance assistant.
                Use save_expense when user mentions spending money.
                Use get_summary when user asks about spending.
                Always use tools when relevant."""}
            ]
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        user_input = st.chat_input("Ask me about your finances...")
        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            st.session_state.messages.append({"role": "user", "content": user_input})

            with st.chat_message("user"):
                st.write(user_input)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        response = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=st.session_state.messages,
                            tools=tools,
                            tool_choice="auto"
                        )
                        message = response.choices[0].message

                        if message.tool_calls:
                            tool_call = message.tool_calls[0]
                            tool_name = tool_call.function.name
                            arguments = json.loads(tool_call.function.arguments)
                            result = run_tool(tool_name, arguments)

                            st.session_state.messages.append({
                                "role": "assistant",
                                "tool_calls": [{"id": tool_call.id, "type": "function",
                                    "function": {"name": tool_name, "arguments": tool_call.function.calls.arguments}}]
                            })
                            st.session_state.messages.append({
                                "role": "tool", "tool_call_id": tool_call.id, "content": result
                            })

                            final = client.chat.completions.create(
                                model="llama-3.3-70b-versatile",
                                messages=st.session_state.messages,
                                tools=tools
                            )
                            reply = final.choices[0].message.content
                        else:
                            reply = message.content

                        st.write(reply)
                        st.session_state.chat_history.append({"role": "assistant", "content": reply})
                        st.rerun()

                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                        st.session_state.messages = st.session_state.messages[:-1]

    # ── Transactions table ────────────────────────────────
    # ── Transactions table ────────────────────────────────
    with col2:
        st.subheader("📋 All Transactions")
        expenses = get_expenses_db(user_id, access_token)

        if "editing_id" not in st.session_state:
            st.session_state.editing_id = None

        if expenses:
            for expense in expenses:
                c1, c2, c3, c4, c5, c6 = st.columns([2, 3, 2, 1.5, 1, 1])
                c1.write(expense["date"])
                c2.write(expense["description"])
                c3.write(expense["category"])
                c4.write(f"€{abs(expense['amount']):.2f}")

                with c5:
                    if st.button("✏️", key=f"edit_{expense['id']}"):
                        st.session_state.editing_id = expense["id"]
                        st.session_state.editing_data = expense
                        st.rerun()

                with c6:
                    if st.button("🗑️", key=f"del_{expense['id']}"):
                        delete_expense_db(user_id, expense["id"], access_token)
                        st.rerun()

            # Edit form
            if st.session_state.editing_id:
                e = st.session_state.editing_data
                st.divider()
                st.subheader(f"✏️ Editing: {e['description']}")

                with st.form("edit_form"):
                    new_description = st.text_input("Description", value=e["description"])
                    new_amount = st.number_input("Amount (€)", value=abs(float(e["amount"])), min_value=0.0, step=0.01)
                    categories = ["food", "transport", "rent", "health", "entertainment", "shopping", "utilities", "other"]
                    idx = categories.index(e["category"]) if e["category"] in categories else 0
                    new_category = st.selectbox("Category", categories, index=idx)

                    col_s, col_c = st.columns(2)
                    submitted = col_s.form_submit_button("💾 Save", type="primary", use_container_width=True)
                    cancelled = col_c.form_submit_button("✖ Cancel", use_container_width=True)

                if submitted:
                    update_expense_db(user_id, e["id"], new_amount, new_category, new_description, access_token)
                    st.session_state.editing_id = None
                    st.session_state.editing_data = None
                    st.rerun()

                if cancelled:
                    st.session_state.editing_id = None
                    st.session_state.editing_data = None
                    st.rerun()
        else:
            st.info("No transactions yet! Upload a statement or add expenses via chat.")