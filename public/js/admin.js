(async () => {
  function showMsg(el, text, ok=false){
    if(!el) return;
    el.style.display = 'block';
    el.textContent = text;
    el.classList.remove('ok','err');
    el.classList.add(ok ? 'ok' : 'err');
  }
  function clearMsg(el){ if(!el) return; el.style.display='none'; el.textContent=''; el.classList.remove('ok','err'); }

  async function getMe(){
    const res = await fetch('/me', { credentials: 'include' });
    if(!res.ok) throw new Error('Non authentifié');
    return await res.json();
  }

  const msg = document.getElementById('admin-msg');
  const userBox = document.getElementById('admin-user');
  const btnLogout = document.getElementById('btn-logout');
  const btnSession = document.getElementById('btn-go-session');

  try{
    const me = await getMe();
    if(me.role !== 'admin'){
      showMsg(msg, "Accès refusé: vous n'avez pas les droits administrateur.");
      window.location.href = '/session';
      return;
    }
    if(userBox){
      userBox.innerHTML = `
        <div style="display:flex;align-items:center;gap:12px">
          <div style="width:40px;height:40px;border-radius:9999px;background:rgba(255,255,255,0.06);display:grid;place-items:center;font-weight:700;color:#d1fae5">${(me.email||'A')[0].toUpperCase()}</div>
          <div>
            <div style="font-weight:700">${me.email}</div>
            <div style="font-size:12px;color:#9ca3af">ID: ${me.id}</div>
            <div style="font-size:12px;color:#9ca3af">Rôle: ${me.role}</div>
          </div>
        </div>`;
    }
  }catch(e){
    showMsg(msg, 'Session expirée ou invalide.');
    window.location.href = '/';
    return;
  }

  // Actions
  if(btnLogout){ btnLogout.addEventListener('click', async () => { try{ await fetch('/logout', { method:'POST', credentials:'include' }); }catch{} window.location.href='/'; }); }
  if(btnSession){ btnSession.addEventListener('click', () => window.location.href='/session'); }

  const btnRefresh = document.getElementById('btn-refresh');
  if(btnRefresh){ btnRefresh.addEventListener('click', async () => {
    clearMsg(msg);
    try{
      const me = await getMe();
      showMsg(msg, 'Actualisé.', true);
    }catch{ showMsg(msg, 'Erreur de rafraîchissement.'); }
  }); }
})();