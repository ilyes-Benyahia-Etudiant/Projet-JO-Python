"use strict";
class TicketsManager {
    constructor() {
        this.init = () => {
            this.loadTickets();
        };
        this.loadTickets = async () => {
            try {
                const response = await fetch('/api/tickets/');
                if (!response.ok) {
                    throw new Error('Erreur lors du chargement des billets');
                }
                const tickets = await response.json();
                this.renderTickets(tickets);
            }
            catch (error) {
                console.error('Erreur:', error);
                this.showError("Erreur lors du chargement des billets. Veuillez réessayer plus tard.");
            }
        };
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
      <div class="event-card">
        <div class="event-content">
          <h3>${ticket.offre_title || 'Billet'}</h3>
          <p>Prix: ${ticket.price_paid || '0.00'} €</p>
          <p>Référence: ${ticket.token || 'N/A'}</p>
          <div style="margin-top:8px;display:flex;flex-direction:column;align-items:center">
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
}
// Initialisation quand le DOM est chargé
document.addEventListener('DOMContentLoaded', () => {
    new TicketsManager();
});
// Expose global pour les tests
window.TicketsManager = TicketsManager;
//# sourceMappingURL=tickets.js.map