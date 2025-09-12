"use strict";
// --- Types ---
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
// --- Sélecteurs ---
const SELECTORS = {
    loginForm: "#web-login-form",
    signupForm: "#web-signup-form",
    forgotForm: "#web-forgot-form",
};
// --- Utilitaires UI ---
function setMessage(element, msg, type) {
    if (!element)
        return;
    element.textContent = msg;
    element.className = `message-area ${type}`;
}
function showGlobalMessage(type, text) {
    const css = type === "error" ? "err" : "ok";
    const clientMsg = document.getElementById("client-msg");
    if (clientMsg) {
        clientMsg.textContent = text;
        clientMsg.className = "msg " + css;
        clientMsg.style.display = "block";
        return;
    }
    const card = document.querySelector(".card");
    let el = document.querySelector(".msg." + css);
    if (!el) {
        el = document.createElement("div");
        el.className = "msg " + css;
        if (card)
            card.prepend(el);
        else
            document.body.prepend(el);
    }
    el.textContent = text;
}
// --- HTTP helper (tolérant) ---
function httpRequest(url, init) {
    return __awaiter(this, void 0, void 0, function* () {
        var _a;
        const w = window;
        if ((_a = w === null || w === void 0 ? void 0 : w.Http) === null || _a === void 0 ? void 0 : _a.request) {
            return w.Http.request(url, init);
        }
        return fetch(url, init);
    });
}
// --- Binding générique de formulaire ---
function bindFormSubmit(options) {
    const form = document.querySelector(options.formSelector);
    if (!form) {
        console.warn(`Formulaire non trouvé: ${options.formSelector}`);
        return;
    }
    const submitBtn = form.querySelector('button[type="submit"]');
    const messageEl = form.querySelector(".message-area");
    form.addEventListener("submit", (e) => __awaiter(this, void 0, void 0, function* () {
        e.preventDefault();
        if (!submitBtn)
            return;
        // Laisser le navigateur afficher ses messages natifs si invalid
        if (typeof form.reportValidity === "function" && !form.reportValidity()) {
            return;
        }
        const formData = new FormData(form);
        const payload = {};
        formData.forEach((value, key) => {
            payload[key] = value;
        });
        if (options.transformPayload) {
            Object.assign(payload, options.transformPayload(payload));
        }
        try {
            submitBtn.disabled = true;
            setMessage(messageEl, "Envoi en cours...", "ok");
            let response;
            try {
                response = yield httpRequest(options.apiEndpoint, {
                    method: "POST",
                    headers: { "Content-Type": "application/json", "Accept": "application/json" },
                    body: JSON.stringify(payload),
                });
            }
            catch (err) {
                // Si le wrapper Http a rejeté (4xx/5xx), tenter de lire err.response
                let errorMsg = "Une erreur est survenue.";
                try {
                    const resp = err === null || err === void 0 ? void 0 : err.response;
                    if (resp) {
                        let body = undefined;
                        try {
                            body = yield resp.json();
                        }
                        catch (_a) { }
                        errorMsg = (body === null || body === void 0 ? void 0 : body.detail) || (body === null || body === void 0 ? void 0 : body.message) || `Erreur HTTP ${resp.status}`;
                    }
                    else if (err === null || err === void 0 ? void 0 : err.message) {
                        errorMsg = err.message;
                    }
                }
                catch (_b) { }
                if (errorMsg.includes("Utilisateur existe déjà")) {
                    errorMsg = "Cet email est déjà utilisé. Essayez de vous connecter ou réinitialisez votre mot de passe.";
                }
                setMessage(messageEl, errorMsg, "err");
                submitBtn.disabled = false;
                return;
            }
            const responseData = yield response.json().catch(() => ({}));
            if (!response.ok) {
                const errorMessage = responseData.detail || responseData.message || `Erreur HTTP ${response.status}`;
                throw new Error(errorMessage);
            }
            const data = responseData;
            setMessage(messageEl, (typeof data === "object" && data && "message" in data
                ? data.message || "Opération réussie !"
                : "Opération réussie !"), "ok");
            if (options.onSuccess) {
                options.onSuccess(data, { form, submitBtn, messageEl });
            }
            if (options.redirectUrl) {
                const url = typeof options.redirectUrl === "function" ? options.redirectUrl(data) : options.redirectUrl;
                window.location.assign(url);
            }
        }
        catch (error) {
            // Réactiver le bouton en cas d'échec (ex: 401 identifiants invalides)
            submitBtn.disabled = false;
            let errorMsg = (error === null || error === void 0 ? void 0 : error.message) || "Une erreur est survenue.";
            if (typeof errorMsg === "string" && errorMsg.includes("Utilisateur existe déjà")) {
                errorMsg = "Cet email est déjà utilisé. Essayez de vous connecter ou réinitialisez votre mot de passe.";
            }
            setMessage(messageEl, errorMsg, "err");
            console.error(`Erreur lors de la soumission à ${options.apiEndpoint}:`, error);
        }
        finally {
            if (!options.redirectUrl) {
                submitBtn.disabled = false;
            }
        }
    }));
}
// --- Confirmation (lecture du hash) ---
function handleAuthConfirmationFromHash() {
    try {
        const raw = window.location.hash || "";
        if (!raw)
            return;
        const params = new URLSearchParams(raw.startsWith("#") ? raw.slice(1) : raw);
        const type = params.get("type");
        const error = params.get("error") || params.get("error_description") || params.get("message");
        const hasAnyToken = params.get("access_token") || params.get("token") || params.get("code");
        if (error) {
            showGlobalMessage("error", error);
        }
        else if (type === "signup" || hasAnyToken) {
            showGlobalMessage("ok", "Votre email est confirmé. Vous pouvez maintenant vous connecter.");
        }
        else {
            return;
        }
        try {
            const url = new URL(window.location.href);
            url.hash = "";
            window.history.replaceState({}, "", url.toString());
        }
        catch (_a) {
            window.location.hash = "";
        }
    }
    catch (e) {
        console.error("Erreur de lecture du hash:", e);
    }
}
// Nouveau: lecture du message de déconnexion depuis la query (?message=... ou ?error=...)
function handleAuthMessageFromQuery() {
    try {
        const url = new URL(window.location.href);
        const params = url.searchParams;
        const msg = params.get("message");
        const err = params.get("error");
        if (!msg && !err)
            return;
        // Si le serveur a déjà rendu un message (.msg ok/err sans l'id client-msg), ne pas en rajouter
        const serverMsgEl = document.querySelector(".msg.ok:not(#client-msg), .msg.err:not(#client-msg)");
        if (!serverMsgEl) {
            if (err) {
                showGlobalMessage("error", err);
            }
            else if (msg) {
                showGlobalMessage("ok", msg);
            }
        }
        // Nettoyer l'URL pour éviter la répétition au rechargement
        const cleanUrl = url.origin + url.pathname;
        window.history.replaceState({}, "", cleanUrl);
    }
    catch (e) {
        console.error("Erreur nettoyage URL (logout):", e);
    }
}
// --- Initialisation principale ---
function initializeAuthForms() {
    // Afficher message de déconnexion si présent dans l’URL puis nettoyer l’URL
    handleAuthMessageFromQuery();
    // Bandeau de confirmation depuis le hash
    handleAuthConfirmationFromHash();
    // Connexion
    bindFormSubmit({
        formSelector: SELECTORS.loginForm,
        apiEndpoint: "/api/v1/auth/login",
        redirectUrl: (data) => (data.user.role === "admin" ? "/admin" : "/session"),
    });
    // Inscription
    bindFormSubmit({
        formSelector: SELECTORS.signupForm,
        apiEndpoint: "/api/v1/auth/signup",
        transformPayload: (p) => {
            const out = Object.assign({}, p);
            if (typeof out.email === "string")
                out.email = out.email.trim().toLowerCase();
            if (typeof out.full_name === "string")
                out.full_name = out.full_name.trim();
            return out;
        },
        onSuccess: (data, { form, messageEl }) => {
            const asAny = data;
            const msg = (asAny && asAny.message) ||
                "Inscription réussie ! Vérifiez votre email pour confirmer et activer votre compte.";
            setMessage(messageEl, msg, "ok");
            if (asAny && asAny.access_token && asAny.user) {
                setTimeout(() => {
                    window.location.assign("/");
                }, 2000);
                return;
            }
            form.reset();
        },
    });
    // Mot de passe oublié
    bindFormSubmit({
        formSelector: SELECTORS.forgotForm,
        apiEndpoint: "/api/v1/auth/request-password-reset",
        transformPayload: (p) => {
            const out = Object.assign({}, p);
            if (typeof out.email === "string")
                out.email = out.email.trim().toLowerCase();
            return out;
        },
        onSuccess: (data, { form, messageEl }) => {
            setMessage(messageEl, data.message || "Un email de réinitialisation a été envoyé si le compte existe.", "ok");
            form.reset();
        },
    });
    // UI: afficher le bloc "mot de passe oublié"
    const forgotLink = document.querySelector("#forgot-link");
    const forgotContainer = document.querySelector("#forgot-container");
    if (forgotLink && forgotContainer) {
        forgotLink.addEventListener("click", (e) => {
            e.preventDefault();
            forgotContainer.style.display = "block";
            try {
                forgotContainer.scrollIntoView({ behavior: "smooth", block: "nearest" });
            }
            catch (_a) { }
        });
    }
    else {
        console.warn("Élément forgot-link ou forgot-container non trouvé");
    }
}
// --- Bootstrap ---
window.initializeAuthForms = initializeAuthForms;
document.addEventListener("DOMContentLoaded", initializeAuthForms);
