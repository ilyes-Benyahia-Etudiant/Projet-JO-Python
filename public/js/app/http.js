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
}
_a = Http;
Http.mergeInit = (init = {}) => {
    const headers = new Headers(init.headers || {});
    return Object.assign(Object.assign({}, init), { headers });
};
// Injection CSRF ici (méthode Http.request)
Http.request = (url, init = {}) => {
    const finalInit = _a.mergeInit(init);
    // CSRF: ajoute X-CSRF-Token pour les méthodes non sûres lorsque les cookies seront envoyés
    try {
        const method = String(finalInit.method || "GET").toUpperCase();
        if (method !== "GET" && method !== "HEAD" && method !== "OPTIONS") {
            const credentials = finalInit.credentials != null ? finalInit.credentials : "same-origin";
            const reqUrl = new URL(url, window.location.href);
            const sameOrigin = reqUrl.origin === window.location.origin;
            const willSendCookies = credentials === "include" || (credentials === "same-origin" && sameOrigin);
            if (willSendCookies) {
                const headers = finalInit.headers instanceof Headers ? finalInit.headers : new Headers(finalInit.headers || {});
                if (!headers.has("X-CSRF-Token")) {
                    // Essaie plusieurs noms de cookies: csrf_token, XSRF-TOKEN, CSRF-TOKEN
                    const token = (() => {
                        const raw = document.cookie || "";
                        const escapeRe = (s) => s.replace(/[-[\]{}()*+?.,\\^$|#\s]/g, "\\$&");
                        const find = (name) => {
                            const m = raw.match(new RegExp("(?:^|;\\s*)" + escapeRe(name) + "=([^;]+)"));
                            return m ? decodeURIComponent(m[1]) : "";
                        };
                        return find("csrf_token") || find("XSRF-TOKEN") || find("CSRF-TOKEN");
                    })();
                    if (token) headers.set("X-CSRF-Token", token);
                }
                finalInit.headers = headers;
            }
        }
    } catch (_e) {
        // silence
    }
    return fetch(url, finalInit);
};
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
Http.getJson = (url, init = {}) => {
    return _a.json(url, Object.assign(Object.assign({}, init), { method: "GET" }));
};
Http.postJson = (url, body, init = {}) => {
    const headers = new Headers(init.headers || {});
    if (!headers.has("Content-Type"))
        headers.set("Content-Type", "application/json");
    return _a.json(url, Object.assign(Object.assign({}, init), { method: "POST", headers, body: body !== undefined ? JSON.stringify(body) : init.body }));
};
// Expose global
// eslint-disable-next-line @typescript-eslint/no-explicit-any
window.Http = Http;
