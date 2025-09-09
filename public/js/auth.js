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
                let errorMsg = error.message || "Une erreur est survenue.";
                if (errorMsg.includes("Utilisateur existe déjà")) {
                    errorMsg = "Cet email est déjà utilisé. Essayez de vous connecter ou réinitialisez votre mot de passe.";
                }
                setMessage(messageEl, errorMsg, "err");
                console.error(`Erreur lors de la soumission à ${options.apiEndpoint}:`, error);
            }
            finally {
                // Ne réactive le bouton qu'en cas d'erreur sans redirection
                if (!options.redirectUrl) {
                    submitBtn.disabled = false;
                }
            }
        }));
    });
}
/**
 * Initialise tous les formulaires d'authentification. Exportée pour les tests.
 */
function initializeAuthForms() {
    // --- Formulaire de Connexion ---
    bindFormSubmit({
        formSelector: SELECTORS.loginForm,
        apiEndpoint: "/api/v1/auth/login",
        // L'API attend 'email', le formulaire utilise 'email', donc pas de transformation nécessaire.
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
