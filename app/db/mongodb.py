import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import uuid
from typing import Optional, List
from pydantic import BaseModel, Field

# MongoDB connection settings
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "service_db")

# MongoDB client
client = AsyncIOMotorClient(MONGODB_URI)
db = client[MONGODB_DB]

# Collections
services_collection = db.services
orders_collection = db.orders

# MongoDB Models
class ServiceMongo(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    price: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class OrderMongo(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    services: List[str]  # List of service IDs
    total_price: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

# MongoDB CRUD operations
async def create_service(service: ServiceMongo):
    service_dict = service.dict()
    await services_collection.insert_one(service_dict)
    return service

async def get_services():
    cursor = services_collection.find()
    services = await cursor.to_list(length=None)
    return [ServiceMongo(**service) for service in services]

async def get_service(service_id: str):
    service = await services_collection.find_one({"id": service_id})
    return ServiceMongo(**service) if service else None

async def create_order(order: OrderMongo):
    order_dict = order.dict()
    await orders_collection.insert_one(order_dict)
    return order

async def get_orders(user_id: str):
    cursor = orders_collection.find({"user_id": user_id})
    orders = await cursor.to_list(length=None)
    return [OrderMongo(**order) for order in orders]

async def get_order(order_id: str):
    order = await orders_collection.find_one({"id": order_id})
    return OrderMongo(**order) if order else None

async def update_order_services(order_id: str, service_ids: List[str], total_price: float):
    await orders_collection.update_one(
        {"id": order_id},
        {"$set": {"services": service_ids, "total_price": total_price}}
    )
    return await get_order(order_id) 