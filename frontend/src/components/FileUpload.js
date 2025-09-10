import React, { useState } from 'react';
import { Upload, Card, Typography, Button, message } from 'antd';
import { InboxOutlined, FileExcelOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Dragger } = Upload;
const { Title, Text } = Typography;

const FileUpload = ({ onSuccess, onError }) => {
  const [uploading, setUploading] = useState(false);

  const uploadProps = {
    name: 'file',
    multiple: false,
    accept: '.xlsx,.xls',
    beforeUpload: (file) => {
      const isExcel = file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' || 
                     file.type === 'application/vnd.ms-excel' ||
                     file.name.endsWith('.xlsx') || 
                     file.name.endsWith('.xls');
      
      if (!isExcel) {
        message.error('只能上传 Excel 文件！');
        return false;
      }
      
      const isLt10M = file.size / 1024 / 1024 < 10;
      if (!isLt10M) {
        message.error('文件大小不能超过 10MB！');
        return false;
      }
      
      return true;
    },
    customRequest: async ({ file, onSuccess: uploadSuccess, onError: uploadError }) => {
      setUploading(true);
      const formData = new FormData();
      formData.append('file', file);

      try {
        const response = await axios.post('/api/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        
        uploadSuccess(response.data);
        onSuccess(response.data);
      } catch (error) {
        const errorMsg = error.response?.data?.error || '上传失败';
        uploadError(error);
        onError(errorMsg);
      } finally {
        setUploading(false);
      }
    },
    showUploadList: false,
  };

  return (
    <div className="upload-container">
      <Card>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <FileExcelOutlined style={{ fontSize: 48, color: '#1890ff', marginBottom: 16 }} />
          <Title level={3}>上传 Excel 文件开始分析</Title>
          <Text type="secondary">
            支持 .xlsx 和 .xls 格式，文件大小不超过 10MB
          </Text>
        </div>
        
        <Dragger {...uploadProps} style={{ padding: '40px 20px' }}>
          <p className="ant-upload-drag-icon">
            <InboxOutlined style={{ fontSize: 48, color: '#1890ff' }} />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">
            系统将自动解析 Excel 文件的所有工作表和列信息
          </p>
        </Dragger>
        
        {uploading && (
          <div style={{ textAlign: 'center', marginTop: 16 }}>
            <Text>正在上传和解析文件...</Text>
          </div>
        )}
      </Card>
    </div>
  );
};

export default FileUpload;