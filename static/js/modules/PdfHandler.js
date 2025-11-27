// ===== PDF HANDLER MODULE =====

export class PdfHandler {
    constructor() {
        this.documents = [];
        this.selectedDocument = null;
        this.currentFilter = 'todos';
        this.tableRenderer = null;
        this.documentDetails = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadDocuments();
    }

    setTableRenderer(tableRenderer) {
        this.tableRenderer = tableRenderer;
    }

    setDocumentDetails(documentDetails) {
        this.documentDetails = documentDetails;
    }

    bindEvents() {
        // Botón actualizar
        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadDocuments());
        }

        // Filtros
        const filterSelect = document.getElementById('filterSelect');
        if (filterSelect) {
            filterSelect.addEventListener('change', (e) => {
                this.currentFilter = e.target.value;
                this.filterDocuments();
            });
        }

        // Buscador
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.searchDocuments(e.target.value);
            });
        }
    }

    async loadDocuments() {
        try {
            const response = await fetch('/api/documents');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.documents = data.data?.documentos || [];
            this.renderTable();
            
            // Deshabilitar chat si no hay documento seleccionado
            if (!this.selectedDocument && window.chatHandler) {
                window.chatHandler.disableChat();
            }
        } catch (error) {
            console.error('Error loading documents:', error);
            this.showMessage('Error al cargar documentos: ' + error.message, 'error');
        }
    }

    filterDocuments() {
        this.renderTable();
    }

    searchDocuments(query) {
        this.renderTable(query);
    }

    renderTable(searchQuery = '') {
        if (this.tableRenderer) {
            this.tableRenderer.renderTable(this.documents, this.currentFilter, searchQuery);
        }
    }

    showDocumentInfo(docId) {
        if (this.documentDetails) {
            this.documentDetails.showDocumentDetails(docId);
        }
    }

    selectDocument(docId) {
        const doc = this.documents.find(d => d.id == docId);
        if (!doc) {
            alert('Documento no encontrado');
            return;
        }

        this.selectedDocument = doc;
        
        // Actualizar UI del chat
        const chatTitle = document.querySelector('#chatSection h3');
        if (chatTitle) {
            chatTitle.textContent = `Chat con Documento: ${doc.nombre_pdf || doc.filename || 'Sin nombre'}`;
        }
        
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            chatMessages.innerHTML = `
                <div class="system-message">
                    <i class="fas fa-robot"></i>
                    Documento seleccionado: <strong>${doc.nombre_pdf || doc.filename}</strong><br>
                    ¡Puedes hacer preguntas sobre este documento!
                </div>
            `;
        }
        
        // Activar el chat handler
        if (window.chatHandler) {
            window.chatHandler.enableChat(docId);
        }
        
        this.showMessage(`Documento "${doc.nombre_pdf || doc.filename}" seleccionado para chat`, 'success');
    }

    async deleteDocument(docId) {
        // Obtener información del documento para mostrar en el modal
        const doc = this.documents.find(d => d.id == docId);
        const docName = doc ? (doc.nombre_pdf || doc.filename || 'documento') : 'documento';
        
        // Mostrar modal de confirmación personalizado
        this.showConfirmModal(
            `¿Estás seguro de que quieres eliminar "${docName}"?`,
            async () => {
                try {
                    const response = await fetch(`/api/documents/${docId}`, {
                        method: 'DELETE'
                    });

                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }

                    this.showMessage('Documento eliminado correctamente', 'success');
                    
                    // Si el documento eliminado era el seleccionado, deshabilitar chat
                    if (this.selectedDocument && this.selectedDocument.id == docId) {
                        this.selectedDocument = null;
                        if (window.chatHandler) {
                            window.chatHandler.disableChat();
                        }
                    }
                    
                    this.loadDocuments(); // Recargar la lista
                } catch (error) {
                    console.error('Error deleting document:', error);
                    this.showMessage('Error al eliminar documento: ' + error.message, 'error');
                }
            }
        );
    }

    showConfirmModal(message, onConfirm) {
        const modal = document.getElementById('confirmModal');
        const messageEl = document.getElementById('confirmMessage');
        const cancelBtn = document.getElementById('confirmCancel');
        const deleteBtn = document.getElementById('confirmDelete');
        
        messageEl.textContent = message;
        modal.style.display = 'flex';
        
        // Limpiar eventos anteriores
        const newCancelBtn = cancelBtn.cloneNode(true);
        const newDeleteBtn = deleteBtn.cloneNode(true);
        cancelBtn.parentNode.replaceChild(newCancelBtn, cancelBtn);
        deleteBtn.parentNode.replaceChild(newDeleteBtn, deleteBtn);
        
        // Agregar nuevos eventos
        newCancelBtn.addEventListener('click', () => {
            modal.style.display = 'none';
        });
        
        newDeleteBtn.addEventListener('click', () => {
            modal.style.display = 'none';
            onConfirm();
        });
        
        // Cerrar con ESC o click fuera del modal
        const closeModal = (e) => {
            if (e.key === 'Escape' || e.target === modal) {
                modal.style.display = 'none';
                document.removeEventListener('keydown', closeModal);
                modal.removeEventListener('click', closeModal);
            }
        };
        
        document.addEventListener('keydown', closeModal);
        modal.addEventListener('click', closeModal);
    }

    showMessage(message, type = 'info') {
        const container = document.getElementById('messageContainer');
        
        // Crear elemento de mensaje
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        // Iconos según el tipo
        const icons = {
            success: '✅',
            error: '❌',
            info: 'ℹ️'
        };
        
        messageDiv.innerHTML = `
            <div class="message-content">
                <span class="message-icon">${icons[type] || icons.info}</span>
                <span class="message-text">${message}</span>
            </div>
            <button class="message-close" onclick="this.parentElement.remove()">×</button>
        `;
        
        container.appendChild(messageDiv);
        
        // Auto-remover después de 5 segundos
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.style.opacity = '0';
                messageDiv.style.transform = 'translateX(100%)';
                setTimeout(() => messageDiv.remove(), 300);
            }
        }, 5000);
    }
}