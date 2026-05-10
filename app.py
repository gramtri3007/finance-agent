import streamlit as st
import json
import os
import plotly.express as px
import pandas as pd
from chat import run_tool, tools, client
from dotenv import load_dotenv

load_dotenv()

# Page config
st.set_page_config(page_title="Finance Agent", page_icon="💰", layout="wide")
st.title("💰 Personal Finance Agent")

# Load expenses
def load_expenses():
    if os.path.exists("expenses.json"):
        with open("expenses.json", "r") as f:
            return json.load(f)
    return []

# ── Sidebar: summary + chart ──────────────────────────────
with st.sidebar:
    st.header("📊 Spending Summary")
    expenses = load_expenses()

    if expenses:
        df = pd.DataFrame(expenses)
        df["amount"] = df["amount"].abs()

        # Totals by category
        totals = df.groupby("category")["amount"].sum().reset_index()
        totals.columns = ["Category", "Amount"]

        # Pie chart
        fig = px.pie(totals, values="Amount", names="Category", title="Spending by Category")
        st.plotly_chart(fig, use_container_width=True)

        # Total
        st.metric("Total Spent", f"€{df['amount'].sum():.2f}")
    else:
        st.info("No expenses yet!")

# ── Main area: two columns ────────────────────────────────
col1, col2 = st.columns([1, 1])

# Left: chat
with col1:
    st.subheader("💬 Chat with your agent")

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "system", "content": """You are a personal finance assistant with two tools:
            - save_expense: call this when user mentions spending money
            - get_summary: call this when user asks about their spending
            Always call a tool when relevant."""}
        ]
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Show chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Chat input
    user_input = st.chat_input("Ask me anything about your finances...")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.chat_message("user"):
            st.write(user_input)

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                import json as json_module
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
                    arguments = json_module.loads(tool_call.function.arguments)
                    result = run_tool(tool_name, arguments)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "tool_calls": [{"id": tool_call.id, "type": "function",
                            "function": {"name": tool_name, "arguments": tool_call.function.arguments}}]
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

# Right: transactions table
with col2:
    st.subheader("📋 All Transactions")
    expenses = load_expenses()
    if expenses:
        df = pd.DataFrame(expenses)
        df["amount"] = df["amount"].abs()
        df = df[["date", "description", "category", "amount"]]
        df.columns = ["Date", "Description", "Category", "Amount (€)"]
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No transactions yet!")