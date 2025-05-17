from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, Table, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .database import Base

class User(Base):
    __tablename__ = "users"

    username = Column(String(50), primary_key=True)
    full_name = Column(String(100))
    hashed_password = Column(String(255), nullable=False)
    disabled = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    orders = relationship("Order", back_populates="user")

class Service(Base):
    __tablename__ = "services"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    orders = relationship("OrderService", back_populates="service")

class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(50), ForeignKey("users.username"))
    total_price = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User", back_populates="orders")
    services = relationship("OrderService", back_populates="order")

class OrderService(Base):
    __tablename__ = "order_services"

    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), primary_key=True)
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id"), primary_key=True)

    order = relationship("Order", back_populates="services")
    service = relationship("Service", back_populates="orders")