"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
// Script minimal pour compter les billets via API Python et updater la pastille
document.addEventListener("DOMContentLoaded", () => {
    // Fonction pour mettre à jour la pastille
    const setBadge = (el, count) => {
        if (!el)
            return;
        if (count > 0) {
            el.textContent = String(count);
            el.style.display = "inline-flex";
            el.setAttribute("aria-label", `Nombre de billets: ${count}`);
        }
        else {
            el.textContent = "0";
            el.style.display = "none";
            el.setAttribute("aria-label", "Aucun billet");
        }
    };
    // Fonction pour fetcher le count depuis l'API Python (avec retry et logs)
    const refreshTicketsCount = (...args_1) => __awaiter(void 0, [...args_1], void 0, function* (retry = 0) {
        var _a;
        try {
            const res = yield fetch("/api/v1/tickets/count", { credentials: "include" });
            console.log("Statut de la réponse API:", res.status); // Log pour déboguer
            if (!res.ok) {
                throw new Error(`Erreur API: ${res.status} - ${res.statusText}`);
            }
            const data = yield res.json();
            const count = Number((_a = data === null || data === void 0 ? void 0 : data.count) !== null && _a !== void 0 ? _a : 0);
            console.log("Nombre de billets reçu de la DB:", count); // Log du count
            setBadge(document.getElementById("tickets-count-pill"), count);
            // Optionnel: Si tu as un autre badge, ajoute-le ici
            // setBadge(document.getElementById("tickets-badge") as HTMLElement | null, count);
        }
        catch (error) {
            console.error("Erreur lors du fetch du count des billets:", error);
            if (retry < 2) {
                console.log("Retry du fetch...");
                setTimeout(() => refreshTicketsCount(retry + 1), 1000); // Retry après 1s
            }
            else {
                setBadge(document.getElementById("tickets-count-pill"), 0);
            }
        }
    });
    // Appels initiaux
    refreshTicketsCount(); // Au chargement de la page
    // Refresh quand la page redevient visible
    document.addEventListener("visibilitychange", () => {
        if (document.visibilityState === "visible")
            refreshTicketsCount();
    });
    // Refresh après paiement réussi (vérifie params URL)
    const params = new URLSearchParams(window.location.search);
    if (params.get("payment") === "success" || params.get("redirect_status") === "succeeded") {
        refreshTicketsCount();
    }
    // Optionnel: Si tu as d'autres événements (ex: après ajout de billet), ajoute un event custom
    // document.addEventListener("ticketsUpdated", refreshTicketsCount);
    // Pour déclencher: dispatchEvent(new Event("ticketsUpdated")) dans d'autres scripts
});
