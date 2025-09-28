import unittest
from unittest.mock import patch, MagicMock
from app.agents.enhanced_matcher_agent import match_product, calculate_similarity, calculate_match_score, find_matching_products
from app.agents.fusion_agent import fuse_product, merge_product_data
from app.models.schema import MasterProduct

class TestEnhancedMatcherAgent(unittest.TestCase):
    def setUp(self):
        self.validated_data = {
            "approval_number": "国药准字H20240001",
            "product_name": "蒙脱石散",
            "manufacturer": "湖北午时药业股份有限公司",
            "specification": "3g*10袋/盒",
            "product_type": "药品"
        }
        
        self.existing_product = MasterProduct(
            spu_id=1,
            product_type="药品",
            product_name="蒙脱石散",
            manufacturer="湖北午时药业股份有限公司",
            approval_number="国药准字H20240001",
            specification="3g*10袋/盒",
            brand="午时"
        )

    def test_calculate_similarity(self):
        # 测试完全相同的字符串
        self.assertEqual(calculate_similarity("蒙脱石散", "蒙脱石散"), 1.0)
        
        # 测试完全不同的字符串
        self.assertEqual(calculate_similarity("蒙脱石散", "布洛芬"), 0.0)
        
        # 测试部分相似的字符串
        self.assertGreater(calculate_similarity("蒙脱石散", "蒙脱石颗粒"), 0.5)

    def test_calculate_match_score_exact_match(self):
        # 测试完全匹配的情况
        score = calculate_match_score(self.validated_data, self.existing_product)
        # 批准文号完全匹配(40) + 产品名称完全匹配(25) + 生产企业完全匹配(20) + 规格完全匹配(10) + 品牌部分匹配(2) = 97
        self.assertGreaterEqual(score, 90)

    def test_calculate_match_score_partial_match(self):
        # 测试部分匹配的情况
        partial_data = self.validated_data.copy()
        partial_data["product_name"] = "蒙脱石颗粒"
        
        score = calculate_match_score(partial_data, self.existing_product)
        # 批准文号完全匹配(40) + 产品名称部分匹配(20) + 生产企业完全匹配(20) + 规格完全匹配(10) + 品牌部分匹配(2) = 92
        self.assertGreaterEqual(score, 75)
        self.assertLess(score, 90)

    @patch('app.agents.enhanced_matcher_agent.SessionLocal')
    def test_find_matching_products_exact_match(self, mock_session):
        # 模拟数据库查询返回完全匹配的产品
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = [self.existing_product]
        
        candidates = find_matching_products(self.validated_data)
        
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["product"].spu_id, 1)
        self.assertGreaterEqual(candidates[0]["score"], 90)

    @patch('app.agents.enhanced_matcher_agent.SessionLocal')
    def test_match_product_exact_match(self, mock_session):
        # 模拟数据库查询返回完全匹配的产品
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = [self.existing_product]
        
        state = {"validated_data": self.validated_data}
        result = match_product(state)
        
        self.assertEqual(result["match_result"]["status"], "MATCH")
        self.assertEqual(result["match_result"]["spu_id"], 1)

    @patch('app.agents.enhanced_matcher_agent.SessionLocal')
    def test_match_product_no_match(self, mock_session):
        # 模拟数据库查询返回空结果
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.limit.return_value.all.return_value = []
        
        state = {"validated_data": self.validated_data}
        result = match_product(state)
        
        self.assertEqual(result["match_result"]["status"], "NO_MATCH")
        self.assertIsNone(result["match_result"]["spu_id"])

class TestFusionAgent(unittest.TestCase):
    def setUp(self):
        self.validated_data = {
            "approval_number": "国药准字H20240001",
            "product_name": "蒙脱石散",
            "manufacturer": "湖北午时药业股份有限公司",
            "specification": "3g*10袋/盒",
            "product_type": "药品",
            "brand": "午时"
        }
        
        self.existing_product = MasterProduct(
            spu_id=1,
            product_type="药品",
            product_name="蒙脱石散",
            manufacturer="湖北午时药业股份有限公司",
            approval_number="国药准字H20240001",
            specification="3g*10袋/盒",
            brand="午时"
        )

    def test_merge_product_data_exact_match(self):
        # 测试完全匹配的数据合并
        fused_data, conflicts = merge_product_data(self.existing_product, self.validated_data)
        
        self.assertEqual(len(conflicts), 0)
        self.assertEqual(fused_data["approval_number"], "国药准字H20240001")
        self.assertEqual(fused_data["product_name"], "蒙脱石散")
        self.assertEqual(fused_data["manufacturer"], "湖北午时药业股份有限公司")
        self.assertEqual(fused_data["specification"], "3g*10袋/盒")
        self.assertEqual(fused_data["brand"], "午时")

    def test_merge_product_data_with_conflicts(self):
        # 测试有冲突的数据合并
        conflicting_data = self.validated_data.copy()
        conflicting_data["product_name"] = "蒙脱石颗粒"  # 与现有产品名称不同
        
        fused_data, conflicts = merge_product_data(self.existing_product, conflicting_data)
        
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]["field"], "product_name")
        # 在有冲突的情况下，应该保留现有产品的数据
        self.assertEqual(fused_data["product_name"], "蒙脱石散")

    def test_fuse_product_exact_match(self):
        state = {
            "validated_data": self.validated_data,
            "match_result": {
                "status": "MATCH",
                "spu_id": 1
            },
            "product_type": "药品"
        }
        
        with patch('app.agents.fusion_agent.SessionLocal') as mock_session:
            # 模拟数据库查询返回完全匹配的产品
            mock_db = MagicMock()
            mock_session.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = self.existing_product
            
            result = fuse_product(state)
            
            self.assertEqual(result["fusion_result"]["status"], "FUSED")
            self.assertEqual(result["fusion_result"]["spu_id"], 1)

    def test_fuse_product_needs_review(self):
        state = {
            "validated_data": self.validated_data,
            "match_result": {
                "status": "HIGH_SIMILARITY",
                "spu_id": 1
            },
            "product_type": "药品"
        }
        
        # 创建一个与新数据有冲突的现有产品
        conflicting_product = MasterProduct(
            spu_id=1,
            product_type="药品",
            product_name="蒙脱石颗粒",  # 与新数据不同
            manufacturer="湖北午时药业股份有限公司",
            approval_number="国药准字H20240001",
            specification="3g*10袋/盒",
            brand="午时"
        )
        
        with patch('app.agents.fusion_agent.SessionLocal') as mock_session:
            # 模拟数据库查询返回有冲突的产品
            mock_db = MagicMock()
            mock_session.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = conflicting_product
            
            result = fuse_product(state)
            
            self.assertEqual(result["fusion_result"]["status"], "NEEDS_REVIEW")
            self.assertEqual(len(result["fusion_result"]["conflicts"]), 1)

if __name__ == '__main__':
    unittest.main()