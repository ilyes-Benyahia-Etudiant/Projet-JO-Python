"use strict";
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
    return { ...init, headers };
};
Http.request = (url, init = {}) => {
    const finalInit = _a.mergeInit(init);
    return fetch(url, finalInit);
};
Http.json = async (url, init = {}) => {
    const res = await _a.request(url, init);
    let data = undefined;
    try {
        data = await res.json();
    }
    catch {
        // ignore JSON parse errors; data stays undefined
    }
    if (!res.ok) {
        let msg = "";
        if (data && typeof data === "object") {
            msg = data.detail || data.message || "";
        }
        if (!msg) {
            try {
                msg = await res.text();
            }
            catch {
                // ignore
            }
        }
        throw new Error(msg || `HTTP ${res.status}`);
    }
    return data;
};
Http.getJson = (url, init = {}) => {
    return _a.json(url, { ...init, method: "GET" });
};
Http.postJson = (url, body, init = {}) => {
    const headers = new Headers(init.headers || {});
    if (!headers.has("Content-Type"))
        headers.set("Content-Type", "application/json");
    return _a.json(url, {
        ...init,
        method: "POST",
        headers,
        body: body !== undefined ? JSON.stringify(body) : init.body,
    });
};
// Expose global
// eslint-disable-next-line @typescript-eslint/no-explicit-any
window.Http = Http;
//# sourceMappingURL=http.js.map