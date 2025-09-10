(function () {
    function ensureToastEl() {
        var el = document.getElementById('toast-success');
        if (!el) {
            el = document.createElement('div');
            el.id = 'toast-success';
            el.setAttribute('role', 'status');
            el.setAttribute('aria-live', 'polite');
            document.body.appendChild(el);
        }
        return el;
    }
    function showToast(message) {
        var el = ensureToastEl();
        el.textContent = message;
        el.classList.add('show');
        setTimeout(function () {
            el.classList.remove('show');
        }, 4000);
    }
    function cleanUrlIfConfirmed(params) {
        var isConfirmed = params.get('confirmed') === '1';
        if (!isConfirmed)
            return;
        var cleanUrl = window.location.origin + window.location.pathname;
        history.replaceState({}, '', cleanUrl);
    }
    document.addEventListener('DOMContentLoaded', function () {
        var params = new URLSearchParams(window.location.search);
        var isSuccess = params.get('payment') === 'success';
        if (!isSuccess)
            return;
        // Afficher le toast une seule fois par session de navigation
        if (!sessionStorage.getItem('payment_success_toast_shown')) {
            showToast('Paiement réussi');
            sessionStorage.setItem('payment_success_toast_shown', '1');
        }
        // Nettoyer l’URL si confirmed=1 est présent pour éviter la répétition au rechargement
        cleanUrlIfConfirmed(params);
    });
})();
