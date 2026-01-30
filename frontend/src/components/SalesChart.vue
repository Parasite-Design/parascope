<template>
  <div ref="chartRef" style="height: 100%; width: 100%"></div>
</template>

<script setup lang="ts">
import type { ECharts, EChartsOption } from "echarts";
import * as echarts from "echarts";
import { onMounted, onUnmounted, ref, watch } from "vue";

interface PeriodSum {
  start: string;
  end: string;
  total: number;
  count: number;
}

const props = defineProps<{
  periodSums: PeriodSum[];
  loading?: boolean;
}>();

const chartRef = ref<HTMLDivElement>();
let chart: ECharts | null = null;

// Initialize chart
const initChart = () => {
  if (!chartRef.value) return;

  chart = echarts.init(chartRef.value);
  renderChart();

  // Add resize listener
  window.addEventListener("resize", handleResize);
};

const handleResize = () => {
  chart?.resize();
};

const renderChart = () => {
  if (!chart || !props.periodSums?.length) {
    renderEmptyChart();
    return;
  }

  const option: EChartsOption = {
    tooltip: {
      trigger: "axis",
      axisPointer: {
        type: "shadow",
      },
      formatter: (params: any) => {
        const data = params[0];
        const period = props.periodSums[data.dataIndex];
        return `
          <strong>${formatPeriod(period.start)} - ${formatPeriod(period.end)}</strong><br/>
          Sales: ${formatCurrency(period.total)}<br/>
          Units: ${period.count}
        `;
      },
    },
    legend: {
      data: ["Sales Amount", "Units Sold"],
    },
    grid: {
      left: "3%",
      right: "4%",
      bottom: "3%",
      containLabel: true,
    },
    xAxis: {
      type: "category",
      data: props.periodSums.map((period, index) => `Period ${index + 1}`),
      axisLabel: {
        formatter: (value: string, index: number) => {
          const period = props.periodSums[index];
          if (!period) return value;
          return formatShortDate(period.start);
        },
      },
    },
    yAxis: [
      {
        type: "value",
        name: "Sales Amount",
        axisLabel: {
          formatter: (value: number) => {
            if (value >= 1000) return `€${(value / 1000).toFixed(0)}K`;
            return `€${value}`;
          },
        },
      },
      {
        type: "value",
        name: "Units Sold",
        position: "right",
        axisLabel: {
          formatter: "{value}",
        },
      },
    ],
    series: [
      {
        name: "Sales Amount",
        type: "bar",
        yAxisIndex: 0,
        data: props.periodSums.map((period) => period.total),
        itemStyle: {
          color: "#5470c6",
        },
        emphasis: {
          focus: "series",
        },
      },
      {
        name: "Units Sold",
        type: "line",
        yAxisIndex: 1,
        data: props.periodSums.map((period) => period.count),
        symbol: "circle",
        symbolSize: 8,
        lineStyle: {
          color: "#91cc75",
        },
        itemStyle: {
          color: "#91cc75",
        },
        emphasis: {
          focus: "series",
        },
      },
    ],
    dataZoom: [
      {
        type: "inside",
        start: 0,
        end: 100,
      },
      {
        show: true,
        type: "slider",
        top: "90%",
        start: 0,
        end: 100,
      },
    ],
  };

  chart.setOption(option);
};

const renderEmptyChart = () => {
  if (!chart) return;

  chart.setOption({
    title: {
      text: "No sales data available",
      left: "center",
      top: "center",
      textStyle: {
        color: "#999",
        fontSize: 14,
        fontWeight: "normal",
      },
    },
    xAxis: {
      show: false,
    },
    yAxis: {
      show: false,
    },
    series: [],
  });
};

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat("fr-CH", {
    style: "currency",
    currency: "EUR",
  }).format(amount);
};

const formatPeriod = (dateString: string) => {
  return new Date(dateString).toLocaleDateString("fr-CH", {
    month: "short",
    year: "numeric",
  });
};

const formatShortDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString("fr-CH", {
    month: "short",
  });
};

// Watch for data changes
watch(
  () => props.periodSums,
  () => {
    renderChart();
  },
  { deep: true },
);

watch(
  () => props.loading,
  (loading) => {
    if (loading) {
      chart?.showLoading();
    } else {
      chart?.hideLoading();
    }
  },
);

onMounted(() => {
  initChart();
});

onUnmounted(() => {
  if (chart) {
    chart.dispose();
    chart = null;
  }
  window.removeEventListener("resize", handleResize);
});
</script>
