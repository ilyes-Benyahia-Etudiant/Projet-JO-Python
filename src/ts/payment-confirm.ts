/**
 * payment-confirm.ts - Confirmation de paiement Stripe en “background”.
 * Si la page contient ?session_id et pas encore ?confirmed=1 :
 * - appelle l’API /payments/confirm
 * - vide le panier client
 * - remplace l’URL avec confirmed=1 et reload pour rafraîchir la vue
 */
(function () {
  try {
    const url = new URL(window.location.href);
    const sessionId = url.searchParams.get("session_id");
    const confirmed = url.searchParams.get("confirmed");

    if (sessionId && !confirmed) {
      Http.request("/api/v1/payments/confirm?session_id=" + encodeURIComponent(sessionId), {
        method: "GET"
      })
        .then(async (res) => {
          // Vider le panier côté client après confirmation OK
          try { localStorage.removeItem("cart.v1"); } catch {}

          url.searchParams.set("confirmed", "1");
          window.history.replaceState({}, "", url.toString());
          window.location.reload();
        })
        .catch((err) => {
          console.error("Erreur confirmation paiement:", err);
        });
    }
  } catch (e) {
    console.error("Erreur script confirmation:", e);
  }
})();