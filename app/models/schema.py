from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

Base = declarative_base()

class MasterProduct(Base):
    __tablename__ = 'master_products'
    spu_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_type = Column(String(50), nullable=False) # 药品, 器械, 药妆, 保健品, 中药饮片, 普通商品
    product_name = Column(String(255), nullable=False)
    brand = Column(String(255))
    manufacturer = Column(String(255), nullable=False)
    approval_number = Column(String(255), index=True) # 批准文号/备案号
    specification = Column(String(255), nullable=False)
    barcode = Column(String(255), index=True)
    mah = Column(String(255)) # 上市许可持有人
    dosage_form = Column(String(100)) # 剂型 (药品特有)
    product_technical_requirements_number = Column(String(255)) # 产品技术要求编号 (器械特有)
    registration_classification = Column(String(100)) # 注册分类 (器械特有)
    main_ingredients = Column(String(500)) # 成分/主要原料 (药妆, 保健品, 中药饮片特有)
    execution_standard = Column(String(255)) # 执行标准 (药妆, 保健品, 中药饮片特有)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class ReviewQueue(Base):
    __tablename__ = 'review_queue'
    review_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    raw_info = Column(Text, nullable=False) # 原始输入信息
    product_type = Column(String(50)) # 商品类型
    extracted_data = Column(Text) # 提取出的结构化数据 (JSON string)
    validated_data = Column(Text) # 验证后的结构化数据 (JSON string)
    review_reason = Column(String(500), nullable=False) # 需要人工审核的原因
    status = Column(String(50), default="PENDING") # PENDING, APPROVED, REJECTED
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

# Pydantic models for API request/response
class ProcessRequest(BaseModel):
    raw_text: str
    sid: Optional[str] = None # Socket ID for real-time updates

class ProductCreate(BaseModel):
    product_type: str
    product_name: str
    brand: Optional[str] = None
    manufacturer: str
    approval_number: Optional[str] = None
    specification: str
    barcode: Optional[str] = None
    mah: Optional[str] = None
    dosage_form: Optional[str] = None
    product_technical_requirements_number: Optional[str] = None
    registration_classification: Optional[str] = None
    main_ingredients: Optional[str] = None
    execution_standard: Optional[str] = None

class ProductResponse(ProductCreate):
    spu_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True