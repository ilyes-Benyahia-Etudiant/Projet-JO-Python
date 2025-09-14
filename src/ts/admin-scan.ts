// Utilitaires
function getCookie(name: string): string | null {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop()!.split(";").shift() || null;
  return null;
}

function getCsrfToken(): string | null {
  // Essaie plusieurs clés possibles
  return getCookie("csrf_token") || getCookie("csrftoken") || null;
}

function getUrlToken(): string | null {
  try {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");
    return token && token.trim().length > 0 ? token.trim() : null;
  } catch {
    return null;
  }
}

type ValidationStatus = "validated" | "already_validated" | "not_found" | "error";

interface ValidationPayload {
  message?: string;
  ticket?: any;
  validation?: any;
}

interface ValidationResponse {
  status: ValidationStatus;
  message?: string;
  ticket?: any;
  validation?: any;
  // Compat: certains back peuvent renvoyer { ok, data } ou d'autres enveloppes
  ok?: boolean;
  data?: {
    status?: ValidationStatus;
    message?: string;
    ticket?: any;
    validation?: any;
  };
}

class AdminScanPage {
  private isValidating = false;
  private inputEl: HTMLInputElement | null = null;
  private btnEl: HTMLButtonElement | null = null;
  private resultEl: HTMLElement | null = null;

  private static __ADMIN_SCAN_INITED = false;

  static initOnce(fn: () => void) {
    if (AdminScanPage.__ADMIN_SCAN_INITED) return;
    AdminScanPage.__ADMIN_SCAN_INITED = true;
    fn();
  }

  constructor() {
    this.inputEl = document.querySelector<HTMLInputElement>("#token-input");
    this.btnEl = document.querySelector<HTMLButtonElement>("#validate-btn");
    this.resultEl = document.querySelector<HTMLElement>("#validation-result");

    this.bindEvents();
    this.prefillFromUrlAndMaybeValidate();
  }

  private bindEvents() {
    if (this.btnEl) {
      this.btnEl.addEventListener("click", (e) => {
        e.preventDefault();
        const token = this.inputEl?.value?.trim() || "";
        if (!token) {
          this.renderMessage("Veuillez saisir un token.", "error");
          return;
        }
        this.validateToken(token);
      });
    }

    if (this.inputEl) {
      this.inputEl.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          const token = this.inputEl?.value?.trim() || "";
          if (!token) {
            this.renderMessage("Veuillez saisir un token.", "error");
            return;
          }
          this.validateToken(token);
        }
      });
    }
  }

  private prefillFromUrlAndMaybeValidate() {
    const urlToken = getUrlToken();
    if (urlToken) {
      if (this.inputEl) this.inputEl.value = urlToken;
      // Auto-validate si le token vient de l'URL
      this.validateToken(urlToken);
    }
  }

  private async validateToken(token: string) {
    if (this.isValidating) return;
    this.isValidating = true;

    const prevBtnText = this.btnEl?.innerText;
    if (this.btnEl) {
      this.btnEl.disabled = true;
      this.btnEl.innerText = "Validation...";
    }

    try {
      const csrf = getCsrfToken();
      const res = await fetch("/api/v1/validation/scan", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(csrf ? { "X-CSRF-Token": csrf } : {}),
        },
        body: JSON.stringify({ token }),
        credentials: "include",
      });

      let json: ValidationResponse;
      try {
        json = (await res.json()) as ValidationResponse;
      } catch {
        this.renderMessage("Réponse serveur invalide.", "error");
        return;
      }

      const parsed = this.normalizeResponse(json);

      switch (parsed.status) {
        case "validated":
          this.renderSuccess(parsed);
          break;
        case "already_validated":
          this.renderAlreadyValidated(parsed);
          break;
        case "not_found":
          this.renderMessage(parsed.message || "Billet introuvable.", "error");
          break;
        default:
          this.renderMessage(parsed.message || "Erreur de validation.", "error");
          break;
      }
    } catch (err) {
      console.error("validateToken error:", err);
      this.renderMessage("Erreur réseau. Réessayez.", "error");
    } finally {
      this.isValidating = false;
      if (this.btnEl) {
        this.btnEl.disabled = false;
        if (prevBtnText !== undefined) this.btnEl.innerText = prevBtnText;
      }
    }
  }

  private normalizeResponse(resp: ValidationResponse): { status: ValidationStatus; message?: string; ticket?: any; validation?: any } {
    // Supporte plusieurs enveloppes de réponse
    if (resp && resp.status) {
      return {
        status: resp.status,
        message: resp.message,
        ticket: resp.ticket,
        validation: resp.validation,
      };
    }
    if (resp && resp.data && resp.data.status) {
      return {
        status: resp.data.status,
        message: resp.data.message,
        ticket: resp.data.ticket,
        validation: resp.data.validation,
      };
    }
    // Fallback si la structure est inattendue
    return {
      status: "error",
      message: "Réponse inattendue du serveur.",
    };
    // ... existing code ...
  }

  private renderSuccess(payload: ValidationPayload) {
    const msg = payload.message || "Validation enregistrée.";
    if (this.resultEl) {
      this.resultEl.innerHTML = `
        <div class="validation validation--success">
          <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
            ${this.renderStatusBadge("validated", payload)}
            <p style="margin:0;">${this.escapeHtml(msg)}</p>
          </div>
          ${this.renderTicketDetails(payload)}
          ${this.renderValidationDetails(payload)}
        </div>
      `;
    } else {
      alert(msg);
    }
  }

  private renderAlreadyValidated(payload: ValidationPayload) {
    const msg = payload.message || "Billet déjà validé.";
    if (this.resultEl) {
      this.resultEl.innerHTML = `
        <div class="validation validation--warning">
          <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
            ${this.renderStatusBadge("already_validated", payload)}
            <p style="margin:0;">${this.escapeHtml(msg)}</p>
          </div>
          ${this.renderTicketDetails(payload)}
          ${this.renderValidationDetails(payload)}
        </div>
      `;
    } else {
      alert(msg);
    }
  }

  private getStatusLabel(status: ValidationStatus): string {
    switch (status) {
      case "validated":
        return "Validé";
      case "already_validated":
        return "Déjà validé";
      case "not_found":
        return "Introuvable";
      default:
        return "Erreur";
    }
  }

  private renderStatusBadge(status: ValidationStatus, payload?: ValidationPayload): string {
    const label = this.getStatusLabel(status);
    const color =
      status === "validated"
        ? "#10b981" // vert
        : status === "already_validated"
        ? "#f59e0b" // orange
        : "#ef4444"; // rouge (not_found | error)

    const v: any = payload?.validation || {};
    const scannedAt = v.scanned_at || v.scannedAt || v.created_at || "";
    const scannedBy = v.scanned_by || v.scannedBy || "";
    const extra =
      [
        payload?.message ? `msg: ${payload.message}` : null,
        scannedAt ? `scanné: ${scannedAt}` : null,
        scannedBy ? `par: ${scannedBy}` : null,
      ]
        .filter(Boolean)
        .join(" | ") || label;

    return `
      <span
        title="${this.escapeHtml(extra)}"
        style="
          display:inline-flex; align-items:center; gap:6px;
          padding:2px 8px; border-radius:999px;
          background: rgba(0,0,0,0.04); color:#111827; font-size:12px; line-height:18px;
          border:1px solid rgba(0,0,0,0.08);
        "
      >
        <span
          aria-hidden="true"
          style="
            width:10px; height:10px; border-radius:50%;
            background:${color}; display:inline-block;
            box-shadow: 0 0 0 2px rgba(0,0,0,0.08) inset;
          "
        ></span>
        <strong style="font-weight:600;">${this.escapeHtml(label)}</strong>
      </span>
    `;
  }

  private renderMessage(message: string, kind: "error" | "info" | "success" = "info") {
    if (this.resultEl) {
      const cls = kind === "error" ? "validation--error" : kind === "success" ? "validation--success" : "validation--info";
      this.resultEl.innerHTML = `
        <div class="validation ${cls}">
          <p>${this.escapeHtml(message)}</p>
        </div>
      `;
    } else {
      if (kind === "error") console.error(message);
      else console.log(message);
    }
  }

  private renderTicketDetails(payload: ValidationPayload): string {
    const ticket = payload.ticket;
    if (!ticket) return "";
    const title = ticket?.offreTitle || ticket?.offres?.title || ticket?.title || "Billet";
    const email = ticket?.userEmail || ticket?.users?.email || ticket?.email || "";
    const createdAt = ticket?.created_at || ticket?.createdAt || ticket?.scanned_at || "";
    return `
      <div class="ticket">
        <div><strong>Billet:</strong> ${this.escapeHtml(String(title))}</div>
        ${email ? `<div><strong>Acheteur:</strong> ${this.escapeHtml(String(email))}</div>` : ""}
        ${createdAt ? `<div><strong>Créé le:</strong> ${this.escapeHtml(String(createdAt))}</div>` : ""}
      </div>
    `;
  }

  private renderValidationDetails(payload: ValidationPayload): string {
    const v = payload.validation;
    if (!v) return "";
    const scannedAt = v.scanned_at || v.scannedAt || v.created_at || "";
    const scannedBy = v.scanned_by || v.scannedBy || "";
    return `
      <div class="validation-meta">
        ${scannedAt ? `<div><strong>Scanné le:</strong> ${this.escapeHtml(String(scannedAt))}</div>` : ""}
        ${scannedBy ? `<div><strong>Scanné par:</strong> ${this.escapeHtml(String(scannedBy))}</div>` : ""}
      </div>
    `;
  }

  private escapeHtml(str: string): string {
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
}

// Initialisation unique
document.addEventListener("DOMContentLoaded", () =>
  AdminScanPage.initOnce(() => new AdminScanPage())
);

// Optionnel: exposition pour debug dans la console
// @ts-ignore
(window as any).AdminScanPage = AdminScanPage;