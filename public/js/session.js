async function loadConfig(){
  try{
    const res = await fetch('/config');
    if(!res.ok) throw new Error('Impossible de charger la config');
    return await res.json();
  }catch(e){ console.warn('[config]', e); return null; }
}

(async () => {
  const cfg = await loadConfig();
  if(!cfg){ console.warn('Config indisponible, on continue côté front.'); }

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
        // Non authentifié: garder la page visible et afficher un message discret
        console.warn('Utilisateur non authentifié, interface accessible en mode limité.');
      }
    }
  
    async function doLogout(){
      try{ await fetch('/logout', { method: 'POST', credentials: 'include' }); }catch{}
      // Après déconnexion, on montre Connexion et masque Déconnexion
      document.querySelectorAll('.btn-login').forEach(el => el.style.display = 'inline-block');
      document.querySelectorAll('.btn-logout').forEach(el => el.style.display = 'none');
      window.location.href = '/';
    }
  
    on('btn-profile', 'click', async () => {
      alert('Mon profil: à compléter si nécessaire.');
    });
    // Gérer tous les boutons de déconnexion (navbar + section)
    document.querySelectorAll('.btn-logout').forEach(el => {
      el.addEventListener('click', doLogout);
    });
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
    details && (details.innerHTML = `
      <div style="display:flex;align-items:center;gap:12px">
        <div style="width:40px;height:40px;border-radius:9999px;background:rgba(255,255,255,0.06);display:grid;place-items:center;font-weight:700;color:#d1fae5">${(me.email||'U')[0].toUpperCase()}</div>
        <div>
          <div style="font-weight:700">${me.email}</div>
          <div style="font-size:12px;color:#9ca3af">ID: ${me.id}</div>
          <div style="font-size:12px;color:#9ca3af">Rôle: ${me.role || 'user'}</div>
        </div>
      </div>`);

    // Toggle navbar buttons: hide Connexion, show Déconnexion
    document.querySelectorAll('.btn-login').forEach(el => el.style.display = 'none');
    document.querySelectorAll('.btn-logout').forEach(el => el.style.display = 'inline-flex');
  
  // Redirection admin côté frontend supprimée
  }catch(e){
    if (details) {
      details.innerHTML = '<div class="user-placeholder">Vous n\'êtes pas connecté.</div>';
    }
    showMsg(msg, 'Connectez-vous pour accéder à votre espace.', false);
    // Laisser la section visible pour permettre l'accès à la modale des billets même si l'utilisateur n'est pas connecté
    // const sessionSection = document.querySelector('.session-section');
    // if (sessionSection) sessionSection.style.display = 'none';
    // const modal = document.getElementById('modal-auth');
    // if (modal) modal.classList.add('open');
    // Non connecté: afficher Connexion et masquer Déconnexion
    document.querySelectorAll('.btn-login').forEach(el => el.style.display = 'inline-block');
    document.querySelectorAll('.btn-logout').forEach(el => el.style.display = 'none');
    return;
  }

  // Boutons - maintenant avec accès à 'me'
  const btnProfile = document.getElementById('btn-profile');
  if (btnProfile) {
    btnProfile.addEventListener('click', async () => {
      alert(`ID: ${me.id}\nEmail: ${me.email}\nRôle: ${me.role || 'user'}`);
    });
  }

  const btnAdmin = document.getElementById('btn-admin');
  const btnBackLogin = document.getElementById('btn-back-login');
  
  // Afficher le bouton Admin seulement si rôle admin
  if (btnAdmin) { 
    btnAdmin.style.display = me.role === 'admin' ? 'inline-flex' : 'none'; 
  }
  
  // Bouton retour
  if (btnBackLogin) {
    btnBackLogin.addEventListener('click', () => window.location.href = '/');
  }
})();

// Mini système de panier côté front
const CART_KEY = 'jo_cart_v1';
const cart = {
  items: [],
  load(){
    try{ this.items = JSON.parse(localStorage.getItem(CART_KEY)||'[]'); }catch{ this.items=[]; }
  },
  save(){ localStorage.setItem(CART_KEY, JSON.stringify(this.items)); },
  count(){ return this.items.reduce((n,i)=>n+i.qty,0); },
  add(item){
    const idx = this.items.findIndex(it => it.id===item.id);
    if(idx>-1){ this.items[idx].qty += item.qty||1; }
    else { this.items.push({...item, qty: item.qty||1}); }
    this.save(); this.updateBadge();
  },
  remove(id){ this.items = this.items.filter(i=>i.id!==id); this.save(); this.updateBadge(); },
  clear(){ this.items=[]; this.save(); this.updateBadge(); },
  updateBadge(){
    const badge = document.getElementById('cart-count');
    if(badge) badge.textContent = String(this.count());
  }
};
cart.load();

const PRICE_MAP = { 'Offre Solo': 50, 'Offre Duo': 90, 'Offre Familiale': 160 };
cart.total = function(){ return this.items.reduce((s,i)=> s + (i.price||0) * (i.qty||1), 0); };

function renderCart(){
  const wrap = document.getElementById('cart-items');
  const totalEl = document.getElementById('cart-total');
  if(!wrap || !totalEl) return;
  if(cart.items.length === 0){
    wrap.innerHTML = '<div class="empty text-gray-600">Votre panier est vide.</div>';
    totalEl.textContent = '0€';
    return;
  }
  wrap.innerHTML = cart.items.map(i=>`
    <div class="cart-item" data-id="${i.id}">
      <div class="cart-item-left">
        <img class="cart-item-thumb" src="${i.img || '/static/images/olympic games.jpg'}" alt="${i.title}">
        <div class="cart-item-info">
          <div class="title">${i.title}</div>
          <div class="desc">${i.desc || ''}</div>
          <div class="price">${(i.price||0)}€</div>
        </div>
      </div>
      <div class="cart-item-actions">
        <button class="qty-btn dec" data-action="dec" aria-label="Diminuer">-</button>
        <span class="qty">${i.qty}</span>
        <button class="qty-btn inc" data-action="inc" aria-label="Augmenter">+</button>
        <button class="remove-btn" data-action="remove" aria-label="Supprimer">&times;</button>
      </div>
    </div>`).join('');
  totalEl.textContent = cart.total().toFixed(2) + '€';
}

function openCartModal(){
  const modal = document.getElementById('modal-cart');
  if(!modal) return;
  modal.classList.add('open');
  modal.setAttribute('aria-hidden','false');
  renderCart();
}
function closeCartModal(){
  const modal = document.getElementById('modal-cart');
  if(!modal) return;
  modal.classList.remove('open');
  modal.setAttribute('aria-hidden','true');
}

function bindCartModalEvents(){
  const bg = document.getElementById('modal-cart-bg');
  const closeBtn = document.getElementById('modal-cart-close');
  const itemsWrap = document.getElementById('cart-items');
  const btnClear = document.getElementById('cart-clear');
  const btnPay = document.getElementById('cart-pay');
  const btnContinue = document.getElementById('cart-continue');
  if(bg){ bg.addEventListener('click', closeCartModal); }
  if(closeBtn){ closeBtn.addEventListener('click', closeCartModal); }
  if(btnContinue){ btnContinue.addEventListener('click', closeCartModal); }
  if(itemsWrap){
    itemsWrap.addEventListener('click', (e)=>{
      const btn = e.target.closest('button');
      if(!btn) return;
      const action = btn.dataset.action;
      const row = btn.closest('.cart-item');
      if(!row) return;
      const id = row.dataset.id;
      const idx = cart.items.findIndex(i=>i.id===id);
      if(idx<0) return;
      if(action==='inc'){ cart.items[idx].qty += 1; }
      else if(action==='dec'){ cart.items[idx].qty = Math.max(1, (cart.items[idx].qty||1)-1); }
      else if(action==='remove'){ cart.items.splice(idx,1); }
      cart.save(); cart.updateBadge(); renderCart();
    });
  }
  if(btnClear){ btnClear.addEventListener('click', ()=>{ cart.clear(); renderCart(); }); }
  if(btnPay){ btnPay.addEventListener('click', ()=>{ alert('Paiement à venir (intégration backend).'); }); }
}

// === Tickets modal (Historique commandes & billets) ===
function loadTickets(){
  try{ return JSON.parse(localStorage.getItem('jo_orders')||'[]'); }catch{ return []; }
}
function makeQrSvg(id){
  return `
    <svg class="ticket-qr-svg" width="112" height="112" viewBox="0 0 64 72" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="QR pour commande ${id}">
      <rect width="64" height="64" fill="#fff"/>
      <rect x="2" y="2" width="20" height="20" fill="#000"/>
      <rect x="42" y="2" width="20" height="20" fill="#000"/>
      <rect x="2" y="42" width="20" height="20" fill="#000"/>
      <rect x="28" y="28" width="8" height="8" fill="#000"/>
      <rect x="38" y="38" width="6" height="6" fill="#000"/>
      <rect x="30" y="46" width="4" height="4" fill="#000"/>
      <rect x="46" y="30" width="4" height="4" fill="#000"/>
      <text x="32" y="70" text-anchor="middle" font-size="6" fill="#111">#${id}</text>
    </svg>`;
}
function renderTickets(){
  const listEl = document.getElementById('tickets-list');
  const emptyEl = document.getElementById('tickets-empty');
  if(!listEl || !emptyEl) return;
  const tickets = loadTickets();
  if(!tickets.length){
    listEl.innerHTML = '';
    emptyEl.style.display = 'block';
    return;
  }
  emptyEl.style.display = 'none';
  listEl.innerHTML = tickets.map(t => `
    <article class="ticket-card" data-order-id="${t.id}">
      <div class="ticket-info">
        <div class="title">Commande #${t.id}</div>
        <div class="type">Type de billet: <strong>${t.type || t.title || 'Billet'}</strong></div>
        ${t.date ? `<div class="date" style="color:#9ca3af">Le ${new Date(t.date).toLocaleString()}</div>` : ''}
      </div>
      <div class="ticket-right">
        <div class="ticket-qr">${makeQrSvg(t.id)}</div>
        <button class="btn btn-secondary btn-print" type="button" data-order-id="${t.id}">Imprimer le QR</button>
      </div>
    </article>`).join('');
}
function openTicketsModal(){
  const modal = document.getElementById('modal-tickets');
  if(!modal) return;
  renderTickets();
  modal.classList.add('open');
  modal.setAttribute('aria-hidden','false');
}
function closeTicketsModal(){
  const modal = document.getElementById('modal-tickets');
  if(!modal) return;
  modal.classList.remove('open');
  modal.setAttribute('aria-hidden','true');
}
function bindTicketsModalEvents(){
  const bg = document.getElementById('modal-tickets-bg');
  const btnClose = document.getElementById('modal-tickets-close');
  const btnBack = document.getElementById('tickets-back');
  const modal = document.getElementById('modal-tickets');
  if(bg){ bg.addEventListener('click', closeTicketsModal); }
  if(btnClose){ btnClose.addEventListener('click', closeTicketsModal); }
  if(btnBack){ btnBack.addEventListener('click', closeTicketsModal); }
  if(modal){
    modal.addEventListener('click', (e)=>{
      const btn = e.target.closest('.btn-print');
      if(!btn) return;
      const card = btn.closest('.ticket-card');
      const qr = card ? card.querySelector('.ticket-qr') : null;
      if(!qr) return;
      const w = window.open('', '_blank');
      if(!w) return;
      w.document.write(`<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>QR #${btn.dataset.orderId}</title><style>body{margin:0;padding:16px;display:grid;place-items:center;background:#fff;} .qr{width:256px;height:256px;display:grid;place-items:center;border:1px solid #ccc;border-radius:8px;padding:12px}</style></head><body><div class="qr">${qr.innerHTML}</div><script>window.onload=()=>{setTimeout(()=>{window.print();window.close();}, 100);};<\/script></body></html>`);
      w.document.close();
    });
  }
}

function wireCartButtons(){
  const btnCart = document.getElementById('btn-cart');
  if(btnCart){
    btnCart.addEventListener('click', openCartModal);
  }
  const btnMyTickets = document.getElementById('btn-my-tickets');
  if(btnMyTickets){
    btnMyTickets.addEventListener('click', openTicketsModal);
  }
}

// Adapter l’ajout au panier pour inclure un prix
let cartToastTimer;
function ensureCartToastEl(){
  let el = document.getElementById('cart-toast');
  if(!el){
    el = document.createElement('div');
    el.id = 'cart-toast';
    el.className = 'cart-toast';
    el.setAttribute('role','status');
    el.setAttribute('aria-live','polite');
    document.body.appendChild(el);
  }
  return el;
}
function showCartSuccess(title){
  const el = ensureCartToastEl();
  el.textContent = `${title} ajouté au panier`;
  el.classList.add('show');
  if (cartToastTimer) clearTimeout(cartToastTimer);
  cartToastTimer = setTimeout(()=>{ el.classList.remove('show'); }, 2500);
}
function bindOfferCards(){
  const offerCards = document.querySelectorAll('.events-section .event-card');
  offerCards.forEach((card, idx) => {
    const oldBtn = card.querySelector('.btn-login');
    const title = card.querySelector('h3')?.textContent?.trim() || `Offre ${idx+1}`;
    const price = PRICE_MAP[title] || 50;
    const imgEl = card.querySelector('.event-img');
    const descEl = card.querySelector('.event-content p');
    const img = imgEl ? imgEl.getAttribute('src') : '';
    const desc = descEl ? descEl.textContent.trim() : '';
    if(oldBtn){
      oldBtn.textContent = 'Ajouter au panier';
      oldBtn.classList.remove('btn-login');
      oldBtn.classList.add('btn', 'btn-accent', 'btn-add-to-cart');
      oldBtn.style.display = 'inline-block';
      oldBtn.setAttribute('role','button');
      oldBtn.addEventListener('click', (e)=>{
        e.preventDefault(); e.stopPropagation(); if (e.stopImmediatePropagation) e.stopImmediatePropagation();
        cart.add({ id: `offer-${idx+1}`, title, price, qty: 1, img, desc });
        showCartSuccess(title);
      }, true);
    }
  });
  cart.updateBadge();
}

if(document.readyState === 'loading'){
  document.addEventListener('DOMContentLoaded', () => { bindOfferCards(); wireCartButtons(); bindCartModalEvents(); bindTicketsModalEvents(); cart.updateBadge(); });
}else{
  bindOfferCards(); wireCartButtons(); bindCartModalEvents(); bindTicketsModalEvents(); cart.updateBadge();
}