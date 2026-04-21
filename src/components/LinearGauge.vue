<template>
  <div class="linear-gauge-wrapper">
    <div class="gauge-title">{{ sensorName }}</div>
    <svg
      :width="width"
      :height="height"
      :viewBox="`0 0 ${width} ${height}`"
      class="linear-gauge"
    >
      <!-- Background plate -->
      <defs>
        <linearGradient id="plateGradient" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" :stop-color="colorPlate" />
          <stop offset="100%" :stop-color="colorPlateEnd" />
        </linearGradient>
      </defs>
      
      <rect
        x="20"
        y="20"
        :width="width - 40"
        :height="height - 40"
        rx="10"
        ry="10"
        fill="url(#plateGradient)"
      />

      <!-- Highlights (zones) -->
      <g class="highlights">
        <rect
          v-for="(highlight, index) in highlights"
          :key="`highlight-${index}`"
          :x="getHighlightX(highlight.from)"
          :y="20"
          :width="getHighlightWidth(highlight.from, highlight.to)"
          :height="height - 40"
          :fill="highlight.color"
          rx="10"
          ry="10"
        />
      </g>

      <!-- Scale background -->
      <rect
        :x="scaleStartX"
        :y="scaleY - 15"
        :width="scaleWidth"
        :height="30"
        fill="#fff"
        opacity="0.1"
        rx="5"
      />

      <!-- Minor ticks -->
      <g class="minor-ticks" :stroke="colorMinorTicks" :stroke-width="1">
        <line
          v-for="i in totalMinorTicks"
          :key="`minor-${i}`"
          :x1="getMinorTickX(i)"
          :y1="scaleY - ticksWidthMinor / 2"
          :x2="getMinorTickX(i)"
          :y2="scaleY + ticksWidthMinor / 2"
        />
      </g>

      <!-- Major ticks -->
      <g class="major-ticks" :stroke="colorMajorTicks" :stroke-width="2">
        <line
          v-for="(tick, index) in majorTicks"
          :key="`major-${index}`"
          :x1="getXFromValue(tick)"
          :y1="scaleY - ticksWidth / 2"
          :x2="getXFromValue(tick)"
          :y2="scaleY + ticksWidth / 2"
        />
      </g>

      <!-- Numbers -->
      <g class="numbers" :fill="colorNumbers" font-size="12" text-anchor="middle">
        <text
          v-for="(tick, index) in majorTicks"
          :key="`num-${index}`"
          :x="getXFromValue(tick)"
          :y="scaleY + ticksWidth + 20"
        >
          {{ tick }}
        </text>
      </g>

      <!-- Needle (arrow) -->
      <g :transform="`translate(${needleX}, ${scaleY})`">
        <!-- Needle arrow -->
        <polygon
          :points="`0,-10 -5,0 5,0`"
          :fill="colorNeedle"
        />
        <!-- Needle line -->
        <line
          x1="0"
          y1="0"
          x2="0"
          y2="50"
          :stroke="colorNeedle"
          :stroke-width="needleWidth"
          stroke-linecap="round"
        />
      </g>

      <!-- Units label -->
      <text
        :x="width - 30"
        :y="30"
        :fill="colorUnits"
        font-size="14"
        text-anchor="end"
      >
        {{ unit }}
      </text>

      <!-- Current value display -->
      <text
        :x="width / 2"
        :y="height - 15"
        :fill="valueDisplayFill"
        font-size="18"
        font-weight="bold"
        text-anchor="middle"
      >
        {{ value.toFixed(2) }}
      </text>
    </svg>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onBeforeUnmount } from 'vue'

const valueDisplayFill = ref('#111827')

function syncValueFill() {
  const dark = document.documentElement.getAttribute('data-theme') === 'dark'
  valueDisplayFill.value = dark ? '#f1f5f9' : '#111827'
}

onMounted(() => {
  syncValueFill()
  window.addEventListener('embalse-theme-change', syncValueFill)
})

onBeforeUnmount(() => {
  window.removeEventListener('embalse-theme-change', syncValueFill)
})

const props = defineProps({
  sensorName: {
    type: String,
    default: 'Sensor'
  },
  value: {
    type: Number,
    required: true
  },
  minValue: {
    type: Number,
    default: -50
  },
  maxValue: {
    type: Number,
    default: 50
  },
  unit: {
    type: String,
    default: '°C'
  },
  width: {
    type: Number,
    default: 400
  },
  height: {
    type: Number,
    default: 150
  },
  majorTicks: {
    type: Array,
    default: () => [-50, -40, -30, -20, -10, 0, 10, 20, 30, 40, 50]
  },
  minorTicks: {
    type: Number,
    default: 5
  },
  highlights: {
    type: Array,
    default: () => [
      { from: -50, to: 0, color: 'rgba(0, 0, 255, 0.2)' },
      { from: 0, to: 50, color: 'rgba(255, 0, 0, 0.2)' }
    ]
  },
  colorMajorTicks: {
    type: String,
    default: '#666'
  },
  colorMinorTicks: {
    type: String,
    default: '#999'
  },
  colorNumbers: {
    type: String,
    default: '#333'
  },
  colorUnits: {
    type: String,
    default: '#666'
  },
  colorPlate: {
    type: String,
    default: '#f5f5f5'
  },
  colorPlateEnd: {
    type: String,
    default: '#f5f5f5'
  },
  colorNeedle: {
    type: String,
    default: '#222'
  },
  ticksWidth: {
    type: Number,
    default: 15
  },
  ticksWidthMinor: {
    type: Number,
    default: 7.5
  },
  needleWidth: {
    type: Number,
    default: 3
  }
})

// Dimensions
const scaleStartX = computed(() => 60)
const scaleEndX = computed(() => props.width - 60)
const scaleWidth = computed(() => scaleEndX.value - scaleStartX.value)
const scaleY = computed(() => props.height / 2 - 20)

// Calculate total minor ticks
const totalMinorTicks = computed(() => {
  if (props.majorTicks.length < 2) return 0
  const majorTickCount = props.majorTicks.length - 1
  return majorTickCount * props.minorTicks
})

// Get X position from value
const getXFromValue = (val) => {
  const range = props.maxValue - props.minValue
  const position = (val - props.minValue) / range
  return scaleStartX.value + position * scaleWidth.value
}

// Get major tick X position
const getXFromMajorTickIndex = (index) => {
  const tickValue = props.majorTicks[index]
  return getXFromValue(tickValue)
}

// Get minor tick X position
const getMinorTickX = (tickIndex) => {
  const majorTickCount = props.majorTicks.length - 1
  const majorTickIndexFloat = (tickIndex - 1) / props.minorTicks
  
  const majorIndex = Math.floor(majorTickIndexFloat)
  const minorIndex = (tickIndex - 1) % props.minorTicks + 1
  
  if (majorIndex >= majorTickCount) return scaleEndX.value
  
  const tick1 = props.majorTicks[majorIndex]
  const tick2 = props.majorTicks[majorIndex + 1]
  
  const minorValue = tick1 + ((tick2 - tick1) / (props.minorTicks + 1)) * minorIndex
  return getXFromValue(minorValue)
}

// Get highlight rect X position (adjusted to fill the plate completely)
const getHighlightX = (fromValue) => {
  const range = props.maxValue - props.minValue
  const position = (fromValue - props.minValue) / range
  return 20 + position * (props.width - 40)
}

// Get highlight rect width
const getHighlightWidth = (fromValue, toValue) => {
  const range = props.maxValue - props.minValue
  const fromPos = (fromValue - props.minValue) / range
  const toPos = (toValue - props.minValue) / range
  return (toPos - fromPos) * (props.width - 40)
}

// Needle position
const clampedValue = computed(() => {
  return Math.max(props.minValue, Math.min(props.maxValue, props.value))
})

const needleX = computed(() => {
  return getXFromValue(clampedValue.value)
})
</script>

<style scoped>
.linear-gauge-wrapper {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.gauge-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  text-align: center;
}

.linear-gauge {
  filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.15));
}
</style>
