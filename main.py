from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Field, Session, SQLModel, create_engine, select
from passlib.context import CryptContext
import jwt

SECRET_KEY = "my-super-secret-key-do-not-share" 
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# --- 1. THE DATABASE MODELS ---

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    hashed_password: str

class DailyEntry(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    item_name: str
    calories: int
    protein_g: float
    water_ml: int
    user_id: int = Field(foreign_key="user.id") # The VIP Link


# --- 2. DATABASE SETUP ---
sqlite_url = "sqlite:///database.db"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield

app = FastAPI(lifespan=lifespan)


# --- 3. THE BOUNCER (Security Dependency) ---
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == username)).first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    
# --- 4. PUBLIC ROUTES (No wristband required) ---

@app.get("/")
def read_root():
    return {"message": "Welcome to the Secure Macro Tracker API!"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}


class UserCreate(SQLModel):
    username: str
    password: str

@app.post("/register")
def register_user(user_data: UserCreate):
    with Session(engine) as session:
        existing_user = session.exec(select(User).where(User.username == user_data.username)).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already taken")
        
        hashed_pw = pwd_context.hash(user_data.password)
        new_user = User(username=user_data.username, hashed_password=hashed_pw)
        session.add(new_user)
        session.commit()
        return {"message": f"User {user_data.username} created successfully!"}
    
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == form_data.username)).first()
        if not user or not pwd_context.verify(form_data.password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Incorrect username or password")
        
        expire = datetime.now(timezone.utc) + timedelta(minutes=30)
        token_data = {"sub": user.username, "exp": expire}
        encoded_jwt = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
        return {"access_token": encoded_jwt, "token_type": "bearer"}
    
# --- 5. PROTECTED ROUTES (Requires VIP Wristband) ---

class EntryCreate(SQLModel):
    item_name: str
    calories: int
    protein_g: float
    water_ml: int

@app.post("/log")
def add_entry(entry_data: EntryCreate, current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        new_entry = DailyEntry(
            item_name=entry_data.item_name,
            calories=entry_data.calories,
            protein_g=entry_data.protein_g,
            water_ml=entry_data.water_ml,
            user_id=current_user.id # Automatically attach the logged-in user's ID
        )
        session.add(new_entry)
        session.commit()
        session.refresh(new_entry)
        return new_entry
    
@app.get("/log")
def get_daily_log(current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        # ONLY fetch food that belongs to the current user
        statement = select(DailyEntry).where(DailyEntry.user_id == current_user.id)
        results = session.exec(statement).all()
        return results
    
@app.get("/log/summary")
def get_daily_summary(current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        # ONLY summarize food that belongs to the current user
        statement = select(DailyEntry).where(DailyEntry.user_id == current_user.id)
        results = session.exec(statement).all()
        
        total_calories = sum(item.calories for item in results)
        total_protein = sum(item.protein_g for item in results)
        total_water = sum(item.water_ml for item in results)
        
        return {
            "user": current_user.username,
            "total_calories": total_calories,
            "total_protein_g": total_protein,
            "total_water_ml": total_water
        }

@app.delete("/log/{entry_id}")
def delete_entry(entry_id: int, current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        # Find the specific entry
        entry = session.get(DailyEntry, entry_id)
        
        # Security Check 1: Does the entry exist?
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
            
        # Security Check 2: Does this food belong to the user trying to delete it?
        if entry.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete someone else's food!")
        
        session.delete(entry)
        session.commit()
        return {"ok": True, "message": f"Deleted entry {entry_id}"}