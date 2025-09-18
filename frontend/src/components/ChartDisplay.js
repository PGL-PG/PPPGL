import React from 'react';
import ReactECharts from 'echarts-for-react';
import { Card, Typography } from 'antd';

const { Title } = Typography;

const ChartDisplay = ({ chartData }) => {
  const getChartOption = () => {
    const { type, column, data, title, subtitle } = chartData;
    const chartTitle = title || `${column || '数据'} 图表`;
    const chartSubtitle = subtitle || '';

    // 调试信息
    console.log('ChartDisplay - 图表类型:', type);
    console.log('ChartDisplay - 图表标题:', chartTitle);
    console.log('ChartDisplay - 数据样本:', data?.slice(0, 3));

    switch (type) {
      case 'histogram':
        // 处理直方图数据
        const histogramData = Array.isArray(data) ? data : [];
        const bins = 10; // 分箱数量
        const min = Math.min(...histogramData);
        const max = Math.max(...histogramData);
        const binWidth = (max - min) / bins;
        
        const binCounts = new Array(bins).fill(0);
        const binLabels = [];
        
        for (let i = 0; i < bins; i++) {
          const binStart = min + i * binWidth;
          const binEnd = min + (i + 1) * binWidth;
          binLabels.push(`${binStart.toFixed(1)}-${binEnd.toFixed(1)}`);
        }
        
        histogramData.forEach(value => {
          const binIndex = Math.min(Math.floor((value - min) / binWidth), bins - 1);
          binCounts[binIndex]++;
        });
        
        return {
          title: {
            text: chartTitle,
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
            data: binLabels,
            name: column || '数值区间'
          },
          yAxis: {
            type: 'value',
            name: '频次'
          },
          series: [{
            name: '频次',
            type: 'bar',
            data: binCounts,
            itemStyle: {
              color: '#1890ff'
            }
          }]
        };

      case 'pie':
        return {
          title: {
            text: chartTitle,
            subtext: chartSubtitle,
            left: 'center',
            textStyle: {
              fontSize: 16,
              fontWeight: 'bold'
            },
            subtextStyle: {
              fontSize: 12,
              color: '#666'
            }
          },
          tooltip: {
            trigger: 'item',
            formatter: '{a} <br/>{b}: {c} ({d}%)'
          },
          legend: {
            orient: 'vertical',
            left: 'left',
            type: 'scroll',
            pageIconSize: 12,
            pageIconColor: '#aaa',
            pageIconInactiveColor: '#2f4554',
            pageFormatter: '{current}/{total}',
            animationDurationUpdate: 800
          },
          series: [{
            name: column || '数据',
            type: 'pie',
            radius: ['20%', '70%'],
            center: ['60%', '50%'],
            data: data,
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            },
            label: {
              formatter: '{b}: {c}\n({d}%)'
            }
          }]
        };

      case 'line':
        return {
          title: {
            text: chartTitle,
            subtext: chartSubtitle,
            left: 'center',
            textStyle: {
              fontSize: 16,
              fontWeight: 'bold'
            },
            subtextStyle: {
              fontSize: 12,
              color: '#666'
            }
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
            text: chartTitle,
            subtext: chartSubtitle,
            left: 'center',
            textStyle: {
              fontSize: 16,
              fontWeight: 'bold'
            },
            subtextStyle: {
              fontSize: 12,
              color: '#666'
            }
          },
          tooltip: {
            trigger: 'axis',
            axisPointer: {
              type: 'shadow'
            },
            formatter: function(params) {
              const param = params[0];
              return `${param.name}<br/>${param.seriesName}: ${param.value?.toLocaleString() || param.value}`;
            }
          },
          grid: {
            left: '3%',
            right: '4%',
            bottom: '15%',
            top: chartSubtitle ? '20%' : '15%',
            containLabel: true
          },
          xAxis: {
            type: 'category',
            data: data.map(item => item.name || item.x),
            axisLabel: {
              rotate: data.length > 8 ? 45 : 0,
              interval: 0,
              fontSize: 11
            }
          },
          yAxis: {
            type: 'value',
            name: column || '数值',
            axisLabel: {
              formatter: function(value) {
                if (value >= 1000000) {
                  return (value / 1000000).toFixed(1) + 'M';
                } else if (value >= 1000) {
                  return (value / 1000).toFixed(1) + 'K';
                }
                return value;
              }
            }
          },
          series: [{
            name: column || '数值',
            type: 'bar',
            data: data.map(item => item.value || item.y),
            itemStyle: {
              color: '#fa8c16'
            },
            markPoint: {
              data: [
                {type: 'max', name: '最大值'},
                {type: 'min', name: '最小值'}
              ]
            }
          }]
        };

      case 'scatter':
        console.log('=== 散点图调试信息 ===');
        console.log('图表类型:', type);
        console.log('数据类型:', typeof data);
        console.log('数据是否为数组:', Array.isArray(data));
        console.log('数据长度:', data?.length);
        console.log('前3个数据点:', data?.slice(0, 3));
        console.log('第一个数据点是否为数组:', Array.isArray(data?.[0]));
        console.log('========================');
        
        return {
          title: {
            text: chartTitle,
            subtext: chartSubtitle,
            left: 'center',
            textStyle: {
              fontSize: 16,
              fontWeight: 'bold'
            },
            subtextStyle: {
              fontSize: 12,
              color: '#666'
            }
          },
          tooltip: {
            trigger: 'item',
            formatter: function(params) {
              return `售价: ${params.data[0]}<br/>销量: ${params.data[1]}`;
            }
          },
          grid: {
            left: '10%',
            right: '10%',
            bottom: '15%',
            top: chartSubtitle ? '25%' : '20%',
            containLabel: true
          },
          xAxis: {
            type: 'value',
            name: '售价',
            nameLocation: 'middle',
            nameGap: 30,
            axisLabel: {
              formatter: function(value) {
                return value.toLocaleString();
              }
            }
          },
          yAxis: {
            type: 'value',
            name: '销量',
            nameLocation: 'middle',
            nameGap: 40,
            axisLabel: {
              formatter: function(value) {
                if (value >= 1000) {
                  return (value / 1000).toFixed(1) + 'K';
                }
                return value;
              }
            }
          },
          series: [{
            name: '数据点',
            type: 'scatter',
            data: data,
            symbolSize: 10,
            symbol: 'circle',
            itemStyle: {
              color: '#722ed1',
              opacity: 0.8,
              borderColor: '#722ed1',
              borderWidth: 1
            },
            emphasis: {
              itemStyle: {
                opacity: 1,
                shadowBlur: 10,
                shadowColor: 'rgba(114, 46, 209, 0.5)'
              }
            }
          }]
        };

      case 'heatmap':
        const heatmapOption = {
          title: {
            text: title || '相关性热力图',
            left: 'center',
            textStyle: {
              fontSize: 16,
              fontWeight: 'bold'
            }
          },
          tooltip: {
            position: 'top',
            formatter: function(params) {
              return `${params.data.field1} ↔ ${params.data.field2}<br/>相关系数: ${params.data.value}`;
            }
          },
          grid: {
            height: '50%',
            top: '10%'
          },
          xAxis: {
            type: 'category',
            data: [...new Set(data.map(d => d.field1))],
            splitArea: {
              show: true
            }
          },
          yAxis: {
            type: 'category',
            data: [...new Set(data.map(d => d.field2))],
            splitArea: {
              show: true
            }
          },
          visualMap: {
            min: -1,
            max: 1,
            calculable: true,
            orient: 'horizontal',
            left: 'center',
            bottom: '15%',
            inRange: {
              color: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#ffffbf', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']
            }
          },
          series: [{
            name: '相关系数',
            type: 'heatmap',
            data: data.map(d => [d.x, d.y, d.value]),
            label: {
              show: true,
              formatter: '{c}'
            },
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            }
          }]
        };
        return heatmapOption;

      case 'boxplot':
        return {
          title: {
            text: title || '箱线图',
            left: 'center',
            textStyle: {
              fontSize: 16,
              fontWeight: 'bold'
            }
          },
          tooltip: {
            trigger: 'item',
            formatter: function(params) {
              const data = params.data;
              return `${params.name}<br/>
                      最小值: ${data[1]}<br/>
                      Q1: ${data[2]}<br/>
                      中位数: ${data[3]}<br/>
                      Q3: ${data[4]}<br/>
                      最大值: ${data[5]}`;
            }
          },
          grid: {
            left: '10%',
            right: '10%',
            bottom: '15%'
          },
          xAxis: {
            type: 'category',
            data: data.map(d => d.name),
            boundaryGap: true,
            nameGap: 30,
            splitArea: {
              show: false
            },
            splitLine: {
              show: false
            }
          },
          yAxis: {
            type: 'value',
            name: '数值',
            splitArea: {
              show: true
            }
          },
          series: [
            {
              name: 'boxplot',
              type: 'boxplot',
              data: data.map(d => [d.min, d.q1, d.median, d.q3, d.max]),
              itemStyle: {
                color: '#b3d4fc',
                borderColor: '#1890ff'
              }
            },
            {
              name: 'outlier',
              type: 'scatter',
              data: data.flatMap((d, index) => 
                (d.outliers || []).map(outlier => [index, outlier])
              ),
              itemStyle: {
                color: '#ff4d4f'
              }
            }
          ]
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