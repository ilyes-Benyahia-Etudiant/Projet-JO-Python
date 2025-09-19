// --- Types ---

interface ApiMessageResponse {
  message?: string;
  detail?: string;
}

interface LoginResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    role: "user" | "admin" | "scanner";
  };
}

interface FormElements {
  form: HTMLFormElement;
  submitBtn: HTMLButtonElement | null;
  messageEl: HTMLElement | null;
}

// --- Sélecteurs ---

const SELECTORS = {
  loginForm: "#web-login-form",
  signupForm: "#web-signup-form",
  forgotForm: "#web-forgot-form",
};

// --- Utilitaires UI ---

function setMessage(element: HTMLElement | null, msg: string, type: "ok" | "err"): void {
  if (!element) return;
  element.textContent = msg;
  element.className = `message-area ${type}`;
}

function showGlobalMessage(type: "ok" | "error", text: string): void {
  const css = type === "error" ? "err" : "ok";
  const clientMsg = document.getElementById("client-msg") as HTMLElement | null;
  if (clientMsg) {
    clientMsg.textContent = text;
    clientMsg.className = "msg " + css;
    clientMsg.style.display = "block";
    return;
  }
  const card = document.querySelector<HTMLElement>(".card");
  let el = document.querySelector<HTMLElement>(".msg." + css);
  if (!el) {
    el = document.createElement("div");
    el.className = "msg " + css;
    if (card) card.prepend(el);
    else document.body.prepend(el);
  }
  el.textContent = text;
}

// --- HTTP helper (tolérant) ---

async function httpRequest(url: string, init?: RequestInit): Promise<Response> {
  const w: any = window as any;
  if (w?.Http?.request) {
    return w.Http.request(url, init);
  }
  return fetch(url, init as RequestInit);
}

// --- Binding générique de formulaire ---

function bindFormSubmit<TData = any>(options: {
  formSelector: string;
  apiEndpoint: string;
  transformPayload?: (payload: Record<string, any>) => Record<string, any>;
  onSuccess?: (data: TData, ctx: FormElements) => void;
  redirectUrl?: string | ((data: TData) => string);
}) {
  const form = document.querySelector<HTMLFormElement>(options.formSelector);
  if (!form) {
    console.warn(`Formulaire non trouvé: ${options.formSelector}`);
    return;
  }

  const submitBtn = form.querySelector<HTMLButtonElement>('button[type="submit"]');
  const messageEl = form.querySelector<HTMLElement>(".message-area");

  form.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!submitBtn) return;

      // Laisser le navigateur afficher ses messages natifs si invalid
      if (typeof form.reportValidity === "function" && !form.reportValidity()) {
        return;
      }

      const formData = new FormData(form);
      const payload: Record<string, any> = {};
      formData.forEach((value, key) => {
        payload[key] = value;
      });

      if (options.transformPayload) {
        Object.assign(payload, options.transformPayload(payload));
      }

      try {
        submitBtn.disabled = true;
        setMessage(messageEl, "Envoi en cours...", "ok");

        let response: Response;
        try {
          response = await httpRequest(options.apiEndpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json", "Accept": "application/json" },
            body: JSON.stringify(payload),
          });
        } catch (err: any) {
          // Si le wrapper Http a rejeté (4xx/5xx), tenter de lire err.response
          let errorMsg = "Une erreur est survenue.";
          try {
            const resp: Response | undefined = err?.response;
            if (resp) {
              let body: any = undefined;
              try { body = await resp.json(); } catch {}
              errorMsg = body?.detail || body?.message || `Erreur HTTP ${resp.status}`;
            } else if (err?.message) {
              errorMsg = err.message;
            }
          } catch {}
          if (errorMsg.includes("Utilisateur existe déjà")) {
            errorMsg = "Cet email est déjà utilisé. Essayez de vous connecter ou réinitialisez votre mot de passe.";
          }
          setMessage(messageEl, errorMsg, "err");
          submitBtn.disabled = false;
          return;
        }

        const responseData = await response.json().catch(() => ({}));
        if (!response.ok) {
          const errorMessage = responseData.detail || responseData.message || `Erreur HTTP ${response.status}`;
          throw new Error(errorMessage);
        }

        const data = responseData as TData;
        setMessage(
          messageEl,
          (typeof data === "object" && data && "message" in data
            ? (data as { message?: string }).message || "Opération réussie !"
            : "Opération réussie !"),
          "ok"
        );

        if (options.onSuccess) {
          options.onSuccess(data, { form, submitBtn, messageEl });
        }

        if (options.redirectUrl) {
          const url = typeof options.redirectUrl === "function" ? options.redirectUrl(data) : options.redirectUrl;
          window.location.assign(url);
        }
      } catch (error: any) {
        // Réactiver le bouton en cas d'échec (ex: 401 identifiants invalides)
        submitBtn.disabled = false;
        let errorMsg = (error as any)?.message || "Une erreur est survenue.";
        if (typeof errorMsg === "string" && errorMsg.includes("Utilisateur existe déjà")) {
          errorMsg = "Cet email est déjà utilisé. Essayez de vous connecter ou réinitialisez votre mot de passe.";
        }
        setMessage(messageEl, errorMsg, "err");
        console.error(`Erreur lors de la soumission à ${options.apiEndpoint}:`, error);
      } finally {
        if (!options.redirectUrl) {
          submitBtn.disabled = false;
        }
      }
    });
}

// --- Confirmation (lecture du hash) ---

function handleAuthConfirmationFromHash(): void {
  try {
    const raw = window.location.hash || "";
    if (!raw) return;

    const params = new URLSearchParams(raw.startsWith("#") ? raw.slice(1) : raw);
    const type = params.get("type");
    const error = params.get("error") || params.get("error_description") || params.get("message");
    const hasAnyToken = params.get("access_token") || params.get("token") || params.get("code");

    if (error) {
      showGlobalMessage("error", error);
    } else if (type === "signup" || hasAnyToken) {
      showGlobalMessage("ok", "Votre email est confirmé. Vous pouvez maintenant vous connecter.");
    } else {
      return;
    }

    try {
      const url = new URL(window.location.href);
      url.hash = "";
      window.history.replaceState({}, "", url.toString());
    } catch {
      window.location.hash = "";
    }
  } catch (e) {
    console.error("Erreur de lecture du hash:", e);
  }
}

// Nouveau: lecture du message de déconnexion depuis la query (?message=... ou ?error=...)
function handleAuthMessageFromQuery(): void {
  try {
    const url = new URL(window.location.href);
    const params = url.searchParams;

    const msg = params.get("message");
    const err = params.get("error");

    if (!msg && !err) return;

    // Si le serveur a déjà rendu un message (.msg ok/err sans l'id client-msg), ne pas en rajouter
    const serverMsgEl = document.querySelector(".msg.ok:not(#client-msg), .msg.err:not(#client-msg)") as HTMLElement | null;

    if (!serverMsgEl) {
      if (err) {
        showGlobalMessage("error", err);
      } else if (msg) {
        showGlobalMessage("ok", msg);
      }
    }

    // Nettoyer l'URL pour éviter la répétition au rechargement
    const cleanUrl = url.origin + url.pathname;
    window.history.replaceState({}, "", cleanUrl);
  } catch (e) {
    console.error("Erreur nettoyage URL (logout):", e);
  }
}

// --- Initialisation principale ---

function initializeAuthForms(): void {
  // Afficher message de déconnexion si présent dans l’URL puis nettoyer l’URL
  handleAuthMessageFromQuery();

  // Bandeau de confirmation depuis le hash
  handleAuthConfirmationFromHash();

  // Connexion
  bindFormSubmit<LoginResponse>({
    formSelector: SELECTORS.loginForm,
    apiEndpoint: "/api/v1/auth/login",
    redirectUrl: (data) =>
      data.user.role === "admin"
        ? "/admin"
        : data.user.role === "scanner"
        ? "/admin/scan"
        : "/session",
  });

  // Inscription
  bindFormSubmit<ApiMessageResponse | LoginResponse>({
    formSelector: SELECTORS.signupForm,
    apiEndpoint: "/api/v1/auth/signup",
    transformPayload: (p) => {
      const out = { ...p };
      if (typeof out.email === "string") out.email = out.email.trim().toLowerCase();
      if (typeof out.full_name === "string") out.full_name = out.full_name.trim();
      return out;
    },
    onSuccess: (data, { form, messageEl }) => {
      const asAny = data as any;
      const msg =
        (asAny && asAny.message) ||
        "Inscription réussie ! Vérifiez votre email pour confirmer et activer votre compte.";
      setMessage(messageEl, msg, "ok");

      if ((data as any)?.access_token && (data as any)?.user) {
        const role = (data as any).user?.role || "user";
        const dest =
          role === "admin" ? "/admin" : role === "scanner" ? "/admin/scan" : "/session";
        setTimeout(() => {
          window.location.assign(dest);
        }, 500);
        return;
      }
      form.reset();
    },
  });

  // Mot de passe oublié
  bindFormSubmit<ApiMessageResponse>({
    formSelector: SELECTORS.forgotForm,
    apiEndpoint: "/api/v1/auth/request-password-reset",
    transformPayload: (p) => {
      const out = { ...p };
      if (typeof out.email === "string") out.email = out.email.trim().toLowerCase();
      return out;
    },
    onSuccess: (data, { form, messageEl }) => {
      setMessage(
        messageEl,
        data.message || "Un email de réinitialisation a été envoyé si le compte existe.",
        "ok"
      );
      form.reset();
    },
  });

  // UI: afficher le bloc "mot de passe oublié"
  const forgotLink = document.querySelector<HTMLAnchorElement>("#forgot-link");
  const forgotContainer = document.querySelector<HTMLElement>("#forgot-container");
  if (forgotLink && forgotContainer) {
    forgotLink.addEventListener("click", (e) => {
      e.preventDefault();
      forgotContainer.style.display = "block";
      try {
        forgotContainer.scrollIntoView({ behavior: "smooth", block: "nearest" });
      } catch {}
    });
  } else {
    console.warn("Élément forgot-link ou forgot-container non trouvé");
  }
}

// --- Bootstrap ---

(window as any).initializeAuthForms = initializeAuthForms;
document.addEventListener("DOMContentLoaded", initializeAuthForms);


