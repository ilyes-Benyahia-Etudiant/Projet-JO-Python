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
        constructor(opts) {
            this.STORAGE_KEY = "cart.v1";
            this.cart = [];
            this.currency = new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR" });
            this.formatCurrency = (amount) => this.currency.format(amount);
            this.loadCart = () => {
                try {
                    const raw = localStorage.getItem(this.STORAGE_KEY) || "[]";
                    const parsed = JSON.parse(raw);
                    return Array.isArray(parsed) ? parsed : [];
                }
                catch (_a) {
                    return [];
                }
            };
            this.saveCart = () => {
                localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.cart));
            };
            this.findItem = (id) => this.cart.find((i) => i.id === id);
            this.calculateTotal = () => this.cart.reduce((s, i) => s + i.price * i.quantity, 0);
            this.render = () => {
                const list = this.cartItemsContainer;
                const empty = this.cartEmptyMessage;
                const total = this.cartTotalElement;
                if (!list || !empty || !total)
                    return;
                if (this.cart.length === 0) {
                    list.innerHTML = "";
                    empty.style.display = "";
                    total.textContent = this.formatCurrency(0);
                    return;
                }
                empty.style.display = "none";
                const html = this.cart
                    .map((item) => {
                    const lineTotal = item.price * item.quantity;
                    return `
          <div class="cart-item" style="display:flex; align-items:center; gap:8px; padding:8px 0; border-bottom:1px solid #f3f3f3">
            <img src="${item.image || ""}" alt="${item.title || ""}" style="width:48px; height:48px; object-fit:cover; border-radius:6px; background:#fafafa" />
            <div style="flex:1">
              <div style="font-weight:600">${item.title}</div>
              <div style="color:#666">${this.formatCurrency(item.price)}</div>
            </div>
            <div style="display:flex; align-items:center; gap:6px">
              <button class="quantity-decrease" data-id="${item.id}" title="Diminuer">-</button>
              <input type="number" class="quantity-input" data-id="${item.id}" min="1" value="${item.quantity}" style="width:56px; text-align:center" />
              <button class="quantity-increase" data-id="${item.id}" title="Augmenter">+</button>
            </div>
            <div style="min-width: 90px; text-align:right">${this.formatCurrency(lineTotal)}</div>
            <button class="remove-from-cart" data-id="${item.id}">Supprimer</button>
          </div>`;
                })
                    .join("");
                list.innerHTML = html;
                total.textContent = this.formatCurrency(this.calculateTotal());
            };
            this.addItem = ({ id, title, price, image, quantity = 1 }) => {
                const existing = this.findItem(id);
                if (existing)
                    existing.quantity += quantity || 1;
                else
                    this.cart.push({
                        id,
                        title: title || "Article",
                        price: price || 0,
                        image: image || "",
                        quantity: quantity || 1,
                    });
                this.saveCart();
                this.render();
            };
            this.removeItem = (id) => {
                this.cart = this.cart.filter((i) => i.id !== id);
                this.saveCart();
                this.render();
            };
            this.updateQuantity = (id, quantity) => {
                const q = Math.max(1, parseInt(String(quantity !== null && quantity !== void 0 ? quantity : "1"), 10) || 1);
                const item = this.findItem(id);
                if (item)
                    item.quantity = q;
                this.saveCart();
                this.render();
            };
            this.bindCatalogActions = () => {
                document.addEventListener("click", (event) => {
                    const target = event.target;
                    if (!target)
                        return;
                    const addButton = target.closest(".btn-add-to-cart");
                    if (addButton) {
                        const id = addButton.dataset.id;
                        if (!id)
                            return;
                        const title = addButton.dataset.title || "Article";
                        const price = parseFloat(addButton.dataset.price || "0");
                        const image = addButton.dataset.image || "";
                        this.addItem({ id, title, price, image, quantity: 1 });
                        return;
                    }
                    const inc = target.closest(".quantity-increase");
                    const dec = target.closest(".quantity-decrease");
                    const del = target.closest(".remove-from-cart");
                    if (inc) {
                        const id = inc.dataset.id;
                        if (!id)
                            return;
                        const item = this.findItem(id);
                        if (item)
                            this.updateQuantity(id, item.quantity + 1);
                        return;
                    }
                    if (dec) {
                        const id = dec.dataset.id;
                        if (!id)
                            return;
                        const item = this.findItem(id);
                        if (item)
                            this.updateQuantity(id, Math.max(1, item.quantity - 1));
                        return;
                    }
                    if (del) {
                        const id = del.dataset.id;
                        if (id)
                            this.removeItem(id);
                        return;
                    }
                });
            };
            this.bindQuantityChange = () => {
                if (!this.cartItemsContainer)
                    return;
                this.cartItemsContainer.addEventListener("change", (event) => {
                    const target = event.target;
                    if (!target)
                        return;
                    const input = target.closest(".quantity-input");
                    if (!input)
                        return;
                    this.updateQuantity(input.dataset.id || "", input.value);
                });
            };
            this.bindCheckout = () => {
                if (!this.payButton)
                    return;
                this.payButton.addEventListener("click", () => __awaiter(this, void 0, void 0, function* () {
                    const latest = this.loadCart();
                    if (!Array.isArray(latest) || latest.length === 0) {
                        alert("Votre panier est vide.");
                        return;
                    }
                    const items = latest.map((it) => ({ id: it.id, quantity: it.quantity }));
                    try {
                        const data = yield Http.postJson("/api/v1/payments/checkout", { items });
                        if (data.url)
                            window.location.href = data.url;
                        else
                            alert("URL de paiement introuvable.");
                    }
                    catch (e) {
                        alert("Erreur de paiement: " + ((e === null || e === void 0 ? void 0 : e.message) || e));
                    }
                }));
            };
            this.cartItemsContainer = opts.itemsContainer;
            this.cartEmptyMessage = opts.emptyMessage;
            this.cartTotalElement = opts.totalElement;
            this.payButton = opts.payButton;
            this.cart = this.loadCart();
            this.bindCatalogActions();
            this.bindQuantityChange();
            this.bindCheckout();
            this.render();
        }
    }
    const cart = new Cart({
        itemsContainer: document.getElementById("cart-items"),
        emptyMessage: document.getElementById("cart-empty"),
        totalElement: document.getElementById("cart-total"),
        payButton: document.getElementById("cart-pay"),
    });
});
