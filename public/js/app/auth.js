"use strict";
document.addEventListener("DOMContentLoaded", () => {
    class AuthUI {
        constructor() {
            var _a, _b;
            this.modalRegisterForm = document.getElementById("register-form");
            this.modalMsgEl = document.getElementById("modal-signup-msg");
            this.modalBtn = ((_a = this.modalRegisterForm) === null || _a === void 0 ? void 0 : _a.querySelector("#modal-btn-signup")) || null;
            this.webSignupForm = document.querySelector('form[action="/auth/signup"]');
            this.webMsg = null;
            this.webBtn = ((_b = this.webSignupForm) === null || _b === void 0 ? void 0 : _b.querySelector('button[type="submit"]')) || null;
            this.setMsg = (el, text, kind = "err") => {
                if (!el)
                    return;
                el.textContent = text || "";
                el.classList.remove("ok", "err");
                el.classList.add(kind === "ok" ? "ok" : "err");
                el.style.display = text ? "" : "none";
                el.setAttribute("role", "alert");
            };
            this.handleSupabaseHash = async () => {
                try {
                    const hash = window.location.hash || "";
                    if (!hash.startsWith("#"))
                        return;
                    const params = new URLSearchParams(hash.slice(1));
                    const type = params.get("type");
                    const accessToken = params.get("access_token");
                    if (type === "signup") {
                        history.replaceState({}, "", window.location.pathname + window.location.search);
                        window.location.href = "/auth?message=Votre%20compte%20a%20%C3%A9t%C3%A9%20confirm%C3%A9%2C%20vous%20pouvez%20vous%20connecter";
                        return;
                    }
                    if (type === "recovery" && accessToken) {
                        const res = await Http.request("/auth/recover/session", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ access_token: accessToken }),
                        }).catch(() => null);
                        history.replaceState({}, "", window.location.pathname + window.location.search);
                        if (res && res.redirected) {
                            window.location.href = res.url;
                        }
                        else if (res && res.ok) {
                            window.location.href = "/auth/reset";
                        }
                    }
                }
                catch (e) {
                    console.warn("Erreur parsing hash Supabase:", e);
                }
            };
            this.bindForgotLink = () => {
                const forgotLink = document.getElementById("forgot-link");
                if (!forgotLink)
                    return;
                forgotLink.addEventListener("click", (e) => {
                    e.preventDefault();
                    const emailInputA = document.querySelector('form[action="/auth/login"] input[name="email"]');
                    const emailInputB = document.getElementById("login-email");
                    const emailEl = emailInputA || emailInputB;
                    const email = ((emailEl === null || emailEl === void 0 ? void 0 : emailEl.value) || "").trim();
                    if (!email) {
                        emailEl === null || emailEl === void 0 ? void 0 : emailEl.focus();
                        alert("Veuillez saisir votre email dans le formulaire de connexion.");
                        return;
                    }
                    const form = document.createElement("form");
                    form.method = "POST";
                    form.action = "/auth/forgot";
                    const input = document.createElement("input");
                    input.type = "hidden";
                    input.name = "email";
                    input.value = email;
                    form.appendChild(input);
                    document.body.appendChild(form);
                    form.submit();
                });
            };
            this.bindModalSignup = () => {
                if (!this.modalRegisterForm)
                    return;
                this.modalRegisterForm.addEventListener("submit", async (e) => {
                    var _a, _b, _c, _d;
                    e.preventDefault();
                    const full_name = ((_a = document.getElementById("modal-signup-name")) === null || _a === void 0 ? void 0 : _a.value.trim()) || "";
                    const email = ((_b = document.getElementById("modal-signup-email")) === null || _b === void 0 ? void 0 : _b.value.trim()) || "";
                    const password = ((_c = document.getElementById("modal-signup-password")) === null || _c === void 0 ? void 0 : _c.value.trim()) || "";
                    const password2 = ((_d = document.getElementById("modal-signup-password2")) === null || _d === void 0 ? void 0 : _d.value.trim()) || "";
                    if (password !== password2) {
                        this.setMsg(this.modalMsgEl, "Les mots de passe ne correspondent pas", "err");
                        return;
                    }
                    if (!email || !password || !full_name) {
                        this.setMsg(this.modalMsgEl, "Veuillez remplir tous les champs requis", "err");
                        return;
                    }
                    try {
                        if (this.modalBtn)
                            this.modalBtn.disabled = true;
                        this.setMsg(this.modalMsgEl, "Inscription en cours...", "ok");
                        const data = await Http.postJson("/api/v1/auth/signup", {
                            email, password, full_name,
                        });
                        const message = (data === null || data === void 0 ? void 0 : data.message) || "Inscription réussie, vérifiez votre email";
                        this.setMsg(this.modalMsgEl, message, "ok");
                    }
                    catch (err) {
                        const msg = (err === null || err === void 0 ? void 0 : err.message) || "Erreur d'inscription";
                        this.setMsg(this.modalMsgEl, msg, "err");
                    }
                    finally {
                        if (this.modalBtn)
                            this.modalBtn.disabled = false;
                    }
                });
            };
            this.ensureWebMsg = () => {
                if (!this.webSignupForm)
                    return;
                let webMsg = this.webSignupForm.querySelector(".msg.auth-signup");
                if (!webMsg) {
                    webMsg = document.createElement("div");
                    webMsg.className = "msg auth-signup";
                    webMsg.style.display = "none";
                    this.webSignupForm.insertBefore(webMsg, this.webSignupForm.firstChild);
                }
                this.webMsg = webMsg;
            };
            this.bindWebSignup = () => {
                if (!this.webSignupForm)
                    return;
                this.ensureWebMsg();
                this.webSignupForm.addEventListener("submit", async (e) => {
                    e.preventDefault();
                    if (!this.webSignupForm)
                        return;
                    const formData = new FormData(this.webSignupForm);
                    const email = (formData.get("email") || "").toString().trim();
                    const password = (formData.get("password") || "").toString().trim();
                    const full_name = (formData.get("full_name") || "").toString().trim();
                    const admin_code = (formData.get("admin_code") || "").toString().trim();
                    if (!email || !password || !full_name) {
                        this.setMsg(this.webMsg, "Veuillez remplir tous les champs requis", "err");
                        return;
                    }
                    try {
                        if (this.webBtn)
                            this.webBtn.disabled = true;
                        this.setMsg(this.webMsg, "Inscription en cours...", "ok");
                        const data = await Http.postJson("/api/v1/auth/signup", {
                            email, password, full_name, admin_code: admin_code || undefined,
                        });
                        const message = (data === null || data === void 0 ? void 0 : data.message) || "Inscription réussie, vérifiez votre email";
                        this.setMsg(this.webMsg, message, "ok");
                    }
                    catch (err) {
                        const msg = (err === null || err === void 0 ? void 0 : err.message) || "Erreur d'inscription";
                        this.setMsg(this.webMsg, msg, "err");
                    }
                    finally {
                        if (this.webBtn)
                            this.webBtn.disabled = false;
                    }
                });
            };
            this.handleSupabaseHash().catch(() => void 0);
            this.bindForgotLink();
            this.bindModalSignup();
            this.bindWebSignup();
        }
    }
    new AuthUI();
});
//# sourceMappingURL=auth.js.map