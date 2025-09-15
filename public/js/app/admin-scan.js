"use strict";
// =============================================================================
// Utilitaires
// =============================================================================
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    return parts.length === 2 ? parts.pop().split(";").shift() || null : null;
}
function getCsrfToken() {
    return getCookie("csrf_token") || getCookie("csrftoken") || null;
}
function getUrlToken() {
    try {
        const params = new URLSearchParams(window.location.search);
        const token = params.get("token");
        return (token === null || token === void 0 ? void 0 : token.trim()) || null;
    }
    catch (_a) {
        return null;
    }
}
function escapeHtml(str) {
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
var ValidationStatus;
(function (ValidationStatus) {
    ValidationStatus["Invalid"] = "Invalid";
    ValidationStatus["Scanned"] = "Scanned";
    ValidationStatus["Validated"] = "Validated";
    ValidationStatus["AlreadyValidated"] = "AlreadyValidated";
})(ValidationStatus || (ValidationStatus = {}));
// =============================================================================
// Classe Principale: AdminScanPage
// =============================================================================
class AdminScanPage {
    static initOnce() {
        if (AdminScanPage.__ADMIN_SCAN_INITED)
            return;
        AdminScanPage.__ADMIN_SCAN_INITED = true;
        new AdminScanPage();
    }
    constructor() {
        this.isValidating = false;
        this.currentToken = null;
        this.inputEl = document.querySelector("#token-input");
        this.validateBtn = document.querySelector("#validate-btn");
        this.payloadEl = document.querySelector("#validation-result");
        this.bindEvents();
        this.prefillFromUrlAndSearch();
    }
    bindEvents() {
        var _a, _b;
        (_a = this.inputEl) === null || _a === void 0 ? void 0 : _a.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                this.handleSearch();
            }
        });
        (_b = this.validateBtn) === null || _b === void 0 ? void 0 : _b.addEventListener("click", (e) => {
            e.preventDefault();
            this.handleSearch();
        });
    }
    handleSearch() {
        var _a, _b;
        const token = (_b = (_a = this.inputEl) === null || _a === void 0 ? void 0 : _a.value) === null || _b === void 0 ? void 0 : _b.trim();
        if (token) {
            this.searchTicket(token);
        }
    }
    prefillFromUrlAndSearch() {
        const urlToken = getUrlToken();
        if (urlToken) {
            if (this.inputEl)
                this.inputEl.value = urlToken;
            this.searchTicket(urlToken);
        }
    }
    performRequest(url, method, body) {
        return __awaiter(this, void 0, void 0, function* () {
            if (this.isValidating)
                return { status: "error", message: "Une opération est déjà en cours." };
            this.isValidating = true;
            try {
                const csrf = getCsrfToken();
                const res = yield fetch(url, {
                    method,
                    headers: Object.assign({ "Content-Type": "application/json" }, (csrf ? { "X-CSRF-Token": csrf } : {})),
                    body: body ? JSON.stringify(body) : undefined,
                    credentials: "include",
                });
                let data = null;
                try {
                    data = yield res.json();
                }
                catch (_a) {
                    data = null;
                }
                const wrapped = Object.assign({ __httpStatus: res.status }, (data !== null && data !== void 0 ? data : {}));
                console.log(`[${method}] ${url} ->`, wrapped);
                return wrapped;
            }
            catch (err) {
                console.error(`${method} error:`, err);
                return { __networkError: true, status: "error", message: "Erreur réseau. Veuillez réessayer." };
            }
            finally {
                this.isValidating = false;
            }
        });
    }
    searchTicket(token) {
        return __awaiter(this, void 0, void 0, function* () {
            this.currentToken = token;
            const json = yield this.performRequest(`/api/v1/validation/ticket/${encodeURIComponent(token)}`, "GET");
            const parsed = this.normalizeResponse(json, "get");
            this.renderPayload(parsed);
        });
    }
    postValidate() {
        return __awaiter(this, void 0, void 0, function* () {
            if (!this.currentToken)
                return;
            const json = yield this.performRequest("/api/v1/validation/scan", "POST", { token: this.currentToken });
            const parsed = this.normalizeResponse(json, "post");
            // Nettoyage du champ si validé
            if (parsed.status === ValidationStatus.Validated && this.inputEl) {
                this.inputEl.value = "";
            }
            // On ne déclenche pas de toast ici; l'affichage se fait sous la barre
            this.renderPayload(parsed);
        });
    }
    normalizeResponse(json, kind) {
        var _a, _b, _c, _d, _e, _f, _g, _h;
        // 404 -> billet inconnu
        if ((json === null || json === void 0 ? void 0 : json.__httpStatus) === 404) {
            return { status: ValidationStatus.Invalid, message: json.message || "Billet inconnu" };
        }
        // Déballage
        const data = (_b = (_a = json === null || json === void 0 ? void 0 : json.data) !== null && _a !== void 0 ? _a : json) !== null && _b !== void 0 ? _b : {};
        const ticket = (_f = (_d = (_c = data.ticket) !== null && _c !== void 0 ? _c : data.billet) !== null && _d !== void 0 ? _d : (_e = data === null || data === void 0 ? void 0 : data.data) === null || _e === void 0 ? void 0 : _e.ticket) !== null && _f !== void 0 ? _f : null;
        const validation = (_h = (_g = data.validation) !== null && _g !== void 0 ? _g : data.scan) !== null && _h !== void 0 ? _h : null;
        const rawStatus = (data.status || data.result || "").toString().toLowerCase();
        const msg = data.message;
        if (kind === "get") {
            // GET: billet connu ? prêt ou déjà validé
            if (ticket && validation) {
                return { status: ValidationStatus.AlreadyValidated, ticket, validation, message: msg };
            }
            if (ticket) {
                return { status: ValidationStatus.Scanned, ticket, validation, message: msg };
            }
            return { status: ValidationStatus.Invalid, message: msg || "Billet inconnu" };
        }
        else {
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
    renderPayload(data) {
        if (!this.payloadEl)
            return;
        this.payloadEl.innerHTML = "";
        const { status, ticket, validation, message } = data;
        // Affiche uniquement le bandeau de statut (sans badge)
        const bannerText = this.getStatusLabel(status);
        this.showStatusBanner(status, this.payloadEl, bannerText);
        // Détails
        if (ticket) {
            this.renderTicketDetails(ticket, validation);
        }
        else {
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
    getStatusLabel(status) {
        const labels = {
            [ValidationStatus.Invalid]: "Invalide",
            [ValidationStatus.Scanned]: "Prêt à valider",
            [ValidationStatus.Validated]: "Validé",
            [ValidationStatus.AlreadyValidated]: "Déjà validé",
        };
        return labels[status] || "Inconnu";
    }
    renderStatusBadge(status) {
        // Intentionnellement vide: on n'affiche plus le badge de statut
    }
    renderTicketDetails(ticket, validation) {
        var _a, _b;
        if (!this.payloadEl)
            return;
        const detailsContainer = document.createElement("div");
        detailsContainer.className = "mt-3";
        const title = ticket.title || ((_a = ticket.offre) === null || _a === void 0 ? void 0 : _a.title) || "Billet";
        const email = ticket.userEmail || ((_b = ticket.users) === null || _b === void 0 ? void 0 : _b.email) || ticket.email || "";
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
    showStatusBanner(status, container, text) {
        let color = "#DC2626", bg = "#FEE2E2"; // défaut rouge
        if (status === ValidationStatus.Validated) {
            color = "#16A34A";
            bg = "#D1FAE5";
        }
        else if (status === ValidationStatus.Scanned) {
            color = "#D97706";
            bg = "#FEF3C7";
        }
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
    showStatusToast(status, ticket, message) {
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
    getTicketSummary(ticket) {
        var _a, _b;
        const title = ticket.title || ((_a = ticket.offre) === null || _a === void 0 ? void 0 : _a.title) || "Billet";
        const email = ticket.userEmail || ((_b = ticket.users) === null || _b === void 0 ? void 0 : _b.email) || ticket.email || "";
        const token = ticket.token || "";
        const parts = [title];
        if (email)
            parts.push(email);
        if (token)
            parts.push(this.shortToken(token));
        return parts.join(" — ");
    }
    shortToken(t) {
        if (!t)
            return "";
        return t.length > 12 ? `${t.slice(0, 4)}…${t.slice(-4)}` : t;
    }
    showToast(message, type = "success") {
        // Supprimer un toast précédent pour éviter l’empilement
        const old = document.getElementById("__toast__");
        if (old)
            old.remove();
        let color = "#16A34A", bg = "#D1FAE5";
        if (type === "error") {
            color = "#DC2626";
            bg = "#FEE2E2";
        }
        else if (type === "warning") {
            color = "#D97706";
            bg = "#FEF3C7";
        }
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
AdminScanPage.__ADMIN_SCAN_INITED = false;
// =============================================================================
// Initialisation
// =============================================================================
document.addEventListener("DOMContentLoaded", () => {
    AdminScanPage.initOnce();
});
console.log("[admin-scan] script chargé");
