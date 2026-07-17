from fastapi import FastAPI, HTTPException
from supabase import create_client
from pydantic import BaseModel
from dotenv import load_dotenv
import os, random, string

load_dotenv()
app = FastAPI()
db = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def random_code(n=6):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=n))

@app.get("/health")
def health():
      result = db.table("rooms").select("id").limit(1).execute()
      return {"supabase": "connected", "data": result.data}