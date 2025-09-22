(() => {
  'use strict';

  const video = document.getElementById('qr-video');
  const canvas = document.getElementById('qr-canvas');
  const startBtn = document.getElementById('start-camera');
  const stopBtn = document.getElementById('stop-camera');
  const camContainer = document.getElementById('camera-container');
  const tokenInput = document.getElementById('token-input');

  let stream = null;
  let rafId = null;
  let lastToken = null;
  let lastScanTs = 0;

  function extractToken(text) {
    // Si le QR est une URL /admin/scan?token=..., on extrait le token; sinon on considère le texte comme token
    try {
      const url = new URL(text, window.location.origin);
      const t = url.searchParams.get('token');
      if (t) return t;
    } catch (e) {}
    return text;
  }

  async function startCamera() {
    if (stream) return;
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: 'environment' } },
        audio: false
      });
      video.srcObject = stream;
      await video.play();
      camContainer.style.display = '';
      if (startBtn) startBtn.style.display = 'none';
      if (stopBtn) stopBtn.style.display = '';
      scanLoop();
    } catch (err) {
      alert('Impossible d’accéder à la caméra: ' + err);
    }
  }

  function stopCamera() {
    if (rafId) cancelAnimationFrame(rafId);
    rafId = null;
    if (stream) {
      stream.getTracks().forEach(t => t.stop());
      stream = null;
    }
    video.srcObject = null;
    camContainer.style.display = 'none';
    if (startBtn) startBtn.style.display = '';
    if (stopBtn) stopBtn.style.display = 'none';
  }

  // Petit toast en overlay (vert/jaune/rouge)
  function showToast(message, type = 'info') {
    let el = document.getElementById('scan-toast');
    if (!el) {
      el = document.createElement('div');
      el.id = 'scan-toast';
      el.style.position = 'fixed';
      el.style.left = '50%';
      el.style.top = '16px';
      el.style.transform = 'translateX(-50%)';
      el.style.zIndex = '9999';
      el.style.padding = '10px 14px';
      el.style.borderRadius = '6px';
      el.style.color = '#fff';
      el.style.fontWeight = '600';
      el.style.boxShadow = '0 2px 8px rgba(0,0,0,0.25)';
      el.style.transition = 'opacity .2s ease';
      el.style.opacity = '0.95';
      document.body.appendChild(el);
    }

    const colors = {
      success: '#16a34a', // vert
      warning: '#ca8a04', // jaune
      error: '#dc2626',   // rouge
      info: '#2563eb'     // bleu
    };
    el.style.background = colors[type] || colors.info;
    el.textContent = message;

    clearTimeout(el._hideTimer);
    el.style.display = 'block';
    el.style.opacity = '0.95';
    el._hideTimer = setTimeout(() => {
      el.style.opacity = '0';
      setTimeout(() => (el.style.display = 'none'), 250);
    }, 1800);
  }

  function scanLoop() {
    if (!stream) return;
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
    if (qr && qr.data) {
      const token = extractToken(qr.data);
      if (token && (token !== lastToken || now - lastScanTs > 3000)) {
        lastToken = token;
        lastScanTs = now;
        if (tokenInput) tokenInput.value = token;
        handleSearchSubmit(new Event('submit', { cancelable: true }));
        if (navigator.vibrate) navigator.vibrate(100);
      }
    }
    rafId = requestAnimationFrame(scanLoop);
  }

  // petit son de validation
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

  async function fetchAndReplace(url, opts) {
    try {
      const res = await fetch(url, Object.assign({ credentials: 'same-origin' }, opts || {}));
      const html = await res.text();
      const doc = new DOMParser().parseFromString(html, 'text/html');
      const newCard = doc.getElementById('scan-card');
      const oldCard = document.getElementById('scan-card');
      if (newCard && oldCard) {
        oldCard.replaceWith(newCard);
        // Ré-attache les écouteurs et met à jour les éléments dynamiques
        requeryDom();
      }
      return { newCard };
    } catch (err) {
      console.error('fetchAndReplace error:', err);
      alert('Erreur réseau pendant la validation. Réessayez.');
      return { newCard: null };
    }
  }

  // Helper: lire un cookie par nom (pour récupérer csrf_token)
  function getCookie(name) {
    const parts = ('; ' + document.cookie).split('; ' + name + '=');
    if (parts.length < 2) return null;
    return decodeURIComponent(parts.pop().split(';').shift());
  }

  // Appel direct à l’API de validation (JSON) sans PRG/redirection
  async function apiValidateCompositeToken(composite) {
    const payload = { token: composite };
    try {
      const headers = {
        'Content-Type': 'application/json',
        'X-Requested-With': 'fetch'
      };
      // Injecter le header CSRF depuis le cookie
      const csrf =
        getCookie('csrf_token') ||
        getCookie('XSRF-TOKEN') ||
        getCookie('CSRF-TOKEN');
      if (csrf) {
        headers['X-CSRF-Token'] = csrf;
      }

      const res = await fetch('/api/v1/validation/scan', {
        method: 'POST',
        credentials: 'same-origin',
        headers,
        body: JSON.stringify(payload)
      });

      const isJson = (res.headers.get('content-type') || '').includes('application/json');
      const data = isJson ? await res.json() : {};

      if (res.ok) {
        // Côté API “ok” signifie validé
        const s = String(data.status || '').toLowerCase();
        if (s === 'ok' || s === 'validated') {
          return { kind: 'validated', data };
        }
        if (s === 'already_validated') {
          return { kind: 'already_validated', data };
        }
        return { kind: 'validated', data }; // fallback
      }

      // Erreurs 4xx/404: message dans data.detail ou data.message
      const msg = data.detail || data.message || 'Validation impossible';
      return { kind: 'error', message: msg };
    } catch (err) {
      return { kind: 'error', message: 'Erreur réseau' };
    }
  }

  function sanitizeTokenInput(value) {
    return (value || '').trim().replace(/^["']|["']$/g, '');
  }

  function handleValidateSubmit(e) {
    e.preventDefault();
    const form = e.target;

    const tokenField = form.querySelector('input[name="token"]');
    let tokenVal = tokenField ? (tokenField.value || '') : '';
    tokenVal = sanitizeTokenInput(tokenVal);

    const userKeyInput = document.getElementById('user-key-input');
    let userKeyVal = userKeyInput ? (userKeyInput.value || '') : '';
    userKeyVal = sanitizeTokenInput(userKeyVal);

    // Compose automatiquement si token brut + user_key fournie
    if (tokenVal && tokenVal.indexOf('.') === -1 && userKeyVal) {
      tokenField.value = `${userKeyVal}.${tokenVal}`;
    } else {
      tokenField.value = tokenVal;
    }

    const finalToken = sanitizeTokenInput(tokenField.value || '');
    if (!finalToken || finalToken.indexOf('.') === -1) {
      showToast('Clé utilisateur requise: format user_key.token', 'error');
      return;
    }

    // Appel direct API, pas de rechargement, pas d’arrêt caméra
    apiValidateCompositeToken(finalToken).then((result) => {
      if (result.kind === 'validated') {
        showToast('Validé', 'success');
        try { playSuccessBeep(); } catch (_) {}
      } else if (result.kind === 'already_validated') {
        showToast('Déjà validé', 'warning');
      } else {
        showToast(result.message || 'Validation impossible', 'error');
      }

      // Reset minimal du champ, garder la caméra active et focus pour enchaîner
      const input = document.getElementById('token-input');
      if (input) {
        input.value = '';
        input.focus();
      }
      lastToken = null;
    }).catch(() => {
      showToast('Erreur réseau', 'error');
    });
  }

  function handleSearchSubmit(e) {
    e.preventDefault();
    const input = document.getElementById('token-input');
    const raw = (input && input.value) || '';
    const token = sanitizeTokenInput(raw);
    if (!token) return;
    const url = '/admin/scan?token=' + encodeURIComponent(token);
    fetchAndReplace(url, { method: 'GET', headers: { 'X-Requested-With': 'fetch' } });
  }

  function attachDynamicHandlers() {
    // Form GET (recherche token)
    const tokenForm = document.querySelector('form[action="/admin/scan"][method="get"]');
    if (tokenForm) tokenForm.addEventListener('submit', handleSearchSubmit);

    // Form POST (validation)
    document.querySelectorAll('form[action="/admin/scan/validate"]').forEach(f => {
      f.addEventListener('submit', handleValidateSubmit);
    });

    // Boutons caméra
    const start = document.getElementById('start-camera');
    const stop = document.getElementById('stop-camera');
    if (start) start.addEventListener('click', startCamera);
    if (stop) stop.addEventListener('click', stopCamera);

    // Focus rapide sur champ token
    const input = document.getElementById('token-input');
    if (input) input.focus();
  }

  function requeryDom() {
    try {
      if (typeof attachDynamicHandlers === 'function') {
        attachDynamicHandlers();
      }
    } catch (e) {
      console.warn('requeryDom: attachDynamicHandlers() a échoué ou est introuvable', e);
    }
  }

  // Bind initial
  attachDynamicHandlers();
  if (startBtn) startBtn.addEventListener('click', startCamera);
  if (stopBtn) stopBtn.addEventListener('click', stopCamera);
  window.addEventListener('beforeunload', stopCamera);
})();
