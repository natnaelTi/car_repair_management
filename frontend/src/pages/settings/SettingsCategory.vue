<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { RouterLink } from 'vue-router'
import {
  LucideArrowLeft,
  LucideExternalLink,
  LucideRefreshCw,
  LucideActivity,
  LucideHistory,
  LucidePlay,
  LucidePlus,
  LucideSave,
  LucideTrash2,
} from 'lucide-vue-next'
import { Card, Button, Badge, Skeleton, EmptyState } from '@/components/ui'
import { apiCall } from '@/api'

const props = defineProps<{ category: string }>()

const CATEGORY_META: Record<string, { title: string; description: string }> = {
  organization: { title: 'Organization & Locations', description: 'Company profile, currency, fiscal year' },
  vehicles: { title: 'Vehicles Configuration', description: 'Vehicle types, service reminders, thresholds' },
  work_orders: { title: 'Work Orders & Workflow', description: 'Statuses, SLA targets, numbering rules' },
  inspections: { title: 'Inspections', description: 'Inspection types, schedules, form templates' },
  issues: { title: 'Issues & Faults', description: 'Severity scales, categories, fault codes' },
  expenses: { title: 'Expenses & Finance', description: 'Expense categories, receipt policies' },
  inventory: { title: 'Inventory', description: 'Warehouses, reorder defaults, stock policies' },
  customers: { title: 'Customers & CRM', description: 'Customer groups, territories, templates' },
  users: { title: 'Users, Roles & Permissions', description: 'Roles, permission sets, access control' },
  notifications: { title: 'Notifications', description: 'Channels, rules, recipient mapping' },
  integrations: { title: 'Integrations', description: 'Email, APIs, webhooks, external modules' },
  data_audit: { title: 'Data & Audit', description: 'Import tools, audit logs, activity history' },
  branding: { title: 'Branding & Documents', description: 'Logo, print formats, PDF and email templates' },
  maintenance: { title: 'System Maintenance', description: 'Scheduled jobs, cache, health checks' },
}

const isLoading = ref(true)
const settings = ref<any>({})
const lastModifiedBy = ref<string | null>(null)
const lastModifiedOn = ref<string | null>(null)
const healthData = ref<any>(null)
const healthLoading = ref(false)
const auditEntries = ref<any[]>([])
const auditLoading = ref(false)
const auditDoctype = ref('')
const auditLimit = ref(20)
const hardwareConfigSaving = ref(false)
const hardwareConfigRunning = ref('')
const hardwareConfigMessage = ref('')
const hardwareConfigError = ref('')
const hardwareConfigForm = ref<any>({
  name: '',
  configuration_name: '',
  enabled: 1,
  endpoint_url: '',
  http_method: 'GET',
  api_key_header: 'key',
  api_key: '',
  request_body_json: '',
  response_root: '',
  ingest_on_run: 1,
  max_records_per_run: 50,
})

const meta = ref(CATEGORY_META[props.category] || { title: props.category, description: '' })

async function loadData() {
  isLoading.value = true
  try {
    const res = await apiCall<any>(
      'car_repair_management.api.settings.get_settings_category',
      { category: props.category }
    )
    settings.value = res?.settings || {}
    lastModifiedBy.value = res?.last_modified_by || null
    lastModifiedOn.value = res?.last_modified_on || null
  } catch (e) {
    console.error('Failed to load settings category:', e)
  } finally {
    isLoading.value = false
  }
}

async function checkHealth() {
  healthLoading.value = true
  try {
    const res = await apiCall<any>(
      'car_repair_management.api.settings.get_system_health'
    )
    healthData.value = res
  } catch (e) {
    console.error('Failed to check health:', e)
  } finally {
    healthLoading.value = false
  }
}

async function loadAuditLog() {
  auditLoading.value = true
  try {
    const args: Record<string, unknown> = { limit: auditLimit.value }
    if (auditDoctype.value) args.doctype = auditDoctype.value
    const res = await apiCall<{ entries: any[]; total: number }>(
      'car_repair_management.api.settings.get_audit_log',
      args,
    )
    auditEntries.value = res.entries || []
  } catch (e) {
    console.warn('Failed to load audit log', e)
  } finally {
    auditLoading.value = false
  }
}

function resetHardwareConfigForm() {
  hardwareConfigForm.value = {
    name: '',
    configuration_name: '',
    enabled: 1,
    endpoint_url: '',
    http_method: 'GET',
    api_key_header: 'key',
    api_key: '',
    request_body_json: '',
    response_root: '',
    ingest_on_run: 1,
    max_records_per_run: 50,
  }
  hardwareConfigMessage.value = ''
  hardwareConfigError.value = ''
}

function editHardwareConfig(config: any) {
  hardwareConfigForm.value = {
    name: config.name,
    configuration_name: config.configuration_name,
    enabled: config.enabled ? 1 : 0,
    endpoint_url: config.endpoint_url,
    http_method: config.http_method || 'GET',
    api_key_header: config.api_key_header || 'key',
    api_key: '',
    request_body_json: '',
    response_root: config.response_root || '',
    ingest_on_run: config.ingest_on_run ? 1 : 0,
    max_records_per_run: config.max_records_per_run || 50,
  }
  hardwareConfigMessage.value = ''
  hardwareConfigError.value = ''
}

async function saveHardwareConfig() {
  hardwareConfigSaving.value = true
  hardwareConfigMessage.value = ''
  hardwareConfigError.value = ''
  const form = hardwareConfigForm.value
  const data: Record<string, unknown> = {
    configuration_name: form.configuration_name,
    enabled: form.enabled ? 1 : 0,
    endpoint_url: form.endpoint_url,
    http_method: form.http_method,
    api_key_header: form.api_key_header || 'key',
    request_body_json: form.request_body_json || '',
    response_root: form.response_root || '',
    ingest_on_run: form.ingest_on_run ? 1 : 0,
    max_records_per_run: Number(form.max_records_per_run || 50),
  }
  if (form.api_key) data.api_key = form.api_key
  try {
    await apiCall('car_repair_management.api.telemetry.hardware_test_configuration', {
      action: form.name ? 'update' : 'create',
      name: form.name || undefined,
      data,
    })
    hardwareConfigMessage.value = form.name ? 'Hardware test configuration updated.' : 'Hardware test configuration created.'
    resetHardwareConfigForm()
    await loadData()
  } catch (e: any) {
    hardwareConfigError.value = e?.message || 'Failed to save hardware test configuration'
  } finally {
    hardwareConfigSaving.value = false
  }
}

async function runHardwareConfig(config: any) {
  hardwareConfigRunning.value = config.name
  hardwareConfigMessage.value = ''
  hardwareConfigError.value = ''
  try {
    const res = await apiCall<any>('car_repair_management.api.telemetry.hardware_test_configuration', {
      action: 'run',
      name: config.name,
    })
    hardwareConfigMessage.value = `Fetched ${res.fetched_count || 0} payload(s), ingested ${res.ingested_count || 0}.`
    await loadData()
  } catch (e: any) {
    hardwareConfigError.value = e?.message || 'Failed to run hardware test configuration'
    await loadData()
  } finally {
    hardwareConfigRunning.value = ''
  }
}

async function deleteHardwareConfig(config: any) {
  hardwareConfigSaving.value = true
  hardwareConfigMessage.value = ''
  hardwareConfigError.value = ''
  try {
    await apiCall('car_repair_management.api.telemetry.hardware_test_configuration', {
      action: 'delete',
      name: config.name,
    })
    hardwareConfigMessage.value = 'Hardware test configuration deleted.'
    if (hardwareConfigForm.value.name === config.name) resetHardwareConfigForm()
    await loadData()
  } catch (e: any) {
    hardwareConfigError.value = e?.message || 'Failed to delete hardware test configuration'
  } finally {
    hardwareConfigSaving.value = false
  }
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return 'N/A'
  try {
    const d = new Date(dateStr)
    return d.toLocaleDateString() + ' ' + d.toLocaleTimeString()
  } catch {
    return dateStr
  }
}

onMounted(loadData)
watch(() => props.category, () => {
  meta.value = CATEGORY_META[props.category] || { title: props.category, description: '' }
  loadData()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center gap-4">
      <RouterLink to="/settings">
        <Button variant="ghost" size="sm">
          <LucideArrowLeft class="size-4" />
        </Button>
      </RouterLink>
      <div>
        <h1 class="text-page-title" style="color: var(--text-primary);">{{ meta.title }}</h1>
        <p class="text-sm mt-1" style="color: var(--text-muted);">{{ meta.description }}</p>
      </div>
    </div>

    <!-- Audit Info -->
    <div
      v-if="lastModifiedBy"
      class="flex items-center gap-2 text-xs px-4 py-2 rounded-lg"
      style="background-color: var(--bg-tertiary); color: var(--text-muted);"
    >
      <LucideActivity class="size-3" />
      <span>Last changed by <strong style="color: var(--text-secondary);">{{ lastModifiedBy }}</strong> on {{ formatDate(lastModifiedOn) }}</span>
    </div>

    <!-- Loading -->
    <template v-if="isLoading">
      <Card v-for="i in 3" :key="i"><Skeleton height="120px" /></Card>
    </template>

    <!-- Organization -->
    <template v-else-if="category === 'organization'">
      <Card>
        <h3 class="text-section-title mb-4" style="color: var(--text-primary);">Companies</h3>
        <div v-if="settings.companies?.length" class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b" style="border-color: var(--border-color);">
                <th class="text-left py-2 px-3 font-medium" style="color: var(--text-muted);">Company</th>
                <th class="text-left py-2 px-3 font-medium" style="color: var(--text-muted);">Currency</th>
                <th class="text-left py-2 px-3 font-medium" style="color: var(--text-muted);">Country</th>
                <th class="text-right py-2 px-3 font-medium" style="color: var(--text-muted);">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="c in settings.companies" :key="c.name" class="border-b" style="border-color: var(--border-subtle);">
                <td class="py-2 px-3" style="color: var(--text-primary);">{{ c.company_name || c.name }}</td>
                <td class="py-2 px-3" style="color: var(--text-secondary);">{{ c.default_currency }}</td>
                <td class="py-2 px-3" style="color: var(--text-secondary);">{{ c.country }}</td>
                <td class="py-2 px-3 text-right">
                  <a :href="`/app/company/${c.name}`" target="_blank" class="inline-flex items-center gap-1 text-xs" style="color: var(--text-muted);">
                    Edit <LucideExternalLink class="size-3" />
                  </a>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <EmptyState v-else title="No companies" description="Configure your company in ERPNext" />
      </Card>
      <Card>
        <div class="flex items-center gap-4">
          <span class="text-sm" style="color: var(--text-muted);">Default Currency:</span>
          <span class="text-sm font-medium" style="color: var(--text-primary);">{{ settings.default_currency || 'Not set' }}</span>
        </div>
      </Card>
    </template>

    <!-- Vehicles -->
    <template v-else-if="category === 'vehicles'">
      <Card>
        <h3 class="text-section-title mb-4" style="color: var(--text-primary);">Vehicle Types</h3>
        <div v-if="settings.vehicle_types?.length" class="space-y-2">
          <div v-for="vt in settings.vehicle_types" :key="vt.vehicle_type"
            class="flex items-center justify-between py-2 px-3 rounded-lg" style="background-color: var(--bg-tertiary);">
            <span class="text-sm" style="color: var(--text-primary);">{{ vt.vehicle_type }}</span>
            <Badge variant="default">{{ vt.count }} vehicles</Badge>
          </div>
        </div>
        <EmptyState v-else title="No vehicle types" description="Vehicle types will appear when vehicles have custom_vehicle_type set" />
      </Card>
      <Card>
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-section-title" style="color: var(--text-primary);">Fleet Replacement Settings</h3>
          <a href="/app/fleet-replacement-settings" target="_blank" class="inline-flex items-center gap-1 text-xs" style="color: var(--text-muted);">
            Edit in Desk <LucideExternalLink class="size-3" />
          </a>
        </div>
        <div v-if="settings.fleet_replacement_settings && Object.keys(settings.fleet_replacement_settings).length" class="grid grid-cols-2 gap-4">
          <div v-for="(val, key) in settings.fleet_replacement_settings" :key="String(key)"
            class="py-2" v-show="!['name','doctype','owner','creation','modified','modified_by','docstatus','idx','__unsaved'].includes(String(key))">
            <p class="text-xs" style="color: var(--text-muted);">{{ String(key).replace(/_/g, ' ') }}</p>
            <p class="text-sm font-medium" style="color: var(--text-primary);">{{ val ?? 'N/A' }}</p>
          </div>
        </div>
        <p v-else class="text-sm" style="color: var(--text-muted);">No settings configured</p>
      </Card>
    </template>

    <!-- Work Orders -->
    <template v-else-if="category === 'work_orders'">
      <Card>
        <h3 class="text-section-title mb-4" style="color: var(--text-primary);">Work Order Statuses</h3>
        <div class="flex flex-wrap gap-2">
          <Badge v-for="s in settings.statuses" :key="s"
            :variant="s === 'Cancelled' ? 'danger' : s === 'On Hold' || s === 'Awaiting Parts' ? 'warning' : s === 'Delivered' || s === 'Closed' ? 'success' : s === 'In Progress' ? 'primary' : s === 'Scheduled' ? 'info' : 'default'">
            {{ s }}
          </Badge>
        </div>
      </Card>
      <Card>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <p class="text-xs" style="color: var(--text-muted);">Naming Series</p>
            <p class="text-sm font-medium" style="color: var(--text-primary);">{{ settings.naming_series || 'Default' }}</p>
          </div>
          <div>
            <p class="text-xs" style="color: var(--text-muted);">Total Work Orders</p>
            <p class="text-sm font-medium" style="color: var(--text-primary);">{{ settings.total_work_orders?.toLocaleString() }}</p>
          </div>
        </div>
      </Card>
    </template>

    <!-- Inspections -->
    <template v-else-if="category === 'inspections'">
      <Card>
        <h3 class="text-section-title mb-4" style="color: var(--text-primary);">Inspection Types</h3>
        <div v-if="settings.inspection_types?.length" class="space-y-2">
          <div v-for="t in settings.inspection_types" :key="t.inspection_type"
            class="flex items-center justify-between py-2 px-3 rounded-lg" style="background-color: var(--bg-tertiary);">
            <span class="text-sm" style="color: var(--text-primary);">{{ t.inspection_type }}</span>
            <Badge variant="default">{{ t.count }}</Badge>
          </div>
        </div>
        <EmptyState v-else title="No inspection types" description="Types will appear when inspections are created" />
      </Card>
      <div class="grid grid-cols-2 gap-4">
        <Card>
          <p class="text-xs" style="color: var(--text-muted);">Form Templates</p>
          <p class="text-2xl font-semibold" style="color: var(--text-primary);">{{ settings.templates_count || 0 }}</p>
          <a href="/app/inspection-form-template" target="_blank" class="inline-flex items-center gap-1 text-xs mt-2" style="color: var(--text-muted);">
            Manage <LucideExternalLink class="size-3" />
          </a>
        </Card>
        <Card>
          <p class="text-xs" style="color: var(--text-muted);">Schedules</p>
          <p class="text-2xl font-semibold" style="color: var(--text-primary);">{{ settings.schedules_count || 0 }}</p>
          <a href="/app/inspection-schedule" target="_blank" class="inline-flex items-center gap-1 text-xs mt-2" style="color: var(--text-muted);">
            Manage <LucideExternalLink class="size-3" />
          </a>
        </Card>
      </div>
    </template>

    <!-- Issues -->
    <template v-else-if="category === 'issues'">
      <Card>
        <h3 class="text-section-title mb-4" style="color: var(--text-primary);">Severity Scales</h3>
        <div class="flex flex-wrap gap-2">
          <Badge variant="default">Low</Badge>
          <Badge variant="warning">Medium</Badge>
          <Badge variant="danger">High</Badge>
          <Badge variant="danger">Critical</Badge>
        </div>
      </Card>
      <Card>
        <h3 class="text-section-title mb-4" style="color: var(--text-primary);">Issue Categories</h3>
        <div v-if="settings.categories?.length" class="space-y-2">
          <div v-for="c in settings.categories" :key="c.category"
            class="flex items-center justify-between py-2 px-3 rounded-lg" style="background-color: var(--bg-tertiary);">
            <span class="text-sm" style="color: var(--text-primary);">{{ c.category }}</span>
            <Badge variant="default">{{ c.count }}</Badge>
          </div>
        </div>
        <EmptyState v-else title="No categories" description="Categories will appear when issues use custom_category field" />
      </Card>
      <Card>
        <div>
          <p class="text-xs" style="color: var(--text-muted);">Total Issues</p>
          <p class="text-2xl font-semibold" style="color: var(--text-primary);">{{ settings.total_issues?.toLocaleString() || 0 }}</p>
        </div>
      </Card>
    </template>

    <!-- Expenses -->
    <template v-else-if="category === 'expenses'">
      <Card>
        <h3 class="text-section-title mb-4" style="color: var(--text-primary);">Expense Categories</h3>
        <div class="flex flex-wrap gap-2">
          <Badge v-for="c in settings.categories" :key="c" variant="default">{{ c }}</Badge>
        </div>
      </Card>
      <Card>
        <div>
          <p class="text-xs" style="color: var(--text-muted);">Total Expenses Recorded</p>
          <p class="text-2xl font-semibold" style="color: var(--text-primary);">{{ settings.total_expenses?.toLocaleString() || 0 }}</p>
        </div>
      </Card>
    </template>

    <!-- Inventory -->
    <template v-else-if="category === 'inventory'">
      <Card>
        <h3 class="text-section-title mb-4" style="color: var(--text-primary);">Warehouses</h3>
        <div v-if="settings.warehouses?.length" class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b" style="border-color: var(--border-color);">
                <th class="text-left py-2 px-3 font-medium" style="color: var(--text-muted);">Warehouse</th>
                <th class="text-left py-2 px-3 font-medium" style="color: var(--text-muted);">Company</th>
                <th class="text-left py-2 px-3 font-medium" style="color: var(--text-muted);">Group</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="w in settings.warehouses" :key="w.name" class="border-b" style="border-color: var(--border-subtle);">
                <td class="py-2 px-3" style="color: var(--text-primary);">{{ w.warehouse_name || w.name }}</td>
                <td class="py-2 px-3" style="color: var(--text-secondary);">{{ w.company || '-' }}</td>
                <td class="py-2 px-3"><Badge :variant="w.is_group ? 'info' : 'default'">{{ w.is_group ? 'Group' : 'Leaf' }}</Badge></td>
              </tr>
            </tbody>
          </table>
        </div>
        <EmptyState v-else title="No warehouses" description="Configure warehouses in ERPNext" />
      </Card>
      <Card>
        <h3 class="text-section-title mb-4" style="color: var(--text-primary);">Stock Settings</h3>
        <div v-if="settings.stock_settings" class="space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-sm" style="color: var(--text-secondary);">Allow Negative Stock</span>
            <Badge :variant="settings.stock_settings.allow_negative_stock ? 'warning' : 'success'">
              {{ settings.stock_settings.allow_negative_stock ? 'Yes' : 'No' }}
            </Badge>
          </div>
        </div>
        <p v-else class="text-sm" style="color: var(--text-muted);">Stock settings not available</p>
      </Card>
    </template>

    <!-- Customers -->
    <template v-else-if="category === 'customers'">
      <Card>
        <h3 class="text-section-title mb-4" style="color: var(--text-primary);">Customer Groups</h3>
        <div v-if="settings.customer_groups?.length" class="space-y-1">
          <div v-for="g in settings.customer_groups" :key="g.name"
            class="flex items-center justify-between py-1.5 px-3 rounded" style="color: var(--text-primary);">
            <span class="text-sm">{{ g.name }}</span>
            <Badge v-if="g.is_group" variant="info" size="sm">Group</Badge>
          </div>
        </div>
        <EmptyState v-else title="No customer groups" />
      </Card>
      <Card>
        <h3 class="text-section-title mb-4" style="color: var(--text-primary);">Territories</h3>
        <div v-if="settings.territories?.length" class="space-y-1">
          <div v-for="t in settings.territories" :key="t.name"
            class="flex items-center justify-between py-1.5 px-3 rounded" style="color: var(--text-primary);">
            <span class="text-sm">{{ t.name }}</span>
            <Badge v-if="t.is_group" variant="info" size="sm">Group</Badge>
          </div>
        </div>
        <EmptyState v-else title="No territories" />
      </Card>
      <Card>
        <p class="text-xs" style="color: var(--text-muted);">Total Customers</p>
        <p class="text-2xl font-semibold" style="color: var(--text-primary);">{{ settings.total_customers?.toLocaleString() || 0 }}</p>
      </Card>
    </template>

    <!-- Users -->
    <template v-else-if="category === 'users'">
      <Card>
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-section-title" style="color: var(--text-primary);">Roles</h3>
          <Badge variant="default">{{ settings.total_users || 0 }} users</Badge>
        </div>
        <div v-if="settings.roles?.length" class="overflow-x-auto max-h-96 overflow-y-auto">
          <table class="w-full text-sm">
            <thead class="sticky top-0" style="background-color: var(--bg-secondary);">
              <tr class="border-b" style="border-color: var(--border-color);">
                <th class="text-left py-2 px-3 font-medium" style="color: var(--text-muted);">Role</th>
                <th class="text-center py-2 px-3 font-medium" style="color: var(--text-muted);">Desk Access</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in settings.roles" :key="r.name" class="border-b" style="border-color: var(--border-subtle);">
                <td class="py-2 px-3" style="color: var(--text-primary);">{{ r.name }}</td>
                <td class="py-2 px-3 text-center">
                  <Badge :variant="r.desk_access ? 'success' : 'default'" size="sm">
                    {{ r.desk_access ? 'Yes' : 'No' }}
                  </Badge>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <EmptyState v-else title="No roles" />
      </Card>
    </template>

    <!-- Notifications -->
    <template v-else-if="category === 'notifications'">
      <Card>
        <h3 class="text-section-title mb-4" style="color: var(--text-primary);">Email Accounts</h3>
        <div v-if="settings.email_accounts?.length" class="space-y-2">
          <div v-for="ea in settings.email_accounts" :key="ea.name"
            class="flex items-center justify-between py-2 px-3 rounded-lg" style="background-color: var(--bg-tertiary);">
            <div>
              <p class="text-sm font-medium" style="color: var(--text-primary);">{{ ea.email_account_name || ea.name }}</p>
              <p class="text-xs" style="color: var(--text-muted);">{{ ea.email_id }}</p>
            </div>
            <Badge :variant="ea.enabled ? 'success' : 'danger'" size="sm">
              {{ ea.enabled ? 'Enabled' : 'Disabled' }}
            </Badge>
          </div>
        </div>
        <EmptyState v-else title="No email accounts" description="Configure email accounts in Frappe setup" />
      </Card>
      <Card>
        <h3 class="text-section-title mb-4" style="color: var(--text-primary);">Recent Notifications</h3>
        <div v-if="settings.recent_notifications?.length" class="space-y-2">
          <div v-for="n in settings.recent_notifications" :key="n.name"
            class="py-2 px-3 rounded-lg" style="background-color: var(--bg-tertiary);">
            <p class="text-sm" style="color: var(--text-primary);">{{ n.subject }}</p>
            <p class="text-xs" style="color: var(--text-muted);">{{ n.type }} · {{ formatDate(n.creation) }}</p>
          </div>
        </div>
        <EmptyState v-else title="No recent notifications" />
      </Card>
    </template>

    <!-- Integrations -->
    <template v-else-if="category === 'integrations'">
      <Card>
        <h3 class="text-section-title mb-4" style="color: var(--text-primary);">Email Accounts</h3>
        <div v-if="settings.email_accounts?.length" class="space-y-2">
          <div v-for="ea in settings.email_accounts" :key="ea.name"
            class="flex items-center justify-between py-2 px-3 rounded-lg" style="background-color: var(--bg-tertiary);">
            <div>
              <p class="text-sm font-medium" style="color: var(--text-primary);">{{ ea.email_account_name || ea.name }}</p>
              <p class="text-xs" style="color: var(--text-muted);">{{ ea.email_id }}</p>
            </div>
            <Badge variant="success" size="sm">Connected</Badge>
          </div>
        </div>
        <EmptyState v-else title="No email integrations" />
      </Card>
      <Card>
        <div class="flex items-center justify-between gap-3 mb-4">
          <h3 class="text-section-title" style="color: var(--text-primary);">Mock Hardware APIs</h3>
          <Button variant="outline" size="sm" @click="resetHardwareConfigForm">
            <LucidePlus class="size-4" />
            New
          </Button>
        </div>

        <div v-if="hardwareConfigMessage" class="mb-4 px-3 py-2 rounded text-sm" style="background: var(--bg-tertiary); color: var(--text-primary);">
          {{ hardwareConfigMessage }}
        </div>
        <div v-if="hardwareConfigError" class="mb-4 px-3 py-2 rounded text-sm" style="background: rgba(239, 68, 68, 0.12); color: rgb(220, 38, 38);">
          {{ hardwareConfigError }}
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-5">
          <div>
            <label class="block text-xs font-medium mb-1" style="color: var(--text-muted);">Configuration Name</label>
            <input
              v-model="hardwareConfigForm.configuration_name"
              type="text"
              class="w-full h-9 px-3 text-sm rounded border"
              style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color);"
            />
          </div>
          <div>
            <label class="block text-xs font-medium mb-1" style="color: var(--text-muted);">Endpoint URL</label>
            <input
              v-model="hardwareConfigForm.endpoint_url"
              type="url"
              placeholder="https://mellatech.et/et/api/api.php?api=user&ver=1.0&cmd=USER_GET_OBJECTS"
              class="w-full h-9 px-3 text-sm rounded border"
              style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color);"
            />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-medium mb-1" style="color: var(--text-muted);">HTTP Method</label>
              <select
                v-model="hardwareConfigForm.http_method"
                class="w-full h-9 px-2 text-sm rounded border"
                style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color);"
              >
                <option value="GET">GET</option>
                <option value="POST">POST</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium mb-1" style="color: var(--text-muted);">API Key Header</label>
              <input
                v-model="hardwareConfigForm.api_key_header"
                type="text"
                class="w-full h-9 px-3 text-sm rounded border"
                style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color);"
              />
            </div>
          </div>
          <div>
            <label class="block text-xs font-medium mb-1" style="color: var(--text-muted);">API Key</label>
            <input
              v-model="hardwareConfigForm.api_key"
              type="password"
              :placeholder="hardwareConfigForm.name ? 'Leave blank to keep existing key' : ''"
              class="w-full h-9 px-3 text-sm rounded border"
              style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color);"
            />
          </div>
          <div>
            <label class="block text-xs font-medium mb-1" style="color: var(--text-muted);">Response Root</label>
            <input
              v-model="hardwareConfigForm.response_root"
              type="text"
              placeholder="data.objects"
              class="w-full h-9 px-3 text-sm rounded border"
              style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color);"
            />
          </div>
          <div class="grid grid-cols-3 gap-3">
            <label class="inline-flex items-center gap-2 text-sm mt-6" style="color: var(--text-secondary);">
              <input v-model="hardwareConfigForm.enabled" type="checkbox" :true-value="1" :false-value="0" />
              Enabled
            </label>
            <label class="inline-flex items-center gap-2 text-sm mt-6" style="color: var(--text-secondary);">
              <input v-model="hardwareConfigForm.ingest_on_run" type="checkbox" :true-value="1" :false-value="0" />
              Ingest
            </label>
            <div>
              <label class="block text-xs font-medium mb-1" style="color: var(--text-muted);">Max Records</label>
              <input
                v-model="hardwareConfigForm.max_records_per_run"
                type="number"
                min="1"
                max="500"
                class="w-full h-9 px-3 text-sm rounded border"
                style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color);"
              />
            </div>
          </div>
          <div class="lg:col-span-2">
            <label class="block text-xs font-medium mb-1" style="color: var(--text-muted);">Request Body JSON</label>
            <textarea
              v-model="hardwareConfigForm.request_body_json"
              rows="3"
              class="w-full px-3 py-2 text-sm rounded border font-mono"
              style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color);"
            ></textarea>
          </div>
        </div>

        <div class="flex justify-end gap-2 mb-5">
          <Button variant="ghost" size="sm" @click="resetHardwareConfigForm">Clear</Button>
          <Button variant="primary" size="sm" :loading="hardwareConfigSaving" @click="saveHardwareConfig">
            <LucideSave class="size-4" />
            Save
          </Button>
        </div>

        <div v-if="settings.hardware_test_configurations?.length" class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b" style="border-color: var(--border-color);">
                <th class="text-left py-2 px-3 font-medium" style="color: var(--text-muted);">Name</th>
                <th class="text-left py-2 px-3 font-medium" style="color: var(--text-muted);">Endpoint</th>
                <th class="text-center py-2 px-3 font-medium" style="color: var(--text-muted);">Status</th>
                <th class="text-center py-2 px-3 font-medium" style="color: var(--text-muted);">Last Run</th>
                <th class="text-right py-2 px-3 font-medium" style="color: var(--text-muted);">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="cfg in settings.hardware_test_configurations" :key="cfg.name" class="border-b" style="border-color: var(--border-subtle);">
                <td class="py-2 px-3" style="color: var(--text-primary);">
                  <button class="text-left hover:underline" @click="editHardwareConfig(cfg)">
                    {{ cfg.configuration_name || cfg.name }}
                  </button>
                  <p class="text-xs" style="color: var(--text-muted);">{{ cfg.http_method }} · {{ cfg.api_key_header || 'key' }}</p>
                </td>
                <td class="py-2 px-3 text-xs truncate max-w-md" style="color: var(--text-muted);">{{ cfg.endpoint_url }}</td>
                <td class="py-2 px-3 text-center">
                  <Badge :variant="cfg.enabled ? (cfg.last_status === 'Failed' ? 'danger' : 'success') : 'default'" size="sm">
                    {{ cfg.enabled ? (cfg.last_status || 'Enabled') : 'Disabled' }}
                  </Badge>
                </td>
                <td class="py-2 px-3 text-center text-xs" style="color: var(--text-muted);">
                  {{ cfg.last_run ? formatDate(cfg.last_run) : '-' }}
                  <span v-if="cfg.last_ingested_count" class="block">{{ cfg.last_ingested_count }} ingested</span>
                </td>
                <td class="py-2 px-3">
                  <div class="flex justify-end gap-1">
                    <Button variant="ghost" size="sm" :loading="hardwareConfigRunning === cfg.name" @click="runHardwareConfig(cfg)">
                      <LucidePlay class="size-4" />
                    </Button>
                    <Button variant="ghost" size="sm" @click="editHardwareConfig(cfg)">Edit</Button>
                    <Button variant="ghost" size="sm" @click="deleteHardwareConfig(cfg)">
                      <LucideTrash2 class="size-4" />
                    </Button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <EmptyState v-else title="No mock hardware APIs configured" />
      </Card>
      <Card>
        <h3 class="text-section-title mb-4" style="color: var(--text-primary);">Webhooks</h3>
        <div v-if="settings.webhooks?.length" class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b" style="border-color: var(--border-color);">
                <th class="text-left py-2 px-3 font-medium" style="color: var(--text-muted);">Name</th>
                <th class="text-left py-2 px-3 font-medium" style="color: var(--text-muted);">DocType</th>
                <th class="text-left py-2 px-3 font-medium" style="color: var(--text-muted);">URL</th>
                <th class="text-center py-2 px-3 font-medium" style="color: var(--text-muted);">Enabled</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="w in settings.webhooks" :key="w.name" class="border-b" style="border-color: var(--border-subtle);">
                <td class="py-2 px-3" style="color: var(--text-primary);">{{ w.name }}</td>
                <td class="py-2 px-3" style="color: var(--text-secondary);">{{ w.webhook_doctype }}</td>
                <td class="py-2 px-3 text-xs truncate max-w-xs" style="color: var(--text-muted);">{{ w.request_url }}</td>
                <td class="py-2 px-3 text-center">
                  <Badge :variant="w.enabled ? 'success' : 'danger'" size="sm">{{ w.enabled ? 'Yes' : 'No' }}</Badge>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <EmptyState v-else title="No webhooks configured" />
      </Card>
    </template>

    <!-- Data & Audit -->
    <template v-else-if="category === 'data_audit'">
      <Card>
        <h3 class="text-section-title mb-4" style="color: var(--text-primary);">Recent Activity</h3>
        <div v-if="settings.recent_activity?.length" class="space-y-2 max-h-96 overflow-y-auto">
          <div v-for="a in settings.recent_activity" :key="a.name"
            class="py-2 px-3 rounded-lg" style="background-color: var(--bg-tertiary);">
            <p class="text-sm" style="color: var(--text-primary);">{{ a.subject }}</p>
            <p class="text-xs" style="color: var(--text-muted);">{{ a.user }} · {{ a.operation }} · {{ formatDate(a.creation) }}</p>
          </div>
        </div>
        <EmptyState v-else title="No recent activity" />
      </Card>

      <!-- Audit Log -->
      <Card>
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-section-title" style="color: var(--text-primary);">
            <LucideHistory class="size-4 inline-block mr-1" />
            Audit Log
          </h3>
          <Button variant="outline" size="sm" :loading="auditLoading" @click="loadAuditLog">
            <LucideRefreshCw class="size-4" />
            Load
          </Button>
        </div>
        <div class="flex items-end gap-3 mb-4">
          <div class="flex-1">
            <label class="block text-xs font-medium mb-1" style="color: var(--text-muted);">Filter by DocType</label>
            <input
              v-model="auditDoctype"
              type="text"
              placeholder="e.g., Repair Order, Vehicle..."
              class="w-full h-9 px-3 text-sm rounded border"
              style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color);"
            />
          </div>
          <select
            v-model="auditLimit"
            class="h-9 px-2 text-sm rounded border"
            style="background: var(--bg-secondary); color: var(--text-primary); border-color: var(--border-color);"
          >
            <option :value="10">10</option>
            <option :value="20">20</option>
            <option :value="50">50</option>
            <option :value="100">100</option>
          </select>
        </div>
        <div v-if="auditEntries.length" class="overflow-x-auto max-h-96 overflow-y-auto">
          <table class="w-full text-sm">
            <thead class="sticky top-0" style="background-color: var(--bg-secondary);">
              <tr class="border-b" style="border-color: var(--border-color);">
                <th class="text-left py-2 px-3 font-medium" style="color: var(--text-muted);">DocType</th>
                <th class="text-left py-2 px-3 font-medium" style="color: var(--text-muted);">Document</th>
                <th class="text-left py-2 px-3 font-medium" style="color: var(--text-muted);">Changed By</th>
                <th class="text-left py-2 px-3 font-medium" style="color: var(--text-muted);">Date</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="entry in auditEntries" :key="entry.name" class="border-b" style="border-color: var(--border-subtle);">
                <td class="py-2 px-3" style="color: var(--text-primary);">{{ entry.ref_doctype }}</td>
                <td class="py-2 px-3">
                  <a :href="`/app/${(entry.ref_doctype || '').toLowerCase().replace(/ /g, '-')}/${entry.ref_name}`" target="_blank" class="text-sm hover:underline" style="color: var(--accent);">
                    {{ entry.ref_name }}
                  </a>
                </td>
                <td class="py-2 px-3" style="color: var(--text-secondary);">{{ entry.owner }}</td>
                <td class="py-2 px-3 text-xs whitespace-nowrap" style="color: var(--text-muted);">{{ formatDate(entry.creation) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-else class="text-sm" style="color: var(--text-muted);">Click "Load" to fetch audit log entries</p>
      </Card>

      <Card>
        <h3 class="text-section-title mb-4" style="color: var(--text-primary);">Data Imports</h3>
        <div v-if="settings.data_imports?.length" class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b" style="border-color: var(--border-color);">
                <th class="text-left py-2 px-3 font-medium" style="color: var(--text-muted);">Name</th>
                <th class="text-left py-2 px-3 font-medium" style="color: var(--text-muted);">DocType</th>
                <th class="text-left py-2 px-3 font-medium" style="color: var(--text-muted);">Status</th>
                <th class="text-left py-2 px-3 font-medium" style="color: var(--text-muted);">Date</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="d in settings.data_imports" :key="d.name" class="border-b" style="border-color: var(--border-subtle);">
                <td class="py-2 px-3" style="color: var(--text-primary);">{{ d.name }}</td>
                <td class="py-2 px-3" style="color: var(--text-secondary);">{{ d.reference_doctype }}</td>
                <td class="py-2 px-3"><Badge :variant="d.status === 'Success' ? 'success' : d.status === 'Error' ? 'danger' : 'warning'">{{ d.status }}</Badge></td>
                <td class="py-2 px-3" style="color: var(--text-muted);">{{ formatDate(d.creation) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <EmptyState v-else title="No data imports" description="Use Data Import to bulk import records" />
      </Card>
    </template>

    <!-- Branding -->
    <template v-else-if="category === 'branding'">
      <Card>
        <h3 class="text-section-title mb-4" style="color: var(--text-primary);">Print Formats</h3>
        <div v-if="settings.print_formats?.length" class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b" style="border-color: var(--border-color);">
                <th class="text-left py-2 px-3 font-medium" style="color: var(--text-muted);">Name</th>
                <th class="text-left py-2 px-3 font-medium" style="color: var(--text-muted);">DocType</th>
                <th class="text-center py-2 px-3 font-medium" style="color: var(--text-muted);">Standard</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="pf in settings.print_formats" :key="pf.name" class="border-b" style="border-color: var(--border-subtle);">
                <td class="py-2 px-3" style="color: var(--text-primary);">{{ pf.name }}</td>
                <td class="py-2 px-3" style="color: var(--text-secondary);">{{ pf.doc_type }}</td>
                <td class="py-2 px-3 text-center">
                  <Badge v-if="pf.standard === 'Yes'" variant="info" size="sm">Standard</Badge>
                  <Badge v-else variant="default" size="sm">Custom</Badge>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <EmptyState v-else title="No print formats" />
      </Card>
      <Card>
        <h3 class="text-section-title mb-4" style="color: var(--text-primary);">Email Templates</h3>
        <div v-if="settings.email_templates?.length" class="space-y-2">
          <div v-for="et in settings.email_templates" :key="et.name"
            class="flex items-center justify-between py-2 px-3 rounded-lg" style="background-color: var(--bg-tertiary);">
            <div>
              <p class="text-sm font-medium" style="color: var(--text-primary);">{{ et.name }}</p>
              <p class="text-xs" style="color: var(--text-muted);">{{ et.subject }}</p>
            </div>
          </div>
        </div>
        <EmptyState v-else title="No email templates" />
      </Card>
      <Card>
        <h3 class="text-section-title mb-4" style="color: var(--text-primary);">Letter Heads</h3>
        <div v-if="settings.letter_heads?.length" class="space-y-2">
          <div v-for="lh in settings.letter_heads" :key="lh.name"
            class="flex items-center justify-between py-2 px-3 rounded-lg" style="background-color: var(--bg-tertiary);">
            <span class="text-sm" style="color: var(--text-primary);">{{ lh.name }}</span>
            <Badge v-if="lh.is_default" variant="primary" size="sm">Default</Badge>
          </div>
        </div>
        <EmptyState v-else title="No letter heads" />
      </Card>
    </template>

    <!-- Maintenance -->
    <template v-else-if="category === 'maintenance'">
      <Card>
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-section-title" style="color: var(--text-primary);">Scheduler</h3>
          <Badge :variant="settings.scheduler_status === 'Active' ? 'success' : 'danger'">
            {{ settings.scheduler_status || 'Unknown' }}
          </Badge>
        </div>
      </Card>
      <Card>
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-section-title" style="color: var(--text-primary);">Scheduled Jobs</h3>
        </div>
        <div v-if="settings.scheduled_jobs?.length" class="overflow-x-auto max-h-96 overflow-y-auto">
          <table class="w-full text-sm">
            <thead class="sticky top-0" style="background-color: var(--bg-secondary);">
              <tr class="border-b" style="border-color: var(--border-color);">
                <th class="text-left py-2 px-3 font-medium" style="color: var(--text-muted);">Method</th>
                <th class="text-left py-2 px-3 font-medium" style="color: var(--text-muted);">Frequency</th>
                <th class="text-left py-2 px-3 font-medium" style="color: var(--text-muted);">Last Run</th>
                <th class="text-center py-2 px-3 font-medium" style="color: var(--text-muted);">Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="j in settings.scheduled_jobs" :key="j.name" class="border-b" style="border-color: var(--border-subtle);">
                <td class="py-2 px-3 text-xs font-mono truncate max-w-xs" style="color: var(--text-primary);">{{ j.method }}</td>
                <td class="py-2 px-3" style="color: var(--text-secondary);">{{ j.frequency }}</td>
                <td class="py-2 px-3 text-xs" style="color: var(--text-muted);">{{ formatDate(j.last_execution) }}</td>
                <td class="py-2 px-3 text-center">
                  <Badge :variant="j.stopped ? 'danger' : 'success'" size="sm">{{ j.stopped ? 'Stopped' : 'Active' }}</Badge>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <EmptyState v-else title="No scheduled jobs" />
      </Card>
      <Card>
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-section-title" style="color: var(--text-primary);">System Health</h3>
          <Button variant="outline" size="sm" @click="checkHealth" :loading="healthLoading">
            <LucideRefreshCw class="size-4" />
            Check Health
          </Button>
        </div>
        <div v-if="healthData" class="grid grid-cols-2 gap-4">
          <div class="py-2 px-3 rounded-lg" style="background-color: var(--bg-tertiary);">
            <p class="text-xs" style="color: var(--text-muted);">Scheduler</p>
            <Badge :variant="healthData.scheduler_status === 'Active' ? 'success' : 'danger'">{{ healthData.scheduler_status }}</Badge>
          </div>
          <div class="py-2 px-3 rounded-lg" style="background-color: var(--bg-tertiary);">
            <p class="text-xs" style="color: var(--text-muted);">Cache</p>
            <Badge :variant="healthData.cache_status === 'Connected' ? 'success' : 'danger'">{{ healthData.cache_status }}</Badge>
          </div>
          <div class="py-2 px-3 rounded-lg" style="background-color: var(--bg-tertiary);">
            <p class="text-xs" style="color: var(--text-muted);">Database</p>
            <Badge :variant="healthData.database_status === 'Connected' ? 'success' : 'danger'">{{ healthData.database_status }}</Badge>
          </div>
          <div class="py-2 px-3 rounded-lg" style="background-color: var(--bg-tertiary);">
            <p class="text-xs" style="color: var(--text-muted);">Pending Jobs</p>
            <p class="text-sm font-medium" style="color: var(--text-primary);">{{ healthData.background_jobs?.pending || 0 }}</p>
          </div>
        </div>
        <p v-else class="text-sm" style="color: var(--text-muted);">Click "Check Health" to run diagnostics</p>
      </Card>
    </template>

    <!-- Default fallback -->
    <template v-else>
      <Card>
        <EmptyState
          :title="`${meta.title} Settings`"
          description="This settings category is available. Configure it via Frappe Desk."
        />
      </Card>
    </template>
  </div>
</template>
