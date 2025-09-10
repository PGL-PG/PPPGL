import React, { useState } from 'react';
import { 
  Select, 
  Button, 
  Typography, 
  Row, 
  Col, 
  Card, 
  Spin, 
  Progress,
  Table,
  Tag,
  Space,
  message
} from 'antd';
import { FundOutlined, TrophyOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import axios from 'axios';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

const AttributionAnalysis = ({ filename, sheetName, availableColumns }) => {
  const [targetColumn, setTargetColumn] = useState('');
  const [attributionResult, setAttributionResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleAttributionAnalysis = async () => {
    if (!targetColumn) {
      message.warning('请选择目标指标列');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post('/api/attribution', {
        filename,
        sheet_name: sheetName,
        target_column: targetColumn
      });

      setAttributionResult(response.data);
      message.success('归因分析完成！');
    } catch (error) {
      const errorMsg = error.response?.data?.error || '归因分析失败';
      message.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  // 相关性图表配置
  const getCorrelationChartOption = () => {
    if (!attributionResult?.correlations) return {};

    const correlations = Object.entries(attributionResult.correlations);
    const sortedCorrelations = correlations.sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]));

    return {
      title: {
        text: '相关性分析',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        }
      },
      xAxis: {
        type: 'value',
        min: -1,
        max: 1,
        name: '相关系数'
      },
      yAxis: {
        type: 'category',
        data: sortedCorrelations.map(([name]) => name),
        name: '影响因素'
      },
      series: [{
        name: '相关系数',
        type: 'bar',
        data: sortedCorrelations.map(([name, value]) => ({
          value: value,
          itemStyle: {
            color: value > 0 ? '#52c41a' : '#ff4d4f'
          }
        })),
        label: {
          show: true,
          position: 'right',
          formatter: '{c}'
        }
      }]
    };
  };

  // 贡献度表格数据
  const getContributionTableData = () => {
    if (!attributionResult?.contributions) return [];

    const data = [];
    Object.entries(attributionResult.contributions).forEach(([factor, categories]) => {
      Object.entries(categories).forEach(([category, contribution]) => {
        data.push({
          key: `${factor}-${category}`,
          factor,
          category,
          contribution: contribution.toFixed(2),
          impact: Math.abs(contribution) > 10 ? 'high' : Math.abs(contribution) > 5 ? 'medium' : 'low'
        });
      });
    });

    return data.sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution));
  };

  const contributionColumns = [
    {
      title: '影响因素',
      dataIndex: 'factor',
      key: 'factor',
    },
    {
      title: '类别',
      dataIndex: 'category',
      key: 'category',
    },
    {
      title: '贡献度 (%)',
      dataIndex: 'contribution',
      key: 'contribution',
      render: (value) => (
        <span style={{ color: value > 0 ? '#52c41a' : '#ff4d4f' }}>
          {value > 0 ? '+' : ''}{value}%
        </span>
      )
    },
    {
      title: '影响程度',
      dataIndex: 'impact',
      key: 'impact',
      render: (impact) => {
        const colors = { high: 'red', medium: 'orange', low: 'green' };
        const texts = { high: '高', medium: '中', low: '低' };
        return <Tag color={colors[impact]}>{texts[impact]}</Tag>;
      }
    }
  ];

  return (
    <div>
      {/* 配置区域 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={16} align="middle">
          <Col span={12}>
            <Text strong>选择目标指标：</Text>
            <Select
              style={{ width: '100%', marginTop: 8 }}
              placeholder="选择要分析的目标指标列"
              value={targetColumn}
              onChange={setTargetColumn}
            >
              {availableColumns.map(col => (
                <Option key={col} value={col}>{col}</Option>
              ))}
            </Select>
          </Col>
          <Col span={12}>
            <Button 
              type="primary" 
              icon={<FundOutlined />}
              onClick={handleAttributionAnalysis}
              loading={loading}
              block
              style={{ marginTop: 24 }}
            >
              开始归因分析
            </Button>
          </Col>
        </Row>
      </Card>

      {loading && (
        <Card>
          <div className="loading-container">
            <Spin size="large" />
            <Text style={{ marginLeft: 16 }}>正在进行归因诊断...</Text>
          </div>
        </Card>
      )}

      {attributionResult && !loading && (
        <>
          {/* 目标指标概览 */}
          <Card title={<><TrophyOutlined /> 目标指标概览</>} style={{ marginBottom: 16 }}>
            <Row gutter={16}>
              <Col span={6}>
                <Card size="small">
                  <Text type="secondary">平均值</Text>
                  <Title level={4} style={{ margin: 0 }}>
                    {attributionResult.target_stats.mean.toFixed(2)}
                  </Title>
                </Card>
              </Col>
              <Col span={6}>
                <Card size="small">
                  <Text type="secondary">标准差</Text>
                  <Title level={4} style={{ margin: 0 }}>
                    {attributionResult.target_stats.std.toFixed(2)}
                  </Title>
                </Card>
              </Col>
              <Col span={6}>
                <Card size="small">
                  <Text type="secondary">最小值</Text>
                  <Title level={4} style={{ margin: 0 }}>
                    {attributionResult.target_stats.min.toFixed(2)}
                  </Title>
                </Card>
              </Col>
              <Col span={6}>
                <Card size="small">
                  <Text type="secondary">最大值</Text>
                  <Title level={4} style={{ margin: 0 }}>
                    {attributionResult.target_stats.max.toFixed(2)}
                  </Title>
                </Card>
              </Col>
            </Row>
          </Card>

          {/* 相关性分析 */}
          {Object.keys(attributionResult.correlations).length > 0 && (
            <Card title="📊 相关性分析" style={{ marginBottom: 16 }}>
              <ReactECharts
                option={getCorrelationChartOption()}
                style={{ height: '300px', width: '100%' }}
              />
            </Card>
          )}

          {/* 贡献度分析 */}
          {Object.keys(attributionResult.contributions).length > 0 && (
            <Card title="🎯 贡献度分析" style={{ marginBottom: 16 }}>
              <Table
                columns={contributionColumns}
                dataSource={getContributionTableData()}
                pagination={{ pageSize: 10 }}
                size="small"
              />
            </Card>
          )}

          {/* 异常检测 */}
          <Card 
            title={<><ExclamationCircleOutlined /> 异常检测</>} 
            style={{ marginBottom: 16 }}
          >
            <Row gutter={16}>
              <Col span={12}>
                <Text strong>异常值数量：</Text>
                <Tag color={attributionResult.outliers_count > 0 ? 'red' : 'green'} style={{ marginLeft: 8 }}>
                  {attributionResult.outliers_count} 个
                </Tag>
              </Col>
              <Col span={12}>
                <Text strong>异常比例：</Text>
                <Progress 
                  percent={((attributionResult.outliers_count / (attributionResult.outliers_data?.length || 1)) * 100).toFixed(1)}
                  status={attributionResult.outliers_count > 0 ? 'exception' : 'success'}
                  size="small"
                />
              </Col>
            </Row>
          </Card>

          {/* AI 归因报告 */}
          <Card title="🤖 AI 归因诊断报告">
            <Paragraph style={{ 
              background: '#f6ffed', 
              padding: 16, 
              borderRadius: 6, 
              border: '1px solid #b7eb8f',
              whiteSpace: 'pre-wrap'
            }}>
              {attributionResult.attribution_report}
            </Paragraph>
          </Card>
        </>
      )}
    </div>
  );
};

export default AttributionAnalysis;