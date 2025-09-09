"use strict";
document.addEventListener("DOMContentLoaded", () => {
    // --- Sélecteurs centralisés ---
    const SELECTORS = {
        loginForm: "#web-login-form",
        signupForm: "#web-signup-form",
        forgotForm: "#web-forgot-form",
        modalSignupForm: "#modal-signup-form",
    };
    class AuthManager {
        constructor() {
            this.init();
        }
        init() {
            this.bindLoginForm();
            this.bindSignupForm();
            this.bindForgotForm();
            this.bindModalSignup();
        }
        // --- Méthodes de binding spécifiques ---
        bindLoginForm() {
            this.handleFormSubmit({
                formSelector: SELECTORS.loginForm,
                apiEndpoint: "/api/v1/auth/login",
                getPayload: (formData) => ({
                    email: formData.get("email"),
                    password: formData.get("password"),
                }),
                onSuccess: (data) => {
                    const targetUrl = data.user.role === "admin" ? "/admin" : "/session";
                    window.location.href = targetUrl;
                },
            });
        }
        bindSignupForm() {
            this.handleFormSubmit({
                formSelector: SELECTORS.signupForm,
                apiEndpoint: "/api/v1/auth/signup",
                getPayload: (formData) => ({
                    email: formData.get("email"),
                    password: formData.get("password"),
                    full_name: formData.get("full_name"),
                }),
                onSuccess: (data, formElements) => {
                    const message = data.message || "Inscription réussie, vérifiez votre email.";
                    this.setMsg(formElements.msgEl, message, "ok");
                    formElements.form.reset();
                },
            });
        }
        bindForgotForm() {
            this.handleFormSubmit({
                formSelector: SELECTORS.forgotForm,
                apiEndpoint: "/api/v1/auth/request-password-reset",
                getPayload: (formData) => ({
                    email: formData.get("email"),
                }),
                onSuccess: (data, formElements) => {
                    const message = data.message || "Email de réinitialisation envoyé.";
                    this.setMsg(formElements.msgEl, message, "ok");
                    formElements.form.reset();
                },
            });
        }
        bindModalSignup() {
            this.handleFormSubmit({
                formSelector: SELECTORS.modalSignupForm,
                apiEndpoint: "/api/v1/auth/signup",
                getPayload: (formData) => ({
                    email: formData.get("email"),
                    password: formData.get("password"),
                    full_name: formData.get("full_name"),
                }),
                onSuccess: (data, formElements) => {
                    const message = data.message || "Inscription réussie !";
                    this.setMsg(formElements.msgEl, message, "ok");
                    setTimeout(() => {
                        // Optionnel: fermer la modale ou rediriger
                    }, 2000);
                },
            });
        }
        // --- Logique générique de soumission de formulaire ---
        async handleFormSubmit(options) {
            const form = document.querySelector(options.formSelector);
            if (!form)
                return;
            const submitBtn = form.querySelector("button[type=submit]");
            const msgEl = form.querySelector(".form-msg");
            form.addEventListener("submit", async (e) => {
                e.preventDefault();
                if (!submitBtn)
                    return;
                const formData = new FormData(form);
                const payload = options.getPayload(formData);
                // Validation simple
                if (Object.values(payload).some(val => !val)) {
                    this.setMsg(msgEl, "Veuillez remplir tous les champs.", "err");
                    return;
                }
                try {
                    submitBtn.disabled = true;
                    this.setMsg(msgEl, "Envoi en cours...", "ok");
                    const data = await Http.postJson(options.apiEndpoint, payload);
                    this.setMsg(msgEl, "Succès !", "ok");
                    options.onSuccess(data, { form, submitBtn, msgEl });
                }
                catch (err) {
                    const errorMsg = (err === null || err === void 0 ? void 0 : err.message) || "Une erreur est survenue.";
                    this.setMsg(msgEl, errorMsg, "err");
                }
                finally {
                    submitBtn.disabled = false;
                }
            });
        }
        // --- Utilitaire d'affichage de message ---
        setMsg(element, msg, type) {
            if (!element)
                return;
            element.textContent = msg;
            element.className = `form-msg ${type}`;
        }
    }
    // --- Initialisation ---
    new AuthManager();
});
//# sourceMappingURL=auth.js.map