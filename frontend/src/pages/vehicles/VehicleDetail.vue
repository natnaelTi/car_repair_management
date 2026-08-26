<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  LucideChevronRight,
  LucideEdit,
  LucideMoreVertical,
  LucideMoreHorizontal,
  LucideGauge,
  LucideCar,
  LucideUser,
  LucideUsers,
  LucideMapPin,
  LucideAlertTriangle,
  LucideBell,
  LucidePlus,
  LucideClipboardList,
  LucideWrench,
  LucideFileText,
  LucidePaperclip,
  LucideTrash2,
  LucideArchive,
  LucideLoader2,
  LucideCalendar,
  LucideDollarSign,
  LucideCpu,
  LucideHistory,
  LucideClipboardCheck,
  LucideShield,
  LucideX,
  LucideLogOut,
  LucideFuel,
} from 'lucide-vue-next'
import { apiCall, apiGet } from '@/api'
import { Card, Button, Badge, Skeleton, Tabs, LinkField } from '@/components/ui'
import SpecsTab from './tabs/SpecsTab.vue'
import FinancialsTab from './tabs/FinancialsTab.vue'
import SensorDataTab from './tabs/SensorDataTab.vue'
import ServiceHistoryTab from './tabs/ServiceHistoryTab.vue'
import InspectionHistoryTab from './tabs/InspectionHistoryTab.vue'
import WorkOrdersTab from './tabs/WorkOrdersTab.vue'
import ServiceRemindersTab from './tabs/ServiceRemindersTab.vue'
import IssuesTab from './tabs/IssuesTab.vue'
import FuelQuotaTab from './tabs/FuelQuotaTab.vue'
import AttachmentsTab from './tabs/AttachmentsTab.vue'

const props = defineProps<{ id: string }>()
const { t } = useI18n()
const router = useRouter()

const isLoading = ref(true)
const dashboardData = ref<any>(null)
const activeTab = ref('overview')
const showActionsMenu = ref(false)
const error = ref('')

const tabs = computed(() => [
  { id: 'overview', label: t('vehicles.overview'), icon: LucideCar },
  { id: 'specs', label: t('vehicles.specs'), icon: LucideClipboardList },
  { id: 'financial', label: t('vehicles.financials'), icon: LucideDollarSign },
  { id: 'sensor-data', label: t('vehicles.sensor_data'), icon: LucideCpu },
  { id: 'services', label: t('vehicles.service_history'), icon: LucideHistory },
  { id: 'inspections', label: t('vehicles.inspection_history'), icon: LucideClipboardCheck },
  { id: 'work-orders', label: t('vehicles.work_orders'), icon: LucideWrench },
  { id: 'reminders', label: t('vehicles.service_reminders'), icon: LucideBell },
  { id: 'issues', label: t('vehicles.issues_tab'), icon: LucideAlertTriangle },
  { id: 'fuel', label: t('fuel.title'), icon: LucideFuel },
  { id: 'attachments', label: t('vehicles.attachments'), icon: LucidePaperclip },
])

const vehicle = computed(() => dashboardData.value?.vehicle)
const custodian = computed(() => dashboardData.value?.custodian)
const drivers = computed(() => dashboardData.value?.drivers || [])
const driverHistory = computed(() => dashboardData.value?.driver_history || [])
const costOfOwnership = computed(() => dashboardData.value?.cost_of_ownership || [])
const serviceReminders = computed(() => dashboardData.value?.service_reminders || { overdue: 0, due_soon: 0, snoozed: 0, items: [] })
const openIssues = computed(() => dashboardData.value?.open_issues || { open: 0, overdue: 0, items: [] })
const telemetry = computed(() => dashboardData.value?.telemetry || null)

// Custodian / Driver management
const showAddDriver = ref(false)
const isSavingAssignment = ref(false)

async function setCustodian(employeeId: string) {
  isSavingAssignment.value = true
  try {
    const res = await apiCall<any>('car_repair_management.api.vehicle.set_custodian', {
      vehicle_name: props.id,
      employee: employeeId,
    })
    if (dashboardData.value) {
      dashboardData.value.custodian = res.custodian
      dashboardData.value.drivers = res.drivers
    }
  } catch (e: any) {
    alert(e.message || 'Failed to set custodian')
  } finally {
    isSavingAssignment.value = false
  }
}

async function addDriver(employeeId: string) {
  isSavingAssignment.value = true
  try {
    const res = await apiCall<any>('car_repair_management.api.vehicle.add_driver', {
      vehicle_name: props.id,
      employee: employeeId,
    })
    if (dashboardData.value) {
      dashboardData.value.custodian = res.custodian
      dashboardData.value.drivers = res.drivers
    }
    showAddDriver.value = false
  } catch (e: any) {
    alert(e.message || 'Failed to add driver')
  } finally {
    isSavingAssignment.value = false
  }
}

async function removeDriver(driverRowName: string) {
  if (!confirm('Remove this driver?')) return
  isSavingAssignment.value = true
  try {
    const res = await apiCall<any>('car_repair_management.api.vehicle.remove_driver', {
      vehicle_name: props.id,
      driver_row_name: driverRowName,
    })
    if (dashboardData.value) {
      dashboardData.value.custodian = res.custodian
      dashboardData.value.drivers = res.drivers
    }
  } catch (e: any) {
    alert(e.message || 'Failed to remove driver')
  } finally {
    isSavingAssignment.value = false
  }
}

async function requestDriverRemoval(driverRowName: string) {
  isSavingAssignment.value = true
  try {
    const res = await apiCall<any>('car_repair_management.api.vehicle.request_driver_removal', {
      vehicle_name: props.id,
      driver_row_name: driverRowName,
    })
    if (dashboardData.value) {
      dashboardData.value.custodian = res.custodian
      dashboardData.value.drivers = res.drivers
    }
  } catch (e: any) {
    alert(e.message || 'Failed to request removal')
  } finally {
    isSavingAssignment.value = false
  }
}

const statusColors: Record<string, string> = {
  'Active': 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  'In Maintenance': 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  'Undergoing Tests': 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  'Delivered to Customer': 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
  'Scrapped': 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400',
}

async function loadDashboard() {
  isLoading.value = true
  error.value = ''
  try {
    const result = await apiCall<any>('car_repair_management.api.vehicle.get_vehicle_dashboard', {
      vehicle_name: props.id,
    })
    dashboardData.value = result
  } catch (e: any) {
    console.error('Failed to load vehicle dashboard', e)
    error.value = e.message || t('common.failed_to_load')
    // Fallback to basic API
    try {
      const basicData = await apiGet('Vehicle', props.id)
      dashboardData.value = { vehicle: basicData, custodian: null, cost_of_ownership: [], service_reminders: {}, open_issues: {} }
    } catch (e2) {
      error.value = t('common.failed_to_load')
    }
  } finally {
    isLoading.value = false
  }
}

async function handleScrapVehicle() {
  if (!confirm(t('vehicles.confirm_scrap'))) return
  try {
    await apiCall('car_repair_management.api.vehicle.scrap_vehicle', { vehicle_name: props.id })
    loadDashboard()
  } catch (e: any) {
    alert(e.message || t('common.failed_to_load'))
  }
  showActionsMenu.value = false
}

async function handleDeleteVehicle() {
  if (!confirm(t('vehicles.confirm_delete_vehicle'))) return
  try {
    await apiCall('car_repair_management.api.vehicle.delete_vehicle', { vehicle_name: props.id })
    router.push('/vehicles')
  } catch (e: any) {
    alert(e.message || t('common.failed_to_load'))
  }
  showActionsMenu.value = false
}

function formatMileage(value: number | null | undefined): string {
  if (!value) return '0 km'
  return `${value.toLocaleString()} km`
}

function formatTelemetryValue(value: any, unit = ''): string {
  if (value === null || value === undefined || value === '') return '-'
  const numeric = Number(value)
  if (!Number.isNaN(numeric)) return `${numeric.toLocaleString()}${unit}`
  return `${value}${unit}`
}

function formatDateTime(value: string | null | undefined): string {
  if (!value) return '-'
  return new Date(value).toLocaleString()
}

onMounted(loadDashboard)
</script>

<template>
  <div class="space-y-6">
    <!-- Breadcrumb Navigation -->
    <nav class="flex items-center gap-2 text-sm" style="color: var(--text-muted);">
      <RouterLink to="/vehicles" class="hover:underline" style="color: var(--text-muted);">{{ $t('nav.vehicles') }}</RouterLink>
      <LucideChevronRight class="size-4" />
      <span style="color: var(--text-primary);">{{ vehicle?.license_plate || props.id }}</span>
    </nav>

    <!-- Loading State -->
    <template v-if="isLoading">
      <Card>
        <div class="flex items-center gap-6">
          <Skeleton width="120px" height="120px" class="rounded-lg" />
          <div class="flex-1 space-y-3">
            <Skeleton width="300px" height="24px" />
            <Skeleton width="400px" height="16px" />
            <Skeleton width="350px" height="16px" />
          </div>
        </div>
      </Card>
    </template>

    <!-- Error State -->
    <Card v-else-if="error && !vehicle" class="text-center py-12">
      <LucideAlertTriangle class="size-12 mx-auto mb-4" style="color: var(--text-muted);" />
      <p style="color: var(--text-primary);">{{ error }}</p>
      <Button variant="outline" class="mt-4" @click="router.push('/vehicles')">{{ $t('vehicles.back_to_vehicles') }}</Button>
    </Card>

    <!-- Vehicle Header -->
    <Card v-else-if="vehicle" class="relative">
      <div class="flex flex-col lg:flex-row lg:items-center gap-6">
        <!-- Vehicle Image -->
        <div class="flex-shrink-0">
          <div 
            class="w-32 h-32 rounded-lg flex items-center justify-center overflow-hidden"
            style="background-color: var(--bg-tertiary);"
          >
            <img 
              v-if="vehicle.image" 
              :src="vehicle.image" 
              :alt="vehicle.license_plate"
              class="w-full h-full object-cover"
            />
            <LucideCar v-else class="size-16" style="color: var(--text-muted);" />
          </div>
        </div>

        <!-- Vehicle Info -->
        <div class="flex-1 min-w-0">
          <!-- Line 1: Plate Number + Model/Year -->
          <h1 class="text-2xl font-semibold" style="color: var(--text-primary);">
            {{ vehicle.license_plate }}
            <span class="text-lg font-normal" style="color: var(--text-muted);">
              {{ [vehicle.model, vehicle.year].filter(Boolean).join(', ') }}
            </span>
          </h1>

          <!-- Line 2: Type, Brand, Model, Year, VIN -->
          <p class="mt-1 text-sm" style="color: var(--text-secondary);">
            {{ [vehicle.vehicle_type, vehicle.make, vehicle.model, vehicle.year, vehicle.chassis_no].filter(Boolean).join(' • ') }}
          </p>

          <!-- Line 3: Mileage, Status, Custodian -->
          <div class="flex flex-wrap items-center gap-4 mt-3">
            <!-- Mileage -->
            <div class="flex items-center gap-1.5">
              <LucideGauge class="size-4" style="color: var(--text-muted);" />
              <span class="text-sm font-medium" style="color: var(--text-primary);">
                {{ formatMileage(vehicle.last_odometer) }}
              </span>
            </div>

            <!-- Status Badge -->
            <span 
              :class="['px-2.5 py-1 rounded-full text-xs font-medium', statusColors[vehicle.status] || statusColors['Active']]"
            >
              {{ vehicle.status || 'Active' }}
            </span>

            <!-- Custodian -->
            <div v-if="custodian" class="flex items-center gap-2">
              <div class="w-6 h-6 rounded-full overflow-hidden" style="background-color: var(--bg-tertiary);">
                <img 
                  v-if="custodian.image" 
                  :src="custodian.image" 
                  :alt="custodian.employee_name"
                  class="w-full h-full object-cover"
                />
                <LucideUser v-else class="w-full h-full p-1" style="color: var(--text-muted);" />
              </div>
              <span class="text-sm" style="color: var(--text-secondary);">{{ custodian.employee_name }}</span>
            </div>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex items-center gap-2 lg:self-start">
          <!-- Actions Dropdown -->
          <div class="relative">
            <Button 
              variant="outline" 
              size="sm" 
              @click="showActionsMenu = !showActionsMenu"
            >
              <LucideMoreHorizontal v-if="showActionsMenu" class="size-4" />
              <LucideMoreVertical v-else class="size-4" />
            </Button>
            
            <!-- Dropdown Menu -->
            <div 
              v-if="showActionsMenu"
              class="absolute right-0 mt-2 w-48 rounded-lg border shadow-lg z-50"
              style="background-color: var(--bg-elevated); border-color: var(--border-color);"
            >
              <button
                class="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-left hover:opacity-80 transition-colors"
                style="color: var(--text-primary);"
                @click="handleScrapVehicle"
              >
                <LucideArchive class="size-4" />
                {{ $t('vehicles.scrap_vehicle') }}
              </button>
              <button
                class="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-left hover:opacity-80 transition-colors text-red-500"
                @click="handleDeleteVehicle"
              >
                <LucideTrash2 class="size-4" />
                {{ $t('common.delete') }}
              </button>
            </div>
          </div>

          <!-- Edit Button -->
          <RouterLink :to="`/vehicles/${vehicle.name}/edit`">
            <Button variant="primary">
              <LucideEdit class="size-4" />
              {{ $t('common.edit') }}
            </Button>
          </RouterLink>
        </div>
      </div>

      <!-- Click outside to close menu -->
      <div 
        v-if="showActionsMenu" 
        class="fixed inset-0 z-40" 
        @click="showActionsMenu = false"
      />
    </Card>

    <!-- Tabs -->
    <div v-if="vehicle" class="border-b overflow-x-auto" style="border-color: var(--border-color);">
      <div class="flex gap-1 min-w-max">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          :class="[
            'flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap',
            activeTab === tab.id 
              ? 'border-current' 
              : 'border-transparent hover:opacity-70'
          ]"
          :style="{
            color: activeTab === tab.id ? 'var(--text-primary)' : 'var(--text-muted)',
            borderColor: activeTab === tab.id ? 'var(--accent)' : 'transparent',
          }"
        >
          <component :is="tab.icon" class="size-4" />
          {{ tab.label }}
        </button>
      </div>
    </div>

    <!-- Tab Content: Overview -->
    <template v-if="vehicle && activeTab === 'overview'">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Left Column -->
        <div class="lg:col-span-2 space-y-6">
          <!-- Identifying Information -->
          <Card>
            <h3 class="text-lg font-semibold mb-4" style="color: var(--text-primary);">{{ $t('vehicles.vehicle_information') }}</h3>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <p class="text-xs uppercase tracking-wide" style="color: var(--text-muted);">{{ $t('vehicles.license_plate') }}</p>
                <p class="text-sm font-medium mt-1" style="color: var(--text-primary);">{{ vehicle.license_plate || '-' }}</p>
              </div>
              <div>
                <p class="text-xs uppercase tracking-wide" style="color: var(--text-muted);">{{ $t('vehicles.chassis_vin') }}</p>
                <p class="text-sm font-medium mt-1" style="color: var(--text-primary);">{{ vehicle.chassis_no || '-' }}</p>
              </div>
              <div>
                <p class="text-xs uppercase tracking-wide" style="color: var(--text-muted);">{{ $t('vehicles.make') }}</p>
                <p class="text-sm font-medium mt-1" style="color: var(--text-primary);">{{ vehicle.make || '-' }}</p>
              </div>
              <div>
                <p class="text-xs uppercase tracking-wide" style="color: var(--text-muted);">{{ $t('vehicles.model') }}</p>
                <p class="text-sm font-medium mt-1" style="color: var(--text-primary);">{{ vehicle.model || '-' }}</p>
              </div>
              <div>
                <p class="text-xs uppercase tracking-wide" style="color: var(--text-muted);">{{ $t('vehicles.year') }}</p>
                <p class="text-sm font-medium mt-1" style="color: var(--text-primary);">{{ vehicle.year || '-' }}</p>
              </div>
              <div>
                <p class="text-xs uppercase tracking-wide" style="color: var(--text-muted);">{{ $t('vehicles.variant') }}</p>
                <p class="text-sm font-medium mt-1" style="color: var(--text-primary);">{{ vehicle.variant || '-' }}</p>
              </div>
              <div>
                <p class="text-xs uppercase tracking-wide" style="color: var(--text-muted);">{{ $t('vehicles.color') }}</p>
                <p class="text-sm font-medium mt-1" style="color: var(--text-primary);">{{ vehicle.color || '-' }}</p>
              </div>
              <div>
                <p class="text-xs uppercase tracking-wide" style="color: var(--text-muted);">{{ $t('vehicles.transmission') }}</p>
                <p class="text-sm font-medium mt-1" style="color: var(--text-primary);">{{ vehicle.transmission || '-' }}</p>
              </div>
              <div>
                <p class="text-xs uppercase tracking-wide" style="color: var(--text-muted);">{{ $t('vehicles.fuel_type') }}</p>
                <p class="text-sm font-medium mt-1" style="color: var(--text-primary);">{{ vehicle.fuel_type || '-' }}</p>
              </div>
              <div>
                <p class="text-xs uppercase tracking-wide" style="color: var(--text-muted);">{{ $t('vehicles.current_odometer') }}</p>
                <p class="text-sm font-medium mt-1" style="color: var(--text-primary);">{{ formatMileage(vehicle.last_odometer) }}</p>
              </div>
            </div>
          </Card>

          <!-- Location Map Placeholder -->
          <Card>
            <h3 class="text-lg font-semibold mb-4" style="color: var(--text-primary);">
              <LucideMapPin class="inline size-5 mr-2" />
              {{ $t('vehicles.last_known_location') }}
            </h3>
            <div 
              class="h-48 rounded-lg flex items-center justify-center"
              style="background-color: var(--bg-tertiary);"
            >
              <div class="text-center">
                <LucideMapPin class="size-8 mx-auto mb-2" style="color: var(--text-muted);" />
                <p class="text-sm" style="color: var(--text-muted);">
                  {{ vehicle.location || $t('vehicles.no_location_data') }}
                </p>
              </div>
            </div>
          </Card>

          <!-- Live Telematics -->
          <Card v-if="telemetry?.device_id || telemetry?.last_sync">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg font-semibold" style="color: var(--text-primary);">
                <LucideCpu class="inline size-5 mr-2" />
                Live Telematics
              </h3>
              <Badge :variant="telemetry?.sensor_health === 'Connected' ? 'success' : 'default'" size="sm">
                {{ telemetry?.sensor_health || 'Not Linked' }}
              </Badge>
            </div>
            <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div>
                <p class="text-xs uppercase tracking-wide" style="color: var(--text-muted);">Device IMEI</p>
                <p class="text-sm font-medium mt-1" style="color: var(--text-primary);">{{ telemetry?.device_id || '-' }}</p>
              </div>
              <div>
                <p class="text-xs uppercase tracking-wide" style="color: var(--text-muted);">Engine</p>
                <p class="text-sm font-medium mt-1" style="color: var(--text-primary);">{{ telemetry?.engine_state || '-' }}</p>
              </div>
              <div>
                <p class="text-xs uppercase tracking-wide" style="color: var(--text-muted);">Tracker Status</p>
                <p class="text-sm font-medium mt-1" style="color: var(--text-primary);">{{ telemetry?.tracker_status || '-' }}</p>
              </div>
              <div>
                <p class="text-xs uppercase tracking-wide" style="color: var(--text-muted);">Speed</p>
                <p class="text-sm font-medium mt-1" style="color: var(--text-primary);">{{ formatTelemetryValue(telemetry?.speed, ' km/h') }}</p>
              </div>
              <div>
                <p class="text-xs uppercase tracking-wide" style="color: var(--text-muted);">Fuel</p>
                <p class="text-sm font-medium mt-1" style="color: var(--text-primary);">
                  {{ formatTelemetryValue(telemetry?.fuel_level, '%') }}
                  <span v-if="telemetry?.fuel_volume_ml" style="color: var(--text-muted);">
                    / {{ formatTelemetryValue(Number(telemetry.fuel_volume_ml) / 1000, ' L') }}
                  </span>
                </p>
              </div>
              <div>
                <p class="text-xs uppercase tracking-wide" style="color: var(--text-muted);">Last Sync</p>
                <p class="text-sm font-medium mt-1" style="color: var(--text-primary);">{{ formatDateTime(telemetry?.last_sync) }}</p>
              </div>
            </div>
          </Card>
        </div>

        <!-- Right Column -->
        <div class="space-y-6">
          <!-- Custodian & Drivers -->
          <Card>
            <div class="flex items-center justify-between mb-4">
              <div class="flex items-center gap-2">
                <LucideUsers class="size-4" style="color: var(--text-muted);" />
                <h3 class="text-lg font-semibold" style="color: var(--text-primary);">Custodian & Drivers</h3>
              </div>
            </div>

            <!-- Custodian -->
            <div class="mb-4 pb-4 border-b" style="border-color: var(--border-subtle);">
              <div class="flex items-center gap-2 mb-2">
                <LucideShield class="size-3.5" style="color: var(--text-muted);" />
                <p class="text-xs font-medium uppercase tracking-wide" style="color: var(--text-muted);">Custodian</p>
              </div>
              <LinkField
                :modelValue="custodian?.name || ''"
                @update:modelValue="setCustodian"
                doctype="Employee"
                placeholder="Assign custodian..."
                titleField="employee_name"
                :disabled="isSavingAssignment"
              />
              <div v-if="custodian" class="flex items-center gap-3 mt-2 p-2 rounded-lg" style="background-color: var(--bg-tertiary);">
                <div class="w-8 h-8 rounded-full overflow-hidden flex-shrink-0" style="background-color: var(--bg-elevated);">
                  <img v-if="custodian.image" :src="custodian.image" :alt="custodian.employee_name" class="w-full h-full object-cover" />
                  <LucideUser v-else class="w-full h-full p-1.5" style="color: var(--text-muted);" />
                </div>
                <div class="min-w-0">
                  <p class="text-sm font-medium truncate" style="color: var(--text-primary);">{{ custodian.employee_name }}</p>
                  <p v-if="custodian.designation" class="text-xs truncate" style="color: var(--text-muted);">{{ custodian.designation }}</p>
                </div>
              </div>
            </div>

            <!-- Drivers -->
            <div>
              <div class="flex items-center justify-between mb-2">
                <div class="flex items-center gap-2">
                  <LucideCar class="size-3.5" style="color: var(--text-muted);" />
                  <p class="text-xs font-medium uppercase tracking-wide" style="color: var(--text-muted);">Drivers</p>
                </div>
                <Button
                  v-if="!showAddDriver"
                  variant="outline"
                  size="sm"
                  @click="showAddDriver = true"
                  :disabled="isSavingAssignment"
                >
                  <LucidePlus class="size-3.5" />
                  Add
                </Button>
              </div>

              <!-- Add Driver Form -->
              <div v-if="showAddDriver" class="mb-3 p-3 rounded-lg border" style="background-color: var(--bg-tertiary); border-color: var(--border-subtle);">
                <p class="text-xs font-medium mb-2" style="color: var(--text-muted);">Select employee to add as driver</p>
                <LinkField
                  modelValue=""
                  @update:modelValue="addDriver"
                  doctype="Employee"
                  placeholder="Search employee..."
                  titleField="employee_name"
                  :disabled="isSavingAssignment"
                />
                <button
                  class="mt-2 text-xs hover:underline"
                  style="color: var(--text-muted);"
                  @click="showAddDriver = false"
                >
                  Cancel
                </button>
              </div>

              <!-- Driver List -->
              <div v-if="drivers.length" class="space-y-2">
                <div
                  v-for="driver in drivers"
                  :key="driver.name"
                  class="flex items-center justify-between p-2 rounded-lg"
                  style="background-color: var(--bg-tertiary);"
                >
                  <div class="flex items-center gap-3 min-w-0">
                    <div class="w-8 h-8 rounded-full overflow-hidden flex-shrink-0" style="background-color: var(--bg-elevated);">
                      <img v-if="driver.image" :src="driver.image" :alt="driver.employee_name" class="w-full h-full object-cover" />
                      <LucideUser v-else class="w-full h-full p-1.5" style="color: var(--text-muted);" />
                    </div>
                    <div class="min-w-0">
                      <p class="text-sm font-medium truncate" style="color: var(--text-primary);">{{ driver.employee_name }}</p>
                      <div class="flex items-center gap-2">
                        <span v-if="driver.designation" class="text-xs truncate" style="color: var(--text-muted);">{{ driver.designation }}</span>
                        <Badge v-if="driver.status === 'Removal Requested'" variant="warning" size="sm">Removal Requested</Badge>
                      </div>
                    </div>
                  </div>
                  <div class="flex items-center gap-1 flex-shrink-0">
                    <button
                      class="p-1.5 rounded-lg transition-colors hover:opacity-80"
                      style="color: var(--text-muted);"
                      title="Request removal"
                      :disabled="isSavingAssignment || driver.status === 'Removal Requested'"
                      @click="requestDriverRemoval(driver.name)"
                    >
                      <LucideLogOut class="size-3.5" />
                    </button>
                    <button
                      class="p-1.5 rounded-lg transition-colors hover:opacity-80"
                      style="color: #ef4444;"
                      title="Remove driver"
                      :disabled="isSavingAssignment"
                      @click="removeDriver(driver.name)"
                    >
                      <LucideX class="size-3.5" />
                    </button>
                  </div>
                </div>
              </div>
              <p v-else class="text-sm text-center py-4" style="color: var(--text-muted);">No drivers assigned</p>
            </div>

            <!-- Driver History -->
            <div v-if="driverHistory.length" class="mt-4 pt-4 border-t" style="border-color: var(--border-subtle);">
              <div class="flex items-center gap-2 mb-2">
                <LucideHistory class="size-3.5" style="color: var(--text-muted);" />
                <p class="text-xs font-medium uppercase tracking-wide" style="color: var(--text-muted);">Previous Drivers</p>
              </div>
              <div class="space-y-2">
                <div
                  v-for="driver in driverHistory"
                  :key="driver.name"
                  class="flex items-center justify-between p-2 rounded-lg"
                  style="background-color: var(--bg-tertiary); opacity: 0.7;"
                >
                  <div class="flex items-center gap-3 min-w-0">
                    <div class="w-7 h-7 rounded-full overflow-hidden flex-shrink-0" style="background-color: var(--bg-elevated);">
                      <img v-if="driver.image" :src="driver.image" :alt="driver.employee_name" class="w-full h-full object-cover" />
                      <LucideUser v-else class="w-full h-full p-1.5" style="color: var(--text-muted);" />
                    </div>
                    <div class="min-w-0">
                      <p class="text-sm truncate" style="color: var(--text-primary);">{{ driver.employee_name }}</p>
                      <p class="text-xs" style="color: var(--text-muted);">
                        {{ driver.assigned_date || '' }}{{ driver.ended_date ? ` → ${driver.ended_date}` : '' }}
                      </p>
                    </div>
                  </div>
                  <Badge variant="default" size="sm">Removed</Badge>
                </div>
              </div>
            </div>
          </Card>

          <!-- Cost of Ownership Chart -->
          <Card>
            <h3 class="text-lg font-semibold mb-4" style="color: var(--text-primary);">{{ $t('vehicles.cost_of_ownership') }}</h3>
            <div class="space-y-3">
              <div v-for="month in costOfOwnership" :key="month.month" class="space-y-1">
                <div class="flex justify-between text-xs">
                  <span style="color: var(--text-muted);">{{ month.month }}</span>
                  <span style="color: var(--text-primary);">ETB {{ (month.fuel + month.maintenance + month.repair).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</span>
                </div>
                <div class="flex h-4 rounded overflow-hidden" style="background-color: var(--bg-tertiary);">
                  <div 
                    class="bg-blue-500" 
                    :style="{ width: `${(month.fuel / (month.fuel + month.maintenance + month.repair || 1)) * 100}%` }"
                    :title="`Fuel: ${month.fuel}`"
                  />
                  <div 
                    class="bg-amber-500" 
                    :style="{ width: `${(month.maintenance / (month.fuel + month.maintenance + month.repair || 1)) * 100}%` }"
                    :title="`Maintenance: ${month.maintenance}`"
                  />
                  <div 
                    class="bg-red-500" 
                    :style="{ width: `${(month.repair / (month.fuel + month.maintenance + month.repair || 1)) * 100}%` }"
                    :title="`Repair: ${month.repair}`"
                  />
                </div>
              </div>
              <div class="flex items-center justify-center gap-4 pt-2 text-xs">
                <span class="flex items-center gap-1">
                  <span class="w-3 h-3 rounded bg-blue-500"></span> {{ $t('vehicles.fuel_legend') }}
                </span>
                <span class="flex items-center gap-1">
                  <span class="w-3 h-3 rounded bg-amber-500"></span> {{ $t('vehicles.maintenance_legend') }}
                </span>
                <span class="flex items-center gap-1">
                  <span class="w-3 h-3 rounded bg-red-500"></span> {{ $t('vehicles.repair_legend') }}
                </span>
              </div>
            </div>
            <div v-if="costOfOwnership.length === 0" class="py-8 text-center">
              <p class="text-sm" style="color: var(--text-muted);">{{ $t('vehicles.no_cost_data') }}</p>
            </div>
          </Card>

          <!-- Service Reminders -->
          <Card>
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg font-semibold" style="color: var(--text-primary);">{{ $t('vehicles.service_reminders') }}</h3>
              <Button variant="outline" size="sm">
                <LucidePlus class="size-4" />
                {{ $t('common.add') }}
              </Button>
            </div>
            
            <!-- Counts -->
            <div class="grid grid-cols-3 gap-2 mb-4">
              <div class="text-center p-3 rounded-lg" style="background-color: var(--bg-tertiary);">
                <p class="text-2xl font-bold text-red-500">{{ serviceReminders.overdue }}</p>
                <p class="text-xs" style="color: var(--text-muted);">{{ $t('vehicles.overdue_label') }}</p>
              </div>
              <div class="text-center p-3 rounded-lg" style="background-color: var(--bg-tertiary);">
                <p class="text-2xl font-bold text-amber-500">{{ serviceReminders.due_soon }}</p>
                <p class="text-xs" style="color: var(--text-muted);">{{ $t('vehicles.due_soon') }}</p>
              </div>
              <div class="text-center p-3 rounded-lg" style="background-color: var(--bg-tertiary);">
                <p class="text-2xl font-bold" style="color: var(--text-muted);">{{ serviceReminders.snoozed }}</p>
                <p class="text-xs" style="color: var(--text-muted);">{{ $t('vehicles.snoozed') }}</p>
              </div>
            </div>

            <!-- List -->
            <div v-if="serviceReminders.items?.length" class="space-y-2">
              <div 
                v-for="reminder in serviceReminders.items" 
                :key="reminder.name"
                class="flex items-center justify-between p-2 rounded-lg"
                style="background-color: var(--bg-tertiary);"
              >
                <div>
                  <p class="text-sm font-medium" style="color: var(--text-primary);">{{ reminder.reminder_type }}</p>
                  <p class="text-xs" style="color: var(--text-muted);">{{ reminder.due_date }}</p>
                </div>
                <Badge :variant="reminder.status === 'Overdue' ? 'danger' : 'default'" size="sm">
                  {{ reminder.status }}
                </Badge>
              </div>
            </div>
            <p v-else class="text-sm text-center py-4" style="color: var(--text-muted);">{{ $t('vehicles.no_reminders') }}</p>
          </Card>

          <!-- Open Issues -->
          <Card>
            <h3 class="text-lg font-semibold mb-4" style="color: var(--text-primary);">{{ $t('issues.open_issues') }}</h3>
            
            <!-- Counts -->
            <div class="grid grid-cols-2 gap-2 mb-4">
              <div class="text-center p-3 rounded-lg" style="background-color: var(--bg-tertiary);">
                <p class="text-2xl font-bold" style="color: var(--text-primary);">{{ openIssues.open }}</p>
                <p class="text-xs" style="color: var(--text-muted);">{{ $t('common.open') }}</p>
              </div>
              <div class="text-center p-3 rounded-lg" style="background-color: var(--bg-tertiary);">
                <p class="text-2xl font-bold text-red-500">{{ openIssues.overdue }}</p>
                <p class="text-xs" style="color: var(--text-muted);">{{ $t('vehicles.overdue_label') }}</p>
              </div>
            </div>

            <!-- List -->
            <div v-if="openIssues.items?.length" class="space-y-2">
              <div 
                v-for="issue in openIssues.items" 
                :key="issue.name"
                class="p-2 rounded-lg"
                style="background-color: var(--bg-tertiary);"
              >
                <p class="text-sm font-medium" style="color: var(--text-primary);">{{ issue.subject }}</p>
                <div class="flex items-center gap-2 mt-1">
                  <Badge :variant="issue.priority === 'High' ? 'danger' : issue.priority === 'Medium' ? 'warning' : 'default'" size="sm">
                    {{ issue.priority }}
                  </Badge>
                  <span class="text-xs" style="color: var(--text-muted);">{{ issue.status }}</span>
                </div>
              </div>
            </div>
            <p v-else class="text-sm text-center py-4" style="color: var(--text-muted);">{{ $t('vehicles.no_open_issues') }}</p>
          </Card>
        </div>
      </div>
    </template>

    <!-- Tab: Specs -->
    <SpecsTab v-else-if="vehicle && activeTab === 'specs'" :vehicleId="props.id" />

    <!-- Tab: Financial -->
    <FinancialsTab v-else-if="vehicle && activeTab === 'financial'" :vehicleId="props.id" />

    <!-- Tab: Sensor Data -->
    <SensorDataTab v-else-if="vehicle && activeTab === 'sensor-data'" :vehicleId="props.id" />

    <!-- Tab: Service History -->
    <ServiceHistoryTab v-else-if="vehicle && activeTab === 'services'" :vehicleId="props.id" />

    <!-- Tab: Inspection History -->
    <InspectionHistoryTab v-else-if="vehicle && activeTab === 'inspections'" :vehicleId="props.id" />

    <!-- Tab: Work Orders -->
    <WorkOrdersTab v-else-if="vehicle && activeTab === 'work-orders'" :vehicleId="props.id" />

    <!-- Tab: Service Reminders -->
    <ServiceRemindersTab v-else-if="vehicle && activeTab === 'reminders'" :vehicleId="props.id" />

    <!-- Tab: Issues -->
    <IssuesTab v-else-if="vehicle && activeTab === 'issues'" :vehicleId="props.id" />

    <!-- Tab: Fuel Quota -->
    <FuelQuotaTab v-else-if="vehicle && activeTab === 'fuel'" :vehicleId="props.id" />

    <!-- Tab: Attachments -->
    <AttachmentsTab v-else-if="vehicle && activeTab === 'attachments'" :vehicleId="props.id" />
  </div>
</template>
