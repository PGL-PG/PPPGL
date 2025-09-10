import React, { useState } from 'react';
import { Layout, Typography, message } from 'antd';
import FileUpload from './components/FileUpload';
import DataAnalysis from './components/DataAnalysis';
import './App.css';

const { Header, Content } = Layout;
const { Title } = Typography;

function App() {
  const [uploadedFile, setUploadedFile] = useState(null);
  const [sheetsData, setSheetsData] = useState(null);

  const handleUploadSuccess = (data) => {
    setUploadedFile(data.filename);
    setSheetsData(data.sheets);
    message.success('文件上传成功！');
  };

  const handleUploadError = (error) => {
    message.error(`上传失败: ${error}`);
  };

  return (
    <Layout className="main-layout">
      <Header className="header">
        <Title level={2} style={{ color: 'white', margin: 0 }}>
          📊 Excel 数据分析平台
        </Title>
      </Header>
      <Content className="main-container">
        {!uploadedFile ? (
          <FileUpload 
            onSuccess={handleUploadSuccess}
            onError={handleUploadError}
          />
        ) : (
          <DataAnalysis 
            filename={uploadedFile}
            sheetsData={sheetsData}
            onReset={() => {
              setUploadedFile(null);
              setSheetsData(null);
            }}
          />
        )}
      </Content>
    </Layout>
  );
}

export default App;