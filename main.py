import os
import json
import hashlib
import uuid
import jwt
import datetime
from fastapi import FastAPI, HTTPException, Depends, Header
from starlette.middleware.sessions import SessionMiddleware
from fastapi.requests import Request
from pydantic import BaseModel
from typing import Dict, Any, Optional

DB_FOLDER = "db/data"
USERS_FILE = os.path.join(DB_FOLDER, "users.json")

SECRET_KEY = "my_super_secret_key" # TODO: Change this later
ALGORITHM = "HS256"
EXP_HOURS = 1

os.makedirs(DB_FOLDER, exist_ok=True)

# Load users
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump({}, f)

didnodb = FastAPI()
didnodb.add_middleware(SessionMiddleware, secret_key="supersecretkey")

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def load_users() -> Dict[str, Any]:
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users: Dict[str, Any]):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def create_jwt(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=EXP_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_jwt(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_user_folder(username: str) -> str:
    user_folder = os.path.join(DB_FOLDER, username)
    os.makedirs(user_folder, exist_ok=True)
    return user_folder

class User(BaseModel):
    username: str
    password: str

class DataModel(BaseModel):
    data: Dict[str, Any]

@didnodb.post("/register")
def register(user: User):
    users = load_users()
    if user.username in users:
        raise HTTPException(status_code=400, detail="User already exists")
    users[user.username] = {"password": hash_password(user.password)}
    save_users(users)
    get_user_folder(user.username)
    return {"message": "User registered successfully"}

@didnodb.post("/login")
def login(user: User, request: Request):
    users = load_users()
    if user.username not in users or users[user.username]["password"] != hash_password(user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_jwt(user.username)
    return {"access_token": token, "token_type": "bearer" }

@didnodb.post("/logout")
def logout(request: Request):
    request.session.clear()
    return { "message": "Logout successful" }

@didnodb.post("/data")
def save_data(data: DataModel, authorization: str = Header(None)):
    username = verify_jwt(authorization)
    user_folder = get_user_folder(username)
    model_id = str(uuid.uuid4())
    model_path = os.path.join(user_folder, f"{model_id}.json")
    with open(model_path, "w") as f:
        json.dump(data.data, f, indent=4)
    return {"message": "Data saved", "model_id": model_id}

@didnodb.get("/data/{model_id}")
def get_data(model_id: str, authorization: str = Header(None)):
    username = verify_jwt(authorization)
    model_path = os.path.join(DB_FOLDER, username, f"{model_id}.json")
    if not os.path.exists(model_path):
        raise HTTPException(status_code=404, detail="Model not found")
    with open(model_path, "r") as f:
        return json.load(f)
    
@didnodb.get("/data")
def get_all_data(authorization: str = Header(None)):
    username = verify_jwt(authorization)
    user_folder = get_user_folder(username)
    all_data = {}
    for file in os.listdir(user_folder):
        file_path = os.path.join(user_folder, file)
        if os.path.isfile(file_path) and file.endswith(".json"):
            with open(file_path, "r") as f:
                all_data[file[:-5]] = json.load(f)
    return all_data

@didnodb.delete("/data/{model_id}")
def delete_data(model_id: str, authorization: str = Header(None)):
    username = verify_jwt(authorization)
    model_path = os.path.join(DB_FOLDER, username, f"{model_id}.json")
    if os.path.exists(model_path):
        os.remove(model_path)
        return {"message": "Model deleted"}
    raise HTTPException(status_code=404, detail="Model not found")

@didnodb.get("/")
def index():
    return {"data": "The server is running perfectly"}

@didnodb.get("/metrics")
def metrics():
    users = load_users()
    num_users = len(users)
    num_entities = sum(len(os.listdir(os.path.join(DB_FOLDER, user))) for user in users if os.path.exists(os.path.join(DB_FOLDER, user)))
    return {"users": num_users, "entities": num_entities}
