<template>
  <div v-if="visible" class="org-switcher">
    <label class="org-switcher-label" for="org-select">Organización</label>
    <select
      id="org-select"
      class="org-switcher-select"
      :value="activeOrganizationId"
      :disabled="switching"
      @change="onChange"
    >
      <option
        v-for="org in organizations"
        :key="org.id"
        :value="org.id"
      >
        {{ org.name }}
      </option>
    </select>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import {
  getActiveOrganizationId,
  getStoredOrganizations,
  shouldShowOrganizationSwitcher,
} from '../services/apiContext.js'
import { switchOrganization } from '../services/sessionAuth.js'

const emit = defineEmits(['organization-changed'])

const organizations = computed(() => getStoredOrganizations())
const activeOrganizationId = computed(() => getActiveOrganizationId())
const visible = computed(() => shouldShowOrganizationSwitcher())
const switching = ref(false)

async function onChange(event) {
  const orgId = event.target.value
  if (!orgId || orgId === activeOrganizationId.value) return
  switching.value = true
  try {
    await switchOrganization(orgId)
    emit('organization-changed', orgId)
  } catch (err) {
    console.error('[OrganizationSwitcher]', err)
    window.alert(err?.message || 'No se pudo cambiar de organización')
    event.target.value = activeOrganizationId.value
  } finally {
    switching.value = false
  }
}
</script>

<style scoped>
.org-switcher {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  margin-right: 0.5rem;
}

.org-switcher-label {
  font-size: 0.8rem;
  color: var(--text-secondary, #64748b);
  white-space: nowrap;
}

.org-switcher-select {
  min-width: 10rem;
  padding: 0.35rem 0.5rem;
  border-radius: 6px;
  border: 1px solid var(--border-color, #cbd5e1);
  background: var(--bg-secondary, #fff);
  color: var(--text-primary, #0f172a);
  font-size: 0.85rem;
}
</style>
