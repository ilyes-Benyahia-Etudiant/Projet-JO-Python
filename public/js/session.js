async function loadConfig(){
  try{
    const res = await fetch('/config');
    if(!res.ok) throw new Error('Impossible de charger la config');
    return await res.json();
  }catch(e){ console.error(e); return null; }
}

(async () => {
  const cfg = await loadConfig();
  if(!cfg){ alert('Erreur de configuration côté serveur.'); return; }

  // Helpers
  function showMsg(el, text, ok=false){
    el.style.display = 'block';
    el.textContent = text;
    el.classList.remove('ok','err');
    el.classList.add(ok ? 'ok' : 'err');
  }
  function clearMsg(el){ el.style.display = 'none'; el.textContent = ''; el.classList.remove('ok','err'); }

  async function getMe(){
    const res = await fetch('/me', { credentials: 'include' });
    if(!res.ok) throw new Error('Non authentifié');
    return await res.json();
  }
  // Sécurité: attacher les gestionnaires seulement si les éléments existent
  (function(){
    const byId = (id) => document.getElementById(id);
    const on = (id, evt, fn) => { const el = byId(id); if (el) el.addEventListener(evt, fn); };
  
    async function loadProfile(){
      try{
        const res = await fetch('/me', { credentials: 'include' });
        if(!res.ok) throw new Error('Non authentifié');
        const data = await res.json();
        const nameEl = byId('user-name');
        const emailEl = byId('user-email');
        if(nameEl) nameEl.textContent = data.id;
        if(emailEl) emailEl.textContent = data.email;
        const roleEl = byId('user-role');
        if(roleEl) roleEl.textContent = data.role || 'user';
      }catch(e){
        // si non authentifié, retourner à la page d'accueil
        window.location.href = '/';
      }
    }
  
    async function doLogout(){
      try{ await fetch('/logout', { method: 'POST', credentials: 'include' }); }catch{}
      window.location.href = '/';
    }
  
    on('btn-profile', 'click', async () => {
      alert('Mon profil: à compléter si nécessaire.');
    });
    on('btn-logout', 'click', doLogout);
    on('btn-back-login', 'click', () => window.location.href = '/');
  
    // init
    loadProfile();
  })();

  // Charger et afficher les infos utilisateur
  const details = document.getElementById('user-details');
  const msg = document.getElementById('session-msg');
  let me = null;
  
  try{
    me = await getMe();
    details.innerHTML = `
      <div style="display:flex;align-items:center;gap:12px">
        <div style="width:40px;height:40px;border-radius:9999px;background:rgba(255,255,255,0.06);display:grid;place-items:center;font-weight:700;color:#d1fae5">${(me.email||'U')[0].toUpperCase()}</div>
        <div>
          <div style="font-weight:700">${me.email}</div>
          <div style="font-size:12px;color:#9ca3af">ID: ${me.id}</div>
          <div style="font-size:12px;color:#9ca3af">Rôle: ${me.role || 'user'}</div>
        </div>
      </div>`;
  
  // Redirection admin côté frontend supprimée: désormais gérée côté backend au login
  // if (me && me.role === 'admin') {
  //   window.location.href = '/admin';
  //   return;
  // }
  }catch(e){
    details.innerHTML = '<div class="user-placeholder">Session invalide. Veuillez vous reconnecter.</div>';
    showMsg(msg, 'Session expirée ou invalide. Redirection...', false);
    setTimeout(() => { window.location.href = '/'; }, 1500);
    return; // Arrêter l'exécution si pas d'utilisateur
  }

  // Boutons - maintenant avec accès à 'me'
  const btnProfile = document.getElementById('btn-profile');
  if (btnProfile) {
    btnProfile.addEventListener('click', async () => {
      alert(`ID: ${me.id}\nEmail: ${me.email}\nRôle: ${me.role || 'user'}`);
    });
  }

  const btnAdmin = document.getElementById('btn-admin');
  const btnLogout = document.getElementById('logout');
  const btnBackLogin = document.getElementById('btn-back-login');
  
  // Afficher le bouton Admin seulement si rôle admin
  if (btnAdmin) { 
    btnAdmin.style.display = me.role === 'admin' ? 'inline-flex' : 'none'; 
  }
  
  // Gestionnaire de déconnexion
  if (btnLogout) { 
    btnLogout.addEventListener('click', async () => { 
      try { 
        await fetch('/logout', { method: 'POST', credentials: 'include' }); 
      } catch {} 
      window.location.href = '/'; 
    }); 
  }
  
  // Bouton retour
  if (btnBackLogin) {
    btnBackLogin.addEventListener('click', () => window.location.href = '/');
  }
})();