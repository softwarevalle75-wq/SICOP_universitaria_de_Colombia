// ===== CHAT HANDLER - SISTEMA SGDEA =====

class ChatHandler {
    constructor() {
        this.currentDocumentId = null;
    }

    init() {
        this.bindEvents();
    }

    bindEvents() {
        // Botón enviar
        const sendButton = document.getElementById('sendChatBtn');
        if (sendButton) {
            sendButton.addEventListener('click', () => this.sendMessage());
        }

        // Enter en input
        const chatInput = document.getElementById('chatInput');
        if (chatInput) {
            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.sendMessage();
                }
            });
        }
    }

    enableChat(documentId) {
        this.currentDocumentId = documentId;
        
        const chatInput = document.getElementById('chatInput');
        const sendButton = document.getElementById('sendChatBtn');
        const chatStatus = document.getElementById('chat-status');
        
        if (chatInput) {
            chatInput.disabled = false;
            chatInput.placeholder = 'Escribe tu pregunta sobre el documento...';
        }
        
        if (sendButton) {
            sendButton.disabled = false;
        }
        
        if (chatStatus) {
            chatStatus.innerHTML = '<p>Documento seleccionado. ¡Puedes hacer preguntas!</p>';
        }
        
        this.clearMessages();
    }

    disableChat() {
        this.currentDocumentId = null;
        
        const chatInput = document.getElementById('chatInput');
        const sendButton = document.getElementById('sendChatBtn');
        const chatStatus = document.getElementById('chat-status');
        
        if (chatInput) {
            chatInput.disabled = true;
            chatInput.placeholder = 'Selecciona un documento para hacer preguntas...';
            chatInput.value = '';
        }
        
        if (sendButton) {
            sendButton.disabled = true;
        }
        
        if (chatStatus) {
            chatStatus.innerHTML = '<p>Selecciona un documento de la tabla para comenzar a chatear</p>';
        }
        
        this.clearMessages();
    }

    async sendMessage() {
        const chatInput = document.getElementById('chatInput');
        const message = chatInput.value.trim();
        
        if (!message) {
            alert('Escribe una pregunta');
            return;
        }
        
        if (!this.currentDocumentId) {
            alert('Selecciona un documento primero');
            return;
        }
        
        // Mostrar mensaje del usuario
        this.addMessage(message, 'user');
        
        // Limpiar input y deshabilitar
        chatInput.value = '';
        this.setLoading(true);
        
        try {
            const response = await fetch('/chat/message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    document_id: this.currentDocumentId
                })
            });
            
            const data = await response.json();
            
            if (response.ok && data.response) {
                this.addMessage(data.response, 'assistant');
            } else {
                this.addMessage('Error: ' + (data.error || 'No se pudo procesar la pregunta'), 'assistant');
            }
        } catch (error) {
            this.addMessage('Error de conexión', 'assistant');
        } finally {
            this.setLoading(false);
        }
    }

    addMessage(text, sender) {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        messageDiv.textContent = text;
        
        chatMessages.appendChild(messageDiv);
        
        // Scroll suave al último mensaje
        this.scrollToBottom();
    }
    
    scrollToBottom() {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;
        
        // Usar requestAnimationFrame para asegurar que el DOM se haya actualizado
        requestAnimationFrame(() => {
            chatMessages.scrollTo({
                top: chatMessages.scrollHeight,
                behavior: 'smooth'
            });
        });
    }

    clearMessages() {
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            chatMessages.innerHTML = '';
        }
    }

    setLoading(loading) {
        const sendButton = document.getElementById('sendChatBtn');
        const chatInput = document.getElementById('chatInput');
        
        if (sendButton) {
            sendButton.disabled = loading;
            sendButton.textContent = loading ? 'Enviando...' : 'Enviar';
        }
        
        if (chatInput) {
            chatInput.disabled = loading;
        }
    }
}

// Exportar para uso global
window.ChatHandler = ChatHandler;