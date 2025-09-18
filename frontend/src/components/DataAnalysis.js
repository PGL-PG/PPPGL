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

// 添加自定义样式
const customStyles = `
  .analysis-report-highlight-number {
    color: #1890ff;
    font-weight: bold;
    background: #e6f7ff;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'Consolas', 'Monaco', monospace;
  }
  
  .analysis-report-highlight-brand {
    color: #722ed1;
    font-weight: bold;
    background: #f9f0ff;
    padding: 2px 6px;
    border-radius: 4px;
  }
  
  .analysis-report-highlight-keyword {
    color: #fa8c16;
    font-weight: bold;
  }
  
  .analysis-report-content {
    line-height: 1.8;
    font-size: 14px;
  }
  
  .analysis-report-section {
    border-left: 4px solid #1890ff;
    padding-left: 16px;
    margin: 16px 0;
  }
`;

// 添加样式到文档
if (typeof document !== 'undefined' && !document.getElementById('analysis-report-styles')) {
  const styleSheet = document.createElement('style');
  styleSheet.id = 'analysis-report-styles';
  styleSheet.textContent = customStyles;
  document.head.appendChild(styleSheet);
}

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

  // 解析分析洞察为结构化内容（过滤可视化建议部分）
  const parseAnalysisInsights = (analysisText) => {
    if (!analysisText || typeof analysisText !== 'string') return [];
    
    const sections = [];
    const lines = analysisText.split('\n').filter(line => line.trim());
    
    let currentSection = null;
    let skipVisualizationSection = false;
    
    for (const line of lines) {
      const trimmedLine = line.trim();
      
      // 检测标题行（以 ## 开头）
      if (trimmedLine.startsWith('##')) {
        // 结束上一个section
        if (currentSection && !skipVisualizationSection) {
          sections.push(currentSection);
        }
        
        const title = trimmedLine.replace(/^##\s*/, '');
        
        // 检测是否为可视化建议相关的章节 - 完全过滤可视化相关章节
        skipVisualizationSection = title.includes('可视化建议') || 
                                   title.includes('推荐图表') || 
                                   title.includes('图表组合') ||
                                   title.includes('图表推荐') ||
                                   title.includes('可视化推荐') ||
                                   title.includes('Excel多维度可视化') ||
                                   title.includes('Excel可视化') ||
                                   title.includes('多维度可视化方案') ||
                                   title.includes('可视化方案') ||
                                   title.includes('图表建议') ||
                                   title.includes('图表分析') ||
                                   (title.includes('📊') && (title.includes('Excel') || title.includes('可视化') || title.includes('图表')));
        
        if (!skipVisualizationSection) {
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
        } else {
          currentSection = null;
        }
      }
      // 检测列表项（以 - 开头）
      else if (trimmedLine.startsWith('-') && !skipVisualizationSection) {
        const content = trimmedLine.replace(/^-\s*/, '');
        
        // 过滤可视化相关的列表项 - 完全过滤图表相关内容
        if (!content.includes('柱状图') && 
            !content.includes('饼图') && 
            !content.includes('折线图') && 
            !content.includes('散点图') && 
            !content.includes('热力图') &&
            !content.includes('箱线图') &&
            !content.includes('直方图') &&
            !content.includes('图表类型') &&
            !content.includes('维度字段') &&
            !content.includes('度量字段') &&
            !content.includes('推荐理由') &&
            !content.includes('预期洞察') &&
            !content.includes('图表说明') &&
            !content.includes('分析目标') &&
            !content.includes('图表建议') &&
            !content.includes('可视化类型') &&
            !(/图表\d+[：:]/.test(content)) &&
            !(/💡\s*图表/.test(content))) {
          
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
      }
      // 检测三级标题（### 开头的图表标题）
      else if (trimmedLine.startsWith('###') && !skipVisualizationSection) {
        // 如果遇到图表相关的三级标题，开始跳过
        if (trimmedLine.includes('图表') || trimmedLine.includes('可视化')) {
          skipVisualizationSection = true;
          // 结束当前section
          if (currentSection) {
            sections.push(currentSection);
            currentSection = null;
          }
        }
      }
      // 其他内容行
      else if (trimmedLine && currentSection && !skipVisualizationSection) {
        // 过滤可视化相关的内容 - 完全过滤图表相关内容
        if (!trimmedLine.includes('柱状图') &&
            !trimmedLine.includes('饼图') &&
            !trimmedLine.includes('折线图') &&
            !trimmedLine.includes('散点图') &&
            !trimmedLine.includes('热力图') &&
            !trimmedLine.includes('箱线图') &&
            !trimmedLine.includes('直方图') &&
            !trimmedLine.includes('图表类型') &&
            !trimmedLine.includes('维度字段') &&
            !trimmedLine.includes('度量字段') &&
            !trimmedLine.includes('推荐理由') &&
            !trimmedLine.includes('预期洞察') &&
            !trimmedLine.includes('图表说明') &&
            !trimmedLine.includes('分析目标') &&
            !trimmedLine.includes('图表建议') &&
            !trimmedLine.includes('可视化类型') &&
            !(/图表\d+[：:]/.test(trimmedLine)) &&
            !(/💡\s*图表/.test(trimmedLine))) {
          currentSection.content.push(trimmedLine);
        }
      }
    }
    
    // 添加最后一个section（如果不是可视化建议部分）
    if (currentSection && !skipVisualizationSection) {
      sections.push(currentSection);
    }
    
    // 如果没有解析到任何section，将整个文本作为一个section（过滤可视化相关内容）
    if (sections.length === 0 && analysisText.trim()) {
      const filteredText = analysisText.split('\n')
        .filter(line => {
          const trimmed = line.trim();
          return !trimmed.includes('可视化建议') &&
                 !trimmed.includes('推荐图表') &&
                 !trimmed.includes('柱状图') &&
                 !trimmed.includes('饼图') &&
                 !trimmed.includes('折线图') &&
                 !trimmed.includes('散点图') &&
                 !trimmed.includes('热力图') &&
                 !trimmed.includes('箱线图') &&
                 !trimmed.includes('直方图') &&
                 !trimmed.includes('维度字段') &&
                 !trimmed.includes('度量字段') &&
                 !trimmed.includes('推荐理由') &&
                 !trimmed.includes('预期洞察') &&
                 !trimmed.includes('图表类型') &&
                 !trimmed.includes('图表建议') &&
                 !trimmed.includes('Excel多维度') &&
                 !trimmed.includes('Excel可视化') &&
                 !(/图表\d+[：:]/.test(trimmed)) &&
                 !(/💡\s*图表/.test(trimmed)) &&
                 !trimmed.startsWith('###') ||
                 (trimmed.startsWith('###') && !trimmed.includes('图表') && !trimmed.includes('可视化'));
        })
        .join('\n')
        .trim();
      
      if (filteredText) {
        sections.push({
          title: '数据分析报告',
          icon: '📊',
          content: [filteredText]
        });
      }
    }
    
    return sections;
  };

  // 美化文本内容，突出数据和关键信息
  const formatContentText = (text) => {
    if (!text || typeof text !== 'string') return text;
    
    // 移除星号标记
    let formattedText = text.replace(/\*\*/g, '');
    
    // 使用正则表达式识别和高亮不同类型的内容
    const parts = [];
    let lastIndex = 0;
    
    // 匹配数字（包含百分比、金额、比例等）
    const numberRegex = /(\d+(?:[.,]\d+)*(?:%|元|万|亿|次|个|件|台|部|款)?)/g;
    // 匹配品牌名称（中英文）
    const brandRegex = /(联想|ThinkPad|华硕|戴尔|苹果|小米|华为|ASUS|HP|惠普|Dell|Apple|Xiaomi|Huawei|Lenovo|OPPO|vivo|三星|Samsung)/g;
    // 匹配关键业务词汇
    const keywordRegex = /(最高|最低|第一|领先|占比|份额|增长|下降|优势|劣势|机会|风险|建议)/g;
    
    let match;
    const matches = [];
    
    // 收集所有匹配项
    while ((match = numberRegex.exec(formattedText)) !== null) {
      matches.push({ start: match.index, end: match.index + match[0].length, type: 'number', text: match[0] });
    }
    
    while ((match = brandRegex.exec(formattedText)) !== null) {
      matches.push({ start: match.index, end: match.index + match[0].length, type: 'brand', text: match[0] });
    }
    
    while ((match = keywordRegex.exec(formattedText)) !== null) {
      matches.push({ start: match.index, end: match.index + match[0].length, type: 'keyword', text: match[0] });
    }
    
    // 按位置排序
    matches.sort((a, b) => a.start - b.start);
    
    // 构建JSX元素
    matches.forEach((match) => {
      // 添加匹配前的普通文本
      if (match.start > lastIndex) {
        const normalText = formattedText.slice(lastIndex, match.start);
        if (normalText) {
          parts.push(<span key={`text-${lastIndex}`}>{normalText}</span>);
        }
      }
      
      // 添加高亮的匹配文本
      let highlightStyle = {};
      let highlightClass = '';
      
      switch (match.type) {
        case 'number':
          highlightStyle = { 
            color: '#1890ff', 
            fontWeight: 'bold', 
            background: '#e6f7ff', 
            padding: '2px 4px', 
            borderRadius: '3px',
            fontFamily: 'monospace'
          };
          break;
        case 'brand':
          highlightStyle = { 
            color: '#722ed1', 
            fontWeight: 'bold',
            background: '#f9f0ff',
            padding: '2px 4px',
            borderRadius: '3px'
          };
          break;
        case 'keyword':
          highlightStyle = { 
            color: '#fa8c16', 
            fontWeight: 'bold'
          };
          break;
      }
      
      parts.push(
        <span key={`highlight-${match.start}`} style={highlightStyle}>
          {match.text}
        </span>
      );
      
      lastIndex = match.end;
    });
    
    // 添加剩余的普通文本
    if (lastIndex < formattedText.length) {
      const remainingText = formattedText.slice(lastIndex);
      if (remainingText) {
        parts.push(<span key={`text-${lastIndex}`}>{remainingText}</span>);
      }
    }
    
    return parts.length > 0 ? parts : formattedText;
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

      // 调用后端分析接口
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

  const currentSheetData = selectedSheet && sheetsData && typeof sheetsData === 'object' ? sheetsData[selectedSheet] : null;
  const availableColumns = currentSheetData?.columns && typeof currentSheetData.columns === 'object' ? Object.keys(currentSheetData.columns) : [];

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

  // 推荐字段选择
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
      width: Math.max(120, Math.min(200, col.length * 8 + 80)), // 动态宽度
      align: columnType === 'numeric' ? 'right' : 'left',
      render: (value) => {
        if (value === null || value === undefined || value === '') {
          return <Text type="secondary" style={{ fontSize: '12px' }}>-</Text>;
        }
        
        // 数值类型格式化
        if (columnType === 'numeric' && typeof value === 'number') {
          return (
            <Text style={{ fontFamily: 'monospace', fontWeight: 500, fontSize: '12px' }}>
              {value.toLocaleString()}
            </Text>
          );
        }
        
        // 文本类型截断显示
        if (typeof value === 'string') {
          const displayValue = value.length > 25 ? value.substring(0, 25) + '...' : value;
          return (
            <Text 
              style={{ fontSize: '12px' }}
              title={value.length > 25 ? value : undefined}
            >
              {displayValue}
            </Text>
          );
        }
        
        return <Text style={{ fontSize: '12px' }}>{String(value)}</Text>;
      }
    };
  }) : [];

  // 渲染数据预览
  const renderDataPreview = () => {
    if (!sheetsData || !currentSheetData) {
      return null;
    }

    return (
      <Card 
        title={
          <Space>
            <BulbOutlined style={{ color: '#1890ff' }} /> 
            <span>数据预览</span>
            <Tag color="blue">{currentSheetData.row_count} 行 × {currentSheetData.column_count} 列</Tag>
          </Space>
        } 
        style={{ marginBottom: 16 }}
      >
        {/* 数据概览信息 */}
        {dataPreview?.preview_insights && (
          <>
            <Divider orientation="left" plain>
              <span>📋 数据概况</span>
            </Divider>
            <List
              size="small"
              dataSource={dataPreview.preview_insights.slice(0, 5) || []}
              renderItem={item => (
                <List.Item>
                  <Text style={{ fontSize: '13px' }}>{item}</Text>
                </List.Item>
              )}
              style={{ marginBottom: 16 }}
            />
          </>
        )}
        
        {/* 前5行数据表格 */}
        <Divider orientation="left" plain>
          <Space>
            <span>📊 前5行数据预览</span>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              共 {currentSheetData?.row_count || 0} 行数据
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
            <span>📊 显示前 5 行，共 {currentSheetData?.row_count || 0} 行数据</span>
            <span>📋 共 {availableColumns.length} 列字段</span>
            <span>🏷️ 数据类型已自动识别</span>
          </Space>
        </div>
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
              {sheetsData && typeof sheetsData === 'object' && Object.keys(sheetsData).length > 0 ? Object.keys(sheetsData).map(sheetName => (
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
                    推荐字段
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
          {/* 先展示可视化图表 */}
          {analysisResult?.charts && analysisResult.charts.length > 0 && (
            <Card 
              title={
                <Space>
                  <BarChartOutlined style={{ color: '#1890ff', fontSize: '16px' }} />
                  <Text strong style={{ color: '#1890ff', fontSize: '16px' }}>数据可视化分析</Text>
                  <Tag color="blue" icon={<BarChartOutlined />}>
                    专业分析
                  </Tag>
                </Space>
              }
              style={{ marginBottom: 24 }}
              extra={
                <Space>
                  <Tag color="blue">
                    {analysisResult.analysis_type?.includes('multidimensional') ? 'Gemini多维度分析' :
                     analysisResult.analysis_type?.includes('gemini') ? 'Gemini主导分析' :
                     analysisResult.analysis_type?.includes('excel') ? 'Excel分析' :
                     analysisResult.analysis_type?.includes('business') ? '商业分析' :
                     '数据分析'}
                  </Tag>
                  <Text type="secondary" style={{ fontSize: '12px' }}>
                    {analysisResult.scenario_info?.multidimensional_features?.length > 0 ? 
                      `支持: ${analysisResult.scenario_info.multidimensional_features.join('、')}` :
                      '基于Gemini的数据理解生成'
                    }
                  </Text>
                </Space>
              }
              headStyle={{
                background: 'linear-gradient(135deg, #e6f7ff 0%, #f0f9ff 100%)',
                borderBottom: '2px solid #91d5ff'
              }}
            >
              <Alert
                message={
                  <Space>
                    <BulbOutlined style={{ color: '#722ed1' }} />
                    <Text strong>AI驱动的智能可视化</Text>
                  </Space>
                }
             
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />
              <Row gutter={[16, 16]}>
                {analysisResult.charts.map((chartData, index) => (
                  <Col xs={24} lg={12} key={index}>
                    <div style={{ border: '1px solid #f0f0f0', borderRadius: '8px', overflow: 'hidden' }}>
                      <div style={{ 
                        padding: '12px 16px', 
                        background: chartData.ai_driven ? 
                          (chartData.multidimensional ? 
                            'linear-gradient(90deg, #f9f0ff 0%, #e6f7ff 50%, #f0f9ff 100%)' : 
                            'linear-gradient(90deg, #f9f0ff 0%, #f0f9ff 100%)'
                          ) : '#fafafa',
                        borderBottom: '1px solid #f0f0f0',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                      }}>
                        <Text strong style={{ color: '#1890ff' }}>{chartData.title}</Text>
                        <Space>
                          {chartData.ai_driven && (
                            <Tag color="purple" size="small">
                              <BulbOutlined /> AI生成
                            </Tag>
                          )}
                          {chartData.multidimensional && (
                            <Tag color="orange" size="small">
                              🔗 多维度
                            </Tag>
                          )}
                          {chartData.dimension_count > 1 && (
                            <Tag color="green" size="small">
                              {chartData.dimension_count}个维度
                            </Tag>
                          )}
                        </Space>
                      </div>
                      <div style={{ padding: '16px' }}>
                        <ChartDisplay chartData={chartData} />
                      </div>
                      {chartData.subtitle && (
                        <div style={{ 
                          padding: '8px 16px', 
                          background: '#f8f9fa', 
                          borderTop: '1px solid #f0f0f0',
                          fontSize: '12px',
                          color: '#666'
                        }}>
                          <Text type="secondary">
                            📊 {chartData.subtitle}
                          </Text>
                        </div>
                      )}
                    </div>
                  </Col>
                ))}
              </Row>
            </Card>
          )}

          {/* 然后展示关键发现（综合分析报告） */}
          <Card 
            title={
              <Space>
                <FileTextOutlined style={{ color: '#1890ff', fontSize: '16px' }} />
                <Text strong style={{ color: '#1890ff', fontSize: '18px' }}>Gemini专业分析报告</Text>
                {analysisResult.ai_called && (
                  <Tag color="green" icon={<BulbOutlined />}>
                    实时AI分析
                  </Tag>
                )}
              </Space>
            }
            style={{ 
              marginBottom: 24,
              border: '1px solid #d9f7be',
              borderRadius: '10px',
              overflow: 'hidden'
            }}
            headStyle={{
              background: 'linear-gradient(135deg, #f6ffed 0%, #e6f7ff 100%)',
              borderBottom: '2px solid #b7eb8f'
            }}
            bodyStyle={{ padding: '24px' }}
          >
            {analysisResult.ai_insights ? (
              <div>
                {(() => {
                  const parsedSections = parseAnalysisInsights(analysisResult.ai_insights);
                  
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
                          <span style={{ fontSize: '18px' }}>{section.icon}</span>
                          <Text strong style={{ color: '#1890ff', fontSize: '16px' }}>{section.title}</Text>
                        </Space>
                      }
                      style={{ 
                        marginBottom: 20,
                        border: '1px solid #e8f4fd',
                        borderRadius: '8px',
                        boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
                      }}
                      headStyle={{
                        background: 'linear-gradient(90deg, #f0f9ff 0%, #e6f7ff 100%)',
                        borderBottom: '1px solid #e8f4fd'
                      }}
                      bodyStyle={{ padding: '16px 20px' }}
                    >
                      <div style={{ lineHeight: '1.8' }}>
                        {section.content.map((item, itemIndex) => (
                          <div 
                            key={itemIndex} 
                            style={{ 
                              marginBottom: '12px',
                              padding: '8px 0',
                              borderBottom: itemIndex < section.content.length - 1 ? '1px dashed #f0f0f0' : 'none',
                              fontSize: '14px'
                            }}
                          >
                            <div style={{ display: 'flex', alignItems: 'flex-start' }}>
                              <span style={{ 
                                color: '#1890ff', 
                                marginRight: '8px', 
                                fontSize: '16px',
                                marginTop: '2px',
                                minWidth: '16px'
                              }}>▶</span>
                              <div style={{ flex: 1, color: '#2c3e50' }}>
                                {formatContentText(item)}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </Card>
                  ));
                })()}
              </div>
            ) : (
              <div style={{ padding: 16, background: '#f0f2f5', borderRadius: 6, textAlign: 'center' }}>
                <Text type="secondary">✅ 数据分析已完成，请查看下方的专业分析结果和可视化图表</Text>
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
                          value={analysisResult.primary_analysis.statistical_summary && typeof analysisResult.primary_analysis.statistical_summary === 'object' ? Object.values(analysisResult.primary_analysis.statistical_summary).filter(s => s && s.is_normal).length : 0} 
                        />
                      </Col>
                      <Col xs={12} sm={6}>
                        <Statistic 
                          title="高变异变量" 
                          value={analysisResult.primary_analysis.statistical_summary && typeof analysisResult.primary_analysis.statistical_summary === 'object' ? Object.values(analysisResult.primary_analysis.statistical_summary).filter(s => s && typeof s.cv === 'number' && s.cv > 0.5).length : 0} 
                        />
                      </Col>
                    </Row>
                  )}

                  {/* 移除了重复的专业洞察展示 */}
                </Card>
              )}

            {/* 图表建议已转换为实际ECharts图表，不再显示文本建议 */}
          </div>
        )}

        </>
      )}
      </div>
    </>
  );
};

export default DataAnalysis;