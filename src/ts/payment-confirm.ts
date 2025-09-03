(function () {
  try {
    const url = new URL(window.location.href);
    const sessionId = url.searchParams.get("session_id");
    const confirmed = url.searchParams.get("confirmed");

    if (sessionId && !confirmed) {
      Http.request("/payments/confirm?session_id=" + encodeURIComponent(sessionId), {
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