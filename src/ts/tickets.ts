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
    this.loadTickets();
  }
  
  private loadTickets = async (): Promise<void> => {
    try {
      const response = await fetch('/api/tickets/');
      if (!response.ok) {
        throw new Error('Erreur lors du chargement des billets');
      }
      
      const tickets: Ticket[] = await response.json();
      this.renderTickets(tickets);
    } catch (error) {
      console.error('Erreur:', error);
      this.showError("Erreur lors du chargement des billets. Veuillez réessayer plus tard.");
    }
  }
  
  private renderTickets = (tickets: Ticket[]): void => {
    if (!this.ticketsListElement) return;
    
    if (!tickets || tickets.length === 0) {
      this.showEmptyMessage("Vous n'avez pas encore de billets. Revenez après l'achat.");
      return;
    }
    
    this.ticketsListElement.innerHTML = tickets.map(this.createTicketHTML).join('');
  }
  
  private createTicketHTML = (ticket: Ticket): string => {
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
              </div>`
            }
          </div>
        </div>
      </div>`;
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
}

// Initialisation quand le DOM est chargé
document.addEventListener('DOMContentLoaded', () => {
  new TicketsManager();
});

// Expose global pour les tests
(window as any).TicketsManager = TicketsManager;