import React, { useState, useEffect } from 'react';
import { Card, Typography, Spin, Select, Badge, Button, Space, Statistic, Empty, Tooltip, List, Divider } from 'antd';
import { ReloadOutlined, DatabaseOutlined, LinkOutlined, DisconnectOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { getQdrantCollections, getCollectionStats } from '../api';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

const QdrantConnectionComponent = ({ onCollectionSelected }) => {
  const [collections, setCollections] = useState([]);
  const [selectedCollection, setSelectedCollection] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('disconnected'); // 'connected', 'disconnected', 'connecting'
  const [collectionStats, setCollectionStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 連接到Qdrant服務器並獲取集合列表
  const connectToQdrant = async () => {
    setLoading(true);
    setConnectionStatus('connecting');
    setError(null);
    
    try {
      const collectionsData = await getQdrantCollections();
      setCollections(collectionsData);
      setConnectionStatus('connected');
      
      // 如果有集合且沒有選擇過，默認選擇第一個集合
      if (collectionsData.length > 0 && !selectedCollection) {
        setSelectedCollection(collectionsData[0].name);
        fetchCollectionStats(collectionsData[0].name);
        if (onCollectionSelected) {
          onCollectionSelected(collectionsData[0]);
        }
      }
    } catch (error) {
      setError('連接Qdrant失敗: ' + error.message);
      setConnectionStatus('disconnected');
      console.error('Error connecting to Qdrant:', error);
    } finally {
      setLoading(false);
    }
  };

  // 獲取集合統計信息
  const fetchCollectionStats = async (collectionName) => {
    if (!collectionName) return;
    
    setLoading(true);
    
    try {
      const stats = await getCollectionStats(collectionName);
      setCollectionStats(stats);
    } catch (error) {
      setError('獲取集合統計信息失敗: ' + error.message);
      console.error('Error fetching collection stats:', error);
    } finally {
      setLoading(false);
    }
  };

  // 組件掛載時嘗試連接Qdrant
  useEffect(() => {
    connectToQdrant();
    //console.log('useEffect fired');
  }, []);

  // 處理集合選擇變更
  const handleCollectionChange = (collectionName) => {
    setSelectedCollection(collectionName);
    fetchCollectionStats(collectionName);
    
    const collection = collections.find(c => c.name === collectionName);
    if (collection && onCollectionSelected) {
      onCollectionSelected(collection);
    }
  };

  // 獲取連接狀態徽章
  const getConnectionBadge = () => {
    switch(connectionStatus) {
      case 'connected':
        return <Badge status="success" text="已連接" />;
      case 'connecting':
        return <Badge status="processing" text="連接中..." />;
      case 'disconnected':
        return <Badge status="error" text="未連接" />;
      default:
        return <Badge status="default" text="未知狀態" />;
    }
  };

  return (
    <div className="qdrant-connection-container">
      <Title level={4}>Qdrant向量數據庫</Title>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Text type="secondary">連接到向量數據庫並選擇集合</Text>
        <Space>
          {getConnectionBadge()}
          <Tooltip title="重新連接">
            <Button 
              icon={<ReloadOutlined />} 
              onClick={connectToQdrant} 
              loading={loading && connectionStatus === 'connecting'}
              size="small"
            />
          </Tooltip>
        </Space>
      </div>
      
      {connectionStatus === 'connected' ? (
        <>
          <div style={{ marginBottom: 16 }}>
            <Select
              style={{ width: '100%' }}
              placeholder="選擇集合"
              value={selectedCollection}
              onChange={handleCollectionChange}
              disabled={loading || collections.length === 0}
            >
              {collections.map(collection => (
                <Option key={collection.name} value={collection.name}>
                  <Space>
                    <DatabaseOutlined />
                    {collection.name}
                    <Text type="secondary">({collection.vectorCount} 向量)</Text>
                  </Space>
                </Option>
              ))}
            </Select>
          </div>
          
          {loading && <Spin tip="加載中..." />}
          
          {error && (
            <Paragraph type="danger">
              {error}
            </Paragraph>
          )}
          
          {selectedCollection && collectionStats && !loading ? (
            <Card size="small">
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <Text strong>集合統計信息</Text>
                <Text type="secondary">{selectedCollection}</Text>
              </div>
              
              <Divider style={{ margin: '8px 0' }} />
              
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px' }}>
                <Statistic 
                  title="向量數量" 
                  value={collectionStats.vectorCount} 
                  valueStyle={{ fontSize: '16px' }}
                />
                <Statistic 
                  title="向量維度" 
                  value={collectionStats.vectorDimension} 
                  valueStyle={{ fontSize: '16px' }}
                />
                <Statistic 
                  title="磁盤使用" 
                  value={collectionStats.diskUsage} 
                  valueStyle={{ fontSize: '16px' }}
                />
              </div>
              
              <List
                size="small"
                style={{ marginTop: 8 }}
                dataSource={[
                  { label: '索引類型', value: collectionStats.indexType },
                  { label: '創建日期', value: collectionStats.created },
                  { label: '最後修改', value: collectionStats.lastModified }
                ]}
                renderItem={item => (
                  <List.Item style={{ padding: '4px 0' }}>
                    <Text type="secondary">{item.label}:</Text>
                    <Text>{item.value}</Text>
                  </List.Item>
                )}
              />
            </Card>
          ) : !loading && selectedCollection ? (
            <Empty description="無法獲取集合統計信息" />
          ) : null}
        </>
      ) : (
        <div style={{ textAlign: 'center', padding: '20px 0' }}>
          <Space direction="vertical" align="center">
            {connectionStatus === 'connecting' ? (
              <Spin tip="正在連接到Qdrant..." />
            ) : (
              <>
                <DisconnectOutlined style={{ fontSize: 32, color: '#ff4d4f' }} />
                <Text>未連接到Qdrant向量數據庫</Text>
                <Button 
                  type="primary" 
                  icon={<LinkOutlined />} 
                  onClick={connectToQdrant}
                  loading={loading}
                >
                  連接
                </Button>
              </>
            )}
          </Space>
        </div>
      )}
      
      <div style={{ marginTop: 16 }}>
        <Text type="secondary">
          <InfoCircleOutlined style={{ marginRight: 8 }} />
          向量數據庫存儲文檔的嵌入向量，用於相似性搜索和檢索
        </Text>
      </div>
    </div>
  );
};

export default QdrantConnectionComponent;
