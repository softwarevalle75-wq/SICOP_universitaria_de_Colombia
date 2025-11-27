// ===== PDF HANDLER MAIN =====

import { PdfHandler } from './modules/PdfHandler.js';
import { FileHandler } from './modules/FileHandler.js';
import { TableRenderer } from './modules/TableRenderer.js';
import { DocumentDetails } from './modules/DocumentDetails.js';

// Variables globales
let pdfHandler;
let fileHandler;
let tableRenderer;
let documentDetails;

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    pdfHandler = new PdfHandler();
    tableRenderer = new TableRenderer();
    documentDetails = new DocumentDetails(pdfHandler);
    fileHandler = new FileHandler(pdfHandler);

    // Configurar referencias cruzadas
    pdfHandler.setTableRenderer(tableRenderer);
    pdfHandler.setDocumentDetails(documentDetails);
    pdfHandler.fileHandler = fileHandler;

    // Hacer disponibles globalmente para onclick handlers
    window.pdfHandler = pdfHandler;
    window.fileHandler = fileHandler;
    window.documentDetails = documentDetails;
});