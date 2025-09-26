// --- Types ---
// Interfaces pour typer les réponses des API et les éléments de formulaire

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

/**
 * auth.ts - Gestion des formulaires d'authentification (login, signup, forgot/reset),
 * affichage des messages globaux, et compatibilité avec un wrapper Http éventuel.
 */

// --- Sélecteurs ---
// Sélecteurs CSS pour les différents formulaires de l’application

/**
 * Sélecteurs des formulaires rendus côté client.
 * S'ils sont absents de la page, leur binding est simplement ignoré.
 */
const SELECTORS = {
  loginForm: "#web-login-form",
  signupForm: "#web-signup-form",
  forgotForm: "#web-forgot-form",
};

// --- Utilitaires UI ---
// Fonction pour afficher un message dans une zone dédiée (ex: sous un formulaire)
function setMessage(element: HTMLElement | null, msg: string, type: "ok" | "err"): void {
  if (!element) return;
  element.textContent = msg;
  element.className = `message-area ${type}`;
}

// Affiche un message global en haut de la page (ex: confirmation email, erreur globale)
function showGlobalMessage(type: "ok" | "error", text: string): void {
  const css = type === "error" ? "err" : "ok";
  const clientMsg = document.getElementById("client-msg") as HTMLElement | null;

  // Si un élément client-msg existe déjà, on l'utilise
  if (clientMsg) {
    clientMsg.textContent = text;
    clientMsg.className = "msg " + css;
    clientMsg.style.display = "block";
    return;
  }

  // Sinon on crée dynamiquement un élément pour afficher le message global
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
// Enveloppe autour de fetch(), compatible avec un éventuel wrapper Http personnalisé
async function httpRequest(url: string, init?: RequestInit): Promise<Response> {
  const w: any = window as any;
  if (w?.Http?.request) {
    return w.Http.request(url, init);
  }
  return fetch(url, init as RequestInit);
}

// --- Binding générique de formulaire ---
// Fonction qui gère l’envoi de n’importe quel formulaire vers une API
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

  // Gestionnaire d'événement de soumission
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!submitBtn) return;

    // Vérifie la validité native du formulaire
    if (typeof form.reportValidity === "function" && !form.reportValidity()) {
      return;
    }

    // Construction du payload à partir du formulaire
    const formData = new FormData(form);
    const payload: Record<string, any> = {};
    formData.forEach((value, key) => {
      payload[key] = value;
    });

    // Transformation personnalisée si nécessaire
    if (options.transformPayload) {
      Object.assign(payload, options.transformPayload(payload));
    }

    try {
      submitBtn.disabled = true;
      setMessage(messageEl, "Envoi en cours...", "ok");

      let response: Response;

      // Envoi de la requête HTTP
      try {
        response = await httpRequest(options.apiEndpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json", "Accept": "application/json" },
          body: JSON.stringify(payload),
        });
      } catch (err: any) {
        // Gestion des erreurs réseau ou rejet par un wrapper Http
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
        // Gestion d’un cas particulier: email déjà utilisé
        if (errorMsg.includes("Utilisateur existe déjà")) {
          errorMsg = "Cet email est déjà utilisé. Essayez de vous connecter ou réinitialisez votre mot de passe.";
        }
        setMessage(messageEl, errorMsg, "err");
        submitBtn.disabled = false;
        return;
      }

      // Lecture et validation de la réponse JSON
      const responseData = await response.json().catch(() => ({}));
      if (!response.ok) {
        const errorMessage = responseData.detail || responseData.message || `Erreur HTTP ${response.status}`;
        throw new Error(errorMessage);
      }

      const data = responseData as TData;
      // Message de succès
      setMessage(
        messageEl,
        (typeof data === "object" && data && "message" in data
          ? (data as { message?: string }).message || "Opération réussie !"
          : "Opération réussie !"),
        "ok"
      );

      // Callback personnalisée si fournie
      if (options.onSuccess) {
        options.onSuccess(data, { form, submitBtn, messageEl });
      }

      // Redirection éventuelle après succès
      if (options.redirectUrl) {
        const url = typeof options.redirectUrl === "function" ? options.redirectUrl(data) : options.redirectUrl;
        window.location.assign(url);
      }
    } catch (error: any) {
      // Gestion globale des erreurs (ex: mauvais identifiants)
      submitBtn.disabled = false;
      let errorMsg = (error as any)?.message || "Une erreur est survenue.";
      if (typeof errorMsg === "string" && errorMsg.includes("Utilisateur existe déjà")) {
        errorMsg = "Cet email est déjà utilisé. Essayez de vous connecter ou réinitialisez votre mot de passe.";
      }
      setMessage(messageEl, errorMsg, "err");
      console.error(`Erreur lors de la soumission à ${options.apiEndpoint}:`, error);
    } finally {
      // Réactivation du bouton si aucune redirection prévue
      if (!options.redirectUrl) {
        submitBtn.disabled = false;
      }
    }
  });
}

// --- Confirmation (lecture du hash) ---
// Analyse l’URL pour afficher un message de confirmation après validation email
function handleAuthConfirmationFromHash(): void {
  try {
    const raw = window.location.hash || "";
    if (!raw) return;

    const params = new URLSearchParams(raw.startsWith("#") ? raw.slice(1) : raw);
    const type = params.get("type");
    const error = params.get("error") || params.get("error_description") || params.get("message");
    const hasAnyToken = params.get("access_token") || params.get("token") || params.get("code");

    // Affichage du message selon les paramètres
    if (error) {
      showGlobalMessage("error", error);
    } else if (type === "signup" || hasAnyToken) {
      showGlobalMessage("ok", "Votre email est confirmé. Vous pouvez maintenant vous connecter.");
    } else {
      return;
    }

    // Nettoyage du hash dans l’URL
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

// --- Lecture message de déconnexion ---
// Lit un éventuel message transmis en query string (?message=... ou ?error=...)
function handleAuthMessageFromQuery(): void {
  try {
    const url = new URL(window.location.href);
    const params = url.searchParams;

    const msg = params.get("message");
    const err = params.get("error");

    if (!msg && !err) return;

    // Vérifie si le serveur a déjà rendu un message pour éviter un doublon
    const serverMsgEl = document.querySelector(".msg.ok:not(#client-msg), .msg.err:not(#client-msg)") as HTMLElement | null;

    if (!serverMsgEl) {
      if (err) {
        showGlobalMessage("error", err);
      } else if (msg) {
        showGlobalMessage("ok", msg);
      }
    }

    // Nettoyage de l’URL
    const cleanUrl = url.origin + url.pathname;
    window.history.replaceState({}, "", cleanUrl);
  } catch (e) {
    console.error("Erreur nettoyage URL (logout):", e);
  }
}

// --- Initialisation principale ---
// Fonction d’initialisation qui connecte tous les formulaires et les comportements associés
function initializeAuthForms(): void {
  // Affiche un éventuel message de déconnexion
  handleAuthMessageFromQuery();

  // Gère la confirmation d’inscription depuis le hash
  handleAuthConfirmationFromHash();

  // --- Connexion ---
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

  // --- Inscription ---
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

      // Si la réponse contient un token, connexion automatique
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

  // --- Mot de passe oublié ---
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

  // --- Gestion du bloc "mot de passe oublié" ---
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
// Attache la fonction d’initialisation au chargement du DOM
(window as any).initializeAuthForms = initializeAuthForms;
document.addEventListener("DOMContentLoaded", initializeAuthForms);
