from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_ANON_KEY")
)

def sign_up(email, password):
    try:
        result = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        return result.user, None
    except Exception as e:
        return None, str(e)

def sign_in(email, password):
    try:
        result = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return result.user, result.session, None
    except Exception as e:
        return None, None, str(e)

def sign_out():
    supabase.auth.sign_out()