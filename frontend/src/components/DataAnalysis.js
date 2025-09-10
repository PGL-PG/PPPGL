import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Select, 
  Button, 
  Typography, 
  Row, 
  Col, 
  Table, 
  Spin, 
  Input, 
  Space,
  Divider,
  Tag,
  message,
  Modal
} from 'antd';
import { 
  FundOutlined, 
  ReloadOutlined, 
  FileTextOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import axios from 'axios';
import ChartDisplay from './ChartDisplay';
import AttributionAnalysis from './AttributionAnalysis';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { TextArea } = Input;

const DataAnalysis = ({ filename, sheetsData, onReset }) => {
  const [selectedSheet, setSelectedSheet] = useState('');
  const [selectedColumns, setSelectedColumns] = useState([]);
  const [customRequirements, setCustomRequirements] = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showAttribution, setShowAttribution] = useState(false);

  useEffect(() => {
    // 默认选择第一个sheet
    if (sheetsData && Object.keys(sheetsData).length > 0) {
      const firstSheet = Object.keys(sheetsData)[0];
      setSelectedSheet(firstSheet);
    }
  }, [sheetsData]);

  const handleAnalyze = async () => {
    if (!selectedSheet) {
      message.warning('请选择要分析的工作表');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post('/api/analyze', {
        filename,
        sheet_name: selectedSheet,
        selected_columns: selectedColumns.length > 0 ? selectedColumns : undefined,
        custom_requirements: customRequirements
      });

      setAnalysisResult(response.data);
      message.success('分析完成！');
    } catch (error) {
      const errorMsg = error.response?.data?.error || '分析失败';
      message.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const getColumnTypeColor = (type) => {
    const colors = {
      numeric: 'blue',
      datetime: 'green',
      categorical: 'orange',
      text: 'default',
      empty: 'red'
    };
    return colors[type] || 'default';
  };

  const getColumnTypeText = (type) => {
    const texts = {
      numeric: '数值',
      datetime: '时间',
      categorical: '分类',
      text: '文本',
      empty: '空值'
    };
    return texts[type] || type;
  };

  const currentSheetData = selectedSheet ? sheetsData[selectedSheet] : null;
  const availableColumns = currentSheetData ? Object.keys(currentSheetData.columns) : [];

  // 准备数据预览表格列
  const previewColumns = availableColumns.map(col => ({
    title: (
      <Space>
        {col}
        <Tag color={getColumnTypeColor(currentSheetData.columns[col].type)} size="small">
          {getColumnTypeText(currentSheetData.columns[col].type)}
        </Tag>
      </Space>
    ),
    dataIndex: col,
    key: col,
    ellipsis: true,
    width: 150
  }));

  return (
    <div className="analysis-container">
      {/* 控制面板 */}
      <Card title="📋 分析配置" style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={8}>
            <Text strong>选择工作表：</Text>
            <Select
              style={{ width: '100%', marginTop: 8 }}
              placeholder="选择工作表"
              value={selectedSheet}
              onChange={setSelectedSheet}
            >
              {Object.keys(sheetsData).map(sheetName => (
                <Option key={sheetName} value={sheetName}>
                  {sheetName} ({sheetsData[sheetName].row_count} 行)
                </Option>
              ))}
            </Select>
          </Col>
          
          <Col xs={24} sm={12} md={8}>
            <Text strong>选择分析列（可选）：</Text>
            <Select
              mode="multiple"
              style={{ width: '100%', marginTop: 8 }}
              placeholder="选择要分析的列"
              value={selectedColumns}
              onChange={setSelectedColumns}
            >
              {availableColumns.map(col => (
                <Option key={col} value={col}>
                  <Space>
                    {col}
                    <Tag color={getColumnTypeColor(currentSheetData.columns[col].type)} size="small">
                      {getColumnTypeText(currentSheetData.columns[col].type)}
                    </Tag>
                  </Space>
                </Option>
              ))}
            </Select>
          </Col>
          
          <Col xs={24} sm={24} md={8}>
            <Text strong>自定义分析需求：</Text>
            <TextArea
              style={{ marginTop: 8 }}
              placeholder="描述您的特殊分析需求..."
              value={customRequirements}
              onChange={(e) => setCustomRequirements(e.target.value)}
              rows={2}
            />
          </Col>
        </Row>
        
        <Divider />
        
        <Space>
          <Button 
            type="primary" 
            icon={<FundOutlined />}
            onClick={handleAnalyze}
            loading={loading}
            size="large"
          >
            开始分析
          </Button>
          <Button 
            icon={<ReloadOutlined />}
            onClick={onReset}
          >
            重新上传
          </Button>
        </Space>
      </Card>

      {/* 数据预览 */}
      {currentSheetData && (
        <Card title="👀 数据预览" style={{ marginBottom: 24 }}>
          <div className="data-preview">
            <Table
              columns={previewColumns}
              dataSource={currentSheetData.preview.map((row, index) => ({ ...row, key: index }))}
              pagination={false}
              scroll={{ x: true }}
              size="small"
            />
          </div>
          <Text type="secondary" style={{ marginTop: 8, display: 'block' }}>
            显示前 5 行数据，共 {currentSheetData.row_count} 行
          </Text>
        </Card>
      )}

      {/* 分析结果 */}
      {loading && (
        <Card>
          <div className="loading-container">
            <Spin size="large" />
            <Text style={{ marginLeft: 16 }}>正在分析数据，请稍候...</Text>
          </div>
        </Card>
      )}

      {analysisResult && !loading && (
        <>
          {/* 智能分析结论 */}
          <Card 
            title={<><FileTextOutlined /> 智能分析结论</>}
            style={{ marginBottom: 24 }}
            extra={
              <Button 
                type="primary"
                icon={<FundOutlined />}
                onClick={() => setShowAttribution(true)}
              >
                归因诊断
              </Button>
            }
          >
            <Paragraph>
              <Text strong>分析方法：</Text>
              {analysisResult.analysis.analysis_methods?.map((method, index) => (
                <Tag key={index} color="blue" style={{ margin: '0 4px' }}>
                  {method}
                </Tag>
              ))}
            </Paragraph>
            
            <Paragraph>
              <Text strong>数据洞察：</Text>
            </Paragraph>
            <Paragraph style={{ background: '#f6ffed', padding: 16, borderRadius: 6, border: '1px solid #b7eb8f' }}>
              {analysisResult.analysis.insights}
            </Paragraph>
            
            {analysisResult.analysis.attribution_analysis && (
              <Paragraph>
                <Text strong>归因建议：</Text>
                <br />
                <Text>{analysisResult.analysis.attribution_analysis}</Text>
              </Paragraph>
            )}
          </Card>

          {/* 可视化图表 */}
          {analysisResult.chart_data && analysisResult.chart_data.length > 0 && (
            <Card title={<><BarChartOutlined /> 数据可视化</>} style={{ marginBottom: 24 }}>
              <Row gutter={[16, 16]}>
                {analysisResult.chart_data.map((chartData, index) => (
                  <Col xs={24} lg={12} key={index}>
                    <ChartDisplay chartData={chartData} />
                  </Col>
                ))}
              </Row>
            </Card>
          )}

          {/* 统计信息 */}
          {analysisResult.statistics && Object.keys(analysisResult.statistics).length > 0 && (
            <Card title="📊 统计摘要" style={{ marginBottom: 24 }}>
              <Row gutter={[16, 16]}>
                {Object.entries(analysisResult.statistics).map(([column, stats]) => (
                  <Col xs={24} sm={12} md={8} key={column}>
                    <Card size="small" title={column}>
                      <Space direction="vertical" size="small" style={{ width: '100%' }}>
                        <div><Text strong>平均值：</Text>{stats.mean?.toFixed(2) || 'N/A'}</div>
                        <div><Text strong>中位数：</Text>{stats.median?.toFixed(2) || 'N/A'}</div>
                        <div><Text strong>标准差：</Text>{stats.std?.toFixed(2) || 'N/A'}</div>
                        <div><Text strong>最小值：</Text>{stats.min?.toFixed(2) || 'N/A'}</div>
                        <div><Text strong>最大值：</Text>{stats.max?.toFixed(2) || 'N/A'}</div>
                      </Space>
                    </Card>
                  </Col>
                ))}
              </Row>
            </Card>
          )}
        </>
      )}

      {/* 归因分析模态框 */}
      <Modal
        title="🔍 归因诊断分析"
        open={showAttribution}
        onCancel={() => setShowAttribution(false)}
        footer={null}
        width={1000}
      >
        <AttributionAnalysis 
          filename={filename}
          sheetName={selectedSheet}
          availableColumns={availableColumns.filter(col => 
            currentSheetData.columns[col].type === 'numeric'
          )}
        />
      </Modal>
    </div>
  );
};

export default DataAnalysis;