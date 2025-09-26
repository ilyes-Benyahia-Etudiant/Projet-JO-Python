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
var _a;
/**
 * Helper HTTP léger pour uniformiser fetch() à travers l'app:
 * - Injecte automatiquement le cookie CSRF pour les méthodes non idempotentes
 * - Sérialise/désérialise JSON et gère les entêtes par défaut
 * - Fournit des utilitaires getJson/postJson qui lèvent en cas d'erreur HTTP
 */
class Http {
    static normalizeExpected(expected) {
        if (!expected)
            return [200];
        return Array.isArray(expected) ? expected : [expected];
    }
    static buildInit(init) {
        var _b;
        const headers = new Headers((init === null || init === void 0 ? void 0 : init.headers) || {});
        // Ajout par défaut: JSON si le corps json est présent
        if ((init === null || init === void 0 ? void 0 : init.json) !== undefined) {
            if (!headers.has("Content-Type"))
                headers.set("Content-Type", "application/json");
            if (!headers.has("Accept"))
                headers.set("Accept", "application/json");
        }
        // Politique par défaut
        const base = {
            method: (init === null || init === void 0 ? void 0 : init.method) || "GET",
            credentials: (_b = init === null || init === void 0 ? void 0 : init.credentials) !== null && _b !== void 0 ? _b : "same-origin",
            headers
        };
        // Corps JSON si fourni
        if ((init === null || init === void 0 ? void 0 : init.json) !== undefined) {
            base.body = JSON.stringify(init.json);
        }
        else if ((init === null || init === void 0 ? void 0 : init.body) !== undefined) {
            base.body = init.body;
        }
        // Recopie des autres options si besoin
        if (init === null || init === void 0 ? void 0 : init.signal)
            base.signal = init.signal;
        if (init === null || init === void 0 ? void 0 : init.mode)
            base.mode = init.mode;
        if (init === null || init === void 0 ? void 0 : init.cache)
            base.cache = init.cache;
        if (init === null || init === void 0 ? void 0 : init.redirect)
            base.redirect = init.redirect;
        if (init === null || init === void 0 ? void 0 : init.referrer)
            base.referrer = init.referrer;
        if (init === null || init === void 0 ? void 0 : init.referrerPolicy)
            base.referrerPolicy = init.referrerPolicy;
        if (init === null || init === void 0 ? void 0 : init.integrity)
            base.integrity = init.integrity;
        if (init === null || init === void 0 ? void 0 : init.keepalive)
            base.keepalive = init.keepalive;
        return base;
    }
    static getCookie(name) {
        if (typeof document === "undefined")
            return null;
        const cookies = document.cookie ? document.cookie.split("; ") : [];
        for (const c of cookies) {
            if (!c)
                continue;
            const [k, ...rest] = c.split("=");
            if (k === name) {
                try {
                    return decodeURIComponent(rest.join("="));
                }
                catch (_b) {
                    return rest.join("=");
                }
            }
        }
        return null;
    }
    /**
     * Récupère le token CSRF depuis les cookies si présent.
     * Retourne null si le token n'est pas disponible ou en contexte non-DOM.
     */
    static getCsrfToken() {
        return this.getCookie("csrf_token");
    }
}
_a = Http;
/**
 * Fusionne les options de requête et injecte automatiquement le token CSRF
 * pour les méthodes non-sûres (POST, PUT, PATCH, DELETE).
 */
Http.mergeInit = (init = {}) => {
    var _b;
    const headers = new Headers(init.headers || {});
    const method = (init.method || "GET").toUpperCase();
    // Injecte automatiquement le token CSRF pour les requêtes non-sûres
    if (method === "POST" || method === "PUT" || method === "PATCH" || method === "DELETE") {
        if (!headers.has("X-CSRF-Token")) {
            const token = _a.getCsrfToken();
            if (token) {
                headers.set("X-CSRF-Token", token);
            }
        }
    }
    return Object.assign(Object.assign({}, init), { headers, credentials: (_b = init.credentials) !== null && _b !== void 0 ? _b : "same-origin" });
};
/**
 * Enveloppe fetch() avec l’injection CSRF et les credentials same-origin par défaut.
 * Ne lève pas en cas d'erreur HTTP; préférez json()/getJson()/postJson() pour ça.
 */
Http.request = (url, init = {}) => {
    const finalInit = _a.mergeInit(init);
    return fetch(url, finalInit);
};
/**
 * Appelle request(), tente de parser JSON, et lève une Error si res.ok est falsy.
 * La Error contient un message construit depuis detail/message/texte de la réponse.
 */
Http.json = (url_1, ...args_1) => __awaiter(void 0, [url_1, ...args_1], void 0, function* (url, init = {}) {
    const res = yield _a.request(url, init);
    let data = undefined;
    try {
        data = yield res.json();
    }
    catch (_b) {
        // ignore JSON parse errors; data stays undefined
    }
    if (!res.ok) {
        let msg = "";
        if (data && typeof data === "object") {
            msg = data.detail || data.message || "";
        }
        if (!msg) {
            try {
                msg = yield res.text();
            }
            catch (_c) {
                // ignore
            }
        }
        throw new Error(msg || `HTTP ${res.status}`);
    }
    return data;
});
/**
 * Raccourci GET qui retourne le JSON de la réponse ou lève en cas d'erreur HTTP.
 */
Http.getJson = (url, init = {}) => {
    return _a.json(url, Object.assign(Object.assign({}, init), { method: "GET" }));
};
/**
 * Raccourci POST JSON (pose Content-Type: application/json si manquant) et lève en cas d'erreur HTTP.
 */
Http.postJson = (url, body, init = {}) => {
    const headers = new Headers(init.headers || {});
    if (!headers.has("Content-Type"))
        headers.set("Content-Type", "application/json");
    return _a.json(url, Object.assign(Object.assign({}, init), { method: "POST", headers, body: body !== undefined ? JSON.stringify(body) : init.body }));
};
// Expose global
// eslint-disable-next-line @typescript-eslint/no-explicit-any
window.Http = Http;
