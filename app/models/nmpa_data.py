from sqlalchemy import Column, Integer, String, Text
from app.models.schema import Base

class NMPADomesticDrug(Base):
    __tablename__ = 'nmpa_domestic_drugs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_code = Column(String(255), index=True, nullable=False) # 药品编码
    approval_numbers = Column(Text, nullable=False) # 批准文号 (分号分隔的字符串)
    product_name = Column(String(255), index=True, nullable=False) # 产品名称
    dosage_form = Column(String(100)) # 剂型
    specification = Column(String(255)) # 规格
    mah = Column(String(255), index=True) # 上市许可持有人
    manufacturer = Column(String(255), index=True) # 生产单位
    remarks = Column(Text) # 药品编码备注

    def __repr__(self):
        return f"<NMPADomesticDrug(drug_code='{self.drug_code}', product_name='{self.product_name}')>"

class NMPAImportedDrug(Base):
    __tablename__ = 'nmpa_imported_drugs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_code = Column(String(255), index=True, nullable=False) # 药品编码
    registration_number = Column(String(255), index=True, nullable=False) # 注册证号
    product_name = Column(String(255), index=True, nullable=False) # 产品名称
    mah_cn = Column(String(255), index=True) # 上市许可持有人中文
    mah_en = Column(String(255)) # 上市许可持有人英文
    company_cn = Column(String(255), index=True) # 公司名称中文
    company_en = Column(String(255)) # 公司名称英文
    dosage_form = Column(String(100)) # 剂型
    specification = Column(String(255)) # 规格
    remarks = Column(Text) # 药品编码备注

    def __repr__(self):
        return f"<NMPAImportedDrug(drug_code='{self.drug_code}', product_name='{self.product_name}')>"
