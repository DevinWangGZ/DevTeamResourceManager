<template>
  <div class="workload-chart-container">
    <div ref="chartRef" :style="{ width: width, height: height }"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'

interface Props {
  type: 'line' | 'bar' | 'pie' | 'trend'
  data: any[]
  width?: string
  height?: string
  title?: string
  xAxisData?: string[]
  seriesName?: string
}

const props = withDefaults(defineProps<Props>(), {
  width: '100%',
  height: '400px',
  title: '',
  seriesName: '工作量',
})

const chartRef = ref<HTMLDivElement>()
let chartInstance: echarts.ECharts | null = null

const initChart = () => {
  if (!chartRef.value) return

  chartInstance = echarts.init(chartRef.value)
  updateChart()
}

const updateChart = () => {
  if (!chartInstance) return

  let option: EChartsOption = {}

  switch (props.type) {
    case 'trend':
    case 'line':
      // 趋势图（折线图）
      option = {
        title: {
          text: props.title,
          left: 'center',
        },
        tooltip: {
          trigger: 'axis',
          formatter: (params: any) => {
            const param = Array.isArray(params) ? params[0] : params
            return `${param.name}<br/>${param.seriesName}: ${param.value} 人天`
          },
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true,
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: props.xAxisData || props.data.map((item: any) => {
            // 如果是日期，格式化显示
            if (item.period_start) {
              const date = new Date(item.period_start)
              return `${date.getMonth() + 1}月`
            }
            return item.name || item.label || ''
          }),
        },
        yAxis: {
          type: 'value',
          name: '人天',
        },
        series: [
          {
            name: props.seriesName,
            type: 'line',
            smooth: true,
            data: props.data.map((item: any) => {
              return typeof item === 'number' ? item : (item.value || item.total_man_days || 0)
            }),
            areaStyle: {
              color: {
                type: 'linear',
                x: 0,
                y: 0,
                x2: 0,
                y2: 1,
                colorStops: [
                  { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
                  { offset: 1, color: 'rgba(64, 158, 255, 0.1)' },
                ],
              },
            },
            itemStyle: {
              color: '#409eff',
            },
          },
        ],
      }
      break

    case 'bar':
      // 柱状图
      option = {
        title: {
          text: props.title,
          left: 'center',
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow',
          },
          formatter: (params: any) => {
            const param = Array.isArray(params) ? params[0] : params
            return `${param.name}<br/>${param.seriesName}: ${param.value} 人天`
          },
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true,
        },
        xAxis: {
          type: 'category',
          data: props.xAxisData || props.data.map((item: any) => {
            return item.name || item.label || item.project_name || ''
          }),
          axisLabel: {
            rotate: props.data.length > 10 ? 45 : 0,
          },
        },
        yAxis: {
          type: 'value',
          name: '人天',
        },
        series: [
          {
            name: props.seriesName,
            type: 'bar',
            data: props.data.map((item: any) => {
              return typeof item === 'number' ? item : (item.value || item.total_man_days || 0)
            }),
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#83bff6' },
                { offset: 0.5, color: '#188df0' },
                { offset: 1, color: '#188df0' },
              ]),
            },
          },
        ],
      }
      break

    case 'pie':
      // 饼图
      option = {
        title: {
          text: props.title,
          left: 'center',
        },
        tooltip: {
          trigger: 'item',
          formatter: '{b}: {c} 人天 ({d}%)',
        },
        legend: {
          orient: 'vertical',
          left: 'left',
        },
        series: [
          {
            name: props.seriesName,
            type: 'pie',
            radius: ['40%', '70%'],
            avoidLabelOverlap: false,
            itemStyle: {
              borderRadius: 10,
              borderColor: '#fff',
              borderWidth: 2,
            },
            label: {
              show: true,
              formatter: '{b}: {c} 人天\n({d}%)',
            },
            emphasis: {
              label: {
                show: true,
                fontSize: 16,
                fontWeight: 'bold',
              },
            },
            data: props.data.map((item: any) => {
              return {
                value: typeof item === 'number' ? item : (item.value || item.total_man_days || 0),
                name: item.name || item.label || item.project_name || '',
              }
            }),
          },
        ],
      }
      break
  }

  chartInstance.setOption(option, true)
}

const resizeChart = () => {
  chartInstance?.resize()
}

watch(
  () => [props.data, props.type, props.title],
  () => {
    updateChart()
  },
  { deep: true }
)

onMounted(() => {
  initChart()
  window.addEventListener('resize', resizeChart)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeChart)
  chartInstance?.dispose()
  chartInstance = null
})
</script>

<style scoped>
.workload-chart-container {
  width: 100%;
}
</style>
