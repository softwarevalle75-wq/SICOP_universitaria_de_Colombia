// ===== TABLE RENDERER MODULE =====

export class TableRenderer {
    constructor(pdfHandler) {
        this.pdfHandler = pdfHandler;
    }

    renderTable(documents, currentFilter = 'todos', searchQuery = '') {
        const tbody = document.querySelector('#documentsTable tbody');
        if (!tbody) return;

        // Filtrar documentos
        let filteredDocs = documents;
        
        // Aplicar filtro de estado
        if (currentFilter !== 'todos') {
            filteredDocs = filteredDocs.filter(doc => 
                doc.estado_procesamiento === currentFilter
            );
        }
        
        // Aplicar búsqueda
        if (searchQuery.trim()) {
            const query = searchQuery.toLowerCase();
            filteredDocs = filteredDocs.filter(doc => 
                (doc.nombre_pdf || '').toLowerCase().includes(query) ||
                (doc.filename || '').toLowerCase().includes(query) ||
                (doc.dominio_origen || '').toLowerCase().includes(query)
            );
        }

        // Limpiar tabla
        tbody.innerHTML = '';

        if (filteredDocs.length === 0) {
            this.showEmptyState();
            return;
        }

        // Renderizar filas
        filteredDocs.forEach(doc => {
            const row = document.createElement('tr');
            
            row.innerHTML = `
                <td>${this.escapeHtml(doc.nombre_pdf || doc.filename || 'Sin nombre')}</td>
                <td>${this.formatDate(doc.fecha_hora_recepcion)}</td>
                <td>
                    <span class="status-badge status-${doc.estado_procesamiento}">
                        ${this.getStatusText(doc.estado_procesamiento)}
                    </span>
                </td>
                <td>${this.formatFileSize(doc.tamano_archivo)}</td>
                <td>
                    <div class="action-buttons">
                        <button class="btn-action btn-info" onclick="pdfHandler.showDocumentInfo(${doc.id})" title="Ver información detallada">
                            📋
                        </button>
                        <button class="btn-action btn-select" onclick="pdfHandler.selectDocument(${doc.id})" title="Seleccionar para chat">
                            💬
                        </button>
                        ${doc.url_google_drive ? `<button class="btn-action btn-drive" onclick="window.open('${doc.url_google_drive}', '_blank')" title="Abrir PDF en Google Drive">
                            📁
                        </button>` : ''}
                        <button class="btn-action btn-delete" onclick="pdfHandler.deleteDocument(${doc.id})" title="Eliminar">
                            🗑️
                        </button>
                    </div>
                </td>
            `;
            
            tbody.appendChild(row);
        });
    }

    showEmptyState() {
        const tbody = document.querySelector('#documentsTable tbody');
        if (!tbody) return;
        
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center py-4">
                    <div class="empty-state">
                        <div style="font-size: 3rem; margin-bottom: 1rem;">📄</div>
                        <h5>No hay documentos disponibles</h5>
                        <p style="color: #6c757d;">Los documentos que subas aparecerán aquí</p>
                    </div>
                </td>
            </tr>
        `;
    }

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

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatDate(dateString) {
        if (!dateString) return 'N/A';
        return new Date(dateString).toLocaleDateString('es-ES');
    }

    formatFileSize(bytes) {
        if (!bytes) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}