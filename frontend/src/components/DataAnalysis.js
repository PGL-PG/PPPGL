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
  Modal,
  Alert,
  Statistic,
  List,
  Collapse,
  Tabs,
  Dropdown,
  Popconfirm
} from 'antd';
import { 
  FundOutlined, 
  ReloadOutlined, 
  FileTextOutlined,
  BarChartOutlined,
  ExclamationCircleOutlined,
  BulbOutlined,
  FileExcelOutlined,
  DeleteOutlined,
  MoreOutlined,
  ClockCircleOutlined,
  TableOutlined
} from '@ant-design/icons';
import axios from 'axios';
import ChartDisplay from './ChartDisplay';

const { Text, Title } = Typography;
const { Option } = Select;
const { TextArea } = Input;
const { Panel } = Collapse;
const { TabPane } = Tabs;

const DataAnalysis = ({ 
  filename, 
  sheetsData, 
  dataPreview, 
  uploadedFiles = [], 
  currentFileIndex = 0, 
  onSwitchFile, 
  onRemoveFile, 
  onShowUpload 
}) => {
  const [selectedSheet, setSelectedSheet] = useState('');
  const [selectedColumns, setSelectedColumns] = useState([]);
  const [customRequirements, setCustomRequirements] = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expandedFieldSummary, setExpandedFieldSummary] = useState(false);

  // 解析AI洞察为结构化内容
  const parseAIInsights = (aiText) => {
    if (!aiText || typeof aiText !== 'string') return [];
    
    const sections = [];
    const lines = aiText.split('\n').filter(line => line.trim());
    
    let currentSection = null;
    
    for (const line of lines) {
      const trimmedLine = line.trim();
      
      // 检测标题行（以 ## 开头）
      if (trimmedLine.startsWith('##')) {
        if (currentSection) {
          sections.push(currentSection);
        }
        
        const title = trimmedLine.replace(/^##\s*/, '');
        let icon = '💡';
        
        // 根据标题内容选择合适的图标
        if (title.includes('发现') || title.includes('洞察') || title.includes('关键')) {
          icon = '🔍';
        } else if (title.includes('建议') || title.includes('策略') || title.includes('推荐')) {
          icon = '💡';
        } else if (title.includes('竞争') || title.includes('市场') || title.includes('格局')) {
          icon = '📊';
        } else if (title.includes('表现') || title.includes('排行') || title.includes('业绩')) {
          icon = '📈';
        } else if (title.includes('趋势') || title.includes('预测') || title.includes('展望')) {
          icon = '🔮';
        }
        
        currentSection = {
          title: title,
          icon: icon,
          content: []
        };
      }
      // 检测列表项（以 - 开头）
      else if (trimmedLine.startsWith('-')) {
        const content = trimmedLine.replace(/^-\s*/, '');
        if (currentSection) {
          currentSection.content.push(content);
        } else {
          // 如果没有当前section，创建一个默认的
          currentSection = {
            title: '分析洞察',
            icon: '📋',
            content: [content]
          };
        }
      }
      // 其他内容行
      else if (trimmedLine && currentSection) {
        currentSection.content.push(trimmedLine);
      }
    }
    
    // 添加最后一个section
    if (currentSection) {
      sections.push(currentSection);
    }
    
    // 如果没有解析到任何section，将整个文本作为一个section
    if (sections.length === 0 && aiText.trim()) {
      sections.push({
        title: 'AI智能分析',
        icon: '🤖',
        content: [aiText.trim()]
      });
    }
    
    return sections;
  };
  const getChartInsight = (chartData, analysisResult, index) => {
    const { type, title, data } = chartData;
    
    if (!data || data.length === 0) return "📊 数据图表展示完成";
    
    if (type === 'bar') {
      const topItem = data[0];
      const total = data.reduce((sum, item) => sum + (item.value || 0), 0);
      const topPercentage = total > 0 ? ((topItem.value || 0) / total * 100).toFixed(1) : 0;
      return `🏆 ${topItem.name} 表现最佳，占比 ${topPercentage}%，显示出明显的领先优势`;
    }
    
    if (type === 'pie') {
      const topItem = data[0];
      return `📊 ${topItem.name} 占据最大份额 (${topItem.value}%)，市场结构清晰可见`;
    }
    
    if (type === 'histogram') {
      return `📈 数据分布图显示了 ${title} 的整体分布特征，有助于理解数据规律`;
    }
    
    if (type === 'scatter') {
      return `🔗 散点图揭示了字段间的关联关系，为进一步分析提供了方向`;
    }
    
    return `💡 ${title} 提供了重要的数据洞察，建议结合业务场景深入分析`;
  };

  // useEffect must be called before any early returns
  useEffect(() => {
    // 默认选择第一个sheet
    if (sheetsData && typeof sheetsData === 'object' && Object.keys(sheetsData).length > 0) {
      const firstSheet = Object.keys(sheetsData)[0];
      setSelectedSheet(firstSheet);
    }
  }, [sheetsData]);

  // 监听文件切换，清空之前的分析结果
  useEffect(() => {
    // 当filename发生变化时（文件切换），清空之前的分析结果
    setAnalysisResult(null);
    setExpandedFieldSummary(false);
    // 重置列选择
    setSelectedColumns([]);
    setCustomRequirements('');
  }, [filename]);

  // Early return if required data is not available
  if (!sheetsData || typeof sheetsData !== 'object' || Object.keys(sheetsData).length === 0) {
    return (
      <Card>
        <Alert
          message="数据加载中..."
          description="正在处理上传的文件，请稍候..."
          type="info"
          showIcon
        />
      </Card>
    );
  }

  const handleAnalyze = async () => {
    if (!selectedSheet) {
      message.warning('请选择要分析的工作表');
      return;
    }

    setLoading(true);
    try {
      // 准备分析数据
      const columnsToAnalyze = selectedColumns.length > 0 ? selectedColumns : availableColumns;
      const dataSample = currentSheetData?.preview ? 
        JSON.stringify(currentSheetData.preview.slice(0, 3), null, 2) : null;

      // 调用后端分析接口（会转发给 Gemini）
      const response = await axios.post('/api/analyze', {
        filename,
        sheet_name: selectedSheet,
        selected_columns: columnsToAnalyze,
        custom_requirements: customRequirements,
        columns: columnsToAnalyze,
        data_sample: dataSample,
        analysis_type: 'comprehensive'
      });

      // 检查响应数据结构
      console.log('分析响应数据:', response.data);
      
      if (response.data && (response.data.status === 'success' || response.data.analysis_report)) {
        // 直接使用后端返回的分析结果
        let analysisResult;
        
        if (response.data.status === 'success') {
          // 如果是包装格式
          analysisResult = response.data.result || response.data;
        } else {
          // 如果是直接的分析结果
          analysisResult = response.data;
        }
        
        // 确保必要的字段存在
        if (!analysisResult.analysis_report && analysisResult.analysis) {
          analysisResult.analysis_report = analysisResult.analysis;
        }
        
        // 添加默认的业务洞察（如果没有的话）
        if (!analysisResult.business_insights && !analysisResult.statistical_insights) {
          analysisResult.business_insights = [
            '✨ 基于专业统计分析方法的深度分析',
            '📊 自动识别数据模式和分布特征',
            '💡 提供专业的数据洞察和建议'
          ];
        }
        
        setAnalysisResult(analysisResult);
        message.success('数据分析完成！');
      } else {
        throw new Error(response.data?.error || '分析失败');
      }
    } catch (error) {
      const errorMsg = error.response?.data?.error || error.message || '分析失败';
      message.error(`分析失败: ${errorMsg}`);
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

  const currentSheetData = selectedSheet && sheetsData ? sheetsData[selectedSheet] : null;
  const availableColumns = currentSheetData?.columns ? Object.keys(currentSheetData.columns) : [];

  // 文件管理相关函数
  const getFileMenuItems = (fileIndex) => {
    return [
      {
        key: 'switch',
        label: '切换到此文件',
        icon: <FileExcelOutlined />,
        onClick: () => onSwitchFile && onSwitchFile(fileIndex)
      },
      {
        key: 'remove',
        label: '移除此文件',
        icon: <DeleteOutlined />,
        danger: true,
        onClick: () => {
          Modal.confirm({
            title: '确认移除文件',
            content: `确定要移除文件 "${uploadedFiles[fileIndex]?.filename}" 吗？`,
            onOk: () => onRemoveFile && onRemoveFile(fileIndex)
          });
        }
      }
    ];
  };

  // 渲染文件管理标签页
  const renderFileManagement = () => {
    if (!uploadedFiles || uploadedFiles.length <= 1) return null;

    return (
      <div className="fixed-file-management">
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1 }}>
              <FileExcelOutlined style={{ color: '#1890ff', fontSize: '16px' }} />
              <Text strong style={{ color: '#1890ff' }}>文件管理</Text>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginLeft: '16px' }}>
                {uploadedFiles.map((file, index) => (
                  <div 
                    key={index}
                    style={{
                      padding: '4px 10px',
                      border: `1px solid ${index === currentFileIndex ? '#1890ff' : '#d9d9d9'}`,
                      borderRadius: '4px',
                      background: index === currentFileIndex ? '#e6f7ff' : '#fafafa',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      fontSize: '12px'
                    }}
                    onClick={() => onSwitchFile && onSwitchFile(index)}
                  >
                    <FileExcelOutlined style={{ 
                      color: index === currentFileIndex ? '#1890ff' : '#666',
                      fontSize: '12px'
                    }} />
                    <span style={{ 
                      fontWeight: index === currentFileIndex ? 'bold' : 'normal',
                      color: index === currentFileIndex ? '#1890ff' : '#333',
                      maxWidth: '120px',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}>
                      {file.filename}
                    </span>
                    {uploadedFiles.length > 1 && (
                      <Dropdown
                        menu={{ items: getFileMenuItems(index) }}
                        trigger={['click']}
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Button 
                          type="text" 
                          size="small" 
                          icon={<MoreOutlined />}
                          style={{ padding: '0 4px', height: '16px', fontSize: '10px' }}
                          onClick={(e) => e.stopPropagation()}
                        />
                      </Dropdown>
                    )}
                  </div>
                ))}
              </div>
            </div>
            <Button 
              type="primary" 
              icon={<FileExcelOutlined />}
              onClick={onShowUpload}
              size="small"
            >
              上传新文件
            </Button>
          </div>
        </div>
      </div>
    );
  };

  // 全选/取消全选功能
  const handleSelectAllColumns = () => {
    if (selectedColumns.length === availableColumns.length) {
      setSelectedColumns([]); // 如果已全选，则取消全选
    } else {
      setSelectedColumns([...availableColumns]); // 全选
    }
  };

  // 智能推荐列选择
  const handleSmartSelect = () => {
    if (!dataPreview || !dataPreview.potential_fields) return;
    
    const smartColumns = [
      ...dataPreview.potential_fields.sales_fields,
      ...dataPreview.potential_fields.brand_fields,
      ...dataPreview.potential_fields.product_fields,
      ...dataPreview.potential_fields.price_fields
    ];
    
    setSelectedColumns(smartColumns);
  };

  // 准备数据预览表格列
  const previewColumns = availableColumns.length > 0 ? availableColumns.map(col => {
    const columnType = currentSheetData?.columns?.[col]?.type || 'text';
    
    return {
      title: (
        <Space>
          <Text strong style={{ fontSize: '13px' }}>{col}</Text>
          <Tag color={getColumnTypeColor(columnType)} size="small">
            {getColumnTypeText(columnType)}
          </Tag>
        </Space>
      ),
      dataIndex: col,
      key: col,
      ellipsis: true,
      width: columnType === 'numeric' ? 120 : 150,
      align: columnType === 'numeric' ? 'right' : 'left',
      render: (value) => {
        if (value === null || value === undefined || value === '') {
          return <Text type="secondary">-</Text>;
        }
        
        // 数值类型格式化
        if (columnType === 'numeric' && typeof value === 'number') {
          return (
            <Text style={{ fontFamily: 'monospace', fontWeight: 500 }}>
              {value.toLocaleString()}
            </Text>
          );
        }
        
        // 文本类型截断显示
        if (typeof value === 'string' && value.length > 20) {
          return (
            <Text ellipsis={{ tooltip: value }} style={{ maxWidth: 130 }}>
              {value}
            </Text>
          );
        }
        
        return <Text>{value}</Text>;
      }
    };
  }) : [];

  // 渲染数据预览
  const renderDataPreview = () => {
    if (!dataPreview || dataPreview.error) {
      return null;
    }

    const { preview_insights } = dataPreview;

    return (
      <Card 
        title={<><BulbOutlined /> 数据预览</>} 
        style={{ marginBottom: 16 }}
      >
        {/* 数据概览信息 */}
        <List
          size="small"
          dataSource={preview_insights || []}
          renderItem={item => (
            <List.Item>
              <Text>{item}</Text>
            </List.Item>
          )}
        />
        
        {/* 数据表格 */}
        {currentSheetData && (
          <div style={{ marginTop: 16 }}>
            <Divider orientation="left" plain>
              <Space>
                <span>📊 数据表格</span>
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  显示前 5 行，共 {currentSheetData?.row_count || 0} 行数据
                </Text>
              </Space>
            </Divider>
            <Table
              columns={previewColumns}
              dataSource={currentSheetData?.preview?.map((row, index) => ({ ...row, key: index })) || []}
              pagination={false}
              scroll={{ x: true }}
              size="small"
              bordered
              style={{ 
                background: '#fafafa',
                borderRadius: '6px'
              }}
              rowClassName={(_, index) => index % 2 === 0 ? 'even-row' : 'odd-row'}
            />
            <div style={{ 
              marginTop: 12, 
              padding: '8px 12px', 
              background: '#f0f2f5', 
              borderRadius: '4px',
              fontSize: '12px',
              color: '#666'
            }}>
              <Space split={<span>|</span>}>
                <span>显示前 5 行，共 {currentSheetData?.row_count || 0} 行数据</span>
                <span>共 {availableColumns.length} 列</span>
                <span>数据类型已自动识别</span>
              </Space>
            </div>
          </div>
        )}
      </Card>
    );
  };



  // 渲染分析建议
  const renderAnalysisSuggestions = () => {
    if (!dataPreview || dataPreview.error || !dataPreview.suggested_analysis) {
      return null;
    }

    const { suggested_analysis } = dataPreview;

    return (
      <Card 
        title={<><ExclamationCircleOutlined /> 分析建议</>} 
        style={{ marginBottom: 16 }}
      >
        <List
          size="small"
          dataSource={suggested_analysis || []}
          renderItem={item => (
            <List.Item>
              <Text>{item}</Text>
            </List.Item>
          )}
        />
      </Card>
    );
  };

  return (
    <>
      {/* 0. 固定的文件管理区域 */}
      {renderFileManagement()}
      
      <div className={`analysis-container ${uploadedFiles && uploadedFiles.length > 1 ? 'content-with-fixed-management' : ''}`}>
        {/* 1. 数据预览 */}
        {renderDataPreview()}

      {/* 2. 分析建议 */}
      {renderAnalysisSuggestions()}

      {/* 3. 分析配置 */}
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
              {sheetsData && typeof sheetsData === 'object' ? Object.keys(sheetsData).map(sheetName => (
                <Option key={sheetName} value={sheetName}>
                  {sheetName} ({sheetsData[sheetName]?.row_count || 0} 行)
                </Option>
              )) : []}
            </Select>
          </Col>
          
          <Col xs={24} sm={12} md={8}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Text strong>选择分析列：</Text>
              <Space>
                <Button 
                  size="small" 
                  type="link" 
                  onClick={handleSelectAllColumns}
                >
                  {selectedColumns.length === availableColumns.length ? '取消全选' : '全选'}
                </Button>
                {dataPreview && dataPreview.potential_fields && (
                  <Button 
                    size="small" 
                    type="link" 
                    onClick={handleSmartSelect}
                  >
                    智能推荐
                  </Button>
                )}
              </Space>
            </div>
            <Select
              mode="multiple"
              style={{ width: '100%', marginTop: 8 }}
              placeholder="选择要分析的列（默认分析全部列）"
              value={selectedColumns}
              onChange={setSelectedColumns}
              maxTagCount="responsive"
            >
              {availableColumns.map(col => (
                <Option key={col} value={col}>
                  <Space>
                    {col}
                    <Tag color={getColumnTypeColor(currentSheetData?.columns?.[col]?.type || 'text')} size="small">
                      {getColumnTypeText(currentSheetData?.columns?.[col]?.type || 'text')}
                    </Tag>
                  </Space>
                </Option>
              ))}
            </Select>
            <Text type="secondary" style={{ fontSize: '12px', display: 'block', marginTop: 4 }}>
              已选择 {selectedColumns.length} / {availableColumns.length} 列
              {selectedColumns.length === 0 && " (将分析全部列)"}
            </Text>
          </Col>
          
          <Col xs={24} sm={24} md={8}>
            <Text strong>分析描述（可选）：</Text>
            <TextArea
              style={{ marginTop: 8 }}
              placeholder="补充分析需求..."
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
            disabled={!selectedSheet}
          >
            {loading ? '分析中...' : '开始深度分析'}
          </Button>
        </Space>
        
        {!selectedSheet && (
          <Alert
            message="请先选择要分析的工作表"
            type="warning"
            showIcon
            style={{ marginTop: 16 }}
          />
        )}
      </Card>



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
          {/* 基础数据概览 - 文本形式 */}
          {analysisResult.basic_stats_overview && (
            <Card 
              title={<><BarChartOutlined /> 基础数据概览</>}
              style={{ marginBottom: 24 }}
            >
              <div style={{ 
                padding: '16px',
                background: '#f8f9fa',
                borderRadius: '8px',
                fontSize: '14px',
                lineHeight: '1.8',
                color: '#2c3e50'
              }}>
                <Text strong style={{ fontSize: '16px', color: '#1890ff', display: 'block', marginBottom: '12px' }}>
                  📊 数据规模概述
                </Text>
                本次分析的数据包含 <Text strong style={{ color: '#52c41a' }}>
                  {analysisResult.basic_stats_overview.data_scale.total_rows}
                </Text> 行数据，
                <Text strong style={{ color: '#52c41a' }}>
                  {analysisResult.basic_stats_overview.data_scale.total_columns}
                </Text> 个字段，
                业务场景识别为 <Text strong style={{ color: '#722ed1' }}>
                  {analysisResult.basic_stats_overview.data_scale.business_scenario}
                </Text>。
                
                {analysisResult.basic_stats_overview.data_quality.missing_data_fields.length > 0 ? (
                  <Text style={{ color: '#fa8c16' }}>
                    数据质量方面，发现 <Text strong>
                      {analysisResult.basic_stats_overview.data_quality.missing_data_fields.length}
                    </Text> 个字段存在缺失值，建议在正式分析前进行数据清洗。
                  </Text>
                ) : (
                  <Text style={{ color: '#52c41a' }}>
                    数据质量良好，无明显缺失值问题。
                  </Text>
                )}
                
                <br /><br />
                
                <Text strong style={{ fontSize: '16px', color: '#1890ff', display: 'block', marginBottom: '8px' }}>
                  📋 字段统计概述
                </Text>
                {(() => {
                  const fieldEntries = Object.entries(analysisResult.basic_stats_overview.field_summary);
                  const shouldCollapse = fieldEntries.length > 5;
                  const displayedFields = shouldCollapse && !expandedFieldSummary 
                    ? fieldEntries.slice(0, 5) 
                    : fieldEntries;
                  
                  return (
                    <>
                      {displayedFields.map(([field, stats], index) => {
                        if (stats.type === 'numeric') {
                          return (
                            <Text key={field} style={{ display: 'block', marginBottom: '6px' }}>
                              • <Text strong>{field}</Text>（数值字段）：
                              均值 <Text code>{stats.mean?.toFixed(2) || 'N/A'}</Text>，
                              中位数 <Text code>{stats.median?.toFixed(2) || 'N/A'}</Text>，
                              取值范围 <Text code>{stats.min}-{stats.max}</Text>
                              {stats.null_count > 0 && (
                                <Text type="secondary">（缺失{stats.null_percentage}%）</Text>
                              )}
                            </Text>
                          );
                        } else if (stats.type === 'categorical') {
                          return (
                            <Text key={field} style={{ display: 'block', marginBottom: '6px' }}>
                              • <Text strong>{field}</Text>（分类字段）：
                              共 <Text code>{stats.unique_count}</Text> 个不同取值，
                              最常见的是 <Text code>"{stats.most_frequent}"</Text>
                              （出现{stats.most_frequent_count}次）
                              {stats.null_count > 0 && (
                                <Text type="secondary">（缺失{stats.null_percentage}%）</Text>
                              )}
                            </Text>
                          );
                        } else {
                          return (
                            <Text key={field} style={{ display: 'block', marginBottom: '6px' }}>
                              • <Text strong>{field}</Text>（{stats.type}字段）：
                              {stats.unique_count} 个不同值
                              {stats.null_count > 0 && (
                                <Text type="secondary">（缺失{stats.null_percentage}%）</Text>
                              )}
                            </Text>
                          );
                        }
                      })}
                      
                      {shouldCollapse && (
                        <div style={{ marginTop: '8px' }}>
                          <Button 
                            type="link" 
                            size="small" 
                            onClick={() => setExpandedFieldSummary(!expandedFieldSummary)}
                            style={{ padding: '0', height: 'auto', fontSize: '12px' }}
                          >
                            {expandedFieldSummary 
                              ? `收起字段详情 ▲` 
                              : `展开全部字段（还有${fieldEntries.length - 5}个）▼`
                            }
                          </Button>
                        </div>
                      )}
                    </>
                  );
                })()}
                
                {/* TOP排名概述 */}
                {Object.keys(analysisResult.basic_stats_overview.top_rankings).length > 0 && (
                  <>
                    <br />
                    <Text strong style={{ fontSize: '16px', color: '#1890ff', display: 'block', marginBottom: '8px' }}>
                      🏆 TOP排名概述
                    </Text>
                    {Object.entries(analysisResult.basic_stats_overview.top_rankings).map(([field, ranking]) => {
                      const topItems = Object.entries(ranking.top_5).slice(0, 3);
                      return (
                        <Text key={field} style={{ display: 'block', marginBottom: '6px' }}>
                          • <Text strong>{field}</Text> 排名前三位：
                          {topItems.map(([value, count], idx) => 
                            <Text code key={idx} style={{ marginLeft: '4px' }}>
                              {idx + 1}. {value}（{count}次）
                            </Text>
                          )}
                          ，共有{ranking.total_unique}个不同类别
                        </Text>
                      );
                    })}
                  </>
                )}
                
                {/* 数据质量提醒 */}
                {analysisResult.basic_stats_overview.data_quality.potential_issues.length > 0 && (
                  <>
                    <br />
                    <div style={{ 
                      padding: '12px',
                      background: '#fff7e6',
                      border: '1px solid #ffd591',
                      borderRadius: '6px',
                      marginTop: '12px'
                    }}>
                      <Text strong style={{ fontSize: '16px', color: '#fa8c16', display: 'block', marginBottom: '8px' }}>
                        ⚠️ 数据质量提醒
                      </Text>
                      {analysisResult.basic_stats_overview.data_quality.potential_issues.map((issue, index) => (
                        <Text key={index} style={{ display: 'block', marginBottom: '6px' }}>
                          在 <Text strong>{issue.field}</Text> 字段中{issue.issue}，
                          这可能影响分析准确性。
                          {issue.examples && issue.examples.length > 0 && (
                            <Text type="secondary" style={{ fontSize: '12px', display: 'block', marginTop: '2px' }}>
                              例如：{issue.examples.map(ex => `"${ex.base}" 与 "${ex.similar.join('、')}"`).join('；')}
                            </Text>
                          )}
                        </Text>
                      ))}
                    </div>
                  </>
                )}
              </div>
            </Card>
          )}

          {/* 结构化数据表格展示 */}
          {analysisResult.data_tables && analysisResult.data_tables.length > 0 && (
            <Card 
              title={<><TableOutlined /> 数据分析结果</>}
              style={{ marginBottom: 24 }}
            >
              <div style={{ marginBottom: 16 }}>
                <Text type="secondary">
                  以下是基于数据分析生成的结构化结果表格，包含实际的数值统计和排名信息：
                </Text>
              </div>
              
              {analysisResult.data_tables.map((table, index) => (
                <div key={index} style={{ marginBottom: 24 }}>
                  <div style={{ marginBottom: 12 }}>
                    <Text strong style={{ fontSize: '16px', color: '#1890ff' }}>
                      {table.title}
                    </Text>
                    {table.description && (
                      <Text type="secondary" style={{ marginLeft: 16, fontSize: '13px' }}>
                        {table.description}
                      </Text>
                    )}
                  </div>
                  
                  {table.type === 'stats_table' && (
                    <Table
                      dataSource={table.data}
                      pagination={false}
                      size="small"
                      scroll={{ x: true }}
                      columns={[
                        {
                          title: '字段名',
                          dataIndex: '字段名',
                          key: '字段名',
                          fixed: 'left',
                          width: 120
                        },
                        {
                          title: '数据类型',
                          dataIndex: '数据类型',
                          key: '数据类型',
                          width: 100,
                          render: (type) => {
                            const color = {
                              'numeric': 'blue',
                              'categorical': 'green', 
                              'text': 'orange',
                              'datetime': 'purple'
                            }[type] || 'default';
                            return <Tag color={color}>{type}</Tag>
                          }
                        },
                        {
                          title: '有效记录数',
                          dataIndex: '有效记录数',
                          key: '有效记录数',
                          width: 100
                        },
                        {
                          title: '缺失率',
                          dataIndex: '缺失率',
                          key: '缺失率',
                          width: 80
                        },
                        {
                          title: '平均值',
                          dataIndex: '平均值',
                          key: '平均值',
                          width: 100,
                          render: (value) => value != null ? (typeof value === 'number' ? value.toFixed(2) : value) : '-'
                        },
                        {
                          title: '中位数',
                          dataIndex: '中位数',
                          key: '中位数',
                          width: 100,
                          render: (value) => value != null ? (typeof value === 'number' ? value.toFixed(2) : value) : '-'
                        },
                        {
                          title: '最小值',
                          dataIndex: '最小值',
                          key: '最小值',
                          width: 100,
                          render: (value) => value != null ? value : '-'
                        },
                        {
                          title: '最大值',
                          dataIndex: '最大值',
                          key: '最大值',
                          width: 100,
                          render: (value) => value != null ? value : '-'
                        },
                        {
                          title: '唯一值数量',
                          dataIndex: '唯一值数量',
                          key: '唯一值数量',
                          width: 100,
                          render: (value) => value != null ? value : '-'
                        },
                        {
                          title: '最常见值',
                          dataIndex: '最常见值',
                          key: '最常见值',
                          width: 120,
                          render: (value) => value != null ? (
                            <Text code style={{ fontSize: '12px' }}>{value}</Text>
                          ) : '-'
                        }
                      ]}
                    />
                  )}
                  
                  {table.type === 'ranking_table' && (
                    <Table
                      dataSource={table.data}
                      pagination={false}
                      size="small"
                      columns={[
                        {
                          title: '排名',
                          dataIndex: '排名',
                          key: '排名',
                          width: 60,
                          render: (rank) => (
                            <Tag color={rank <= 3 ? 'gold' : 'default'}>
                              #{rank}
                            </Tag>
                          )
                        },
                        {
                          title: '值',
                          dataIndex: '值',
                          key: '值',
                          ellipsis: true
                        },
                        {
                          title: '出现次数',
                          dataIndex: '出现次数',
                          key: '出现次数',
                          width: 100
                        },
                        {
                          title: '占比',
                          dataIndex: '占比',
                          key: '占比',
                          width: 80
                        }
                      ]}
                    />
                  )}
                  
                  {table.type === 'aggregation_table' && (
                    <Table
                      dataSource={table.data}
                      pagination={false}
                      size="small"
                      columns={[
                        {
                          title: '字段',
                          dataIndex: '字段',
                          key: '字段'
                        },
                        {
                          title: '统计类型',
                          dataIndex: '统计类型',
                          key: '统计类型',
                          render: (type) => <Tag color="blue">{type}</Tag>
                        },
                        {
                          title: '数值',
                          dataIndex: '数值',
                          key: '数值',
                          render: (value) => (
                            <Text strong style={{ color: '#1890ff' }}>
                              {typeof value === 'number' ? value.toLocaleString() : value}
                            </Text>
                          )
                        }
                      ]}
                    />
                  )}
                </div>
              ))}
            </Card>
          )}

          {/* 综合分析报告 */}
          <Card 
            title={<><FileTextOutlined /> 专业分析报告</>}
            style={{ marginBottom: 24 }}
          >
            {analysisResult.ai_insights ? (
              <div>
                {(() => {
                  const parsedSections = parseAIInsights(analysisResult.ai_insights);
                  
                  if (parsedSections.length === 0) {
                    return (
                      <div style={{ whiteSpace: 'pre-wrap', background: '#fafafa', padding: 16, borderRadius: 6 }}>
                        {analysisResult.ai_insights}
                      </div>
                    );
                  }
                  
                  return parsedSections.map((section, index) => (
                    <Card 
                      key={index}
                      size="small" 
                      title={
                        <Space>
                          <span style={{ fontSize: '16px' }}>{section.icon}</span>
                          <Text strong style={{ color: '#1890ff' }}>{section.title}</Text>
                        </Space>
                      }
                      style={{ marginBottom: 16 }}
                      bodyStyle={{ padding: '12px 16px' }}
                    >
                      <List
                        size="small"
                        dataSource={section.content}
                        renderItem={item => (
                          <List.Item style={{ padding: '4px 0', border: 'none' }}>
                            <Text>{item}</Text>
                          </List.Item>
                        )}
                      />
                    </Card>
                  ));
                })()}
              </div>
            ) : (
              <div style={{ padding: 16, background: '#f0f2f5', borderRadius: 6 }}>
                <p>✅ 数据分析已完成</p>
                <p>📊 分析类型: {analysisResult.analysis_type || '统计分析'}</p>
                <p>📈 数据规模: {analysisResult.statistics ? Object.keys(analysisResult.statistics).length : 0} 个字段</p>
                {analysisResult.charts && analysisResult.charts.length > 0 && (
                  <p>📈 生成图表: {analysisResult.charts.length} 个</p>
                )}
              </div>
            )}
          </Card>

          {/* 专业分析结果展示 */}
          {analysisResult && (
            <div style={{ marginBottom: 24 }}>
              {/* 主要分析结果 */}
              {analysisResult?.primary_analysis && (
                <Card 
                  title={`📊 ${analysisResult.primary_analysis.analysis_title || '主要分析'}`} 
                  style={{ marginBottom: 24 }}
                  extra={
                    <Space>
                      <Tag color="blue">
                        {analysisResult.analysis_type === 'business_analysis' ? '商业分析' :
                         analysisResult.analysis_type === 'comparative_analysis' ? '对比分析' :
                         analysisResult.analysis_type === 'statistical_analysis' ? '统计分析' :
                         analysisResult.analysis_type === 'categorical_analysis' ? '分类分析' : '描述分析'}
                      </Tag>
                      {analysisResult.analysis_type === 'business_analysis' && analysisResult.primary_analysis.market_structure && (
                        <Tag color="orange">{analysisResult.primary_analysis.market_structure.type}</Tag>
                      )}
                    </Space>
                  }
                >
                  {/* 专业指标展示 */}
                  {analysisResult.analysis_type === 'business_analysis' && analysisResult.primary_analysis.market_structure && (
                    <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
                      <Col xs={12} sm={6}>
                        <Statistic 
                          title="HHI指数" 
                          value={analysisResult.primary_analysis.market_structure.hhi_index} 
                          precision={4}
                          valueStyle={{ color: analysisResult.primary_analysis.market_structure.hhi_index > 0.25 ? '#cf1322' : '#3f8600' }}
                        />
                      </Col>
                      <Col xs={12} sm={6}>
                        <Statistic 
                          title="基尼系数" 
                          value={analysisResult.primary_analysis.market_structure.gini_coefficient} 
                          precision={3}
                          valueStyle={{ color: analysisResult.primary_analysis.market_structure.gini_coefficient > 0.6 ? '#cf1322' : '#3f8600' }}
                        />
                      </Col>
                      <Col xs={12} sm={6}>
                        <Statistic 
                          title="前3集中度" 
                          value={analysisResult.primary_analysis.market_structure.top_3_concentration} 
                          suffix="%" 
                          precision={1}
                        />
                      </Col>
                      <Col xs={12} sm={6}>
                        <Statistic 
                          title="帕累托比例" 
                          value={analysisResult.primary_analysis.market_structure.pareto_ratio} 
                          suffix="%" 
                          precision={1}
                        />
                      </Col>
                    </Row>
                  )}

                  {/* 统计分析专业指标 */}
                  {analysisResult.analysis_type === 'statistical_analysis' && analysisResult.primary_analysis.sample_size && (
                    <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
                      <Col xs={12} sm={6}>
                        <Statistic title="样本量" value={analysisResult.primary_analysis.sample_size} />
                      </Col>
                      <Col xs={12} sm={6}>
                        <Statistic title="分析变量" value={analysisResult.primary_analysis.variables_analyzed} />
                      </Col>
                      <Col xs={12} sm={6}>
                        <Statistic 
                          title="正态分布变量" 
                          value={Object.values(analysisResult.primary_analysis.statistical_summary || {}).filter(s => s.is_normal).length} 
                        />
                      </Col>
                      <Col xs={12} sm={6}>
                        <Statistic 
                          title="高变异变量" 
                          value={Object.values(analysisResult.primary_analysis.statistical_summary || {}).filter(s => s.cv > 0.5).length} 
                        />
                      </Col>
                    </Row>
                  )}

                  <Row gutter={[16, 16]}>
                    {/* 显示图表 */}
                    {analysisResult?.charts && analysisResult.charts.length > 0 && (
                      <>
                        {analysisResult.charts.slice(0, 2).map((chartData, index) => (
                          <Col xs={24} lg={12} key={index}>
                            <ChartDisplay chartData={chartData} />
                            {chartData.subtitle && (
                              <div style={{ padding: '8px 16px', background: '#f0f2f5', borderRadius: '4px', marginTop: '8px' }}>
                                <Text type="secondary" style={{ fontSize: '12px' }}>
                                  {chartData.subtitle}
                                </Text>
                              </div>
                            )}
                          </Col>
                        ))}
                      </>
                    )}
                  </Row>

                  {/* 专业洞察展示 */}
                  {(analysisResult.business_insights || analysisResult.statistical_insights) && (
                    <div style={{ marginTop: 16 }}>
                      <Divider orientation="left">💡 专业洞察</Divider>
                      <List
                        size="small"
                        dataSource={analysisResult.business_insights || analysisResult.statistical_insights || []}
                        renderItem={item => (
                          <List.Item>
                            <Text>{item}</Text>
                          </List.Item>
                        )}
                      />
                    </div>
                  )}
                </Card>
              )}

              {/* 次要分析结果 */}
              {analysisResult?.secondary_analysis && (
                <Card 
                  title={`🔍 ${analysisResult.secondary_analysis.analysis_title || '次要分析'}`} 
                  style={{ marginBottom: 24 }}
                >
                  <Row gutter={[16, 16]}>
                    {/* 显示剩余的图表 */}
                    {analysisResult?.charts && analysisResult.charts.length > 2 && (
                      <>
                        {analysisResult.charts.slice(2, 4).map((chartData, index) => (
                          <Col xs={24} lg={12} key={index + 2}>
                            <ChartDisplay chartData={chartData} />
                            <div style={{ padding: '8px 16px', background: '#f6f6f6', borderRadius: '4px', marginTop: '8px' }}>
                              <Text type="secondary" style={{ fontSize: '12px' }}>
                                {getChartInsight(chartData, analysisResult, index + 2)}
                              </Text>
                            </div>
                          </Col>
                        ))}
                      </>
                    )}
                    
                    {/* 相关性分析特殊显示 */}
                    {analysisResult.secondary_analysis.correlations && (
                      <Col xs={24}>
                        <Card size="small" title="字段相关性分析">
                          <List
                            size="small"
                            dataSource={analysisResult.secondary_analysis.correlations}
                            renderItem={(item) => (
                              <List.Item>
                                <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                                  <Text>{item.field1} ↔ {item.field2}</Text>
                                  <Space>
                                    <Text strong>{item.correlation?.toFixed(3)}</Text>
                                    <Tag color={Math.abs(item.correlation) > 0.7 ? 'red' : Math.abs(item.correlation) > 0.3 ? 'orange' : 'blue'}>
                                      {item.strength}
                                    </Tag>
                                  </Space>
                                </Space>
                              </List.Item>
                            )}
                          />
                        </Card>
                      </Col>
                    )}
                    
                    {/* 其他次要分析结果 */}
                    {!analysisResult.secondary_analysis.correlations && (
                      <Col xs={24}>
                        <div style={{ padding: '16px', background: '#fafafa', borderRadius: '6px' }}>
                          <Text type="secondary">
                            {analysisResult.secondary_analysis.analysis_title} 提供了补充性的分析视角
                          </Text>
                        </div>
                      </Col>
                    )}
                  </Row>
                </Card>
              )}

              {/* 战略建议展示 */}
              {(analysisResult.strategic_recommendations || analysisResult.modeling_recommendations) && (
                <Card title="🎯 专业建议" style={{ marginBottom: 24 }}>
                  <List
                    dataSource={analysisResult.strategic_recommendations || analysisResult.modeling_recommendations || []}
                    renderItem={(item, index) => (
                      <List.Item>
                        <div style={{ width: '100%' }}>
                          <Text strong style={{ color: '#1890ff' }}>建议 {index + 1}:</Text>
                          <br />
                          <Text>{item}</Text>
                        </div>
                      </List.Item>
                    )}
                  />
                </Card>
              )}

              {/* 剩余图表展示 */}
              {analysisResult?.charts && analysisResult.charts.length > 2 && (
                <Card title="📈 补充分析图表" style={{ marginBottom: 24 }}>
                  <Row gutter={[16, 16]}>
                    {analysisResult.charts.slice(2).map((chartData, index) => (
                      <Col xs={24} lg={12} key={index + 2}>
                        <ChartDisplay chartData={chartData} />
                        {chartData.subtitle && (
                          <div style={{ padding: '8px 16px', background: '#f0f2f5', borderRadius: '4px', marginTop: '8px' }}>
                            <Text type="secondary" style={{ fontSize: '12px' }}>
                              {chartData.subtitle}
                            </Text>
                          </div>
                        )}
                      </Col>
                    ))}
                  </Row>
                </Card>
              )}
            </div>
          )}

          {/* 可视化图表 - 嵌入到分析报告中 */}
          {analysisResult?.charts && analysisResult.charts.length > 0 && (
            <Card title={<><BarChartOutlined /> 数据可视化分析</>} style={{ marginBottom: 24 }}>
              <div style={{ marginBottom: 16 }}>
                <Text type="secondary">
                  以下图表直观展示了数据分析的关键发现，每个图表都对应分析报告中的具体洞察点：
                </Text>
              </div>
              <Row gutter={[16, 16]}>
                {analysisResult.charts.map((chartData, index) => (
                  <Col xs={24} lg={12} key={index}>
                    <div style={{ 
                      border: '1px solid #f0f0f0', 
                      borderRadius: '8px', 
                      padding: '16px',
                      background: '#fafafa',
                      marginBottom: '16px'
                    }}>
                      <div style={{ marginBottom: '12px' }}>
                        <Text strong style={{ fontSize: '16px', color: '#1890ff' }}>
                          📈 {chartData.title}
                        </Text>
                      </div>
                      <ChartDisplay chartData={chartData} />
                      <div style={{ 
                        marginTop: '12px', 
                        padding: '8px 12px', 
                        background: '#f6f6f6', 
                        borderRadius: '4px',
                        borderLeft: '4px solid #1890ff'
                      }}>
                        <Text type="secondary" style={{ fontSize: '13px' }}>
                          <strong>图表解读：</strong>
                          {chartData.subtitle || getChartInsight(chartData, analysisResult, index)}
                        </Text>
                      </div>
                    </div>
                  </Col>
                ))}
              </Row>
            </Card>
          )}


        </>
      )}
      </div>
    </>
  );
};

export default DataAnalysis;