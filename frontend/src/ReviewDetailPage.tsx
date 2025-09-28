import { Container, Row, Col, Card, Button, Form, Badge, Table, ListGroup } from 'react-bootstrap';
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

// 定义审核项的类型
interface ReviewItem {
  review_id: number;
  raw_info: string;
  product_type: string;
  extracted_data: Record<string, any>;
  validated_data: Record<string, any>;
  review_reason: Array<{
    type: string;
    message: string;
    field?: string;
    expected_format?: string;
  }>;
  agent_history: Array<{
    agent_name: string;
    output: Record<string, any>;
    timestamp: string;
  }>;
  match_candidates: Array<{
    spu_id: number;
    score: number;
    product_info: Record<string, string>;
  }>;
  fusion_conflicts: Array<{
    field: string;
    existing_value: string;
    new_value: string;
    reason: string;
  }>;
  status: string;
  priority_score: number;
  created_at: string;
  updated_at: string;
}

function ReviewDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [reviewItem, setReviewItem] = useState<ReviewItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState('');
  const [approving, setApproving] = useState(false);
  const [rejecting, setRejecting] = useState(false);
  
  // 从环境变量中获取后端API的Base URL
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  useEffect(() => {
    if (id) {
      fetchReviewItem(parseInt(id));
    }
  }, [id]);

  const fetchReviewItem = async (reviewId: number) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/products/review/queue/${reviewId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data: ReviewItem = await response.json();
      setReviewItem(data);
    } catch (err) {
      console.error('Failed to fetch review item:', err);
      setError('获取审核项详情失败');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!reviewItem) return;
    
    setApproving(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/products/review/submit/${reviewItem.review_id}?approved=true`, 
        { method: 'POST' }
      );
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      // 返回审核队列页面
      navigate('/review');
    } catch (err) {
      console.error('Failed to approve review item:', err);
      setError('批准审核项失败');
    } finally {
      setApproving(false);
    }
  };

  const handleReject = async () => {
    if (!reviewItem) return;
    
    setRejecting(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/products/review/submit/${reviewItem.review_id}?approved=false`, 
        { method: 'POST' }
      );
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      // 返回审核队列页面
      navigate('/review');
    } catch (err) {
      console.error('Failed to reject review item:', err);
      setError('拒绝审核项失败');
    } finally {
      setRejecting(false);
    }
  };

  const handleFeedbackSubmit = async () => {
    if (!reviewItem || !feedback.trim()) return;
    
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/products/review/feedback/${reviewItem.review_id}`, 
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ feedback })
        }
      );
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      // 清空反馈输入框
      setFeedback('');
    } catch (err) {
      console.error('Failed to submit feedback:', err);
      setError('提交反馈失败');
    }
  };

  // 获取优先级颜色
  const getPriorityColor = (score: number) => {
    if (score >= 80) return 'danger'; // 红色
    if (score >= 60) return 'warning'; // 黄色
    if (score >= 40) return 'info'; // 蓝色
    return 'secondary'; // 灰色
  };

  // 获取商品类型中文名称
  const getProductTypeName = (type: string) => {
    const typeMap: Record<string, string> = {
      '药品': '药品',
      '器械': '器械',
      '药妆': '药妆',
      '保健品': '保健品',
      '中药饮片': '中药饮片',
      '普通商品': '普通商品'
    };
    return typeMap[type] || type;
  };

  if (loading) {
    return (
      <Container className="mt-4">
        <p>加载中...</p>
      </Container>
    );
  }

  if (error) {
    return (
      <Container className="mt-4">
        <p className="text-danger">{error}</p>
        <Button onClick={() => navigate('/review')}>返回审核队列</Button>
      </Container>
    );
  }

  if (!reviewItem) {
    return (
      <Container className="mt-4">
        <p>未找到审核项</p>
        <Button onClick={() => navigate('/review')}>返回审核队列</Button>
      </Container>
    );
  }

  return (
    <Container fluid className="p-3">
      <Row className="mb-3">
        <Col>
          <Button variant="secondary" onClick={() => navigate('/review')}>
            ← 返回审核队列
          </Button>
        </Col>
      </Row>
      
      <Row>
        <Col md={8}>
          <Card className="mb-3">
            <Card.Header>
              <div className="d-flex justify-content-between align-items-center">
                <span>审核详情 (ID: {reviewItem.review_id})</span>
                <Badge bg={getPriorityColor(reviewItem.priority_score)}>
                  优先级: {reviewItem.priority_score}
                </Badge>
              </div>
            </Card.Header>
            <Card.Body>
              <h5>原始输入信息</h5>
              <p className="border p-3 bg-light">{reviewItem.raw_info}</p>
              
              <h5 className="mt-4">AI提取数据</h5>
              <Table striped bordered hover>
                <tbody>
                  {Object.entries(reviewItem.extracted_data).map(([key, value]) => (
                    <tr key={key}>
                      <td style={{ width: '30%' }}><strong>{key}</strong></td>
                      <td>{String(value)}</td>
                    </tr>
                  ))}
                </tbody>
              </Table>
              
              {reviewItem.validated_data && Object.keys(reviewItem.validated_data).length > 0 && (
                <>
                  <h5 className="mt-4">验证后数据</h5>
                  <Table striped bordered hover>
                    <tbody>
                      {Object.entries(reviewItem.validated_data).map(([key, value]) => (
                        <tr key={key}>
                          <td style={{ width: '30%' }}><strong>{key}</strong></td>
                          <td>{String(value)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                </>
              )}
              
              <h5 className="mt-4">审核原因</h5>
              <ListGroup>
                {reviewItem.review_reason.map((reason, idx) => (
                  <ListGroup.Item key={idx}>
                    <strong>{reason.type}:</strong> {reason.message}
                    {reason.field && <div>字段: {reason.field}</div>}
                    {reason.expected_format && <div>期望格式: {reason.expected_format}</div>}
                  </ListGroup.Item>
                ))}
              </ListGroup>
            </Card.Body>
          </Card>
        </Col>
        
        <Col md={4}>
          <Card className="mb-3">
            <Card.Header>操作</Card.Header>
            <Card.Body>
              <div className="d-grid gap-2">
                <Button 
                  variant="success" 
                  size="lg" 
                  onClick={handleApprove}
                  disabled={approving || rejecting}
                >
                  {approving ? '批准中...' : '批准'}
                </Button>
                <Button 
                  variant="danger" 
                  size="lg" 
                  onClick={handleReject}
                  disabled={approving || rejecting}
                >
                  {rejecting ? '拒绝中...' : '拒绝'}
                </Button>
              </div>
            </Card.Body>
          </Card>
          
          <Card className="mb-3">
            <Card.Header>反馈</Card.Header>
            <Card.Body>
              <Form.Group className="mb-3">
                <Form.Control 
                  as="textarea" 
                  rows={3} 
                  placeholder="输入您的反馈意见..." 
                  value={feedback}
                  onChange={(e) => setFeedback(e.target.value)}
                />
              </Form.Group>
              <Button 
                variant="primary" 
                onClick={handleFeedbackSubmit}
                disabled={!feedback.trim()}
              >
                提交反馈
              </Button>
            </Card.Body>
          </Card>
          
          <Card className="mb-3">
            <Card.Header>Agent处理历史</Card.Header>
            <Card.Body>
              <ListGroup>
                {reviewItem.agent_history.map((history, idx) => (
                  <ListGroup.Item key={idx}>
                    <div>
                      <strong>{history.agent_name}</strong>
                    </div>
                    <div className="text-muted">
                      {new Date(history.timestamp).toLocaleString()}
                    </div>
                  </ListGroup.Item>
                ))}
              </ListGroup>
            </Card.Body>
          </Card>
          
          {reviewItem.match_candidates && reviewItem.match_candidates.length > 0 && (
            <Card className="mb-3">
              <Card.Header>匹配候选产品</Card.Header>
              <Card.Body>
                <ListGroup>
                  {reviewItem.match_candidates.map((candidate, idx) => (
                    <ListGroup.Item key={idx}>
                      <div>
                        <strong>SPU ID: {candidate.spu_id}</strong> 
                        <Badge bg="info" className="ms-2">相似度: {candidate.score}%</Badge>
                      </div>
                      <div>
                        {Object.entries(candidate.product_info).map(([key, value]) => (
                          <div key={key}><strong>{key}:</strong> {String(value)}</div>
                        ))}
                      </div>
                    </ListGroup.Item>
                  ))}
                </ListGroup>
              </Card.Body>
            </Card>
          )}
          
          {reviewItem.fusion_conflicts && reviewItem.fusion_conflicts.length > 0 && (
            <Card className="mb-3">
              <Card.Header>数据冲突详情</Card.Header>
              <Card.Body>
                <Table striped bordered hover>
                  <thead>
                    <tr>
                      <th>字段</th>
                      <th>现有值</th>
                      <th>新值</th>
                      <th>原因</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reviewItem.fusion_conflicts.map((conflict, idx) => (
                      <tr key={idx}>
                        <td>{conflict.field}</td>
                        <td>{conflict.existing_value}</td>
                        <td>{conflict.new_value}</td>
                        <td>{conflict.reason}</td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </Card.Body>
            </Card>
          )}
        </Col>
      </Row>
    </Container>
  );
}

export default ReviewDetailPage;