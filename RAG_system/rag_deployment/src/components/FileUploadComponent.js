import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Upload, Button, List, Card, Progress, message, Typography, Space, Tooltip, Modal, Switch, Radio, Select, Input, Form, Divider, Alert, Row, Col, Tag, Spin, Empty } from 'antd';
import { InboxOutlined, FileOutlined, DeleteOutlined, CheckCircleOutlined, SyncOutlined, ExclamationCircleOutlined, UploadOutlined, QuestionCircleOutlined, InfoCircleOutlined, DatabaseOutlined, ReloadOutlined } from '@ant-design/icons';
import { uploadPdfDocument, getKnowledgeBases, getKnowledgeBaseDocuments, deleteDocument } from '../api';

const { Dragger } = Upload;
const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

const FileUploadComponent = ({ onFileProcessed, selectedCollection, onKbSelected }) => {
  const [fileList, setFileList] = useState([]);
  const [uploading, setUploading] = useState(false); 
  const [isProcessing, setIsProcessing] = useState(false); 
  const onKbSelectedRef = useRef(onKbSelected);

  const [doOcr, setDoOcr] = useState(false);
  const [doImageSummary, setDoImageSummary] = useState(true);
  const [kbMode, setKbMode] = useState('select'); 
  const [existingKbList, setExistingKbList] = useState([]);
  const [selectedKbFromList, setSelectedKbFromList] = useState(null);
  const [manualKbName, setManualKbName] = useState('');
  const [kbLoading, setKbLoading] = useState(false);
  const [kbError, setKbError] = useState(null);

  // 新增狀態
  const [selectedKbDocuments, setSelectedKbDocuments] = useState([]);
  const [isLoadingKbDocuments, setIsLoadingKbDocuments] = useState(false);
  const [kbDocumentsError, setKbDocumentsError] = useState(null);
  const [isDeletingDocument, setIsDeletingDocument] = useState(false);

  const processingStates = {
    PENDING: 'pending',
    UPLOADING: 'uploading',
    COMPLETED: 'completed',
    ERROR: 'error',
  };

  // 獲取知識庫列表
  const fetchKnowledgeBases = useCallback(async (collectionName) => {
    if (!collectionName) {
      setKbError('未選擇集合，無法獲取知識庫列表');
      return;
    }
    
    setKbLoading(true);
    setKbError(null);
    try {
      const response = await getKnowledgeBases(collectionName);
      const kbs = response.knowledge_bases || [];
      setExistingKbList(kbs);
      if (kbs.length > 0) {
        // 如果目前的 selected 不在新的列表中，才改成第一個
        setSelectedKbFromList(prev => (kbs.includes(prev) ? prev : kbs[0]));
      } else {
        setSelectedKbFromList(null);
      }
      // if (kbs.length > 0 && !selectedKbFromList) {
      //   setSelectedKbFromList(kbs[0]);
      // }
    } catch (error) {
      console.error('Error fetching knowledge bases:', error);
      setKbError('無法獲取知識庫列表: ' + (error.response?.data?.error || error.message));
      setExistingKbList([]);
    } finally {
      setKbLoading(false);
    }
  }, [selectedKbFromList]);

  // 獲取知識庫內文檔列表
  const fetchKbDocuments = useCallback(async (collectionName, kbName) => {
    if (!collectionName || !kbName) {
      setSelectedKbDocuments([]);
      return;
    }
    
    setIsLoadingKbDocuments(true);
    setKbDocumentsError(null);
    
    try {
      const response = await getKnowledgeBaseDocuments(collectionName, kbName);
      setSelectedKbDocuments(response || []);
      // 使用 ref 來調用回調
      onKbSelectedRef.current?.(kbName);
    } catch (error) {
      console.error('Error fetching KB documents:', error);
      setKbDocumentsError('無法獲取知識庫文檔列表: ' + (error.response?.data?.error || error.message));
      setSelectedKbDocuments([]);
    } finally {
      setIsLoadingKbDocuments(false);
    }
  }, []);

  // 當選擇集合變更時，獲取知識庫列表
  useEffect(() => {
    if (selectedCollection && selectedCollection.name) {
      fetchKnowledgeBases(selectedCollection.name);
    }
  }, [selectedCollection, fetchKnowledgeBases]);

  // 當知識庫選擇變更時，獲取文檔列表
  useEffect(() => {
    if (selectedCollection && selectedCollection.name) {
      if (kbMode === 'select' && selectedKbFromList) {
        fetchKbDocuments(selectedCollection.name, selectedKbFromList);
      } else if (kbMode === 'create' && manualKbName.trim()) {
        // 對於新創建的知識庫，清空文檔列表
        setSelectedKbDocuments([]);
      }
    }
  }, [kbMode, selectedKbFromList, manualKbName, selectedCollection, fetchKbDocuments]);

  // 更新 ref 當 onKbSelected 改變時
  useEffect(() => {
    onKbSelectedRef.current = onKbSelected;
  }, [onKbSelected]);

  const updateFileStatusAndProgress = (fileId, status, percent = null, file_id_from_backend = null, error_message = null) => {
    setFileList(prevList =>
      prevList.map(file => {
        if (file.uid === fileId) {
          const updatedFile = { ...file, status };
          if (percent !== null) updatedFile.percent = percent;
          if (file_id_from_backend) updatedFile.file_id = file_id_from_backend;
          if (error_message) updatedFile.errorMessage = error_message;
          return updatedFile;
        }
        return file;
      })
    );
  };

  const handleFileChange = (info) => {
    let newFileList = [...info.fileList];
    newFileList = newFileList.filter(file => {
      if (file.type && !file.type.includes('pdf') && file.status !== 'removed') {
        message.error(`${file.name} 不是PDF文件，已被過濾`);
        return false;
      }
      return true;
    }).map(file => {
      if (!file.status) { 
        return { ...file, status: processingStates.PENDING, percent: 0 };
      }
      return file;
    });
    setFileList(newFileList);
  };

  const handleRemoveFileFromUploadList = (fileToRemove) => {
    setFileList(prevList => prevList.filter(file => file.uid !== fileToRemove.uid));
  };

  // 檢查知識庫名稱是否已存在
  const checkKbNameExists = useCallback(async (kbName) => {
    if (!selectedCollection || !selectedCollection.name) return null;
    
    try {
      const response = await getKnowledgeBases(selectedCollection.name);
      const kbs = response.knowledge_bases || [];
      
      // 尋找匹配的知識庫名稱（比較截斷後的名稱）
      const existingKb = kbs.find(existingKbName => {
        const existingPrefix = existingKbName.split('_').slice(0, -1).join('_');
        return existingPrefix === kbName;
      });
      
      return existingKb || null;
    } catch (error) {
      console.error('Error checking KB name:', error);
      return null;
    }
  }, [selectedCollection]);

  // 處理知識庫名稱輸入
  const handleKbNameChange = async (e) => {
    const newName = e.target.value.trim();
    setManualKbName(newName);
    
    if (newName) {
      const existingKb = await checkKbNameExists(newName);
      if (existingKb) {
        message.info('此知識庫名稱已存在，您可以繼續輸入或選擇使用現有知識庫');
        // 使用完整的知識庫名稱（包含ID）獲取文檔
        fetchKbDocuments(selectedCollection.name, existingKb);
      } else {
        // 如果不存在，清空文檔列表
        setSelectedKbDocuments([]);
      }
    }
  };

  // 修改文件上傳完成後的處理
  const handleConfirmProcessFiles = async () => {
    if (fileList.filter(f => f.status === processingStates.PENDING).length === 0) {
      message.warning('沒有等待處理的文件。');
      return;
    }
    
    // 獲取當前知識庫名稱
    let currentKbName = '';
    if (kbMode === 'select') {
      if (!selectedKbFromList) {
        message.error('請選擇一個現有的知識庫。');
        return;
      }
      // 在傳遞到後端時截斷ID
      currentKbName = selectedKbFromList.split('_').slice(0, -1).join('_');
    } else {
      if (!manualKbName.trim()) {
        message.error('請輸入新的知識庫名稱。');
        return;
      }
      currentKbName = manualKbName.trim();
    }
    
    if (!selectedCollection || !selectedCollection.name) {
      message.error('請選擇一個集合。');
      return;
    }
    
    setIsProcessing(true);
    setUploading(true);
    
    const filesToProcess = fileList.filter(f => f.status === processingStates.PENDING);
    
    for (const file of filesToProcess) {
      updateFileStatusAndProgress(file.uid, processingStates.UPLOADING, 0);
      
      try {
        const response = await uploadPdfDocument(
          file.originFileObj,
          selectedCollection.name,
          currentKbName,
          doOcr,
          doImageSummary
        );
        
        updateFileStatusAndProgress(file.uid, processingStates.COMPLETED, 100, response.file_id);
        message.success(`${file.name} 已成功處理。`);
        
        if (onFileProcessed) {
          onFileProcessed({ ...file, file_id: response.file_id }, response);
        }
        
        // 上傳完成後刷新文檔列表
        if (kbMode === 'select') {
          fetchKbDocuments(selectedCollection.name, selectedKbFromList);
        } else {
          // 如果是新建的知識庫，切換到選擇模式並刷新列表
          setKbMode('select');
          setSelectedKbFromList(response.kb_name);
          fetchKbDocuments(selectedCollection.name, response.kb_name);
        }
      } catch (error) {
        console.error('Error processing file:', error);
        updateFileStatusAndProgress(
          file.uid,
          processingStates.ERROR,
          null,
          null,
          error.response?.data?.error || error.message
        );
        message.error(`${file.name} 處理失敗: ${error.response?.data?.error || error.message}`);
      }
    }
    
    setUploading(false);
    setIsProcessing(false);
  };
  
  // 刪除文檔
  const handleDeleteDocument = async (doc) => {
    Modal.confirm({
      title: '確認從知識庫刪除',
      icon: <QuestionCircleOutlined />,
      content: `確定要從知識庫中刪除 ${doc.filename} 嗎？相關向量數據也將被移除。`,
      okText: '確認刪除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        setIsDeletingDocument(true);
        try {
          await deleteDocument(
            doc.file_id,
            doc.filename,
            doc.kb_name,
            selectedCollection.name
          );
          
          message.success(`${doc.filename} 已成功從知識庫刪除。`);
          fetchKbDocuments(selectedCollection.name, doc.kb_name);
        } catch (error) {
          message.error(`刪除 ${doc.filename} 失敗: ${error.message}`);
        } finally {
          setIsDeletingDocument(false);
        }
      }
    });
  };

  const getStatusIconAndColor = (status) => {
    switch (status) {
      case processingStates.PENDING:
        return { icon: <FileOutlined />, color: 'default' };
      case processingStates.UPLOADING:
        return { icon: <SyncOutlined spin />, color: 'processing' };
      case processingStates.COMPLETED:
        return { icon: <CheckCircleOutlined />, color: 'success' };
      case processingStates.ERROR:
        return { icon: <ExclamationCircleOutlined />, color: 'error' };
      default:
        return { icon: <FileOutlined />, color: 'default' };
    }
  };

  const uploadProps = {
    name: 'file',
    multiple: true,
    fileList: fileList.map(f => ({ ...f, originFileObj: f.originFileObj || f })), 
    onChange: handleFileChange,
    onRemove: handleRemoveFileFromUploadList, 
    beforeUpload: () => false, 
    accept: '.pdf',
    showUploadList: false, 
  };

  return (
    <div className="file-upload-container">
      <Title level={4}>文件管理</Title>
      <Paragraph type="secondary">選擇或創建知識庫，管理文件，並上傳新的PDF文檔。</Paragraph>

      {/* 知識庫選擇區域 */}
      <Card style={{ marginTop: 16, marginBottom: 16 }}>
        <Form layout="vertical">
          <Form.Item label="知識庫">
            <Radio.Group onChange={(e) => setKbMode(e.target.value)} value={kbMode} disabled={isProcessing}>
              <Radio value="select">選擇現有知識庫</Radio>
              <Radio value="create">創建新知識庫</Radio>
            </Radio.Group>
          </Form.Item>

          {kbMode === 'select' ? (
            <Form.Item>
              <Select
                placeholder="選擇一個知識庫"
                value={selectedKbFromList ?? undefined}
                onChange={(value) => setSelectedKbFromList(value)}
                loading={kbLoading}
                disabled={isProcessing || kbLoading}
                style={{ width: '100%' }}
                notFoundContent={kbLoading ? <Spin size="small" /> : (kbError ? <Alert message={kbError} type="error" showIcon /> : <Empty description="無可用知識庫" />)}
              >
                {existingKbList.map(kb => <Option key={kb} value={kb}>{kb}</Option>)}
              </Select>
              {kbError && !kbLoading && (
                <div style={{ marginTop: 8 }}>
                  <Button 
                    icon={<ReloadOutlined />} 
                    size="small" 
                    onClick={() => selectedCollection && fetchKnowledgeBases(selectedCollection.name)}
                  >
                    重試
                  </Button>
                </div>
              )}
            </Form.Item>
          ) : (
            <Form.Item>
              <Input 
                placeholder="輸入新的知識庫名稱"
                value={manualKbName} 
                onChange={handleKbNameChange}
                disabled={isProcessing}
              />
            </Form.Item>
          )}
        </Form>

        {/* 知識庫文檔列表區域 */}
        {(kbMode === 'select' && selectedKbFromList) || (kbMode === 'create' && manualKbName.trim()) ? (
          <>
            <Divider style={{ margin: '16px 0' }} />
            <Title level={5}>
              知識庫 "{kbMode === 'select' ? selectedKbFromList : manualKbName}" 中的文檔
              <Button 
                icon={<ReloadOutlined />} 
                size="small" 
                style={{ marginLeft: 8 }}
                onClick={() => {
                  if (selectedCollection && selectedCollection.name) {
                    if (kbMode === 'select' && selectedKbFromList) {
                      fetchKbDocuments(selectedCollection.name, selectedKbFromList);
                    }
                  }
                }}
                disabled={isLoadingKbDocuments || kbMode === 'create'}
              >
                刷新
              </Button>
            </Title>
            
            {isLoadingKbDocuments ? (
              <div style={{ textAlign: 'center', padding: '20px 0' }}>
                <Spin tip="加載文檔中..." />
              </div>
            ) : kbDocumentsError ? (
              <Alert 
                message={kbDocumentsError} 
                type="error" 
                showIcon 
                action={
                  <Button 
                    size="small" 
                    danger 
                    onClick={() => {
                      if (selectedCollection && selectedCollection.name && kbMode === 'select' && selectedKbFromList) {
                        fetchKbDocuments(selectedCollection.name, selectedKbFromList);
                      }
                    }}
                  >
                    重試
                  </Button>
                }
              />
            ) : selectedKbDocuments.length > 0 ? (
              <List
                itemLayout="horizontal"
                dataSource={selectedKbDocuments}
                renderItem={doc => (
                  <List.Item
                    actions={[
                      <Tooltip title="刪除此文檔">
                        <Button
                          icon={<DeleteOutlined />}
                          type="text"
                          danger
                          onClick={() => handleDeleteDocument(doc)}
                          loading={isDeletingDocument}
                        />
                      </Tooltip>
                    ]}
                  >
                    <List.Item.Meta
                      avatar={<DatabaseOutlined />}
                      title={<Text>{doc.filename}</Text>}
                      description={<Text type="secondary">ID: {doc.file_id}</Text>}
                    />
                  </List.Item>
                )}
              />
            ) : (
              <Empty
                description={
                  <span>
                    {kbMode === 'select'
                      ? '此知識庫中目前沒有文檔'
                      : '新建的知識庫中沒有文檔，請上傳文件'}
                  </span>
                }
              />
            )}
          </>
        ) : null}
      </Card>

      {/* 上傳區域 */}
      <Card style={{ marginBottom: 16 }}>
        <Title level={5}>上傳新文件</Title>
        <Paragraph type="secondary">將文件拖放到下方區域或點擊選擇文件，設定處理選項後，點擊「確認處理文件」按鈕開始處理。</Paragraph>

        <Dragger {...uploadProps} style={{ marginTop: 16, marginBottom: 16 }} disabled={isProcessing}>
          <p className="ant-upload-drag-icon"><InboxOutlined /></p>
          <p className="ant-upload-text">點擊或拖放PDF文件到此區域</p>
          <p className="ant-upload-hint">僅支持PDF格式。處理選項可在下方設定。</p>
        </Dragger>

        <Form layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="OCR文字識別">
                <Switch checked={doOcr} onChange={setDoOcr} disabled={isProcessing} />
                <Text type="secondary" style={{ marginLeft: 8 }}>{doOcr ? '啟用' : '停用'}</Text>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="圖片內容摘要">
                <Switch checked={doImageSummary} onChange={setDoImageSummary} disabled={isProcessing} />
                <Text type="secondary" style={{ marginLeft: 8 }}>{doImageSummary ? '啟用' : '停用'}</Text>
              </Form.Item>
            </Col>
          </Row>
        </Form>

        {/* 待處理文件列表 */}
        {fileList.length > 0 && (
          <>
            <Divider style={{ margin: '16px 0' }} />
            <List
              header={<Text strong>待處理文件列表 ({fileList.filter(f=>f.status === processingStates.PENDING).length} 個等待 / {fileList.length} 個總計)</Text>}
              itemLayout="horizontal"
              dataSource={fileList}
              renderItem={file => {
                const { icon, color } = getStatusIconAndColor(file.status);
                return (
                  <Card size="small" style={{ marginTop: 8, opacity: isProcessing && file.status === processingStates.PENDING ? 0.5 : 1}}>
                    <List.Item
                      actions={[
                        !isProcessing && (
                            <Tooltip title="從列表移除">
                                <Button icon={<DeleteOutlined />} type="text" danger onClick={() => handleRemoveFileFromUploadList(file)} />
                            </Tooltip>
                        )
                      ].filter(Boolean)}
                    >
                      <List.Item.Meta
                        avatar={icon}
                        title={<Text strong>{file.name}</Text>}
                        description={
                            <> 
                                <Tag color={color}>{file.status.toUpperCase()}</Tag>
                                {file.status === processingStates.UPLOADING && <Progress percent={file.percent} size="small" />}
                                {file.status === processingStates.ERROR && <Text type="danger">{file.errorMessage}</Text>}
                                {file.file_id && <Text type="secondary" style={{marginLeft: 8}}>ID: {file.file_id}</Text>}
                            </>
                        }
                      />
                    </List.Item>
                  </Card>
                );
              }}
            />
            <div style={{ marginTop: 24, textAlign: 'right' }}>
              <Button 
                onClick={() => setFileList([])} 
                style={{ marginRight: 8 }} 
                disabled={isProcessing || fileList.length === 0}
              >
                清空列表
              </Button>
              <Button 
                type="primary" 
                icon={<UploadOutlined />} 
                onClick={handleConfirmProcessFiles} 
                loading={uploading} 
                disabled={isProcessing || fileList.filter(f => f.status === processingStates.PENDING).length === 0}
              >
                確認處理文件
              </Button>
            </div>
          </>
        )}
      </Card>
    </div>
  );
};

export default FileUploadComponent;
