async function loadConfig(){
  try{
    const res = await fetch('/config');
    if(!res.ok) throw new Error('Impossible de charger la config');
    return await res.json();
  }catch(e){
    console.error(e);
    return null;
  }
}

(async () => {
  const cfg = await loadConfig();
  if(!cfg){
    alert('Erreur de configuration côté serveur.');
    return;
  }
  const SUPABASE_URL = cfg.supabase_url;
  const SUPABASE_ANON_KEY = cfg.supabase_anon_key;
  
  // Créer un fetch wrapper qui injecte systématiquement l'en-tête apikey
  const injectApiKeyFetch = (url, options = {}) => {
    const headers = Object.assign({}, options.headers || {}, {
      'apikey': SUPABASE_ANON_KEY,
    });
    return fetch(url, { ...options, headers });
  };
  
  // Créer le client Supabase (garde pour certaines fonctionnalités comme la détection de PASSWORD_RECOVERY)
  const client = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
    auth: {
      autoRefreshToken: true,
      persistSession: true,
    },
    global: {
      fetch: injectApiKeyFetch,
      headers: {
        'apikey': SUPABASE_ANON_KEY,
      }
    }
  });

  // Helper pour poser la session côté serveur (cookie HttpOnly)
  async function setServerSession(access){
    try{
      await fetch('/session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ access_token: access })
      });
    }catch{}
  }

  // Si on vient d'un lien de récupération, récupérer le token dans le hash et poser un cookie serveur
  const hash = window.location.hash || '';
  if(hash.includes('access_token')){
    const params = new URLSearchParams(hash.replace(/^#/, ''));
    const at = params.get('access_token');
    const type = params.get('type');
    if(at && type === 'recovery'){
      await setServerSession(at);
    }
  }

  // Détecter le flux de récupération de mot de passe
  client.auth.onAuthStateChange((event, session) => {
    if(event === 'PASSWORD_RECOVERY'){
      const rec = document.getElementById('password-recovery');
      if(rec) rec.style.display = 'block';
      const msg = document.getElementById('recovery-msg');
      if(msg){ msg.style.display='block'; msg.classList.remove('err'); msg.classList.add('ok'); msg.textContent = 'Lien de réinitialisation validé. Choisissez un nouveau mot de passe.'; }
    }
  });

  // Helper sécurisé pour attacher des événements
  const bind = (id, evt, handler) => {
    const el = document.getElementById(id);
    if (el) el.addEventListener(evt, handler);
  };

  // UI Tabs
  const tabs = document.querySelectorAll('.tab');
  const panels = { login: document.getElementById('login'), signup: document.getElementById('signup') };
  tabs.forEach(t => {
    if (t) {
      t.addEventListener('click', () => {
        tabs.forEach(x => x.classList.remove('active'));
        t.classList.add('active');
        const sel = t.dataset.tab;
        Object.keys(panels).forEach(k => {
          if (panels[k]) panels[k].style.display = (k === sel) ? 'block' : 'none';
        });
      });
    }
  });

  function showMsg(el, text, ok=false){
    if(!el) return;
    el.style.display = 'block';
    el.textContent = text;
    el.classList.remove('ok','err');
    el.classList.add(ok ? 'ok' : 'err');
  }
  function clearMsg(el){ 
    if(!el) return;
    el.style.display = 'none'; 
    el.textContent = ''; 
    el.classList.remove('ok','err'); 
  }

  // =================== HELPERS POUR APPELS API PYTHON ===================
  
  async function callAuthAPI(endpoint, data = null) {
    const options = {
      method: 'POST', // Always POST for auth endpoints
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include' // Important pour les cookies HttpOnly
    };
    if (data !== null) {
      options.body = JSON.stringify(data);
    }
    
    const response = await fetch(endpoint, options);
    let result = {};
    try {
      result = await response.json();
    } catch (_) {
      result = {};
    }
    
    if (!response.ok) {
      const err = new Error(result.message || 'Erreur réseau');
      err.status = response.status;
      throw err;
    }
    
    return result;
  }

  async function fetchMe(){
    try{
      const res = await fetch('/me', { credentials: 'include' });
      if(!res.ok) throw new Error('Non authentifié');
      const data = await res.json();
      alert(`ID: ${data.id}\nEmail: ${data.email}\nRôle: ${data.role}`);
    }catch(e){ alert(e.message || 'Erreur /me'); }
  }

  async function doLogout(){
    try{
      await fetch('/logout', { method: 'POST', credentials: 'include' });
      alert('Déconnecté.');
    }catch(e){ alert(e.message || 'Erreur logout'); }
  }

  // =================== GESTIONNAIRES D'ÉVÉNEMENTS AVEC NOUVEAU SYSTÈME ===================
  
  bind('btn-me', 'click', fetchMe);
  bind('btn-logout', 'click', doLogout);
  
  bind('btn-forgot', 'click', async () => {
    const email = document.getElementById('login-email')?.value.trim();
    const msg = document.getElementById('login-msg');
    clearMsg(msg);
    if(!email){ return showMsg(msg, 'Veuillez saisir votre email pour réinitialiser votre mot de passe.'); }
    
    try{
      const result = await callAuthAPI('/auth/forgot', { email });
      showMsg(msg, result.message, true);
    }catch(e){ 
      showMsg(msg, e.message || 'Erreur lors de la demande de réinitialisation.'); 
    }
  });
  
  // (Connexion via formulaire HTML, pas de gestionnaire JS ici)

  bind('btn-signup', 'click', async () => {
    const email = document.getElementById('signup-email')?.value.trim();
    const password = document.getElementById('signup-password')?.value;
    const password2 = document.getElementById('signup-password2')?.value;
    const msg = document.getElementById('signup-msg');
    clearMsg(msg);
    if(!email || !password || !password2){ return showMsg(msg, 'Veuillez remplir tous les champs.'); }
    if(password !== password2){ return showMsg(msg, 'Les mots de passe ne correspondent pas.'); }
    
    try{
      const result = await callAuthAPI('/auth/signup', { email, password });
      showMsg(msg, result.message, true);
    }catch(e){ 
      showMsg(msg, e.message || 'Erreur lors de l\'inscription.'); 
    }
  });

  // Renvoyer l'email de confirmation avec anti-spam
  bind('btn-resend-confirm', 'click', async (e) => {
    const btn = e.currentTarget;
    const email = (document.getElementById('signup-email')?.value.trim() || document.getElementById('login-email')?.value.trim());
    const activeTab = document.querySelector('.tab.active')?.dataset.tab;
    const msg = activeTab === 'signup' ? document.getElementById('signup-msg') : document.getElementById('login-msg');
    clearMsg(msg);
    if(!email){ return showMsg(msg, "Veuillez saisir votre email (onglet Inscription) pour renvoyer la confirmation."); }

    const cooldown = 20; // secondes
    let remaining = cooldown;
    const originalText = btn.textContent;

    const startCooldown = () => {
      btn.disabled = true; btn.style.opacity = 0.7;
      const timer = setInterval(() => {
        remaining -= 1;
        btn.textContent = `Renvoyer (${remaining}s)`;
        if (remaining <= 0) {
          clearInterval(timer);
          btn.disabled = false; btn.style.opacity = 1;
          btn.textContent = originalText;
        }
      }, 1000);
    };
    
    try{
      const result = await callAuthAPI('/auth/resend', { email, type: 'signup' });
      showMsg(msg, result.message, true);
      startCooldown();
    }catch(e){ 
      if (e.status === 429) {
        showMsg(msg, 'Vous avez demandé trop de renvois, réessayez plus tard.');
      } else {
        showMsg(msg, e.message || 'Erreur lors du renvoi de l\'email.'); 
      }
      startCooldown();
    }
  });

  // Mettre à jour le mot de passe après récupération
  bind('btn-update-password', 'click', async () => {
    const p1 = document.getElementById('new-password')?.value;
    const p2 = document.getElementById('new-password2')?.value;
    const msg = document.getElementById('recovery-msg');
    clearMsg(msg);
    if(!p1 || !p2){ return showMsg(msg, 'Veuillez remplir les deux champs.'); }
    if(p1 !== p2){ return showMsg(msg, 'Les mots de passe ne correspondent pas.'); }
    
    try{
      const result = await callAuthAPI('/auth/update-password', { password: p1 });
      showMsg(msg, result.message, true);
    }catch(e){ 
      showMsg(msg, e.message || 'Erreur lors de la mise à jour du mot de passe.'); 
    }
  });
})();