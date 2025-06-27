#!/usr/bin/env python3
"""
Implementación de Encoding Facial Robusto sin dependencias complejas
Alternativa segura a face_recognition usando OpenCV y técnicas avanzadas
"""

import cv2
import numpy as np
import json
import hashlib
from typing import List, Tuple, Optional

class RobustFaceEncoder:
    """Codificador facial robusto usando múltiples características"""
    
    def __init__(self):
        # Inicializar detectores
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        
        # Parámetros de seguridad
        self.encoding_dim = 128  # Simular dimensión de face_recognition
        
    def extract_facial_features(self, face_image: np.ndarray) -> np.ndarray:
        """Extraer características faciales robustas"""
        features = []
        
        # Convertir a escala de grises
        if len(face_image.shape) == 3:
            gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = face_image
        
        # Redimensionar a tamaño estándar
        gray = cv2.resize(gray, (128, 128))
        
        # 1. Histograma Local Binario (LBP) - Robusto a iluminación
        def compute_lbp(image, radius=1, n_points=8):
            h, w = image.shape
            lbp = np.zeros((h, w), dtype=np.uint8)
            
            for i in range(radius, h - radius):
                for j in range(radius, w - radius):
                    center = image[i, j]
                    pattern = 0
                    for k in range(n_points):
                        angle = 2 * np.pi * k / n_points
                        x = int(round(i + radius * np.cos(angle)))
                        y = int(round(j + radius * np.sin(angle)))
                        if x >= 0 and x < h and y >= 0 and y < w:
                            if image[x, y] >= center:
                                pattern |= (1 << k)
                    lbp[i, j] = pattern
            
            # Histograma de LBP
            hist_lbp, _ = np.histogram(lbp.ravel(), bins=256, range=(0, 256))
            return hist_lbp / np.sum(hist_lbp)  # Normalizar
        
        lbp_features = compute_lbp(gray)
        features.extend(lbp_features[:32])  # Tomar primeros 32 bins
        
        # 2. Momentos de Hu - Invariantes geométricos
        moments = cv2.moments(gray)
        hu_moments = cv2.HuMoments(moments).flatten()
        # Log-transform para estabilidad numérica
        hu_moments = -np.sign(hu_moments) * np.log10(np.abs(hu_moments) + 1e-10)
        features.extend(hu_moments)  # 7 características
        
        # 3. Análisis de gradientes direccionales
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        magnitude = np.sqrt(grad_x**2 + grad_y**2)
        angle = np.arctan2(grad_y, grad_x)
        
        # Histograma de gradientes orientados
        hist_grad, _ = np.histogram(angle.ravel(), bins=16, range=(-np.pi, np.pi))
        hist_grad = hist_grad / (np.sum(hist_grad) + 1e-10)
        features.extend(hist_grad)  # 16 características
        
        # 4. Características de textura usando filtros de Gabor
        def gabor_filter_bank(image):
            filters = []
            angles = [0, 45, 90, 135]  # 4 orientaciones
            frequencies = [0.1, 0.3]  # 2 frecuencias
            
            for angle in angles:
                for freq in frequencies:
                    kernel = cv2.getGaborKernel((21, 21), 3, np.radians(angle), 
                                              2 * np.pi * freq, 0.5, 0, ktype=cv2.CV_32F)
                    filtered = cv2.filter2D(image, cv2.CV_8UC3, kernel)
                    filters.append(np.std(filtered))  # Desviación estándar como característica
            
            return filters
        
        gabor_features = gabor_filter_bank(gray)
        features.extend(gabor_features)  # 8 características
        
        # 5. Características estadísticas por regiones
        h, w = gray.shape
        regions = [
            gray[0:h//2, 0:w//2],      # Superior izquierda
            gray[0:h//2, w//2:w],      # Superior derecha
            gray[h//2:h, 0:w//2],      # Inferior izquierda
            gray[h//2:h, w//2:w]       # Inferior derecha
        ]
        
        for region in regions:
            features.extend([
                np.mean(region),
                np.std(region),
                np.max(region) - np.min(region)
            ])  # 3 características por región = 12 total
        
        # 6. Análisis de ojos (si se detectan)
        eyes = self.eye_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        eye_features = [
            len(eyes),  # Número de ojos detectados
            np.mean([ey[2]*ey[3] for ey in eyes]) if len(eyes) > 0 else 0,  # Área promedio
            np.std([ey[0] for ey in eyes]) if len(eyes) > 0 else 0  # Variación horizontal
        ]
        features.extend(eye_features)  # 3 características
        
        # Completar hasta 128 dimensiones con características adicionales
        current_len = len(features)
        if current_len < self.encoding_dim:
            # Agregar características espectrales
            fft = np.fft.fft2(gray)
            fft_magnitude = np.abs(fft)
            fft_features = []
            
            # Características espectrales por cuadrantes
            h, w = fft_magnitude.shape
            quadrants = [
                fft_magnitude[0:h//2, 0:w//2],
                fft_magnitude[0:h//2, w//2:w],
                fft_magnitude[h//2:h, 0:w//2],
                fft_magnitude[h//2:h, w//2:w]
            ]
            
            for quad in quadrants:
                fft_features.extend([
                    np.mean(quad),
                    np.std(quad)
                ])
            
            features.extend(fft_features[:self.encoding_dim - current_len])
        
        # Asegurar exactamente 128 dimensiones
        features = features[:self.encoding_dim]
        if len(features) < self.encoding_dim:
            features.extend([0.0] * (self.encoding_dim - len(features)))
        
        return np.array(features, dtype=np.float64)
    
    def create_encoding(self, face_image: np.ndarray) -> Optional[np.ndarray]:
        """Crear encoding robusto de un rostro"""
        try:
            # Verificar que la imagen tenga tamaño mínimo
            if face_image.shape[0] < 64 or face_image.shape[1] < 64:
                return None
            
            # Extraer características
            encoding = self.extract_facial_features(face_image)
            
            # Normalizar el encoding
            encoding = (encoding - np.mean(encoding)) / (np.std(encoding) + 1e-10)
            
            return encoding
            
        except Exception as e:
            print(f"Error creando encoding: {e}")
            return None
    
    def compare_encodings(self, encoding1: np.ndarray, encoding2: np.ndarray) -> float:
        """Comparar dos encodings y retornar distancia (0=idéntico, mayor=más diferente)"""
        try:
            # Calcular múltiples métricas de distancia para mayor robustez
            
            # 1. Distancia euclidiana normalizada
            euclidean_dist = np.linalg.norm(encoding1 - encoding2) / np.sqrt(len(encoding1))
            
            # 2. Distancia coseno
            dot_product = np.dot(encoding1, encoding2)
            norm1 = np.linalg.norm(encoding1)
            norm2 = np.linalg.norm(encoding2)
            cosine_similarity = dot_product / (norm1 * norm2 + 1e-10)
            cosine_distance = 1 - cosine_similarity
            
            # 3. Distancia de Manhattan normalizada
            manhattan_dist = np.sum(np.abs(encoding1 - encoding2)) / len(encoding1)
            
            # 4. Correlación pearson como distancia
            correlation = np.corrcoef(encoding1, encoding2)[0, 1]
            if np.isnan(correlation):
                correlation = 0
            correlation_distance = 1 - abs(correlation)
            
            # Combinar métricas con pesos (euclidiana tiene más peso)
            combined_distance = (
                0.4 * euclidean_dist +
                0.3 * cosine_distance +
                0.2 * manhattan_dist +
                0.1 * correlation_distance
            )
            
            # Normalizar resultado final
            final_distance = np.clip(combined_distance, 0.0, 2.0) / 2.0
            
            return float(final_distance)
            
        except Exception as e:
            print(f"Error comparando encodings: {e}")
            return 1.0  # Máxima distancia en caso de error
    
    def encode_face_from_image(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Detectar y codificar rostro desde una imagen completa - Versión mejorada"""
        try:
            print(f"🔍 DEBUG: Procesando imagen de tamaño {image.shape}")
            
            # Convertir a escala de grises si es necesario
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Aplicar ecualización del histograma para mejorar el contraste
            gray = cv2.equalizeHist(gray)
            
            # Aplicar filtro bilateral para reducir ruido preservando bordes
            gray = cv2.bilateralFilter(gray, 5, 80, 80)
            
            # Intentar múltiples configuraciones de detección (desde más restrictiva a más permisiva)
            detection_configs = [
                {"scaleFactor": 1.1, "minNeighbors": 5, "minSize": (60, 60), "maxSize": (300, 300)},  # Más restrictiva
                {"scaleFactor": 1.1, "minNeighbors": 4, "minSize": (50, 50), "maxSize": (400, 400)},  # Intermedia
                {"scaleFactor": 1.2, "minNeighbors": 3, "minSize": (40, 40), "maxSize": (500, 500)},  # Más permisiva
                {"scaleFactor": 1.3, "minNeighbors": 3, "minSize": (30, 30), "maxSize": (600, 600)}   # Muy permisiva
            ]
            
            faces = []
            for i, config in enumerate(detection_configs):
                try:
                    faces = self.face_cascade.detectMultiScale(gray, **config)
                    print(f"🔍 DEBUG: Configuración {i+1}: {len(faces)} rostros detectados")
                    if len(faces) > 0:
                        break
                except cv2.error as e:
                    print(f"⚠️ DEBUG: Error en configuración {i+1}: {e}")
                    continue
            
            if len(faces) == 0:
                print("⚠️ DEBUG: No se detectaron rostros con ninguna configuración")
                return None
            
            # Filtrar rostros válidos (no demasiado pequeños ni grandes)
            valid_faces = []
            img_area = gray.shape[0] * gray.shape[1]
            
            for (x, y, w, h) in faces:
                face_area = w * h
                area_ratio = face_area / img_area
                aspect_ratio = w / h
                
                # Filtros de calidad
                if (0.01 <= area_ratio <= 0.8 and  # Área razonable
                    0.7 <= aspect_ratio <= 1.4):   # Proporción facial válida
                    valid_faces.append((x, y, w, h, face_area))
                    print(f"🔍 DEBUG: Rostro válido - área: {face_area}, ratio: {area_ratio:.3f}")
            
            if len(valid_faces) == 0:
                print("⚠️ DEBUG: Ningún rostro pasó los filtros de calidad")
                return None
            
            # Seleccionar el mejor rostro (más grande y más centrado)
            best_face = None
            best_score = -1
            center_x, center_y = gray.shape[1] // 2, gray.shape[0] // 2
            
            for (x, y, w, h, area) in valid_faces:
                face_center_x = x + w // 2
                face_center_y = y + h // 2
                
                # Distancia al centro (normalizada)
                center_dist = np.sqrt((face_center_x - center_x)**2 + (face_center_y - center_y)**2)
                max_dist = np.sqrt(center_x**2 + center_y**2)
                center_score = 1 - (center_dist / max_dist)
                
                # Puntuación por área (normalizada)
                area_score = area / max([f[4] for f in valid_faces])
                
                # Puntuación combinada (favorece rostros grandes y centrados)
                combined_score = 0.6 * area_score + 0.4 * center_score
                
                if combined_score > best_score:
                    best_score = combined_score
                    best_face = (x, y, w, h)
            
            x, y, w, h = best_face
            print(f"🔍 DEBUG: Mejor rostro seleccionado - puntuación: {best_score:.3f}")
            
            # Extraer región del rostro con margen inteligente
            margin_ratio = 0.15  # 15% de margen
            margin_x = int(w * margin_ratio)
            margin_y = int(h * margin_ratio)
            
            x1 = max(0, x - margin_x)
            y1 = max(0, y - margin_y)
            x2 = min(image.shape[1], x + w + margin_x)
            y2 = min(image.shape[0], y + h + margin_y)
            
            face_region = image[y1:y2, x1:x2]
            print(f"🔍 DEBUG: Región facial extraída: {face_region.shape}")
            
            # Verificar que la región extraída sea válida
            if face_region.shape[0] < 32 or face_region.shape[1] < 32:
                print("❌ DEBUG: Región facial demasiado pequeña")
                return None
            
            # Crear encoding del rostro
            encoding = self.create_encoding(face_region)
            
            if encoding is not None:
                print("✅ DEBUG: Encoding creado exitosamente")
                return encoding
            else:
                print("❌ DEBUG: Error al crear encoding")
                return None
            
        except Exception as e:
            print(f"❌ DEBUG: Error en encode_face_from_image: {e}")
            import traceback
            traceback.print_exc()
            return None

# Funciones de compatibilidad con face_recognition
def face_locations(image: np.ndarray, model: str = "hog") -> List[Tuple[int, int, int, int]]:
    """Detectar ubicaciones de rostros (compatible con face_recognition)"""
    try:
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        
        # Convertir formato (x,y,w,h) a (top, right, bottom, left)
        locations = []
        for (x, y, w, h) in faces:
            locations.append((y, x + w, y + h, x))
        
        return locations
        
    except Exception as e:
        print(f"Error detectando rostros: {e}")
        return []

def face_encodings(image: np.ndarray, known_face_locations: List[Tuple[int, int, int, int]]) -> List[np.ndarray]:
    """Crear encodings de rostros en ubicaciones conocidas"""
    encoder = RobustFaceEncoder()
    encodings = []
    
    try:
        for (top, right, bottom, left) in known_face_locations:
            # Extraer región del rostro
            face_region = image[top:bottom, left:right]
            
            # Crear encoding
            encoding = encoder.create_encoding(face_region)
            if encoding is not None:
                encodings.append(encoding)
        
        return encodings
        
    except Exception as e:
        print(f"Error creando encodings: {e}")
        return []

def face_distance(known_face_encodings: List[np.ndarray], face_encoding_to_check: np.ndarray) -> List[float]:
    """Calcular distancias entre encodings (compatible con face_recognition)"""
    encoder = RobustFaceEncoder()
    distances = []
    
    for known_encoding in known_face_encodings:
        distance = encoder.compare_encodings(known_encoding, face_encoding_to_check)
        distances.append(distance)
    
    return distances

# Test de compatibilidad
if __name__ == "__main__":
    print("🧪 Probando codificador facial robusto...")
    
    # Crear imagen de prueba
    test_image = np.random.randint(0, 255, (150, 150, 3), dtype=np.uint8)
    
    # Probar detección
    locations = face_locations(test_image)
    print(f"Rostros detectados: {len(locations)}")
    
    if locations:
        # Probar encoding
        encodings = face_encodings(test_image, locations)
        print(f"Encodings creados: {len(encodings)}")
        
        if encodings:
            print(f"Dimensiones del encoding: {len(encodings[0])}")
            
            # Probar comparación
            distances = face_distance([encodings[0]], encodings[0])
            print(f"Distancia consigo mismo: {distances[0]:.6f}")
    
    print("✅ Codificador facial robusto listo")
