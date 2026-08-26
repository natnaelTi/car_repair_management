<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { 
  LucideGauge, 
  LucideFuel, 
  LucideClock, 
  LucideActivity, 
  LucideAlertTriangle, 
  LucideDownload, 
  LucideWifi, 
  LucideWifiOff,
  LucideMapPin,
  LucideSettings,
  LucideX,
  LucideCheck,
  LucideList,
  LucideMap,
  LucideDroplets,
  LucideTable2
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, Badge, Skeleton } from '@/components/ui'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'

const props = defineProps<{ vehicleId: string }>()

const isLoading = ref(true)
const sensorData = ref<any>(null)
const timeframe = ref('30d')
const showConfigureModal = ref(false)
const mapContainer = ref<HTMLElement | null>(null)
const locationViewMode = ref<'map' | 'list'>('map')
const showRawData = ref(false)
let map: L.Map | null = null

const timeframes = [
  { id: '7d', label: '7 Days' },
  { id: '30d', label: '30 Days' },
  { id: '90d', label: '90 Days' },
]

const sensorConfig = ref([
  { id: 'gps', label: 'GPS Tracking', enabled: true },
  { id: 'fuel', label: 'Fuel Level Sensor', enabled: true },
  { id: 'obd', label: 'OBD-II Diagnostics', enabled: true },
  { id: 'temp', label: 'Engine Temperature', enabled: false },
  { id: 'tire', label: 'Tire Pressure (TPMS)', enabled: false },
])

async function loadSensorData() {
  isLoading.value = true
  try {
    sensorData.value = await apiCall('car_repair_management.api.vehicle.get_vehicle_sensor_data', {
      vehicle_name: props.vehicleId,
      timeframe: timeframe.value,
    })
    await nextTick()
    if (locationViewMode.value === 'map') {
      initMap()
    }
  } catch (e) {
    console.error('Failed to load sensor data', e)
  } finally {
    isLoading.value = false
  }
}

function initMap() {
  if (!mapContainer.value || !sensorData.value?.location_history?.length) return
  
  if (map) map.remove()
  
  const history = sensorData.value.location_history
  const lastLoc = history[0]
  
  map = L.map(mapContainer.value).setView([lastLoc.latitude, lastLoc.longitude], 13)
  
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map)
  
  const carIcon = L.divIcon({
    html: `<div style="transform: rotate(${lastLoc.direction || 0}deg);"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: #3b82f6;"><polygon points="3 11 22 2 13 21 11 13 3 11"/></svg></div>`,
    className: 'custom-div-icon',
    iconSize: [24, 24],
    iconAnchor: [12, 12]
  })

  L.marker([lastLoc.latitude, lastLoc.longitude], { icon: carIcon })
    .addTo(map)
    .bindPopup(`Last Update: ${new Date(lastLoc.timestamp).toLocaleString()}<br>Speed: ${lastLoc.speed || 0} km/h`)

  const points = history.map((loc: any) => [loc.latitude, loc.longitude] as L.LatLngExpression)
  L.polyline(points, { color: '#3b82f6', weight: 3, opacity: 0.6 }).addTo(map)
}

async function switchLocationView(mode: 'map' | 'list') {
  locationViewMode.value = mode
  if (mode === 'map') {
    await nextTick()
    initMap()
    await nextTick()
    map?.invalidateSize()
  }
}

function formatValue(value: any, unit: string = ''): string {
  if (value === null || value === undefined) return '—'
  return `${Number(value).toLocaleString()}${unit}`
}

function formatText(value: any): string {
  if (value === null || value === undefined || value === '') return '—'
  return String(value)
}

function formatDateTime(dateStr: string | null): string {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleString()
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString()
}

function toggleSensor(idx: number) {
  sensorConfig.value[idx].enabled = !sensorConfig.value[idx].enabled
}

function exportRawDataCSV() {
  if (!sensorData.value?.raw_data?.length) return
  
  const headers = ['Timestamp', 'Sensor', 'Value', 'Unit', 'Source']
  const rows = sensorData.value.raw_data.map((r: any) => [
    r.timestamp, r.sensor, r.value, r.unit || '', r.source || '',
  ])
  
  const csvContent = [headers, ...rows]
    .map(row => row.map((cell: any) => `"${String(cell).replace(/"/g, '""')}"`).join(','))
    .join('\n')
  
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `sensor_data_${props.vehicleId}_${timeframe.value}.csv`
  link.click()
  URL.revokeObjectURL(url)
}

function exportLocationCSV() {
  if (!sensorData.value?.location_history?.length) return
  
  const headers = ['Timestamp', 'Latitude', 'Longitude', 'Speed (km/h)', 'Direction']
  const rows = sensorData.value.location_history.map((r: any) => [
    r.timestamp, r.latitude, r.longitude, r.speed || 0, r.direction || 0,
  ])
  
  const csvContent = [headers, ...rows]
    .map(row => row.map((cell: any) => `"${cell}"`).join(','))
    .join('\n')
  
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `location_history_${props.vehicleId}_${timeframe.value}.csv`
  link.click()
  URL.revokeObjectURL(url)
}

onMounted(loadSensorData)

watch(timeframe, () => {
  loadSensorData()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Loading State -->
    <template v-if="isLoading">
      <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card v-for="i in 5" :key="i"><Skeleton height="80px" /></Card>
      </div>
      <Card><Skeleton height="400px" /></Card>
    </template>

    <template v-else-if="sensorData">
      <!-- 1. Live Status Panel -->
      <Card>
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold" style="color: var(--text-primary);">Live Status</h3>
          <div class="flex items-center gap-2">
            <component 
              :is="sensorData.has_sensors ? LucideWifi : LucideWifiOff" 
              :class="sensorData.has_sensors ? 'text-green-500' : 'text-gray-400'"
              class="size-4"
            />
            <Badge :variant="sensorData.has_sensors ? 'success' : 'default'">
              {{ sensorData.live_status?.sensor_health }}
            </Badge>
          </div>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-8 gap-4">
          <div class="p-4 rounded-xl flex flex-col items-center justify-center transition-all hover:bg-surface-secondary/50 border border-transparent hover:border-default" style="background-color: var(--bg-tertiary);">
            <LucideGauge class="size-6 mb-2" style="color: var(--text-muted);" />
            <p class="text-xl font-bold" style="color: var(--text-primary);">{{ formatValue(sensorData.live_status?.odometer, ' km') }}</p>
            <p class="text-xs uppercase tracking-wider font-semibold" style="color: var(--text-muted);">Odometer</p>
          </div>
          <div class="p-4 rounded-xl flex flex-col items-center justify-center transition-all hover:bg-surface-secondary/50 border border-transparent hover:border-default" style="background-color: var(--bg-tertiary);">
            <LucideFuel class="size-6 mb-2" style="color: var(--text-muted);" />
            <p class="text-xl font-bold" style="color: var(--text-primary);">{{ formatValue(sensorData.live_status?.fuel_level, '%') }}</p>
            <p class="text-xs uppercase tracking-wider font-semibold" style="color: var(--text-muted);">Fuel Level</p>
          </div>
          <div class="p-4 rounded-xl flex flex-col items-center justify-center transition-all hover:bg-surface-secondary/50 border border-transparent hover:border-default" style="background-color: var(--bg-tertiary);">
            <LucideDroplets class="size-6 mb-2" style="color: var(--text-muted);" />
            <p class="text-xl font-bold" style="color: var(--text-primary);">{{ sensorData.live_status?.fuel_volume_ml !== null && sensorData.live_status?.fuel_volume_ml !== undefined ? formatValue(Number(sensorData.live_status.fuel_volume_ml) / 1000, ' L') : '—' }}</p>
            <p class="text-xs uppercase tracking-wider font-semibold" style="color: var(--text-muted);">Fuel Volume</p>
          </div>
          <div class="p-4 rounded-xl flex flex-col items-center justify-center transition-all hover:bg-surface-secondary/50 border border-transparent hover:border-default" style="background-color: var(--bg-tertiary);">
            <LucideActivity class="size-6 mb-2" style="color: var(--text-muted);" />
            <p class="text-xl font-bold" style="color: var(--text-primary);">{{ formatText(sensorData.live_status?.engine_state) }}</p>
            <p class="text-xs uppercase tracking-wider font-semibold" style="color: var(--text-muted);">Engine</p>
          </div>
          <div class="p-4 rounded-xl flex flex-col items-center justify-center transition-all hover:bg-surface-secondary/50 border border-transparent hover:border-default" style="background-color: var(--bg-tertiary);">
            <LucideGauge class="size-6 mb-2" style="color: var(--text-muted);" />
            <p class="text-xl font-bold" style="color: var(--text-primary);">{{ formatValue(sensorData.live_status?.speed, ' km/h') }}</p>
            <p class="text-xs uppercase tracking-wider font-semibold" style="color: var(--text-muted);">Speed</p>
          </div>
          <div class="p-4 rounded-xl flex flex-col items-center justify-center transition-all hover:bg-surface-secondary/50 border border-transparent hover:border-default" style="background-color: var(--bg-tertiary);">
            <LucideClock class="size-6 mb-2" style="color: var(--text-muted);" />
            <p class="text-xl font-bold" style="color: var(--text-primary);">{{ formatValue(sensorData.live_status?.engine_hours, ' hrs') }}</p>
            <p class="text-xs uppercase tracking-wider font-semibold" style="color: var(--text-muted);">Engine Hours</p>
          </div>
          <div class="p-4 rounded-xl flex flex-col items-center justify-center transition-all hover:bg-surface-secondary/50 border border-transparent hover:border-default" style="background-color: var(--bg-tertiary);">
            <LucideActivity class="size-6 mb-2" style="color: var(--text-muted);" />
            <p class="text-sm font-medium" style="color: var(--text-primary);">{{ formatDateTime(sensorData.live_status?.last_sync) }}</p>
            <p class="text-xs uppercase tracking-wider font-semibold" style="color: var(--text-muted);">Last Sync</p>
          </div>
          <div class="p-4 rounded-xl flex flex-col items-center justify-center transition-all hover:bg-surface-secondary/50 border border-transparent hover:border-default" style="background-color: var(--bg-tertiary);">
            <LucideWifi class="size-6 mb-2" style="color: var(--text-muted);" />
            <p class="text-xl font-bold" :class="sensorData.has_sensors ? 'text-green-500' : ''" style="color: var(--text-primary);">
              {{ sensorData.has_sensors ? 'Connected' : 'N/A' }}
            </p>
            <p class="text-xs uppercase tracking-wider font-semibold" style="color: var(--text-muted);">Backend Link</p>
          </div>
        </div>

        <div class="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
          <div class="px-3 py-2 rounded-lg" style="background-color: var(--bg-tertiary);">
            <span style="color: var(--text-muted);">Device IMEI</span>
            <p class="font-medium mt-1" style="color: var(--text-primary);">{{ formatText(sensorData.live_status?.device_id) }}</p>
          </div>
          <div class="px-3 py-2 rounded-lg" style="background-color: var(--bg-tertiary);">
            <span style="color: var(--text-muted);">Device Name</span>
            <p class="font-medium mt-1" style="color: var(--text-primary);">{{ formatText(sensorData.live_status?.device_name) }}</p>
          </div>
          <div class="px-3 py-2 rounded-lg" style="background-color: var(--bg-tertiary);">
            <span style="color: var(--text-muted);">Tracker Status</span>
            <p class="font-medium mt-1" style="color: var(--text-primary);">{{ formatText(sensorData.live_status?.tracker_status) }}</p>
          </div>
        </div>
      </Card>

      <!-- 2. Location Tracking — Map / List Toggle -->
      <Card class="overflow-hidden" padding="none">
        <div class="p-4 flex items-center justify-between border-b" style="border-color: var(--border-color);">
          <div class="flex items-center gap-2">
            <LucideMapPin class="size-5 text-blue-500" />
            <h3 class="text-lg font-semibold" style="color: var(--text-primary);">Location History</h3>
          </div>
          <div class="flex items-center gap-2">
            <Button variant="ghost" size="sm" @click="exportLocationCSV" :disabled="!sensorData.location_history?.length">
              <LucideDownload class="size-4" />
            </Button>
            <div class="flex rounded-lg border overflow-hidden" style="border-color: var(--border-color);">
              <button
                @click="switchLocationView('map')"
                class="px-3 py-1.5 text-xs font-medium flex items-center gap-1 transition-colors"
                :style="{
                  backgroundColor: locationViewMode === 'map' ? 'var(--bg-tertiary)' : 'transparent',
                  color: locationViewMode === 'map' ? 'var(--text-primary)' : 'var(--text-muted)',
                }"
              >
                <LucideMap class="size-3.5" /> Map
              </button>
              <button
                @click="switchLocationView('list')"
                class="px-3 py-1.5 text-xs font-medium flex items-center gap-1 transition-colors"
                :style="{
                  backgroundColor: locationViewMode === 'list' ? 'var(--bg-tertiary)' : 'transparent',
                  color: locationViewMode === 'list' ? 'var(--text-primary)' : 'var(--text-muted)',
                }"
              >
                <LucideList class="size-3.5" /> List
              </button>
            </div>
          </div>
        </div>

        <!-- Map View -->
        <div v-show="locationViewMode === 'map'">
          <div 
            ref="mapContainer" 
            class="w-full h-[400px] z-0"
            style="background-color: var(--bg-tertiary);"
          >
            <div v-if="!sensorData.location_history?.length" class="flex flex-col items-center justify-center h-full text-center p-8">
              <LucideMapPin class="size-12 mb-4 animate-bounce text-ink-muted" />
              <p class="text-lg font-semibold">No location data</p>
              <p class="text-sm text-ink-muted">Historical GPS coordinates will appear here.</p>
            </div>
          </div>
        </div>

        <!-- List View -->
        <div v-if="locationViewMode === 'list'">
          <div v-if="sensorData.location_history?.length" class="max-h-[400px] overflow-auto">
            <table class="w-full text-sm">
              <thead class="sticky top-0" style="background-color: var(--bg-tertiary);">
                <tr>
                  <th class="text-left px-4 py-2 font-medium" style="color: var(--text-muted);">Timestamp</th>
                  <th class="text-left px-4 py-2 font-medium" style="color: var(--text-muted);">Latitude</th>
                  <th class="text-left px-4 py-2 font-medium" style="color: var(--text-muted);">Longitude</th>
                  <th class="text-left px-4 py-2 font-medium" style="color: var(--text-muted);">Speed</th>
                  <th class="text-left px-4 py-2 font-medium" style="color: var(--text-muted);">Direction</th>
                </tr>
              </thead>
              <tbody>
                <tr 
                  v-for="(loc, idx) in sensorData.location_history" 
                  :key="idx"
                  class="border-t hover:opacity-80 transition-opacity"
                  style="border-color: var(--border-color);"
                >
                  <td class="px-4 py-2" style="color: var(--text-primary);">{{ formatDateTime(loc.timestamp) }}</td>
                  <td class="px-4 py-2 font-mono text-xs" style="color: var(--text-secondary);">{{ loc.latitude?.toFixed(6) }}</td>
                  <td class="px-4 py-2 font-mono text-xs" style="color: var(--text-secondary);">{{ loc.longitude?.toFixed(6) }}</td>
                  <td class="px-4 py-2" style="color: var(--text-primary);">{{ loc.speed || 0 }} km/h</td>
                  <td class="px-4 py-2" style="color: var(--text-secondary);">{{ loc.direction?.toFixed(0) || '—' }}°</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="flex flex-col items-center justify-center h-[200px] text-center p-8">
            <LucideMapPin class="size-12 mb-4 text-ink-muted" />
            <p class="text-lg font-semibold">No location data</p>
          </div>
        </div>
      </Card>

      <!-- 3. Fuel Refueling Efficiency Analysis -->
      <Card v-if="sensorData.fuel_analysis">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-2">
            <LucideDroplets class="size-5 text-blue-500" />
            <h3 class="text-lg font-semibold" style="color: var(--text-primary);">Refueling Efficiency</h3>
          </div>
          <div class="flex gap-1">
            <button
              v-for="tf in timeframes"
              :key="tf.id"
              @click="timeframe = tf.id"
              class="px-3 py-1 text-sm rounded-lg transition-colors border"
              :style="{
                backgroundColor: timeframe === tf.id ? 'var(--bg-tertiary)' : 'transparent',
                borderColor: timeframe === tf.id ? 'var(--border-color)' : 'transparent',
                color: timeframe === tf.id ? 'var(--text-primary)' : 'var(--text-muted)',
              }"
            >
              {{ tf.label }}
            </button>
          </div>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          <div class="p-3 rounded-xl text-center" style="background-color: var(--bg-tertiary);">
            <p class="text-2xl font-bold" style="color: var(--text-primary);">{{ sensorData.fuel_analysis.summary.refuel_count }}</p>
            <p class="text-xs" style="color: var(--text-muted);">Refuels</p>
          </div>
          <div class="p-3 rounded-xl text-center" style="background-color: var(--bg-tertiary);">
            <p class="text-2xl font-bold" style="color: var(--text-primary);">{{ sensorData.fuel_analysis.summary.avg_refuel_level }}%</p>
            <p class="text-xs" style="color: var(--text-muted);">Avg Trigger Level</p>
          </div>
          <div class="p-3 rounded-xl text-center" style="background-color: var(--bg-tertiary);">
            <p class="text-2xl font-bold" :class="sensorData.fuel_analysis.summary.lowest_refuel_level < 15 ? 'text-red-500' : ''" style="color: var(--text-primary);">{{ sensorData.fuel_analysis.summary.lowest_refuel_level }}%</p>
            <p class="text-xs" style="color: var(--text-muted);">Lowest Trigger</p>
          </div>
          <div class="p-3 rounded-xl text-center" style="background-color: var(--bg-tertiary);">
            <p class="text-2xl font-bold text-amber-500">{{ sensorData.fuel_analysis.summary.pct_below_25 }}%</p>
            <p class="text-xs" style="color: var(--text-muted);">Refueled &lt; 25%</p>
          </div>
          <div class="p-3 rounded-xl text-center" style="background-color: var(--bg-tertiary);">
            <p class="text-2xl font-bold text-green-500">{{ sensorData.fuel_analysis.summary.pct_above_50 }}%</p>
            <p class="text-xs" style="color: var(--text-muted);">Refueled &gt; 50%</p>
          </div>
        </div>

        <div v-if="sensorData.fuel_analysis.refuel_events?.length">
          <h4 class="text-sm font-semibold mb-3" style="color: var(--text-muted);">Recent Refueling Events</h4>
          <div class="space-y-2">
            <div 
              v-for="(event, idx) in sensorData.fuel_analysis.refuel_events.slice(0, 5)" 
              :key="idx"
              class="flex items-center justify-between p-3 rounded-xl border border-default"
              style="background-color: var(--bg-tertiary);"
            >
              <div class="flex items-center gap-3">
                <LucideFuel class="size-4 text-blue-500" />
                <div>
                  <p class="text-sm font-medium" style="color: var(--text-primary);">{{ formatDate(event.timestamp) }}</p>
                  <p class="text-xs" style="color: var(--text-muted);">{{ formatDateTime(event.timestamp) }}</p>
                </div>
              </div>
              <div class="flex items-center gap-4">
                <div class="text-right">
                  <p class="text-xs" style="color: var(--text-muted);">Before</p>
                  <p class="text-sm font-bold" :class="event.before_level < 25 ? 'text-red-500' : ''" style="color: var(--text-primary);">{{ event.before_level }}%</p>
                </div>
                <span class="text-lg" style="color: var(--text-muted);">→</span>
                <div class="text-right">
                  <p class="text-xs" style="color: var(--text-muted);">After</p>
                  <p class="text-sm font-bold text-green-500">{{ event.after_level }}%</p>
                </div>
                <Badge variant="success" size="sm">+{{ event.delta }}%</Badge>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="text-center py-8">
          <LucideFuel class="size-8 mx-auto mb-2" style="color: var(--text-muted);" />
          <p class="text-sm" style="color: var(--text-muted);">No refueling events detected in this period</p>
        </div>
      </Card>

      <!-- 4. Alerts & Configure -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card class="md:col-span-2">
          <h3 class="text-lg font-semibold mb-4" style="color: var(--text-primary);">
            <LucideAlertTriangle class="inline size-5 mr-2 text-amber-500" />
            Anomalies &amp; Critical Events
          </h3>
          
          <div v-if="sensorData.alerts?.length" class="space-y-3">
            <div 
              v-for="(alert, idx) in sensorData.alerts" 
              :key="idx"
              class="flex items-center justify-between p-4 rounded-xl border border-default transition-all hover:bg-surface-secondary"
              style="background-color: var(--bg-tertiary);"
            >
              <div class="flex items-center gap-3">
                <div class="size-10 rounded-full flex items-center justify-center bg-red-100 dark:bg-red-900/30 text-red-600">
                  <LucideAlertTriangle class="size-5" />
                </div>
                <div>
                  <p class="text-sm font-bold" style="color: var(--text-primary);">{{ alert.type }}</p>
                  <p class="text-xs" style="color: var(--text-muted);">{{ formatDateTime(alert.timestamp) }}</p>
                </div>
              </div>
              <div class="text-right">
                <p class="text-sm font-bold mb-1" style="color: var(--text-primary);">{{ alert.value }}</p>
                <Badge variant="danger" size="sm">{{ alert.severity }}</Badge>
              </div>
            </div>
          </div>
          <div v-else class="flex flex-col items-center justify-center py-12 text-center">
            <LucideCheck class="size-12 mb-4 text-green-500" />
            <p class="font-semibold text-lg">System Healthy</p>
            <p class="text-sm text-ink-muted">No issues detected in the last {{ timeframe }}.</p>
          </div>
        </Card>

        <Card class="bg-gradient-to-br from-indigo-500 to-purple-600 text-white border-none shadow-xl">
          <div class="flex flex-col h-full justify-between">
            <div>
              <LucideSettings class="size-10 mb-6 opacity-80" />
              <h3 class="text-2xl font-bold mb-2">Sensor Config</h3>
              <p class="text-sm opacity-90 leading-relaxed mb-8">
                Manage telemetry hardware settings, sampling rates, and alert thresholds.
              </p>
            </div>
            <Button 
              variant="secondary" 
              class="w-full bg-white/20 hover:bg-white/30 border-none text-white backdrop-blur-md"
              @click="showConfigureModal = true"
            >
              Configure Sensors
            </Button>
          </div>
        </Card>
      </div>

      <!-- 5. Raw Sensor Data Table -->
      <Card padding="none">
        <div class="p-4 flex items-center justify-between border-b" style="border-color: var(--border-color);">
          <div class="flex items-center gap-2">
            <LucideTable2 class="size-5" style="color: var(--text-muted);" />
            <h3 class="text-lg font-semibold" style="color: var(--text-primary);">Raw Sensor Data</h3>
            <Badge v-if="sensorData.raw_data?.length" variant="default" size="sm">{{ sensorData.raw_data.length }} records</Badge>
          </div>
          <div class="flex items-center gap-2">
            <Button variant="outline" size="sm" @click="exportRawDataCSV" :disabled="!sensorData.raw_data?.length">
              <LucideDownload class="size-4 mr-1" />
              Export CSV
            </Button>
            <Button variant="ghost" size="sm" @click="showRawData = !showRawData">
              {{ showRawData ? 'Hide' : 'Show' }}
            </Button>
          </div>
        </div>

        <div v-if="showRawData && sensorData.raw_data?.length" class="max-h-[400px] overflow-auto">
          <table class="w-full text-sm">
            <thead class="sticky top-0" style="background-color: var(--bg-tertiary);">
              <tr>
                <th class="text-left px-4 py-2 font-medium" style="color: var(--text-muted);">Timestamp</th>
                <th class="text-left px-4 py-2 font-medium" style="color: var(--text-muted);">Sensor</th>
                <th class="text-left px-4 py-2 font-medium" style="color: var(--text-muted);">Value</th>
                <th class="text-left px-4 py-2 font-medium" style="color: var(--text-muted);">Unit</th>
                <th class="text-left px-4 py-2 font-medium" style="color: var(--text-muted);">Source</th>
              </tr>
            </thead>
            <tbody>
              <tr 
                v-for="(row, idx) in sensorData.raw_data" 
                :key="idx"
                class="border-t hover:opacity-80 transition-opacity"
                style="border-color: var(--border-color);"
              >
                <td class="px-4 py-2 whitespace-nowrap" style="color: var(--text-primary);">{{ formatDateTime(row.timestamp) }}</td>
                <td class="px-4 py-2">
                  <Badge variant="default" size="sm">{{ row.sensor }}</Badge>
                </td>
                <td class="px-4 py-2 font-mono" style="color: var(--text-primary);">{{ row.value }}</td>
                <td class="px-4 py-2" style="color: var(--text-muted);">{{ row.unit || '—' }}</td>
                <td class="px-4 py-2 text-xs" style="color: var(--text-muted);">{{ row.source || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else-if="showRawData" class="p-8 text-center">
          <p class="text-sm" style="color: var(--text-muted);">No sensor data available for this period</p>
        </div>
      </Card>

      <!-- Configure Modal -->
      <div v-if="showConfigureModal" class="fixed inset-0 z-[100] flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="showConfigureModal = false"></div>
        <Card class="relative w-full max-w-md z-10 shadow-2xl" padding="none">
          <div class="p-6 border-b flex items-center justify-between" style="border-color: var(--border-color);">
            <h3 class="text-xl font-bold">Configure Telemetry</h3>
            <button @click="showConfigureModal = false" class="p-1 hover:bg-surface-secondary rounded-full transition-colors">
              <LucideX class="size-5" />
            </button>
          </div>
          <div class="p-6 space-y-6">
            <div class="space-y-4">
              <div 
                v-for="(sensor, idx) in sensorConfig" 
                :key="sensor.id"
                class="flex items-center justify-between p-3 rounded-xl border border-default transition-all hover:border-accent"
                :class="sensor.enabled ? 'bg-accent/5' : 'opacity-60'"
              >
                <div class="flex flex-col">
                  <span class="font-bold text-sm">{{ sensor.label }}</span>
                  <span class="text-[10px] uppercase tracking-widest text-ink-muted font-bold">
                    {{ sensor.enabled ? 'Currently Polling' : 'Disabled' }}
                  </span>
                </div>
                <button 
                  @click="toggleSensor(idx)"
                  class="w-12 h-6 rounded-full transition-colors relative"
                  :class="sensor.enabled ? 'bg-accent' : 'bg-surface-tertiary'"
                >
                  <div 
                    class="absolute top-1 size-4 bg-white rounded-full transition-transform"
                    :class="sensor.enabled ? 'left-7' : 'left-1'"
                  ></div>
                </button>
              </div>
            </div>
            
            <Button variant="primary" class="w-full h-12 text-lg font-bold" @click="showConfigureModal = false">
              Save Configuration
            </Button>
          </div>
        </Card>
      </div>
    </template>
  </div>
</template>

<style scoped>
.leaflet-container {
  font-family: inherit;
}
.custom-div-icon {
  background: none;
  border: none;
}
</style>
