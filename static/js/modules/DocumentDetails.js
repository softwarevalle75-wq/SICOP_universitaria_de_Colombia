// ===== DOCUMENT DETAILS MODULE =====

export class DocumentDetails {
    constructor(pdfHandler) {
        this.pdfHandler = pdfHandler;
        this.createModal();
    }

    createModal() {
        // Crear el modal si no existe
        if (!document.getElementById('documentDetailsModal')) {
            const modal = document.createElement('div');
            modal.id = 'documentDetailsModal';
            modal.className = 'document-modal';
            modal.innerHTML = `
                <div class="modal-overlay"></div>
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>Información Detallada del Documento</h3>
                        <button class="modal-close">✕</button>
                    </div>
                    <div class="modal-body" id="documentDetailsContent">
                        <!-- Contenido dinámico -->
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
            
            // Agregar event listeners
            this.bindModalEvents();
            
            // Agregar estilos CSS
            this.addModalStyles();
        }
    }

    bindModalEvents() {
        const modal = document.getElementById('documentDetailsModal');
        const overlay = modal.querySelector('.modal-overlay');
        const closeBtn = modal.querySelector('.modal-close');
        
        // Cerrar al hacer click en el overlay
        overlay.addEventListener('click', () => this.closeModal());
        
        // Cerrar al hacer click en el botón X
        closeBtn.addEventListener('click', () => this.closeModal());
        
        // Cerrar con la tecla ESC
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modal.classList.contains('show')) {
                this.closeModal();
            }
        });
        
        // Prevenir que el click en el contenido cierre el modal
        modal.querySelector('.modal-content').addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }
    
    addModalStyles() {
        if (!document.getElementById('documentDetailsStyles')) {
            const style = document.createElement('style');
            style.id = 'documentDetailsStyles';
            style.textContent = `
                .document-modal {
                    display: none;
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    z-index: 1000;
                }
                
                .document-modal.show {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                
                .modal-overlay {
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.5);
                }
                
                .modal-content {
                    position: relative;
                    background: white;
                    border-radius: 8px;
                    max-width: 800px;
                    max-height: 90vh;
                    width: 90%;
                    overflow: hidden;
                    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
                    animation: modalSlideIn 0.3s ease;
                    z-index: 1001;
                }
                
                @keyframes modalSlideIn {
                    from {
                        opacity: 0;
                        transform: translateY(-20px) scale(0.95);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0) scale(1);
                    }
                }
                
                .modal-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 1rem 1.5rem;
                    border-bottom: 1px solid #e9ecef;
                    background: #f8f9fa;
                }
                
                .modal-header h3 {
                    margin: 0;
                    color: #495057;
                }
                
                .modal-close {
                    background: none;
                    border: none;
                    font-size: 1.5rem;
                    cursor: pointer;
                    color: #6c757d;
                    padding: 0;
                    width: 30px;
                    height: 30px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                
                .modal-close:hover {
                    color: #dc3545;
                }
                
                .modal-body {
                    padding: 1.5rem;
                    max-height: calc(90vh - 80px);
                    overflow-y: auto;
                }
                
                .detail-section {
                    margin-bottom: 1.5rem;
                    padding: 1rem;
                    border: 1px solid #e9ecef;
                    border-radius: 6px;
                    background: #f8f9fa;
                }
                
                .detail-section h4 {
                    margin: 0 0 1rem 0;
                    color: #495057;
                    font-size: 1.1rem;
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                }
                
                .detail-grid {
                    display: grid;
                    grid-template-columns: 1fr 2fr;
                    gap: 0.5rem;
                    margin-bottom: 1rem;
                }
                
                .detail-label {
                    font-weight: 600;
                    color: #6c757d;
                }
                
                .detail-value {
                    color: #495057;
                }
                
                .json-content {
                    background: #f1f3f4;
                    border: 1px solid #d1d5db;
                    border-radius: 4px;
                    padding: 1rem;
                    font-family: 'Courier New', monospace;
                    font-size: 0.9rem;
                    white-space: pre-wrap;
                    max-height: 300px;
                    overflow-y: auto;
                }
                
                .keywords-list {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 0.5rem;
                }
                
                .keyword-tag {
                    background: #007bff;
                    color: white;
                    padding: 0.2rem 0.5rem;
                    border-radius: 12px;
                    font-size: 0.8rem;
                }
                
                .confidence-bar {
                    width: 100%;
                    height: 20px;
                    background: #e9ecef;
                    border-radius: 10px;
                    overflow: hidden;
                }
                
                .confidence-fill {
                    height: 100%;
                    background: linear-gradient(90deg, #dc3545, #ffc107, #28a745);
                    transition: width 0.3s ease;
                }
            `;
            document.head.appendChild(style);
        }
    }

    async showDocumentDetails(docId) {
        const doc = this.pdfHandler.documents.find(d => d.id == docId);
        if (!doc) {
            alert('Documento no encontrado');
            return;
        }

        const content = this.generateDetailContent(doc);
        document.getElementById('documentDetailsContent').innerHTML = content;
        
        const modal = document.getElementById('documentDetailsModal');
        modal.classList.add('show');
    }

    generateDetailContent(doc) {
        const aiInfo = doc.ai_info;
        const contentInfo = doc.content_info;
        const processingInfo = doc.processing_info;

        let content = `
            <!-- Información Básica -->
            <div class="detail-section">
                <h4>📄 Información Básica</h4>
                <div class="detail-grid">
                    <span class="detail-label">Nombre:</span>
                    <span class="detail-value">${doc.nombre_pdf || doc.filename || 'Sin nombre'}</span>
                    
                    <span class="detail-label">Estado:</span>
                    <span class="detail-value">${this.getStatusText(doc.estado_procesamiento)}</span>
                    
                    <span class="detail-label">Tamaño:</span>
                    <span class="detail-value">${this.formatFileSize(doc.tamano_archivo)}</span>
                    
                    <span class="detail-label">Fecha de recepción:</span>
                    <span class="detail-value">${this.formatDate(doc.fecha_hora_recepcion)}</span>
                    
                    <span class="detail-label">Dominio origen:</span>
                    <span class="detail-value">${doc.dominio_origen || 'N/A'}</span>
                </div>
            </div>
        `;

        // Información de IA removida por solicitud del usuario

        // Información de contenido
        if (contentInfo) {
            content += `
                <div class="detail-section">
                    <h4>📊 Análisis de Contenido</h4>
                    <div class="detail-grid">
                        <span class="detail-label">Total de páginas:</span>
                        <span class="detail-value">${contentInfo.total_pages}</span>
                        
                        <span class="detail-label">Caracteres totales:</span>
                        <span class="detail-value">${this.formatNumber(contentInfo.total_chars)}</span>
                        
                        <span class="detail-label">Contiene imágenes:</span>
                        <span class="detail-value">${contentInfo.has_images ? 'Sí' : 'No'}</span>
                        
                        ${contentInfo.has_images ? `
                            <span class="detail-label">Imágenes con texto:</span>
                            <span class="detail-value">${contentInfo.images_with_text}</span>
                        ` : ''}
                        
                        <span class="detail-label">Contiene texto:</span>
                        <span class="detail-value">${contentInfo.has_text ? 'Sí' : 'No'}</span>
                    </div>
                </div>
            `;
        }

        // Información de procesamiento
        if (processingInfo) {
            content += `
                <div class="detail-section">
                    <h4>⚙️ Información de Procesamiento</h4>
                    <div class="detail-grid">
                        <span class="detail-label">Fecha de procesamiento:</span>
                        <span class="detail-value">${this.formatDate(processingInfo.processed_at)}</span>
                        
                        <span class="detail-label">Tiempo de procesamiento:</span>
                        <span class="detail-value">${processingInfo.processing_time?.toFixed(2) || 'N/A'} segundos</span>
                        
                        <span class="detail-label">Versión del procesador:</span>
                        <span class="detail-value">${processingInfo.version || 'N/A'}</span>
                    </div>
                </div>
            `;
        }

        // JSON completo de información extraída desde la base de datos
        if (doc.contenido_json) {
            content += `
                <div class="detail-section">
                    <h4>🔍 Contenido JSON Procesado</h4>
                    <div class="json-content">${JSON.stringify(doc.contenido_json, null, 2)}</div>
                </div>
            `;
        } else {
            content += `
                <div class="detail-section">
                    <h4>🔍 Contenido JSON Procesado</h4>
                    <div class="json-content">No hay contenido procesado disponible para este documento.</div>
                </div>
            `;
        }

        return content;
    }

    closeModal() {
        const modal = document.getElementById('documentDetailsModal');
        modal.classList.remove('show');
    }

    // Métodos auxiliares
    getStatusText(status) {
        const statusMap = {
            'pendiente': 'Pendiente',
            'procesando': 'Procesando',
            'procesado': 'Procesado',
            'error': 'Error',
            'pending': 'Pendiente',
            'processing': 'Procesando',
            'completed': 'Completado'
        };
        return statusMap[status] || status;
    }



    formatDate(dateString) {
        if (!dateString) return 'N/A';
        return new Date(dateString).toLocaleDateString('es-ES', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    formatFileSize(bytes) {
        if (!bytes) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    formatNumber(num) {
        if (!num) return '0';
        if (num < 1000) return num.toString();
        if (num < 1000000) return (num / 1000).toFixed(1) + 'K';
        return (num / 1000000).toFixed(1) + 'M';
    }
}