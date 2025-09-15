// =============================================================================
// Utilitaires
// =============================================================================

function getCookie(name: string): string | null {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  return parts.length === 2 ? parts.pop()!.split(";").shift() || null : null;
}

function getCsrfToken(): string | null {
  return getCookie("csrf_token") || getCookie("csrftoken") || null;
}

function getUrlToken(): string | null {
  try {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");
    return token?.trim() || null;
  } catch {
    return null;
  }
}

function escapeHtml(str: string): string {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// =============================================================================
// Types et Énumérations
// =============================================================================

enum ValidationStatus {
  Invalid = "Invalid",
  Scanned = "Scanned",
  Validated = "Validated",
  AlreadyValidated = "AlreadyValidated",
}

interface ValidationPayload {
  status: ValidationStatus;
  ticket?: any;
  validation?: any;
  message?: string;
}

// =============================================================================
// Classe Principale: AdminScanPage
// =============================================================================

class AdminScanPage {
  private isValidating = false;
  private inputEl: HTMLInputElement | null;
  private validateBtn: HTMLButtonElement | null;
  private payloadEl: HTMLElement | null;
  private currentToken: string | null = null;

  private static __ADMIN_SCAN_INITED = false;

  static initOnce() {
    if (AdminScanPage.__ADMIN_SCAN_INITED) return;
    AdminScanPage.__ADMIN_SCAN_INITED = true;
    new AdminScanPage();
  }

  constructor() {
    this.inputEl = document.querySelector<HTMLInputElement>("#token-input");
    this.validateBtn = document.querySelector<HTMLButtonElement>("#validate-btn");
    this.payloadEl = document.querySelector<HTMLElement>("#validation-result");

    this.bindEvents();
    this.prefillFromUrlAndSearch();
  }

  private bindEvents() {
    this.inputEl?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        this.handleSearch();
      }
    });

    this.validateBtn?.addEventListener("click", (e) => {
      e.preventDefault();
      this.handleSearch();
    });
  }

  private handleSearch() {
    const token = this.inputEl?.value?.trim();
    if (token) {
      this.searchTicket(token);
    }
  }

  private prefillFromUrlAndSearch() {
    const urlToken = getUrlToken();
    if (urlToken) {
      if (this.inputEl) this.inputEl.value = urlToken;
      this.searchTicket(urlToken);
    }
  }

  private async performRequest(
    url: string,
    method: "GET" | "POST",
    body?: any
  ): Promise<any> {
    if (this.isValidating) return { status: "error", message: "Une opération est déjà en cours." };
    this.isValidating = true;

    try {
      const csrf = getCsrfToken();
      const res = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          ...(csrf ? { "X-CSRF-Token": csrf } : {}),
        },
        body: body ? JSON.stringify(body) : undefined,
        credentials: "include",
      });

      let data: any = null;
      try {
        data = await res.json();
      } catch {
        data = null;
      }

      const wrapped = { __httpStatus: res.status, ...(data ?? {}) };
      console.log(`[${method}] ${url} ->`, wrapped);
      return wrapped;
    } catch (err) {
      console.error(`${method} error:`, err);
      return { __networkError: true, status: "error", message: "Erreur réseau. Veuillez réessayer." };
    } finally {
      this.isValidating = false;
    }
  }

  private async searchTicket(token: string) {
    this.currentToken = token;
    const json = await this.performRequest(`/api/v1/validation/ticket/${encodeURIComponent(token)}`, "GET");
    const parsed = this.normalizeResponse(json, "get");
    this.renderPayload(parsed);
  }

  private async postValidate() {
    if (!this.currentToken) return;
    const json = await this.performRequest("/api/v1/validation/scan", "POST", { token: this.currentToken });
    const parsed = this.normalizeResponse(json, "post");

    // Nettoyage du champ si validé
    if (parsed.status === ValidationStatus.Validated && this.inputEl) {
      this.inputEl.value = "";
    }

    // On ne déclenche pas de toast ici; l'affichage se fait sous la barre
    this.renderPayload(parsed);
  }

  private normalizeResponse(json: any, kind: "get" | "post"): ValidationPayload {
    // 404 -> billet inconnu
    if (json?.__httpStatus === 404) {
      return { status: ValidationStatus.Invalid, message: json.message || "Billet inconnu" };
    }

    // Déballage
    const data = json?.data ?? json ?? {};
    const ticket = data.ticket ?? data.billet ?? data?.data?.ticket ?? null;
    const validation = data.validation ?? data.scan ?? null;
    const rawStatus = (data.status || data.result || "").toString().toLowerCase();
    const msg = data.message as string | undefined;

    if (kind === "get") {
      // GET: billet connu ? prêt ou déjà validé
      if (ticket && validation) {
        return { status: ValidationStatus.AlreadyValidated, ticket, validation, message: msg };
      }
      if (ticket) {
        return { status: ValidationStatus.Scanned, ticket, validation, message: msg };
      }
      return { status: ValidationStatus.Invalid, message: msg || "Billet inconnu" };
    } else {
      // POST: validation
      const isValidated = rawStatus === "validated" || rawStatus === "success" || data.validated === true;
      const isAlreadyValidated = rawStatus === "already_validated" || (typeof msg === "string" && msg.toLowerCase().includes("déjà valid"));
      if (isAlreadyValidated) {
        return { status: ValidationStatus.AlreadyValidated, ticket, validation, message: msg || "Déjà validé" };
      }
      if (isValidated) {
        return { status: ValidationStatus.Validated, ticket, validation, message: msg || "Billet validé" };
      }
      // Si le backend renvoie juste le ticket après POST sans statut clair
      if (ticket && validation) {
        return { status: ValidationStatus.Validated, ticket, validation, message: msg || "Billet validé" };
      }
      return { status: ValidationStatus.Invalid, message: msg || "Billet inconnu" };
    }
  }

  private renderPayload(data: ValidationPayload) {
    if (!this.payloadEl) return;
    this.payloadEl.innerHTML = "";

    const { status, ticket, validation, message } = data;

    // Affiche uniquement le bandeau de statut (sans badge)
    const bannerText = this.getStatusLabel(status);
    this.showStatusBanner(status, this.payloadEl, bannerText);

    // Détails
    if (ticket) {
      this.renderTicketDetails(ticket, validation);
    } else {
      const msgEl = document.createElement("p");
      msgEl.textContent = message || (status === ValidationStatus.Invalid ? "Billet inconnu" : "Aucune donnée");
      this.payloadEl.appendChild(msgEl);
    }

    // Bouton de validation si prêt
    if (status === ValidationStatus.Scanned) {
      const validateBtn = document.createElement("button");
      validateBtn.className = "btn btn-success mt-3";
      validateBtn.textContent = "Valider le billet";
      validateBtn.onclick = () => this.postValidate();
      this.payloadEl.appendChild(validateBtn);
    }
  }

  private getStatusLabel(status: ValidationStatus): string {
    const labels = {
      [ValidationStatus.Invalid]: "Invalide",
      [ValidationStatus.Scanned]: "Prêt à valider",
      [ValidationStatus.Validated]: "Validé",
      [ValidationStatus.AlreadyValidated]: "Déjà validé",
    };
    return labels[status] || "Inconnu";
  }

  private renderStatusBadge(status: ValidationStatus) {
    // Intentionnellement vide: on n'affiche plus le badge de statut
  }

  private renderTicketDetails(ticket: any, validation?: any) {
    if (!this.payloadEl) return;

    const detailsContainer = document.createElement("div");
    detailsContainer.className = "mt-3";

    const title = ticket.title || ticket.offre?.title || "Billet";
    const email = ticket.userEmail || ticket.users?.email || ticket.email || "";
    const createdAt = ticket.created_at || ticket.createdAt || "";

    let html = `
      <div><strong>Token:</strong> ${escapeHtml(ticket.token || "")}</div>
      <div><strong>Détails:</strong> ${escapeHtml(title)}</div>
      ${email ? `<div><strong>Acheteur:</strong> ${escapeHtml(email)}</div>` : ""}
      ${createdAt ? `<div><strong>Créé le:</strong> ${escapeHtml(new Date(createdAt).toLocaleString())}</div>` : ""}
    `;

    if (validation) {
      const scannedAt = validation.scanned_at || validation.scannedAt || validation.created_at || "";
      const scannedBy = validation.scanned_by || validation.scannedBy || "";
      html += `
        <div class="mt-2">
          ${scannedAt ? `<div><strong>Scanné le:</strong> ${escapeHtml(new Date(scannedAt).toLocaleString())}</div>` : ""}
          ${scannedBy ? `<div><strong>Scanné par:</strong> ${escapeHtml(scannedBy)}</div>` : ""}
        </div>
      `;
    }
    
    detailsContainer.innerHTML = html;
    this.payloadEl.appendChild(detailsContainer);
  }

  // Bandeau de statut très visible
  private showStatusBanner(status: ValidationStatus, container: HTMLElement, text: string) {
    let color = "#DC2626", bg = "#FEE2E2"; // défaut rouge
    if (status === ValidationStatus.Validated) { color = "#16A34A"; bg = "#D1FAE5"; }
    else if (status === ValidationStatus.Scanned) { color = "#D97706"; bg = "#FEF3C7"; }

    const banner = document.createElement("div");
    banner.style.cssText = `
      padding: 10px 12px;
      border: 1px solid ${color};
      background: ${bg};
      color: ${color};
      border-radius: 8px;
      font-weight: 600;
      margin-bottom: 12px;
    `;
    banner.textContent = text;
    container.appendChild(banner);
  }

  // Toast avec support warning selon statut
  private showStatusToast(status: ValidationStatus, ticket?: any, message?: string) {
    const summary = ticket ? this.getTicketSummary(ticket) : "";
    switch (status) {
      case ValidationStatus.Validated:
        this.showToast(`Billet validé${summary ? " : " + summary : ""}`, "success");
        break;
      case ValidationStatus.AlreadyValidated:
        this.showToast(`Déjà validé${summary ? " : " + summary : ""}`, "error");
        break;
      case ValidationStatus.Scanned:
        this.showToast(`Prêt à valider${summary ? " : " + summary : ""}`, "warning");
        break;
      case ValidationStatus.Invalid:
      default:
        this.showToast(message || "Billet inconnu", "error");
        break;
    }
  }

  private getTicketSummary(ticket: any): string {
    const title = ticket.title || ticket.offre?.title || "Billet";
    const email = ticket.userEmail || ticket.users?.email || ticket.email || "";
    const token = ticket.token || "";
    const parts = [title];
    if (email) parts.push(email);
    if (token) parts.push(this.shortToken(token));
    return parts.join(" — ");
  }

  private shortToken(t: string): string {
    if (!t) return "";
    return t.length > 12 ? `${t.slice(0, 4)}…${t.slice(-4)}` : t;
  }

  private showToast(message: string, type: "success" | "error" | "warning" = "success") {
    // Supprimer un toast précédent pour éviter l’empilement
    const old = document.getElementById("__toast__");
    if (old) old.remove();

    let color = "#16A34A", bg = "#D1FAE5";
    if (type === "error") { color = "#DC2626"; bg = "#FEE2E2"; }
    else if (type === "warning") { color = "#D97706"; bg = "#FEF3C7"; }

    const el = document.createElement("div");
    el.id = "__toast__";
    el.textContent = message;
    el.style.cssText = `
      position: fixed;
      top: 16px;
      right: 16px;
      z-index: 99999;
      background: ${bg};
      color: ${color};
      border: 1px solid ${color};
      border-radius: 8px;
      padding: 10px 14px;
      font-weight: 600;
      box-shadow: 0 4px 10px rgba(0,0,0,.08);
      transition: opacity 0.3s;
      max-width: 420px;
      line-height: 1.3;
    `;
    document.body.appendChild(el);
    setTimeout(() => {
      el.style.opacity = "0";
      setTimeout(() => el.remove(), 300);
    }, 2500);
  }
}

// =============================================================================
// Initialisation
// =============================================================================

document.addEventListener("DOMContentLoaded", () => {
  AdminScanPage.initOnce();
});

console.log("[admin-scan] script chargé");