document.addEventListener("DOMContentLoaded", () => {
  const STORAGE_KEY = "cart.v1";

  const cartItemsContainer = document.getElementById("cart-items");
  const cartEmptyMessage = document.getElementById("cart-empty");
  const cartTotalElement = document.getElementById("cart-total");
  const payButton = document.getElementById("cart-pay");

  const currency = new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR" });
  const formatCurrency = (amount) => currency.format(amount);

  const loadCart = () => {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]"); }
    catch { return []; }
  };
  const saveCart = (cart) => localStorage.setItem(STORAGE_KEY, JSON.stringify(cart));

  const findItem = (cart, id) => cart.find((item) => item.id === id);
  const calculateTotal = (cart) => cart.reduce((sum, item) => sum + item.price * item.quantity, 0);

  let cart = loadCart();

  const renderCart = () => {
    if (!cartItemsContainer || !cartEmptyMessage || !cartTotalElement) return;

    if (cart.length === 0) {
      cartItemsContainer.innerHTML = "";
      cartEmptyMessage.style.display = "";
      cartTotalElement.textContent = formatCurrency(0);
      return;
    }
    cartEmptyMessage.style.display = "none";

    const html = cart.map((item) => {
      const lineTotal = item.price * item.quantity;
      return `
        <div class="cart-item" style="display:flex; align-items:center; gap:8px; padding:8px 0; border-bottom:1px solid #f3f3f3">
          <img src="${item.image || ""}" alt="${item.title || ""}" style="width:48px; height:48px; object-fit:cover; border-radius:6px; background:#fafafa" />
          <div style="flex:1">
            <div style="font-weight:600">${item.title}</div>
            <div style="color:#666">${formatCurrency(item.price)}</div>
          </div>
          <div style="display:flex; align-items:center; gap:6px">
            <button class="quantity-decrease" data-id="${item.id}" title="Diminuer">-</button>
            <input type="number" class="quantity-input" data-id="${item.id}" min="1" value="${item.quantity}" style="width:56px; text-align:center" />
            <button class="quantity-increase" data-id="${item.id}" title="Augmenter">+</button>
          </div>
          <div style="min-width: 90px; text-align:right">${formatCurrency(lineTotal)}</div>
          <button class="remove-from-cart" data-id="${item.id}">Supprimer</button>
        </div>
      `;
    }).join("");

    cartItemsContainer.innerHTML = html;
    cartTotalElement.textContent = formatCurrency(calculateTotal(cart));
  };

  const addItem = ({ id, title, price, image, quantity = 1 }) => {
    const existing = findItem(cart, id);
    if (existing) existing.quantity += quantity;
    else cart.push({ id, title, price, image, quantity });
    saveCart(cart);
    renderCart();
  };

  const removeItem = (id) => {
    cart = cart.filter((item) => item.id !== id);
    saveCart(cart);
    renderCart();
  };

  const updateQuantity = (id, quantity) => {
    const q = Math.max(1, parseInt(quantity, 10) || 1);
    const item = findItem(cart, id);
    if (item) item.quantity = q;
    saveCart(cart);
    renderCart();
  };

  // Ajout depuis le catalogue
  document.addEventListener("click", (event) => {
    const addButton = event.target.closest(".btn-add-to-cart");
    if (addButton) {
      const id = addButton.dataset.id;
      if (!id) return;
      const title = addButton.dataset.title || "Article";
      const price = parseFloat(addButton.dataset.price || "0");
      const image = addButton.dataset.image || "";
      addItem({ id, title, price, image, quantity: 1 });
      return;
    }

    // Incrément, décrément, suppression
    const inc = event.target.closest(".quantity-increase");
    const dec = event.target.closest(".quantity-decrease");
    const del = event.target.closest(".remove-from-cart");

    if (inc) {
      const id = inc.dataset.id;
      const item = findItem(cart, id);
      if (item) updateQuantity(id, item.quantity + 1);
      return;
    }
    if (dec) {
      const id = dec.dataset.id;
      const item = findItem(cart, id);
      if (item) updateQuantity(id, Math.max(1, item.quantity - 1));
      return;
    }
    if (del) {
      removeItem(del.dataset.id);
      return;
    }
  });

  // Changement direct via input nombre
  if (cartItemsContainer) {
    cartItemsContainer.addEventListener("change", (event) => {
      const input = event.target.closest(".quantity-input");
      if (!input) return;
      updateQuantity(input.dataset.id, input.value);
    });
  }

  // Placeholder paiement
  if (payButton) {
    payButton.addEventListener("click", async () => {
      const cart = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
      if (!Array.isArray(cart) || cart.length === 0) {
        alert("Votre panier est vide.");
        return;
      }
      const items = cart.map((it) => ({ id: it.id, quantity: it.quantity }));
      try {
        const res = await fetch("/payments/checkout", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ items }),
        });
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();
        if (data.url) window.location.href = data.url;
        else alert("URL de paiement introuvable.");
      } catch (e) {
        alert("Erreur de paiement: " + e);
      }
    });
  }

  renderCart();
});