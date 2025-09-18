import sys
import os
import re

# 将项目根目录添加到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from tqdm import tqdm # 导入tqdm库

# 导入数据库模型
from app.models.schema import Base
from app.models.nmpa_data import NMPADomesticDrug, NMPAImportedDrug

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """确保所有表都已创建，并在每次运行时先删除旧表"""
    Base.metadata.drop_all(bind=engine) # 先删除所有表
    Base.metadata.create_all(bind=engine) # 再创建所有表

def parse_remarks_for_specs(remarks_str: str) -> dict:
    """解析 'DRUG_CODE[SPEC];DRUG_CODE[SPEC]' 格式的字符串，返回 {DRUG_CODE: SPEC} 字典"""
    spec_map = {}
    if not remarks_str:
        return spec_map
    
    # 使用全角分号和半角分号分割
    parts = re.split(r'[；;]', remarks_str)
    for part in parts:
        match = re.match(r'(\d+)\[(.*?)\]', part.strip())
        if match:
            drug_code = match.group(1)
            spec = match.group(2)
            spec_map[drug_code] = spec
    return spec_map

def import_domestic_drugs(file_path: str):
    """导入国产药品数据"""
    print(f"正在导入国产药品数据: {file_path}")
    df = pd.read_excel(file_path)
    df.fillna('', inplace=True) # 填充NaN值为空字符串

    session = SessionLocal()
    try:
        # 清空表数据
        session.query(NMPADomesticDrug).delete()
        session.commit()
        print("已清空 NMPADomesticDrug 表数据。")

        processed_records = []

        # 遍历原始DataFrame的每一行
        for index, row in tqdm(df.iterrows(), total=len(df), desc="预处理国产药品数据"): 
            drug_codes_str = str(row['药品编码'])
            approval_numbers_str = str(row['批准文号'])
            remarks_str = str(row['药品编码备注'])

            # 检查药品编码是否包含多个值
            if '；' in drug_codes_str or ';' in drug_codes_str:
                individual_drug_codes = re.split(r'[；;]', drug_codes_str)
                # 批准文号也可能包含多个，但示例中是单个，这里假设批准文号是通用的
                # 如果批准文号也需要拆分，则需要更复杂的逻辑来匹配
                individual_approval_numbers = re.split(r'[；;]', approval_numbers_str) if '；' in approval_numbers_str or ';' in approval_numbers_str else [approval_numbers_str] * len(individual_drug_codes)
                
                spec_map = parse_remarks_for_specs(remarks_str)

                for i, dc in enumerate(individual_drug_codes):
                    dc = dc.strip()
                    if not dc: continue

                    # 获取对应的批准文号，如果individual_approval_numbers长度不够，就用第一个
                    current_approval_number = individual_approval_numbers[i] if i < len(individual_approval_numbers) else individual_approval_numbers[0]

                    # 从解析的备注中获取精确的规格，如果不存在则使用原始规格列的值
                    specific_spec = spec_map.get(dc, row['规格'])
                    specific_remarks = f"{dc}[{specific_spec}]" if specific_spec != row['规格'] else remarks_str # 构造单条备注

                    processed_records.append({
                        '药品编码': dc,
                        '批准文号': current_approval_number.strip(),
                        '产品名称': row['产品名称'],
                        '剂型': row['剂型'],
                        '规格': specific_spec.strip(),
                        '上市许可持有人': row['上市许可持有人'],
                        '生产单位': row['生产单位'],
                        '药品编码备注': specific_remarks.strip()
                    })
            else:
                # 单个药品编码的行，直接添加
                processed_records.append({
                    '药品编码': drug_codes_str.strip(),
                    '批准文号': approval_numbers_str.strip(),
                    '产品名称': row['产品名称'],
                    '剂型': row['剂型'],
                    '规格': str(row['规格']).strip(),
                    '上市许可持有人': row['上市许可持有人'],
                    '生产单位': row['生产单位'],
                    '药品编码备注': remarks_str.strip()
                })
        
        # 将处理后的记录转换为DataFrame
        final_df = pd.DataFrame(processed_records)

        # 批量添加新记录
        for index, row in tqdm(final_df.iterrows(), total=len(final_df), desc="导入国产药品到数据库"): 
            drug = NMPADomesticDrug(
                drug_code=row['药品编码'],
                approval_numbers=row['批准文号'],
                product_name=row['产品名称'],
                dosage_form=row['剂型'],
                specification=row['规格'],
                mah=row['上市许可持有人'],
                manufacturer=row['生产单位'],
                remarks=row['药品编码备注']
            )
            session.add(drug)
        session.commit()
        print(f"成功导入 {len(final_df)} 条国产药品数据。")
    except Exception as e:
        session.rollback()
        print(f"导入国产药品数据失败: {e}")
    finally:
        session.close()

def import_imported_drugs(file_path: str):
    """导入进口药品数据"""
    print(f"正在导入进口药品数据: {file_path}")
    df = pd.read_excel(file_path)
    df.fillna('', inplace=True) # 填充NaN值为空字符串

    session = SessionLocal()
    try:
        # 清空表数据
        session.query(NMPAImportedDrug).delete()
        session.commit()
        print("已清空 NMPAImportedDrug 表数据。")

        # 批量添加新记录
        for index, row in tqdm(df.iterrows(), total=len(df), desc="导入进口药品到数据库"): 
            drug = NMPAImportedDrug(
                drug_code=row['药品编码'],
                registration_number=row['注册证号'],
                product_name=row['产品名称'],
                mah_cn=row['上市许可持有人中文'],
                mah_en=row['上市许可持有人英文'],
                company_cn=row['公司名称中文'],
                company_en=row['公司名称英文'],
                dosage_form=row['剂型'],
                specification=row['规格'],
                remarks=row['药品编码备注']
            )
            session.add(drug)
        session.commit()
        print(f"成功导入 {len(df)} 条进口药品数据。")
    except Exception as e:
        session.rollback()
        print(f"导入进口药品数据失败: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    init_db() # 确保数据库表已创建

    data_dir = "data" # 假设Excel文件在项目根目录下的data文件夹中
    domestic_file = os.path.join(data_dir, "国家药品编码本位码信息（国产药品）.xlsx")
    imported_file = os.path.join(data_dir, "国家药品编码本位码信息（进口药品）.xlsx")

    if not os.path.exists(data_dir):
        print(f"错误: 数据目录 '{data_dir}' 不存在。请将Excel文件放入 '{data_dir}' 文件夹。")
    else:
        if os.path.exists(domestic_file):
            import_domestic_drugs(domestic_file)
        else:
            print(f"警告: 未找到国产药品文件 '{domestic_file}'。")

        if os.path.exists(imported_file):
            import_imported_drugs(imported_file)
        else:
            print(f"警告: 未找到进口药品文件 '{imported_file}'。")

    print("NMPA数据导入脚本执行完毕。")
