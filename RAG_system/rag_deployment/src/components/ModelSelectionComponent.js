import React, { useState, useEffect } from 'react';
import { Select, Card, Typography, Spin, List, Tag, Space, Tooltip, Button } from 'antd';
import { ReloadOutlined, InfoCircleOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { getOllamaModels } from '../api';

const { Option } = Select;
const { Title, Text, Paragraph } = Typography;

const ModelSelectionComponent = ({ onModelSelected }) => {
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 從後端獲取模型列表
  const fetchModels = async () => {
    setLoading(true);
    setError(null);

    try {
      const modelList = await getOllamaModels();
      setModels(modelList);

      // 自動選擇第一個 loaded 模型
      if (modelList.length > 0 && !selectedModel) {
        const defaultModel = modelList.find(m => m.loaded);
        if (defaultModel) {
          setSelectedModel(defaultModel.id);
          if (onModelSelected) {
            onModelSelected(defaultModel);
          }
        }
      }
    } catch (err) {
      setError('獲取模型列表失敗: ' + err.message);
      console.error('Error fetching models:', err);
    } finally {
      setLoading(false);
    }
  };

  // 組件掛載時獲取模型列表
  useEffect(() => {
    fetchModels();
  }, []);

  // 處理模型選擇變更
  const handleModelChange = (modelId) => {
    setSelectedModel(modelId);
    const model = models.find(m => m.id === modelId);
    if (model && onModelSelected) {
      onModelSelected(model);
    }
  };

  // 獲取模型標籤顏色
  const getTagColor = (tag) => {
    switch(tag) {
      case 'small':
        return 'green';
      case 'medium':
        return 'blue';
      case 'large':
        return 'purple';
      case 'embedding':
        return 'cyan';
      case 'reasoning':
        return 'orange';
      case 'general':
        return 'geekblue';
      default:
        return 'default';
    }
  };

  return (
    <div className="model-selection-container">
      <Title level={4}>選擇Ollama模型</Title>
      <Text type="secondary">選擇用於問答的大語言模型</Text>
      
      <div style={{ marginTop: 16, marginBottom: 16, display: 'flex', alignItems: 'center' }}>
        <Select
          style={{ width: '100%' }}
          placeholder="選擇模型"
          loading={loading}
          value={selectedModel}
          onChange={handleModelChange}
          disabled={loading}
        >
          {models.map(model => (
            <Option key={model.id} value={model.id} disabled={!model.loaded}>
              <Space>
                {model.name} ({model.size})
                {model.loaded ? 
                  <CheckCircleOutlined style={{ color: '#52c41a' }} /> : 
                  <Text type="secondary">(未加載)</Text>
                }
              </Space>
            </Option>
          ))}
        </Select>
        <Tooltip title="刷新模型列表">
          <Button 
            icon={<ReloadOutlined />} 
            onClick={fetchModels} 
            style={{ marginLeft: 8 }}
            disabled={loading}
          />
        </Tooltip>
      </div>
      
      {loading && <Spin tip="加載模型列表中..." />}
      
      {error && (
        <Paragraph type="danger">
          {error}
        </Paragraph>
      )}
      
      {selectedModel && !loading && (
        <Card size="small">
          <List.Item>
            <div style={{ width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text strong>{models.find(m => m.id === selectedModel)?.name}</Text>
                <Space>
                  {models.find(m => m.id === selectedModel)?.tags.map(tag => (
                    <Tag key={tag} color={getTagColor(tag)}>{tag}</Tag>
                  ))}
                </Space>
              </div>
              <Paragraph type="secondary" style={{ marginTop: 8, marginBottom: 0 }}>
                {models.find(m => m.id === selectedModel)?.description}
              </Paragraph>
            </div>
          </List.Item>
        </Card>
      )}
      
      <div style={{ marginTop: 16 }}>
        <Text type="secondary">
          <InfoCircleOutlined style={{ marginRight: 8 }} />
          模型大小影響推理速度和質量，較大的模型通常能提供更好的回答，但需要更多資源
        </Text>
      </div>
    </div>
  );
};

export default ModelSelectionComponent;
