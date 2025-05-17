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
from db.models import Service as ServiceModel
from db.models import Order as OrderModel
from db.models import OrderService as OrderServiceModel

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
    id: uuid.UUID
    created_at: datetime

    class Config:
        orm_mode = True

class OrderBase(BaseModel):
    services: List[uuid.UUID]

class OrderCreate(OrderBase):
    pass

class Order(OrderBase):
    id: uuid.UUID
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

def get_user(db: Session, username: str):
    return db.query(UserModel).filter(UserModel.username == username).first()

def authenticate_user(db: Session, username: str, password: str):
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
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
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
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
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

@app.get("/users/all", response_model=List[User])
async def get_all_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    users = db.query(UserModel).all()
    return users

@app.get("/users/search", response_model=List[User])
async def search_users(name_mask: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    users = db.query(UserModel).filter(UserModel.full_name.ilike(f"%{name_mask}%")).all()
    return users

@app.get("/users/{username}", response_model=User)
async def get_user_by_username(username: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = get_user(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/services", response_model=Service)
async def create_service(service: ServiceCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_service = ServiceModel(**service.dict())
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service

@app.get("/services", response_model=List[Service])
async def get_services(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    services = db.query(ServiceModel).all()
    return services

@app.post("/orders", response_model=Order)
async def create_order(order: OrderCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    services = db.query(ServiceModel).filter(ServiceModel.id.in_(order.services)).all()
    total_price = sum(service.price for service in services)
    
    db_order = OrderModel(
        user_id=current_user.username,
        total_price=total_price
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    for service_id in order.services:
        order_service = OrderServiceModel(
            order_id=db_order.id,
            service_id=service_id
        )
        db.add(order_service)
    
    db.commit()
    db.refresh(db_order)
    
    service_ids = [os.service_id for os in db_order.services]
    return Order(
        id=db_order.id,
        user_id=db_order.user_id,
        services=service_ids,
        total_price=db_order.total_price,
        created_at=db_order.created_at
    )

@app.get("/orders", response_model=List[Order])
async def get_all_orders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    orders = db.query(OrderModel).filter(OrderModel.user_id == current_user.username).all()
    return [
        Order(
            id=order.id,
            user_id=order.user_id,
            services=[os.service_id for os in order.services],
            total_price=order.total_price,
            created_at=order.created_at
        )
        for order in orders
    ]

@app.get("/orders/{order_id}", response_model=Order)
async def get_order(order_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.user_id != current_user.username:
        raise HTTPException(status_code=403, detail="Not authorized to access this order")
    
    return Order(
        id=order.id,
        user_id=order.user_id,
        services=[os.service_id for os in order.services],
        total_price=order.total_price,
        created_at=order.created_at
    )

@app.put("/orders/{order_id}/services", response_model=Order)
async def add_services_to_order(
    order_id: uuid.UUID,
    service_ids: List[uuid.UUID],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.user_id != current_user.username:
        raise HTTPException(status_code=403, detail="Not authorized to modify this order")
    
    new_services = db.query(ServiceModel).filter(ServiceModel.id.in_(service_ids)).all()
    if not new_services:
        raise HTTPException(status_code=404, detail="No valid services found")
    
    for service_id in service_ids:
        order_service = OrderServiceModel(
            order_id=order.id,
            service_id=service_id
        )
        db.add(order_service)
    
    db.commit()
    
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    
    all_services = db.query(ServiceModel).join(OrderServiceModel).filter(OrderServiceModel.order_id == order.id).all()
    order.total_price = sum(service.price for service in all_services)
    
    db.commit()
    db.refresh(order)
    
    return Order(
        id=order.id,
        user_id=order.user_id,
        services=[os.service_id for os in order.services],
        total_price=order.total_price,
        created_at=order.created_at
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)