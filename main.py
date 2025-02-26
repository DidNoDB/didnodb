import os
import json
import hashlib
import uuid
import jwt
import datetime
from datetime import timedelta
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from starlette.middleware.sessions import SessionMiddleware
from fastapi.requests import Request
from pydantic import BaseModel
from typing import Dict, Any, Optional

DB_FOLDER = "db/data"
USERS_FILE = os.path.join(DB_FOLDER, "users.json")

SECRET_KEY = "my_super_secret_key" # TODO: Change this later
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

os.makedirs(DB_FOLDER, exist_ok=True)

# Load users
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump({}, f)

didnodb = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def load_users() -> Dict[str, Any]:
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users: Dict[str, Any]):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def get_user_folder(username: str) -> str:
    user_folder = os.path.join(DB_FOLDER, username)
    os.makedirs(user_folder, exist_ok=True)
    return user_folder

class User(BaseModel):
    username: str
    password: str

class DataModel(BaseModel):
    data: Dict[str, Any]

class TokenData(BaseModel):
    username: str
    role: str

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str = Depends(oauth2_scheme)) -> TokenData:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenData(username=payload["sub"], role=payload["role"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def verify_role(required_role: str):
    def role_checker(token_data: TokenData = Depends(verify_token)):
        if token_data.role != required_role:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return token_data
    return role_checker

@didnodb.post("/register")
def register(user: User):
    users = load_users()
    
    if user.username in users:
        raise HTTPException(status_code=400, detail="User already exists")
    
    users[user.username] = {
        "password": hash_password(user.password),
        "role": "USER" # Default role
    }

    save_users(users)
    get_user_folder(user.username)
    return {"message": "User registered successfully"}

@didnodb.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    users = load_users()
    username = form_data.username
    password = form_data.password

    if username not in users or users[username]["password"] != hash_password(password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    role = users[username]["role"]
    token = create_access_token({"sub": username, "role": role})

    return {"access_token": token, "token_type": "bearer"}

@didnodb.post("/data")
def save_data(data: DataModel, token_data: TokenData = Depends(verify_token)):
    user_folder = get_user_folder(token_data.username)
    model_id = str(uuid.uuid4())
    model_path = os.path.join(user_folder, f"{model_id}.json")
    
    with open(model_path, "w") as f:
        json.dump(data.data, f, indent=4)

    return {"message": "Data saved", "model_id": model_id}

@didnodb.get("/data/{model_id}")
def get_data(model_id: str, token_data: TokenData = Depends(verify_token)):
    model_path = os.path.join(DB_FOLDER, token_data.username, f"{model_id}.json")
    if not os.path.exists(model_path):
        raise HTTPException(status_code=404, detail="Model not found")
    
    with open(model_path, "r") as f:
        return json.load(f)

@didnodb.get("/data")
def get_all_data(token_data: TokenData = Depends(verify_token)):
    user_folder = get_user_folder(token_data.username)
    all_data = {}

    for file in os.listdir(user_folder):
        file_path = os.path.join(user_folder, file)
        if os.path.isfile(file_path) and file.endswith(".json"):
            with open(file_path, "r") as f:
                all_data[file[:-5]] = json.load(f)
    
    return all_data

@didnodb.delete("/data/{model_id}")
def delete_data(model_id: str, token_data: TokenData = Depends(verify_token)):
    model_path = os.path.join(DB_FOLDER, token_data.username, f"{model_id}.json")
    if os.path.exists(model_path):
        os.remove(model_path)
        return {"message": "Model deleted"}
    
    raise HTTPException(status_code=404, detail="Model not found")

@didnodb.get("/admin/users", dependencies=[Depends(verify_role("ADMIN"))])
def get_all_users():
    return load_users()

@didnodb.get("/")
def index():
    return {"data": "the server is running perfectly"}

@didnodb.get("/metrics", dependencies=[Depends(verify_role("ADMIN"))])
def metrics():
    users = load_users()
    num_users = len(users)
    num_entities = sum(len(os.listdir(os.path.join(DB_FOLDER, user))) for user in users if os.path.exists(os.path.join(DB_FOLDER, user)))
    return {"users": num_users, "entities": num_entities}
