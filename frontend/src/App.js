import React, { useState } from 'react';
import { Layout, Typography, message, Button, Space, Switch } from 'antd';
import { FileAddOutlined } from '@ant-design/icons';
import FileUpload from './components/FileUpload';
import DataAnalysis from './components/DataAnalysis';
import './App.css';

const { Header, Content } = Layout;
const { Title, Paragraph } = Typography;

function App() {
  const [uploadedFiles, setUploadedFiles] = useState([]); // 改为数组支持多文件
  const [currentFileIndex, setCurrentFileIndex] = useState(0);
  const [showUploadArea, setShowUploadArea] = useState(false);
  const [darkMode, setDarkMode] = useState(false); // 添加深色模式状态
  
  // 添加深色模式切换逻辑
  const toggleDarkMode = (checked) => {
    setDarkMode(checked);
    if (checked) {
      document.body.classList.add('dark-mode');
    } else {
      document.body.classList.remove('dark-mode');
    }
  };

  const handleUploadSuccess = (data) => {
    const newFile = {
      filename: data.filename,
      sheetsData: data.sheets || data.sheets_data,
      dataPreview: data.data_preview,
      uploadTime: new Date().toLocaleString()
    };
    
    setUploadedFiles(prev => [...prev, newFile]);
    setCurrentFileIndex(uploadedFiles.length); // 切换到新上传的文件
    setShowUploadArea(false); // 隐藏上传区域
    
    if (data.data_preview && !data.data_preview.error) {
      message.success('文件上传成功！已生成数据预览');
    } else {
      message.success('文件上传成功！');
    }
  };

  const handleUploadError = (error) => {
    message.error(`上传失败: ${error}`);
  };

  const handleSwitchFile = (index) => {
    setCurrentFileIndex(index);
  };

  const handleRemoveFile = (index) => {
    const newFiles = uploadedFiles.filter((_, i) => i !== index);
    setUploadedFiles(newFiles);
    
    if (newFiles.length === 0) {
      setCurrentFileIndex(0);
    } else if (currentFileIndex >= newFiles.length) {
      setCurrentFileIndex(newFiles.length - 1);
    } else if (currentFileIndex > index) {
      setCurrentFileIndex(currentFileIndex - 1);
    }
  };

  const currentFile = uploadedFiles[currentFileIndex];

  return (
    <Layout className={`main-layout ${darkMode ? 'dark-mode' : ''}`}>
      <Header className="header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
          <Title level={2} style={{ color: 'white', margin: 0 }}>
            📊 Excel 数据分析平台
          </Title>
          <Space>
            {/* 深色模式开关 - 放在上传新文件按钮左侧 */}
            <Space style={{ color: 'white' }}>
              <span>深色模式</span>
              <Switch 
                checked={darkMode} 
                onChange={toggleDarkMode} 
                checkedChildren="开" 
                unCheckedChildren="关" 
                style={{ color: '#1890ff' }} 
              />
            </Space>
            
            {uploadedFiles.length > 0 && (
              <Button 
                icon={<FileAddOutlined />}
                type="default"
                style={{ background: 'rgba(255,255,255,0.2)', color: 'white', border: 'none' }}
                onClick={() => setShowUploadArea(!showUploadArea)}
              >
                {showUploadArea ? '收起上传' : '上传新文件'}
              </Button>
            )}
          </Space>
        </div>
      </Header>
      <Content className="main-container">
        {/* 添加内容包装器，只限制内容区域的宽度 */}
        <div className="content-wrapper">
          {/* 上传区域 - 在有文件时可收起 */}
          {(uploadedFiles.length === 0 || showUploadArea) && (
            <div style={{ 
              marginBottom: uploadedFiles.length > 0 ? 24 : 0,
              padding: uploadedFiles.length > 0 ? '16px' : '0',
              border: uploadedFiles.length > 0 ? '2px dashed #d9d9d9' : 'none',
              borderRadius: uploadedFiles.length > 0 ? '8px' : '0',
              background: uploadedFiles.length > 0 ? '#fafafa' : 'transparent'
            }}>
              {/* 添加欢迎语，仅在没有上传文件时显示 */}
              {uploadedFiles.length === 0 && (
                <div className="welcome-section">
                  <Title level={3} className="welcome-title">
                    欢迎使用 Excel 数据分析平台
                  </Title>
                  <Paragraph className="welcome-description">
                    这是一个强大的数据分析工具，可以帮助您快速导入、预览和分析Excel数据，发现数据背后的价值
                  </Paragraph>
                </div>
              )}
              
              <FileUpload 
                onSuccess={handleUploadSuccess}
                onError={handleUploadError}
                compact={uploadedFiles.length > 0} // 传递紧凑模式标志
              />
            </div>
          )}
          
          {/* 分析区域 - 显示当前选中的文件 */}
          {uploadedFiles.length > 0 && currentFile && (
            <DataAnalysis 
              filename={currentFile.filename}
              sheetsData={currentFile.sheetsData}
              dataPreview={currentFile.dataPreview}
              uploadedFiles={uploadedFiles}
              currentFileIndex={currentFileIndex}
              onSwitchFile={handleSwitchFile}
              onRemoveFile={handleRemoveFile}
              onShowUpload={() => setShowUploadArea(true)}
            />
          )}
        </div>
      </Content>
    </Layout>
  );
}

export default App;