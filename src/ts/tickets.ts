/**
 * tickets.ts - Page “Mes billets”
 * - Confirme un paiement si on revient de Stripe (query ?session_id)
 * - Charge la liste des billets et insère les QR codes (lazy fetch image/URI)
 * - Affiche un toast de succès/erreur pour le feedback utilisateur
 */

interface Ticket {
  id?: string;
  offre_title?: string;
  price_paid?: number;
  token?: string;
  qr_code?: string;
  created_at?: string;
}

class TicketsManager {
  private ticketsListElement: HTMLElement | null;
  private emptyMessageElement: HTMLElement | null;
  
  constructor() {
    this.ticketsListElement = document.getElementById('tickets-list');
    this.emptyMessageElement = document.getElementById('tickets-empty');
    this.init();
  }
  
  private init = (): void => {
    this.confirmIfReturnedFromStripe().finally(() => this.loadTickets());
  }
  
  /**
   * Si on revient de Stripe avec un session_id, tente la confirmation côté API,
   * nettoie l’URL, vide le panier local et affiche un toast de succès.
   */
  private async confirmIfReturnedFromStripe(): Promise<void> {
    try {
      const url = new URL(window.location.href);
      const sessionId = url.searchParams.get("session_id");
      const confirmed = url.searchParams.get("confirmed");

      if (!sessionId || confirmed === "1") return;

      const HttpAny = (window as any).Http;
      if (HttpAny && typeof HttpAny.request === "function") {
        await HttpAny.request("/api/v1/payments/confirm?session_id=" + encodeURIComponent(sessionId), { method: "GET" });
      } else {
        await fetch("/api/v1/payments/confirm?session_id=" + encodeURIComponent(sessionId), {
          method: "GET",
          credentials: "same-origin",
        });
      }

      try { localStorage.removeItem("cart.v1"); } catch {}

      url.searchParams.set("confirmed", "1");
      window.history.replaceState({}, "", url.toString());

      // Affiche un toast vert de succès
      this.showToast("Paiement confirmé. Vos billets ont été générés.", "success");
    } catch (e) {
      console.warn("Confirmation Stripe échouée:", e);
    }
  }
  
  /**
   * Charge la liste des billets utilisateur depuis l’API puis les rend.
   * Enchaîne un fetch des QR codes pour chaque billet affiché.
   */
  private loadTickets = async (): Promise<void> => {
    try {
      const HttpAny = (window as any).Http;
      const tickets: Ticket[] = HttpAny
        ? await HttpAny.getJson("/api/v1/tickets/")
        : await (await fetch("/api/v1/tickets/", { credentials: "same-origin" })).json();
      this.renderTickets(tickets);
      // Nouveau: télécharger les QR codes pour chaque billet
      this.fetchQRCodes(tickets).catch(() => {});
    } catch (error) {
      console.error('Erreur:', error);
      this.showError("Erreur lors du chargement des billets. Veuillez réessayer plus tard.");
    }
  }
  
  /**
   * Rend la liste des billets ou affiche un message vide s’il n’y en a pas.
   */
  private renderTickets = (tickets: Ticket[]): void => {
    if (!this.ticketsListElement) return;
    
    if (!tickets || tickets.length === 0) {
      this.showEmptyMessage("Vous n'avez pas encore de billets. Revenez après l'achat.");
      return;
    }
    
    this.ticketsListElement.innerHTML = tickets.map(this.createTicketHTML).join('');
  }
  
  /**
   * Génére le HTML pour un billet, avec un slot pour le QR code.
   */
  private createTicketHTML = (ticket: Ticket): string => {
    return `
      <div class="event-card" data-token="${ticket.token || ''}">
        <div class="event-content">
          <h3>${ticket.offre_title || 'Billet'}</h3>
          <p>Prix: ${ticket.price_paid || '0.00'} €</p>
          <p>Référence: ${ticket.token || 'N/A'}</p>
          <div class="qr-slot" style="margin-top:8px;display:flex;flex-direction:column;align-items:center">
            ${ticket.qr_code ? `<img src="${ticket.qr_code}" alt="QR Code" style="width:150px;height:150px;">` : 
              `<div style="display:flex;gap:8px;align-items:center">
                <span class="material-symbols-outlined">qr_code_2</span>
                <span class="text-gray-700">QR code non disponible</span>
              </div>`
            }
          </div>
        </div>
      </div>`;
  }
  
  /**
   * Récupère et injecte les QR codes des billets déjà rendus dans le DOM.
   */
  private async fetchQRCodes(tickets: Ticket[]): Promise<void> {
    const HttpAny = (window as any).Http;
    for (const t of tickets) {
      const token = t.token;
      if (!token) continue;
      try {
        const res = HttpAny
          ? await HttpAny.getJson(`/api/v1/tickets/${encodeURIComponent(token)}/qrcode`)
          : await (await fetch(`/api/v1/tickets/${encodeURIComponent(token)}/qrcode`, { credentials: "same-origin" })).json();
        const qr = res?.qr_code;
        if (!qr) continue;
        const card = document.querySelector(`.event-card[data-token="${token}"] .qr-slot`) as HTMLElement | null;
        if (card) {
          card.innerHTML = `<img src="${qr}" alt="QR Code" style="width:150px;height:150px;">`;
        }
      } catch {}
    }
  }
  
  private showEmptyMessage = (message: string): void => {
    if (!this.emptyMessageElement) return;
    this.emptyMessageElement.textContent = message;
    this.emptyMessageElement.style.display = 'block';
    if (this.ticketsListElement) {
      this.ticketsListElement.innerHTML = '';
    }
  }
  
  private showError = (message: string): void => {
    this.showEmptyMessage(message);
  }
  
  // Ajout: Toast générique (success/erreur)
  private showToast(message: string, type: "success" | "error" = "success"): void {
    let el = document.getElementById("toast-success") as HTMLElement | null;
    if (!el) {
      el = document.createElement("div");
      el.id = "toast-success";
      el.setAttribute("role", "status");
      el.setAttribute("aria-live", "polite");
      document.body.appendChild(el);
    }
    el.textContent = message;
    el.classList.toggle("error", type === "error");
    el.classList.remove("show");
    void (el as any).offsetWidth; // relance la transition CSS
    el.classList.add("show");
    setTimeout(() => {
      el.classList.remove("show");
    }, 3000);
  }
}

// Initialisation quand le DOM est chargé
document.addEventListener('DOMContentLoaded', () => {
  new TicketsManager();
});

// Expose global pour les tests
(window as any).TicketsManager = TicketsManager;