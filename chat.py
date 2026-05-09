from groq import Groq
from dotenv import load_dotenv
import os
import json
from storage import save_expense
from summary import get_summary

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

tools = [
    {
        "type": "function",
        "function": {
            "name": "save_expense",
            "description": "Save a new expense. Use this when the user mentions spending money on something.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "The amount spent"},
                    "category": {"type": "string", "description": "One of: food, transport, rent, health, entertainment, shopping, utilities, other"},
                    "description": {"type": "string", "description": "Short description of the expense"}
                },
                "required": ["amount", "category", "description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_summary",
            "description": "Get total spending by category. Use this when the user asks how much they spent.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

def run_tool(tool_name, arguments):
    if tool_name == "save_expense":
        arguments["amount"] = float(arguments["amount"])
        return save_expense(**arguments)
    elif tool_name == "get_summary":
        return get_summary()
print("💰 Finance Agent ready! Type 'quit' to exit.\n")

messages = [
    {
        "role": "system",
        "content": """You are a personal finance assistant with two tools:
        - save_expense: call this when user mentions spending money
        - get_summary: call this when user asks about their spending
        Always call a tool when relevant. After the tool runs, give a friendly response."""
    }
]

while True:
    user_input = input("You: ")
    if user_input.lower() == "quit":
        break

    messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )

    message = response.choices[0].message

    if message.tool_calls:
        tool_call = message.tool_calls[0]
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        print(f"  → Calling {tool_name}...")
        result = run_tool(tool_name, arguments)

        messages.append({
            "role": "assistant",
            "tool_calls": [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "arguments": tool_call.function.arguments
                    }
                }
            ]
        })
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result
        })

        final = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            tools=tools
        )
        reply = final.choices[0].message.content
    else:
        reply = message.content

    print(f"Agent: {reply}\n")
    messages.append({"role": "assistant", "content": reply})