import sqlite3
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# 1. The Pydantic Bouncer
class DailyEntry(BaseModel):
    item_name: str
    calories: int
    protein_g: float
    water_ml: int

# 2. Raw SQL Table Setup
def setup_database():
    conn = sqlite3.connect("practice.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            calories INTEGER,
            protein_g REAL,
            water_ml INTEGER
        )
    """)
    conn.commit()
    conn.close()

# 3. FastAPI Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_database()
    yield

app = FastAPI(lifespan=lifespan)

# --- THE RAW SQL ROUTES ---

# CREATE (POST)
@app.post("/log/raw")
def add_entry(entry: DailyEntry):
    conn = sqlite3.connect("practice.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO daily_logs (item_name, calories, protein_g, water_ml)
        VALUES (?, ?, ?, ?)
    """, (entry.item_name, entry.calories, entry.protein_g, entry.water_ml))
    
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    
    return {"id": new_id, "item_name": entry.item_name, "message": "Added via raw SQL!"}

# READ (GET)
@app.get("/log/raw")
def get_all_entries():
    conn = sqlite3.connect("practice.db")
    conn.row_factory = sqlite3.Row  # Magic line to make rows act like dictionaries
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM daily_logs")
    rows = cursor.fetchall()
    conn.close()
    
    # Convert the raw database rows into a format Postman can read (JSON)
    return [dict(row) for row in rows]

# SUMMARY (GET)
@app.get("/log/raw/summary")
def get_summary():
    conn = sqlite3.connect("practice.db")
    cursor = conn.cursor()
    
    # We ask the SQL database to do the math for us using SUM()
    cursor.execute("""
        SELECT 
            SUM(calories), 
            SUM(protein_g), 
            SUM(water_ml) 
        FROM daily_logs
    """)
    result = cursor.fetchone() 
    conn.close()
    
    return {
        "total_calories": result[0] or 0,
        "total_protein_g": result[1] or 0.0,
        "total_water_ml": result[2] or 0
    }

# DELETE (DELETE)
@app.delete("/log/raw/{entry_id}")
def delete_entry(entry_id: int):
    conn = sqlite3.connect("practice.db")
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM daily_logs WHERE id = ?", (entry_id,))
    conn.commit()
    
    rows_deleted = cursor.rowcount
    conn.close()
    
    if rows_deleted == 0:
        raise HTTPException(status_code=404, detail="Entry not found")
        
    return {"message": f"Deleted entry {entry_id}"}