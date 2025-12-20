
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKeyConstraint
from datetime import datetime
import enum

Base = declarative_base()

class Brand(Base):
    __tablename__ = 'brands'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    products = relationship("Product", back_populates="brand", cascade="all, delete-orphan")

class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)  # Уникальное имя категории
    products = relationship("Product", back_populates="category", cascade="all, delete-orphan")

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    price = Column(Float, nullable=False)
    photo_url = Column(String(500))
    description = Column(String(500))
    category_id = Column(Integer, ForeignKey('categories.id', ondelete="CASCADE"), nullable=False)
    brand_id = Column(Integer, ForeignKey('brands.id', ondelete="CASCADE"), nullable=False)  # Бренд теперь в продукте
    category = relationship("Category", back_populates="products")
    brand = relationship("Brand")

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    order_id = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(Integer, nullable=False)
    user_name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=False)
    address = Column(Text, nullable=False)
    comment = Column(Text)
    total = Column(Float, nullable=False)
    status = Column(String(20), default=OrderStatus.PENDING.value, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    action_logs = relationship("OrderActionLog", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = 'order_items'
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id', ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, nullable=False)
    product_name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    order = relationship("Order", back_populates="items")

class OrderActionLog(Base):
    __tablename__ = 'order_action_logs'
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id', ondelete="CASCADE"), nullable=False)
    admin_id = Column(Integer, nullable=False)
    admin_name = Column(String(255))
    action = Column(String(20), nullable=False)  # 'confirm' or 'reject'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    order = relationship("Order", back_populates="action_logs")