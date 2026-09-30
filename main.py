import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from datetime import datetime, timezone

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class UserLogin(BaseModel):
    telegram_id: int
    username: str = ""
    first_name: str = ""

class ClaimRequest(BaseModel):
    telegram_id: int
    amount: float

@app.get("/")
def read_root():
    return {"status": "Lion Miner API is online!"}

@app.post("/api/user")
def get_or_create_user(user: UserLogin):
    res = supabase.table("players").select("*").eq("telegram_id", user.telegram_id).execute()
    
    if len(res.data) == 0:
        new_player = {
            "telegram_id": user.telegram_id,
            "username": user.username,
            "first_name": user.first_name,
            "balance": 100.0000,
            "daily_rate": 0.5000,
            "level": 1
        }
        res = supabase.table("players").insert(new_player).execute()
        player = res.data[0]
    else:
        player = res.data[0]

    return {"status": "success", "player": player}

@app.post("/api/claim")
def claim_yield(req: ClaimRequest):
    res = supabase.table("players").select("*").eq("telegram_id", req.telegram_id).execute()
    if len(res.data) == 0:
        raise HTTPException(status_code=404, detail="Speler niet gevonden")
    
    player = res.data[0]
    new_balance = float(player["balance"]) + req.amount
    
    update_res = supabase.table("players").update({
        "balance": new_balance,
        "last_claim_time": datetime.now(timezone.utc).isoformat()
    }).eq("telegram_id", req.telegram_id).execute()
    
    return {"status": "success", "new_balance": new_balance}
