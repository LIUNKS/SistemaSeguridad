#!/usr/bin/env python3
"""
Sistema de Autenticación Dual
Maneja tanto autenticación tradicional como biométrica
"""

import tkinter as tk
from tkinter import ttk, messagebox, font
import cv2
import numpy as np
from PIL import Image, ImageTk
import threading
import sys
import os

import socket  # Para obtener la IP local

# Añadir rutas
sys.path.append(os.path.join(os.path.dirname(__file__), 'database'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.dual_auth_backend import DualAuthDatabase
from face_encoder import RobustFaceEncoder

class DualAuthSystem:
    """Sistema principal de autenticación dual"""
    
    def __init__(self):
        self.db = DualAuthDatabase()
        self.face_encoder = RobustFaceEncoder()
        self.current_user = None
        self.camera = None
        self.camera_active = False
        
        # Inicializar base de datos
        self.db.create_database_and_tables()
    
    def start_login_interface(self):
        """Iniciar interfaz de login"""
        self.login_window = LoginWindow(self)
        self.login_window.root.mainloop()
    
    def authenticate_password(self, email: str, password: str) -> dict:
        """Autenticar con email y contraseña, registrando IP local"""
        ip_address = self.get_local_ip()
        return self.db.authenticate_user(email, password, ip_address=ip_address)
    
    def authenticate_biometric(self, face_encoding: list) -> dict:
        """Autenticar con biometría, registrando IP local"""
        ip_address = self.get_local_ip()
        return self.db.authenticate_biometric(face_encoding, ip_address=ip_address)
    
    def register_user(self, user_data: dict) -> dict:
        """Registrar nuevo usuario, registrando IP local"""
        ip_address = self.get_local_ip()
        return self.db.register_user(**user_data, ip_address=ip_address)
    def get_local_ip(self):
        """Obtener la IP local de la máquina"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
    
    def register_face_biometric(self, user_id: str, face_encoding: list) -> dict:
        """Registrar biometría facial"""
        return self.db.register_face_biometric(user_id, face_encoding)
    
    def refresh_user_state(self, user_id: str):
        """Actualizar estado del usuario tras registro biométrico"""
        try:
            # Actualizar el usuario actual si coincide
            if (self.current_user and 
                str(self.current_user.get('id')) == str(user_id)):
                
                # Marcar que ahora tiene biometría registrada
                self.current_user['face_registered'] = True
                print(f"✅ DEBUG: Estado actualizado para usuario {user_id} - Biometría: Sí")
                
                # Si hay una aplicación principal abierta, actualizar su interfaz
                if hasattr(self, 'main_app') and self.main_app:
                    self.main_app.refresh_biometric_status()
                    print("🔄 DEBUG: Interfaz principal actualizada")
                    
        except Exception as e:
            print(f"❌ DEBUG: Error actualizando estado del usuario: {e}")
    
    def start_main_application(self, user: dict):
        """Iniciar aplicación principal después del login"""
        self.current_user = user
        print(f"✅ Usuario autenticado: {user['username']} ({user['email']})")
        
        # Cerrar ventana de login
        if hasattr(self, 'login_window'):
            self.login_window.root.destroy()
        
        # Abrir aplicación principal
        self.main_app = MainApplication(self, user)
        self.main_app.root.mainloop()

class LoginWindow:
    """Ventana de login con opciones duales"""
    
    def __init__(self, auth_system: DualAuthSystem):
        self.auth_system = auth_system
        self.setup_ui()
        
    def cleanup(self):
        """Limpiar recursos antes de cerrar"""
        try:
            # Detener cámara si está activa
            if hasattr(self.auth_system, 'camera_active') and self.auth_system.camera_active:
                self.auth_system.stop_camera()
        except:
            pass
    
    def on_closing(self):
        """Manejar cierre de ventana"""
        self.cleanup()
        self.root.quit()
        self.root.destroy()
        
    def setup_ui(self):
        """Configurar interfaz de usuario"""
        self.root = tk.Tk()
        self.root.title("Sistema de Autenticación Dual")
        self.root.geometry("1000x800")  # Más grande para asegurar que todo sea visible
        self.root.configure(bg='#f0f0f0')
        
        # Configurar protocolo de cierre
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Estilos
        self.setup_styles()
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(
            main_frame, 
            text="🔐 Sistema de Autenticación", 
            font=('Arial', 24, 'bold'),
            foreground='#2c3e50'
        )
        title_label.pack(pady=(0, 30))
        
        # Notebook para tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Tab 1: Login tradicional
        self.create_password_tab()
        
        # Tab 2: Login biométrico
        self.create_biometric_tab()
        
        # Tab 3: Registro
        self.create_register_tab()
        
        # Frame de estado
        self.status_frame = ttk.Frame(main_frame)
        self.status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_label = ttk.Label(
            self.status_frame, 
            text="Selecciona un método de autenticación",
            font=('Arial', 10),
            foreground='#7f8c8d'
        )
        self.status_label.pack()
        
    def setup_styles(self):
        """Configurar estilos personalizados"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configurar colores
        style.configure('Custom.TLabel', font=('Arial', 11))
        style.configure('Title.TLabel', font=('Arial', 14, 'bold'))
        style.configure('Success.TLabel', foreground='#27ae60')
        style.configure('Error.TLabel', foreground='#e74c3c')
        style.configure('Accent.TButton', font=('Arial', 11, 'bold'))
    
    def create_password_tab(self):
        """Crear tab de autenticación por contraseña"""
        password_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(password_frame, text="📧 Email y Contraseña")
        
        # Título
        ttk.Label(
            password_frame, 
            text="Iniciar Sesión",
            style='Title.TLabel'
        ).pack(pady=(0, 20))
        
        # Formulario
        form_frame = ttk.Frame(password_frame)
        form_frame.pack(fill=tk.X, padx=50)
        
        # Email
        ttk.Label(form_frame, text="Email:", style='Custom.TLabel').pack(anchor=tk.W, pady=(0, 5))
        self.email_entry = ttk.Entry(form_frame, font=('Arial', 12), width=40)
        self.email_entry.pack(fill=tk.X, pady=(0, 15))
        
        # Contraseña
        ttk.Label(form_frame, text="Contraseña:", style='Custom.TLabel').pack(anchor=tk.W, pady=(0, 5))
        self.password_entry = ttk.Entry(form_frame, font=('Arial', 12), width=40, show='*')
        self.password_entry.pack(fill=tk.X, pady=(0, 20))
        
        # Botón de login
        login_btn = ttk.Button(
            form_frame,
            text="🔓 Iniciar Sesión",
            command=self.handle_password_login,
            width=20
        )
        login_btn.pack(pady=10)
        
        # Bind Enter key
        self.password_entry.bind('<Return>', lambda e: self.handle_password_login())
    
    def create_biometric_tab(self):
        """Crear tab de autenticación biométrica mejorada"""
        biometric_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(biometric_frame, text="👤 Reconocimiento Facial")
        
        # Título
        ttk.Label(
            biometric_frame, 
            text="Autenticación Biométrica",
            font=('Arial', 16, 'bold')
        ).pack(pady=(0, 10))
        
        # Instrucciones
        self.biometric_instructions = ttk.Label(
            biometric_frame,
            text="Activa la cámara y verifica tu identidad mediante reconocimiento facial",
            font=('Arial', 11),
            foreground='#7f8c8d'
        )
        self.biometric_instructions.pack(pady=(0, 10))
        
        # Frame de cámara con tamaño fijo para evitar salto de botones
        camera_container = ttk.Frame(biometric_frame)
        camera_container.pack(pady=5)  # Reducir espacio vertical
        
        self.camera_frame = ttk.Frame(camera_container, relief=tk.RAISED, borderwidth=2)
        self.camera_frame.pack()
        
        # Label para mostrar video con tamaño fijo
        self.camera_label = ttk.Label(
            self.camera_frame, 
            text="📹 Cámara desactivada\n\nPresiona 'Activar Cámara' para comenzar",
            font=('Arial', 10),  # Reducir tamaño de fuente
            width=45,  # Reducir ancho
            anchor='center',
            background='#f8f9fa'
        )
        self.camera_label.pack(padx=5, pady=5)  # Reducir padding
        
        # Estado de detección facial
        self.face_status_label = ttk.Label(
            biometric_frame,
            text="⚪ Esperando activación de cámara...",
            font=('Arial', 11, 'bold'),
            foreground='#7f8c8d'
        )
        self.face_status_label.pack(pady=5)
        
        # Separador visual
        separator = ttk.Separator(biometric_frame, orient='horizontal')
        separator.pack(fill='x', pady=10)
        
        # Frame de controles con layout mejorado
        control_frame = ttk.Frame(biometric_frame)
        control_frame.pack(pady=5)
        
        # Botones en fila superior
        top_buttons = ttk.Frame(control_frame)
        top_buttons.pack(pady=5)
        
        self.start_camera_btn = ttk.Button(
            top_buttons,
            text="📹 Activar Cámara",
            command=self.start_camera,
            width=18
        )
        self.start_camera_btn.pack(side=tk.LEFT, padx=5)
        print("🔧 DEBUG: Botón 'Activar Cámara' creado")
        
        self.stop_camera_btn = ttk.Button(
            top_buttons,
            text="⏹ Detener Cámara",
            command=self.stop_camera,
            state=tk.DISABLED,
            width=18
        )
        self.stop_camera_btn.pack(side=tk.LEFT, padx=5)
        print("🔧 DEBUG: Botón 'Detener Cámara' creado")
        
        # Botón principal en fila inferior
        bottom_buttons = ttk.Frame(control_frame)
        bottom_buttons.pack(pady=5)  # Reducir espacio
        
        self.biometric_login_btn = ttk.Button(
            bottom_buttons,
            text="🔍 Verificar Identidad",
            command=self.handle_biometric_login,
            state=tk.DISABLED,
            width=25
        )
        self.biometric_login_btn.pack()
        print("🔧 DEBUG: Botón 'Verificar Identidad' creado")
        
        # Mensaje de estado del proceso
        self.biometric_status_label = ttk.Label(
            biometric_frame,
            text="",
            font=('Arial', 10),
            foreground='#3498db'
        )
        self.biometric_status_label.pack(pady=5)  # Reducir espacio
        
        # Nota informativa sobre cancelación
        help_label = ttk.Label(
            biometric_frame,
            text="💡 Tip: Puedes detener la cámara en cualquier momento usando el botón 'Detener Cámara'",
            font=('Arial', 9),
            foreground='#95a5a6'
        )
        help_label.pack(pady=2)  # Reducir espacio
        
        # Variables para detección facial
        self.detecting_face = False
        self.face_detected = False
    
    def create_register_tab(self):
        """Crear tab de registro"""
        register_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(register_frame, text="👤 Registro")
        
        # Título
        ttk.Label(
            register_frame, 
            text="Crear Nueva Cuenta",
            style='Title.TLabel'
        ).pack(pady=(0, 20))
        
        # Contenedor principal centrado
        main_container = ttk.Frame(register_frame)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Frame del formulario centrado tanto horizontal como verticalmente
        form_frame = ttk.Frame(main_container)
        form_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Campos del formulario
        fields = [
            ("Nombre:", "first_name"),
            ("Apellido:", "last_name"),
            ("Nombre de usuario:", "username"),
            ("Email:", "email"),
            ("Contraseña:", "password"),
            ("Confirmar contraseña:", "confirm_password")
        ]
        
        self.register_entries = {}
        
        for label_text, field_name in fields:
            # Contenedor para cada campo
            field_frame = ttk.Frame(form_frame)
            field_frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(field_frame, text=label_text, style='Custom.TLabel').pack(anchor=tk.W)
            
            entry = ttk.Entry(field_frame, font=('Arial', 11), width=50)
            if 'password' in field_name:
                entry.configure(show='*')
                
            entry.pack(fill=tk.X, pady=(2, 0))
            self.register_entries[field_name] = entry
        
        # Botón de registro centrado
        button_frame = ttk.Frame(form_frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        register_btn = ttk.Button(
            button_frame,
            text="✅ Crear Cuenta",
            command=self.handle_register,
            width=25,
            style='Accent.TButton'
        )
        register_btn.pack(pady=10)  # Centrar el botón con padding
    
    def handle_password_login(self):
        """Manejar login por contraseña"""
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        
        if not email or not password:
            self.show_status("Por favor completa todos los campos", "error")
            return
        
        self.show_status("Verificando credenciales...", "info")
        
        # Autenticar en hilo separado
        threading.Thread(target=self._authenticate_password, args=(email, password)).start()
    
    def _authenticate_password(self, email: str, password: str):
        """Autenticar contraseña en hilo separado"""
        result = self.auth_system.authenticate_password(email, password)
        
        # Actualizar UI en hilo principal
        self.root.after(0, self._handle_auth_result, result)
    
    def handle_register(self):
        """Manejar registro de usuario"""
        # Recopilar datos
        user_data = {}
        for field, entry in self.register_entries.items():
            user_data[field] = entry.get().strip()
        
        # Validaciones
        if not all([user_data.get('first_name'), user_data.get('username'), 
                   user_data.get('email'), user_data.get('password')]):
            self.show_status("Por favor completa los campos obligatorios", "error")
            return
        
        if user_data['password'] != user_data['confirm_password']:
            self.show_status("Las contraseñas no coinciden", "error")
            return
        
        if len(user_data['password']) < 6:
            self.show_status("La contraseña debe tener al menos 6 caracteres", "error")
            return
        
        # Preparar datos para registro
        register_data = {
            'email': user_data['email'],
            'username': user_data['username'],
            'password': user_data['password'],
            'first_name': user_data['first_name'],
            'last_name': user_data.get('last_name'),
            'phone': None  # Campo removido de la interfaz
        }
        
        self.show_status("Creando cuenta...", "info")
        
        # Registrar en hilo separado
        threading.Thread(target=self._register_user, args=(register_data,)).start()
    
    def _register_user(self, user_data: dict):
        """Registrar usuario en hilo separado"""
        result = self.auth_system.register_user(user_data)
        
        # Actualizar UI en hilo principal
        self.root.after(0, self._handle_register_result, result)
    
    def _handle_register_result(self, result: dict):
        """Manejar resultado del registro"""
        if result['success']:
            self.show_status("✅ Cuenta creada exitosamente", "success")
            
            # Limpiar formulario
            for entry in self.register_entries.values():
                entry.delete(0, tk.END)
            
            # Cambiar a tab de login
            self.notebook.select(0)
            
            messagebox.showinfo(
                "Registro Exitoso",
                "Tu cuenta ha sido creada exitosamente.\n\n"
                "Ahora puedes iniciar sesión y luego registrar tu rostro "
                "para habilitar la autenticación biométrica."
            )
        else:
            self.show_status(f"❌ Error: {result['error']}", "error")
    
    def start_camera(self):
        """Iniciar cámara para login biométrico"""
        try:
            self.auth_system.camera = cv2.VideoCapture(0)
            if not self.auth_system.camera.isOpened():
                self.face_status_label.configure(text="❌ Error: No se pudo acceder a la cámara", foreground='#e74c3c')
                self.biometric_status_label.configure(text="Verifica que tu cámara esté conectada y no esté siendo usada por otra aplicación")
                return
            
            self.auth_system.camera_active = True
            self.update_camera_controls(True)
            self.update_camera_feed()
            
            self.face_status_label.configure(text="📹 Cámara activada - Posiciónate frente a la cámara", foreground='#27ae60')
            self.biometric_status_label.configure(text="Cámara lista. Presiona 'Verificar Identidad' cuando detectes tu rostro.")
            self.biometric_instructions.configure(
                text="✅ Cámara activada. Asegúrate de estar bien iluminado y centrado.",
                foreground='#27ae60'
            )
            
        except Exception as e:
            self.face_status_label.configure(text=f"❌ Error iniciando cámara: {e}", foreground='#e74c3c')
            self.biometric_status_label.configure(text="Hubo un problema al acceder a la cámara")
    
    def stop_camera(self):
        """Detener cámara y resetear estado"""
        self.auth_system.camera_active = False
        self.detecting_face = False
        self.face_detected = False
        
        if self.auth_system.camera:
            self.auth_system.camera.release()
        
        self.camera_label.configure(
            image='', 
            text="📹 Cámara desactivada\n\nPresiona 'Activar Cámara' para comenzar",
            background='#f8f9fa'
        )
        self.face_status_label.configure(text="⚪ Esperando activación de cámara...", foreground='#7f8c8d')
        self.biometric_status_label.configure(text="")
        self.biometric_instructions.configure(
            text="Activa la cámara y verifica tu identidad mediante reconocimiento facial",
            foreground='#7f8c8d'
        )
        
        # Cancelar cualquier verificación en curso
        self.biometric_login_btn.configure(text="🔍 Verificar Identidad")
        
        self.update_camera_controls(False)
    
    def update_camera_controls(self, camera_active: bool):
        """Actualizar estado de controles de cámara"""
        if camera_active:
            self.start_camera_btn.configure(state=tk.DISABLED)
            # El botón de verificar se habilitará cuando se detecte rostro
            self.biometric_login_btn.configure(state=tk.DISABLED)
            self.stop_camera_btn.configure(state=tk.NORMAL)
        else:
            self.start_camera_btn.configure(state=tk.NORMAL)
            self.biometric_login_btn.configure(state=tk.DISABLED)
            self.stop_camera_btn.configure(state=tk.DISABLED)
    
    def update_camera_feed(self):
        """Actualizar feed de la cámara con detección facial en tiempo real"""
        # Verificar que la ventana y componentes existan
        if not hasattr(self, 'root') or not self.root.winfo_exists():
            return
        
        if not hasattr(self, 'camera_label') or not self.camera_label.winfo_exists():
            return
            
        if not self.auth_system.camera_active or not self.auth_system.camera:
            return
        
        ret, frame = self.auth_system.camera.read()
        if ret:
            # Redimensionar frame
            frame = cv2.resize(frame, (400, 300))
            display_frame = frame.copy()
            
            # Detectar rostros en tiempo real
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            try:
                faces = self.auth_system.face_encoder.face_cascade.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30), maxSize=(300, 300)
                )
            except cv2.error as e:
                print(f"⚠️ DEBUG: Error en detección facial: {e}")
                faces = []
            
            # Dibujar bounding boxes y actualizar estado
            if len(faces) > 0:
                self.face_detected = True
                # Habilitar botón de verificar solo si no estamos verificando
                if not self.detecting_face:
                    self.biometric_login_btn.configure(state=tk.NORMAL)
                    
                for (x, y, w, h) in faces:
                    # Color del cuadro según el estado
                    if self.detecting_face:
                        color = (255, 165, 0)  # Naranja durante verificación
                        thickness = 3
                        self.face_status_label.configure(
                            text="🔍 Verificando rostro...",
                            foreground='#f39c12'
                        )
                    else:
                        color = (0, 255, 0)  # Verde cuando detecta rostro
                        thickness = 2
                        self.face_status_label.configure(
                            text="✅ Rostro detectado",
                            foreground='#27ae60'
                        )
                    
                    # Dibujar rectángulo alrededor del rostro
                    cv2.rectangle(display_frame, (x, y), (x+w, y+h), color, thickness)
                    
                    # Añadir texto encima del cuadro
                    cv2.putText(display_frame, "Rostro", (x, y-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            else:
                self.face_detected = False
                # Deshabilitar botón de verificar cuando no hay rostro
                if not self.detecting_face:
                    self.biometric_login_btn.configure(state=tk.DISABLED)
                    self.face_status_label.configure(
                        text="👤 Posiciónate frente a la cámara",
                        foreground='#7f8c8d'
                    )
            
            # Convertir a RGB para mostrar
            frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            
            # Convertir a ImageTk
            image = Image.fromarray(frame_rgb)
            photo = ImageTk.PhotoImage(image)
            
            self.camera_label.configure(image=photo, text='')
            self.camera_label.image = photo
        
        # Programar siguiente actualización
        if self.auth_system.camera_active and hasattr(self, 'root') and self.root.winfo_exists():
            try:
                self.root.after(30, self.update_camera_feed)
            except tk.TclError:
                # La ventana fue cerrada, detener la actualización
                pass
    
    def handle_biometric_login(self):
        """Manejar login biométrico con retroalimentación visual mejorada"""
        if not self.auth_system.camera_active or not self.auth_system.camera:
            self.face_status_label.configure(text="❌ Primero activa la cámara", foreground='#e74c3c')
            self.biometric_status_label.configure(text="Debes activar la cámara antes de verificar tu identidad")
            return
        
        if not self.face_detected:
            self.face_status_label.configure(text="❌ No se detecta rostro válido", foreground='#e74c3c')
            self.biometric_status_label.configure(text="Posiciónate frente a la cámara y asegúrate de que tu rostro esté visible")
            return
        
        # Iniciar proceso de verificación
        self.detecting_face = True
        self.biometric_login_btn.configure(state=tk.DISABLED, text="🔍 Verificando...")
        self.start_camera_btn.configure(state=tk.DISABLED)
        # Mantener stop_camera_btn activo para permitir cancelar la verificación
        
        self.face_status_label.configure(text="🔍 Analizando rostro...", foreground='#f39c12')
        self.biometric_status_label.configure(text="Mantente quieto mientras se analiza tu rostro")
        self.biometric_instructions.configure(
            text="🔍 Verificando identidad... No te muevas",
            foreground='#f39c12'
        )
        
        # Capturar y procesar en hilo separado
        threading.Thread(target=self._capture_and_authenticate, daemon=True).start()
    
    def _capture_and_authenticate(self):
        """Capturar rostro y autenticar"""
        try:
            ret, frame = self.auth_system.camera.read()
            if not ret:
                self.root.after(0, self._reset_biometric_ui, "❌ Error capturando imagen", False)
                return
            
            # Procesar rostro
            encoding = self.auth_system.face_encoder.encode_face_from_image(frame)
            
            if encoding is None:
                self.root.after(0, self._reset_biometric_ui, "❌ No se detectó rostro válido", False)
                return
            
            # Autenticar
            result = self.auth_system.authenticate_biometric(encoding)
            
            # Actualizar UI en hilo principal
            self.root.after(0, self._handle_auth_result, result)
            
        except Exception as e:
            self.root.after(0, self._reset_biometric_ui, f"❌ Error: {e}", False)
    
    def _reset_biometric_ui(self, message, success=False):
        """Resetear la UI biométrica después de verificación"""
        self.detecting_face = False
        
        # Restaurar botones según el estado de la cámara
        if self.auth_system.camera_active:
            self.biometric_login_btn.configure(
                state=tk.NORMAL if self.face_detected else tk.DISABLED, 
                text="🔍 Verificar Identidad"
            )
            self.start_camera_btn.configure(state=tk.DISABLED)
            self.stop_camera_btn.configure(state=tk.NORMAL)
        else:
            # Si la cámara se detuvo durante la verificación
            self.biometric_login_btn.configure(state=tk.DISABLED, text="🔍 Verificar Identidad")
            self.start_camera_btn.configure(state=tk.NORMAL)
            self.stop_camera_btn.configure(state=tk.DISABLED)
        
        # Actualizar mensajes
        color = '#27ae60' if success else '#e74c3c'
        self.face_status_label.configure(text=message, foreground=color)
        
        if not success:
            self.biometric_status_label.configure(text="Intenta de nuevo o verifica tu registro biométrico")
            self.biometric_instructions.configure(
                text="Verifica que estés bien iluminado y centrado en la cámara",
                foreground='#7f8c8d'
            )
    
    def _handle_auth_result(self, result: dict):
        """Manejar resultado de autenticación con retroalimentación visual mejorada"""
        # Reiniciar estado de detección
        self.detecting_face = False
        
        # Restaurar controles según el estado de la cámara
        if self.auth_system.camera_active:
            self.biometric_login_btn.configure(
                state=tk.NORMAL if self.face_detected else tk.DISABLED,
                text="🔍 Verificar Identidad"
            )
            self.start_camera_btn.configure(state=tk.DISABLED)
            self.stop_camera_btn.configure(state=tk.NORMAL)
        
        if result['success']:
            user = result['user']
            confidence = result.get('confidence', 1.0)
            
            # Determinar nombre a mostrar
            display_name = user.get('first_name', '').strip()
            if not display_name:
                display_name = user.get('username', 'Usuario')
            
            # Mostrar éxito con información del usuario
            self.biometric_instructions.configure(
                text=f"✅ ¡Bienvenido/a {display_name}!",
                foreground='#27ae60'
            )
            self.face_status_label.configure(
                text="🎉 Acceso concedido",
                foreground='#27ae60'
            )
            self.show_status(f"✅ Autenticación exitosa - {user.get('username', 'Usuario')}", "success")
            
            # Cerrar cámara después de un breve retraso para mostrar el mensaje
            self.root.after(2000, self._successful_login_cleanup, user)
            
        else:
            # Mostrar error visual
            self.biometric_instructions.configure(
                text="❌ Usuario no reconocido o rostro no registrado",
                foreground='#e74c3c'
            )
            self.face_status_label.configure(
                text="🚫 Biometría no registrada",
                foreground='#e74c3c'
            )
            self.show_status(f"❌ Acceso denegado: {result['error']}", "error")
            
            # Restaurar instrucciones después de unos segundos
            self.root.after(3000, self._reset_biometric_interface)
    
    def _successful_login_cleanup(self, user: dict):
        """Limpiar interfaz después de login exitoso"""
        if self.auth_system.camera_active:
            self.stop_camera()
        self.auth_system.start_main_application(user)
    
    def _reset_biometric_interface(self):
        """Resetear interfaz biométrica a estado inicial"""
        self.biometric_instructions.configure(
            text="Posiciónate frente a la cámara para verificar tu identidad",
            foreground='#7f8c8d'
        )
        self.face_status_label.configure(text="", foreground='#7f8c8d')
    
    def show_status(self, message: str, status_type: str = "info"):
        """Mostrar mensaje de estado"""
        colors = {
            "info": "#3498db",
            "success": "#27ae60", 
            "error": "#e74c3c"
        }
        
        self.status_label.configure(
            text=message,
            foreground=colors.get(status_type, "#7f8c8d")
        )

class MainApplication:
    """Aplicación principal después del login"""
    
    def __init__(self, auth_system: DualAuthSystem, user: dict):
        self.auth_system = auth_system
        self.user = user
        self.setup_ui()
    
    def setup_ui(self):
        """Configurar interfaz principal"""
        self.root = tk.Tk()
        self.root.title(f"Sistema Principal - {self.user['username']}")
        self.root.geometry("900x700")
        self.root.configure(bg='#ecf0f1')
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(
            header_frame,
            text=f"🎉 Bienvenido, {self.user['username']}!",
            font=('Arial', 20, 'bold'),
            foreground='#2c3e50'
        ).pack(side=tk.LEFT)
        
        # Botón de logout
        ttk.Button(
            header_frame,
            text="🚪 Cerrar Sesión",
            command=self.logout
        ).pack(side=tk.RIGHT)
        
        # Notebook para funciones
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab de perfil
        self.create_profile_tab(notebook)
        
        # Tab de configuración biométrica
        self.create_biometric_setup_tab(notebook)
        
        # Tab de historial
        self.create_history_tab(notebook)
    
    def create_profile_tab(self, notebook):
        """Crear tab de perfil de usuario"""
        profile_frame = ttk.Frame(notebook, padding="20")
        notebook.add(profile_frame, text="👤 Perfil")
        
        ttk.Label(
            profile_frame,
            text="Información del Usuario",
            font=('Arial', 16, 'bold')
        ).pack(pady=(0, 20))
        
        # Información del usuario
        info_frame = ttk.LabelFrame(profile_frame, text="Datos Personales", padding="15")
        info_frame.pack(fill=tk.X, pady=10)
        
        # Construir información del usuario de forma dinámica
        user_info = []
        
        # Agregar nombre completo si está disponible
        first_name = self.user.get('first_name', '').strip()
        last_name = self.user.get('last_name', '').strip()
        if first_name or last_name:
            full_name = f"{first_name} {last_name}".strip()
            user_info.append(("Nombre completo:", full_name))
        
        user_info.extend([
            ("Email:", self.user.get('email', 'No disponible')),
            ("Nombre de usuario:", self.user.get('username', 'No disponible')),
            ("Biometría registrada:", "✅ Sí" if self.user.get('face_registered') else "❌ No")
        ])
        
        for label, value in user_info:
            row_frame = ttk.Frame(info_frame)
            row_frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(row_frame, text=label, font=('Arial', 11, 'bold')).pack(side=tk.LEFT)
            ttk.Label(row_frame, text=value, font=('Arial', 11)).pack(side=tk.LEFT, padx=(10, 0))
    
    def create_biometric_setup_tab(self, notebook):
        """Crear tab de configuración biométrica"""
        bio_frame = ttk.Frame(notebook, padding="20")
        notebook.add(bio_frame, text="🔐 Configuración Biométrica")
        
        ttk.Label(
            bio_frame,
            text="Gestión de Autenticación Facial",
            font=('Arial', 16, 'bold')
        ).pack(pady=(0, 20))
        
        if self.user.get('face_registered'):
            # Usuario ya tiene biometría
            ttk.Label(
                bio_frame,
                text="✅ Ya tienes configurada la autenticación facial",
                font=('Arial', 12),
                foreground='#27ae60'
            ).pack(pady=10)
            
            ttk.Button(
                bio_frame,
                text="🔄 Actualizar Datos Biométricos",
                command=self.setup_new_biometric
            ).pack(pady=10)
        else:
            # Usuario sin biometría
            ttk.Label(
                bio_frame,
                text="⚠️ Aún no tienes configurada la autenticación facial",
                font=('Arial', 12),
                foreground='#f39c12'
            ).pack(pady=10)
            
            ttk.Label(
                bio_frame,
                text="Registra tu rostro para habilitar el login biométrico en futuras sesiones:",
                font=('Arial', 11)
            ).pack(pady=10)
            
            ttk.Button(
                bio_frame,
                text="📷 Registrar Mi Rostro",
                command=self.setup_new_biometric
            ).pack(pady=20)
    
    def create_history_tab(self, notebook):
        """Crear tab de historial"""
        history_frame = ttk.Frame(notebook, padding="20")
        notebook.add(history_frame, text="📊 Historial")

        ttk.Label(
            history_frame,
            text="Historial de Sesiones",
            font=('Arial', 16, 'bold')
        ).pack(pady=(0, 20))

        # Obtener historial del usuario
        logs = self.auth_system.db.get_auth_logs(user_id=self.user['id'], limit=50)

        columns = ("timestamp", "auth_method", "status", "failure_reason", "ip_address")
        tree = ttk.Treeview(history_frame, columns=columns, show="headings", height=15)
        tree.heading("timestamp", text="Fecha/Hora")
        tree.heading("auth_method", text="Método")
        tree.heading("status", text="Estado")
        tree.heading("failure_reason", text="Motivo (si falla)")
        tree.heading("ip_address", text="IP")

        for log in logs:
            tree.insert("", "end", values=(
                log.get("timestamp", ""),
                log.get("auth_method", ""),
                log.get("status", ""),
                log.get("failure_reason", ""),
                log.get("ip_address", "")
            ))
        tree.pack(fill=tk.BOTH, expand=True)

        if not logs:
            ttk.Label(
                history_frame,
                text="No hay historial de autenticaciones para este usuario.",
                font=('Arial', 11),
                foreground='#7f8c8d'
            ).pack(pady=10)
    
    def setup_new_biometric(self):
        """Configurar nueva biometría"""
        BiometricSetupWindow(self.auth_system, self.user['id'])
    
    def refresh_biometric_status(self):
        """Actualizar la interfaz tras registro biométrico exitoso"""
        try:
            # Marcar que el usuario ahora tiene biometría
            self.user['face_registered'] = True
            
            # Recrear las pestañas para mostrar el estado actualizado
            # Obtener el notebook
            for widget in self.root.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Notebook):
                            # Encontrar y actualizar la pestaña biométrica
                            for tab_id in child.tabs():
                                tab_text = child.tab(tab_id, "text")
                                if "Configuración Biométrica" in tab_text:
                                    # Obtener el frame de la pestaña biométrica
                                    bio_frame = child.nametowidget(tab_id)
                                    
                                    # Limpiar contenido actual
                                    for widget in bio_frame.winfo_children():
                                        widget.destroy()
                                    
                                    # Recrear contenido con estado actualizado
                                    self._recreate_biometric_tab_content(bio_frame)
                                    
                                    print("✅ DEBUG: Pestaña biométrica actualizada automáticamente")
                                    break
                            break
                    break
                    
        except Exception as e:
            print(f"❌ DEBUG: Error actualizando interfaz biométrica: {e}")
    
    def _recreate_biometric_tab_content(self, bio_frame):
        """Recrear contenido de la pestaña biométrica con estado actualizado"""
        ttk.Label(
            bio_frame,
            text="Gestión de Autenticación Facial",
            font=('Arial', 16, 'bold')
        ).pack(pady=(0, 20))
        
        # Mostrar estado actualizado (ahora con biometría)
        ttk.Label(
            bio_frame,
            text="✅ Ya tienes configurada la autenticación facial",
            font=('Arial', 12),
            foreground='#27ae60'
        ).pack(pady=10)
        
        ttk.Label(
            bio_frame,
            text="🎉 Tu biometría se ha registrado correctamente",
            font=('Arial', 11),
            foreground='#2ecc71'
        ).pack(pady=5)
        
        ttk.Label(
            bio_frame,
            text="Ahora puedes cerrar sesión y usar reconocimiento facial para iniciar sesión",
            font=('Arial', 10),
            foreground='#7f8c8d'
        ).pack(pady=10)
        
        ttk.Button(
            bio_frame,
            text="🔄 Actualizar Datos Biométricos",
            command=self.setup_new_biometric
        ).pack(pady=20)
    
    def logout(self):
        """Cerrar sesión"""
        self.root.destroy()
        # Reiniciar sistema de login
        self.auth_system.start_login_interface()

class BiometricSetupWindow:
    """Ventana mejorada para configurar biometría con retroalimentación visual"""
    
    def __init__(self, auth_system: DualAuthSystem, user_id: str):
        self.auth_system = auth_system
        self.user_id = user_id
        self.camera = None
        self.camera_active = False
        self.registering = False
        self.face_detected = False
        # Número de muestras requeridas para registro biométrico
        self.required_samples = 5  # Puedes ajustar este valor según lo necesario
        self.samples_captured = 0
        self.setup_ui()
        
    def cleanup(self):
        """Limpiar recursos antes de cerrar"""
        try:
            if self.camera_active and self.camera:
                self.stop_camera()
        except:
            pass
    
    def on_closing(self):
        """Manejar cierre de ventana"""
        self.cleanup()
        if hasattr(self, 'root'):
            self.root.quit()
            self.root.destroy()
    
    def setup_ui(self):
        """Configurar interfaz de usuario"""
        self.root = tk.Toplevel()
        self.root.title("Configuración Biométrica")
        self.root.geometry("800x700")
        self.root.configure(bg='#ecf0f1')
        
        # Configurar protocolo de cierre
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Frame principal con scroll
        canvas = tk.Canvas(self.root, bg='#ecf0f1')
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Frame principal
        main_frame = ttk.Frame(scrollable_frame, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        ttk.Label(
            main_frame,
            text="📷 Registro de Datos Biométricos",
            font=('Arial', 18, 'bold'),
            foreground='#2c3e50'
        ).pack(pady=(0, 20))
        
        # Instrucciones dinámicas (más compactas)
        self.instructions_label = ttk.Label(
            main_frame,
            text="Para registrar tu rostro:\n"
                 "1. Activa la cámara  2. Mantén tu rostro en el cuadro verde\n"
                 "3. El sistema capturará automáticamente",
            font=('Arial', 10),
            foreground='#7f8c8d',
            justify=tk.CENTER
        )
        self.instructions_label.pack(pady=(0, 15))
        
        # Frame de cámara más compacto
        self.camera_frame = ttk.Frame(main_frame, relief=tk.RAISED, borderwidth=2)
        self.camera_frame.pack(pady=10)
        
        self.camera_label = ttk.Label(
            self.camera_frame, 
            text="🎥 Cámara desactivada\n\nPresiona 'Activar Cámara' para comenzar",
            font=('Arial', 11),
            foreground='#7f8c8d'
        )
        self.camera_label.pack(padx=15, pady=15)
        
        # Estado de detección facial
        self.face_status_label = ttk.Label(
            main_frame,
            text="",
            font=('Arial', 11, 'bold')
        )
        self.face_status_label.pack(pady=5)
        
        # Barra de progreso para muestras (más compacta)
        self.progress_frame = ttk.Frame(main_frame)
        self.progress_frame.pack(pady=5)
        
        ttk.Label(self.progress_frame, text="Progreso:", font=('Arial', 9)).pack()
        self.progress_bar = ttk.Progressbar(
            self.progress_frame, 
            length=250,  # Más pequeña
            maximum=self.required_samples,
            mode='determinate'
        )
        self.progress_bar.pack(pady=3)
        
        self.progress_label = ttk.Label(
            self.progress_frame,
            text=f"0 / {self.required_samples} muestras capturadas",
            font=('Arial', 9),
            foreground='#7f8c8d'
        )
        self.progress_label.pack()
        
        # Controles mejorados
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(pady=15)
        
        self.start_btn = ttk.Button(
            control_frame,
            text="📹 Activar Cámara",
            command=self.start_camera,
            width=18,
            style='Accent.TButton'
        )
        self.start_btn.pack(side=tk.LEFT, padx=3)
        
        self.start_registration_btn = ttk.Button(
            control_frame,
            text="� Iniciar Registro",
            command=self.start_registration,
            state=tk.DISABLED,
            width=20,
            style='Accent.TButton'
        )
        self.start_registration_btn.pack(side=tk.LEFT, padx=3)
        
        self.cancel_btn = ttk.Button(
            control_frame,
            text="❌ Cancelar",
            command=self.close_window,
            width=15
        )
        self.cancel_btn.pack(side=tk.LEFT, padx=3)
        
        # Estado general
        self.status_label = ttk.Label(
            main_frame,
            text="Presiona 'Activar Cámara' para comenzar el registro",
            font=('Arial', 11),
            foreground='#3498db'
        )
        self.status_label.pack(pady=15)
    
    def start_camera(self):
        """Iniciar cámara con mejor manejo de errores"""
        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                self.show_status("❌ Error: No se pudo acceder a la cámara", "error")
                return
            
            self.camera_active = True
            self.start_btn.configure(state=tk.DISABLED)
            self.start_registration_btn.configure(state=tk.NORMAL)
            self.update_camera_feed()
            self.show_status("📹 Cámara activada correctamente", "success")
            self.instructions_label.configure(
                text="✅ Cámara activada\nPosiciónate frente a la cámara y presiona 'Iniciar Registro'",
                foreground='#27ae60'
            )
            
        except Exception as e:
            self.show_status(f"❌ Error iniciando cámara: {e}", "error")
    
    def update_camera_feed(self):
        """Actualizar feed con detección facial en tiempo real"""
        # Verificar que la ventana y componentes existan
        if not hasattr(self, 'root') or not self.root.winfo_exists():
            return
            
        if not hasattr(self, 'camera_label') or not self.camera_label.winfo_exists():
            return
            
        if not self.camera_active or not self.camera:
            return
        
        ret, frame = self.camera.read()
        if ret:
            frame = cv2.resize(frame, (400, 280))  # Tamaño más compacto
            display_frame = frame.copy()
            
            # Detectar rostros con parámetros más permisivos
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            try:
                faces = self.auth_system.face_encoder.face_cascade.detectMultiScale(
                    gray, 
                    scaleFactor=1.1,   # Valor más seguro
                    minNeighbors=3,    # Menos restrictivo
                    minSize=(40, 40),  # Tamaño mínimo reducido
                    maxSize=(300, 300) # Tamaño máximo para evitar errores
                )
            except cv2.error as e:
                print(f"⚠️ DEBUG: Error en detección de registro: {e}")
                faces = []
            
            # Dibujar bounding boxes
            if len(faces) > 0:
                self.face_detected = True
                for (x, y, w, h) in faces:
                    if self.registering:
                        color = (255, 165, 0)  # Naranja durante registro
                        text = "Registrando..."
                        thickness = 3
                    else:
                        color = (0, 255, 0)  # Verde cuando detecta rostro
                        text = "Rostro detectado"
                        thickness = 2
                    
                    cv2.rectangle(display_frame, (x, y), (x+w, y+h), color, thickness)
                    cv2.putText(display_frame, text, (x, y-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                
                if not self.registering:
                    self.face_status_label.configure(
                        text="✅ Rostro detectado - Listo para registrar",
                        foreground='#27ae60'
                    )
            else:
                self.face_detected = False
                if not self.registering:
                    self.face_status_label.configure(
                        text="👤 Posiciónate frente a la cámara",
                        foreground='#f39c12'
                    )
            
            # Convertir y mostrar
            frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(frame_rgb)
            photo = ImageTk.PhotoImage(image)
            
            self.camera_label.configure(image=photo, text='')
            self.camera_label.image = photo
        
        if self.camera_active and hasattr(self, 'root') and self.root.winfo_exists():
            try:
                self.root.after(30, self.update_camera_feed)
            except tk.TclError:
                # La ventana fue cerrada, detener la actualización
                pass
    
    def start_registration(self):
        """Iniciar proceso de registro automático"""
        print(f"🔍 DEBUG: Intentando iniciar registro - camera_active: {self.camera_active}, face_detected: {self.face_detected}")
        
        if not self.camera_active:
            self.show_status("❌ Primero activa la cámara", "error")
            return
        
        # Verificar detección facial en tiempo real antes de proceder
        current_faces_detected = False
        if self.camera and self.camera.isOpened():
            ret, frame = self.camera.read()
            if ret:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                try:
                    faces = self.auth_system.face_encoder.face_cascade.detectMultiScale(
                        gray, 
                        scaleFactor=1.1,   # Valor más seguro
                        minNeighbors=3,    # Menos restrictivo
                        minSize=(40, 40),  # Tamaño mínimo más pequeño
                        maxSize=(300, 300) # Tamaño máximo para evitar errores
                    )
                except cv2.error as e:
                    print(f"⚠️ DEBUG: Error en verificación de rostro: {e}")
                    faces = []
                current_faces_detected = len(faces) > 0
                print(f"🔍 DEBUG: Detección actual - rostros encontrados: {len(faces)}")
        
        if not current_faces_detected:
            self.show_status("❌ No se detecta rostro claro. Mejora la iluminación y centra tu rostro", "error")
            return
        
        print("✅ DEBUG: Rostro detectado correctamente, iniciando registro...")
        
        self.registering = True
        self.samples_captured = 0
        self.start_registration_btn.configure(state=tk.DISABLED)
        self.cancel_btn.configure(text="⏹ Detener", command=self.stop_registration)
        
        self.show_status("🔄 Registrando rostro... Mantente quieto", "info")
        self.instructions_label.configure(
            text="� Capturando muestras de tu rostro...\nMantente quieto y mira a la cámara",
            foreground='#f39c12'
        )
        
        # Iniciar captura automática
        self.capture_sample()
    
    def capture_sample(self):
        """Capturar una muestra del rostro - Versión mejorada"""
        if not self.registering or not self.camera_active:
            return
        
        try:
            ret, frame = self.camera.read()
            if not ret:
                self.show_status("❌ Error capturando imagen", "error")
                self.root.after(500, self.capture_sample)  # Reintentar
                return
            
            # Procesar rostro con mensaje de depuración
            print(f"🔍 DEBUG: Intentando procesar rostro para muestra {self.samples_captured + 1}")
            
            # Verificar calidad de la imagen antes de procesar
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Verificar iluminación
            brightness = np.mean(gray)
            if brightness < 50:
                self.face_status_label.configure(
                    text="💡 Imagen muy oscura - Mejora la iluminación",
                    foreground='#f39c12'
                )
                self.root.after(1000, self.capture_sample)
                return
            elif brightness > 200:
                self.face_status_label.configure(
                    text="☀️ Imagen muy brillante - Reduce la iluminación",
                    foreground='#f39c12'
                )
                self.root.after(1000, self.capture_sample)
                return
            
            # Verificar si hay movimiento (comparar con frame anterior si existe)
            if hasattr(self, 'previous_frame'):
                diff = cv2.absdiff(gray, self.previous_frame)
                movement = np.mean(diff)
                if movement > 15:  # Mucho movimiento
                    self.face_status_label.configure(
                        text="🤚 Mantente quieto - Detectando movimiento",
                        foreground='#f39c12'
                    )
                    self.previous_frame = gray
                    self.root.after(800, self.capture_sample)
                    return
            
            self.previous_frame = gray
            
            # Intentar crear encoding
            encoding = self.auth_system.face_encoder.encode_face_from_image(frame)
            
            if encoding is not None:
                self.samples_captured += 1
                print(f"✅ DEBUG: Muestra {self.samples_captured} capturada exitosamente")
                
                # Guardar encoding para promediado final
                if not hasattr(self, 'collected_encodings'):
                    self.collected_encodings = []
                self.collected_encodings.append(encoding)
                
                # Actualizar interfaz
                self.progress_bar['value'] = self.samples_captured
                self.progress_label.configure(
                    text=f"{self.samples_captured} / {self.required_samples} muestras capturadas"
                )
                
                self.face_status_label.configure(
                    text=f"📸 Muestra {self.samples_captured} capturada ✅",
                    foreground='#27ae60'
                )
                
                # Feedback sonoro visual
                self.root.after(100, lambda: self.face_status_label.configure(
                    text=f"📸 Muestra {self.samples_captured} capturada ✅",
                    foreground='#2ecc71'
                ))
                
                if self.samples_captured >= self.required_samples:
                    # Registro completo - promediar encodings
                    self.complete_registration_with_average()
                else:
                    # Programar siguiente captura con pausa más larga
                    self.face_status_label.configure(
                        text=f"⏳ Preparando siguiente muestra... ({self.required_samples - self.samples_captured} restantes)",
                        foreground='#3498db'
                    )
                    self.root.after(2000, self.capture_sample)  # 2 segundos entre capturas
            else:
                # Rostro no válido, intentar de nuevo con mensaje específico
                print("⚠️ DEBUG: No se pudo procesar el rostro, reintentando...")
                self.face_status_label.configure(
                    text="🔄 Procesando rostro... Mantente en el cuadro verde",
                    foreground='#f39c12'
                )
                self.root.after(1000, self.capture_sample)  # Reintentar en 1 segundo
                
        except Exception as e:
            print(f"❌ DEBUG: Error en capture_sample: {e}")
            self.show_status(f"❌ Error: {e}", "error")
            self.stop_registration()
    
    def complete_registration_with_average(self):
        """Completar registro promediando múltiples encodings"""
        try:
            self.show_status("🧮 Calculando encoding promedio...", "info")
            
            if not hasattr(self, 'collected_encodings') or len(self.collected_encodings) == 0:
                self.show_status("❌ Error: No hay encodings válidos", "error")
                self.stop_registration()
                return
            
            # Calcular encoding promedio para mayor precisión
            encoding_matrix = np.array(self.collected_encodings)
            averaged_encoding = np.mean(encoding_matrix, axis=0)
            
            print(f"✅ DEBUG: Promediando {len(self.collected_encodings)} encodings")
            print(f"📊 DEBUG: Encoding final tiene {len(averaged_encoding)} dimensiones")
            
            # Normalizar el encoding final
            averaged_encoding = (averaged_encoding - np.mean(averaged_encoding)) / (np.std(averaged_encoding) + 1e-10)
            
            self.complete_registration(averaged_encoding)
            
        except Exception as e:
            print(f"❌ DEBUG: Error calculando promedio: {e}")
            self.show_status(f"❌ Error calculando promedio: {e}", "error")
            self.stop_registration()
    
    def complete_registration(self, final_encoding):
        """Completar el proceso de registro con flujo automático mejorado"""
        print("🔄 DEBUG: Iniciando complete_registration...")
        self.show_status("💾 Guardando datos biométricos...", "info")
        
        try:
            print(f"🔄 DEBUG: Llamando register_face_biometric para usuario {self.user_id}")
            print(f"🔄 DEBUG: Encoding shape: {final_encoding.shape if hasattr(final_encoding, 'shape') else 'No shape'}")
            
            # Registrar en base de datos
            result = self.auth_system.register_face_biometric(self.user_id, final_encoding)
            
            print(f"🔄 DEBUG: Resultado de register_face_biometric: {result}")
            
            if result and result.get('success'):
                print("✅ DEBUG: Registro en BD exitoso, iniciando cierre automático...")
                self.registering = False
                
                # Desactivar cámara inmediatamente
                if self.camera_active and self.camera:
                    self.camera_active = False
                    self.camera.release()
                    print("📹 DEBUG: Cámara desactivada")
                
                # Mensaje de confirmación claro y específico
                self.show_status("✅ Biometría del usuario registrada con éxito", "success")
                self.instructions_label.configure(
                    text="🎉 ¡Proceso completado!\nTu biometría ha sido registrada correctamente",
                    foreground='#27ae60'
                )
                self.face_status_label.configure(
                    text="✅ Registro biométrico completado",
                    foreground='#27ae60'
                )
                
                # Actualizar barra de progreso a 100%
                self.progress_bar['value'] = self.required_samples
                self.progress_label.configure(
                    text=f"✅ Completado: {self.required_samples}/{self.required_samples} muestras",
                    foreground='#27ae60'
                )
                
                # Deshabilitar todos los controles para indicar finalización
                self.start_btn.configure(state=tk.DISABLED)
                self.start_registration_btn.configure(state=tk.DISABLED)
                self.cancel_btn.configure(text="✅ Finalizado", state=tk.DISABLED)
                
                print("🎉 DEBUG: Registro biométrico completado exitosamente")
                print(f"👤 DEBUG: Usuario {self.user_id} ahora tiene biometría registrada")
                
                # Cerrar automáticamente e inmediatamente (1.5 segundos para que el usuario vea el éxito)
                print("⏰ DEBUG: Programando cierre automático en 1.5 segundos...")
                self.root.after(1500, self._auto_close_success)
                
            else:
                error_msg = result.get('error', 'Error desconocido') if result else 'Resultado nulo'
                print(f"❌ DEBUG: Error en registro BD: {error_msg}")
                self.show_status(f"❌ Error guardando: {error_msg}", "error")
                self.stop_registration()
                
        except Exception as e:
            print(f"❌ DEBUG: Excepción en complete_registration: {e}")
            import traceback
            traceback.print_exc()
            self.show_status(f"❌ Error: {e}", "error")
            self.stop_registration()
    
    def _auto_close_success(self):
        """Cierre automático tras registro exitoso"""
        try:
            # Notificar al sistema principal que se actualizó la biometría
            if hasattr(self.auth_system, 'refresh_user_state'):
                self.auth_system.refresh_user_state(self.user_id)
            
            print("🔐 DEBUG: Cerrando ventana de registro biométrico automáticamente")
            print("✅ DEBUG: El usuario puede ahora usar login biométrico")
            
            # Cerrar ventana sin mostrar mensaje adicional (ya se mostró el éxito)
            self.close_window()
            
        except Exception as e:
            print(f"❌ DEBUG: Error en cierre automático: {e}")
            self.close_window()
    
    def _show_success_and_close(self):
        """Método legacy - ya no se usa con el nuevo flujo automático"""
        # Este método se mantiene por compatibilidad pero el nuevo flujo usa _auto_close_success
        self._auto_close_success()
    
    def stop_registration(self):
        """Detener proceso de registro"""
        self.registering = False
        self.start_registration_btn.configure(state=tk.NORMAL)
        self.cancel_btn.configure(text="❌ Cancelar", command=self.close_window)
        
        self.show_status("Registro detenido", "info")
        self.instructions_label.configure(
            text="Registro detenido. Puedes intentar de nuevo.",
            foreground='#7f8c8d'
        )
    
    def show_status(self, message: str, status_type: str = "info"):
        """Mostrar mensaje de estado con colores"""
        colors = {
            "info": "#3498db",
            "success": "#27ae60", 
            "error": "#e74c3c"
        }
        
        self.status_label.configure(
            text=message,
            foreground=colors.get(status_type, "#7f8c8d")
        )
    
    def close_window(self):
        """Cerrar ventana y limpiar recursos"""
        if self.camera_active and self.camera:
            self.camera_active = False
            self.camera.release()
        
        self.root.destroy()

def main():
    """Función principal"""
    print("🚀 Iniciando Sistema de Autenticación Dual...")
    
    try:
        auth_system = DualAuthSystem()
        auth_system.start_login_interface()
    except Exception as e:
        print(f"❌ Error iniciando sistema: {e}")

if __name__ == "__main__":
    main()
