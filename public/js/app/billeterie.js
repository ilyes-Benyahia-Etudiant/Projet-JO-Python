// Gestion de la sélection d'événement et enrichissement des offres
(function () {
  const STORAGE_KEY = "selectedEvent.v1";

  function showMessage(type, text) {
    const el = document.getElementById("client-msg");
    if (!el) return;
    el.textContent = text || "";
    el.className = "msg " + (type === "warn" ? "warn" : "info");
    el.style.display = "block";
  }

  function saveSelected(ev) {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(ev)); } catch {}
  }
  function loadSelected() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || "null"); } catch { return null; }
  }

  function markSelectedCard(evId) {
    document.querySelectorAll(".event-card.selectable").forEach((card) => {
      const id = card.getAttribute("data-ev-id");
      card.classList.toggle("selected", !!evId && id === evId);
    });
  }

  function propagateToOfferButtons(ev) {
    document.querySelectorAll(".btn-add-to-cart").forEach((btn) => {
      btn.dataset.evId = ev?.id || "";
      btn.dataset.evNom = ev?.nom || "";
      btn.dataset.evType = ev?.type || "";
      btn.dataset.evDate = ev?.date || "";
    });
  }

  function onSelectCard(card) {
    const ev = {
      id: card.getAttribute("data-ev-id") || "",
      nom: card.getAttribute("data-ev-nom") || "",
      type: card.getAttribute("data-ev-type") || "",
      date: card.getAttribute("data-ev-date") || "",
    };
    if (!ev.id) return;
    saveSelected(ev);
    markSelectedCard(ev.id);
    propagateToOfferButtons(ev);
    showMessage("info", `Événement sélectionné: ${ev.nom} (${ev.type}) • ${ev.date}`);
  }

  document.addEventListener("DOMContentLoaded", () => {
    const existing = loadSelected();
    if (existing?.id) {
      markSelectedCard(existing.id);
      propagateToOfferButtons(existing);
    }

    document.querySelectorAll(".event-card.selectable").forEach((card) => {
      const btn = card.querySelector(".event-select-btn");
      const handler = () => onSelectCard(card);
      if (btn) btn.addEventListener("click", handler);
      else card.addEventListener("click", handler);
    });

    // Intercepter le clic sur "Connexion" et l'icône panier pour rediriger selon l'état de connexion
    document.addEventListener("click", async (e) => {
      // Connexion
      const loginLink = e.target.closest('a.btn-login[href="/auth"]');
      if (loginLink) {
        e.preventDefault();
        try {
          const res = await fetch("/api/v1/auth/me", { credentials: "include" });
          if (res.ok) {
            window.location.href = "/session";
          } else {
            window.location.href = "/auth";
          }
        } catch {
          window.location.href = "/auth";
        }
        return;
      }

      // Icône panier (billeterie)
      const cartLink = e.target.closest('a.btn-cart[href="/session"]');
      if (cartLink) {
        e.preventDefault();
        try {
          const res = await fetch("/api/v1/auth/me", { credentials: "include" });
          if (res.ok) {
            window.location.href = "/session";
          } else {
            window.location.href = "/auth";
          }
        } catch {
          window.location.href = "/auth";
        }
        return;
      }

      // [FIX] Garde-fou: exiger la sélection d’un événement avant l’ajout au panier
      const addBtn = e.target.closest(".btn-add-to-cart");
      if (addBtn) {
        const evId = addBtn.getAttribute("data-ev-id");
        if (!evId) {
          e.preventDefault();
          showMessage("warn", "Sélectionnez d’abord un événement, puis choisissez votre offre.");
          return;
        }
        // Feedback visuel
        addBtn.classList.add("selected");
        window.setTimeout(() => addBtn.classList.remove("selected"), 500);
      }
    });
  });
})(); // fermeture correcte de l’IIFE
