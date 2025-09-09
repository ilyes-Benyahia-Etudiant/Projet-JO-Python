// Détecte le retour Supabase (hash dans l'URL) et affiche un message
document.addEventListener("DOMContentLoaded", () => {
  try {
    const hash = window.location.hash || "";
    const params = new URLSearchParams(hash.startsWith("#") ? hash.slice(1) : hash);
    const type = params.get("type"); // ex: "signup"
    const error = params.get("error") || params.get("error_description");
    const msgEl = document.getElementById("client-msg");

    if (!msgEl) return;

    if (error) {
      msgEl.textContent = error;
      msgEl.className = "msg err";
      (msgEl as HTMLElement).style.display = "block";
    } else if (type === "signup") {
      msgEl.textContent = "Votre email est confirmé. Vous pouvez maintenant vous connecter.";
      msgEl.className = "msg ok";
      (msgEl as HTMLElement).style.display = "block";
    }

    // Nettoyer le hash pour éviter de réafficher au rafraîchissement
    try {
      const url = new URL(window.location.href);
      url.hash = "";
      window.history.replaceState({}, "", url.toString());
    } catch {
      // no-op
    }
  } catch (e) {
    // Optionnel: log non bloquant
    console.error("Erreur de lecture du hash Supabase:", e);
  }
});