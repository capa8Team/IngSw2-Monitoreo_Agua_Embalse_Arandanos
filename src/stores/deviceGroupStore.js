import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getActiveOrganizationId, getApiAuthHeaders } from '../services/apiContext.js'

export const useDeviceGroupStore = defineStore('deviceGroup', () => {
  const groups = ref([])
  const loading = ref(false)
  const error = ref(null)

  const apiBase = () => `${import.meta.env.VITE_API_URL || ''}/api/device-groups`

  const fetchGroups = async () => {
    loading.value = true
    error.value = null
    try {
      const response = await fetch(apiBase(), { headers: getApiAuthHeaders() })
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      const data = await response.json()
      groups.value = Array.isArray(data) ? data : []
      return groups.value
    } catch (err) {
      error.value = err.message
      console.error('[DeviceGroupStore] Error fetching groups:', err)
      return groups.value
    } finally {
      loading.value = false
    }
  }

  const createGroup = async (groupData) => {
    loading.value = true
    error.value = null
    try {
      const response = await fetch(apiBase(), {
        method: 'POST',
        headers: getApiAuthHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify(groupData),
      })
      if (!response.ok) {
        const errData = await response.json().catch(() => ({}))
        throw new Error(errData.detail || `HTTP ${response.status}`)
      }
      const created = await response.json()
      groups.value.push(created)
      return created
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const updateGroup = async (groupId, updateData) => {
    loading.value = true
    error.value = null
    try {
      const response = await fetch(`${apiBase()}/${groupId}`, {
        method: 'PUT',
        headers: getApiAuthHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify(updateData),
      })
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      const updated = await response.json()
      const index = groups.value.findIndex((g) => g.id === groupId)
      if (index !== -1) groups.value[index] = updated
      return updated
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const getGroupById = (groupId) => groups.value.find((g) => g.id === groupId) || null

  const reset = () => {
    groups.value = []
    loading.value = false
    error.value = null
  }

  return {
    groups,
    loading,
    error,
    fetchGroups,
    createGroup,
    updateGroup,
    getGroupById,
    reset,
  }
})
