"use strict";
// reset_password.ts - logique dédiée à la page de réinitialisation
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
(function () {
    function getTokenFromUrl() {
        try {
            const qs = new URLSearchParams(window.location.search);
            let token = qs.get("token");
            if (token)
                return token || "";
            const raw = (window.location.hash || "").replace(/^#/, "");
            const hs = new URLSearchParams(raw);
            token = hs.get("access_token") || hs.get("token") || hs.get("code");
            return token || "";
        }
        catch (_a) {
            return "";
        }
    }
    function showMessage(type, text) {
        const css = type === "error" ? "err" : "ok";
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
    function httpRequest(url, init) {
        var _a;
        const w = window;
        if ((_a = w === null || w === void 0 ? void 0 : w.Http) === null || _a === void 0 ? void 0 : _a.request)
            return w.Http.request(url, init);
        return fetch(url, init);
    }
    function bindResetForm() {
        const form = document.getElementById("web-update-password-form");
        if (!form)
            return;
        const submitBtn = form.querySelector('button[type="submit"]');
        form.addEventListener("submit", (e) => __awaiter(this, void 0, void 0, function* () {
            e.preventDefault();
            if (typeof form.reportValidity === "function" && !form.reportValidity()) {
                return;
            }
            const input = form.querySelector('input[name="new_password"]');
            const new_password = (input === null || input === void 0 ? void 0 : input.value) || "";
            const token = getTokenFromUrl();
            if (!token) {
                showMessage("error", "Lien invalide: token manquant.");
                return;
            }
            if (!new_password) {
                showMessage("error", "Veuillez saisir un nouveau mot de passe.");
                return;
            }
            try {
                if (submitBtn)
                    submitBtn.disabled = true;
                const res = yield httpRequest("/api/v1/auth/update-password", {
                    method: "POST",
                    headers: { "Content-Type": "application/json", "Accept": "application/json" },
                    body: JSON.stringify({ token, new_password }),
                });
                let body = {};
                try {
                    body = yield res.json();
                }
                catch (_a) { }
                if (!res.ok) {
                    let msg = (body === null || body === void 0 ? void 0 : body.detail) || (body === null || body === void 0 ? void 0 : body.message) || "Erreur lors de la mise à jour du mot de passe";
                    if (Array.isArray(body === null || body === void 0 ? void 0 : body.detail)) {
                        msg = body.detail.map((d) => d === null || d === void 0 ? void 0 : d.msg).filter(Boolean).join(" / ") || msg;
                    }
                    showMessage("error", msg);
                    return;
                }
                showMessage("ok", (body === null || body === void 0 ? void 0 : body.message) || "Mot de passe mis à jour");
                setTimeout(() => {
                    window.location.assign("/auth?message=" + encodeURIComponent("Mot de passe mis à jour"));
                }, 500);
            }
            catch (_b) {
                showMessage("error", "Erreur réseau. Veuillez réessayer.");
            }
            finally {
                if (submitBtn)
                    submitBtn.disabled = false;
            }
        }));
    }
    // Bootstrap "safe"
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", bindResetForm);
    }
    else {
        bindResetForm();
    }
})();
