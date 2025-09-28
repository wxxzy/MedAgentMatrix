import { Container, Row, Col, Table, Button, Form, Pagination } from 'react-bootstrap';
import { useState, useEffect } from 'react';

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

function ReviewQueuePage() {
  const [reviewItems, setReviewItems] = useState<ReviewItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [priorityOrder, setPriorityOrder] = useState<'desc' | 'asc'>('desc');
  const [productTypeFilter, setProductTypeFilter] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState<string>('');
  
  // 分页状态
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  // 从环境变量中获取后端API的Base URL
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  useEffect(() => {
    fetchReviewQueue();
  }, [priorityOrder, productTypeFilter, searchTerm]);

  const fetchReviewQueue = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // 构造查询参数
      const params = new URLSearchParams();
      if (priorityOrder) params.append('priority_order', priorityOrder);
      
      const response = await fetch(`${API_BASE_URL}/api/products/review/queue?${params.toString()}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data: ReviewItem[] = await response.json();
      setReviewItems(data);
    } catch (err) {
      console.error('Failed to fetch review queue:', err);
      setError('获取审核队列失败');
    } finally {
      setLoading(false);
    }
  };

  // 处理优先级排序
  const handlePrioritySort = (order: 'asc' | 'desc') => {
    setPriorityOrder(order);
  };

  // 处理商品类型筛选
  const handleProductTypeFilter = (type: string) => {
    setProductTypeFilter(type);
    setCurrentPage(1); // 重置到第一页
  };

  // 处理搜索
  const handleSearch = (term: string) => {
    setSearchTerm(term);
    setCurrentPage(1); // 重置到第一页
  };

  // 计算分页数据
  const filteredItems = reviewItems.filter(item => {
    // 应用商品类型筛选
    if (productTypeFilter !== 'all' && item.product_type !== productTypeFilter) {
      return false;
    }
    
    // 应用搜索筛选
    if (searchTerm) {
      const lowerSearchTerm = searchTerm.toLowerCase();
      const productName = item.extracted_data?.product_name?.toLowerCase() || '';
      const manufacturer = item.extracted_data?.manufacturer?.toLowerCase() || '';
      const rawInfo = item.raw_info.toLowerCase();
      
      if (!productName.includes(lowerSearchTerm) && 
          !manufacturer.includes(lowerSearchTerm) && 
          !rawInfo.includes(lowerSearchTerm)) {
        return false;
      }
    }
    
    return true;
  });
  
  const totalPages = Math.ceil(filteredItems.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const currentItems = filteredItems.slice(startIndex, startIndex + itemsPerPage);

  // 处理分页更改
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
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
        <Button onClick={fetchReviewQueue}>重新加载</Button>
      </Container>
    );
  }

  return (
    <Container fluid className="p-3">
      <h2>人工审核队列</h2>
      
      {/* 控制栏 */}
      <Row className="mb-3 align-items-center">
        <Col md={4}>
          <Form.Control
            type="text"
            placeholder="搜索产品名称、生产企业..."
            value={searchTerm}
            onChange={(e) => handleSearch(e.target.value)}
          />
        </Col>
        <Col md={3}>
          <Form.Select 
            value={productTypeFilter} 
            onChange={(e) => handleProductTypeFilter(e.target.value)}
          >
            <option value="all">所有商品类型</option>
            <option value="药品">药品</option>
            <option value="器械">器械</option>
            <option value="药妆">药妆</option>
            <option value="保健品">保健品</option>
            <option value="中药饮片">中药饮片</option>
            <option value="普通商品">普通商品</option>
          </Form.Select>
        </Col>
        <Col md={3}>
          <div className="d-flex align-items-center">
            <span className="me-2">优先级:</span>
            <Button 
              variant={priorityOrder === 'desc' ? 'primary' : 'outline-primary'}
              onClick={() => handlePrioritySort('desc')}
              className="me-2"
            >
              降序
            </Button>
            <Button 
              variant={priorityOrder === 'asc' ? 'primary' : 'outline-primary'}
              onClick={() => handlePrioritySort('asc')}
            >
              升序
            </Button>
          </div>
        </Col>
      </Row>
      
      {/* 审核项表格 */}
      <Table striped bordered hover responsive>
        <thead>
          <tr>
            <th>优先级</th>
            <th>商品类型</th>
            <th>产品名称</th>
            <th>生产企业</th>
            <th>审核原因</th>
            <th>时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          {currentItems.length === 0 ? (
            <tr>
              <td colSpan={7} className="text-center">
                没有待审核的项目
              </td>
            </tr>
          ) : (
            currentItems.map((item) => (
              <tr key={item.review_id}>
                <td>
                  <div className="d-flex align-items-center">
                    <span className={`badge bg-${getPriorityColor(item.priority_score)}`}>
                      {item.priority_score}
                    </span>
                  </div>
                </td>
                <td>{getProductTypeName(item.product_type)}</td>
                <td>{item.extracted_data?.product_name || '-'}</td>
                <td>{item.extracted_data?.manufacturer || '-'}</td>
                <td>
                  {item.review_reason.map((reason, idx) => (
                    <div key={idx}>{reason.message}</div>
                  ))}
                </td>
                <td>{new Date(item.created_at).toLocaleString()}</td>
                <td>
                  <Button 
                    variant="primary" 
                    size="sm"
                    href={`#/review/${item.review_id}`}
                  >
                    查看详情
                  </Button>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </Table>
      
      {/* 分页控件 */}
      {totalPages > 1 && (
        <Pagination className="justify-content-center">
          <Pagination.First 
            onClick={() => handlePageChange(1)} 
            disabled={currentPage === 1}
          />
          <Pagination.Prev 
            onClick={() => handlePageChange(currentPage - 1)} 
            disabled={currentPage === 1}
          />
          
          {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
            let page;
            if (totalPages <= 5) {
              page = i + 1;
            } else if (currentPage <= 3) {
              page = i + 1;
            } else if (currentPage >= totalPages - 2) {
              page = totalPages - 4 + i;
            } else {
              page = currentPage - 2 + i;
            }
            
            return (
              <Pagination.Item
                key={page}
                active={page === currentPage}
                onClick={() => handlePageChange(page)}
              >
                {page}
              </Pagination.Item>
            );
          })}
          
          <Pagination.Next 
            onClick={() => handlePageChange(currentPage + 1)} 
            disabled={currentPage === totalPages}
          />
          <Pagination.Last 
            onClick={() => handlePageChange(totalPages)} 
            disabled={currentPage === totalPages}
          />
        </Pagination>
      )}
    </Container>
  );
}

export default ReviewQueuePage;