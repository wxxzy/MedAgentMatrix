import 'bootstrap/dist/css/bootstrap.min.css';
import 'reactflow/dist/style.css';
import { Container, Row, Col, Card, Form, Button, ListGroup, Nav, Navbar } from 'react-bootstrap';
import { useCallback, useState, useEffect } from 'react';
import ReactFlow, {
    useNodesState,
    useEdgesState,
} from 'reactflow';
import type { Edge, Node} from 'reactflow';
import io from 'socket.io-client';
import ReviewQueuePage from './ReviewQueuePage';
import ReviewDetailPage from './ReviewDetailPage';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Link
} from "react-router-dom";

// 从环境变量中获取后端API的Base URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'; // 默认值

const socket = io(API_BASE_URL); // Socket.IO也需要连接到后端

const initialNodes: Node[] = [
    { id: 'classifier', position: { x: 0, y: 100 }, data: { label: '商品分类' } },
    { id: 'drug_extractor', position: { x: -350, y: 250 }, data: { label: '药品提取' } },
    { id: 'device_extractor', position: { x: -200, y: 250 }, data: { label: '器械提取' } },
    { id: 'cosmeceutical_extractor', position: { x: -50, y: 250 }, data: { label: '药妆提取' } },
    { id: 'supplement_extractor', position: { x: 100, y: 250 }, data: { label: '保健品提取' } },
    { id: 'tcm_extractor', position: { x: 250, y: 250 }, data: { label: '中药饮片提取' } },
    { id: 'general_extractor', position: { x: 400, y: 250 }, data: { label: '普通商品提取' } },
    { id: 'validator', position: { x: 0, y: 400 }, data: { label: '数据验证' } },
    { id: 'matcher', position: { x: 0, y: 550 }, data: { label: '主数据匹配' } },
    { id: 'save_product', position: { x: -150, y: 700 }, data: { label: '保存新商品' } },
    { id: 'request_review', position: { x: 200, y: 550 }, data: { label: '人工审核' } },
    { id: 'end', position: { x: 0, y: 850 }, data: { label: '结束' }, type: 'output' },
];

const initialEdges: Edge[] = [
    { id: 'e-classifier-drug', source: 'classifier', target: 'drug_extractor', animated: true },
    { id: 'e-classifier-device', source: 'classifier', target: 'device_extractor', animated: true },
    { id: 'e-classifier-cosmeceutical', source: 'classifier', target: 'cosmeceutical_extractor', animated: true },
    { id: 'e-classifier-supplement', source: 'classifier', target: 'supplement_extractor', animated: true },
    { id: 'e-classifier-tcm', source: 'classifier', target: 'tcm_extractor', animated: true },
    { id: 'e-classifier-general', source: 'classifier', target: 'general_extractor', animated: true },
    { id: 'e-drug-validator', source: 'drug_extractor', target: 'validator', animated: true },
    { id: 'e-device-validator', source: 'device_extractor', target: 'validator', animated: true },
    { id: 'e-cosmeceutical-validator', source: 'cosmeceutical_extractor', target: 'validator', animated: true },
    { id: 'e-supplement-validator', source: 'supplement_extractor', target: 'validator', animated: true },
    { id: 'e-tcm-validator', source: 'tcm_extractor', target: 'validator', animated: true },
    { id: 'e-general-validator', source: 'general_extractor', target: 'validator', animated: true },
    { id: 'e-validator-matcher', source: 'validator', target: 'matcher', animated: true },
    { id: 'e-validator-review', source: 'validator', target: 'request_review', animated: true },
    { id: 'e-matcher-end', source: 'matcher', target: 'end', label: '匹配成功', animated: true },
    { id: 'e-matcher-review', source: 'matcher', target: 'request_review', label: '未匹配', animated: true },
    { id: 'e-review-save', source: 'request_review', target: 'save_product', label: '批准', animated: true },
    { id: 'e-review-end', source: 'request_review', target: 'end', label: '拒绝', animated: true },
    { id: 'e-save-end', source: 'save_product', target: 'end', animated: true },
];

const nodeStyles = {
  active: { border: '2px solid #007bff', boxShadow: '0 0 10px rgba(0, 123, 255, 0.5)' },
  completed: { backgroundColor: '#d4edda', color: '#155724' },
  failed: { backgroundColor: '#f8d7da', color: '#721c24' },
  pending: { backgroundColor: '#fff3cd', color: '#856404' },
};

function App() {
    const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
    const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
    const [sid, setSid] = useState<string | null>(null);
    const [productInfo, setProductInfo] = useState('');
    const [taskHistory, setTaskHistory] = useState<any[]>([]);
    const [selectedNodeState, setSelectedNodeState] = useState<any>(null);
    const [currentTaskStatus, setCurrentTaskStatus] = useState<string>('等待提交');
    const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
    const [reviewItem, setReviewItem] = useState<any>(null);

    useEffect(() => {
        socket.on('connect', () => setSid(socket.id));

        socket.on('agent_step', (data) => {
            console.log('Received agent_step:', data);
            const { node: activeNodeId, state } = data;

            setTaskHistory((prev) => [...prev, data]);
            updateTaskStatus(state, activeNodeId);

            setNodes((nds) =>
                nds.map((n) => {
                    const isNodeActive = n.id === activeNodeId;
                    const isNodeCompleted = taskHistory.some(h => h.node === n.id) || isNodeActive;

                    let style = { ...n.style };
                    if (isNodeActive) {
                        style = { ...style, ...nodeStyles.active };
                    } else if (isNodeCompleted) {
                        if (n.id === 'validator' && state.review_reason) {
                            style = { ...style, ...nodeStyles.failed };
                        } else if (n.id === 'request_review') {
                            style = { ...style, ...nodeStyles.pending };
                        } else {
                            style = { ...style, ...nodeStyles.completed };
                        }
                    }
                    return { ...n, style };
                })
            );

            setEdges((eds) =>
                eds.map((e) => {
                    const isEdgeActive = taskHistory.some(h => e.source === h.node) || e.source === activeNodeId;
                    return { ...e, animated: isEdgeActive };
                })
            );
        });

        return () => {
            socket.off('connect');
            socket.off('agent_step');
        };
    }, [taskHistory]);

    const updateTaskStatus = (state: any, activeNodeId: string) => {
        if (activeNodeId === 'request_review') {
            setCurrentTaskStatus('需要人工审核');
            setReviewItem(state);
        } else if (state.spu_id) {
            setCurrentTaskStatus(`处理完成: 已创建 SPU ID ${state.spu_id}`);
        } else if (state.match_result?.status === 'MATCH') {
            setCurrentTaskStatus(`处理完成: 已匹配 SPU ID ${state.match_result.spu_id}`);
        } else {
            setCurrentTaskStatus('处理中...');
        }
    };

    const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
        const nodeHistory = taskHistory.filter(h => h.node === node.id);
        setSelectedNodeState(nodeHistory.length > 0 ? nodeHistory[nodeHistory.length - 1] : null);
    }, [taskHistory]);

    const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        setNodes(initialNodes.map(node => ({ ...node, style: {} })));
        setEdges(initialEdges.map(edge => ({ ...edge, animated: false })));
        setTaskHistory([]);
        setSelectedNodeState(null);
        setCurrentTaskStatus('处理中...');
        setReviewItem(null);

        const response = await fetch(`${API_BASE_URL}/api/products/process`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ raw_text: productInfo, sid }),
        });
        const data = await response.json();
        setCurrentTaskId(data.task_id);
    };

    const handleReviewSubmit = async (approved: boolean) => {
        if (!reviewItem?.review_id) return;

        const response = await fetch(`${API_BASE_URL}/api/products/review/submit/${reviewItem.review_id}?approved=${approved}`, {
            method: 'POST',
        });
        const data = await response.json();
        if (data.status === 'SUCCESS') {
            setReviewItem(null);
            setCurrentTaskStatus(`人工审核: ${approved ? '已批准，继续处理...' : '已拒绝'}`);
        }
    };

    return (
        <Router>
            <Container fluid className="p-0" style={{ height: '100vh' }}>
                <Navbar bg="dark" variant="dark" expand="lg">
                    <Navbar.Brand as={Link} to="/" className="px-3">MedAgentMatrix</Navbar.Brand>
                    <Nav className="me-auto">
                        <Nav.Link as={Link} to="/">任务面板</Nav.Link>
                        <Nav.Link as={Link} to="/review">人工审核</Nav.Link>
                    </Nav>
                </Navbar>
                
                <Routes>
                    <Route path="/" element={
                        <Row style={{ height: 'calc(100vh - 56px)' }}>
                            <Col md={3} className="d-flex flex-column p-3">
                                <Card className="mb-3">
                                    <Card.Body>
                                        <Card.Title>任务状态</Card.Title>
                                        <p><strong>任务ID:</strong> {currentTaskId || '无'}</p>
                                        <p><strong>状态:</strong> {currentTaskStatus}</p>
                                    </Card.Body>
                                </Card>
                                <Card className="mb-3 flex-grow-1">
                                    <Card.Body>
                                        <Card.Title>提交新商品</Card.Title>
                                        <Form onSubmit={handleSubmit}>
                                            <Form.Group className="mb-3">
                                                <Form.Label>商品信息 (原始文本)</Form.Label>
                                                <Form.Control as="textarea" rows={15} placeholder='粘贴商品描述...' value={productInfo} onChange={(e) => setProductInfo(e.target.value)} />
                                            </Form.Group>
                                            <Button variant="primary" type="submit">提交</Button>
                                        </Form>
                                    </Card.Body>
                                </Card>
                            </Col>

                            <Col md={6} className="border rounded h-100 p-3">
                                <ReactFlow
                                    nodes={nodes}
                                    edges={edges}
                                    onNodesChange={onNodesChange}
                                    onEdgesChange={onEdgesChange}
                                    onNodeClick={onNodeClick}
                                    fitView
                                />
                            </Col>

                            <Col md={3} className="d-flex flex-column p-3">
                                {reviewItem && (
                                    <Card className="mb-3 border-warning">
                                        <Card.Body>
                                            <Card.Title className="text-warning">人工审核 (ID: {reviewItem.review_id})</Card.Title>
                                            <p><strong>原因:</strong> {reviewItem.review_reason}</p>
                                            <Button variant="success" className="me-2" onClick={() => handleReviewSubmit(true)}>批准</Button>
                                            <Button variant="danger" onClick={() => handleReviewSubmit(false)}>拒绝</Button>
                                        </Card.Body>
                                    </Card>
                                )}
                                {selectedNodeState && (
                                    <Card className="mb-3">
                                        <Card.Body>
                                            <Card.Title>节点详情: {selectedNodeState.node}</Card.Title>
                                            <pre style={{ maxHeight: '200px', overflowY: 'auto' }}>
                                                {JSON.stringify(selectedNodeState.state, null, 2)}
                                            </pre>
                                        </Card.Body>
                                    </Card>
                                )}
                                <Card className="flex-grow-1">
                                    <Card.Body>
                                        <Card.Title>处理历史</Card.Title>
                                        <ListGroup style={{ maxHeight: '100%', overflowY: 'auto' }}>
                                            {taskHistory.map((h, i) => (
                                                <ListGroup.Item key={i} action onClick={() => setSelectedNodeState(h)}>
                                                    步骤 {i + 1}: <strong>{h.node}</strong>
                                                </ListGroup.Item>
                                            ))}
                                        </ListGroup>
                                    </Card.Body>
                                </Card>
                            </Col>
                        </Row>
                    } />
                    <Route path="/review" element={<ReviewQueuePage />} />
                    <Route path="/review/:id" element={<ReviewDetailPage />} />
                </Routes>
            </Container>
        </Router>
    );
}

export default App;