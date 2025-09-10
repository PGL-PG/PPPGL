import React from 'react';
import ReactECharts from 'echarts-for-react';
import { Card, Typography } from 'antd';

const { Title } = Typography;

const ChartDisplay = ({ chartData }) => {
  const getChartOption = () => {
    const { type, column, data } = chartData;

    switch (type) {
      case 'histogram':
        return {
          title: {
            text: `${column} 分布图`,
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
            name: column
          },
          yAxis: {
            type: 'value',
            name: '频次'
          },
          series: [{
            name: '频次',
            type: 'bar',
            data: data.map((value, index) => [value, 1]),
            itemStyle: {
              color: '#1890ff'
            }
          }]
        };

      case 'pie':
        return {
          title: {
            text: `${column} 分布`,
            left: 'center'
          },
          tooltip: {
            trigger: 'item',
            formatter: '{a} <br/>{b}: {c} ({d}%)'
          },
          legend: {
            orient: 'vertical',
            left: 'left'
          },
          series: [{
            name: column,
            type: 'pie',
            radius: '50%',
            data: data,
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            }
          }]
        };

      case 'line':
        return {
          title: {
            text: `${column} 趋势图`,
            left: 'center'
          },
          tooltip: {
            trigger: 'axis'
          },
          xAxis: {
            type: 'category',
            data: data.map((_, index) => index + 1)
          },
          yAxis: {
            type: 'value',
            name: column
          },
          series: [{
            name: column,
            type: 'line',
            data: data,
            smooth: true,
            itemStyle: {
              color: '#52c41a'
            }
          }]
        };

      case 'bar':
        return {
          title: {
            text: `${column} 柱状图`,
            left: 'center'
          },
          tooltip: {
            trigger: 'axis',
            axisPointer: {
              type: 'shadow'
            }
          },
          xAxis: {
            type: 'category',
            data: data.map(item => item.name || item.x)
          },
          yAxis: {
            type: 'value',
            name: column
          },
          series: [{
            name: column,
            type: 'bar',
            data: data.map(item => item.value || item.y),
            itemStyle: {
              color: '#fa8c16'
            }
          }]
        };

      case 'scatter':
        return {
          title: {
            text: `${column} 散点图`,
            left: 'center'
          },
          tooltip: {
            trigger: 'item'
          },
          xAxis: {
            type: 'value',
            name: 'X轴'
          },
          yAxis: {
            type: 'value',
            name: 'Y轴'
          },
          series: [{
            name: column,
            type: 'scatter',
            data: data,
            itemStyle: {
              color: '#722ed1'
            }
          }]
        };

      default:
        return {
          title: {
            text: '暂不支持的图表类型',
            left: 'center'
          }
        };
    }
  };

  return (
    <div className="chart-container">
      <ReactECharts
        option={getChartOption()}
        style={{ height: '400px', width: '100%' }}
        opts={{ renderer: 'canvas' }}
      />
    </div>
  );
};

export default ChartDisplay;