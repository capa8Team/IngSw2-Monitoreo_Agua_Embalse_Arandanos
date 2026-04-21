# Monitoreo de Agua Embalse Arándanos

## Descripción del sistema

Este proyecto implementa una plataforma de monitoreo de calidad de agua para embalses de arándanos. Integra adquisición de datos desde dispositivos Arduino/ESP8266, procesamiento y exposición de datos mediante un backend FastAPI, almacenamiento en MongoDB y visualización en tiempo real desde una aplicación web en Vue.

El sistema soporta operación con datos reales de sensores y modo simulado para pruebas y desarrollo.

## Funcionalidades principales

- Visualización en tiempo real de pH, temperatura y conductividad.
- Dashboard por dispositivo con estado de conexión y diagnóstico de solicitudes.
- Gestión de alertas por rangos configurables.
- Registro histórico con gráficos y exportación PDF con filtros.
- Gestión de usuarios y roles (administrador y empleado) usando Supabase.
- Integración de notificaciones de alerta.
- Soporte de despliegue local con Docker Compose.

## Arquitectura

La solución está organizada en cuatro capas principales:

1. Capa de adquisición de datos
- Firmware en Arduino/ESP8266 para lectura de sensores.
- Envío de mediciones al backend vía HTTP.

2. Capa de servicios backend
- API REST en FastAPI.
- Procesamiento de lecturas, control de alertas y endpoints de dashboard/histórico.

3. Capa de persistencia
- MongoDB para datos de sensores e histórico de lecturas.
- Supabase para autenticación, usuarios, roles y configuración administrativa.
- PostgreSQL de apoyo en entorno de contenedores cuando se levanta con Docker Compose.

4. Capa de presentación
- Frontend en Vue 3 + Vite.
- Vistas para dispositivos conectados, dashboard, alertas, administración e histórico.

## Instalación

Para el paso a paso de instalación y puesta en marcha, revisar:

- QUICK_START.md
