document.addEventListener("DOMContentLoaded", () => {
  // 1) Si on revient de Supabase avec un hash (#access_token&type=recovery ...),
  //    on poste le token au backend pour poser les cookies puis on navigue vers /auth/reset.
  try {
    const hash = window.location.hash || "";
    if (hash.startsWith("#")) {
      const params = new URLSearchParams(hash.slice(1));
      const type = params.get("type");
      const accessToken = params.get("access_token");

      // Ajout: confirmation d’inscription => redirection vers /auth avec message
      if (type === "signup") {
        // Nettoyer l’URL (on retire le token du hash)
        history.replaceState({}, "", window.location.pathname + window.location.search);
        // Rediriger vers la page de connexion avec un message de succès
        window.location.href = "/auth?message=Votre%20compte%20a%20%C3%A9t%C3%A9%20confirm%C3%A9%2C%20vous%20pouvez%20vous%20connecter";
        return;
      }

      if (type === "recovery" && accessToken) {
        // Utiliser fetch pour transmettre en JSON proprement
        fetch("/auth/recover/session", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ access_token: accessToken })
        })
        .then(res => {
          // Quoi qu'il arrive, nettoyer le hash pour éviter de le conserver
          history.replaceState({}, "", window.location.pathname + window.location.search);
          if (res.redirected) {
            window.location.href = res.url;
          } else if (res.ok) {
            window.location.href = "/auth/reset";
          }
        })
        .catch(() => {
          history.replaceState({}, "", window.location.pathname + window.location.search);
        });
      }
    }
  } catch (e) {
    console.warn("Erreur parsing hash Supabase:", e);
  }

  // 2) Lien "Mot de passe oublié ?" qui utilise l'email du formulaire de connexion
  const forgotLink = document.getElementById("forgot-link");
  if (forgotLink) {
    forgotLink.addEventListener("click", (e) => {
      e.preventDefault();
      const emailInput = document.querySelector('form[action="/auth/login"] input[name="email"]') ||
                         document.getElementById("login-email");
      const email = (emailInput && emailInput.value || "").trim();
      if (!email) {
        if (emailInput) emailInput.focus();
        alert("Veuillez saisir votre email dans le formulaire de connexion.");
        return;
      }
      // POST traditionnel via formulaire caché pour suivre la redirection serveur
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
  }

  // 3) Helpers UI pour messages
  function setMsg(el, text, kind = "err") {
    if (!el) return;
    el.textContent = text || "";
    el.classList.remove("ok", "err");
    el.classList.add(kind === "ok" ? "ok" : "err");
    el.style.display = text ? "" : "none";
    el.setAttribute("role", "alert");
  }

  // 4) Inscription - Modale (#register-form) pour Accueil/Billetterie
  const modalRegisterForm = document.getElementById("register-form");
  if (modalRegisterForm) {
    const msgEl = document.getElementById("modal-signup-msg");
    const btn = modalRegisterForm.querySelector("#modal-btn-signup");

    modalRegisterForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const full_name = (document.getElementById("modal-signup-name")?.value || "").trim();
      const email = (document.getElementById("modal-signup-email")?.value || "").trim();
      const password = (document.getElementById("modal-signup-password")?.value || "").trim();
      const password2 = (document.getElementById("modal-signup-password2")?.value || "").trim();

      if (password !== password2) {
        setMsg(msgEl, "Les mots de passe ne correspondent pas", "err");
        return;
      }
      if (!email || !password || !full_name) {
        setMsg(msgEl, "Veuillez remplir tous les champs requis", "err");
        return;
      }

      try {
        btn && (btn.disabled = true);
        setMsg(msgEl, "Inscription en cours...", "ok");

        const resp = await fetch("/api/v1/auth/signup", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password, full_name }),
        });

        if (resp.ok) {
          const data = await resp.json().catch(() => ({}));
          const message = data?.message || "Inscription réussie, vérifiez votre email";
          setMsg(msgEl, message, "ok");
        } else {
          let err = "Erreur d'inscription";
          try {
            const j = await resp.json();
            err = j?.detail || j?.message || err;
          } catch (_) {}
          setMsg(msgEl, err, "err");
        }
      } catch (ex) {
        setMsg(msgEl, "Erreur réseau, veuillez réessayer", "err");
      } finally {
        btn && (btn.disabled = false);
      }
    });
  }

  // 5) Inscription - Page /auth (form[action="/auth/signup"])
  const webSignupForm = document.querySelector('form[action="/auth/signup"]');
  if (webSignupForm) {
    // Crée une zone de message si absente
    let webMsg = webSignupForm.querySelector(".msg.auth-signup");
    if (!webMsg) {
      webMsg = document.createElement("div");
      webMsg.className = "msg auth-signup";
      webMsg.style.display = "none";
      webSignupForm.insertBefore(webMsg, webSignupForm.firstChild);
    }
    const btn = webSignupForm.querySelector('button[type="submit"]');

    webSignupForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const formData = new FormData(webSignupForm);
      const email = (formData.get("email") || "").toString().trim();
      const password = (formData.get("password") || "").toString().trim();
      const full_name = (formData.get("full_name") || "").toString().trim();

      if (!email || !password || !full_name) {
        setMsg(webMsg, "Veuillez remplir tous les champs requis", "err");
        return;
      }

      try {
        btn && (btn.disabled = true);
        setMsg(webMsg, "Inscription en cours...", "ok");

        const resp = await fetch("/api/v1/auth/signup", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password, full_name }),
        });

        if (resp.ok) {
          const data = await resp.json().catch(() => ({}));
          const message = data?.message || "Inscription réussie, vérifiez votre email";
          setMsg(webMsg, message, "ok");
        } else {
          let err = "Erreur d'inscription";
          try {
            const j = await resp.json();
            err = j?.detail || j?.message || err;
          } catch (_) {}
          setMsg(webMsg, err, "err");
        }
      } catch (ex) {
        setMsg(webMsg, "Erreur réseau, veuillez réessayer", "err");
      } finally {
        btn && (btn.disabled = false);
      }
    });
  }
});