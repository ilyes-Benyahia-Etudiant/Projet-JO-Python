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
                .then((res) => __awaiter(this, void 0, void 0, function* () {
                // Vider le panier côté client après confirmation OK
                try {
                    localStorage.removeItem("cart.v1");
                }
                catch (_a) { }
                url.searchParams.set("confirmed", "1");
                window.history.replaceState({}, "", url.toString());
                window.location.reload();
            }))
                .catch((err) => {
                console.error("Erreur confirmation paiement:", err);
            });
        }
    }
    catch (e) {
        console.error("Erreur script confirmation:", e);
    }
})();
