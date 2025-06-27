#!/usr/bin/env python3
"""
Sistema de Autenticación Dual - Punto de Entrada Principal
Combina autenticación tradicional (email/password) con biométrica
"""

import sys
import os

# Añadir src al path para importaciones
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """Lanzar sistema de autenticación dual"""
    try:
        print("🚀 Iniciando Sistema de Autenticación Dual...")
        print("🔐 Cargando módulos de autenticación...")
        
        # Importar y ejecutar el sistema dual
        from dual_auth_system import DualAuthSystem
        
        auth_system = DualAuthSystem()
        auth_system.start_login_interface()
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        print("💡 Asegúrate de que todas las dependencias estén instaladas:")
        print("   pip install -r requirements.txt")
        print("💡 Y que la estructura del proyecto esté correcta.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
