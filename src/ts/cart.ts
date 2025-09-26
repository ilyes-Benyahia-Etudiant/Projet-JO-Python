document.addEventListener("DOMContentLoaded", () => {
  /**
   * Représente un article dans le panier côté client.
   * - id: identifiant unique (correspond à l’offre)
   * - title: libellé affiché
   * - price: prix unitaire en EUR
   * - quantity: quantité souhaitée
   */
  interface CartItem {
    id: string;
    title: string;
    price: number;
    quantity: number;
    eventId?: string;
    eventName?: string;
    eventType?: string;
    eventDate?: string;
  }

  /**
   * Gestionnaire du panier:
   * - persiste dans localStorage
   * - met à jour dynamiquement la vue (liste, totaux, badges)
   * - centralise les interactions UI via un seul gestionnaire d’événements
   */
  class Cart {
    private readonly STORAGE_KEY = "cart.v1";
    private cart: CartItem[] = [];
    private readonly currency = new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR" });

    // Raccourcis DOM — initialisés une fois
    private readonly $ = {
      items: document.getElementById("cart-items"),
      empty: document.getElementById("cart-empty"),
      total: document.getElementById("cart-total"),
      payBtn: document.getElementById("cart-pay") as HTMLButtonElement | null,
      countBadges: [
        document.getElementById("cart-count-pill"),
        document.getElementById("cart-fab-badge"),
      ].filter(Boolean) as HTMLElement[],
    };

    constructor() {
      this.cart = this.loadCart();
      this.bindEvents();
      this.render();
      // Met à jour les badges même si les éléments du panier n'existent pas sur la page
      this.updateCartCountBadge();
    }

    // ===== GESTION DU PANIER =====

    private loadCart(): CartItem[] {
      try {
        const raw = localStorage.getItem(this.STORAGE_KEY) || "[]";
        return JSON.parse(raw) as CartItem[];
      } catch {
        return [];
      }
    }

    private saveCart() {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.cart));
    }

    private findItem(id: string): CartItem | undefined {
      return this.cart.find((item) => item.id === id);
    }

    private calculateTotal(): number {
      return this.cart.reduce((sum, item) => sum + item.price * item.quantity, 0);
    }

    private countItems(): number {
      return this.cart.reduce((sum, item) => sum + item.quantity, 0);
    }

    /**
     * Retourne un libellé "1 article" ou "N articles" pour le compteur.
     */
    private formatItemsCount(count: number): string {
      return `${count} ${count > 1 ? "articles" : "article"}`;
    }

    // ===== UI =====

    private updateCartCountBadge() {
      const count = this.countItems();
      this.$.countBadges.forEach((badge) => {
        badge.textContent = String(count);
        badge.style.display = count > 0 ? "inline-flex" : "none";
        badge.setAttribute("aria-label", count > 0
          ? `Articles dans le panier: ${count}`
          : "Aucun article"
        );
      });
    }

    private render() {
      const { items, empty, total } = this.$;
      if (!items || !empty || !total) return;

      if (this.cart.length === 0) {
        items.innerHTML = "";
        empty.style.display = "block";
        total.textContent = this.formatCurrency(0);
        this.updateCartCountBadge();
        return;
      }

      empty.style.display = "none";
      items.innerHTML = this.cart.map(this.renderItem).join("");
      total.textContent = this.formatCurrency(this.calculateTotal());
      this.updateCartCountBadge();
    }

    private renderItem = (item: CartItem): string => {
      const lineTotal = item.price * item.quantity;
      // Construit une ligne “événement • date” si dispo
      const eventLine = [item.eventName || item.eventType || "", item.eventDate || ""]
        .filter(Boolean)
        .join(" • ");
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
            ${eventLine ? `<div class="cart-item-subtitle" style="color:#666;font-size:0.9em;">${eventLine}</div>` : ""}
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

    private formatCurrency(amount: number): string {
      return this.currency.format(amount);
    }

    // ===== TOAST — ✅ CORRIGÉ POUR AFFICHAGE GARANTI =====
    private ensureToastEl(): HTMLElement {
        let el = document.getElementById("toast-success") as HTMLElement | null;
        if (!el) {
            el = document.createElement("div");
            el.id = "toast-success";
            el.setAttribute("role", "status");
            el.setAttribute("aria-live", "polite");
            el.setAttribute("aria-live", "polite");
            document.body.appendChild(el);
        }
        return el;
    }

    private showToast(message: string) {
        const el = this.ensureToastEl();
        // toast succès: s'assurer qu'on n'a pas la classe erreur
        el.classList.remove("error");
        el.classList.remove("show");
        void (el as any).offsetWidth; // relance la transition CSS
        el.textContent = message || "Article ajouté au panier";
        el.classList.add("show");
        window.setTimeout(() => {
            el.classList.remove("show");
        }, 3000);
    }

    addItem = ({ id, title, price, quantity = 1, eventId, eventName, eventType, eventDate }: Partial<CartItem> & { id: string }) => {
        console.log(`addItem appelée pour ID: ${id}, Titre: ${title}`);
        const existing = this.findItem(id);
        if (existing) {
            existing.quantity += quantity || 1;
            // Hydrate l'événement si manquant
            if (!existing.eventId && eventId) existing.eventId = eventId;
            if (!existing.eventName && eventName) existing.eventName = eventName;
            if (!existing.eventType && eventType) existing.eventType = eventType;
            if (!existing.eventDate && eventDate) existing.eventDate = eventDate;
            console.log("Article existant mis à jour");
        } else {
            this.cart.push({
                id,
                title: title || "Article",
                price: price || 0,
                quantity: quantity || 1,
                eventId,
                eventName,
                eventType,
                eventDate,
            });
            console.log("Nouvel article ajouté au panier");
        }
        this.saveCart();

        // Met à jour les badges même si render() ne peut pas s'exécuter sur cette page
        this.updateCartCountBadge();

        this.render();

        // Toast avec compteur compact
        const currentCount = this.countItems();
        this.showToast(`“${title || "Article"}” ajouté au panier • ${this.formatItemsCount(currentCount)}`);

        console.log("Fin de addItem – toast devrait être affiché");
    };

    removeItem(id: string) {
      this.cart = this.cart.filter((item) => item.id !== id);
      this.saveCart();
      this.render();
    }

    /**
     * Met à jour la quantité d’un article (min = 1) puis persiste et re-render.
     */
    updateQuantity(id: string, quantity: number) {
      const item = this.findItem(id);
      if (item) {
        item.quantity = Math.max(1, quantity);
        this.saveCart();
        this.render();
      }
    }

    /**
     * Vide le panier, persiste, re-render, et referme le drawer.
     */
    clearCart() {
      this.cart = [];
      this.saveCart();
      this.render();
      this.closeDrawer();
    }

    // ===== ÉVÉNEMENTS — UN SEUL GESTIONNAIRE CENTRAL =====

    private bindEvents() {
      // Gestionnaire centralisé pour tout le document
      document.addEventListener("click", (e) => {
        const target = e.target as HTMLElement;

        // Ajout depuis catalogue
        const addBtn = target.closest<HTMLElement>(".btn-add-to-cart");
        if (addBtn) {
          const id = addBtn.dataset.id;
          const title = addBtn.dataset.title || "Article";
          const price = parseFloat(addBtn.dataset.price || "0");

          // 1) Essaye via data-ev-* posés par billeterie.js
          let eventId = addBtn.dataset.evId || "";
          let eventName = addBtn.dataset.evNom || "";
          let eventType = addBtn.dataset.evType || "";
          let eventDate = addBtn.dataset.evDate || "";

          // 2) Fallback: si non renseigné, récupère depuis localStorage (selectedEvent.v1)
          if (!eventId) {
            const ev = (() => {
              try {
                const raw = localStorage.getItem("selectedEvent.v1");
                const ev = raw ? JSON.parse(raw) : null;
                return {
                  eventId: ev?.id || "",
                  eventName: ev?.nom || "",
                  eventType: ev?.type || "",
                  eventDate: ev?.date || "",
                };
              } catch {
                return {};
              }
            })();
            eventId = ev.eventId || eventId;
            eventName = ev.eventName || eventName;
            eventType = ev.eventType || eventType;
            eventDate = ev.eventDate || eventDate;
          }

          if (id) this.addItem({ id, title, price, eventId, eventName, eventType, eventDate });
          return;
        }

        // Actions dans le panier
        const actionBtn = target.closest<HTMLElement>(
          ".quantity-increase, .quantity-decrease, .remove-from-cart"
        );
        if (actionBtn) {
          const id = actionBtn.dataset.id;
          if (!id) return;

          if (actionBtn.classList.contains("quantity-increase")) {
            const item = this.findItem(id);
            if (item) this.updateQuantity(id, item.quantity + 1);
          } else if (actionBtn.classList.contains("quantity-decrease")) {
            const item = this.findItem(id);
            if (item) this.updateQuantity(id, Math.max(1, item.quantity - 1));
          } else if (actionBtn.classList.contains("remove-from-cart")) {
            this.removeItem(id);
          }
          return;
        }

        // UI Drawer
        if (target.id === "cart-clear") this.clearCart();
        if (target.id === "cart-fab") this.openDrawer();
        if (target.id === "cart-close") this.closeDrawer();
      });

      // Changement de quantité via input
      this.$.items?.addEventListener("change", (e) => {
        const input = (e.target as HTMLElement).closest<HTMLInputElement>(".quantity-input");
        if (input) {
          const id = input.dataset.id;
          const value = parseInt(input.value, 10) || 1;
          if (id) this.updateQuantity(id, Math.max(1, value));
        }
      });

      // Paiement
      this.$.payBtn?.addEventListener("click", async () => {
        if (this.cart.length === 0) {
          alert("Votre panier est vide.");
          return;
        }
        try {
          const data = await Http.postJson<{ url?: string }>("/api/v1/payments/checkout", {
            items: this.cart.map(({ id, quantity }) => ({ id, quantity })),
          });
          if (data.url) window.location.href = data.url;
          else alert("URL de paiement introuvable.");
        } catch (err: any) {
          const msg = String(err?.message || err || "");
          const unauthorized = /HTTP\s*401|Non\s*authentifié|Session expirée/i.test(msg);
          if (unauthorized) {
            const params = new URLSearchParams({ error: "Authentifiez-vous pour finaliser le paiement" });
            window.location.assign("/auth?" + params.toString());
            return;
          }
          alert("Erreur de paiement: " + (msg || "Une erreur est survenue."));
        }
      });

      // Touche Échap
      document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") this.closeDrawer();
      });
    }

    // ===== DRAWER =====

    private openDrawer() {
      const cart = document.getElementById("cart");
      cart?.classList.add("open");
    }

    private closeDrawer() {
      const cart = document.getElementById("cart");
      cart?.classList.remove("open");
    }
  }

  // ✅ Initialisation
  new Cart();
});


class Cart {
    // Fallback: lit l'événement sélectionné (défini par billeterie.js) si data-ev-* ne sont pas présents
    private getSelectedEventFromStorage(): { eventId?: string; eventName?: string; eventType?: string; eventDate?: string } {
      try {
        const raw = localStorage.getItem("selectedEvent.v1");
        const ev = raw ? JSON.parse(raw) : null;
        return {
          eventId: ev?.id || "",
          eventName: ev?.nom || "",
          eventType: ev?.type || "",
          eventDate: ev?.date || "",
        };
      } catch {
        return {};
      }
    }
}