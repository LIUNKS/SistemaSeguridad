# Sistema de Autenticación Dual

> **Autenticación avanzada combinando métodos tradicionales y biométricos (reconocimiento facial) con seguridad de nivel profesional.**

---

## Tabla de Contenidos

1. [Descripción General](#descripción-general)
2. [Características](#características)
3. [Instalación](#instalación)
4. [Guía de Uso](#guía-de-uso)
5. [Arquitectura](#arquitectura)
6. [Tecnologías](#tecnologías)
7. [Configuración Avanzada](#configuración-avanzada)
8. [Base de Datos](#base-de-datos)
9. [Solución de Problemas](#solución-de-problemas)
10. [Notas Importantes](#notas-importantes)
11. [Contribución](#contribución)
12. [Licencia](#licencia)
13. [Autor](#autor)
14. [Agradecimientos](#agradecimientos)
15. [Estado del Proyecto](#estado-del-proyecto)

---

## 1. Descripción General

Sistema de autenticación dual que integra:

- **Email y contraseña** (tradicional)
- **Reconocimiento facial** (biométrico, en tiempo real)

Ideal para aplicaciones que requieren máxima seguridad y experiencia de usuario moderna.

---

## 2. Características

- **Autenticación dual:** Email/contraseña + reconocimiento facial
- **Reconocimiento facial avanzado:** Preciso y rápido, con umbrales configurables
- **Base de datos segura:** MySQL, contraseñas encriptadas (bcrypt)
- **Interfaz gráfica moderna:** Tkinter
- **Registro de actividad:** Logging detallado de intentos de autenticación
- **Seguridad avanzada:** Bloqueo de cuentas, umbrales biométricos, control de sesiones

---

## 3. Instalación

### Prerrequisitos

- Python 3.8 o superior
- MySQL Server
- Cámara web

### Pasos

1. **Clonar el repositorio:**
   ```bash
   git clone <repository-url>
   cd SistemaSeguridad
   ```
2. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configurar base de datos:**
   - Instalar MySQL Server
   - Crear la base de datos `dual_auth_system`
   - Editar credenciales en `config/database_config.py`
4. **Ejecutar el sistema:**
   ```bash
   python main.py
   ```

---

## 4. Guía de Uso

### Registro de Usuario

1. Ejecutar el sistema
2. Ir a la pestaña **Registro**
3. Completar los campos requeridos
4. Clic en **Registrar Usuario**

### Configuración Biométrica

1. Ir a la pestaña **Reconocimiento Facial**
2. Clic en **Activar Cámara**
3. Seguir instrucciones para registrar el rostro

### Autenticación

- **Tradicional:** Email y contraseña
- **Biométrica:** Reconocimiento facial

---

## 5. Arquitectura

```text
SistemaSeguridad/
├── main.py                  # Punto de entrada principal
├── src/
│   ├── dual_auth_system.py  # Lógica principal e interfaz
│   ├── face_encoder.py      # Procesamiento biométrico
│   └── database/
│       └── dual_auth_backend.py # Backend de base de datos
├── config/
│   └── database_config.py   # Configuración de BD
├── requirements.txt         # Dependencias
├── LICENSE                  # Licencia MIT
└── README.md                # Documentación
```

---

## 6. Tecnologías

- **Python 3.8+**
- **OpenCV** (procesamiento de imágenes)
- **face-recognition** (biometría facial)
- **Tkinter** (GUI)
- **MySQL** (base de datos)
- **bcrypt** (encriptación)
- **Pillow** (imágenes)
- **NumPy** (matemáticas)

---

## 7. Configuración Avanzada

### Umbrales de Confianza Biométrica

| Rango     | Descripción                                     |
| --------- | ----------------------------------------------- |
| 0.0 - 0.4 | Muy seguro (idéntico, condiciones óptimas)      |
| 0.4 - 0.6 | Seguro (variaciones normales) **(Recomendado)** |
| 0.6 - 0.8 | Precaución (posible coincidencia)               |
| 0.8+      | Rechazar (rostros diferentes)                   |

### Seguridad

- Umbrales y parámetros configurables en el código fuente
- Intentos máximos de login
- Configuración de cámara y detección facial
- Encriptación robusta

---

## 8. Base de Datos

Tablas principales:

- **users:** Usuarios y credenciales
- **user_biometrics:** Datos biométricos encriptados
- **user_sessions:** Sesiones activas
- **auth_logs:** Registro de autenticaciones

---

## 9. Solución de Problemas

### Problemas Frecuentes

**Cámara no detectada:**

- Verifique que ninguna otra aplicación esté usando la cámara
- Revise permisos de cámara

**Reconocimiento facial falla:**

- Buena iluminación y rostro centrado
- Ajuste el umbral de confianza si es necesario

**Error de conexión a la base de datos:**

- Asegúrese de que MySQL esté ejecutándose
- Revise credenciales en `config/database_config.py`

---

## 10. Notas Importantes

- **Archivo principal:** `main.py`
- **Configuración:** Solo requiere `config/database_config.py` con credenciales
- **Dependencias:** Listadas en `requirements.txt`
- **Estructura simple y funcional**

---

## 11. Contribución

1. Realice un fork del proyecto
2. Cree una rama (`git checkout -b feature/NuevaFuncionalidad`)
3. Realice commits descriptivos
4. Haga push a su rama
5. Abra un Pull Request

---

## 12. Licencia

Proyecto bajo Licencia MIT. Consulte el archivo [LICENSE](LICENSE) para más detalles.

---

## 13. Autor

**Johann Camiloaga**  
Email: jgcamiloaga@gmail.com

---

## 14. Agradecimientos

- OpenCV (procesamiento de imágenes)
- Comunidad Python (librerías y soporte)
- Contribuidores y testers

---

## 15. Estado del Proyecto

> **✅ COMPLETAMENTE FUNCIONAL**

El sistema está desarrollado, probado y listo para producción.
