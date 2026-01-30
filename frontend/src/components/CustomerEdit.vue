<template>
  <el-dialog
    v-model="visible"
    title="Edit Customer"
    width="600px"
    :before-close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="120px"
      label-position="left"
    >
      <el-form-item label="Customer Code">
        <el-input v-model="customerCode" disabled />
      </el-form-item>

      <el-form-item label="Name">
        <el-input v-model="customerName" disabled />
      </el-form-item>

      <el-form-item label="City">
        <el-input v-model="customerCity" disabled />
      </el-form-item>

      <el-form-item label="Phone">
        <el-input v-model="customerPhone" disabled />
      </el-form-item>

      <el-form-item label="Objective" prop="objective">
        <el-input-number
          v-model="form.objective"
          :min="0"
          :step="1000"
          style="width: 100%"
          placeholder="Sales objective"
        />
      </el-form-item>

      <el-form-item label="Visits Count" prop="visits_count">
        <el-input-number
          v-model="form.visits_count"
          :min="0"
          :step="1"
          style="width: 100%"
          placeholder="Number of visits"
        />
      </el-form-item>

      <el-form-item label="Favorite" prop="favorite">
        <el-switch v-model="form.favorite" />
      </el-form-item>

      <el-form-item label="Notes" prop="note">
        <el-input
          v-model="form.note"
          type="textarea"
          :rows="4"
          placeholder="Enter notes about the customer"
          maxlength="500"
          show-word-limit
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">Cancel</el-button>
      <el-button type="primary" @click="submitForm" :loading="loading">
        Update Customer
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ElMessage, type FormInstance, type FormRules } from "element-plus";
import { reactive, ref, watch } from "vue";
import { api } from "../stores/auth";

interface Customer {
  _id?: string;
  code: string;
  city: string;
  latitude: string;
  longitude: string;
  name: string;
  phone: string;
  period1_total: number;
  period1_count: number;
  period2_total: number;
  objective: number;
  visits_count: number;
  favorite: boolean;
  active: boolean;
  period_progress: number;
  objective_progress: number;
  last_visit: string | null;
  note?: string;
}

interface Props {
  visible: boolean;
  customer?: Customer | null;
}

const props = defineProps<Props>();
const emit = defineEmits(["update:visible", "customer-updated"]);

const formRef = ref<FormInstance>();
const loading = ref(false);
const visible = ref(props.visible);

// Display-only fields (readonly)
const customerCode = ref("");
const customerName = ref("");
const customerCity = ref("");
const customerPhone = ref("");

// Editable fields
const form = reactive({
  objective: 0,
  visits_count: 0,
  favorite: false,
  note: "",
});

const rules: FormRules = {
  objective: [
    {
      type: "number",
      min: 0,
      message: "Objective must be a positive number",
      trigger: "blur",
    },
  ],
  visits_count: [
    {
      type: "number",
      min: 0,
      message: "Visits count must be a positive number",
      trigger: "blur",
    },
  ],
  note: [
    {
      max: 500,
      message: "Notes cannot exceed 500 characters",
      trigger: "blur",
    },
  ],
};

// Initialize form when customer changes
watch(
  () => props.customer,
  (customer) => {
    if (customer) {
      // Set display fields
      customerCode.value = customer.code || "";
      customerName.value = customer.name || "";
      customerCity.value = customer.city || "";
      customerPhone.value = customer.phone || "";

      // Set editable fields
      Object.assign(form, {
        objective: customer.objective || 0,
        visits_count: customer.visits_count || 0,
        favorite: customer.favorite || false,
        note: customer.note || "",
      });
    } else {
      // Reset form
      resetForm();
    }
  },
);

watch(
  () => props.visible,
  (val) => {
    visible.value = val;
  },
);

watch(visible, (val) => {
  emit("update:visible", val);
});

const resetForm = () => {
  customerCode.value = "";
  customerName.value = "";
  customerCity.value = "";
  customerPhone.value = "";

  Object.assign(form, {
    objective: 0,
    visits_count: 0,
    favorite: false,
    note: "",
  });
  formRef.value?.clearValidate();
};

const handleClose = () => {
  visible.value = false;
  resetForm();
};

const submitForm = async () => {
  if (!formRef.value) return;

  const valid = await formRef.value.validate().catch(() => false);
  if (!valid) return;

  loading.value = true;
  try {
    if (props.customer?._id) {
      // Only send allowed fields to the API
      const updateData = {
        objective: form.objective,
        visits_count: form.visits_count,
        favorite: form.favorite,
        note: form.note,
      };

      await api.put(`/api/v1/customers/${props.customer._id}`, updateData);
      ElMessage.success("Customer updated successfully");

      emit("customer-updated");
      handleClose();
    } else {
      ElMessage.error("No customer selected for editing");
    }
  } catch (error: any) {
    console.error("Failed to update customer:", error);
    const errorMessage =
      error.response?.data?.message || "Failed to update customer";
    ElMessage.error(errorMessage);
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.el-input-number {
  width: 100%;
}

/* Style for disabled fields to make them look read-only but clean */
:deep(.el-input.is-disabled .el-input__wrapper) {
  background-color: #f5f7fa;
  box-shadow: 0 0 0 1px #e4e7ed inset;
}
</style>
