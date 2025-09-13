// Définition d'options typées pour la requête
type HttpMethod = "GET" | "POST" | "PUT" | "DELETE" | "PATCH";
type JsonRecord = Record<string, unknown>;

interface RequestOptions extends RequestInit {
    method?: HttpMethod;
    json?: JsonRecord | unknown;
    expectedStatus?: number | number[]; // Optionnel: valider le code de statut attendu
}

class Http {
    private static normalizeExpected(expected?: number | number[]): number[] {
        if (!expected) return [200];
        return Array.isArray(expected) ? expected : [expected];
    }

    private static buildInit(init?: RequestOptions): RequestInit {
        const headers = new Headers(init?.headers || {});
        // Ajout par défaut: JSON si le corps json est présent
        if (init?.json !== undefined) {
            if (!headers.has("Content-Type")) headers.set("Content-Type", "application/json");
            if (!headers.has("Accept")) headers.set("Accept", "application/json");
        }
        // Politique par défaut
        const base: RequestInit = {
            method: init?.method || "GET",
            credentials: init?.credentials ?? "same-origin",
            headers
        };
        // Corps JSON si fourni
        if (init?.json !== undefined) {
            base.body = JSON.stringify(init.json);
        } else if (init?.body !== undefined) {
            base.body = init.body;
        }
        // Recopie des autres options si besoin
        if (init?.signal) base.signal = init.signal;
        if (init?.mode) base.mode = init.mode;
        if (init?.cache) base.cache = init.cache;
        if (init?.redirect) base.redirect = init.redirect;
        if (init?.referrer) base.referrer = init.referrer;
        if (init?.referrerPolicy) base.referrerPolicy = init.referrerPolicy;
        if (init?.integrity) base.integrity = init.integrity;
        if (init?.keepalive) base.keepalive = init.keepalive;

        return base;
    }

    private static getCookie(name: string): string | null {
        if (typeof document === "undefined") return null;
        const cookies = document.cookie ? document.cookie.split("; ") : [];
        for (const c of cookies) {
            if (!c) continue;
            const [k, ...rest] = c.split("=");
            if (k === name) {
                try {
                    return decodeURIComponent(rest.join("="));
                } catch {
                    return rest.join("=");
                }
            }
        }
        return null;
    }

    private static getCsrfToken(): string | null {
        return this.getCookie("csrf_token");
    }

  private static mergeInit = (init: RequestInit = {}): RequestInit => {
    const headers = new Headers(init.headers || {});
    const method = ((init.method as string) || "GET").toUpperCase();

    // Injecte automatiquement le token CSRF pour les requêtes non-sûres
    if (method === "POST" || method === "PUT" || method === "PATCH" || method === "DELETE") {
      if (!headers.has("X-CSRF-Token")) {
        const token = Http.getCsrfToken();
        if (token) {
          headers.set("X-CSRF-Token", token);
        }
      }
    }

    return { ...init, headers, credentials: init.credentials ?? "same-origin" };
  };

  static request = (url: string, init: RequestInit = {}): Promise<Response> => {
    const finalInit = this.mergeInit(init);
    return fetch(url, finalInit);
  };

  static json = async <T = unknown>(url: string, init: RequestInit = {}): Promise<T> => {
    const res = await this.request(url, init);
    let data: any = undefined;
    try {
      data = await res.json();
    } catch {
      // ignore JSON parse errors; data stays undefined
    }
    if (!res.ok) {
      let msg = "";
      if (data && typeof data === "object") {
        msg = data.detail || data.message || "";
      }
      if (!msg) {
        try {
          msg = await res.text();
        } catch {
          // ignore
        }
      }
      throw new Error(msg || `HTTP ${res.status}`);
    }
    return data as T;
  };

  static getJson = <T = unknown>(url: string, init: RequestInit = {}): Promise<T> => {
    return this.json<T>(url, { ...init, method: "GET" });
  };

  static postJson = <T = unknown>(url: string, body?: unknown, init: RequestInit = {}): Promise<T> => {
    const headers = new Headers(init.headers || {});
    if (!headers.has("Content-Type")) headers.set("Content-Type", "application/json");
    return this.json<T>(url, {
      ...init,
      method: "POST",
      headers,
      body: body !== undefined ? JSON.stringify(body) : init.body,
    });
  };
}

// Expose global
// eslint-disable-next-line @typescript-eslint/no-explicit-any
(window as any).Http = Http;