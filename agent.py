from groq import Groq
from dotenv import load_dotenv
import os
import json
from storage import save_expense

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Describe the tool to the AI
tools = [
    {
        "type": "function",
        "function": {
            "name": "save_expense",
            "description": "Save a new expense to the finance tracker",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "The amount spent"},
                    "category": {"type": "string", "description": "Category e.g. food, transport, rent"},
                    "description": {"type": "string", "description": "Short description of the expense"}
                },
                "required": ["amount", "category", "description"]
            }
        }
    }
]

# Send a message and let the AI decide to use the tool
user_input = input("Tell me about an expense: ")
messages = [{"role": "user", "content": user_input}]

response = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=messages,
    tools=tools
)

# Check if the AI wants to call a tool
tool_call = response.choices[0].message.tool_calls[0]
arguments = json.loads(tool_call.function.arguments)

# Execute the function with the AI's extracted arguments
result = save_expense(**arguments)
print(f"Result: {result}")