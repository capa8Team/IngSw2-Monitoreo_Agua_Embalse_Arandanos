<template>
  <div v-if="currentView === 'devices'" class="devices-view">
    <DeviceList
      :devices-data="devices"
      :is-admin="isAdmin"
      @select-device="selectDevice"
      @open-history="openHistory"
      @open-user-management="openUserManagementView"
      @logout="handleLogout"
      @add-device="openAddDeviceFromDeviceList"
    />
  </div>

  <div v-else-if="currentView === 'dashboard'" class="dashboard">
    <header class="dashboard-header">
      <div class="header-content">
        <ThemeToggleButton />
        <button class="back-btn" @click="goBack" title="Volver a dispositivos">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
            <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
          </svg>
        </button>
        <div>
          <h1 class="header-title">{{ selectedDevice.name }}</h1>
          <p class="header-subtitle">{{ selectedDevice.model }}</p>
        </div>
      </div>
      <div class="header-status">
        <div class="status-indicator" :class="`indicator-${overallStatus}`"></div>
        <span class="status-label">{{ overallStatusText }}</span>
      </div>
      <div v-if="isAdmin" class="header-center admin-top-actions">
        <button class="admin-nav-btn" @click="openAlertConfigView">Configuracion rango alertas</button>
      </div>
      <div class="header-right">
        <div class="data-source-badge" :class="`source-${selectedDevice.dataSource}`">
          <span v-if="selectedDevice.dataSource === 'real'">📊 Datos Reales</span>
          <span v-else-if="selectedDevice.dataSource === 'simulated'">⚙️ Datos Simulados</span>
          <span v-else>❓ Fuente Desconocida</span>
        </div>
        <button class="history-btn" type="button" @click="openHistory" title="Ver datos históricos">Históricos</button>
        <button class="logout-btn" type="button" @click="handleLogout">Cerrar sesión</button>
      </div>
    </header>

    <main class="dashboard-content">
      <section class="info-section">
        <h2 class="section-title">Información del Sistema</h2>
        <div class="info-grid">
          <div class="info-card">
            <div class="info-card-label">Sensores Activos</div>
            <div class="info-card-value">3/3</div>
          </div>
          <div class="info-card">
            <div class="info-card-label">Última Sincronización</div>
            <div class="info-card-value">{{ lastSync }}</div>
          </div>
          <div class="info-card">
            <div class="info-card-label">Conexión Arduino</div>
            <div class="info-card-value" :class="selectedDevice.status === 'connected' ? 'connected' : 'disconnected'">
              {{ selectedDevice.status === 'connected' ? 'Conectado' : 'Desconectado' }}
            </div>
          </div>
          <div class="info-card">
            <div class="info-card-label">Estado de Batería</div>
            <div class="info-card-value battery-card">
              <BatteryIndicator 
                :level="batteryLevel" 
                size="medium" 
                :show-text="true"
              />
            </div>
          </div>
          <div class="info-card">
            <div class="info-card-label">Rol de Usuario</div>
            <div class="info-card-value" :class="isAdmin ? 'admin-role' : 'user-role'">
              {{ isAdmin ? '👨‍💼 Administrador' : '👤 Empleado' }}
            </div>
          </div>
        </div>
      </section>

      <div class="sensors-grid">
        <SensorCard
          sensor-name="pH"
          :value="sensors.ph.value"
          :min="sensorThresholds.ph.dangerMin"
          :max="sensorThresholds.ph.dangerMaxSup"
          :thresholds="sensorThresholds.ph"
          unit="pH"
          :last-updated="lastSync"
        />
        <SensorCard
          sensor-name="Temperatura"
          :value="sensors.temperature.value"
          :min="sensorThresholds.temperature.dangerMin"
          :max="sensorThresholds.temperature.dangerMaxSup"
          :thresholds="sensorThresholds.temperature"
          unit="°C"
          :last-updated="lastSync"
        />
        <SensorCard
          sensor-name="Conductividad Eléctrica"
          :value="sensors.conductivity.value"
          :min="sensorThresholds.conductivity.dangerMin"
          :max="sensorThresholds.conductivity.dangerMaxSup"
          :thresholds="sensorThresholds.conductivity"
          unit="µS/cm"
          :last-updated="lastSync"
        />
      </div>

      <section class="alerts-section">
        <div class="alerts-header">
          <h2 class="section-title">Tabla de Alertas (día actual)</h2>
          <span class="alerts-count">Mostrando {{ visibleAlerts.length }} de {{ todayAlerts.length }}</span>
        </div>
        <div class="table-wrapper" :class="{ expanded: showAllTodayAlerts }">
          <div class="table-wrap">
            <table class="alerts-table">
              <thead>
                <tr>
                  <th>Dispositivo</th>
                  <th>pH</th>
                  <th>Temperatura</th>
                  <th>Conductividad</th>
                  <th>Estado de carga</th>
                  <th>Fecha</th>
                  <th>Hora</th>
                  <th>Telegram</th>
                  <th>Email</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="alert in visibleAlerts" :key="alert.id">
                  <td>{{ alert.deviceName }}</td>
                  <td>{{ alert.ph }}</td>
                  <td>{{ alert.temperature }}</td>
                  <td>{{ alert.conductivity }}</td>
                  <td>{{ alert.battery }}%</td>
                  <td>{{ alert.date }}</td>
                  <td>{{ alert.time }}</td>
                  <td>{{ alert.telegramStatus }}</td>
                  <td>{{ alert.emailStatus }}</td>
                </tr>
                <tr v-if="visibleAlerts.length === 0">
                  <td colspan="9" class="empty-cell">Sin alertas registradas para hoy.</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-if="todayAlerts.length > ALERT_TABLE_LIMIT" class="table-footer">
            <button
              class="see-more-btn"
              @click="showAllTodayAlerts = !showAllTodayAlerts"
            >
              {{ showAllTodayAlerts ? 'Ver menos' : 'Mostrar más' }}
            </button>
          </div>
        </div>
      </section>
    </main>
  </div>

  <div v-else-if="currentView === 'admin-alerts'" class="dashboard">
    <header class="dashboard-header">
      <div class="header-content">
        <ThemeToggleButton />
        <button class="back-btn" @click="goBack" title="Volver">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
            <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
          </svg>
        </button>
        <div>
          <h1 class="header-title">Configuracion rango alertas</h1>
          <p class="header-subtitle">Define umbrales por sensor para dashboard y alertas</p>
        </div>
      </div>
      <div class="header-center admin-top-actions">
        <button class="admin-nav-btn active">Configuracion rango alertas</button>
      </div>
      <div class="header-right">
        <div class="data-source-badge" :class="`source-${selectedDevice.dataSource}`">
          <span v-if="selectedDevice.dataSource === 'real'">📊 Datos Reales</span>
          <span v-else-if="selectedDevice.dataSource === 'simulated'">⚙️ Datos Simulados</span>
          <span v-else>❓ Fuente Desconocida</span>
        </div>
        <button class="logout-btn" type="button" @click="handleLogout">Cerrar sesión</button>
      </div>
    </header>

    <main class="dashboard-content">
      <section class="alerts-config-section">
        <div class="alerts-header">
          <h2 class="section-title">Configuracion de rangos por sensor</h2>
          <p class="section-subtitle">Define 3 valores clave: mínimo, central (óptimo) y máximo. Los rangos se calculan automáticamente.</p>
        </div>

        <div class="alerts-config-grid">
          <!-- pH -->
          <div class="alert-config-card">
            <h3>🔬 pH</h3>
            <p class="card-instructions">Proporciona los 3 valores de interés</p>

            <div class="config-group">
              <label>Valor Mínimo (escala):</label>
              <input v-model.number="editingLimits.ph.min_value" type="number" step="0.1" />
              <span class="help-text">Mínimo absoluto de la escala de pH</span>
            </div>
            <div class="config-group">
              <label>Valor Central/Óptimo:</label>
              <input v-model.number="editingLimits.ph.central_value" type="number" step="0.1" />
              <span class="help-text">Valor ideal u óptimo para pH</span>
            </div>
            <div class="config-group">
              <label>Valor Máximo (escala):</label>
              <input v-model.number="editingLimits.ph.max_value" type="number" step="0.1" />
              <span class="help-text">Máximo absoluto de la escala de pH</span>
            </div>

            <div class="ranges-preview">
              <h5>Rangos Calculados Automáticamente:</h5>
              <div class="range-row danger">🔴 Peligroso Inf: {{ editingRanges.ph.danger_min.toFixed(2) }} — {{ editingRanges.ph.danger_max.toFixed(2) }}</div>
              <div class="range-row warning">🟠 Advertencia Inf: {{ editingRanges.ph.warning_min.toFixed(2) }} — {{ editingRanges.ph.warning_max.toFixed(2) }}</div>
              <div class="range-row safe">🟢 Seguro: {{ editingRanges.ph.safe_min.toFixed(2) }} — {{ editingRanges.ph.safe_max.toFixed(2) }}</div>
              <div class="range-row warning">🟠 Advertencia Sup: {{ editingRanges.ph.warning_min_sup.toFixed(2) }} — {{ editingRanges.ph.warning_max_sup.toFixed(2) }}</div>
              <div class="range-row danger">🔴 Peligroso Sup: {{ editingRanges.ph.danger_min_sup.toFixed(2) }} — {{ editingRanges.ph.danger_max_sup.toFixed(2) }}</div>
            </div>

            <button class="save-config-btn" @click="saveAlertConfig('ph')">Guardar pH</button>
          </div>

          <!-- Temperatura -->
          <div class="alert-config-card">
            <h3>🌡️ Temperatura (°C)</h3>
            <p class="card-instructions">Proporciona los 3 valores de interés</p>

            <div class="config-group">
              <label>Valor Mínimo (escala):</label>
              <input v-model.number="editingLimits.temperature.min_value" type="number" step="1" />
              <span class="help-text">Mínimo absoluto de temperatura</span>
            </div>
            <div class="config-group">
              <label>Valor Central/Óptimo:</label>
              <input v-model.number="editingLimits.temperature.central_value" type="number" step="1" />
              <span class="help-text">Temperatura ideal u óptima</span>
            </div>
            <div class="config-group">
              <label>Valor Máximo (escala):</label>
              <input v-model.number="editingLimits.temperature.max_value" type="number" step="1" />
              <span class="help-text">Máximo absoluto de temperatura</span>
            </div>

            <div class="ranges-preview">
              <h5>Rangos Calculados Automáticamente:</h5>
              <div class="range-row danger">🔴 Peligroso Inf: {{ editingRanges.temperature.danger_min.toFixed(1) }} — {{ editingRanges.temperature.danger_max.toFixed(1) }}</div>
              <div class="range-row warning">🟠 Advertencia Inf: {{ editingRanges.temperature.warning_min.toFixed(1) }} — {{ editingRanges.temperature.warning_max.toFixed(1) }}</div>
              <div class="range-row safe">🟢 Seguro: {{ editingRanges.temperature.safe_min.toFixed(1) }} — {{ editingRanges.temperature.safe_max.toFixed(1) }}</div>
              <div class="range-row warning">🟠 Advertencia Sup: {{ editingRanges.temperature.warning_min_sup.toFixed(1) }} — {{ editingRanges.temperature.warning_max_sup.toFixed(1) }}</div>
              <div class="range-row danger">🔴 Peligroso Sup: {{ editingRanges.temperature.danger_min_sup.toFixed(1) }} — {{ editingRanges.temperature.danger_max_sup.toFixed(1) }}</div>
            </div>

            <button class="save-config-btn" @click="saveAlertConfig('temperature')">Guardar Temperatura</button>
          </div>

          <!-- Conductividad -->
          <div class="alert-config-card">
            <h3>⚡ Conductividad (µS/cm)</h3>
            <p class="card-instructions">Proporciona los 3 valores de interés</p>

            <div class="config-group">
              <label>Valor Mínimo (escala):</label>
              <input v-model.number="editingLimits.conductivity.min_value" type="number" step="10" />
              <span class="help-text">Mínimo absoluto de conductividad</span>
            </div>
            <div class="config-group">
              <label>Valor Central/Óptimo:</label>
              <input v-model.number="editingLimits.conductivity.central_value" type="number" step="10" />
              <span class="help-text">Conductividad ideal u óptima</span>
            </div>
            <div class="config-group">
              <label>Valor Máximo (escala):</label>
              <input v-model.number="editingLimits.conductivity.max_value" type="number" step="10" />
              <span class="help-text">Máximo absoluto de conductividad</span>
            </div>

            <div class="ranges-preview">
              <h5>Rangos Calculados Automáticamente:</h5>
              <div class="range-row danger">🔴 Peligroso Inf: {{ editingRanges.conductivity.danger_min.toFixed(0) }} — {{ editingRanges.conductivity.danger_max.toFixed(0) }}</div>
              <div class="range-row warning">🟠 Advertencia Inf: {{ editingRanges.conductivity.warning_min.toFixed(0) }} — {{ editingRanges.conductivity.warning_max.toFixed(0) }}</div>
              <div class="range-row safe">🟢 Seguro: {{ editingRanges.conductivity.safe_min.toFixed(0) }} — {{ editingRanges.conductivity.safe_max.toFixed(0) }}</div>
              <div class="range-row warning">🟠 Advertencia Sup: {{ editingRanges.conductivity.warning_min_sup.toFixed(0) }} — {{ editingRanges.conductivity.warning_max_sup.toFixed(0) }}</div>
              <div class="range-row danger">🔴 Peligroso Sup: {{ editingRanges.conductivity.danger_min_sup.toFixed(0) }} — {{ editingRanges.conductivity.danger_max_sup.toFixed(0) }}</div>
            </div>

            <button class="save-config-btn" @click="saveAlertConfig('conductivity')">Guardar Conductividad</button>
          </div>
        </div>
      </section>
    </main>
  </div>

  <div v-else-if="currentView === 'admin-users'" class="dashboard">
    <header class="dashboard-header">
      <div class="header-content">
        <ThemeToggleButton />
        <button class="back-btn" @click="goToHome" title="Volver al inicio">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
            <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
          </svg>
        </button>
        <div>
          <h1 class="header-title">Gestion de usuarios</h1>
          <p class="header-subtitle">Crea cuentas y administra roles en Supabase</p>
        </div>
      </div>
      <div class="header-center admin-top-actions">
        <button class="admin-nav-btn active">Gestion de usuarios</button>
      </div>
      <div class="header-right">
        <div class="data-source-badge" :class="`source-${selectedDevice.dataSource}`">
          <span v-if="selectedDevice.dataSource === 'real'">📊 Datos Reales</span>
          <span v-else-if="selectedDevice.dataSource === 'simulated'">⚙️ Datos Simulados</span>
          <span v-else>❓ Fuente Desconocida</span>
        </div>
        <button class="logout-btn" type="button" @click="handleLogout">Cerrar sesión</button>
      </div>
    </header>

    <main class="dashboard-content">
      <section class="user-management-section">
        <div class="alerts-header">
          <h2 class="section-title">Administracion de cuentas</h2>
        </div>

        <div class="user-management-content">
          <div v-if="supabaseSessionWarning" class="error-message session-warning">
            {{ supabaseSessionWarning }}
          </div>

          <div class="user-creation-form">
            <h3>Crear nueva cuenta</h3>
            <div class="form-grid">
              <div class="form-group">
                <label>Email:</label>
                <input v-model="newUser.email" type="email" placeholder="usuario@empresa.com" />
              </div>
              <div class="form-group">
                <label>Contrasena:</label>
                <input v-model="newUser.password" type="password" placeholder="********" />
              </div>
              <div class="form-group">
                <label>Nombre completo:</label>
                <input v-model="newUser.fullName" type="text" placeholder="Juan Perez" />
              </div>
              <div class="form-group">
                <label>Rol:</label>
                <select v-model="newUser.role">
                  <option value="employee">Trabajador</option>
                  <option value="admin">Administrador</option>
                </select>
              </div>
            </div>

            <div v-if="userCreationError" class="error-message">
              {{ userCreationError }}
            </div>
            <div v-if="userCreationSuccess" class="success-message">
              {{ userCreationSuccess }}
            </div>

            <button
              class="create-user-btn"
              @click="createNewUser"
              :disabled="isCreatingUser"
            >
              {{ isCreatingUser ? 'Creando...' : 'Crear usuario' }}
            </button>
          </div>

          <div class="users-list">
            <div class="users-list-header">
              <div class="users-list-title-block">
                <h3>Usuarios en Supabase Auth</h3>
                <p v-if="!isLoadingUsers" class="users-count-summary">
                  <strong>{{ supabaseUsersTotal }}</strong> en Supabase Auth —
                  <strong class="verified-count">{{ supabaseUsersVerified }}</strong> verificados,
                  <strong class="pending-count">{{ supabaseUsersPending }}</strong> pendientes
                  <span v-if="usersListSource === 'supabase_auth'" class="users-source-tag">· sincronizado con Auth</span>
                  <span v-else-if="usersListSource === 'users_roles'" class="users-source-tag users-source-warn">· incompleto (falta RPC)</span>
                </p>
              </div>
              <button class="refresh-users-btn" @click="loadExistingUsers" :disabled="isLoadingUsers">
                {{ isLoadingUsers ? '⟳ Cargando...' : '↻ Actualizar' }}
              </button>
            </div>
            <div v-if="usersLoadError" class="error-message users-load-hint">
              {{ usersLoadError }}
            </div>
            <div v-if="!isLoadingUsers && existingUsers.length > 0" class="users-filter-bar">
              <button
                type="button"
                class="filter-chip"
                :class="{ active: userVerificationFilter === 'all' }"
                @click="userVerificationFilter = 'all'"
              >
                Todos ({{ existingUsers.length }})
              </button>
              <button
                type="button"
                class="filter-chip"
                :class="{ active: userVerificationFilter === 'verified' }"
                @click="userVerificationFilter = 'verified'"
              >
                Verificados ({{ supabaseUsersVerified }})
              </button>
              <button
                type="button"
                class="filter-chip"
                :class="{ active: userVerificationFilter === 'pending' }"
                @click="userVerificationFilter = 'pending'"
              >
                Pendientes ({{ supabaseUsersPending }})
              </button>
            </div>
            <div v-if="isLoadingUsers" class="loading-users">
              Cargando usuarios...
            </div>
            <div v-else-if="displayedUsers.length > 0" class="users-table">
              <table>
                <thead>
                  <tr>
                    <th>Email</th>
                    <th>Nombre</th>
                    <th>Estado</th>
                    <th>Rol</th>
                    <th>Creado</th>
                    <th>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="user in displayedUsers" :key="user.id">
                    <td>{{ user.email }}</td>
                    <td>{{ user.full_name || 'N/A' }}</td>
                    <td>
                      <span
                        class="verification-badge"
                        :class="user.is_verified ? 'verification-verified' : 'verification-pending'"
                      >
                        {{ user.verification_label || (user.is_verified ? 'Verificado' : 'Pendiente') }}
                      </span>
                    </td>
                    <td>
                      <span class="role-badge" :class="`role-${user.role}`">
                        {{ user.role === 'admin' ? 'Admin' : 'Trabajador' }}
                      </span>
                    </td>
                    <td>{{ formatDate(user.created_at) }}</td>
                    <td>
                      <button class="delete-user-btn" @click="deleteUser(user.id)">Eliminar</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-else class="no-users">
              <template v-if="supabaseSessionWarning">
                Inicia sesión con una cuenta admin de Supabase para ver el listado.
              </template>
              <template v-else-if="existingUsers.length > 0 && displayedUsers.length === 0">
                Ningún usuario coincide con el filtro seleccionado.
              </template>
              <template v-else>
                No hay usuarios en Supabase Auth (total: 0).
              </template>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>

  <div v-else class="history-view">
    <header class="dashboard-header">
      <div class="header-content">
        <ThemeToggleButton />
        <button class="back-btn" @click="goBack" title="Volver a dispositivos">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
            <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
          </svg>
        </button>
        <div>
          <h1 class="header-title">Registro Histórico</h1>
          <p class="header-subtitle">Todas las mediciones guardadas por dispositivo y fecha</p>
        </div>
      </div>
      <button class="pdf-btn" @click="downloadHistoryPdf">Descargar PDF</button>
    </header>

    <main class="dashboard-content">
      <section class="filters-section">
        <h2 class="section-title">Opciones de filtrado</h2>
        <div class="filters-grid">
          <label class="filter-item">
            <span>Dispositivo</span>
            <select v-model="historyFilters.deviceId">
              <option value="all">Todos</option>
              <option v-for="device in devices" :key="device.id" :value="String(device.id)">
                {{ device.name }}
              </option>
            </select>
          </label>
          <label class="filter-item">
            <span>Fecha</span>
            <select v-model="historyFilters.date">
              <option value="all">Todas</option>
              <option v-for="dateValue in availableDates" :key="dateValue" :value="dateValue">
                {{ dateValue }}
              </option>
            </select>
          </label>
        </div>
      </section>

      <section class="charts-section">
        <h2 class="section-title">Gráficos de tendencias</h2>
        <div class="chart-grid">
          <div class="chart-card">
            <h3>pH</h3>
            <svg viewBox="0 0 320 120" class="line-chart">
              <polyline :points="buildLineChartPoints(historyFilteredRows, 'ph', 5, 9)" />
            </svg>
          </div>
          <div class="chart-card">
            <h3>Temperatura</h3>
            <svg viewBox="0 0 320 120" class="line-chart">
              <polyline :points="buildLineChartPoints(historyFilteredRows, 'temperature', 15, 35)" />
            </svg>
          </div>
          <div class="chart-card">
            <h3>Conductividad</h3>
            <svg viewBox="0 0 320 120" class="line-chart">
              <polyline :points="buildLineChartPoints(historyFilteredRows, 'conductivity', 200, 1800)" />
            </svg>
          </div>
        </div>
      </section>

      <section class="alerts-section">
        <div class="alerts-header">
          <h2 class="section-title">Mediciones filtradas</h2>
          <span class="alerts-count">{{ historyFilteredRows.length }} filas</span>
        </div>
        <div class="table-wrap">
          <table class="alerts-table">
            <thead>
              <tr>
                <th>Dispositivo</th>
                <th>pH</th>
                <th>Temperatura</th>
                <th>Conductividad</th>
                <th>Estado de carga</th>
                <th>Fecha</th>
                <th>Hora</th>
                <th>Telegram</th>
                <th>Email</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in historyFilteredRows" :key="row.id">
                <td>{{ row.deviceName }}</td>
                <td>{{ row.ph }}</td>
                <td>{{ row.temperature }}</td>
                <td>{{ row.conductivity }}</td>
                <td>{{ row.battery }}%</td>
                <td>{{ row.date }}</td>
                <td>{{ row.time }}</td>
                <td>{{ row.telegramStatus }}</td>
                <td>{{ row.emailStatus }}</td>
              </tr>
              <tr v-if="historyFilteredRows.length === 0">
                <td colspan="9" class="empty-cell">No hay datos para los filtros seleccionados.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </main>
  </div>

  <!-- Sección de Gestión de Dispositivos (siempre renderizada para acceso desde cualquier vista) -->
  <AdminDevicesSection ref="devicesSectionRef" :show-section="currentView === 'dashboard'" :trigger-open-modal="triggerOpenAddModal" />

  <!-- Modal Agregar Dispositivo (simple, para evitar problemas con AdminDevicesSection) -->
  <div v-if="showAddDeviceModal" class="modal-overlay" @click.self="showAddDeviceModal = false">
    <div class="modal-content">
      <div class="modal-header">
        <h3>Agregar Nuevo Dispositivo</h3>
        <button class="close-btn" @click="showAddDeviceModal = false">×</button>
      </div>

      <div class="modal-body">
        <form @submit.prevent="handleAddDeviceSubmit">
          <!-- Nombre -->
          <div class="form-group">
            <label for="device-name">Nombre del Dispositivo *</label>
            <input
              id="device-name"
              v-model.trim="addDeviceFormData.name"
              type="text"
              placeholder="Ej: Sensor Embalse Norte"
              required
              class="form-input"
            />
          </div>

          <!-- Tipo de Dispositivo -->
          <div class="form-group">
            <label for="device-type">Tipo de Microcontrolador</label>
            <select v-model="addDeviceFormData.device_type" id="device-type" class="form-select">
              <option value="ESP8266">ESP8266 (WiFi)</option>
              <option value="Arduino">Arduino</option>
              <option value="STM32">STM32</option>
              <option value="other">Otro</option>
            </select>
          </div>

          <!-- Ubicación -->
          <div class="form-group">
            <label for="device-location">Ubicación (opcional)</label>
            <input
              id="device-location"
              v-model.trim="addDeviceFormData.location"
              type="text"
              placeholder="Ej: Zona A - Profundidad 5m"
              class="form-input"
            />
          </div>

          <!-- Arduino ID (si aplica) -->
          <div class="form-group">
            <label for="arduino-id">Arduino ID (opcional)</label>
            <input
              id="arduino-id"
              v-model.trim="addDeviceFormData.arduino_id"
              type="text"
              placeholder="Auto-detectado si se deja vacío"
              class="form-input"
            />
            <small class="help-text">
              Si tienes el ID del Arduino, colócalo aquí. De lo contrario, se asignará automáticamente.
            </small>
          </div>

          <!-- Botones -->
          <div class="form-actions">
            <button
              type="button"
              class="btn btn-secondary"
              @click="showAddDeviceModal = false"
              :disabled="isSubmittingDevice"
            >
              Cancelar
            </button>
            <button
              type="submit"
              class="btn btn-primary"
              :disabled="!addDeviceFormData.name || isSubmittingDevice"
            >
              {{ isSubmittingDevice ? 'Guardando...' : 'Agregar Dispositivo' }}
            </button>
          </div>
        </form>

        <!-- Mensaje de Error -->
        <div v-if="addDeviceError" class="alert alert-error">
          {{ addDeviceError }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import DeviceList from './DeviceList.vue'
import ThemeToggleButton from './ThemeToggleButton.vue'
import SensorCard from './SensorCard.vue'
import BatteryIndicator from './BatteryIndicator.vue'
import AdminDevicesSection from './AdminDevicesSection.vue'
import { checkAndSendAlerts } from '../services/AlertService.js'
import { fetchDashboardData, fetchSensorHistory, IS_SIMULATED_MODE, DATA_MODE } from '../services/ArduinoConfig.js'
import {
  createUserInSupabase,
  fetchSupabaseAuthUsersForAdmin,
  deleteUserFromSupabase,
  getAlertLimitsByAdmin,
  getCurrentUser,
} from '../services/SupabaseAuthService.js'
import { ensureSupabaseAdminSession } from '../services/supabaseSessionBridge.js'
import { clearSession, stopSessionIdleWatcher, hasValidSessionToken } from '../services/sessionAuth.js'

const router = useRouter()
const API_BASE_URL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')

const ALERT_TABLE_LIMIT = 5

// Almacena solo los 3 valores clave (min, central, max)
let SENSOR_LIMITS_CONFIG = ref({
  ph:           { min_value: 0,  central_value: 5,    max_value: 10   },
  temperature:  { min_value: 0,  central_value: 15,   max_value: 30   },
  conductivity: { min_value: 0,  central_value: 1000, max_value: 2000 },
})

// Deriva automáticamente los 10 rangos a partir de los 3 valores clave
const calculateRanges = (minVal, centralVal, maxVal) => {
  const rangeTotal = maxVal - minVal
  const safeMargin    = rangeTotal * 0.25
  const warningMargin = rangeTotal * 0.40
  return {
    min_value: minVal, central_value: centralVal, max_value: maxVal,
    danger_min:    minVal,
    danger_max:    centralVal - warningMargin,
    warning_min:   centralVal - warningMargin,
    warning_max:   centralVal - safeMargin,
    safe_min:      centralVal - safeMargin,
    safe_max:      centralVal + safeMargin,
    warning_min_sup: centralVal + safeMargin,
    warning_max_sup: centralVal + warningMargin,
    danger_min_sup:  centralVal + warningMargin,
    danger_max_sup:  maxVal,
  }
}

// Computed: rangos completos para los 3 sensores
const SENSOR_LIMITS = computed(() => ({
  ph:           calculateRanges(SENSOR_LIMITS_CONFIG.value.ph.min_value,           SENSOR_LIMITS_CONFIG.value.ph.central_value,           SENSOR_LIMITS_CONFIG.value.ph.max_value),
  temperature:  calculateRanges(SENSOR_LIMITS_CONFIG.value.temperature.min_value,  SENSOR_LIMITS_CONFIG.value.temperature.central_value,  SENSOR_LIMITS_CONFIG.value.temperature.max_value),
  conductivity: calculateRanges(SENSOR_LIMITS_CONFIG.value.conductivity.min_value, SENSOR_LIMITS_CONFIG.value.conductivity.central_value, SENSOR_LIMITS_CONFIG.value.conductivity.max_value),
}))

// Computed: mapea snake_case → camelCase para SensorCard
const sensorThresholds = computed(() => ({
  ph: {
    dangerMin:    SENSOR_LIMITS.value?.ph?.danger_min,    dangerMax:    SENSOR_LIMITS.value?.ph?.danger_max,
    warningMin:   SENSOR_LIMITS.value?.ph?.warning_min,   warningMax:   SENSOR_LIMITS.value?.ph?.warning_max,
    safeMin:      SENSOR_LIMITS.value?.ph?.safe_min,      safeMax:      SENSOR_LIMITS.value?.ph?.safe_max,
    warningMinSup: SENSOR_LIMITS.value?.ph?.warning_min_sup, warningMaxSup: SENSOR_LIMITS.value?.ph?.warning_max_sup,
    dangerMinSup:  SENSOR_LIMITS.value?.ph?.danger_min_sup,  dangerMaxSup:  SENSOR_LIMITS.value?.ph?.danger_max_sup,
  },
  temperature: {
    dangerMin:    SENSOR_LIMITS.value?.temperature?.danger_min,    dangerMax:    SENSOR_LIMITS.value?.temperature?.danger_max,
    warningMin:   SENSOR_LIMITS.value?.temperature?.warning_min,   warningMax:   SENSOR_LIMITS.value?.temperature?.warning_max,
    safeMin:      SENSOR_LIMITS.value?.temperature?.safe_min,      safeMax:      SENSOR_LIMITS.value?.temperature?.safe_max,
    warningMinSup: SENSOR_LIMITS.value?.temperature?.warning_min_sup, warningMaxSup: SENSOR_LIMITS.value?.temperature?.warning_max_sup,
    dangerMinSup:  SENSOR_LIMITS.value?.temperature?.danger_min_sup,  dangerMaxSup:  SENSOR_LIMITS.value?.temperature?.danger_max_sup,
  },
  conductivity: {
    dangerMin:    SENSOR_LIMITS.value?.conductivity?.danger_min,    dangerMax:    SENSOR_LIMITS.value?.conductivity?.danger_max,
    warningMin:   SENSOR_LIMITS.value?.conductivity?.warning_min,   warningMax:   SENSOR_LIMITS.value?.conductivity?.warning_max,
    safeMin:      SENSOR_LIMITS.value?.conductivity?.safe_min,      safeMax:      SENSOR_LIMITS.value?.conductivity?.safe_max,
    warningMinSup: SENSOR_LIMITS.value?.conductivity?.warning_min_sup, warningMaxSup: SENSOR_LIMITS.value?.conductivity?.warning_max_sup,
    dangerMinSup:  SENSOR_LIMITS.value?.conductivity?.danger_min_sup,  dangerMaxSup:  SENSOR_LIMITS.value?.conductivity?.danger_max_sup,
  },
}))

// Computed: preview en tiempo real mientras el admin edita (antes de guardar)
const editingRanges = computed(() => {
  const toNum = (val) => Number(val) || 0
  return {
    ph:           calculateRanges(toNum(editingLimits.value.ph.min_value),           toNum(editingLimits.value.ph.central_value),           toNum(editingLimits.value.ph.max_value)),
    temperature:  calculateRanges(toNum(editingLimits.value.temperature.min_value),  toNum(editingLimits.value.temperature.central_value),  toNum(editingLimits.value.temperature.max_value)),
    conductivity: calculateRanges(toNum(editingLimits.value.conductivity.min_value), toNum(editingLimits.value.conductivity.central_value), toNum(editingLimits.value.conductivity.max_value)),
  }
})

let lastSavedLimits = JSON.parse(JSON.stringify(SENSOR_LIMITS_CONFIG.value))
const hasUnsavedChanges = ref(false)

// Estado para edición temporal — NO afecta gráficos hasta guardar
let editingLimits = ref({
  ph:           { min_value: 0,  central_value: 5,    max_value: 10   },
  temperature:  { min_value: 0,  central_value: 15,   max_value: 30   },
  conductivity: { min_value: 0,  central_value: 1000, max_value: 2000 },
})

const currentView = ref('devices')
const previousView = ref(null)
const selectedDeviceId = ref(null)
const devicesSectionRef = ref(null)
const triggerOpenAddModal = ref(false)
const showAddDeviceModal = ref(false)
const addDeviceFormData = ref({
  name: '',
  device_type: 'ESP8266',
  location: '',
  arduino_id: ''
})
const addDeviceError = ref('')
const isSubmittingDevice = ref(false)
const lastSync = ref('Sin datos del Arduino')
const showAllTodayAlerts = ref(false)

// Detectar si es admin
const isAdmin = computed(() => {
  const userRole = String(localStorage.getItem('userRole') || '').toLowerCase()
  return userRole === 'admin' || userRole === 'administrador'
})

// Estado de creación de usuario
const newUser = ref({
  email: '',
  password: '',
  fullName: '',
  role: 'employee'
})
const isCreatingUser = ref(false)
const userCreationError = ref('')
const userCreationSuccess = ref('')
const supabaseSessionWarning = ref('')
const existingUsers = ref([])
const supabaseUsersTotal = ref(0)
const supabaseUsersVerified = ref(0)
const supabaseUsersPending = ref(0)
const userVerificationFilter = ref('all')
const usersListSource = ref(null)
const usersLoadError = ref('')
const isLoadingUsers = ref(false)

const displayedUsers = computed(() => {
  const list = existingUsers.value || []
  if (userVerificationFilter.value === 'verified') {
    return list.filter((u) => u.is_verified)
  }
  if (userVerificationFilter.value === 'pending') {
    return list.filter((u) => !u.is_verified)
  }
  return list
})

const devices = ref([
  {
    id: 1,
    name: 'ESP8266 Embalse',
    model: 'ESP8266 - Lectura en tiempo real',
    status: 'disconnected',
    lastUpdate: 'Sin datos',
    battery: 100,
    sensors: { ph: 0, temperature: 0, conductivity: 0 },
    dataSource: IS_SIMULATED_MODE ? 'simulated' : 'real'
  }
])

const selectedDevice = computed(() => {
  return devices.value.find((device) => device.id === selectedDeviceId.value) || {
    id: null,
    name: 'Sin dispositivo',
    model: 'Selecciona un dispositivo para comenzar',
    status: 'disconnected',
    sensors: { ph: 0, temperature: 0, conductivity: 0 }
  }
})

const batteryLevel = computed(() => {
  const level = selectedDevice.value?.battery || selectedDevice.value?.bateria
  return typeof level === 'number' ? Math.min(100, Math.max(0, level)) : 100
})

const sensors = computed(() => ({
  ph: { value: selectedDevice.value.sensors.ph },
  temperature: { value: selectedDevice.value.sensors.temperature },
  conductivity: { value: selectedDevice.value.sensors.conductivity }
}))

const historyRecords = ref([])
const historyFilters = ref({
  deviceId: 'all',
  date: 'all'
})
const lastProcessedAlertTimestamp = ref(0)

const getStatus = (value, min, max) => {
  const percentage = ((value - min) / (max - min)) * 100
  if (percentage < 15 || percentage > 85) return 'danger'
  if (percentage < 35 || percentage > 65) return 'warning'
  return 'safe'
}

const overallStatus = computed(() => {
  const phStatus      = getStatus(sensors.value.ph.value,           SENSOR_LIMITS.value?.ph?.safe_min           || 0, SENSOR_LIMITS.value?.ph?.safe_max           || 14)
  const tempStatus    = getStatus(sensors.value.temperature.value,  SENSOR_LIMITS.value?.temperature?.safe_min  || 0, SENSOR_LIMITS.value?.temperature?.safe_max  || 50)
  const conductStatus = getStatus(sensors.value.conductivity.value, SENSOR_LIMITS.value?.conductivity?.safe_min || 0, SENSOR_LIMITS.value?.conductivity?.safe_max || 3000)
  const statuses = [phStatus, tempStatus, conductStatus]
  if (statuses.includes('danger')) return 'danger'
  if (statuses.includes('warning')) return 'warning'
  return 'safe'
})

const overallStatusText = computed(() => {
  if (overallStatus.value === 'danger') return 'Situación Peligrosa'
  if (overallStatus.value === 'warning') return 'Advertencia'
  return 'Sistema Normal'
})

const formatDate = (date) => {
  if (!date) return 'N/A'
  const d = typeof date === 'string' ? new Date(date) : date
  const day = String(d.getDate()).padStart(2, '0')
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const year = d.getFullYear()
  return `${day}-${month}-${year}`
}

const formatTime = (date) => {
  const hour = String(date.getHours()).padStart(2, '0')
  const minute = String(date.getMinutes()).padStart(2, '0')
  const second = String(date.getSeconds()).padStart(2, '0')
  return `${hour}:${minute}:${second}`
}

const formatDateTime = (date) => {
  return `${formatDate(date)} ${formatTime(date)}`
}

const createRecord = ({ ph, temperature, conductivity, timestamp }) => {
  const now = timestamp ? new Date(timestamp) : new Date()
  const safePh = Number(Number(ph).toFixed(2))
  const safeTemperature = Number(Number(temperature).toFixed(2))
  const safeConductivity = Number(Number(conductivity).toFixed(2))
  const phLimits      = SENSOR_LIMITS.value?.ph           || {}
  const tempLimits    = SENSOR_LIMITS.value?.temperature  || {}
  const conductLimits = SENSOR_LIMITS.value?.conductivity || {}
  const isAlert =
    (safePh           < (phLimits.safe_min      ?? 0) || safePh           > (phLimits.safe_max      ?? 14))   ||
    (safeTemperature  < (tempLimits.safe_min    ?? 0) || safeTemperature  > (tempLimits.safe_max    ?? 50))   ||
    (safeConductivity < (conductLimits.safe_min ?? 0) || safeConductivity > (conductLimits.safe_max ?? 3000))

  return {
    id: `real-${now.getTime()}-${Math.random().toString(16).slice(2, 8)}`,
    deviceId: 1,
    deviceName: devices.value[0].name,
    ph: safePh,
    temperature: safeTemperature,
    conductivity: safeConductivity,
    battery: devices.value[0].battery,
    date: formatDate(now),
    time: formatTime(now),
    timestamp: now.getTime(),
    telegramStatus: IS_SIMULATED_MODE ? 'deshabilitado (simulado)' : (isAlert ? 'pendiente' : 'sin alerta'),
    emailStatus: IS_SIMULATED_MODE ? 'deshabilitado (simulado)' : (isAlert ? 'pendiente' : 'sin alerta'),
    isAlert
  }
}

const availableDates = computed(() => {
  const uniqueDates = [...new Set(historyRecords.value.map((record) => record.date))]
  return uniqueDates.sort((a, b) => {
    const [da, ma, ya] = a.split('-').map(Number)
    const [db, mb, yb] = b.split('-').map(Number)
    return new Date(yb, mb - 1, db) - new Date(ya, ma - 1, da)
  })
})

const historyFilteredRows = computed(() => {
  return historyRecords.value
    .filter((record) => {
      const matchesDevice = historyFilters.value.deviceId === 'all' || record.deviceId === Number(historyFilters.value.deviceId)
      const matchesDate = historyFilters.value.date === 'all' || record.date === historyFilters.value.date
      return matchesDevice && matchesDate
    })
    .sort((a, b) => b.timestamp - a.timestamp)
})

const todayString = computed(() => formatDate(new Date()))
const todayAlerts = computed(() => {
  return historyRecords.value
    .filter((record) => record.isAlert && record.deviceId === selectedDeviceId.value && record.date === todayString.value)
    .sort((a, b) => b.timestamp - a.timestamp)
})

const visibleAlerts = computed(() => {
  return showAllTodayAlerts.value ? todayAlerts.value : todayAlerts.value.slice(0, ALERT_TABLE_LIMIT)
})

const buildLineChartPoints = (rows, key, min, max) => {
  const chartRows = rows.slice(0, 20).reverse()
  if (chartRows.length < 2) return '0,100 320,100'
  return chartRows.map((row, index) => {
    const x = (index / (chartRows.length - 1)) * 320
    const value = Number(row[key])
    const normalized = (value - min) / (max - min)
    const y = 110 - Math.max(0, Math.min(1, normalized)) * 100
    return `${x.toFixed(2)},${y.toFixed(2)}`
  }).join(' ')
}

const escapeHtml = (value) => {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

const downloadHistoryPdf = () => {
  const groupedByDevice = historyFilteredRows.value.reduce((acc, row) => {
    if (!acc[row.deviceName]) acc[row.deviceName] = []
    acc[row.deviceName].push(row)
    return acc
  }, {})

  const rowsHtml = Object.entries(groupedByDevice).map(([deviceName, rows]) => {
    const tableRows = rows.map((row) => {
      return `<tr>
        <td>${escapeHtml(row.ph)}</td>
        <td>${escapeHtml(row.temperature)}</td>
        <td>${escapeHtml(row.conductivity)}</td>
        <td>${escapeHtml(row.battery)}%</td>
        <td>${escapeHtml(row.date)}</td>
        <td>${escapeHtml(row.time)}</td>
        <td>${escapeHtml(row.telegramStatus)}</td>
        <td>${escapeHtml(row.emailStatus)}</td>
      </tr>`
    }).join('')
    return `
      <h2>${escapeHtml(deviceName)}</h2>
      <table>
        <thead>
          <tr>
            <th>pH</th>
            <th>Temperatura</th>
            <th>Conductividad</th>
            <th>Estado de carga</th>
            <th>Fecha</th>
            <th>Hora</th>
            <th>Telegram</th>
            <th>Email</th>
          </tr>
        </thead>
        <tbody>${tableRows}</tbody>
      </table>
    `
  }).join('')

  const win = window.open('', '_blank')
  if (!win) return
  win.document.write(`
    <html>
      <head>
        <title>Registro Historico</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 20px; color: #1f2937; }
          h1 { margin-bottom: 8px; }
          h2 { margin-top: 28px; margin-bottom: 8px; color: #2e7d32; }
          p { margin-top: 0; color: #4b5563; }
          table { width: 100%; border-collapse: collapse; margin-bottom: 16px; }
          th, td { border: 1px solid #d1d5db; padding: 6px 8px; font-size: 12px; text-align: left; }
          th { background: #f3f4f6; }
        </style>
      </head>
      <body>
        <h1>Registro Historico de Mediciones</h1>
        <p>Filtro dispositivo: ${escapeHtml(historyFilters.value.deviceId === 'all' ? 'Todos' : selectedDevice.value.name)} | Filtro fecha: ${escapeHtml(historyFilters.value.date === 'all' ? 'Todas' : historyFilters.value.date)}</p>
        ${rowsHtml || '<p>No hay datos para exportar.</p>'}
      </body>
    </html>
  `)
  win.document.close()
  win.focus()
  win.print()
}

const formatLastSync = (value) => {
  if (!value) return 'Sin datos del Arduino'
  const diff = Math.max(0, Math.floor((Date.now() - new Date(value).getTime()) / 1000))
  if (diff < 60) return `hace ${diff}s`
  return `hace ${Math.floor(diff / 60)}m`
}

const loadHistoryFromApi = async () => {
  const rows = await fetchSensorHistory(300)
  if (!Array.isArray(rows)) {
    return
  }

  historyRecords.value = rows.map((item) =>
    createRecord({
      ph: item.ph,
      temperature: item.temperature,
      conductivity: item.conductivity,
      timestamp: item.timestamp
    })
  )
}

const loadDashboardFromApi = async () => {
  const dashboard = await fetchDashboardData()
  console.log('[DEBUG] Respuesta de /api/dashboard:', dashboard)
  if (!dashboard) {
    devices.value[0] = {
      ...devices.value[0],
      status: 'disconnected',
      lastUpdate: 'Sin datos',
      sensors: { ph: 0, temperature: 0, conductivity: 0 },
      dataSource: 'unknown'
    }
    lastSync.value = 'Sin datos del Arduino'
    return
  }

  let dataSource = IS_SIMULATED_MODE ? 'simulated' : 'real'
  if (!IS_SIMULATED_MODE) {
    try {
      const diagResponse = await fetch(`${API_BASE_URL}/api/diagnostics`)
      if (diagResponse.ok) {
        const diag = await diagResponse.json()
        dataSource = diag.data_source || 'real'
      }
    } catch (e) {
      console.log('No se pudo obtener datos de diagnóstico:', e)
    }
  }

  devices.value[0] = {
    ...devices.value[0],
    status: dashboard.metadata.arduinoConnected ? 'connected' : 'disconnected',
    lastUpdate: formatLastSync(dashboard.ph.lastUpdated),
    sensors: {
      ph: Number(dashboard.ph.value),
      temperature: Number(dashboard.temperature.value),
      conductivity: Number(dashboard.conductivity.value)
    },
    battery: dashboard.battery || 100,
    bateria: dashboard.battery || 100,
    dataSource: dataSource
  }
  lastSync.value = formatLastSync(dashboard.metadata.lastSync)
}

const selectDevice = (device) => {
  selectedDeviceId.value = device.id
  currentView.value = 'dashboard'
  showAllTodayAlerts.value = false
}

const openHistory = () => {
  router.push('/historical')
}

const openAlertConfigView = () => {
  if (!isAdmin.value) return
  // Guardar desde donde vino el usuario
  previousView.value = currentView.value
  // Copiar valores actuales a editingLimits para que los cambios no afecten los gráficos hasta guardar
  editingLimits.value = JSON.parse(JSON.stringify(SENSOR_LIMITS_CONFIG.value))
  currentView.value = 'admin-alerts'
}

const refreshSupabaseSessionState = async () => {
  const check = await ensureSupabaseAdminSession()
  supabaseSessionWarning.value = check.ok ? '' : check.message
  return check.ok
}

const openUserManagementView = async () => {
  if (!isAdmin.value) return
  currentView.value = 'admin-users'
  const ready = await refreshSupabaseSessionState()
  if (ready) await loadExistingUsers()
  startUsersAutoRefresh()
}

const goToDashboardView = () => {
  currentView.value = 'dashboard'
}

const goToHome = () => {
  currentView.value = 'devices'
}

const goBack = () => {
  // Descartar cambios sin guardar cuando se regresa de la vista de configuración
  if (currentView.value === 'admin-alerts') {
    editingLimits.value = JSON.parse(JSON.stringify(SENSOR_LIMITS_CONFIG.value))
    // Volver a la vista anterior (dashboard si viene del dispositivo)
    currentView.value = previousView.value || 'devices'
  } else {
    // Para otros casos, volver al home
    currentView.value = 'devices'
  }
}

const openAddDeviceFromHeader = () => {
  if (!isAdmin.value) return
  // Llamar el método openAddModal del componente AdminDevicesSection
  if (devicesSectionRef.value) {
    devicesSectionRef.value.openAddModal()
  }
}

const openAddDeviceFromDeviceList = () => {
  console.log('🔘 openAddDeviceFromDeviceList called')
  console.log('isAdmin:', isAdmin.value)
  
  if (!isAdmin.value) {
    console.log('❌ Usuario no es admin')
    return
  }
  
  console.log('✅ Abriendo modal')
  showAddDeviceModal.value = true
}

const handleAddDeviceSubmit = async () => {
  if (!addDeviceFormData.value.name) return
  
  isSubmittingDevice.value = true
  addDeviceError.value = ''
  
  try {
    console.log('Enviando datos del dispositivo:', addDeviceFormData.value)
    
    const response = await fetch(`${API_BASE_URL}/api/devices`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('sessionToken')}`
      },
      body: JSON.stringify({
        name: addDeviceFormData.value.name,
        device_type: addDeviceFormData.value.device_type,
        location: addDeviceFormData.value.location || null,
        arduino_id: addDeviceFormData.value.arduino_id || null
      })
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || `Error ${response.status}`)
    }
    
    console.log('✅ Dispositivo creado exitosamente')
    showAddDeviceModal.value = false
    addDeviceFormData.value = { name: '', device_type: 'ESP8266', location: '', arduino_id: '' }
    
    // Recargar dispositivos
    // await deviceStore.fetchDevices(API_BASE_URL)
  } catch (error) {
    addDeviceError.value = `Error: ${error.message}`
    console.error('Error al agregar dispositivo:', error)
  } finally {
    isSubmittingDevice.value = false
  }
}

const handleLogout = () => {
  stopSessionIdleWatcher()
  clearSession()
  router.push('/login')
}

const saveAlertConfig = async (sensorType) => {
  try {
    isCreatingUser.value = true

    const userRole = String(localStorage.getItem('userRole') || '').toLowerCase()
    if (userRole !== 'admin' && userRole !== 'administrador') {
      alert('⚠️ Debes ser administrador para guardar configuraciones de alertas')
      return
    }

    const config = editingLimits.value[sensorType]

    if (config.min_value >= config.central_value) {
      alert(`❌ Error: El valor mínimo debe ser menor al valor central para ${sensorType}`)
      return
    }
    if (config.central_value >= config.max_value) {
      alert(`❌ Error: El valor central debe ser menor al valor máximo para ${sensorType}`)
      return
    }

    SENSOR_LIMITS_CONFIG.value[sensorType] = JSON.parse(JSON.stringify(config))

    const configToSave = { ...SENSOR_LIMITS_CONFIG.value }
    localStorage.setItem('sensorLimitsConfig', JSON.stringify(configToSave))

    hasUnsavedChanges.value = false
    lastSavedLimits = JSON.parse(JSON.stringify(SENSOR_LIMITS_CONFIG.value))

    alert(`✅ Rangos de ${sensorType} guardados exitosamente`)
  } catch (error) {
    console.error('Error en saveAlertConfig:', error)
    alert(`Error: ${error.message}`)
  } finally {
    isCreatingUser.value = false
  }
}

const createNewUser = async () => {
  const sanitizedEmail = String(newUser.value.email || '').trim().toLowerCase()
  const sanitizedFullName = String(newUser.value.fullName || '').trim()

  // Validar campos
  if (!sanitizedEmail || !newUser.value.password || !sanitizedFullName) {
    userCreationError.value = 'Por favor completa todos los campos'
    userCreationSuccess.value = ''
    return
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/
  if (!emailRegex.test(sanitizedEmail)) {
    userCreationError.value = 'Correo invalido. Usa formato nombre@dominio.com sin espacios.'
    userCreationSuccess.value = ''
    return
  }

  newUser.value.email = sanitizedEmail
  newUser.value.fullName = sanitizedFullName

  isCreatingUser.value = true
  userCreationError.value = ''
  userCreationSuccess.value = ''

  try {
    const result = await createUserInSupabase(
      newUser.value.email,
      newUser.value.password,
      newUser.value.fullName,
      newUser.value.role
    )

    if (result.success) {
      userCreationSuccess.value =
        `Usuario ${sanitizedEmail} creado en Supabase. Aparece en la lista como Pendiente hasta que confirme el correo; tras aceptar la invitación, pulsa Actualizar y pasará a Verificado.`
      newUser.value = {
        email: '',
        password: '',
        fullName: '',
        role: 'employee'
      }

      await loadExistingUsers()
      console.log('[createNewUser] ✅ Lista de usuarios refrescada')
    } else {
      userCreationError.value = result.error || 'Error al crear usuario'
      console.error('[createNewUser] ❌ Error:', result.error)
    }
  } catch (error) {
    userCreationError.value = `Error: ${error.message}`
  } finally {
    isCreatingUser.value = false
  }
}

const loadExistingUsers = async () => {
  isLoadingUsers.value = true
  usersLoadError.value = ''
  console.log('[loadExistingUsers] Iniciando carga...')
  try {
    await refreshSupabaseSessionState()
    const result = await fetchSupabaseAuthUsersForAdmin()
    console.log('[loadExistingUsers] Resultado:', result)

    if (Array.isArray(result.users)) {
      existingUsers.value = result.users
      supabaseUsersTotal.value = result.total ?? result.users.length
      supabaseUsersVerified.value = result.verifiedCount ?? result.users.filter((u) => u.is_verified).length
      supabaseUsersPending.value = result.pendingCount ?? supabaseUsersTotal.value - supabaseUsersVerified.value
      usersListSource.value = result.source
      usersLoadError.value = result.error || ''
      userVerificationFilter.value = 'all'
    }

    if (!result.success && !result.users?.length) {
      usersLoadError.value = result.error || usersLoadError.value
      supabaseUsersTotal.value = 0
      existingUsers.value = []
    }
  } catch (error) {
    console.error('[loadExistingUsers] ❌ Error al cargar usuarios:', error)
    usersLoadError.value = error?.message || 'Error al cargar usuarios'
  } finally {
    isLoadingUsers.value = false
  }
}

const deleteUser = async (userId) => {
  const target = existingUsers.value.find((u) => u.id === userId)
  const label = target?.email || userId
  if (!confirm(`¿Eliminar permanentemente la cuenta ${label} en Supabase Auth?`)) {
    return
  }

  try {
    const result = await deleteUserFromSupabase(userId)
    if (result.success) {
      userCreationSuccess.value = `Cuenta ${label} eliminada de Supabase.`
      userCreationError.value = ''
      await loadExistingUsers()
    } else {
      userCreationError.value = result.error || 'No se pudo eliminar el usuario'
      userCreationSuccess.value = ''
    }
  } catch (error) {
    console.error('Error al eliminar usuario:', error)
    userCreationError.value = error?.message || 'Error al eliminar usuario'
  }
}

let updateInterval = null
let usersRefreshInterval = null

const stopUsersAutoRefresh = () => {
  if (usersRefreshInterval) {
    clearInterval(usersRefreshInterval)
    usersRefreshInterval = null
  }
}

const startUsersAutoRefresh = () => {
  stopUsersAutoRefresh()
  usersRefreshInterval = setInterval(() => {
    if (currentView.value === 'admin-users' && !isLoadingUsers.value) {
      loadExistingUsers()
    }
  }, 45000)
}

const updateSensorData = async () => {
  if (!selectedDeviceId.value) return

  await loadDashboardFromApi()

  if (currentView.value === 'dashboard' || currentView.value === 'history') {
    await loadHistoryFromApi()
  }

  if (currentView.value !== 'dashboard') return
  if (IS_SIMULATED_MODE) return

  const latestRecord = historyRecords.value[0]
  if (!latestRecord || !latestRecord.isAlert) return

  if (latestRecord.timestamp > lastProcessedAlertTimestamp.value) {
    await checkAndSendAlerts(devices.value[0], SENSOR_LIMITS.value)
    lastProcessedAlertTimestamp.value = latestRecord.timestamp
  }
}

const startSensorUpdates = () => {
  if (updateInterval) clearInterval(updateInterval)
  updateSensorData()
  updateInterval = setInterval(updateSensorData, 2000)
}

const stopSensorUpdates = () => {
  if (updateInterval) {
    clearInterval(updateInterval)
    updateInterval = null
  }
}

watch(currentView, (view) => {
  if (view === 'admin-users') {
    startUsersAutoRefresh()
  } else {
    stopUsersAutoRefresh()
  }
})

watch(() => SENSOR_LIMITS_CONFIG.value,
  () => { hasUnsavedChanges.value = true },
  { deep: true }
)

onMounted(async () => {
  if (!hasValidSessionToken()) {
    router.push('/login')
    return
  }

  selectedDeviceId.value = 1
  console.log('[FRONTEND] VITE_DATA_MODE:', DATA_MODE)
  startSensorUpdates()

  // Cargar configuración de 3 valores desde localStorage
  const savedConfig = localStorage.getItem('sensorLimitsConfig')
  if (savedConfig) {
    try {
      const parsed = JSON.parse(savedConfig)
      SENSOR_LIMITS_CONFIG.value = parsed
      editingLimits.value = JSON.parse(savedConfig)
      console.log('✅ Configuración de rangos cargada desde localStorage:', SENSOR_LIMITS_CONFIG.value)
    } catch (e) {
      console.error('Error al cargar configuración guardada:', e)
    }
  }

  if (isAdmin.value) {
    await loadExistingUsers()
  }
})

onUnmounted(() => {
  stopSensorUpdates()
  stopUsersAutoRefresh()
})
</script>

<style scoped>
.dashboard {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
  display: flex;
  flex-direction: column;
}

.dashboard-header {
  background: #ffffff;
  border-bottom: 1px solid #e8e8e8;
  padding: 32px 40px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
  gap: 20px;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}

.header-center {
  display: flex;
  justify-content: center;
  flex: 1;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
  justify-content: flex-end;
}

.admin-top-actions {
  gap: 10px;
  flex-wrap: wrap;
}

.admin-nav-btn {
  border: 1px solid #ff9800;
  background: #ffffff;
  color: #a85c00;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}

.admin-nav-btn:hover {
  background: #fff3e0;
}

.admin-nav-btn.active {
  background: #ff9800;
  color: #ffffff;
  border-color: #ff9800;
}

.history-btn {
  border: 1px solid #66bb6a;
  background: #ffffff;
  color: #2e7d32;
  border-radius: 8px;
  padding: 10px 14px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 700;
  transition: all 0.2s ease;
}

.history-btn:hover {
  background: #e8f5e9;
}

.logout-btn {
  border: 1px solid #ef9a9a;
  background: #ffffff;
  color: #c62828;
  border-radius: 8px;
  padding: 10px 14px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 700;
  transition: all 0.2s ease;
}

.logout-btn:hover {
  background: #ffebee;
}

.back-btn {
  width: 40px;
  height: 40px;
  background: #f0f2f5;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #333;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.back-btn:hover {
  background: #e0e2e5;
  color: #66bb6a;
}

.header-content h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  color: #222;
  letter-spacing: -0.5px;
}

.header-subtitle {
  margin: 8px 0 0 0;
  color: #888;
  font-size: 14px;
  font-weight: 400;
}

.header-status {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #f8f9fa;
  padding: 12px 20px;
  border-radius: 8px;
}

.status-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  animation: pulse 2s ease-in-out infinite;
}

.indicator-safe {
  background-color: #66bb6a;
}

.indicator-warning {
  background-color: #ffb84d;
}

.indicator-danger {
  background-color: #ff4444;
}

.status-label {
  font-size: 14px;
  font-weight: 600;
  color: #555;
}

.data-source-badge {
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.source-real {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.source-simulated {
  background-color: #fff3cd;
  color: #856404;
  border: 1px solid #ffeaa7;
}

.source-unknown {
  background-color: #e2e3e5;
  color: #383d41;
  border: 1px solid #d6d8db;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

.dashboard-content {
  flex: 1;
  padding: 40px;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}

.sensors-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
  gap: 24px;
  margin-bottom: 40px;
}

.info-section {
  background: #ffffff;
  border-radius: 12px;
  padding: 28px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #e8e8e8;
  margin-bottom: 60px;
}

.section-title {
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
  letter-spacing: 0.3px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.info-card {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 8px;
  border-left: 3px solid #d0d0d0;
}

.info-card-label {
  font-size: 12px;
  color: #888;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

.info-card-value {
  font-size: 16px;
  color: #333;
  font-weight: 600;
}

.info-card-value.connected {
  color: #2e7d32;
}

.info-card-value.disconnected {
  color: #c62828;
}

.info-card-value.battery-card {
  font-weight: normal;
  color: inherit;
  display: flex;
  align-items: center;
}

.info-card-value.admin-role {
  color: #d32f2f;
  background: #ffebee;
  padding: 4px 8px;
  border-radius: 4px;
}

.info-card-value.user-role {
  color: #1976d2;
  background: #e3f2fd;
  padding: 4px 8px;
  border-radius: 4px;
}

/* Admin Sections */
.admin-section {
  background: #fff8f8;
  border: 2px solid #ffcdd2;
  margin-top: 28px;
}

.alerts-config-section,
.user-management-section {
  background: #ffffff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 2px solid #ff9800;
  margin-top: 28px;
}

.alerts-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.collapse-btn {
  background: #ff9800;
  color: white;
  border: none;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.3s;
}

.collapse-btn:hover {
  background: #f57c00;
}

.alerts-count {
  font-size: 12px;
  color: #6b7280;
  font-weight: 600;
}

.alerts-config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.alert-config-card {
  background: #f5f5f5;
  padding: 20px;
  border-radius: 8px;
  border-left: 4px solid #ff9800;
}

.alert-config-card h3 {
  margin-top: 0;
  color: #333;
  margin-bottom: 8px;
}

.card-instructions {
  font-size: 12px;
  color: #777;
  margin: 0 0 16px 0;
}

.section-subtitle {
  font-size: 13px;
  color: #666;
  margin: 4px 0 0 0;
}

.config-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 12px;
}

.config-group label {
  font-size: 13px;
  font-weight: 600;
  color: #555;
}

.config-group input {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 13px;
}

.config-group input:focus {
  outline: none;
  border-color: #ff9800;
  box-shadow: 0 0 0 3px rgba(255, 152, 0, 0.1);
}

.help-text {
  font-size: 11px;
  color: #999;
}

.ranges-preview {
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 12px;
  margin: 12px 0;
}

.ranges-preview h5 {
  margin: 0 0 8px 0;
  font-size: 12px;
  font-weight: 600;
  color: #555;
}

.range-row {
  font-size: 12px;
  padding: 3px 0;
  font-weight: 500;
}

.range-row.danger  { color: #c62828; }
.range-row.warning { color: #e65100; }
.range-row.safe    { color: #2e7d32; }

.save-config-btn {
  background: #4caf50;
  color: white;
  border: none;
  padding: 10px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  font-size: 13px;
  margin-top: 12px;
  transition: all 0.3s;
}

.save-config-btn:hover {
  background: #45a049;
}

.user-management-content {
  margin-top: 20px;
}

.user-creation-form {
  background: #f5f5f5;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 30px;
}

.user-creation-form h3 {
  margin-top: 0;
  color: #333;
  margin-bottom: 16px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 13px;
  font-weight: 600;
  color: #555;
}

.form-group input,
.form-group select {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 13px;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #ff9800;
  box-shadow: 0 0 0 3px rgba(255, 152, 0, 0.1);
}

.error-message {
  background: #ffebee;
  color: #c62828;
  padding: 12px;
  border-radius: 4px;
  margin-bottom: 12px;
  font-size: 13px;
  border-left: 4px solid #c62828;
}

.success-message {
  background: #e8f5e9;
  color: #2e7d32;
  padding: 12px;
  border-radius: 4px;
  margin-bottom: 12px;
  font-size: 13px;
  border-left: 4px solid #2e7d32;
}

.create-user-btn {
  background: #2196f3;
  color: white;
  border: none;
  padding: 12px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.3s;
}

.create-user-btn:hover:not(:disabled) {
  background: #1976d2;
}

.create-user-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.users-list {
  margin-top: 30px;
}

.users-list-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 16px;
}

.users-list-title-block h3 {
  color: #333;
  margin: 0 0 4px 0;
}

.users-count-summary {
  margin: 0;
  font-size: 14px;
  color: #555;
}

.users-source-tag {
  font-size: 13px;
  color: #667eea;
}

.users-source-warn {
  color: #b45309;
}

.users-load-hint {
  margin-bottom: 12px;
}

.users-filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.filter-chip {
  padding: 6px 12px;
  border: 1px solid #d0d0d0;
  border-radius: 999px;
  background: #fff;
  color: #444;
  font-size: 13px;
  cursor: pointer;
}

.filter-chip.active {
  background: #667eea;
  border-color: #667eea;
  color: #fff;
}

.verified-count {
  color: #2e7d32;
}

.pending-count {
  color: #b45309;
}

.verification-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.verification-verified {
  background: #e8f5e9;
  color: #2e7d32;
}

.verification-pending {
  background: #fff3e0;
  color: #e65100;
}

.users-list-header h3 {
  color: #333;
  margin: 0;
}

.refresh-users-btn {
  padding: 6px 12px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  font-size: 12px;
  transition: background 0.3s;
}

.refresh-users-btn:hover:not(:disabled) {
  background: #5568d3;
}

.refresh-users-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.loading-users {
  text-align: center;
  padding: 20px;
  color: #666;
  font-style: italic;
}

.users-table {
  overflow-x: auto;
}

.users-table table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.users-table th,
.users-table td {
  border: 1px solid #e5e7eb;
  padding: 10px;
  text-align: left;
}

.users-table th {
  background: #f9fafb;
  color: #374151;
  font-weight: 600;
}

.role-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.role-admin {
  background: #ffebee;
  color: #c62828;
}

.role-employee {
  background: #e3f2fd;
  color: #1976d2;
}

.delete-user-btn {
  background: #ff9800;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  transition: all 0.3s;
}

.delete-user-btn:hover {
  background: #f57c00;
}

.no-users {
  text-align: center;
  color: #999;
  padding: 20px;
  font-size: 13px;
}

.alerts-section,
.filters-section,
.charts-section {
  margin-top: 28px;
  background: #ffffff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #e8e8e8;
}

.table-wrap {
  overflow: auto;
  transition: max-height 0.3s ease;
}

.alerts-section:has(.see-more-btn:disabled) .table-wrap,
.table-wrap:not(:has(~ .table-footer .see-more-btn:not(:disabled))) {
  max-height: none;
}

/* Cuando mostrar menos está activo (todas las alertas visibles) */
.table-wrapper.expanded .table-wrap {
  max-height: 400px;
  overflow-y: auto;
  overflow-x: auto;
}

.table-wrapper {
  position: relative;
}

.table-footer {
  display: flex;
  justify-content: flex-end;
  padding-top: 12px;
}

.alerts-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.alerts-table th,
.alerts-table td {
  border: 1px solid #e5e7eb;
  padding: 8px 10px;
  text-align: left;
  white-space: nowrap;
}

.alerts-table th {
  background: #f9fafb;
  color: #374151;
}

.empty-cell {
  text-align: center;
  color: #6b7280;
}

.see-more-btn,
.pdf-btn {
  margin-top: 0;
  border: 1px solid #66bb6a;
  background: #ffffff;
  color: #2e7d32;
  border-radius: 8px;
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.see-more-btn:hover,
.pdf-btn:hover {
  background: #e8f5e9;
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.filters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  color: #374151;
  font-weight: 600;
}

.filter-item select {
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 13px;
  background: #ffffff;
}

.chart-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 16px;
}

.chart-card {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 12px;
  background: #f9fafb;
}

.chart-card h3 {
  margin-bottom: 8px;
  font-size: 14px;
}

.line-chart {
  width: 100%;
  height: 120px;
}

.line-chart polyline {
  fill: none;
  stroke: #2e7d32;
  stroke-width: 2.5;
}

.dashboard-footer {
  background: #ffffff;
  border-top: 1px solid #e8e8e8;
  padding: 20px 40px;
  text-align: center;
  color: #999;
  font-size: 13px;
  margin-top: auto;
}

.dashboard-footer p {
  margin: 0;
}

@media (max-width: 1024px) {
  .sensors-grid {
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  }

  .dashboard-header {
    flex-direction: column;
    gap: 20px;
    align-items: flex-start;
  }

  .pdf-btn {
    width: 100%;
  }

  .header-center {
    width: 100%;
    justify-content: flex-start;
  }
}

@media (max-width: 768px) {
  .dashboard-header {
    padding: 20px 16px;
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }

  .header-content {
    gap: 12px;
  }

  .header-content h1 {
    font-size: 22px;
  }

  .header-subtitle {
    font-size: 13px;
  }

  .header-status {
    width: 100%;
    justify-content: center;
  }

  .admin-top-actions {
    width: 100%;
  }

  .admin-nav-btn {
    flex: 1;
    min-width: 0;
  }

  .dashboard-content {
    padding: 16px;
  }

  .sensors-grid {
    grid-template-columns: 1fr;
    gap: 16px;
    margin-bottom: 24px;
  }

  .info-section {
    padding: 20px;
  }

  .alerts-section,
  .filters-section,
  .charts-section,
  .diagnostics-section,
  .alerts-config-section,
  .user-management-section {
    margin-top: 20px;
    padding: 16px;
  }

  .dashboard-footer {
    padding: 16px;
    font-size: 12px;
  }
}

@media (max-width: 480px) {
  .dashboard {
    min-height: 100vh;
  }

  .dashboard-header {
    padding: 16px 12px;
  }

  .back-btn {
    width: 36px;
    height: 36px;
  }

  .header-content {
    gap: 10px;
  }

  .header-content h1 {
    font-size: 18px;
  }

  .header-subtitle {
    font-size: 12px;
  }

  .status-label {
    font-size: 12px;
  }

  .dashboard-content {
    padding: 12px;
  }

  .sensors-grid {
    gap: 12px;
    margin-bottom: 20px;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }

  .info-section {
    padding: 16px;
  }

  .section-title {
    font-size: 16px;
    margin-bottom: 16px;
  }

  .info-card {
    padding: 12px;
    border-left-width: 2px;
  }

  .info-card-label {
    font-size: 11px;
  }

  .info-card-value {
    font-size: 15px;
  }

  .alerts-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }

  .dashboard-footer {
    padding: 12px;
    font-size: 11px;
  }
}

/*
 * Modo oscuro: reglas en este SFC para que Vue añada [data-v-*] y ganen
 * a theme-dark.css + estilos claros locales (evita títulos claros sobre fondo blanco).
 */
html[data-theme='dark'] .dashboard {
  background: linear-gradient(135deg, #1a1d26 0%, #121520 100%);
  background-color: #121520;
  flex: 1 0 auto;
  width: 100%;
  min-height: 100%;
  min-height: 100dvh;
}

html[data-theme='dark'] .dashboard-header {
  background: #22252e;
  border-bottom: 1px solid #343845;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.35);
}

html[data-theme='dark'] .header-content h1 {
  color: #f1f5f9;
}

html[data-theme='dark'] .header-subtitle {
  color: #94a3b8;
}

html[data-theme='dark'] .back-btn {
  background: #2e3240;
  color: #e2e8f0;
}

html[data-theme='dark'] .back-btn:hover {
  background: #3d4254;
  color: #86efac;
}

html[data-theme='dark'] .admin-nav-btn {
  background: #262a36;
  border-color: #fb923c;
  color: #fed7aa;
}

html[data-theme='dark'] .admin-nav-btn:hover {
  background: #431407;
}

html[data-theme='dark'] .admin-nav-btn.active {
  background: #ea580c;
  color: #fff7ed;
  border-color: #ea580c;
}

html[data-theme='dark'] .history-btn {
  background: #262a36;
  border-color: #4ade80;
  color: #bbf7d0;
}

html[data-theme='dark'] .history-btn:hover {
  background: #1e3a2a;
}

html[data-theme='dark'] .logout-btn {
  background: #262a36;
  border-color: #f87171;
  color: #fecaca;
}

html[data-theme='dark'] .logout-btn:hover {
  background: #3f1d1d;
}

html[data-theme='dark'] .header-status {
  background: #2a2d38;
}

html[data-theme='dark'] .status-label {
  color: #cbd5e1;
}

html[data-theme='dark'] .source-real {
  background-color: #14532d !important;
  color: #bbf7d0 !important;
  border-color: #22c55e !important;
}

html[data-theme='dark'] .source-simulated {
  background-color: #422006 !important;
  color: #fed7aa !important;
  border-color: #f59e0b !important;
}

html[data-theme='dark'] .source-unknown {
  background-color: #2e3240 !important;
  color: #cbd5e1 !important;
  border-color: #64748b !important;
}

html[data-theme='dark'] .info-section {
  background: #262a36;
  border-color: #3d4254;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.35);
}

html[data-theme='dark'] .section-title {
  color: #f1f5f9;
}

html[data-theme='dark'] .info-card {
  background: #2e3240;
  border-left-color: #4b5563;
}

html[data-theme='dark'] .info-card-label {
  color: #94a3b8;
}

html[data-theme='dark'] .info-card-value {
  color: #e2e8f0;
}

html[data-theme='dark'] .info-card-value.connected {
  color: #86efac;
}

html[data-theme='dark'] .info-card-value.disconnected {
  color: #fca5a5;
}

html[data-theme='dark'] .info-card-value.battery-card {
  color: inherit;
}

html[data-theme='dark'] .info-card-value.admin-role {
  color: #fecaca;
  background: rgba(127, 29, 29, 0.35);
}

html[data-theme='dark'] .info-card-value.user-role {
  color: #93c5fd;
  background: rgba(30, 58, 95, 0.45);
}

html[data-theme='dark'] .alerts-section,
html[data-theme='dark'] .filters-section,
html[data-theme='dark'] .charts-section {
  background: #262a36;
  border-color: #3d4254;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.35);
}

html[data-theme='dark'] .alerts-count {
  color: #94a3b8;
}

html[data-theme='dark'] .table-wrap {
  border: 1px solid #3d4254;
  border-radius: 8px;
}

html[data-theme='dark'] .alerts-table th {
  background: #2a2d38;
  color: #e2e8f0;
  border-color: #3d4254;
}

html[data-theme='dark'] .alerts-table td {
  background: #262a36;
  color: #e2e8f0;
  border-color: #3d4254;
}

html[data-theme='dark'] .alerts-table tbody tr:hover td {
  background: #2e3240;
}

html[data-theme='dark'] .empty-cell {
  color: #94a3b8 !important;
}

html[data-theme='dark'] .see-more-btn,
html[data-theme='dark'] .pdf-btn {
  background: #262a36;
  border-color: #4ade80;
  color: #bbf7d0;
}

html[data-theme='dark'] .see-more-btn:hover,
html[data-theme='dark'] .pdf-btn:hover {
  background: #1e3a2a;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.35);
}

html[data-theme='dark'] .filter-item {
  color: #cbd5e1;
}

html[data-theme='dark'] .filter-item select {
  background: #1a1d26;
  border-color: #4b5563;
  color: #f1f5f9;
}

html[data-theme='dark'] .chart-card {
  background: #2e3240;
  border-color: #3d4254;
}

html[data-theme='dark'] .chart-card h3 {
  color: #e2e8f0;
}

html[data-theme='dark'] .line-chart polyline {
  stroke: #86efac;
}

html[data-theme='dark'] .dashboard-footer {
  background: #1a1d26;
  border-top-color: #343845;
  color: #94a3b8;
}

html[data-theme='dark'] .alerts-config-section,
html[data-theme='dark'] .user-management-section {
  background: #262a36;
  border-color: #b45309;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.35);
}

html[data-theme='dark'] .alert-config-card {
  background: #2e3240;
  border-left-color: #fb923c;
}

html[data-theme='dark'] .alert-config-card h3 {
  color: #f1f5f9;
}

html[data-theme='dark'] .config-level {
  background: #1a1d26;
  border-left-color: #666;
}

html[data-theme='dark'] .config-level h4 {
  color: #e2e8f0;
}

html[data-theme='dark'] .config-group label {
  color: #cbd5e1;
}

html[data-theme='dark'] .config-group input {
  background: #1a1d26;
  border-color: #4b5563;
  color: #f1f5f9;
}

html[data-theme='dark'] .save-config-btn {
  background: #15803d;
}

html[data-theme='dark'] .save-config-btn:hover {
  background: #16a34a;
}

html[data-theme='dark'] .user-creation-form {
  background: #2e3240;
}

html[data-theme='dark'] .user-creation-form h3 {
  color: #f1f5f9;
}

html[data-theme='dark'] .form-group label {
  color: #cbd5e1;
}

html[data-theme='dark'] .form-group input,
html[data-theme='dark'] .form-group select {
  background: #1a1d26;
  border-color: #4b5563;
  color: #f1f5f9;
}

html[data-theme='dark'] .users-list-header h3 {
  color: #f1f5f9;
}

html[data-theme='dark'] .users-table th {
  background: #2a2d38;
  color: #e2e8f0;
  border-color: #3d4254;
}

html[data-theme='dark'] .users-table td {
  background: #262a36;
  color: #e2e8f0;
  border-color: #3d4254;
}

html[data-theme='dark'] .role-admin {
  background: #450a0a;
  color: #fecaca;
}

html[data-theme='dark'] .role-employee {
  background: #1e3a5f;
  color: #93c5fd;
}

html[data-theme='dark'] .loading-users,
html[data-theme='dark'] .no-users {
  color: #94a3b8;
}

html[data-theme='dark'] .collapse-btn {
  background: #c2410c;
}

html[data-theme='dark'] .collapse-btn:hover {
  background: #ea580c;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-content {
  background: white;
  border-radius: 8px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e5e7eb;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 28px;
  cursor: pointer;
  color: white;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.close-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.modal-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
  color: #374151;
  font-size: 0.95rem;
}

.form-input,
.form-select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 1rem;
  font-family: inherit;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.help-text {
  display: block;
  margin-top: 4px;
  font-size: 0.85rem;
  color: #6b7280;
}

.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 20px;
}

.btn {
  padding: 10px 16px;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 14px;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-secondary:hover:not(:disabled) {
  background: #e5e7eb;
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.alert {
  padding: 12px 16px;
  border-radius: 6px;
  margin-top: 16px;
  font-size: 0.95rem;
}

.alert-error {
  background: #fee2e2;
  color: #991b1b;
  border: 1px solid #fecaca;
}

html[data-theme='dark'] .modal-content {
  background: #1f2937;
  color: #f3f4f6;
}

html[data-theme='dark'] .modal-header {
  border-bottom-color: #374151;
}

html[data-theme='dark'] .form-group label {
  color: #e5e7eb;
}

html[data-theme='dark'] .form-input,
html[data-theme='dark'] .form-select {
  background: #111827;
  color: #f3f4f6;
  border-color: #4b5563;
}

html[data-theme='dark'] .form-input:focus,
html[data-theme='dark'] .form-select:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
}

html[data-theme='dark'] .help-text {
  color: #9ca3af;
}

html[data-theme='dark'] .btn-secondary {
  background: #374151;
  color: #f3f4f6;
  border-color: #4b5563;
}

html[data-theme='dark'] .btn-secondary:hover:not(:disabled) {
  background: #4b5563;
}

html[data-theme='dark'] .alert-error {
  background: #7f1d1d;
  color: #fecaca;
  border-color: #b91c1c;
}
</style>
