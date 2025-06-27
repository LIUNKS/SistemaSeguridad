# 🔐 Sistema de Autenticación Dual

Un sistema moderno de autenticación que combina métodos tradicionales (email/contraseña) con autenticación biométrica avanzada usando reconocimiento facial.

## ✨ Características Principales

- **🔑 Autenticación Dual**: Email/contraseña + Reconocimiento facial
- **👤 Reconocimiento Facial**: Detección y autenticación biométrica en tiempo real
- **🗄️ Base de Datos Segura**: MySQL con encriptación de contraseñas
- **🖥️ Interfaz Gráfica**: Tkinter con diseño moderno y intuitivo
- **📊 Logging Completo**: Registro detallado de intentos de autenticación
- **🔒 Seguridad Avanzada**: Bloqueo de cuentas, umbrales de confianza ajustables

## 🚀 Instalación y Configuración

### Prerrequisitos

- Python 3.8+
- MySQL Server
- Cámara web (para autenticación biométrica)

### Instalación

1. **Clonar el repositorio**:

   ```bash
   git clone <repository-url>
   cd SistemaSeguridad
   ```

2. **Instalar dependencias**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar base de datos**:

   - Instalar MySQL Server
   - Crear base de datos `dual_auth_system`
   - Actualizar credenciales en `config/database_config.py`

4. **Ejecutar el sistema**:
   ```bash
   python main.py
   ```

## 📋 Uso del Sistema

### 1. Registro de Usuario

1. Ejecutar el sistema
2. Ir a la pestaña "Registro"
3. Completar todos los campos requeridos
4. Hacer clic en "Registrar Usuario"

### 2. Configuración Biométrica

1. Ir a la pestaña "Reconocimiento Facial"
2. Hacer clic en "Activar Cámara"
3. Posicionarse frente a la cámara
4. Seguir las instrucciones para registrar el rostro

### 3. Autenticación

- **Tradicional**: Email y contraseña en la pestaña "Email y Contraseña"
- **Biométrica**: Reconocimiento facial en la pestaña "Reconocimiento Facial"

## 🏗️ Arquitectura del Sistema

```
SistemaSeguridad/
├── main.py                    # Punto de entrada principal
├── src/
│   ├── dual_auth_system.py    # Sistema principal e interfaz
│   ├── face_encoder.py        # Procesamiento de rostros
│   └── database/
│       └── dual_auth_backend.py # Gestión de base de datos
├── config/
│   └── database_config.py     # Configuración de BD
├── requirements.txt           # Dependencias
├── LICENSE                    # Licencia MIT
├── .gitignore                # Archivos ignorados por Git
└── README.md                 # Este archivo
```

## 🛠️ Tecnologías Utilizadas

- **Python 3.8+**: Lenguaje principal
- **OpenCV**: Procesamiento de imágenes y detección facial
- **Tkinter**: Interfaz gráfica
- **MySQL**: Base de datos
- **bcrypt**: Encriptación de contraseñas
- **Pillow**: Manipulación de imágenes
- **NumPy**: Operaciones matemáticas

## ⚙️ Configuración Avanzada

### Umbrales de Confianza Biométrica

- **0.0 - 0.4**: Muy seguro (mismo rostro, condiciones similares)
- **0.4 - 0.6**: Seguro (mismo rostro, variaciones normales) - **Recomendado**
- **0.6 - 0.8**: Precaución (podría ser la misma persona)
- **0.8+**: Rechazar (diferentes personas)

### Configuración de Seguridad

Las configuraciones de seguridad están integradas directamente en el código fuente:

- Umbrales de confianza biométrica
- Intentos de login máximos
- Configuraciones de cámara y detección facial
- Parámetros de encriptación

## 📊 Base de Datos

### Tablas Principales:

- **users**: Información de usuarios y credenciales
- **user_biometrics**: Datos biométricos encriptados
- **user_sessions**: Sesiones activas
- **auth_logs**: Registro de intentos de autenticación

## 🔧 Solución de Problemas

### Problemas Comunes:

1. **Cámara no detectada**:

   - Verificar que ninguna otra aplicación use la cámara
   - Verificar permisos de cámara

2. **Reconocimiento facial falla**:

   - Asegurar buena iluminación
   - Posicionarse centrado frente a la cámara
   - Verificar umbral de confianza

3. **Error de conexión a BD**:
   - Verificar que MySQL esté ejecutándose
   - Verificar credenciales en `config/database_config.py`

## � Notas Importantes

- **Archivo principal**: `main.py` - Este es el punto de entrada del sistema
- **Configuración**: Solo se requiere `config/database_config.py` con las credenciales de MySQL
- **Dependencias**: Todas las librerías necesarias están en `requirements.txt`
- **Estructura simple**: El proyecto ha sido optimizado para máxima simplicidad y funcionalidad

## 🤝 Contribución

1. Fork el proyecto
2. Crear rama para feature (`git checkout -b feature/NuevaFuncionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/NuevaFuncionalidad`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 👨‍💻 Autor

**Johann Camiloaga**

- Email: jgcamiloaga@gmail.com

## 🙏 Agradecimientos

- OpenCV por las herramientas de procesamiento de imágenes
- La comunidad de Python por las excelentes librerías
- Todos los contribuidores y testers del proyecto

---

## 📈 Estado del Proyecto: ✅ COMPLETAMENTE FUNCIONAL

El sistema ha sido completamente desarrollado, probado y está listo para uso en producción.
