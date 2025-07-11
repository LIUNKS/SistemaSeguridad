#!/usr/bin/env python3
"""
Sistema de Autenticación Dual - Base de Datos Expandida
Soporte para autenticación tradicional y biométrica
"""

import mysql.connector
from mysql.connector import Error
import hashlib
import json
import uuid
from datetime import datetime
import bcrypt
import sys
import os

# Importar configuración de base de datos
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'config'))
from database_config import get_database_config

class DualAuthDatabase:
    def get_auth_logs(self, limit=50, user_id=None, email=None):
        """Obtener historial de autenticaciones desde la tabla auth_logs"""
        if not self.connection:
            self.connect()
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT id, user_id, email, auth_method, status, failure_reason, ip_address, timestamp FROM auth_logs"
            params = []
            filters = []
            if user_id:
                filters.append("user_id = %s")
                params.append(user_id)
            if email:
                filters.append("email = %s")
                params.append(email)
            if filters:
                query += " WHERE " + " AND ".join(filters)
            query += " ORDER BY timestamp DESC LIMIT %s"
            params.append(limit)
            cursor.execute(query, tuple(params))
            logs = cursor.fetchall()
            return logs
        except Error as e:
            print(f"Error al obtener historial de autenticaciones: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
    """Base de datos expandida para autenticación dual"""
    
    def __init__(self):
        # Obtener configuración de base de datos
        try:
            config = get_database_config()
            self.host = config['host']
            self.database = config['database']
            self.user = config['user']
            self.password = config['password']
            self.port = config.get('port', 3306)
        except:
            # Configuración por defecto
            self.host = 'localhost'
            self.database = 'dual_auth_system'
            self.user = 'root'
            self.password = 'Johan12315912'
            self.port = 3306
        
        self.connection = None
    
    def connect(self, use_database=True):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                database=self.database if use_database else None,
                user=self.user,
                password=self.password,
                autocommit=True
            )
            
            if self.connection.is_connected():
                print(f"✅ Conectado a MySQL: {self.database if use_database else 'servidor'}")
                return True
                
        except Error as e:
            print(f"❌ Error conectando a MySQL: {e}")
            return False
    
    def create_database_and_tables(self):
        """Crear base de datos y todas las tablas necesarias"""
        try:
            # Conectar sin especificar base de datos
            if not self.connect(use_database=False):
                return False
            
            cursor = self.connection.cursor()
            
            # Crear base de datos
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            print(f"✅ Base de datos '{self.database}' creada/verificada")
            
            # Usar la base de datos
            cursor.execute(f"USE {self.database}")
            
            # Tabla principal de usuarios
            create_users_table = """
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(64) PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                username VARCHAR(100) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                phone VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP NULL,
                is_active BOOLEAN DEFAULT TRUE,
                email_verified BOOLEAN DEFAULT FALSE,
                face_registered BOOLEAN DEFAULT FALSE,
                biometric_enabled BOOLEAN DEFAULT FALSE,
                login_attempts INT DEFAULT 0,
                locked_until TIMESTAMP NULL
            )
            """
            
            # Tabla de datos biométricos (separada para seguridad)
            create_biometric_table = """
            CREATE TABLE IF NOT EXISTS user_biometrics (
                id VARCHAR(64) PRIMARY KEY,
                user_id VARCHAR(64) NOT NULL,
                face_encoding TEXT NOT NULL,
                face_model_version VARCHAR(20) DEFAULT 'v1.0',
                registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_verification TIMESTAMP NULL,
                verification_count INT DEFAULT 0,
                confidence_threshold FLOAT DEFAULT 0.6,
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
            
            # Tabla de sesiones
            create_sessions_table = """
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id VARCHAR(128) PRIMARY KEY,
                user_id VARCHAR(64) NOT NULL,
                auth_method ENUM('password', 'biometric', 'dual') NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                ip_address VARCHAR(45),
                user_agent TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
            
            # Tabla de logs de autenticación
            create_auth_logs_table = """
            CREATE TABLE IF NOT EXISTS auth_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(64),
                email VARCHAR(255),
                auth_method ENUM('password', 'biometric', 'registration') NOT NULL,
                status ENUM('success', 'failed', 'blocked') NOT NULL,
                failure_reason VARCHAR(255),
                ip_address VARCHAR(45),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_user_timestamp (user_id, timestamp),
                INDEX idx_email_timestamp (email, timestamp)
            )
            """
            
            # Ejecutar creación de tablas
            for table_query in [create_users_table, create_biometric_table, 
                              create_sessions_table, create_auth_logs_table]:
                cursor.execute(table_query)
            
            print("✅ Todas las tablas creadas/verificadas correctamente")
            return True
            
        except Error as e:
            print(f"❌ Error creando base de datos: {e}")
            return False
        finally:
            if self.connection and self.connection.is_connected():
                cursor.close()
    
    def hash_password(self, password: str) -> str:
        """Hashear contraseña con bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verificar contraseña"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def register_user(self, email: str, username: str, password: str, 
                     first_name: str = None, last_name: str = None, phone: str = None, ip_address: str = None) -> dict:
        """Registrar nuevo usuario"""
        try:
            if not self.connection:
                self.connect()
            
            cursor = self.connection.cursor()
            
            # Verificar si el email ya existe
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                return {"success": False, "error": "El email ya está registrado"}
            
            # Crear nuevo usuario
            user_id = str(uuid.uuid4())
            password_hash = self.hash_password(password)
            
            insert_query = """
            INSERT INTO users (id, email, username, password_hash, first_name, last_name, phone)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(insert_query, (user_id, email, username, password_hash, 
                                        first_name, last_name, phone))
            
            # Log del registro
            self.log_auth_attempt(user_id, email, 'registration', 'success', ip_address=ip_address)
            
            return {
                "success": True, 
                "user_id": user_id,
                "message": "Usuario registrado exitosamente"
            }
            
        except Error as e:
            return {"success": False, "error": f"Error en registro: {e}"}
        finally:
            if cursor:
                cursor.close()
    
    def authenticate_user(self, email: str, password: str, ip_address: str = None) -> dict:
        """Autenticar usuario con email y contraseña"""
        try:
            if not self.connection:
                self.connect()
            
            cursor = self.connection.cursor(dictionary=True)
            
            # Obtener usuario
            cursor.execute("""
                SELECT id, email, username, password_hash, first_name, last_name, is_active, 
                       login_attempts, locked_until, face_registered
                FROM users WHERE email = %s
            """, (email,))
            
            user = cursor.fetchone()
            
            if not user:
                self.log_auth_attempt(None, email, 'password', 'failed', 'User not found', ip_address=ip_address)
                return {"success": False, "error": "Credenciales inválidas"}
            
            # Verificar si está bloqueado
            if user['locked_until'] and datetime.now() < user['locked_until']:
                self.log_auth_attempt(user['id'], email, 'password', 'blocked', 'Account locked', ip_address=ip_address)
                return {"success": False, "error": "Cuenta temporalmente bloqueada"}
            
            # Verificar si está activo
            if not user['is_active']:
                self.log_auth_attempt(user['id'], email, 'password', 'failed', 'Account disabled', ip_address=ip_address)
                return {"success": False, "error": "Cuenta desactivada"}
            
            # Verificar contraseña
            if not self.verify_password(password, user['password_hash']):
                # Incrementar intentos fallidos
                self.increment_login_attempts(user['id'])
                self.log_auth_attempt(user['id'], email, 'password', 'failed', 'Wrong password', ip_address=ip_address)
                return {"success": False, "error": "Credenciales inválidas"}
            
            # Autenticación exitosa
            self.reset_login_attempts(user['id'])
            self.update_last_login(user['id'])
            self.log_auth_attempt(user['id'], email, 'password', 'success', ip_address=ip_address)
            
            return {
                "success": True,
                "user": {
                    "id": user['id'],
                    "email": user['email'],
                    "username": user['username'],
                    "first_name": user.get('first_name', ''),
                    "last_name": user.get('last_name', ''),
                    "face_registered": bool(user['face_registered'])
                }
            }
            
        except Error as e:
            return {"success": False, "error": f"Error en autenticación: {e}"}
        finally:
            if cursor:
                cursor.close()
    
    def register_face_biometric(self, user_id: str, face_encoding: list) -> dict:
        """Registrar datos biométricos del rostro"""
        try:
            if not self.connection:
                self.connect()
            
            cursor = self.connection.cursor()
            
            # Convertir numpy array a lista si es necesario
            if hasattr(face_encoding, 'tolist'):
                face_encoding = face_encoding.tolist()
            
            print(f"🔄 DEBUG: Registrando biometría para usuario {user_id}")
            print(f"🔄 DEBUG: Encoding length: {len(face_encoding)}")
            
            # Verificar si ya tiene biometría registrada
            cursor.execute("SELECT id FROM user_biometrics WHERE user_id = %s", (user_id,))
            existing = cursor.fetchone()
            
            biometric_id = str(uuid.uuid4())
            encoding_json = json.dumps(face_encoding)
            
            if existing:
                print("🔄 DEBUG: Actualizando biometría existente")
                # Actualizar existente
                cursor.execute("""
                    UPDATE user_biometrics 
                    SET face_encoding = %s, registration_date = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                """, (encoding_json, user_id))
            else:
                print("🔄 DEBUG: Creando nuevo registro biométrico")
                # Crear nuevo registro
                cursor.execute("""
                    INSERT INTO user_biometrics (id, user_id, face_encoding)
                    VALUES (%s, %s, %s)
                """, (biometric_id, user_id, encoding_json))
            
            # Actualizar flags en usuario
            print("🔄 DEBUG: Actualizando flags face_registered y biometric_enabled en usuario")
            cursor.execute("""
                UPDATE users SET face_registered = TRUE, biometric_enabled = TRUE WHERE id = %s
            """, (user_id,))
            
            # ¡IMPORTANTE! Hacer commit de los cambios
            self.connection.commit()
            print("✅ DEBUG: Commit realizado exitosamente")
            
            cursor.close()
            
            return {"success": True, "message": "Biometría registrada exitosamente"}
            
        except Error as e:
            print(f"❌ DEBUG: Error MySQL en register_face_biometric: {e}")
            if self.connection:
                self.connection.rollback()
            return {"success": False, "error": f"Error registrando biometría: {e}"}
        except Exception as e:
            print(f"❌ DEBUG: Error general en register_face_biometric: {e}")
            if self.connection:
                self.connection.rollback()
            return {"success": False, "error": f"Error inesperado: {e}"}
    
    def authenticate_biometric(self, face_encoding: list, threshold: float = 0.6, ip_address: str = None) -> dict:
        """Autenticar usuario por biometría facial"""
        try:
            if not self.connection:
                self.connect()
            
            cursor = self.connection.cursor(dictionary=True)
            
            # Debug: Verificar el encoding recibido
            print(f"🔍 DEBUG: Intentando autenticación biométrica")
            print(f"🔍 DEBUG: Encoding recibido: {len(face_encoding)} dimensiones")
            print(f"🔍 DEBUG: Umbral de confianza: {threshold}")
            
            # Obtener todos los usuarios con biometría activa
            cursor.execute("""
                SELECT b.user_id, b.face_encoding, u.email, u.username, u.first_name, u.last_name, u.is_active, u.face_registered, u.biometric_enabled
                FROM user_biometrics b
                JOIN users u ON b.user_id = u.id
                WHERE b.is_active = TRUE AND u.is_active = TRUE AND u.biometric_enabled = TRUE
            """)
            
            biometric_users = cursor.fetchall()
            
            print(f"🔍 DEBUG: Usuarios con biometría encontrados: {len(biometric_users)}")
            
            if not biometric_users:
                print("❌ DEBUG: No hay usuarios con biometría registrada y activa")
                return {"success": False, "error": "No hay usuarios con biometría registrada"}
            
            # Debug: Mostrar usuarios encontrados
            for user in biometric_users:
                print(f"🔍 DEBUG: Usuario {user['username']} - biometric_enabled: {user['biometric_enabled']}, face_registered: {user['face_registered']}")
            
            # Comparar con cada encoding registrado
            import numpy as np
            
            best_match = None
            best_distance = float('inf')
            
            for bio_user in biometric_users:
                stored_encoding = json.loads(bio_user['face_encoding'])
                print(f"🔍 DEBUG: Comparando con {bio_user['username']} (encoding: {len(stored_encoding)} dim)")
                
                distance = np.linalg.norm(np.array(face_encoding) - np.array(stored_encoding))
                print(f"🔍 DEBUG: Distancia calculada: {distance:.4f}")
                
                if distance < best_distance:
                    best_distance = distance
                    best_match = bio_user
                    print(f"🔍 DEBUG: Nuevo mejor match: {bio_user['username']} (distancia: {distance:.4f})")
            
            print(f"🔍 DEBUG: Mejor match final: {best_match['username'] if best_match else 'None'}")
            print(f"🔍 DEBUG: Distancia final: {best_distance:.4f}, Umbral: {threshold}")
            
            # Verificar si está dentro del umbral
            if best_match and best_distance < threshold:
                print(f"✅ DEBUG: Autenticación exitosa para {best_match['username']}")
                user_id = best_match['user_id']
                
                # Actualizar estadísticas
                cursor.execute("""
                    UPDATE user_biometrics 
                    SET last_verification = CURRENT_TIMESTAMP, verification_count = verification_count + 1
                    WHERE user_id = %s
                """, (user_id,))
                
                self.update_last_login(user_id)
                self.log_auth_attempt(user_id, best_match['email'], 'biometric', 'success', ip_address=ip_address)
                
                return {
                    "success": True,
                    "user": {
                        "id": user_id,
                        "email": best_match['email'],
                        "username": best_match['username'],
                        "first_name": best_match.get('first_name', ''),
                        "last_name": best_match.get('last_name', ''),
                        "face_registered": best_match.get('face_registered', True)
                    },
                    "confidence": 1.0 - (best_distance / threshold)
                }
            else:
                print(f"❌ DEBUG: Autenticación rechazada - distancia {best_distance:.4f} > umbral {threshold}")
                self.log_auth_attempt(None, None, 'biometric', 'failed', 'No biometric match', ip_address=ip_address)
                return {"success": False, "error": "No se pudo verificar la identidad biométrica"}
            
        except Exception as e:
            print(f"❌ DEBUG: Error en authenticate_biometric: {e}")
            return {"success": False, "error": f"Error en autenticación biométrica: {e}"}
        finally:
            if cursor:
                cursor.close()
    
    def log_auth_attempt(self, user_id: str, email: str, method: str, status: str, reason: str = None, ip_address: str = None):
        """Registrar intento de autenticación"""
        try:
            if not self.connection:
                return
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO auth_logs (user_id, email, auth_method, status, failure_reason, ip_address)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, email, method, status, reason, ip_address))
        except Error as e:
            print(f"Error logging auth attempt: {e}")
        finally:
            if cursor:
                cursor.close()
    
    def increment_login_attempts(self, user_id: str):
        """Incrementar intentos de login fallidos"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE users SET login_attempts = login_attempts + 1
                WHERE id = %s
            """, (user_id,))
            
            # Bloquear si supera 5 intentos
            cursor.execute("""
                UPDATE users SET locked_until = DATE_ADD(NOW(), INTERVAL 15 MINUTE)
                WHERE id = %s AND login_attempts >= 5
            """, (user_id,))
            
        except Error as e:
            print(f"Error incrementing login attempts: {e}")
        finally:
            if cursor:
                cursor.close()
    
    def reset_login_attempts(self, user_id: str):
        """Resetear intentos de login"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE users SET login_attempts = 0, locked_until = NULL
                WHERE id = %s
            """, (user_id,))
        except Error as e:
            print(f"Error resetting login attempts: {e}")
        finally:
            if cursor:
                cursor.close()
    
    def update_last_login(self, user_id: str):
        """Actualizar último login"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE users SET last_login = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (user_id,))
        except Error as e:
            print(f"Error updating last login: {e}")
        finally:
            if cursor:
                cursor.close()
    
    def get_user_profile(self, user_id: str) -> dict:
        """Obtener perfil completo del usuario"""
        try:
            if not self.connection:
                self.connect()
            
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT u.*, 
                       CASE WHEN b.id IS NOT NULL THEN TRUE ELSE FALSE END as has_biometric
                FROM users u
                LEFT JOIN user_biometrics b ON u.id = b.user_id AND b.is_active = TRUE
                WHERE u.id = %s
            """, (user_id,))
            
            return cursor.fetchone()
            
        except Error as e:
            return None
        finally:
            if cursor:
                cursor.close()
    
    def close(self):
        """Cerrar conexión"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("✅ Conexión MySQL cerrada")

if __name__ == "__main__":
    # Test de la base de datos
    db = DualAuthDatabase()
    
    print("🔧 Inicializando sistema de autenticación dual...")
    if db.create_database_and_tables():
        print("✅ Sistema de base de datos listo")
    else:
        print("❌ Error inicializando base de datos")
    
    db.close()
