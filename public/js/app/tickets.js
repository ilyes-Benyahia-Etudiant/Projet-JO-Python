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
class TicketsManager {
    constructor() {
        this.init = () => {
            this.confirmIfReturnedFromStripe().finally(() => this.loadTickets());
        };
        this.loadTickets = () => __awaiter(this, void 0, void 0, function* () {
            try {
                const HttpAny = window.Http;
                const tickets = HttpAny
                    ? yield HttpAny.getJson("/api/v1/tickets/")
                    : yield (yield fetch("/api/v1/tickets/", { credentials: "same-origin" })).json();
                this.renderTickets(tickets);
                // Nouveau: télécharger les QR codes pour chaque billet
                this.fetchQRCodes(tickets).catch(() => { });
            }
            catch (error) {
                console.error('Erreur:', error);
                this.showError("Erreur lors du chargement des billets. Veuillez réessayer plus tard.");
            }
        });
        this.renderTickets = (tickets) => {
            if (!this.ticketsListElement)
                return;
            if (!tickets || tickets.length === 0) {
                this.showEmptyMessage("Vous n'avez pas encore de billets. Revenez après l'achat.");
                return;
            }
            this.ticketsListElement.innerHTML = tickets.map(this.createTicketHTML).join('');
        };
        this.createTicketHTML = (ticket) => {
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
              </div>`}
          </div>
        </div>
      </div>`;
        };
        this.showEmptyMessage = (message) => {
            if (!this.emptyMessageElement)
                return;
            this.emptyMessageElement.textContent = message;
            this.emptyMessageElement.style.display = 'block';
            if (this.ticketsListElement) {
                this.ticketsListElement.innerHTML = '';
            }
        };
        this.showError = (message) => {
            this.showEmptyMessage(message);
        };
        this.ticketsListElement = document.getElementById('tickets-list');
        this.emptyMessageElement = document.getElementById('tickets-empty');
        this.init();
    }
    confirmIfReturnedFromStripe() {
        return __awaiter(this, void 0, void 0, function* () {
            try {
                const url = new URL(window.location.href);
                const sessionId = url.searchParams.get("session_id");
                const confirmed = url.searchParams.get("confirmed");
                if (!sessionId || confirmed === "1")
                    return;
                const HttpAny = window.Http;
                if (HttpAny && typeof HttpAny.request === "function") {
                    yield HttpAny.request("/api/v1/payments/confirm?session_id=" + encodeURIComponent(sessionId), { method: "GET" });
                }
                else {
                    yield fetch("/api/v1/payments/confirm?session_id=" + encodeURIComponent(sessionId), {
                        method: "GET",
                        credentials: "same-origin",
                    });
                }
                try {
                    localStorage.removeItem("cart.v1");
                }
                catch (_a) { }
                url.searchParams.set("confirmed", "1");
                window.history.replaceState({}, "", url.toString());
                // Affiche un toast vert de succès
                this.showToast("Paiement confirmé. Vos billets ont été générés.", "success");
            }
            catch (e) {
                console.warn("Confirmation Stripe échouée:", e);
            }
        });
    }
    fetchQRCodes(tickets) {
        return __awaiter(this, void 0, void 0, function* () {
            const HttpAny = window.Http;
            for (const t of tickets) {
                const token = t.token;
                if (!token)
                    continue;
                try {
                    const res = HttpAny
                        ? yield HttpAny.getJson(`/api/v1/tickets/${encodeURIComponent(token)}/qrcode`)
                        : yield (yield fetch(`/api/v1/tickets/${encodeURIComponent(token)}/qrcode`, { credentials: "same-origin" })).json();
                    const qr = res === null || res === void 0 ? void 0 : res.qr_code;
                    if (!qr)
                        continue;
                    const card = document.querySelector(`.event-card[data-token="${token}"] .qr-slot`);
                    if (card) {
                        card.innerHTML = `<img src="${qr}" alt="QR Code" style="width:150px;height:150px;">`;
                    }
                }
                catch (_a) { }
            }
        });
    }
    // Ajout: Toast générique (success/erreur)
    showToast(message, type = "success") {
        const toast = document.createElement("div");
        toast.textContent = message;
        toast.style.position = "fixed";
        toast.style.right = "16px";
        toast.style.bottom = "16px";
        toast.style.zIndex = "9999";
        toast.style.padding = "12px 16px";
        toast.style.borderRadius = "6px";
        toast.style.color = "#fff";
        toast.style.fontWeight = "600";
        toast.style.boxShadow = "0 4px 12px rgba(0,0,0,0.15)";
        toast.style.background = type === "success" ? "#16a34a" : "#dc2626"; // vert / rouge
        toast.style.opacity = "0";
        toast.style.transition = "opacity 150ms ease";
        document.body.appendChild(toast);
        requestAnimationFrame(() => {
            toast.style.opacity = "1";
        });
        setTimeout(() => {
            toast.style.opacity = "0";
            setTimeout(() => toast.remove(), 200);
        }, 3000);
    }
}
// Initialisation quand le DOM est chargé
document.addEventListener('DOMContentLoaded', () => {
    new TicketsManager();
});
// Expose global pour les tests
window.TicketsManager = TicketsManager;
