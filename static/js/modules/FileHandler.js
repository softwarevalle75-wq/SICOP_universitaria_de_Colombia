// ===== FILE HANDLER MODULE =====

export class FileHandler {
    constructor(pdfHandler) {
        this.pdfHandler = pdfHandler;
        this.initializeUploadButton();
    }

    initializeUploadButton() {
        const uploadToggle = document.getElementById('uploadToggle');
        const fileInput = document.getElementById('pdfFile');
        
        if (uploadToggle && fileInput) {
            uploadToggle.addEventListener('click', () => {
                fileInput.click();
            });
            
            fileInput.addEventListener('change', (event) => {
                this.handleFileSelect(event);
            });
        }
    }

    handleFileSelect(event) {
        const file = event.target.files[0];
        if (!file) {
            return;
        }

        if (file.type !== 'application/pdf') {
            this.showMessage('Solo se permiten archivos PDF', 'error');
            event.target.value = '';
            return;
        }

        this.pdfHandler.selectedFile = file;
        this.uploadFile(file);
    }

    async uploadFile(file) {
        if (this.pdfHandler.isUploading) return;
        
        try {
            this.pdfHandler.isUploading = true;
            this.showMessage('Subiendo archivo...', 'info');
            
            const formData = new FormData();
            formData.append('pdf_file', file);
            
            const response = await fetch('/api/upload-pdf', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showMessage('Archivo subido exitosamente', 'success');
                // Limpiar el input
                document.getElementById('pdfFile').value = '';
                this.pdfHandler.selectedFile = null;
                
                // Actualizar la tabla de documentos
                if (window.pdfHandler) {
                    window.pdfHandler.loadDocuments();
                }
            } else {
                this.showMessage(result.error || 'Error al subir el archivo', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showMessage('Error de conexión', 'error');
        } finally {
            this.pdfHandler.isUploading = false;
        }
    }

    showFileInfo(file) {
        const fileInfo = document.getElementById('fileInfo');
        
        if (fileInfo) {
            fileInfo.innerHTML = `
                <div style="display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem; background: #f8f9fa; border-radius: 4px; margin: 0.5rem 0;">
                    <span>📄</span>
                    <div style="flex: 1; font-size: 0.9rem;">
                        <div style="font-weight: 500;">${file.name}</div>
                        <div style="color: #6c757d; font-size: 0.8rem;">${this.formatFileSize(file.size)}</div>
                    </div>
                    <button type="button" id="removeFile" style="background: none; border: none; color: #dc3545; cursor: pointer; font-size: 1.2rem;">✕</button>
                    <button type="submit" style="background: #495057; color: white; border: none; padding: 0.4rem 0.8rem; border-radius: 4px; font-size: 0.8rem; cursor: pointer;">Subir</button>
                </div>
            `;
            
            // Re-bind remove button event
            const removeBtn = document.getElementById('removeFile');
            if (removeBtn) {
                removeBtn.addEventListener('click', () => this.removeFile());
            }
        }
    }

    removeFile() {
        const fileInput = document.getElementById('pdfFile');
        const fileInfo = document.getElementById('fileInfo');
        const progressContainer = document.getElementById('progressContainer');
        const uploadMessage = document.getElementById('uploadMessage');

        if (fileInput) fileInput.value = '';
        if (fileInfo) fileInfo.innerHTML = '';
        if (progressContainer) progressContainer.classList.remove('show');
        if (uploadMessage) uploadMessage.classList.remove('show');
        
        this.pdfHandler.selectedFile = null;
    }

    async handleUpload(event) {
        if (this.pdfHandler.isUploading) return;
        
        event.preventDefault();
        
        if (!this.pdfHandler.selectedFile) {
            this.showMessage('Selecciona un archivo PDF', 'error');
            return;
        }
        
        try {
            this.pdfHandler.isUploading = true;
            this.showProgress(true);
            
            const formData = new FormData();
            formData.append('pdf_file', this.pdfHandler.selectedFile);
            
            const response = await fetch('/api/upload-pdf', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showMessage('Documento subido exitosamente', 'success');
                this.removeFile();
                this.pdfHandler.loadDocuments();
            } else {
                this.showMessage('Error: ' + (data.error || 'No se pudo subir el archivo'), 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showMessage('Error de conexión', 'error');
        } finally {
            this.pdfHandler.isUploading = false;
            this.showProgress(false);
        }
    }

    showProgress(show) {
        const progressContainer = document.getElementById('progressContainer');
        const submitContainer = document.getElementById('submitContainer');
        
        if (show) {
            if (progressContainer) progressContainer.classList.add('show');
            if (submitContainer) submitContainer.classList.remove('show');
        } else {
            if (progressContainer) progressContainer.classList.remove('show');
            if (submitContainer) submitContainer.classList.add('show');
        }
    }

    showMessage(text, type) {
        // Crear el elemento de mensaje si no existe
        let messageEl = document.getElementById('uploadMessage');
        if (!messageEl) {
            messageEl = document.createElement('div');
            messageEl.id = 'uploadMessage';
            document.body.appendChild(messageEl);
        }
        
        messageEl.textContent = text;
        messageEl.className = `upload-message-compact ${type} show`;
        
        setTimeout(() => {
            messageEl.classList.remove('show');
        }, 4000);
    }

    formatFileSize(bytes) {
        if (!bytes) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}