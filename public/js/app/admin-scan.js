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
class AdminScanPage {
    constructor() {
        this.input = document.getElementById("token-input");
        this.btn = document.getElementById("validate-btn");
        this.result = document.getElementById("result");
        this.init();
    }
    init() {
        var _a;
        (_a = this.btn) === null || _a === void 0 ? void 0 : _a.addEventListener("click", () => this.handleValidate());
        // Si l’URL contient ?token=..., on pré-remplit et on valide
        const url = new URL(window.location.href);
        const token = url.searchParams.get("token");
        if (token && this.input) {
            this.input.value = token;
            this.handleValidate();
        }
    }
    handleValidate() {
        return __awaiter(this, void 0, void 0, function* () {
            var _a;
            const token = (((_a = this.input) === null || _a === void 0 ? void 0 : _a.value) || "").trim();
            if (!token)
                return this.renderInfo("Veuillez saisir un token.", "warn");
            try {
                const HttpAny = window.Http;
                let res;
                if (HttpAny === null || HttpAny === void 0 ? void 0 : HttpAny.postJson) {
                    res = yield HttpAny.postJson("/api/v1/validation/scan", { token });
                }
                else {
                    const csrf = this.getCookie("csrf_token") || "";
                    const r = yield fetch("/api/v1/validation/scan", {
                        method: "POST",
                        credentials: "same-origin",
                        headers: {
                            "Content-Type": "application/json",
                            "X-CSRF-Token": csrf,
                        },
                        body: JSON.stringify({ token }),
                    });
                    if (!r.ok) {
                        const errTxt = yield r.text().catch(() => "");
                        throw new Error(`HTTP ${r.status}: ${errTxt}`);
                    }
                    res = yield r.json();
                }
                if (res.status === "ok") {
                    this.renderSuccess(`Succès: billet validé.`);
                    this.renderTicket(res.ticket, res.validation);
                }
                else if (res.status === "already_validated") {
                    this.renderInfo(`Info: billet déjà validé.`, "warn");
                    this.renderTicket(res.ticket, res.validation);
                }
                else {
                    this.renderError(`Erreur: ${res.message || "Validation impossible"}`);
                }
            }
            catch (e) {
                this.renderError(`Erreur: ${(e === null || e === void 0 ? void 0 : e.message) || e}`);
            }
        });
    }
    renderTicket(ticket, validation) {
        if (!this.result)
            return;
        const offre = ((ticket === null || ticket === void 0 ? void 0 : ticket.offres) || {});
        const scannedAt = (validation === null || validation === void 0 ? void 0 : validation.scanned_at) || "—";
        const scannedBy = (validation === null || validation === void 0 ? void 0 : validation.scanned_by) || "—";
        this.result.innerHTML = `
      <div class="border rounded p-3 mt-2">
        <div><strong>Référence:</strong> ${(ticket === null || ticket === void 0 ? void 0 : ticket.token) || "N/A"}</div>
        <div><strong>Offre:</strong> ${(offre === null || offre === void 0 ? void 0 : offre.title) || "—"}</div>
        <div><strong>Validé le:</strong> ${scannedAt}</div>
        <div><strong>Validé par:</strong> ${scannedBy}</div>
      </div>
    `;
    }
    renderSuccess(msg) { this.toast(msg, "success"); }
    renderError(msg) { this.toast(msg, "error"); }
    renderInfo(msg, type = "info") {
        this.toast(msg, type === "warn" ? "warn" : "info");
    }
    toast(message, type = "info") {
        const el = document.createElement("div");
        el.textContent = message;
        el.style.position = "fixed";
        el.style.right = "16px";
        el.style.bottom = "16px";
        el.style.zIndex = "9999";
        el.style.padding = "10px 14px";
        el.style.borderRadius = "6px";
        el.style.color = "#fff";
        el.style.fontWeight = "600";
        el.style.boxShadow = "0 4px 12px rgba(0,0,0,0.15)";
        el.style.opacity = "0";
        el.style.transition = "opacity 150ms ease";
        const color = type === "success" ? "#16a34a" : type === "error" ? "#dc2626" : type === "warn" ? "#f59e0b" : "#2563eb";
        el.style.background = color;
        document.body.appendChild(el);
        requestAnimationFrame(() => (el.style.opacity = "1"));
        setTimeout(() => {
            el.style.opacity = "0";
            setTimeout(() => el.remove(), 220);
        }, 2500);
    }
    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2)
            return parts.pop().split(';').shift() || null;
        return null;
    }
}
document.addEventListener("DOMContentLoaded", () => new AdminScanPage());
window.AdminScanPage = AdminScanPage;
function byId(id) {
    const el = document.getElementById(id);
    if (!el)
        throw new Error(`Element #${id} introuvable`);
    return el;
}
function getQueryToken() {
    const url = new URL(window.location.href);
    const t = url.searchParams.get("token");
    return t && t.trim() ? t.trim() : null;
}
function renderResultOk(container, data) {
    var _a, _b, _c;
    const { status, ticket, validation, message } = data;
    const displayName = (((_a = ticket.users) === null || _a === void 0 ? void 0 : _a.full_name) && ticket.users.full_name.trim()) ||
        (((_b = ticket.users) === null || _b === void 0 ? void 0 : _b.email) && ticket.users.email.trim()) ||
        "Utilisateur";
    const offreTitle = ((_c = ticket.offres) === null || _c === void 0 ? void 0 : _c.title) || "Offre";
    const badgeClass = status === "already_validated"
        ? "bg-yellow-100 text-yellow-800"
        : "bg-green-100 text-green-800";
    const statusText = status === "already_validated" ? "Déjà validé" : "Validé";
    container.innerHTML = `
    <div class="border rounded p-4 bg-white">
      <div class="flex items-center justify-between mb-2">
        <h3 class="text-lg font-semibold">${escapeHtml(displayName)}</h3>
        <span class="px-2 py-1 rounded text-sm ${badgeClass}">${statusText}</span>
      </div>
      <p class="text-gray-700 mb-1"><strong>Offre:</strong> ${escapeHtml(offreTitle)}</p>
      <p class="text-gray-700 mb-1"><strong>Token:</strong> <code>${escapeHtml(ticket.token)}</code></p>
      <p class="text-gray-700 mb-1"><strong>Message:</strong> ${escapeHtml(message || "")}</p>
      <p class="text-gray-600 mt-2 text-sm">
        <strong>Horodatage:</strong> ${escapeHtml(validation.scanned_at || "")}
      </p>
    </div>
  `;
}
function renderResultError(container, err) {
    const msg = err instanceof Error ? err.message : String(err || "Erreur");
    container.innerHTML = `
    <div class="border rounded p-4 bg-white">
      <div class="px-2 py-1 rounded text-sm bg-red-100 text-red-800 inline-block mb-2">Erreur</div>
      <p class="text-red-700">${escapeHtml(msg)}</p>
    </div>
  `;
}
function escapeHtml(s) {
    return s
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;");
}
function validateToken(token) {
    return __awaiter(this, void 0, void 0, function* () {
        const result = byId("result");
        result.innerHTML = `<div class="text-gray-500">Validation en cours...</div>`;
        try {
            // @ts-expect-error Http est exposé globalement par src/ts/http.ts
            const data = yield window.Http.postJson("/api/v1/validation/scan", { token });
            renderResultOk(result, data);
        }
        catch (err) {
            renderResultError(result, err);
        }
    });
}
function setup() {
    const input = byId("token-input");
    const btn = byId("validate-btn");
    const result = byId("result");
    btn.addEventListener("click", () => {
        const token = (input.value || "").trim();
        if (!token) {
            renderResultError(result, new Error("Veuillez saisir un token."));
            return;
        }
        validateToken(token);
    });
    // Préremplir depuis l'URL si ?token=...
    const t = getQueryToken();
    if (t) {
        input.value = t;
        // Valide automatiquement si le token est présent dans l'URL
        validateToken(t);
    }
}
document.addEventListener("DOMContentLoaded", setup);
