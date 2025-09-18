import pytest
from app.agents.graph import agent_executor
from unittest.mock import MagicMock, patch

# Test case for a successful run where the product is found
@pytest.mark.asyncio
async def test_agent_executor_success(mocker):
    # Mock chains
    mock_classifier_chain = MagicMock()
    mock_classifier_chain.invoke.return_value = MagicMock(content="药品")
    mocker.patch('app.agents.classifier_agent.get_classifier_chain', return_value=mock_classifier_chain)

    mock_extractor_chain = MagicMock()
    mock_extractor_chain.invoke.return_value = MagicMock(dict=lambda: {"approval_number": "国药准字H20010142", "product_name": "测试药品", "specification": "100mg", "manufacturer": "测试厂家"})
    mocker.patch('app.agents.drug_extractor_agent.get_extractor_chain', return_value=mock_extractor_chain)

    # Mock NMPA tool to return FOUND
    mocker.patch('app.agents.validator_agent.query_nmpa', return_value={"status": "FOUND"})

    # Mock DB to return a match
    mock_db_session = MagicMock()
    mock_product = MagicMock()
    mock_product.spu_id = 12345
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_product
    mocker.patch('app.agents.matcher_agent.SessionLocal', return_value=mock_db_session)

    raw_text = "芬必得 布洛芬缓释胶囊 国药准字H20010142"
    result = await agent_executor.ainvoke({"raw_text": raw_text})

    assert result["product_type"] == "药品"
    assert result["match_result"]["status"] == "MATCH"
    assert result["match_result"]["spu_id"] == 12345
    assert result.get("review_reason") is None

# Test case for when NMPA validation fails and data goes to review
@pytest.mark.asyncio
async def test_agent_executor_nmpa_fails(mocker):
    # Mock chains
    mock_classifier_chain = MagicMock()
    mock_classifier_chain.invoke.return_value = MagicMock(content="药品")
    mocker.patch('app.agents.classifier_agent.get_classifier_chain', return_value=mock_classifier_chain)

    mock_extractor_chain = MagicMock()
    mock_extractor_chain.invoke.return_value = MagicMock(dict=lambda: {"approval_number": "国药准字H99999999"})
    mocker.patch('app.agents.drug_extractor_agent.get_extractor_chain', return_value=mock_extractor_chain)

    # Mock NMPA tool to return NOT_FOUND
    mocker.patch('app.agents.validator_agent.query_nmpa', return_value={"status": "NOT_FOUND"})

    # Mock DB for saving to review queue
    mock_db_session = MagicMock()
    mock_review_item = MagicMock()
    mock_review_item.review_id = 1
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = None
    mock_db_session.refresh.return_value = None
    type(mock_db_session).query = MagicMock()
    mocker.patch('app.agents.human_in_the_loop_agent.SessionLocal', return_value=mock_db_session)

    raw_text = "一个不存在的药品 国药准字H99999999"
    result = await agent_executor.ainvoke({"raw_text": raw_text})

    assert result["review_reason"] is not None
    assert "NMPA数据库查询失败" in result["review_reason"]

# Test case for when product is not found in DB and goes to review
@pytest.mark.asyncio
async def test_agent_executor_no_match(mocker):
    # Mock chains and tools for a valid product
    mock_classifier_chain = MagicMock()
    mock_classifier_chain.invoke.return_value = MagicMock(content="药品")
    mocker.patch('app.agents.classifier_agent.get_classifier_chain', return_value=mock_classifier_chain)

    mock_extractor_chain = MagicMock()
    mock_extractor_chain.invoke.return_value = MagicMock(dict=lambda: {"approval_number": "国药准字H20010142", "product_name": "测试药品", "specification": "100mg", "manufacturer": "测试厂家"})
    mocker.patch('app.agents.drug_extractor_agent.get_extractor_chain', return_value=mock_extractor_chain)

    mocker.patch('app.agents.validator_agent.query_nmpa', return_value={"status": "FOUND"})

    # Mock DB to return NO match
    mock_matcher_db = MagicMock()
    mock_matcher_db.query.return_value.filter.return_value.first.return_value = None
    mocker.patch('app.agents.matcher_agent.SessionLocal', return_value=mock_matcher_db)

    # Mock DB for saving to review queue
    mock_review_db = MagicMock()
    mock_review_db.add.return_value = None
    mock_review_db.commit.return_value = None
    mock_review_db.refresh.return_value = None
    mocker.patch('app.agents.human_in_the_loop_agent.SessionLocal', return_value=mock_review_db)

    raw_text = "芬必得 布洛芬缓释胶囊 国药准字H20010142"
    result = await agent_executor.ainvoke({"raw_text": raw_text})

    assert result["match_result"]["status"] == "NO_MATCH"
    assert result["review_reason"] is not None
    assert "未在主数据库中匹配到记录" in result["review_reason"]
