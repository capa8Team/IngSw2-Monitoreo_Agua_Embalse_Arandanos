<template>
  <div class="battery-indicator" :title="`Batería: ${batteryLevel}%`">
    <svg 
      viewBox="0 0 24 24" 
      width="36" 
      height="36" 
      fill="none" 
      stroke="currentColor" 
      stroke-width="2" 
      stroke-linecap="round" 
      stroke-linejoin="round"
      :class="batteryClass"
    >
      <!-- Cuerpo de la batería -->
      <rect x="1" y="6" width="18" height="12" rx="2" ry="2" />
      <!-- Terminal de la batería -->
      <line x1="23" y1="9" x2="23" y2="15" />
      <!-- Nivel de carga interno -->
      <rect 
        x="3" 
        y="8" 
        :width="batteryFillWidth" 
        height="8" 
        rx="1" 
        ry="1" 
        fill="currentColor"
        class="battery-fill"
      />
    </svg>
    <span class="battery-text">{{ batteryLevel }}%</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  level: {
    type: Number,
    default: 100,
    validator: (value) => value >= 0 && value <= 100
  },
  size: {
    type: String,
    default: 'small', // 'small', 'medium', 'large'
    validator: (value) => ['small', 'medium', 'large'].includes(value)
  },
  showText: {
    type: Boolean,
    default: true
  }
})

const batteryLevel = computed(() => Math.round(Math.min(100, Math.max(0, props.level))))

const batteryFillWidth = computed(() => {
  // El ancho máximo de la barra de carga es ~14 (desde x=3 hasta x=17)
  return (batteryLevel.value / 100) * 14
})

const batteryClass = computed(() => {
  const level = batteryLevel.value
  
  if (level > 60) return 'battery-full'
  if (level > 30) return 'battery-medium'
  if (level > 10) return 'battery-low'
  return 'battery-critical'
})
</script>

<style scoped>
.battery-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
}

svg {
  flex-shrink: 0;
}

.battery-fill {
  transition: all 0.3s ease;
}

.battery-full {
  color: #4ade80; /* Verde */
}

.battery-medium {
  color: #eab308; /* Amarillo */
}

.battery-low {
  color: #f97316; /* Naranja */
}

.battery-critical {
  color: #ef4444; /* Rojo */
}

.battery-text {
  color: inherit;
  white-space: nowrap;
}

/* Modo oscuro */
html[data-theme='dark'] .battery-indicator {
  color: inherit;
}

html[data-theme='dark'] .battery-full {
  color: #86efac;
}

html[data-theme='dark'] .battery-medium {
  color: #facc15;
}

html[data-theme='dark'] .battery-low {
  color: #fb923c;
}

html[data-theme='dark'] .battery-critical {
  color: #fca5a5;
}
</style>
