/**
 * Module front de la page Admin Scan.
 * Objectif:
 * - Activer la caméra et scanner des QR codes (lib jsQR) pour extraire un token.
 * - Pré-remplir et soumettre le formulaire de recherche /admin/scan?token=... (GET).
 * - Envoyer une validation (POST /admin/scan/validate) avec protection CSRF.
 * - Afficher des feedbacks UI (toast, bannière de statut) et masquer automatiquement.
 * Dépendance:
 * - jsQR: doit être chargé globalement (par le template admin-scan.html).
 * Intégration back:
 * - GET /admin/scan (recherche billet) et POST /admin/scan/validate (validation).
 * - CSRF: cookie 'csrf_token' et header 'X-CSRF-Token' (middleware côté backend).
 */
(() => {
  'use strict';

  /*** Sélecteurs DOM (mis à jour dynamiquement) ***/
  let els = {};

  /*** Variables d’état ***/
  let stream = null;
  let rafId = null;
  let lastToken = null;
  let lastScanTs = 0;
  let hideTimer = null; // Timer unique pour le masquage

  /*** Helpers génériques ***/
  /**
   * Récupère la valeur d'un cookie par son nom.
   * @param {string} name - Nom du cookie.
   * @returns {string|null} Valeur décodée ou null si absent.
   */
  const getCookie = (name) => {
    const parts = ('; ' + document.cookie).split('; ' + name + '=');
    return parts.length < 2 ? null : decodeURIComponent(parts.pop().split(';').shift());
  };

  /*** UI utils ***/
  /**
   * Affiche un toast éphémère en haut de page.
   * @param {string} message - Contenu du message.
   * @param {'success'|'warning'|'error'|'info'} [type='info'] - Type de toast pour la couleur.
   */
  function showToast(message, type = 'info') {
    let el = document.getElementById('scan-toast');
    if (!el) {
      el = document.createElement('div');
      el.id = 'scan-toast';
      Object.assign(el.style, {
        position: 'fixed', left: '50%', top: '16px', transform: 'translateX(-50%)',
        zIndex: 9999, padding: '10px 14px', borderRadius: '6px', color: '#fff',
        fontWeight: '600', boxShadow: '0 2px 8px rgba(0,0,0,0.25)', transition: 'opacity .2s ease',
      });
      document.body.appendChild(el);
    }
    const colors = { success: '#16a34a', warning: '#ca8a04', error: '#dc2626', info: '#2563eb' };
    el.style.background = colors[type] || colors.info;
    el.textContent = message;
    clearTimeout(el._hideTimer);
    el.style.display = 'block';
    el.style.opacity = '0.95';
    el._hideTimer = setTimeout(() => {
      el.style.opacity = '0';
      setTimeout(() => (el.style.display = 'none'), 250);
    }, 2200);
  }

  function playSuccessBeep() {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.value = 880;
      osc.connect(gain);
      gain.connect(ctx.destination);
      gain.gain.setValueAtTime(0.0001, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.08, ctx.currentTime + 0.01);
      osc.start();
      setTimeout(() => {
        gain.gain.exponentialRampToValueAtTime(0.00001, ctx.currentTime + 0.15);
        osc.stop(ctx.currentTime + 0.16);
        ctx.close();
      }, 150);
    } catch (_) {}
  }

  // Ajout: mise en cache des références DOM
  function ensureDomRefs() {
    els.video = els.video || document.getElementById('qr-video');
    els.canvas = els.canvas || document.getElementById('qr-canvas');
    els.camContainer = els.camContainer || document.getElementById('camera-container');
    els.startBtn = els.startBtn || document.getElementById('start-camera');
    els.stopBtn = els.stopBtn || document.getElementById('stop-camera');
    els.tokenInput = els.tokenInput || document.getElementById('token-input');

    if (els.video) {
      els.video.setAttribute('playsinline', '');
      // Sur iOS, muter la vidéo aide l’autoplay après interaction
      els.video.muted = true;
    }
  }

  /*** Caméra ***/
  async function startCamera() {
    if (stream) return;

    ensureDomRefs();

    if (!els.video || !els.camContainer) {
      alert('Éléments vidéo/caméra introuvables dans la page.');
      return;
    }

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      alert('Votre navigateur ne supporte pas getUserMedia. Utilisez HTTPS et un navigateur récent.');
      return;
    }

    try {
      // Contrainte préférée: caméra arrière
      const preferred = { video: { facingMode: { ideal: 'environment' } }, audio: false };
      try {
        stream = await navigator.mediaDevices.getUserMedia(preferred);
      } catch (e1) {
        // Fallback large si la contrainte échoue
        stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      }

      els.video.srcObject = stream;
      try { await els.video.play(); } catch (_) {}

      els.camContainer.style.display = '';
      if (els.startBtn) els.startBtn.style.display = 'none';
      if (els.stopBtn) els.stopBtn.style.display = '';
      scanLoop();
    } catch (err) {
      let msg = 'Impossible d’accéder à la caméra.';
      if (location.protocol !== 'https:' && location.hostname !== 'localhost') {
        msg += ' Cette fonctionnalité nécessite une origine sécurisée (HTTPS).';
      }
      if (err?.name === 'NotAllowedError') {
        msg += ' Permission refusée. Vérifiez les autorisations caméra du navigateur.';
      }
      if (err?.name === 'NotFoundError') {
        msg += ' Aucune caméra détectée sur l’appareil.';
      }
      alert(msg);
    }
  }

  function stopCamera() {
    if (rafId) cancelAnimationFrame(rafId);
    rafId = null;
    if (stream) {
      stream.getTracks().forEach((t) => t.stop());
      stream = null;
    }
    if (els.video) els.video.srcObject = null;
    if (els.camContainer) els.camContainer.style.display = 'none';
    if (els.startBtn) els.startBtn.style.display = '';
    if (els.stopBtn) els.stopBtn.style.display = 'none';
  }

  function scanLoop() {
    if (!stream) return;
    const { video, canvas, tokenInput } = els;
    const w = video.videoWidth, h = video.videoHeight;
    if (!w || !h) {
      rafId = requestAnimationFrame(scanLoop);
      return;
    }
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, w, h);
    const imageData = ctx.getImageData(0, 0, w, h);
    const qr = jsQR(imageData.data, w, h, { inversionAttempts: 'dontInvert' });
    const now = Date.now();
    if (qr?.data) {
      const token = extractToken(qr.data);
      if (token && (token !== lastToken || now - lastScanTs > 3000)) {
        lastToken = token;
        lastScanTs = now;
        if (tokenInput) {
          tokenInput.value = token;
          // Déclenche la soumission du formulaire de recherche (plus robuste)
          const form = tokenInput.form;
          if (form) {
            if (typeof form.requestSubmit === 'function') {
              form.requestSubmit();
            } else {
              form.submit();
            }
          }
        }
        if (navigator.vibrate) navigator.vibrate(100);
      }
    }
    rafId = requestAnimationFrame(scanLoop);
  }

  /*** Extraction token ***/
  function extractToken(text) {
    try {
      const url = new URL(text, window.location.origin);
      return url.searchParams.get('token') || text;
    } catch (_) {
      return text;
    }
  }

  /*** Logique de la page ***/

  // Masque les infos et réinitialise le champ après un délai
  const scheduleHideAndReset = (delayMs = 2000) => {
    clearTimeout(window.hideTimer);
    window.hideTimer = setTimeout(() => {
      const UIElements = ['#scan-status-banner', '#ticket-details', '#validate-form'];
      UIElements.forEach(sel => {
        const el = document.querySelector(sel);
        if (el) el.style.display = 'none';
      });
      
      const tokenInput = document.getElementById('token-input');
      if (tokenInput) {
        tokenInput.value = '';
        tokenInput.focus();
      }
    }, delayMs);
  };

  // Gère la soumission du formulaire de validation via fetch
  const handleValidateSubmit = async (event) => {
    event.preventDefault();
    const form = event.target;
    const tokenInput = form.querySelector('input[name="token"]');
    const csrfInput = form.querySelector('input[name="csrf_token"]');
    try {
      const response = await fetch(form.action, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'Accept': 'application/json',
          'X-CSRF-Token': getCookie('csrf_token') || ''
        },
        body: new URLSearchParams({ token: tokenInput.value, csrf_token: csrfInput.value })
      });

      let result = {};
      try {
        result = await response.json();
      } catch (_) {
        // Si la réponse n'est pas JSON, on ne casse pas l'UX
        result = {};
      }

      if (response.ok) {
        showToast('Billet Validé avec succès', 'success');
        playSuccessBeep?.();
        scheduleHideAndReset(2000);
      } else {
        showToast(result.message || 'La validation a échoué.', 'error');
      }
    } catch (error) {
      showToast('Erreur de communication.', 'error');
    }
  };

  // Auto-hide quand le statut est "Déjà validé"
  function applyAutoHideForAlreadyValidated() {
    const banner = document.getElementById('scan-status-banner');
    const status = banner?.dataset?.status;
    if (status === 'AlreadyValidated') {
      scheduleHideAndReset(2000);
    }
  }

  /*** Init ***/
  /**
   * Point d’entrée du module:
   * - Lie les events (start/stop caméra, submit validation).
   * - Focus sur le champ token et soumet automatiquement si pré-rempli (cas: lien avec token).
   * - Applique l’auto-hide si nécessaire et arrête la caméra au déchargement.
   */
  function init() {
    ensureDomRefs();

    els.startBtn?.addEventListener('click', startCamera);
    els.stopBtn?.addEventListener('click', stopCamera);

    els.tokenInput?.focus();

    // Soumission auto si le champ token est déjà pré-rempli au chargement
    const tokenForm = document.getElementById('token-form');
    if (tokenForm && els.tokenInput && els.tokenInput.value && els.tokenInput.value.trim().length > 0) {
      if (typeof tokenForm.requestSubmit === 'function') {
        tokenForm.requestSubmit();
      } else {
        tokenForm.submit();
      }
    }

    const validateForm = document.getElementById('validate-form');
    validateForm?.addEventListener('submit', handleValidateSubmit);

    applyAutoHideForAlreadyValidated();

    window.addEventListener('beforeunload', stopCamera);
  }

  document.addEventListener('DOMContentLoaded', init);
})();
