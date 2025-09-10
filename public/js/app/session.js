"use strict";
(function () {
    function ensureToastEl() {
        let el = document.getElementById('toast-success');
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
        const el = ensureToastEl();
        el.textContent = message;
        el.classList.add('show');
        setTimeout(() => {
            el.classList.remove('show');
        }, 4000);
    }
    function cleanUrlIfConfirmed(params) {
        const isConfirmed = params.get('confirmed') === '1';
        if (!isConfirmed)
            return;
        const cleanUrl = window.location.origin + window.location.pathname;
        history.replaceState({}, '', cleanUrl);
    }
    document.addEventListener('DOMContentLoaded', () => {
        const params = new URLSearchParams(window.location.search);
        // Succès si ?payment=success (config par défaut) OU si Stripe appose redirect_status=succeeded
        const isSuccess = params.get('payment') === 'success' || params.get('redirect_status') === 'succeeded';
        if (!isSuccess)
            return;
        // Afficher le toast une seule fois PAR session Stripe
        const sessionId = params.get('session_id') || '';
        const storageKey = sessionId ? `payment_success_toast_shown:${sessionId}` : 'payment_success_toast_shown';
        if (!sessionStorage.getItem(storageKey)) {
            showToast('Paiement réussi');
            sessionStorage.setItem(storageKey, '1');
        }
        // Nettoyer l’URL si confirmed=1 est présent pour éviter la répétition au rechargement
        cleanUrlIfConfirmed(params);
    });
})();
