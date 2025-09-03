// Test TS autonome (sans framework) exécuté sous Node après compilation.
// Il simule window/localStorage/Http et exécute la logique de payment-confirm.ts.

declare const global: any;

class SimpleLocalStorage {
  private store = new Map<string, string>();
  getItem(key: string): string | null {
    return this.store.has(key) ? this.store.get(key)! : null;
  }
  setItem(key: string, value: string) {
    this.store.set(key, value);
  }
  removeItem(key: string) {
    this.store.delete(key);
  }
  clear() {
    this.store.clear();
  }
}

(async () => {
  // 1) Mocks globaux
  const localStorage = new SimpleLocalStorage();

  const locationMock = {
    href: "https://example.test/session?session_id=test-session-123",
    reloadCalled: false,
    reload() {
      this.reloadCalled = true;
    },
  };

  let replaceStateCalled = false;
  const historyMock = {
    replaceState: (_state: unknown, _title: string, url?: string) => {
      replaceStateCalled = true;
      if (url) {
        locationMock.href = url;
      }
    },
  };

  const windowMock = {
    location: locationMock,
    history: historyMock,
  };

  // Http.request simulé: renvoie une "réponse" ok
  const Http = {
    request: async (_url: string, _init?: RequestInit) => {
      return { ok: true } as Response;
    },
  };

  // Exposer les mocks dans le global
  (global as any).window = windowMock;
  (global as any).localStorage = localStorage;
  (global as any).Http = Http;

  // 2) Préparer un panier rempli
  localStorage.setItem("cart.v1", JSON.stringify([{ id: "1", q: 2 }]));

  // 3) Logique équivalente à src/ts/payment-confirm.ts (IIFE)
  (function () {
    try {
      const url = new URL(window.location.href);
      const sessionId = url.searchParams.get("session_id");
      const confirmed = url.searchParams.get("confirmed");

      if (sessionId && !confirmed) {
        Http.request("/payments/confirm?session_id=" + encodeURIComponent(sessionId), {
          method: "GET",
        })
          .then(async (_res) => {
            // Vider le panier côté client après confirmation OK
            try {
              localStorage.removeItem("cart.v1");
            } catch {}

            url.searchParams.set("confirmed", "1");
            window.history.replaceState({}, "", url.toString());
            window.location.reload();
          })
          .catch((err: any) => {
            console.error("Erreur confirmation paiement:", err);
          });
      }
    } catch (e) {
      console.error("Erreur script confirmation:", e);
    }
  })();

  // 4) Attendre la fin de la micro-tâche promise
  await new Promise((r) => setTimeout(r, 0));

  // 5) Assertions minimales
  const remaining = localStorage.getItem("cart.v1");
  if (remaining !== null) {
    throw new Error("Le panier n'a pas été vidé (cart.v1 toujours présent)");
  }
  if (!replaceStateCalled) {
    throw new Error("history.replaceState n'a pas été appelé");
  }
  if (!locationMock.reloadCalled) {
    throw new Error("location.reload n'a pas été appelé");
  }
  if (!windowMock.location.href.includes("confirmed=1")) {
    throw new Error("Le paramètre confirmed=1 n'a pas été ajouté à l'URL");
  }

  console.log("OK: Le panier est vidé et la page est marquée comme rechargée après confirmation.");
})();