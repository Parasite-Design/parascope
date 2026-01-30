<!-- eslint-disable vue/multi-word-component-names -->
<template>
  <div class="products-container">
    <div class="page-header">
      <h1>Products Analysis</h1>
    </div>

    <!-- Filters Section - Only include zero sales toggle -->
    <div class="filters-section">
      <div class="filter-group">
        <el-switch
          v-model="includeNoSales"
          @change="fetchProducts"
          active-text="Include Zero Sales"
          inactive-text="Hide Zero Sales"
        />
      </div>
    </div>

    <!-- Sales Overview Cards -->
    <div class="sales-overview">
      <el-card class="overview-card">
        <div class="card-content">
          <div class="card-icon total-sales">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="card-stats">
            <div class="stat-value">{{ formatNumber(totalSales) }}€</div>
            <div class="stat-label">Total Sales</div>
          </div>
        </div>
      </el-card>

      <el-card class="overview-card">
        <div class="card-content">
          <div class="card-icon my-sales">
            <el-icon><User /></el-icon>
          </div>
          <div class="card-stats">
            <div class="stat-value">{{ formatNumber(myTotalSales) }}€</div>
            <div class="stat-label">My Sales</div>
          </div>
        </div>
      </el-card>

      <el-card class="overview-card">
        <div class="card-content">
          <div class="card-icon web-sales">
            <el-icon><Monitor /></el-icon>
          </div>
          <div class="card-stats">
            <div class="stat-value">{{ formatNumber(webTotalSales) }}€</div>
            <div class="stat-label">Web Sales</div>
          </div>
        </div>
      </el-card>

      <el-card class="overview-card">
        <div class="card-content">
          <div class="card-icon products-count">
            <el-icon><Box /></el-icon>
          </div>
          <div class="card-stats">
            <div class="stat-value">{{ products.length }}</div>
            <div class="stat-label">Products</div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- Brand Distribution -->
    <div class="distribution-section">
      <el-card class="distribution-card">
        <template #header>
          <div class="card-header">
            <span>Sales Distribution by Brand</span>
            <el-radio-group v-model="distributionView" size="small">
              <el-radio-button label="total">Total Sales</el-radio-button>
              <el-radio-button label="my">My Sales</el-radio-button>
            </el-radio-group>
          </div>
        </template>

        <div class="distribution-content">
          <div
            v-for="brand in brandDistribution"
            :key="brand.brand_name"
            class="brand-item"
          >
            <div class="brand-header">
              <span class="brand-name">{{ brand.showed_brand_name }}</span>
              <span class="brand-percentage">{{ brand.percentage }}%</span>
            </div>
            <el-progress
              :percentage="brand.percentage"
              :show-text="false"
              :color="getBrandColor(brand.brand_name)"
            />
            <div class="brand-amount">{{ formatNumber(brand.amount) }}€</div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- Products Table -->
    <el-card class="table-card">
      <template #header>
        <div class="table-header">
          <span>Products Details</span>
          <div class="table-actions">
            <el-input
              v-model="searchQuery"
              placeholder="Search products..."
              clearable
              style="width: 250px"
              @clear="handleSearch"
              @keyup.enter="handleSearch"
            >
              <template #suffix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>
        </div>
      </template>

      <el-table
        :data="sortedAndFilteredProducts"
        v-loading="loading"
        style="width: 100%"
        :default-sort="{ prop: 'sales', order: 'descending' }"
        @sort-change="handleSortChange"
        stripe
      >
        <el-table-column
          prop="product_id"
          label="ID"
          sortable="custom"
          width="120"
        />
        <el-table-column
          prop="brand"
          label="Brand"
          sortable="custom"
          width="130"
        >
          <template #default="{ row }">
            <el-tag effect="plain">
              {{ getBrandDisplayName(row.brand) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="name"
          label="Name"
          sortable="custom"
          min-width="180"
        />
        <el-table-column
          prop="price"
          label="Price"
          sortable="custom"
          width="120"
          align="right"
        >
          <template #default="{ row }">
            {{ row.price === "WIP" ? "TBD" : `$${row.price}` }}
          </template>
        </el-table-column>

        <!-- Sales Columns -->
        <el-table-column
          prop="sales"
          label="Units Sold"
          sortable="custom"
          width="120"
          align="right"
        >
          <template #default="{ row }">
            <span class="sales-number">{{ formatNumber(row.sales) }}</span>
          </template>
        </el-table-column>

        <el-table-column
          prop="total"
          label="Total Revenue"
          sortable="custom"
          width="140"
          align="right"
        >
          <template #default="{ row }">
            <span class="revenue">{{ formatNumber(row.total) }}€</span>
          </template>
        </el-table-column>

        <el-table-column
          prop="my_sales"
          label="My Units"
          sortable="custom"
          width="110"
          align="right"
        >
          <template #default="{ row }">
            {{ formatNumber(row.my_sales) }}
          </template>
        </el-table-column>

        <el-table-column
          prop="my_total"
          label="My Revenue"
          sortable="custom"
          width="130"
          align="right"
        >
          <template #default="{ row }">
            <span class="my-revenue">{{ formatNumber(row.my_total) }}€</span>
          </template>
        </el-table-column>

        <el-table-column
          prop="web_sales"
          label="Web Units"
          sortable="custom"
          width="110"
          align="right"
        >
          <template #default="{ row }">
            {{ formatNumber(row.web_sales) }}
          </template>
        </el-table-column>

        <el-table-column
          prop="web_total"
          label="Web Revenue"
          sortable="custom"
          width="130"
          align="right"
        >
          <template #default="{ row }">
            {{ formatNumber(row.web_total) }}€
          </template>
        </el-table-column>

        <el-table-column
          prop="my_web_sales"
          label="My Web Units"
          sortable="custom"
          width="120"
          align="right"
        >
          <template #default="{ row }">
            {{ formatNumber(row.my_web_sales) }}
          </template>
        </el-table-column>

        <el-table-column
          prop="my_web_total"
          label="My Web Revenue"
          sortable="custom"
          width="140"
          align="right"
        >
          <template #default="{ row }">
            {{ formatNumber(row.my_web_total) }}€
          </template>
        </el-table-column>

        <el-table-column
          prop="edi"
          label="EDI"
          sortable="custom"
          width="100"
          align="right"
        >
          <template #default="{ row }">
            {{ formatNumber(row.edi) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import {
  Box,
  Monitor,
  Search,
  TrendCharts,
  User,
} from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { computed, onMounted, ref, watch } from "vue";
import { api } from "../stores/auth";
import { useSettingsStore } from "../stores/settings";

interface Product {
  product_id: string;
  brand: string;
  name: string;
  price: string;
  sales: number;
  total: number;
  web_sales: number;
  web_total: number;
  my_sales: number;
  my_total: number;
  my_web_sales: number;
  my_web_total: number;
  edi: number;
}

interface Brand {
  brand_name: string;
  showed_brand_name: string;
}

interface SortConfig {
  prop: string;
  order: "ascending" | "descending" | null;
}

const settingsStore = useSettingsStore();

const products = ref<Product[]>([]);
const brands = ref<Brand[]>([]);
const loading = ref(false);
const searchQuery = ref("");
const includeNoSales = ref(false);
const distributionView = ref<"total" | "my">("total");
const sortConfig = ref<SortConfig>({ prop: "sales", order: "descending" });

// Get date range from settings
const period1Start = settingsStore.period.period_start;
const period1End = settingsStore.period.period_end;

const period1StartDate = new Date(period1Start);
const period1EndDate = new Date(period1End);

// Computed properties
const filteredProducts = computed(() => {
  if (!searchQuery.value) return products.value;

  const query = searchQuery.value.toLowerCase();
  return products.value.filter(
    (product) =>
      product.product_id.toLowerCase().includes(query) ||
      product.name.toLowerCase().includes(query) ||
      product.brand.toLowerCase().includes(query),
  );
});

const sortedAndFilteredProducts = computed(() => {
  const data = [...filteredProducts.value];

  if (!sortConfig.value.prop || !sortConfig.value.order) {
    return data;
  }

  return data.sort((a, b) => {
    const aVal = a[sortConfig.value.prop as keyof Product];
    const bVal = b[sortConfig.value.prop as keyof Product];

    // Handle string and number comparisons
    if (typeof aVal === "string" && typeof bVal === "string") {
      return sortConfig.value.order === "ascending"
        ? aVal.localeCompare(bVal)
        : bVal.localeCompare(aVal);
    }

    // Handle number comparisons
    const numA =
      typeof aVal === "string" && aVal !== "WIP"
        ? parseFloat(aVal)
        : Number(aVal);
    const numB =
      typeof bVal === "string" && bVal !== "WIP"
        ? parseFloat(bVal)
        : Number(bVal);

    if (sortConfig.value.order === "ascending") {
      return numA - numB;
    } else {
      return numB - numA;
    }
  });
});

const totalSales = computed(() =>
  products.value.reduce((sum, product) => sum + product.total, 0),
);

const myTotalSales = computed(() =>
  products.value.reduce((sum, product) => sum + product.my_total, 0),
);

const webTotalSales = computed(() =>
  products.value.reduce((sum, product) => sum + product.web_total, 0),
);

const brandDistribution = computed(() => {
  const brandMap = new Map();

  // Initialize with all brands
  brands.value.forEach((brand) => {
    brandMap.set(brand.brand_name, {
      brand_name: brand.brand_name,
      showed_brand_name: brand.showed_brand_name,
      amount: 0,
    });
  });

  // Sum up amounts based on current view
  products.value.forEach((product) => {
    const currentAmount =
      distributionView.value === "total" ? product.total : product.my_total;
    if (brandMap.has(product.brand)) {
      brandMap.get(product.brand).amount += currentAmount;
    }
  });

  const totalAmount = Array.from(brandMap.values()).reduce(
    (sum, brand) => sum + brand.amount,
    0,
  );

  // Calculate percentages
  return Array.from(brandMap.values())
    .map((brand) => ({
      ...brand,
      percentage:
        totalAmount > 0 ? Math.round((brand.amount / totalAmount) * 100) : 0,
    }))
    .filter((brand) => brand.amount > 0)
    .sort((a, b) => b.amount - a.amount);
});

// Watchers
watch([includeNoSales], () => {
  fetchProducts();
});

// Methods
const fetchProducts = async () => {
  loading.value = true;
  try {
    const params = new URLSearchParams();

    // Add date range
    params.append("start_date", period1StartDate.toISOString().split("T")[0]);
    params.append("end_date", period1EndDate.toISOString().split("T")[0]);

    // Add brand filter
    if (settingsStore.selectedBrand) {
      params.append("brand", settingsStore.selectedBrand);
    }

    // Add include no sales filter
    params.append("include_no_sales", includeNoSales.value.toString());

    const url = `/api/v1/products/?${params.toString()}`;

    const response = await api.get(url);

    products.value = response.data;
  } catch (error) {
    console.error("Failed to fetch products:", error);
    ElMessage.error("Failed to load products data");
  } finally {
    loading.value = false;
  }
};

const fetchBrands = async () => {
  try {
    const response = await api.get("/api/v1/settings/brand");
    brands.value = response.data;
  } catch (error) {
    console.error("Failed to fetch brands:", error);
  }
};

const getBrandDisplayName = (brandName: string) => {
  const brand = brands.value.find((b) => b.brand_name === brandName);
  return brand ? brand.showed_brand_name : brandName;
};

const getBrandColor = (brandName: string) => {
  const colors = [
    "#409EFF",
    "#67C23A",
    "#E6A23C",
    "#F56C6C",
    "#909399",
    "#B37FEB",
    "#FF85C0",
  ];
  const index = brands.value.findIndex((b) => b.brand_name === brandName);
  return colors[index % colors.length];
};

const handleSortChange = ({
  prop,
  order,
}: {
  prop: string;
  order: "ascending" | "descending" | null;
}) => {
  sortConfig.value = { prop, order };
};

const handleSearch = () => {
  // Search is handled by the computed property, but we can add debouncing here if needed
  console.log("Searching for:", searchQuery.value);
};

const formatNumber = (num: number) => {
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(num);
};

onMounted(() => {
  fetchBrands();
  fetchProducts();
});
</script>

<style scoped>
.products-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.filters-section {
  display: flex;
  gap: 40px;
  margin-bottom: 24px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  align-items: flex-end;
}

.sales-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.overview-card {
  border-radius: 8px;
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.card-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.card-icon {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.card-icon.total-sales {
  background: #ecf5ff;
  color: #409eff;
}

.card-icon.my-sales {
  background: #f0f9eb;
  color: #67c23a;
}

.card-icon.web-sales {
  background: #fdf6ec;
  color: #e6a23c;
}

.card-icon.products-count {
  background: #f4f4f5;
  color: #909399;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.distribution-section {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.distribution-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.brand-item {
  padding: 8px 0;
}

.brand-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.brand-name {
  font-weight: 500;
  color: #303133;
}

.brand-percentage {
  font-weight: 600;
  color: #409eff;
}

.brand-amount {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.table-card {
  border-radius: 8px;
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sales-number {
  font-weight: 600;
  color: #303133;
}

.revenue {
  font-weight: 600;
  color: #67c23a;
}

.my-revenue {
  font-weight: 600;
  color: #409eff;
}

:deep(.el-table .cell) {
  line-height: 1.5;
}

:deep(.el-progress-bar__inner) {
  transition: width 0.6s ease;
}
</style>
