from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.nmpa_data import NMPADomesticDrug, NMPAImportedDrug
from typing import List, Dict, Optional
from langchain.tools import tool

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@tool
def query_nmpa_by_approval_number(approval_number: str) -> List[Dict]:
    """根据批准文号（或注册证号）查询NMPA数据库中的国产或进口药品信息。
    输入参数: approval_number (str) - 批准文号或注册证号。
    返回: 匹配的药品信息列表，每个药品信息是一个字典。"""
    db = next(get_db())
    results = []

    # 查询国产药品
    domestic_drugs = db.query(NMPADomesticDrug).filter(
        NMPADomesticDrug.approval_numbers.like(f'%{approval_number}%')
    ).all()
    for drug in domestic_drugs:
        results.append({
            "source": "国产药品",
            "drug_code": drug.drug_code,
            "approval_numbers": drug.approval_numbers,
            "product_name": drug.product_name,
            "dosage_form": drug.dosage_form,
            "specification": drug.specification,
            "mah": drug.mah,
            "manufacturer": drug.manufacturer,
            "remarks": drug.remarks
        })

    # 查询进口药品
    imported_drugs = db.query(NMPAImportedDrug).filter(
        NMPAImportedDrug.registration_number == approval_number
    ).all()
    for drug in imported_drugs:
        results.append({
            "source": "进口药品",
            "drug_code": drug.drug_code,
            "registration_number": drug.registration_number,
            "product_name": drug.product_name,
            "mah_cn": drug.mah_cn,
            "mah_en": drug.mah_en,
            "company_cn": drug.company_cn,
            "company_en": drug.company_en,
            "dosage_form": drug.dosage_form,
            "specification": drug.specification,
            "remarks": drug.remarks
        })
    
    return results

@tool
def query_nmpa_by_drug_code(drug_code: str) -> Optional[Dict]:
    """根据药品编码查询NMPA数据库中的国产或进口药品信息。
    输入参数: drug_code (str) - 药品编码。
    返回: 匹配的药品信息字典，如果未找到则返回None。"""
    db = next(get_db())

    # 查询国产药品
    domestic_drug = db.query(NMPADomesticDrug).filter(
        NMPADomesticDrug.drug_code == drug_code
    ).first()
    if domestic_drug:
        return {
            "source": "国产药品",
            "drug_code": domestic_drug.drug_code,
            "approval_numbers": domestic_drug.approval_numbers,
            "product_name": domestic_drug.product_name,
            "dosage_form": domestic_drug.dosage_form,
            "specification": domestic_drug.specification,
            "mah": domestic_drug.mah,
            "manufacturer": domestic_drug.manufacturer,
            "remarks": domestic_drug.remarks
        }

    # 查询进口药品
    imported_drug = db.query(NMPAImportedDrug).filter(
        NMPAImportedDrug.drug_code == drug_code
    ).first()
    if imported_drug:
        return {
            "source": "进口药品",
            "drug_code": imported_drug.drug_code,
            "registration_number": imported_drug.registration_number,
            "product_name": imported_drug.product_name,
            "mah_cn": imported_drug.mah_cn,
            "mah_en": imported_drug.mah_en,
            "company_cn": imported_drug.company_cn,
            "company_en": imported_drug.company_en,
            "dosage_form": imported_drug.dosage_form,
            "specification": imported_drug.specification,
            "remarks": imported_drug.remarks
        }
    
    return None

@tool
def query_nmpa_by_product_name_and_manufacturer(product_name: str, manufacturer: str) -> List[Dict]:
    """根据产品名称和生产企业（或上市许可持有人）模糊查询NMPA数据库中的药品信息。
    输入参数: product_name (str) - 产品名称, manufacturer (str) - 生产企业或上市许可持有人。
    返回: 匹配的药品信息列表，每个药品信息是一个字典。"""
    db = next(get_db())
    results = []

    # 查询国产药品
    domestic_drugs = db.query(NMPADomesticDrug).filter(
        NMPADomesticDrug.product_name.like(f'%{product_name}%'),
        (NMPADomesticDrug.manufacturer.like(f'%{manufacturer}%') | NMPADomesticDrug.mah.like(f'%{manufacturer}%'))
    ).all()
    for drug in domestic_drugs:
        results.append({
            "source": "国产药品",
            "drug_code": drug.drug_code,
            "approval_numbers": drug.approval_numbers,
            "product_name": drug.product_name,
            "dosage_form": drug.dosage_form,
            "specification": drug.specification,
            "mah": drug.mah,
            "manufacturer": drug.manufacturer,
            "remarks": drug.remarks
        })

    # 查询进口药品
    imported_drugs = db.query(NMPAImportedDrug).filter(
        NMPAImportedDrug.product_name.like(f'%{product_name}%'),
        (NMPAImportedDrug.company_cn.like(f'%{manufacturer}%') | NMPAImportedDrug.mah_cn.like(f'%{manufacturer}%'))
    ).all()
    for drug in imported_drugs:
        results.append({
            "source": "进口药品",
            "drug_code": drug.drug_code,
            "registration_number": drug.registration_number,
            "product_name": drug.product_name,
            "mah_cn": drug.mah_cn,
            "company_cn": drug.company_cn,
            "dosage_form": drug.dosage_form,
            "specification": drug.specification,
            "remarks": drug.remarks
        })
    
    return results
