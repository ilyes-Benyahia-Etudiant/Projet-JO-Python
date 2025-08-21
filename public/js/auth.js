document.addEventListener('DOMContentLoaded', () => {
  const modal = document.getElementById('modal-auth');
  const bg = document.getElementById('modal-auth-bg');
  const closeBtn = document.getElementById('modal-auth-close');
  const btnsOpen = [document.querySelector('.btn-login'), document.getElementById('open-login')].filter(Boolean);

  const openModal = (e) => { if(e) e.preventDefault(); if(modal){ modal.classList.add('open'); } };
  const closeModal = (e) => { if(e) e.preventDefault(); if(modal){ modal.classList.remove('open'); } };

  btnsOpen.forEach(b => b.addEventListener('click', openModal));
  if(bg) bg.addEventListener('click', closeModal);
  if(closeBtn) closeBtn.addEventListener('click', closeModal);
  document.addEventListener('keydown', (e) => { if(e.key === 'Escape') closeModal(); });

  // Tabs Connexion / Inscription
  const tabLogin = document.getElementById('tab-login');
  const tabRegister = document.getElementById('tab-register');
  const loginForm = document.getElementById('login-form');
  const registerForm = document.getElementById('register-form');
  function activateTab(which){
    if(which === 'login'){
      if(loginForm) loginForm.style.display = '';
      if(registerForm) registerForm.style.display = 'none';
      tabLogin && tabLogin.classList.add('active');
      tabRegister && tabRegister.classList.remove('active');
    }else{
      if(loginForm) loginForm.style.display = 'none';
      if(registerForm) registerForm.style.display = '';
      tabRegister && tabRegister.classList.add('active');
      tabLogin && tabLogin.classList.remove('active');
    }
  }
  if(tabLogin) tabLogin.addEventListener('click', () => activateTab('login'));
  if(tabRegister) tabRegister.addEventListener('click', () => activateTab('register'));
  const switchToRegister = document.getElementById('switch-to-register');
  if(switchToRegister){ switchToRegister.addEventListener('click', (e) => { e.preventDefault(); activateTab('register'); }); }

  // Helpers de messages
  function showMsg(el, text, ok=false){ if(!el) return; el.style.display='block'; el.textContent=text; el.classList.remove('ok','err'); el.classList.add(ok?'ok':'err'); }
  function clearMsg(el){ if(!el) return; el.style.display='none'; el.textContent=''; el.classList.remove('ok','err'); }

  // Connexion: POST vers /auth/login (form-urlencoded) pour bénéficier de la redirection serveur
  const loginMsg = document.getElementById('modal-login-msg');
  if(loginForm){
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      clearMsg(loginMsg);
      const email = document.getElementById('modal-login-email')?.value.trim();
      const password = document.getElementById('modal-login-password')?.value;
      if(!email || !password){ return showMsg(loginMsg, 'Email et mot de passe requis'); }
      try{
        const body = new URLSearchParams({ email, password });
        const res = await fetch('/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          credentials: 'include',
          body
        });
        if(res.redirected){
          window.location.href = res.url; // /session ou /admin
          return;
        }
        let data = {};
        try{ data = await res.json(); }catch{}
        if(!res.ok){ throw new Error(data.message || 'Identifiants invalides'); }
        window.location.href = '/session';
      }catch(err){ showMsg(loginMsg, err.message || 'Erreur lors de la connexion'); }
    });
  }

  // Inscription: POST JSON -> afficher message et éventuellement rediriger
  const signupMsg = document.getElementById('modal-signup-msg');
  if(registerForm){
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      clearMsg(signupMsg);
      const email = document.getElementById('modal-signup-email')?.value.trim();
      const p1 = document.getElementById('modal-signup-password')?.value;
      const p2 = document.getElementById('modal-signup-password2')?.value;
      if(!email || !p1 || !p2){ return showMsg(signupMsg, 'Veuillez remplir tous les champs'); }
      if(p1 !== p2){ return showMsg(signupMsg, 'Les mots de passe ne correspondent pas'); }
      try{
        const res = await fetch('/auth/signup', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ email, password: p1 })
        });
        const data = await res.json().catch(() => ({}));
        if(!res.ok){ throw new Error(data.message || 'Erreur lors de l\'inscription'); }
        showMsg(signupMsg, data.message || 'Inscription réussie. Vérifiez vos emails.', true);
        // Si une session est créée côté serveur, rediriger vers /session après un court délai
        setTimeout(() => { window.location.href = '/session'; }, 800);
      }catch(err){ showMsg(signupMsg, err.message || 'Erreur lors de l\'inscription'); }
    });
  }

  // Mot de passe oublié
  const forgot = document.getElementById('modal-forgot');
  if(forgot){
    forgot.addEventListener('click', async (e) => {
      e.preventDefault();
      clearMsg(loginMsg);
      const email = document.getElementById('modal-login-email')?.value.trim();
      if(!email){ return showMsg(loginMsg, 'Saisissez votre email pour recevoir un lien de réinitialisation'); }
      try{
        const res = await fetch('/auth/forgot', {
          method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email })
        });
        const data = await res.json().catch(() => ({}));
        if(!res.ok){ throw new Error(data.message || 'Erreur lors de la demande de réinitialisation'); }
        showMsg(loginMsg, data.message || 'Email de réinitialisation envoyé si l\'utilisateur existe.', true);
      }catch(err){ showMsg(loginMsg, err.message || 'Erreur lors de la demande de réinitialisation'); }
    });
  }

  // Renvoi de l'email de confirmation (Inscription)
  const resendConfirm = document.getElementById('modal-resend-confirm');
  if(resendConfirm){
    resendConfirm.addEventListener('click', async (e) => {
      e.preventDefault();
      clearMsg(signupMsg);
      const email = document.getElementById('modal-signup-email')?.value.trim();
      if(!email){ return showMsg(signupMsg, 'Veuillez saisir votre email (Inscription) pour renvoyer la confirmation.'); }

      const originalText = resendConfirm.textContent;
      const startCooldown = (seconds = 20) => {
        let remaining = seconds;
        resendConfirm.style.pointerEvents = 'none';
        resendConfirm.style.opacity = '0.6';
        resendConfirm.textContent = `Renvoyer (${remaining}s)`;
        const timer = setInterval(() => {
          remaining -= 1;
          resendConfirm.textContent = `Renvoyer (${remaining}s)`;
          if(remaining <= 0){
            clearInterval(timer);
            resendConfirm.style.pointerEvents = 'auto';
            resendConfirm.style.opacity = '1';
            resendConfirm.textContent = originalText;
          }
        }, 1000);
      };

      try{
        const res = await fetch('/auth/resend', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ email, type: 'signup' })
        });
        const data = await res.json().catch(() => ({}));
        if(!res.ok){ throw new Error(data.message || 'Erreur lors du renvoi de la confirmation'); }
        showMsg(signupMsg, data.message || 'Email renvoyé (si le compte existe).', true);
        startCooldown();
      }catch(err){
        showMsg(signupMsg, err.message || 'Erreur lors du renvoi de la confirmation');
        startCooldown();
      }
    });
  }
});