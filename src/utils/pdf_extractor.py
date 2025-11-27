import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
from typing import Dict, List, Any, Tuple
import base64

class PDFExtractor:
    """Extractor de contenido de PDFs usando PyMuPDF y pytesseract"""
    
    def __init__(self):
        # Configurar pytesseract para Windows
        import os
        import platform
        
        if platform.system() == 'Windows':
            # Rutas comunes de instalación de Tesseract en Windows
            possible_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                r'C:\Users\{}\AppData\Local\Tesseract-OCR\tesseract.exe'.format(os.getenv('USERNAME', '')),
                r'C:\tesseract\tesseract.exe'
            ]
            
            # Buscar Tesseract en las rutas posibles
            tesseract_found = False
            for path in possible_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    tesseract_found = True
                    print(f"Tesseract encontrado en: {path}")
                    break
            
            if not tesseract_found:
                print("ADVERTENCIA: Tesseract no encontrado en las rutas comunes.")
                print("Para usar OCR en imágenes, instale Tesseract desde: https://github.com/UB-Mannheim/tesseract/wiki")
                print("O configure manualmente la ruta en pdf_extractor.py")
        
        # Verificar si Tesseract está disponible
        try:
            pytesseract.get_tesseract_version()
            self.tesseract_available = True
            print("Tesseract OCR configurado correctamente")
        except Exception as e:
            self.tesseract_available = False
            print(f"Tesseract no disponible: {e}")
            print("El procesamiento de imágenes con OCR estará deshabilitado")
    
    def extract_content(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """Extrae todo el contenido del PDF
        
        Args:
            pdf_bytes: Contenido del PDF en bytes
            
        Returns:
            Dict con texto, imágenes y metadatos extraídos
        """
        try:
            # Abrir PDF desde bytes
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            # Extraer información básica
            metadata = self._extract_metadata(pdf_document)
            
            # Extraer texto de todas las páginas
            text_content = self._extract_text(pdf_document)
            
            # Extraer imágenes y aplicar OCR
            images_content = self._extract_images_with_ocr(pdf_document)
            
            # Cerrar documento
            pdf_document.close()
            
            return {
                "metadata": metadata,
                "text": text_content,
                "images": images_content,
                "total_pages": len(text_content["pages"]),
                "has_images": len(images_content["images"]) > 0,
                "extraction_success": True
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "extraction_success": False,
                "metadata": {},
                "text": {"full_text": "", "pages": []},
                "images": {"ocr_text": "", "images": []}
            }
    
    def _extract_metadata(self, pdf_document) -> Dict[str, Any]:
        """Extrae metadatos del PDF"""
        try:
            metadata = pdf_document.metadata
            return {
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "subject": metadata.get("subject", ""),
                "creator": metadata.get("creator", ""),
                "producer": metadata.get("producer", ""),
                "creation_date": metadata.get("creationDate", ""),
                "modification_date": metadata.get("modDate", ""),
                "page_count": pdf_document.page_count,
                "is_encrypted": pdf_document.needs_pass
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _extract_text(self, pdf_document) -> Dict[str, Any]:
        """Extrae texto de todas las páginas"""
        try:
            full_text = ""
            pages_text = []
            
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                page_text = page.get_text()
                
                pages_text.append({
                    "page_number": page_num + 1,
                    "text": page_text,
                    "char_count": len(page_text)
                })
                
                full_text += page_text + "\n"
            
            return {
                "full_text": full_text.strip(),
                "pages": pages_text,
                "total_chars": len(full_text),
                "has_text": len(full_text.strip()) > 0
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "full_text": "",
                "pages": [],
                "has_text": False
            }
    
    def _extract_images_with_ocr(self, pdf_document) -> Dict[str, Any]:
        """Extrae imágenes y aplica OCR"""
        try:
            all_ocr_text = ""
            images_info = []
            
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    try:
                        # Extraer imagen
                        xref = img[0]
                        pix = fitz.Pixmap(pdf_document, xref)
                        
                        # Convertir a PIL Image si no es GRAY o RGB
                        if pix.n - pix.alpha < 4:
                            img_data = pix.tobytes("ppm")
                            pil_image = Image.open(io.BytesIO(img_data))
                        else:
                            # Convertir CMYK a RGB
                            pix = fitz.Pixmap(fitz.csRGB, pix)
                            img_data = pix.tobytes("ppm")
                            pil_image = Image.open(io.BytesIO(img_data))
                        
                        # Aplicar OCR solo si Tesseract está disponible
                        if self.tesseract_available:
                            ocr_text = pytesseract.image_to_string(pil_image, lang='spa+eng')
                        else:
                            ocr_text = "[OCR no disponible - Tesseract no configurado]"
                        
                        # Guardar información de la imagen
                        images_info.append({
                            "page": page_num + 1,
                            "image_index": img_index,
                            "ocr_text": ocr_text.strip(),
                            "width": pix.width,
                            "height": pix.height,
                            "has_text": len(ocr_text.strip()) > 0
                        })
                        
                        all_ocr_text += ocr_text + "\n"
                        
                        # Limpiar memoria
                        pix = None
                        
                    except Exception as img_error:
                        images_info.append({
                            "page": page_num + 1,
                            "image_index": img_index,
                            "error": str(img_error),
                            "ocr_text": "",
                            "has_text": False
                        })
            
            return {
                "ocr_text": all_ocr_text.strip(),
                "images": images_info,
                "total_images": len(images_info),
                "images_with_text": len([img for img in images_info if img.get("has_text", False)])
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "ocr_text": "",
                "images": [],
                "total_images": 0
            }

# Instancia global del extractor
pdf_extractor = PDFExtractor()