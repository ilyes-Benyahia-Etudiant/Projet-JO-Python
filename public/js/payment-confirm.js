(function () {
  try {
    const url = new URL(window.location.href);
    const sessionId = url.searchParams.get("session_id");
    const confirmed = url.searchParams.get("confirmed");

    if (sessionId && !confirmed) {
      fetch("/payments/confirm?session_id=" + encodeURIComponent(sessionId), {
        method: "GET",
        credentials: "include",
      })
        .then(function (res) {
          return res.json().catch(function () {
            return {};
          });
        })
        .then(function (data) {
          // Empêche les doubles appels
          url.searchParams.set("confirmed", "1");
          window.history.replaceState({}, "", url.toString());
          // Recharge pour afficher les nouveaux billets
          window.location.reload();
        })
        .catch(function (err) {
          console.error("Erreur confirmation paiement:", err);
        });
    }
  } catch (e) {
    console.error("Erreur script confirmation:", e);
  }
})();