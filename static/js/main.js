// ===== MAIN.JS - SISTEMA SGDEA =====

// Variables globales
window.chatHandler = null;

// Cargar módulos
function loadModule(src, callback) {
    const script = document.createElement('script');
    script.src = src;
    script.onload = callback;
    document.head.appendChild(script);
}

// Inicializar aplicación
function init() {
    // Cargar chat handler
    loadModule('/static/js/chatHandler.js', () => {
        if (window.ChatHandler) {
            window.chatHandler = new window.ChatHandler();
            window.chatHandler.init();
        }
    });
    
    // El PDF handler ahora se carga como módulo ES6 desde el HTML
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', init);