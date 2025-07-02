import React, { useState, useRef, useEffect } from 'react';
import { Input, Button, Card, Typography, List, Avatar, Space, Divider, Spin, Tag, Tooltip, Collapse, Empty, Image } from 'antd';
import { SendOutlined, UserOutlined, RobotOutlined, FileTextOutlined, InfoCircleOutlined, LinkOutlined, PictureOutlined, TableOutlined } from '@ant-design/icons';
import { chatWithRag } from '../api';

const { TextArea } = Input;
const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;

const API_BASE_URL = process.env.REACT_APP_API_URL
  ? `${process.env.REACT_APP_API_URL}/api/`
  : 'http://localhost:5050/api/';

const ChatInterfaceComponent = ({ selectedModel, selectedCollection, selectedKbFromList }) => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  // 追蹤中文輸入
  const [isComposing, setIsComposing] = useState(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;
    if (!selectedModel) {
      setError('請先選擇一個模型');
      return;
    }
    if (!selectedCollection) {
      setError('請先選擇一個向量數據庫集合');
      return;
    }

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: inputValue,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setLoading(true);
    setError(null);

    try {
      const response = await chatWithRag(
        userMessage.content,
        selectedModel.id,
        selectedCollection.name,
        selectedKbFromList
      );

      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.answer,
        timestamp: new Date().toISOString(),
        sources: response.sources
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      setError('獲取回答失敗: ' + error.message);
      console.error('Error getting answer:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    setInputValue(e.target.value);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !isComposing) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatMessageContent = (content) => {
    return content.split('\n').map((line, i) => (
      <React.Fragment key={i}>
        {line}
        {i < content.split('\n').length - 1 && <br />}
      </React.Fragment>
    ));
  };

  const renderImageReferences = (refs, type) => {
    if (!refs || refs.length === 0) return null;

    const icon = type === 'image' ? <PictureOutlined /> : <TableOutlined />;
    const title = type === 'image' ? '圖片參考' : '表格參考';

    return (
      <div style={{ marginTop: '8px' }}>
        <Text type="secondary">
          {icon} {title}:
        </Text>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', marginTop: '8px' }}>
          {refs.map((ref, idx) => (
            <div key={idx} style={{ width: '100%', maxWidth: '300px', marginBottom: '10px' }}>
              <Image
                src={`${API_BASE_URL}figure_storage/${ref}`}
                //src={`http://127.0.0.1:5050/api/figure_storage/${ref}`}
                alt={`${type === 'image' ? '圖片' : '表格'} ${idx + 1}`}
                style={{ width: '100%', objectFit: 'contain', border: '1px solid #f0f0f0', borderRadius: '4px' }}
                fallback="/fallback.png"
              />
              <div style={{ textAlign: 'center', marginTop: '4px' }}>
                <Text type="secondary" style={{ fontSize: '12px' }}>{ref}</Text>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="chat-interface-container" style={{ 
      display: 'flex', 
      flexDirection: 'column', 
      height: '100%',
      width: '100%',
      position: 'relative'
    }}>
      <div style={{ marginBottom: '16px' }}>
        <Title level={4} style={{ margin: 0 }}>RAG問答系統</Title>
        <Text type="secondary">基於您上傳的文檔進行問答</Text>
      </div>

      <div className="chat-messages" style={{ 
        flex: '1 1 auto', 
        overflowY: 'auto', 
        padding: '16px', 
        border: '1px solid #f0f0f0', 
        borderRadius: '4px', 
        backgroundColor: '#f9f9f9',
        marginBottom: '16px',
        minHeight: '200px' // 確保聊天區域有最小高度
      }}>
        {messages.length === 0 ? (
          <Empty description="尚無對話歷史，請輸入您的問題" />
        ) : (
          <List
            itemLayout="horizontal"
            dataSource={messages}
            renderItem={message => (
              <List.Item style={{ padding: '8px 0' }}>
                <div style={{ width: '100%' }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', marginBottom: '8px' }}>
                    <Avatar icon={message.role === 'user' ? <UserOutlined /> : <RobotOutlined />} style={{ backgroundColor: message.role === 'user' ? '#1890ff' : '#52c41a', marginRight: '8px' }} />
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Text strong>{message.role === 'user' ? '您' : 'AI助手'}</Text>
                        <Text type="secondary" style={{ fontSize: '12px' }}>{new Date(message.timestamp).toLocaleTimeString()}</Text>
                      </div>
                      <div style={{ marginTop: '4px', padding: '8px 12px', backgroundColor: message.role === 'user' ? '#e6f7ff' : '#f6ffed', borderRadius: '4px' }}>
                        <Paragraph style={{ margin: 0 }}>{formatMessageContent(message.content)}</Paragraph>
                      </div>
                    </div>
                  </div>

                  {message.sources && message.sources.length > 0 && (
                    <div style={{ marginLeft: '40px', marginTop: '8px' }}>
                      <Collapse ghost>
                        <Panel header={<Text type="secondary"><InfoCircleOutlined /> 查看引用來源 ({message.sources.length})</Text>} key="1">
                          <List
                            size="small"
                            dataSource={message.sources}
                            renderItem={(source, index) => (
                              <List.Item style={{ padding: '8px 0' }}>
                                <Space direction="vertical" style={{ width: '100%' }}>
                                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <Space>
                                      <FileTextOutlined />
                                      <Text strong>{source.source}</Text>
                                      <Text type="secondary">頁面 {source.page}</Text>
                                    </Space>
                                    <Tag color="blue">相關度: {(source.score * 100).toFixed(0)}%</Tag>
                                  </div>
                                  <div style={{ padding: '8px', backgroundColor: '#f5f5f5', borderRadius: '4px', fontSize: '13px' }}>
                                    "{source.text}"
                                  </div>
                                  {source.image_ref && source.image_ref.length > 0 && renderImageReferences(source.image_ref, 'image')}
                                  {source.table_ref && source.table_ref.length > 0 && renderImageReferences(source.table_ref, 'table')}
                                </Space>
                              </List.Item>
                            )}
                          />
                        </Panel>
                      </Collapse>
                    </div>
                  )}
                </div>
              </List.Item>
            )}
          />
        )}

        {loading && (
          <div style={{ textAlign: 'center', padding: '20px 0' }}>
            <Spin tip="思考中..." />
          </div>
        )}

        {error && (
          <div style={{ margin: '8px 0', padding: '8px', backgroundColor: '#fff2f0', borderRadius: '4px' }}>
            <Text type="danger">{error}</Text>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div style={{ 
        display: 'flex', 
        marginBottom: '16px',
        flex: '0 0 auto' // 確保輸入區域不會被壓縮
      }}>
        <TextArea
          value={inputValue}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onCompositionStart={() => setIsComposing(true)}
          onCompositionEnd={() => setIsComposing(false)}   
          placeholder="輸入您的問題..."
          autoSize={{ minRows: 2, maxRows: 6 }}
          disabled={loading || !selectedModel || !selectedCollection}
          style={{ marginRight: '8px', flex: 1 }}
        />
        <Button 
          type="primary" 
          icon={<SendOutlined />} 
          onClick={handleSendMessage} 
          loading={loading}
          disabled={!inputValue.trim() || !selectedModel || !selectedCollection}
        >
          發送
        </Button>
      </div>

      <div style={{ marginBottom: '8px', flex: '0 0 auto' }}>
        {!selectedModel && (
          <Text type="warning" style={{ marginRight: '16px' }}>
            <InfoCircleOutlined style={{ marginRight: '4px' }} />
            請先選擇一個模型
          </Text>
        )}
        {!selectedCollection && (
          <Text type="warning">
            <InfoCircleOutlined style={{ marginRight: '4px' }} />
            請先選擇一個向量數據庫集合
          </Text>
        )}
      </div>

      <div style={{ flex: '0 0 auto' }}>
        <Text type="secondary">
          <InfoCircleOutlined style={{ marginRight: '8px' }} />
          系統會基於您上傳的文檔內容回答問題，如果沒有相關信息，可能無法提供準確答案
        </Text>
      </div>
    </div>
  );
};

export default ChatInterfaceComponent;
