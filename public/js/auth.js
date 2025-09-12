"use strict";
// --- Type Definitions ---
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
// --- Constantes ---
const SELECTORS = {
    loginForm: "#web-login-form",
    signupForm: "#web-signup-form",
    forgotForm: "#web-forgot-form",
};
// --- Utilitaires DOM ---
function setMessage(element, msg, type) {
    if (!element)
        return;
    element.textContent = msg;
    element.className = `message-area ${type}`; // Classe cohérente pour les messages
}
// Ajout: message global (bandeau .msg ok/err en haut de la carte)
function showGlobalMessage(type, text) {
    const card = document.querySelector(".card");
    let el = document.querySelector(".msg." + (type === "error" ? "err" : "ok"));
    if (!el) {
        el = document.createElement("div");
        el.className = "msg " + (type === "error" ? "err" : "ok");
        if (card)
            card.prepend(el);
        else
            document.body.prepend(el);
    }
    el.textContent = text;
}
// Ajout: extraction du token depuis query string ou fragment
function getTokenFromUrl() {
    try {
        const qs = new URLSearchParams(window.location.search);
        let token = qs.get("token");
        if (token)
            return token;
        const hash = (window.location.hash || "").replace(/^#/, "");
        const hs = new URLSearchParams(hash);
        token = hs.get("access_token") || hs.get("token") || hs.get("code");
        return token || "";
    }
    catch (_a) {
        return "";
    }
}
// --- Logique principale ---
/**
 * Lie un gestionnaire de soumission à un formulaire pour les appels API.
 * Envoie les données en tant que JSON.
 */
function bindFormSubmit(options) {
    return __awaiter(this, void 0, void 0, function* () {
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
            const formData = new FormData(form);
            // Correction : Remplacer Object.fromEntries par une boucle forEach
            const payload = {};
            formData.forEach((value, key) => {
                payload[key] = value;
            });
            if (options.transformPayload) {
                // Note: la transformation se fait maintenant sur l'objet 'payload'
                Object.assign(payload, options.transformPayload(payload));
            }
            try {
                submitBtn.disabled = true;
                setMessage(messageEl, "Envoi en cours...", "ok");
                const response = yield window.Http.request(options.apiEndpoint, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    },
                    body: JSON.stringify(payload),
                });
                const responseData = yield response.json();
                if (!response.ok) {
                    const errorMessage = responseData.detail || `Erreur HTTP ${response.status}`;
                    throw new Error(errorMessage);
                }
                const data = responseData;
                setMessage(messageEl, (typeof data === 'object' && data && 'message' in data
                    ? data.message || "Opération réussie !"
                    : "Opération réussie !"), "ok");
                if (options.onSuccess) {
                    options.onSuccess(data, { form, submitBtn, messageEl });
                }
                if (options.redirectUrl) {
                    const url = typeof options.redirectUrl === 'function' ? options.redirectUrl(data) : options.redirectUrl;
                    window.location.assign(url);
                }
            }
            catch (error) {
                // Réactiver le bouton en cas d'échec
                submitBtn.disabled = false;
                let errorMsg = error.message || "Une erreur est survenue.";
                if (errorMsg.includes("Utilisateur existe déjà")) {
                    errorMsg = "Cet email est déjà utilisé. Essayez de vous connecter ou réinitialisez votre mot de passe.";
                }
                setMessage(messageEl, errorMsg, "err");
                console.error(`Erreur lors de la soumission à ${options.apiEndpoint}:`, error);
            } finally {
                if (!options.redirectUrl) {
                    submitBtn.disabled = false;
                }
            }
        }));
    });
}
// Ajout: lecture du hash de confirmation (ex: #type=signup&...)
// Affiche dans #client-msg et nettoie le hash.
function handleAuthConfirmationFromHash() {
    try {
        const msgEl = document.getElementById("client-msg");
        if (!msgEl)
            return;
        const raw = window.location.hash || "";
        const params = new URLSearchParams(raw.startsWith("#") ? raw.slice(1) : raw);
        const type = params.get("type");
        const error = params.get("error") || params.get("error_description");
        if (error) {
            msgEl.textContent = error;
            msgEl.className = "msg err";
            msgEl.style.display = "block";
        }
        else if (type === "signup") {
            msgEl.textContent = "Votre email est confirmé. Vous pouvez maintenant vous connecter.";
            msgEl.className = "msg ok";
            msgEl.style.display = "block";
        }
        // Nettoyage du hash
        try {
            const url = new URL(window.location.href);
            url.hash = "";
            window.history.replaceState({}, "", url.toString());
        }
        catch (_a) {
            // no-op
        }
    }
    catch (e) {
        console.error("Erreur de lecture du hash:", e);
    }
}
// Ajout: support du formulaire de réinitialisation de mot de passe (#web-update-password-form)
function initializeResetPasswordForm() {
    const form = document.getElementById("web-update-password-form");
    if (!form)
        return;
    form.addEventListener("submit", (e) => __awaiter(this, void 0, void 0, function* () {
        e.preventDefault();
        const newPasswordInput = form.querySelector('input[name="new_password"]');
        const new_password = newPasswordInput ? newPasswordInput.value : "";
        const token = getTokenFromUrl();
        if (!token) {
            showGlobalMessage("error", "Lien invalide: token manquant.");
            return;
        }
        if (!new_password) {
            showGlobalMessage("error", "Veuillez saisir un nouveau mot de passe.");
            return;
        }
        try {
            const res = yield window.Http.request("/api/v1/auth/update-password", {
                method: "POST",
                headers: { "Content-Type": "application/json", "Accept": "application/json" },
                body: JSON.stringify({ token, new_password }),
            });
            let body = undefined;
            try {
                body = yield res.json();
            }
            catch (_a) { }
            if (!res.ok) {
                const msg = (body && (body.detail || body.message)) || "Erreur lors de la mise à jour du mot de passe";
                showGlobalMessage("error", msg);
                return;
            }
            showGlobalMessage("ok", (body && body.message) || "Mot de passe mis à jour");
            setTimeout(() => {
                window.location.assign("/auth?message=" + encodeURIComponent("Mot de passe mis à jour"));
            }, 500);
        }
        catch (err) {
            showGlobalMessage("error", "Erreur réseau. Veuillez réessayer.");
        }
    }));
}
/**
 * Initialise tous les formulaires d'authentification. Exportée pour les tests.
 */
function initializeAuthForms() {
    // Ajout: gérer la confirmation par hash si présent (page /auth)
    handleAuthConfirmationFromHash();
    // --- Formulaire de Connexion ---
    bindFormSubmit({
        formSelector: SELECTORS.loginForm,
        apiEndpoint: "/api/v1/auth/login",
        redirectUrl: (data) => (data.user.role === "admin" ? "/admin" : "/session"),
    });
    // --- Formulaire d'Inscription ---
    bindFormSubmit({
        formSelector: SELECTORS.signupForm,
        apiEndpoint: "/api/v1/auth/signup",
        onSuccess: (data, { form, messageEl }) => {
            const asAny = data;
            let msg = (asAny && asAny.message) || "Inscription réussie ! Vérifiez votre email pour confirmer et activez votre compte.";
            setMessage(messageEl, msg, "ok");
            if (asAny && asAny.access_token && asAny.user) {
                // Délai pour que le message soit visible avant redirection
                setTimeout(() => {
                    window.location.assign("/");
                }, 2000);
                return;
            }
            form.reset();
        },
    });
    bindFormSubmit({
        formSelector: SELECTORS.forgotForm,
        apiEndpoint: "/api/v1/auth/request-password-reset",
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
            console.log("Formulaire mot de passe oublié affiché");
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
// --- Initialisation automatique au chargement de la page ---
window.initializeAuthForms = initializeAuthForms;
document.addEventListener("DOMContentLoaded", initializeAuthForms);
