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
// Utilitaires
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2)
        return parts.pop().split(";").shift() || null;
    return null;
}
function getCsrfToken() {
    // Essaie plusieurs clés possibles
    return getCookie("csrf_token") || getCookie("csrftoken") || null;
}
function getUrlToken() {
    try {
        const params = new URLSearchParams(window.location.search);
        const token = params.get("token");
        return token && token.trim().length > 0 ? token.trim() : null;
    }
    catch (_a) {
        return null;
    }
}
class AdminScanPage {
    static initOnce(fn) {
        if (AdminScanPage.__ADMIN_SCAN_INITED)
            return;
        AdminScanPage.__ADMIN_SCAN_INITED = true;
        fn();
    }
    constructor() {
        this.isValidating = false;
        this.inputEl = null;
        this.btnEl = null;
        this.resultEl = null;
        this.inputEl = document.querySelector("#token-input");
        this.btnEl = document.querySelector("#validate-btn");
        this.resultEl = document.querySelector("#validation-result");
        this.bindEvents();
        this.prefillFromUrlAndMaybeValidate();
    }
    bindEvents() {
        if (this.btnEl) {
            this.btnEl.addEventListener("click", (e) => {
                var _a, _b;
                e.preventDefault();
                const token = ((_b = (_a = this.inputEl) === null || _a === void 0 ? void 0 : _a.value) === null || _b === void 0 ? void 0 : _b.trim()) || "";
                if (!token) {
                    this.renderMessage("Veuillez saisir un token.", "error");
                    return;
                }
                this.validateToken(token);
            });
        }
        if (this.inputEl) {
            this.inputEl.addEventListener("keydown", (e) => {
                var _a, _b;
                if (e.key === "Enter") {
                    e.preventDefault();
                    const token = ((_b = (_a = this.inputEl) === null || _a === void 0 ? void 0 : _a.value) === null || _b === void 0 ? void 0 : _b.trim()) || "";
                    if (!token) {
                        this.renderMessage("Veuillez saisir un token.", "error");
                        return;
                    }
                    this.validateToken(token);
                }
            });
        }
    }
    prefillFromUrlAndMaybeValidate() {
        const urlToken = getUrlToken();
        if (urlToken) {
            if (this.inputEl)
                this.inputEl.value = urlToken;
            // Auto-validate si le token vient de l'URL
            this.validateToken(urlToken);
        }
    }
    validateToken(token) {
        return __awaiter(this, void 0, void 0, function* () {
            var _a;
            if (this.isValidating)
                return;
            this.isValidating = true;
            const prevBtnText = (_a = this.btnEl) === null || _a === void 0 ? void 0 : _a.innerText;
            if (this.btnEl) {
                this.btnEl.disabled = true;
                this.btnEl.innerText = "Validation...";
            }
            try {
                const csrf = getCsrfToken();
                const res = yield fetch("/api/v1/validation/scan", {
                    method: "POST",
                    headers: Object.assign({ "Content-Type": "application/json" }, (csrf ? { "X-CSRF-Token": csrf } : {})),
                    body: JSON.stringify({ token }),
                    credentials: "include",
                });
                let json;
                try {
                    json = (yield res.json());
                }
                catch (_b) {
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
            }
            catch (err) {
                console.error("validateToken error:", err);
                this.renderMessage("Erreur réseau. Réessayez.", "error");
            }
            finally {
                this.isValidating = false;
                if (this.btnEl) {
                    this.btnEl.disabled = false;
                    if (prevBtnText !== undefined)
                        this.btnEl.innerText = prevBtnText;
                }
            }
        });
    }
    normalizeResponse(resp) {
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
    renderSuccess(payload) {
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
        }
        else {
            alert(msg);
        }
    }
    renderAlreadyValidated(payload) {
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
        }
        else {
            alert(msg);
        }
    }
    getStatusLabel(status) {
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
    renderStatusBadge(status, payload) {
        const label = this.getStatusLabel(status);
        const color = status === "validated"
            ? "#10b981" // vert
            : status === "already_validated"
                ? "#f59e0b" // orange
                : "#ef4444"; // rouge (not_found | error)
        const v = (payload === null || payload === void 0 ? void 0 : payload.validation) || {};
        const scannedAt = v.scanned_at || v.scannedAt || v.created_at || "";
        const scannedBy = v.scanned_by || v.scannedBy || "";
        const extra = [
            (payload === null || payload === void 0 ? void 0 : payload.message) ? `msg: ${payload.message}` : null,
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
    renderMessage(message, kind = "info") {
        if (this.resultEl) {
            const cls = kind === "error" ? "validation--error" : kind === "success" ? "validation--success" : "validation--info";
            this.resultEl.innerHTML = `
        <div class="validation ${cls}">
          <p>${this.escapeHtml(message)}</p>
        </div>
      `;
        }
        else {
            if (kind === "error")
                console.error(message);
            else
                console.log(message);
        }
    }
    renderTicketDetails(payload) {
        var _a, _b;
        const ticket = payload.ticket;
        if (!ticket)
            return "";
        const title = (ticket === null || ticket === void 0 ? void 0 : ticket.offreTitle) || ((_a = ticket === null || ticket === void 0 ? void 0 : ticket.offres) === null || _a === void 0 ? void 0 : _a.title) || (ticket === null || ticket === void 0 ? void 0 : ticket.title) || "Billet";
        const email = (ticket === null || ticket === void 0 ? void 0 : ticket.userEmail) || ((_b = ticket === null || ticket === void 0 ? void 0 : ticket.users) === null || _b === void 0 ? void 0 : _b.email) || (ticket === null || ticket === void 0 ? void 0 : ticket.email) || "";
        const createdAt = (ticket === null || ticket === void 0 ? void 0 : ticket.created_at) || (ticket === null || ticket === void 0 ? void 0 : ticket.createdAt) || (ticket === null || ticket === void 0 ? void 0 : ticket.scanned_at) || "";
        return `
      <div class="ticket">
        <div><strong>Billet:</strong> ${this.escapeHtml(String(title))}</div>
        ${email ? `<div><strong>Acheteur:</strong> ${this.escapeHtml(String(email))}</div>` : ""}
        ${createdAt ? `<div><strong>Créé le:</strong> ${this.escapeHtml(String(createdAt))}</div>` : ""}
      </div>
    `;
    }
    renderValidationDetails(payload) {
        const v = payload.validation;
        if (!v)
            return "";
        const scannedAt = v.scanned_at || v.scannedAt || v.created_at || "";
        const scannedBy = v.scanned_by || v.scannedBy || "";
        return `
      <div class="validation-meta">
        ${scannedAt ? `<div><strong>Scanné le:</strong> ${this.escapeHtml(String(scannedAt))}</div>` : ""}
        ${scannedBy ? `<div><strong>Scanné par:</strong> ${this.escapeHtml(String(scannedBy))}</div>` : ""}
      </div>
    `;
    }
    escapeHtml(str) {
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/\"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
}
AdminScanPage.__ADMIN_SCAN_INITED = false;
// Initialisation unique
document.addEventListener("DOMContentLoaded", () => AdminScanPage.initOnce(() => new AdminScanPage()));
// Optionnel: exposition pour debug dans la console
// @ts-ignore
window.AdminScanPage = AdminScanPage;
