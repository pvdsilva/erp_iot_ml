// Sistema de proteção de autenticação - Versão Silenciosa
document.addEventListener('DOMContentLoaded', function() {
    // Proteção contra navegação via botão voltar
    window.history.pushState(null, null, window.location.href);
    window.onpopstate = function() {
        window.history.go(1);
    };
    
    // Proteção contra recarregamento de página
    document.addEventListener('keydown', function(e) {
        // Bloquear F5, Ctrl+R, Ctrl+Shift+R silenciosamente
        if (e.key === 'F5' || (e.ctrlKey && e.key === 'r') || (e.ctrlKey && e.shiftKey && e.key === 'R')) {
            e.preventDefault();
        }
    });
});

// Prevenir clique direito
document.addEventListener('contextmenu', function(e) {
    e.preventDefault();
});

// Prevenir arrastar imagens
document.addEventListener('dragstart', function(e) {
    if (e.target.tagName === 'IMG') {
        e.preventDefault();
    }
});

// Prevenir seleção de texto (exceto em inputs)
document.addEventListener('selectstart', function(e) {
    if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA' && e.target.contentEditable !== 'true') {
        e.preventDefault();
    }
});
