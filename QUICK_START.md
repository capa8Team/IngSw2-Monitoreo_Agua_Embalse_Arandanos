# ⚡ Guía Rápida de Inicio - Sistema de Autenticación

## 🎯 En 5 Minutos

### Paso 1: Preparar Supabase (2 min)

1. Ve a [supabase.com](https://supabase.com) y crea una cuenta
2. Crea un nuevo proyecto llamado `arandanos-monitoring`
3. Espera a que se configure (1-2 minutos)
4. Ve a **Settings → API** y copia:
   - **Project URL**
   - **anon public key**

### Paso 2: Configurar Variables (1 min)

Crea archivo `.env` en la raíz del proyecto:

```env
VITE_SUPABASE_URL=<pega-aqui-project-url>
VITE_SUPABASE_ANON_KEY=<pega-aqui-anon-key>
VITE_API_URL=http://localhost:8000
```

### Paso 3: Configurar Base de Datos (2 min)

1. En Supabase Dashboard → **SQL Editor**
2. Clic en **New Query**
3. Copia todo el contenido de `SUPABASE_SETUP.sql`
4. Pega en el editor y ejecuta (Play button)

✅ ¡Base de datos lista!

### Paso 4: Instalar Dependencias

```bash
npm install
```

### Paso 5: Iniciar la Aplicación

```bash
npm run dev
```

La app estará en `http://localhost:5173`

---

## 🚀 Usar la Aplicación

### Crear Primer Usuario (Admin)

1. Ve a `http://localhost:5173/register`
2. Completa el formulario con:
   - Nombre: `Admin Usuario`
   - Email: `admin@example.com`
   - Contraseña: `demo123`
3. Click en **Crear Cuenta**
4. Ahora ve a **Login** e inicia sesión

### Convertir a Admin

En Supabase → **SQL Editor**, ejecuta:

```sql
UPDATE users_roles 
SET role = 'admin' 
WHERE email = 'admin@example.com';
```

### Inicia Sesión

1. Vuelve a la app y recarga
2. Ve a `/login`
3. Ingresa tus credenciales
4. ¡Serás redirigido al panel de admin!

---

## 👤 Crear Más Usuarios

Como administrador:

1. Vete a **Panel de Admin → Gestión de Usuarios**
2. Clic en **+ Nuevo Usuario**
3. Completa los datos
4. Selecciona rol (Usuario o Admin)
5. Click en **Crear Usuario**

¡El usuario recibe sus credenciales por email!

---

## ⚙️ Configurar Alertas

### Global (para todos los usuarios nuevos)

1. **Panel Admin → Límites de Alertas**
2. Sección **Configuración Global**
3. Ajusta valores:
   - **pH:** 6.5 - 8.5 (recomendado)
   - **Temperatura:** 15 - 30°C (recomendado)
   - **Turbidez:** 0 - 5 NTU (recomendado)
4. Click en **Guardar**

### Para Usuario Específico

1. **Panel Admin → Límites de Alertas**
2. Sección **Límites por Usuario**
3. Selecciona el usuario
4. Ajusta sus límites personalizados
5. Click en **Guardar**

---

## 🧪 Casos de Prueba

### Test 1: Login Correcto
```
Email: admin@example.com
Password: demo123
Esperado: Redirige a /admin
```

### Test 2: Login Incorrecto
```
Email: admin@example.com
Password: wrong
Esperado: Muestra error
```

### Test 3: Crear Usuario
```
Acción: En /admin/users, crear nuevo usuario
Esperado: Usuario aparece en tabla
```

### Test 4: Protección de Rutas
```
Acción: Acceder a /admin sin autenticación
Esperado: Redirige a /login
```

---

## 🐛 Si Algo No Funciona

### Error: "Variables de Supabase no configuradas"
- [ ] Verifica que existe `.env` en la raíz
- [ ] Verifica variables tienen valores (no vacías)
- [ ] Reinicia el servidor (`npm run dev`)

### Error: "No puedes acceder a esta página"
- [ ] Verifica que estés logueado
- [ ] Verifica tu rol (admin vs user)
- [ ] Revisa la consola (F12)

### Email de confirmación no llega
- [ ] En Supabase, ve a Auth → Providers
- [ ] Verifica que Email esté habilitado
- [ ] Usa admin@example.com si está en modo test

### Base de datos vacía
- [ ] Verifica que ejecutaste SUPABASE_SETUP.sql
- [ ] En Supabase → SQL Editor → verificar ejecución
- [ ] Ejecutar nuevamente si es necesario

---

## 📱 Pantallas Principales

### Pantalla de Login
```
┌─────────────────────┐
│  🌊 Monitoreo       │
│     Embalse         │
├─────────────────────┤
│ Email: [________]   │
│ Pass:  [________]   │
│ [Iniciar Sesión]    │
│                     │
│ ¿No tienes cuenta?  │
│ Regístrate aquí     │
└─────────────────────┘
```

### Panel de Admin
```
┌──────────────────────────────┐
│ 👨‍💼 Panel de Administración   │
├──────────────────────────────┤
│ 📊 Dashboard                 │
│ 👥 Gestión de Usuarios       │
│ 🚨 Límites de Alertas        │
├──────────────────────────────┤
│ Estadísticas:                │
│ - Total de Usuarios: 24      │
│ - Dispositivos Activos: 5    │
│ - Alertas Pendientes: 3      │
└──────────────────────────────┘
```

### Dashboard de Usuario
```
┌──────────────────────────────┐
│ Sensor Estación 1            │
├──────────────────────────────┤
│ ┌────────────────┐           │
│ │ pH: 7.2 ✓      │           │
│ ├────────────────┤           │
│ │ Temp: 22.5°C ✓ │           │
│ ├────────────────┤           │
│ │ TBD: 1.2 NTU ✓ │           │
│ └────────────────┘           │
└──────────────────────────────┘
```

---

## 📚 Archivos Importantes

```
src/
├── router.js               👈 Rutas
├── stores/
│   └── authStore.js        👈 Estado
├── services/
│   └── supabaseClient.js    👈 API
└── views/
    ├── Login.vue           👈 Inicio
    ├── AdminDashboard.vue  👈 Admin
    ├── AdminUsers.vue      👈 Usuarios
    └── AdminAlerts.vue     👈 Alertas
```

---

## 🔐 Roles y Permisos

### Usuario Normal
- ✅ Ver dispositivos
- ✅ Ver sensores
- ✅ Ver histórico
- ❌ Crear usuarios
- ❌ Cambiar alertas globales

### Administrador
- ✅ Ver todo
- ✅ Crear usuarios
- ✅ Cambiar roles
- ✅ Configurar alertas
- ✅ Eliminar usuarios

---

## 📞 Necesitas Más Ayuda?

1. **Documentación Completa:** Ver `AUTHENTICATION_GUIDE.md`
2. **Cambios Realizados:** Ver `CHANGELOG.md`
3. **SQL Setup:** Ver `SUPABASE_SETUP.sql`
4. **Consola del Navegador:** F12 → Console (errores)
5. **Supabase Dashboard:** Verificar estado de BD

---

## ✅ Checklist

- [ ] Creé cuenta en Supabase
- [ ] Copié credenciales
- [ ] Creé archivo `.env`
- [ ] Ejecuté `SUPABASE_SETUP.sql`
- [ ] Ejecuté `npm install`
- [ ] Ejecuté `npm run dev`
- [ ] Accedí a `/login`
- [ ] Creé usuario admin
- [ ] Convertí a admin con SQL
- [ ] Logueé correctamente
- [ ] ✅ ¡Listo para usar!

---

**¡Felicidades!** 🎉  
Tu sistema de autenticación está listo.

*Última actualización: 2026-04-07*
