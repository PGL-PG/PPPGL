import React, { useState, useEffect } from 'react';
import { Upload, Card, Typography, message } from 'antd';
import { InboxOutlined, FileExcelOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Dragger } = Upload;
const { Title, Text } = Typography;

const FileUpload = ({ onSuccess, onError, compact = false }) => {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  
  // 模拟上传进度效果
  useEffect(() => {
    let interval;
    
    if (uploading && progress < 95) {
      // 创建一个计时器来模拟上传进度的增加
      interval = setInterval(() => {
        // 随机增加进度，让进度条看起来更自然
        setProgress(prev => Math.min(prev + Math.random() * 5, 95));
      }, 300);
    }
    
    // 组件卸载或状态改变时清除计时器
    return () => clearInterval(interval);
  }, [uploading, progress]);

  const uploadProps = {
    name: 'file',
    multiple: false,
    accept: '.xlsx,.xls',
    beforeUpload: (file) => {
      // 检查文件是否为Excel格式
      const isExcel = file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' || 
                     file.type === 'application/vnd.ms-excel' ||
                     file.name.endsWith('.xlsx') || 
                     file.name.endsWith('.xls');
      
      if (!isExcel) {
        message.error('只能上传 Excel 文件！');
        return false;
      }
      
      // 重置进度条
      setProgress(0);
      return true;
    },
    customRequest: async ({ file, onSuccess: uploadSuccess, onError: uploadError }) => {
      setUploading(true);
      const formData = new FormData();
      formData.append('file', file);

      try {
        // 发送文件到后端API
        const response = await axios.post('/api/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        
        // 完成上传进度
        setProgress(100);
        setTimeout(() => {
          uploadSuccess(response.data);
          onSuccess(response.data);
          // 重置状态
          setUploading(false);
          setProgress(0);
        }, 500);
      } catch (error) {
        // 处理上传错误
        const errorMsg = error.response?.data?.error || '上传失败';
        uploadError(error);
        onError(errorMsg);
        setUploading(false);
        setProgress(0);
      }
    },
    showUploadList: false,
  };

  return (
    <div className="upload-container">
      <Card 
        className="upload-card"
        style={{
          borderRadius: '16px',
          border: 'none',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.08)',
          overflow: 'hidden',
          transition: 'all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1)'
        }}
      >
        {/* 添加顶部装饰条 */}
        <div className="card-decoration"></div>
        
        {/* 非紧凑模式下显示完整标题 */}
        {!compact && (
          <div style={{ textAlign: 'center', marginBottom: 32, paddingTop: '24px' }}>
            <div className="excel-icon-container">
              <FileExcelOutlined className="excel-icon" />
            </div>
            <Title level={3} style={{ marginBottom: '8px' }}>上传 Excel 文件开始分析</Title>
            <Text type="secondary">
              支持 .xlsx 和 .xls 格式，无文件大小限制
            </Text>
          </div>
        )}
        
        {/* 紧凑模式下显示简化标题 */}
        {compact && (
          <div style={{ textAlign: 'center', marginBottom: 16, paddingTop: '16px' }}>
            <Title level={4} style={{ margin: 0, color: '#1890ff' }}>
              <FileExcelOutlined style={{ marginRight: 8 }} />
              上传新的 Excel 文件
            </Title>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              支持 .xlsx/.xls 格式，无大小限制
            </Text>
          </div>
        )}
        
        {/* 文件上传拖拽区域 */}
        <Dragger 
          {...uploadProps} 
          style={{ 
            padding: compact ? '20px 10px' : '40px 20px',
            border: '2px dashed #d9d9d9',
            borderRadius: '12px',
            background: 'linear-gradient(120deg, rgba(24, 144, 255, 0.03), rgba(24, 144, 255, 0.06), rgba(24, 144, 255, 0.03))',
            backgroundSize: '200% 100%',
            transition: 'all 0.4s ease'
          }}
          className="upload-dragger"
        >
          <p className="ant-upload-drag-icon">
            <InboxOutlined style={{ fontSize: compact ? 32 : 48, color: '#1890ff' }} />
          </p>
          <p className="ant-upload-text" style={{ fontSize: compact ? '14px' : '16px' }}>
            点击或拖拽文件到此区域上传
          </p>
          {!compact && (
            <p className="ant-upload-hint">
              系统将自动解析 Excel 文件的所有工作表和列信息
            </p>
          )}
        </Dragger>
        
        {/* 上传进度条 - 只有在上传过程中显示 */}
        {uploading && (
          <div className="upload-progress-container">
            {/* 进度条背景 */}
            <div className="upload-progress-bar">
              {/* 进度条填充部分 */}
              <div 
                className="upload-progress-fill"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
            {/* 进度文本 */}
            <Text className="upload-progress-text">正在上传和解析文件... {Math.round(progress)}%</Text>
          </div>
        )}
      </Card>
    </div>
  );
};

export default FileUpload;