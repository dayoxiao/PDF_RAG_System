import React, { useState } from 'react';
import { Layout, Menu, Typography, Divider, Card, Row, Col, Alert, Badge, Button, Modal } from 'antd';
import { UploadOutlined, RobotOutlined, DatabaseOutlined, MessageOutlined, DashboardOutlined } from '@ant-design/icons';

import FileUploadComponent from './components/FileUploadComponent';
import ModelSelectionComponent from './components/ModelSelectionComponent';
import QdrantConnectionComponent from './components/QdrantConnectionComponent';
import ChatInterfaceComponent from './components/ChatInterfaceComponent';
import SystemStatusComponent from './components/SystemStatusComponent';

const { Header, Sider, Content } = Layout;
const { Title, Text } = Typography;

function App() {
  const [selectedModel, setSelectedModel] = useState(null);
  const [selectedCollection, setSelectedCollection] = useState(null);
  // 知識庫選擇
  const [selectedKbFromList, setSelectedKbFromList] = useState(null);
  const [systemStatus, setSystemStatus] = useState({
    status: 'idle', // 'idle', 'processing', 'error'
    message: '系統就緒',
    cpuUsage: 0,
    memoryUsage: 0,
    lastUpdated: new Date().toISOString()
  });
  const [isStatusModalVisible, setIsStatusModalVisible] = useState(false); // State for status modal

  // 處理模型選擇
  const handleModelSelected = (model) => {
    setSelectedModel(model);
    console.log('Selected model:', model);
    
    // 更新系統狀態
    setSystemStatus(prev => ({
      ...prev,
      status: 'idle',
      message: `已選擇模型: ${model.name}`,
      lastUpdated: new Date().toISOString()
    }));
  };

  // 處理集合選擇
  const handleCollectionSelected = (collection) => {
    setSelectedCollection(collection);
    console.log('Selected collection:', collection);
    
    // 更新系統狀態
    setSystemStatus(prev => ({
      ...prev,
      status: 'idle',
      message: `已選擇集合: ${collection.name}`,
      lastUpdated: new Date().toISOString()
    }));
  };

  // 處理文件處理完成
  const handleFileProcessed = (file, data) => {
    console.log('File processed:', file, data);
    
    // 更新系統狀態
    setSystemStatus(prev => ({
      ...prev,
      status: 'idle',
      message: `文件 ${file.name} 處理完成`,
      lastUpdated: new Date().toISOString()
    }));
  };

  // 處理知識庫選擇
  const handleKbSelected = (kbName) => {
    setSelectedKbFromList(kbName);
    console.log('Selected knowledge base:', kbName);
    
    // 更新系統狀態
    setSystemStatus(prev => ({
      ...prev,
      status: 'idle',
      message: `已選擇知識庫: ${kbName}`,
      lastUpdated: new Date().toISOString()
    }));
  };

  // 處理系統狀態更新
  const handleStatusUpdate = (newStatus) => {
    setSystemStatus(prev => ({
      ...prev,
      ...newStatus,
      lastUpdated: new Date().toISOString()
    }));
  };

  // 處理浮動按鈕點擊
  const handleFloatingStatusButtonClick = () => {
    setIsStatusModalVisible(true);
  };

  // 處理 Modal 關閉
  const handleStatusModalClose = () => {
    setIsStatusModalVisible(false);
  };

  return (
    <Layout style={{ minHeight: '100vh', height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', alignItems: 'center', flex: '0 0 auto' }}>
        <Title level={3} style={{ margin: 0, marginRight: '16px' }}>本地RAG系統</Title>
        <Badge 
          status={systemStatus.status === 'idle' ? 'success' : systemStatus.status === 'processing' ? 'processing' : 'error'} 
          text={systemStatus.message} 
        />
      </Header>
      <Layout style={{ flex: '1 1 auto', display: 'flex', overflow: 'hidden' }}>
        <Sider width={400} style={{ background: '#fff', padding: '24px', overflow: 'auto', height: '100%' }}>
          <div style={{ marginBottom: '24px' }}>
            <FileUploadComponent 
              onFileProcessed={handleFileProcessed}
              selectedCollection={selectedCollection}
              // 傳遞知識庫選擇
              onKbSelected={handleKbSelected}
            />
          </div>
          <Divider />
          <div style={{ marginBottom: '24px' }}>
            <ModelSelectionComponent onModelSelected={handleModelSelected} />
          </div>
          <Divider />
          <div>
            <QdrantConnectionComponent onCollectionSelected={handleCollectionSelected} />
          </div>
        </Sider>
        <Content style={{ 
          padding: '24px', 
          background: '#f0f2f5', 
          height: '100%', 
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column'
        }}>
          <Row style={{ 
            height: '100%', 
            flex: '1 1 auto',
            display: 'flex'
          }}>
            <Col span={24} style={{ 
              height: '100%',
              display: 'flex',
              flexDirection: 'column'
            }}>
              <Card style={{ 
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                flex: '1 1 auto'
              }}
              bodyStyle={{ 
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                padding: '16px',
                flex: '1 1 auto'
              }}>
                <ChatInterfaceComponent 
                  selectedModel={selectedModel} 
                  selectedCollection={selectedCollection}
                  // 傳遞知識庫選擇
                  selectedKbFromList={selectedKbFromList}
                />
              </Card>
            </Col>
          </Row>
        </Content>

        {/* Floating Button for System Status */}
        <Button
          type="primary"
          shape="circle"
          icon={<DashboardOutlined />}
          size="large"
          style={{
            position: 'fixed',
            bottom: '24px',
            right: '24px',
            zIndex: 1001,
          }}
          onClick={handleFloatingStatusButtonClick} // Call the handler
        />

      </Layout>

      {/* System Status Modal */}
      <Modal
        title="系統狀態"
        visible={isStatusModalVisible}
        onCancel={handleStatusModalClose}
        footer={null} // No footer buttons
      >
        <SystemStatusComponent 
          status={systemStatus} 
          onStatusUpdate={handleStatusUpdate} 
        />
      </Modal>

    </Layout>
  );
}

export default App;
