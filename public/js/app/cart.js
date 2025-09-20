"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
document.addEventListener("DOMContentLoaded", () => {
    class Cart {
        constructor() {
            this.STORAGE_KEY = "cart.v1";
            this.cart = [];
            this.currency = new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR" });
            // Raccourcis DOM — initialisés une fois
            this.$ = {
                items: document.getElementById("cart-items"),
                empty: document.getElementById("cart-empty"),
                total: document.getElementById("cart-total"),
                payBtn: document.getElementById("cart-pay"),
                countBadges: [
                    document.getElementById("cart-count-pill"),
                    document.getElementById("cart-fab-badge"),
                ].filter(Boolean),
            };
            this.renderItem = (item) => {
                const lineTotal = item.price * item.quantity;
                return `
        <div class="cart-item">
          <div class="cart-item-icon" aria-hidden="true">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#555" stroke-width="1.8">
              <path d="M3 7a2 2 0 0 1 2-2h8l2 2h4a2 2 0 0 1 2 2v1.5a2.5 2.5 0 0 0 0 5V17a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1.5a2.5 2.5 0 0 0 0-5V7z"></path>
              <path d="M10 8v8"></path>
              <circle cx="10" cy="12" r="0.5"></circle>
            </svg>
          </div>
          <div class="cart-item-info">
            <div class="cart-item-title" title="${item.title}">${item.title}</div>
            ${item?.event ? `<div class="cart-item-event">${item.event.type || ""} • ${item.event.nom || ""} • ${item.event.date || ""}</div>` : ""}
            <div class="cart-item-price">${this.formatCurrency(item.price)}</div>
          </div>
          <div class="quantity-group">
            <button class="quantity-decrease" data-id="${item.id}" title="Diminuer">-</button>
            <input type="number" class="quantity-input" data-id="${item.id}" min="1" value="${item.quantity}" />
            <button class="quantity-increase" data-id="${item.id}" title="Augmenter">+</button>
          </div>
          <div class="cart-line-total">${this.formatCurrency(lineTotal)}</div>
          <button class="remove-from-cart" data-id="${item.id}" title="Retirer cet article" aria-label="Retirer cet article">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
              <polyline points="3 6 5 6 21 6"></polyline>
              <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"></path>
              <path d="M10 11v6"></path>
              <path d="M14 11v6"></path>
              <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"></path>
            </svg>
          </button>
        </div>`;
            };
            this.addItem = ({ id, title, price, quantity = 1, event }) => {
                console.log(`addItem appelée pour ID: ${id}, Titre: ${title}`);
                const existing = this.findItem(id);
                if (existing) {
                    existing.quantity += quantity || 1;
                    // Si un événement est fourni, on l’associe si absent
                    if (event && !existing.event) existing.event = event;
                    console.log("Article existant mis à jour");
                }
                else {
                    this.cart.push({
                        id,
                        title: title || "Article",
                        price: price || 0,
                        quantity: quantity || 1,
                        event: event || undefined,
                    });
                    console.log("Nouvel article ajouté au panier");
                }
                this.saveCart();
                this.render();
                this.showToast(`“${title || "Article"}” ajouté au panier`);
                // Publier un événement global pour que les pages (ex: billeterie) puissent réagir
                document.dispatchEvent(new CustomEvent("cart:itemAdded", {
                    detail: { id, title: title || "Article", count: this.countItems() }
                }));
                console.log("Fin de addItem – toast devrait être affiché");
            };
            this.cart = this.loadCart();
            // Ajout: hydrater les prix depuis le backend si nécessaire
            this.hydratePrices().catch(() => {});
            this.bindEvents();
            this.render();
        }
        // ===== GESTION DU PANIER =====
        loadCart() {
            try {
                const raw = localStorage.getItem(this.STORAGE_KEY) || "[]";
                return JSON.parse(raw);
            }
            catch (_a) {
                return [];
            }
        }
        saveCart() {
            localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.cart));
        }
        findItem(id) {
            return this.cart.find((item) => item.id === id);
        }
        calculateTotal() {
            return this.cart.reduce((sum, item) => sum + item.price * item.quantity, 0);
        }
        countItems() {
            return this.cart.reduce((sum, item) => sum + item.quantity, 0);
        }
        // ===== UI =====
        updateCartCountBadge() {
            const count = this.countItems();
            this.$.countBadges.forEach((badge) => {
                badge.textContent = String(count);
                badge.style.display = count > 0 ? "inline-flex" : "none";
                badge.setAttribute("aria-label", count > 0
                    ? `Articles dans le panier: ${count}`
                    : "Aucun article");
            });
        }
        render() {
            const { items, empty, total } = this.$;
            // Toujours mettre à jour la pastille, même si on n'a pas l'UI du panier (billeterie)
            this.updateCartCountBadge();
            if (!items || !empty || !total) return;

            if (this.cart.length === 0) {
                items.innerHTML = "";
                empty.style.display = "block";
                total.textContent = this.formatCurrency(0);
                return;
            }
            empty.style.display = "none";
            items.innerHTML = this.cart.map(this.renderItem).join("");
            total.textContent = this.formatCurrency(this.calculateTotal());
        }
        formatCurrency(amount) {
            return this.currency.format(amount);
        }
        // ===== TOAST — ✅ CORRIGÉ POUR AFFICHAGE GARANTI =====
        ensureToastEl() {
            console.log("ensureToastEl appelée – Vérification/création de l'élément toast");
            let el = document.getElementById("toast-success");
            if (!el) {
                console.log("Élément toast non trouvé, création d'un nouveau");
                el = document.createElement("div");
                el.id = "toast-success";
                el.setAttribute("role", "status");
                el.setAttribute("aria-live", "polite");
                document.body.appendChild(el);
            }
            else {
                console.log("Élément toast existant trouvé");
            }
            return el;
        }
        showToast(message) {
            console.log(`showToast appelée avec message: "${message}"`);
            const el = this.ensureToastEl();
            el.classList.remove("show");
            void el.offsetWidth; // relance la transition CSS
            el.textContent = message || "Article ajouté au panier";
            el.classList.add("show");
            console.log("Classe 'show' ajoutée au toast – il devrait s'afficher maintenant");
            window.setTimeout(() => {
                el.classList.remove("show");
                console.log("Classe 'show' retirée après 3s");
            }, 3000);
        }
        removeItem(id) {
            this.cart = this.cart.filter((item) => item.id !== id);
            this.saveCart();
            this.render();
        }
        updateQuantity(id, quantity) {
            const item = this.findItem(id);
            if (item) {
                item.quantity = Math.max(1, quantity);
                this.saveCart();
                this.render();
            }
        }
        clearCart() {
            this.cart = [];
            this.saveCart();
            this.render();
            this.closeDrawer();
        }
        // ===== ÉVÉNEMENTS — UN SEUL GESTIONNAIRE CENTRAL =====
        bindEvents() {
            var _a, _b;
            // Gestionnaire centralisé pour tout le document
            document.addEventListener("click", (e) => {
                const target = e.target;
                // Ajout depuis catalogue
                const addBtn = target.closest(".btn-add-to-cart");
                if (addBtn) {
                    const id = addBtn.dataset.id;
                    const title = addBtn.dataset.title || "Article";
                    const price = parseFloat(addBtn.dataset.price || "0");
                    const evId = addBtn.dataset.evId;
                    const eventInfo = evId
                        ? {
                            id: evId,
                            nom: addBtn.dataset.evNom || "",
                            type: addBtn.dataset.evType || "",
                            date: addBtn.dataset.evDate || "",
                        }
                        : undefined;
                    if (id)
                        this.addItem({ id, title, price, event: eventInfo });
                    return;
                }
                // Actions dans le panier
                const actionBtn = target.closest(".quantity-increase, .quantity-decrease, .remove-from-cart");
                if (actionBtn) {
                    const id = actionBtn.dataset.id;
                    if (!id)
                        return;
                    if (actionBtn.classList.contains("quantity-increase")) {
                        const item = this.findItem(id);
                        if (item)
                            this.updateQuantity(id, item.quantity + 1);
                    }
                    else if (actionBtn.classList.contains("quantity-decrease")) {
                        const item = this.findItem(id);
                        if (item)
                            this.updateQuantity(id, Math.max(1, item.quantity - 1));
                    }
                    else if (actionBtn.classList.contains("remove-from-cart")) {
                        this.removeItem(id);
                    }
                    return;
                }
                // UI Drawer
                if (target.id === "cart-clear")
                    this.clearCart();
                if (target.id === "cart-fab")
                    this.openDrawer();
                if (target.id === "cart-close")
                    this.closeDrawer();
            });
            // Changement de quantité via input
            (_a = this.$.items) === null || _a === void 0 ? void 0 : _a.addEventListener("change", (e) => {
                const input = e.target.closest(".quantity-input");
                if (input) {
                    const id = input.dataset.id;
                    const value = parseInt(input.value, 10) || 1;
                    if (id)
                        this.updateQuantity(id, Math.max(1, value));
                }
            });
            // Paiement
            (_b = this.$.payBtn) === null || _b === void 0 ? void 0 : _b.addEventListener("click", () => __awaiter(this, void 0, void 0, function* () {
                if (this.cart.length === 0) {
                    alert("Votre panier est vide.");
                    return;
                }
                try {
                    const data = yield Http.postJson("/api/v1/payments/checkout", {
                        items: this.cart.map(({ id, quantity }) => ({ id, quantity })),
                    });
                    if (data.url)
                        window.location.href = data.url;
                    else
                        alert("URL de paiement introuvable.");
                }
                catch (err) {
                    alert("Erreur de paiement: " + ((err === null || err === void 0 ? void 0 : err.message) || err));
                }
            }));
            // Touche Échap
            document.addEventListener("keydown", (e) => {
                if (e.key === "Escape")
                    this.closeDrawer();
            });
        }
        // ===== DRAWER =====
        openDrawer() {
            const cart = document.getElementById("cart");
            cart === null || cart === void 0 ? void 0 : cart.classList.add("open");
        }
        closeDrawer() {
            const cart = document.getElementById("cart");
            cart === null || cart === void 0 ? void 0 : cart.classList.remove("open");
        }
        // Ajout: Hydratation des prix et validation des items via l’API
        async hydratePrices() {
            try {
                const ids = Array.from(new Set(this.cart.map((i) => i.id))).filter(Boolean);
                if (ids.length === 0) return;

                const url = `/api/v1/payments/offres?ids=${encodeURIComponent(ids.join(","))}`;
                const res = await fetch(url, { credentials: "include" });
                if (!res.ok) return;
                const data = await res.json().catch(() => ({}));
                const list = (data && data.offres) || [];
                const byId = new Map(list.map((o) => [String(o.id), o]));

                // Reconstruire le panier: mettre à jour prix/titre et retirer les inconnus
                let removed = 0;
                const updated = [];
                for (const item of this.cart) {
                    const o = byId.get(String(item.id));
                    if (!o) {
                        removed++;
                        continue; // Offre inconnue: on retire l’article invalide
                    }
                    updated.push({
                        ...item,
                        title: item.title || o.title || "Article",
                        price: typeof o.price === "number" ? o.price : Number(o.price || 0),
                    });
                }
                if (removed > 0 || updated.length !== this.cart.length) {
                    this.cart = updated;
                    this.saveCart();
                    this.render();
                    if (removed > 0) {
                        this.showToast(`${removed} article(s) retiré(s): offre(s) invalide(s)`);
                    }
                } else {
                    // Si rien retiré, mais prix 0 → mettre à jour pour cohérence
                    let changed = false;
                    for (const item of this.cart) {
                        const o = byId.get(String(item.id));
                        if (o && (item.price !== o.price)) {
                            item.price = o.price;
                            changed = true;
                        }
                    }
                    if (changed) {
                        this.saveCart();
                        this.render();
                    }
                }
            } catch (e) {
                // Tolérant: ne bloque pas l’UI
                console.warn("hydratePrices failed", e);
            }
        }
    }
    // ✅ Initialisation
    new Cart();
});
