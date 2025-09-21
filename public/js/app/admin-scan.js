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
      alert('Clé utilisateur requise: scannez le QR du billet (format user_key.token).');
      return;
    }

    const fd = new FormData(form);
    const body = new URLSearchParams();
    for (const [k, v] of fd.entries()) body.append(k, v);

    fetchAndReplace('/admin/scan/validate', {
      method: 'POST',
      headers: {
        'X-Requested-With': 'fetch',
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body
    }).then(() => {
      const input = document.getElementById('token-input');
      if (input) {
        input.value = '';
        input.focus();
      }
      lastToken = null;

      setTimeout(() => {
        stopCamera();
        fetchAndReplace('/admin/scan', { method: 'GET', headers: { 'X-Requested-With': 'fetch' } })
          .then(() => startCamera());
      }, 3000);
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
