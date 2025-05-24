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
from sqlalchemy.orm import Session
import uvicorn

from db.database import get_db
from db.models import User as UserModel
from db.mongodb import (
    ServiceMongo, OrderMongo,
    create_service, get_services, get_service,
    create_order, get_orders, get_order, update_order_services
)
from db.cache_decorators import cache_read_through, cache_write_through
from db.redis_client import redis_client

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

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

class UserBase(BaseModel):
    username: str
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class UserCreate(UserBase):
    password: str

class User(UserBase):
    class Config:
        orm_mode = True

class ServiceBase(BaseModel):
    name: str
    description: str
    price: float

class ServiceCreate(ServiceBase):
    pass

class Service(ServiceBase):
    id: str
    created_at: datetime

    class Config:
        orm_mode = True

class OrderBase(BaseModel):
    services: List[str]

class OrderCreate(OrderBase):
    pass

class Order(OrderBase):
    id: str
    user_id: str
    total_price: float
    created_at: datetime

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

@cache_read_through(prefix="user", ttl=3600)
async def get_user(db: Session, username: str):
    return db.query(UserModel).filter(UserModel.username == username).first()

async def authenticate_user(db: Session, username: str, password: str):
    user = await get_user(db, username)
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

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
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
    user = await get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = await authenticate_user(db, form_data.username, form_data.password)
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

@cache_write_through(prefix="user", invalidate_pattern="*")
async def create_user_in_db(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = UserModel(
        username=user.username,
        full_name=user.full_name,
        hashed_password=hashed_password,
        disabled=user.disabled
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/users", response_model=User)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = await get_user(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    return await create_user_in_db(db, user)

@cache_read_through(prefix="users", ttl=3600)
async def get_all_users_from_db(db: Session):
    return db.query(UserModel).all()

@app.get("/users/all", response_model=List[User])
async def get_all_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await get_all_users_from_db(db)

@cache_read_through(prefix="users_search", ttl=3600)
async def search_users_from_db(db: Session, name_mask: str):
    return db.query(UserModel).filter(UserModel.full_name.ilike(f"%{name_mask}%")).all()

@app.get("/users/search", response_model=List[User])
async def search_users(name_mask: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await search_users_from_db(db, name_mask)

@app.get("/users/{username}", response_model=User)
async def get_user_by_username(username: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = await get_user(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/services", response_model=Service)
async def create_service_endpoint(service: ServiceCreate, current_user: User = Depends(get_current_user)):
    service_mongo = ServiceMongo(**service.dict())
    created_service = await create_service(service_mongo)
    return created_service

@app.get("/services", response_model=List[Service])
async def get_services_endpoint(current_user: User = Depends(get_current_user)):
    services = await get_services()
    return services

@app.post("/orders", response_model=Order)
async def create_order_endpoint(order: OrderCreate, current_user: User = Depends(get_current_user)):
    total_price = 0
    for service_id in order.services:
        service = await get_service(service_id)
        if not service:
            raise HTTPException(status_code=404, detail=f"Service {service_id} not found")
        total_price += service.price

    order_mongo = OrderMongo(
        user_id=current_user.username,
        services=order.services,
        total_price=total_price
    )
    created_order = await create_order(order_mongo)
    return created_order

@app.get("/orders", response_model=List[Order])
async def get_orders_endpoint(current_user: User = Depends(get_current_user)):
    orders = await get_orders(current_user.username)
    return orders

@app.get("/orders/{order_id}", response_model=Order)
async def get_order_endpoint(order_id: str, current_user: User = Depends(get_current_user)):
    order = await get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.user_id != current_user.username:
        raise HTTPException(status_code=403, detail="Not authorized to access this order")
    return order

@app.put("/orders/{order_id}/services", response_model=Order)
async def add_services_to_order_endpoint(
    order_id: str,
    service_ids: List[str],
    current_user: User = Depends(get_current_user)
):
    order = await get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.user_id != current_user.username:
        raise HTTPException(status_code=403, detail="Not authorized to modify this order")

    total_price = 0
    for service_id in service_ids:
        service = await get_service(service_id)
        if not service:
            raise HTTPException(status_code=404, detail=f"Service {service_id} not found")
        total_price += service.price

    updated_order = await update_order_services(order_id, service_ids, total_price)
    return updated_order

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)