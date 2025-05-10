import os
import uuid
from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from jose import JWTError, jwt
from passlib.context import CryptContext
import uvicorn

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI(
    title="Service Ordering API",
    description="API for ordering services with JWT authentication",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class User(BaseModel):
    username: str
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str

class Service(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    price: float

class Order(BaseModel):
    id: uuid.UUID
    user_id: str 
    services: List[uuid.UUID]
    total_price: float
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class OrderCreate(BaseModel):
    services: List[uuid.UUID]

# In-memory storage
users_db = {
    "admin": {
        "username": "admin",
        "full_name": "Administrator",
        "hashed_password": pwd_context.hash("secret"),
        "disabled": False
    }
}

services_db = {}
orders_db = {}

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def authenticate_user(db, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users", response_model=User)
async def create_user(user: User, current_user: User = Depends(get_current_user)):
    if user.username in users_db:
        raise HTTPException(status_code=400, detail="Username already registered")
    users_db[user.username] = user.dict()
    return user

@app.get("/users/all", response_model=List[User])
async def get_all_users(current_user: User = Depends(get_current_user)):
    return list(users_db.values())

@app.get("/users/search", response_model=List[User])
async def search_users(name_mask: str, current_user: User = Depends(get_current_user)):
    return [
        user for user in users_db.values()
        if user.get("full_name") and name_mask.lower() in user["full_name"].lower()
    ]

@app.get("/users/{username}", response_model=User)
async def get_user_by_username(username: str, current_user: User = Depends(get_current_user)):
    if username not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return users_db[username]

@app.post("/services", response_model=Service)
async def create_service(service: Service, current_user: User = Depends(get_current_user)):
    service_id = uuid.uuid4()
    service.id = service_id
    services_db[service_id] = service.dict()
    return service

@app.get("/services", response_model=List[Service])
async def get_services(current_user: User = Depends(get_current_user)):
    return list(services_db.values())

@app.post("/orders", response_model=Order)
async def create_order(order: OrderCreate, current_user: User = Depends(get_current_user)):
    order_id = uuid.uuid4()
    user_id = current_user.username
    created_at = datetime.utcnow()
    total_price = sum(services_db[service_id]["price"] for service_id in order.services if service_id in services_db)
    order_data = Order(
        id=order_id,
        user_id=user_id,
        services=order.services,
        total_price=total_price,
        created_at=created_at
    )
    orders_db[order_id] = order_data.dict()
    return order_data

@app.get("/orders", response_model=List[Order])
async def get_all_orders(current_user: User = Depends(get_current_user)):
    return list(orders_db.values())

@app.get("/orders/{order_id}", response_model=Order)
async def get_order(order_id: uuid.UUID, current_user: User = Depends(get_current_user)):
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    return orders_db[order_id]

@app.put("/orders/{order_id}/services", response_model=Order)
async def add_services_to_order(order_id: uuid.UUID, service_ids: List[uuid.UUID], current_user: User = Depends(get_current_user)):
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    order = orders_db[order_id]
    order["services"].extend(service_ids)
    total_price = sum(services_db[service_id]["price"] for service_id in order["services"])
    order["total_price"] = total_price
    return order

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 