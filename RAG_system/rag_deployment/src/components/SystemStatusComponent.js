import React, { useState, useEffect } from 'react';
import { Card, Typography, Statistic, Row, Col, Progress, Timeline, Badge, Space, Divider } from 'antd';
import { DashboardOutlined, ClockCircleOutlined, WarningOutlined } from '@ant-design/icons';
import { getSystemStatus } from '../api';

const { Title, Text, Paragraph } = Typography;

const SystemStatusComponent = ({ status: externalStatus }) => {
  const [status, setStatus] = useState({
    cpuUsage: 0,
    memoryUsage: 0,
    status: 'idle',
    message: '載入中...',
    lastUpdated: new Date().toISOString()
  });
  const [logs, setLogs] = useState([]);

  // 監聽外部狀態變化
  useEffect(() => {
    if (externalStatus?.message && externalStatus.message !== '系統就緒') {
      const newLog = {
        time: new Date().toLocaleTimeString(),
        message: externalStatus.message,
        type: externalStatus.status
      };
      setLogs(prev => [newLog, ...prev].slice(0, 5));
    }
  }, [externalStatus?.message]);

  // 🔁 每 5 秒呼叫後端 API 獲取系統狀態
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const newStatus = await getSystemStatus();

        // 更新系統資源使用率
        setStatus(prev => ({
          ...prev,
          cpuUsage: newStatus.cpuUsage,
          memoryUsage: newStatus.memoryUsage,
          lastUpdated: newStatus.lastUpdated
        }));

        // 加入日誌（僅記錄後端的錯誤狀態）
        if (newStatus.status === 'error' && newStatus.message) {
          const newLog = {
            time: new Date().toLocaleTimeString(),
            message: newStatus.message,
            type: newStatus.status
          };
          setLogs(prev => [newLog, ...prev].slice(0, 5));
        }
      } catch (err) {
        console.error('無法取得系統狀態:', err);
        setStatus(prev => ({
          ...prev,
          status: 'error',
          message: '無法取得系統狀態'
        }));
      }
    };

    fetchStatus(); // 第一次立即呼叫
    const interval = setInterval(fetchStatus, 5000); // 每 5 秒更新
    return () => clearInterval(interval); // 清除 interval
  }, []);

  const getStatusColor = (statusType) => {
    switch (statusType) {
      case 'idle': return 'green';
      case 'processing': return 'blue';
      case 'error': return 'red';
      default: return 'gray';
    }
  };

  return (
    <div className="system-status-container">
      <Title level={4}>
        <DashboardOutlined style={{ marginRight: 8 }} />
        系統狀態
      </Title>

      <Row gutter={[16, 16]}>
        <Col span={12}>
          <Card size="small">
            <Statistic title="CPU 使用率" value={status.cpuUsage.toFixed(1)} suffix="%" />
            <Progress
              percent={status.cpuUsage}
              status={status.cpuUsage > 80 ? 'exception' : 'normal'}
              showInfo={false}
              strokeColor={status.cpuUsage > 80 ? '#ff4d4f' : '#87d068'}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card size="small">
            <Statistic title="記憶體使用率" value={status.memoryUsage.toFixed(1)} suffix="%" />
            <Progress
              percent={status.memoryUsage}
              status={status.memoryUsage > 80 ? 'exception' : 'normal'}
              showInfo={false}
              strokeColor={status.memoryUsage > 80 ? '#ff4d4f' : '#87d068'}
            />
          </Card>
        </Col>
      </Row>

      <Divider style={{ margin: '16px 0' }} />

      <div>
        <Text strong>系統日誌</Text>
        <div style={{ marginTop: 8 }}>
          {logs.length > 0 ? (
            <Timeline style={{ marginTop: 8 }}>
              {logs.map((log, index) => (
                <Timeline.Item
                  key={index}
                  color={getStatusColor(log.type)}
                  dot={log.type === 'error' ? <WarningOutlined style={{ fontSize: 16 }} /> : null}
                >
                  <Space>
                    <Text type="secondary">{log.time}</Text>
                    <Text>{log.message}</Text>
                  </Space>
                </Timeline.Item>
              ))}
            </Timeline>
          ) : (
            <Paragraph type="secondary" style={{ textAlign: 'center', margin: '16px 0' }}>
              尚無系統日誌
            </Paragraph>
          )}
        </div>
      </div>

      <div style={{ marginTop: 8 }}>
        <Space>
          <ClockCircleOutlined />
          <Text type="secondary">
            最後更新: {new Date(status.lastUpdated).toLocaleTimeString()}
          </Text>
        </Space>
      </div>
    </div>
  );
};

export default SystemStatusComponent;