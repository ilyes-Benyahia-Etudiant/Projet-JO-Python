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
});