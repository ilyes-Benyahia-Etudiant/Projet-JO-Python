document.addEventListener("DOMContentLoaded", () => {
  interface CartItem {
    id: string;
    title: string;
    price: number;
    image: string;
    quantity: number;
  }

  class Cart {
    private readonly STORAGE_KEY = "cart.v1";
    private cart: CartItem[] = [];
    private readonly cartItemsContainer: HTMLElement | null;
    private readonly cartEmptyMessage: HTMLElement | null;
    private readonly cartTotalElement: HTMLElement | null;
    private readonly payButton: HTMLButtonElement | null;
    private readonly currency = new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR" });

    constructor(opts: {
      itemsContainer: HTMLElement | null;
      emptyMessage: HTMLElement | null;
      totalElement: HTMLElement | null;
      payButton: HTMLButtonElement | null;
    }) {
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

    private formatCurrency = (amount: number): string => this.currency.format(amount);

    private loadCart = (): CartItem[] => {
      try {
        const raw = localStorage.getItem(this.STORAGE_KEY) || "[]";
        const parsed = JSON.parse(raw);
        return Array.isArray(parsed) ? (parsed as CartItem[]) : [];
      } catch {
        return [];
      }
    };

    private saveCart = () => {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.cart));
    };

    private findItem = (id: string): CartItem | undefined => this.cart.find((i) => i.id === id);

    private calculateTotal = (): number => this.cart.reduce((s, i) => s + i.price * i.quantity, 0);

    private render = (): void => {
      const list = this.cartItemsContainer;
      const empty = this.cartEmptyMessage;
      const total = this.cartTotalElement;
      if (!list || !empty || !total) return;

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

    addItem = ({ id, title, price, image, quantity = 1 }: Partial<CartItem> & { id: string }) => {
      const existing = this.findItem(id);
      if (existing) existing.quantity += quantity || 1;
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

    removeItem = (id: string) => {
      this.cart = this.cart.filter((i) => i.id !== id);
      this.saveCart();
      this.render();
    };

    updateQuantity = (id: string, quantity: number | string | null | undefined) => {
      const q = Math.max(1, parseInt(String(quantity ?? "1"), 10) || 1);
      const item = this.findItem(id);
      if (item) item.quantity = q;
      this.saveCart();
      this.render();
    };

    private bindCatalogActions = () => {
      document.addEventListener("click", (event) => {
        const target = event.target as HTMLElement | null;
        if (!target) return;

        const addButton = target.closest(".btn-add-to-cart") as HTMLElement | null;
        if (addButton) {
          const id = addButton.dataset.id;
          if (!id) return;
          const title = addButton.dataset.title || "Article";
          const price = parseFloat(addButton.dataset.price || "0");
          const image = addButton.dataset.image || "";
          this.addItem({ id, title, price, image, quantity: 1 });
          return;
        }

        const inc = target.closest(".quantity-increase") as HTMLElement | null;
        const dec = target.closest(".quantity-decrease") as HTMLElement | null;
        const del = target.closest(".remove-from-cart") as HTMLElement | null;

        if (inc) {
          const id = inc.dataset.id;
          if (!id) return;
          const item = this.findItem(id);
          if (item) this.updateQuantity(id, item.quantity + 1);
          return;
        }
        if (dec) {
          const id = dec.dataset.id;
          if (!id) return;
          const item = this.findItem(id);
          if (item) this.updateQuantity(id, Math.max(1, item.quantity - 1));
          return;
        }
        if (del) {
          const id = del.dataset.id;
          if (id) this.removeItem(id);
          return;
        }
      });
    };

    private bindQuantityChange = () => {
      if (!this.cartItemsContainer) return;
      this.cartItemsContainer.addEventListener("change", (event) => {
        const target = event.target as HTMLElement | null;
        if (!target) return;
        const input = target.closest(".quantity-input") as HTMLInputElement | null;
        if (!input) return;
        this.updateQuantity(input.dataset.id || "", input.value);
      });
    };

    private bindCheckout = () => {
      if (!this.payButton) return;
      this.payButton.addEventListener("click", async () => {
        const latest = this.loadCart();
        if (!Array.isArray(latest) || latest.length === 0) {
          alert("Votre panier est vide.");
          return;
        }
        const items = latest.map((it) => ({ id: it.id, quantity: it.quantity }));
        try {
          const data = await Http.postJson<{ url?: string }>("/payments/checkout", { items });
          if (data.url) window.location.href = data.url;
          else alert("URL de paiement introuvable.");
        } catch (e: any) {
          alert("Erreur de paiement: " + (e?.message || e));
        }
      });
    };
  }

  const cart = new Cart({
    itemsContainer: document.getElementById("cart-items"),
    emptyMessage: document.getElementById("cart-empty"),
    totalElement: document.getElementById("cart-total"),
    payButton: document.getElementById("cart-pay") as HTMLButtonElement | null,
  });
});