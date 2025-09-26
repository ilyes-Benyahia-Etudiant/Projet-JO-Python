/**
 * reset_password.ts - Logique front pour la page de mise à jour du mot de passe.
 * Récupère le token dans l’URL, valide le formulaire et appelle l’API,
 * affiche des messages et redirige vers /auth en cas de succès.
 */

(function () {
  /**
   * Extrait un token depuis ?token=... ou depuis le hash (#access_token / #token / #code)
   */
  function getTokenFromUrl(): string {
    try {
      const qs = new URLSearchParams(window.location.search);
      let token = qs.get("token");
      if (token) return token || "";
      const raw = (window.location.hash || "").replace(/^#/, "");
      const hs = new URLSearchParams(raw);
      token = hs.get("access_token") || hs.get("token") || hs.get("code");
      return token || "";
    } catch {
      return "";
    }
  }

  /**
   * Affiche un message global en préservant le style serveur (.msg.ok/.msg.err).
   */
  function showMessage(type: "ok" | "error", text: string) {
    const css = type === "error" ? "err" : "ok";
    const card = document.querySelector<HTMLElement>(".card");
    let el = document.querySelector<HTMLElement>(".msg." + css);
    if (!el) {
      el = document.createElement("div");
      el.className = "msg " + css;
      if (card) card.prepend(el);
      else document.body.prepend(el);
    }
    el.textContent = text;
  }

  /**
   * Enveloppe fetch() – utilise window.Http.request si disponible.
   */
  function httpRequest(url: string, init?: RequestInit) {
    const w: any = window as any;
    if (w?.Http?.request) return w.Http.request(url, init);
    return fetch(url, init as RequestInit);
  }

  /**
   * Bind et traite la soumission du formulaire de mise à jour mot de passe.
   * Valide la présence du token et du nouveau mot de passe avant l’appel API.
   */
  function bindResetForm() {
    const form = document.getElementById("web-update-password-form") as HTMLFormElement | null;
    if (!form) return;

    const submitBtn = form.querySelector('button[type="submit"]') as HTMLButtonElement | null;

    form.addEventListener("submit", async (e) => {
      e.preventDefault();

      if (typeof form.reportValidity === "function" && !form.reportValidity()) {
        return;
      }

      const input = form.querySelector('input[name="new_password"]') as HTMLInputElement | null;
      const new_password = input?.value || "";
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
        if (submitBtn) submitBtn.disabled = true;

        const res = await httpRequest("/api/v1/auth/update-password", {
          method: "POST",
          headers: { "Content-Type": "application/json", "Accept": "application/json" },
          body: JSON.stringify({ token, new_password }),
        });

        let body: any = {};
        try { body = await res.json(); } catch {}

        if (!res.ok) {
          let msg = body?.detail || body?.message || "Erreur lors de la mise à jour du mot de passe";
          if (Array.isArray(body?.detail)) {
            msg = body.detail.map((d: any) => d?.msg).filter(Boolean).join(" / ") || msg;
          }
          showMessage("error", msg);
          return;
        }

        showMessage("ok", body?.message || "Mot de passe mis à jour");
        setTimeout(() => {
          window.location.assign("/auth?message=" + encodeURIComponent("Mot de passe mis à jour"));
        }, 500);
      } catch {
        showMessage("error", "Erreur réseau. Veuillez réessayer.");
      } finally {
        if (submitBtn) submitBtn.disabled = false;
      }
    });
  }

  // Bootstrap "safe"
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bindResetForm);
  } else {
    bindResetForm();
  }
})();