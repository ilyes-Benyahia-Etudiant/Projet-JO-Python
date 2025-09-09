// --- Type Definitions ---

// Réponse générique pour les messages simples (inscription, etc.)
interface ApiMessageResponse {
  message?: string;
  detail?: string;
}

// Réponse spécifique pour une connexion réussie
interface LoginResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    role: "user" | "admin";
  };
}

// Éléments du formulaire passés aux fonctions de rappel
interface FormElements {
  form: HTMLFormElement;
  submitBtn: HTMLButtonElement | null;
  messageEl: HTMLElement | null;
}

// --- Constantes ---

const SELECTORS = {
  loginForm: "#web-login-form",
  signupForm: "#web-signup-form",
  forgotForm: "#web-forgot-form",
};

// --- Utilitaires DOM ---

function setMessage(element: HTMLElement | null, msg: string, type: "ok" | "err"): void {
  if (!element) return;
  element.textContent = msg;
  element.className = `message-area ${type}`; // Classe cohérente pour les messages
}

// --- Logique principale ---

/**
 * Lie un gestionnaire de soumission à un formulaire pour les appels API.
 * Envoie les données en tant que JSON.
 */
async function bindFormSubmit<T>(options: {
  formSelector: string;
  apiEndpoint: string;
  transformPayload?: (payload: Record<string, any>) => Record<string, any>;
  onSuccess?: (data: T, elements: FormElements) => void;
  redirectUrl?: string | ((data: T) => string); // URL de redirection statique ou dynamique
}): Promise<void> {
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

    const formData = new FormData(form);
    
    // Correction : Remplacer Object.fromEntries par une boucle forEach
    const payload: { [key: string]: any } = {};
    formData.forEach((value, key) => {
      payload[key] = value;
    });

    if (options.transformPayload) {
      // Note: la transformation se fait maintenant sur l'objet 'payload'
      Object.assign(payload, options.transformPayload(payload));
    }

    try {
      submitBtn.disabled = true;
      setMessage(messageEl, "Envoi en cours...", "ok");

      const response = await (window as any).Http.request(options.apiEndpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Accept": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const responseData = await response.json();

      if (!response.ok) {
        const errorMessage = responseData.detail || `Erreur HTTP ${response.status}`;
        throw new Error(errorMessage);
      }

      const data = responseData as T;
      setMessage(
        messageEl,
        (typeof data === 'object' && data && 'message' in data
          ? (data as { message?: string }).message || "Opération réussie !"
          : "Opération réussie !"),
        "ok"
      );

      if (options.onSuccess) {
        options.onSuccess(data, { form, submitBtn, messageEl });
      }

      if (options.redirectUrl) {
        const url = typeof options.redirectUrl === 'function' ? options.redirectUrl(data) : options.redirectUrl;
        window.location.assign(url);
      }
    } catch (error: any) {
      let errorMsg = error.message || "Une erreur est survenue.";
      if (errorMsg.includes("Utilisateur existe déjà")) {
        errorMsg = "Cet email est déjà utilisé. Essayez de vous connecter ou réinitialisez votre mot de passe.";
      }
      setMessage(messageEl, errorMsg, "err");
      console.error(`Erreur lors de la soumission à ${options.apiEndpoint}:`, error);
    } finally {
      // Ne réactive le bouton qu'en cas d'erreur sans redirection
      if (!options.redirectUrl) {
          submitBtn.disabled = false;
      }
    }
  });
}

/**
 * Initialise tous les formulaires d'authentification. Exportée pour les tests.
 */
function initializeAuthForms(): void {
  // --- Formulaire de Connexion ---
  bindFormSubmit<LoginResponse>({
    formSelector: SELECTORS.loginForm,
    apiEndpoint: "/api/v1/auth/login",
    // L'API attend 'email', le formulaire utilise 'email', donc pas de transformation nécessaire.
    redirectUrl: (data) => (data.user.role === "admin" ? "/admin" : "/session"),
  });

  // --- Formulaire d'Inscription ---
  bindFormSubmit<ApiMessageResponse | LoginResponse>({
    formSelector: SELECTORS.signupForm,
    apiEndpoint: "/api/v1/auth/signup",
    onSuccess: (data, { form, messageEl }) => {
      const asAny = data as any;
      let msg = (asAny && asAny.message) || "Inscription réussie ! Vérifiez votre email pour confirmer et activez votre compte.";
      setMessage(messageEl, msg, "ok");

      if (asAny && asAny.access_token && asAny.user) {
        // Délai pour que le message soit visible avant redirection
        setTimeout(() => {
          window.location.assign("/");
        }, 2000);
        return;
      }
      form.reset();
    },
  });

  bindFormSubmit<ApiMessageResponse>({
    formSelector: SELECTORS.forgotForm,
    apiEndpoint: "/api/v1/auth/request-password-reset",
    onSuccess: (data, { form, messageEl }) => {
      setMessage(messageEl, data.message || "Un email de réinitialisation a été envoyé si le compte existe.", "ok");
      form.reset();
    },
  });

  const forgotLink = document.querySelector<HTMLAnchorElement>("#forgot-link");
  const forgotContainer = document.querySelector<HTMLElement>("#forgot-container");
  if (forgotLink && forgotContainer) {
    forgotLink.addEventListener("click", (e) => {
      e.preventDefault();
      forgotContainer.style.display = "block";
      console.log("Formulaire mot de passe oublié affiché");
      try { forgotContainer.scrollIntoView({ behavior: "smooth", block: "nearest" }); } catch {}
    });
  } else {
    console.warn("Élément forgot-link ou forgot-container non trouvé");
  }
}

// --- Initialisation automatique au chargement de la page ---
window.initializeAuthForms = initializeAuthForms;
document.addEventListener("DOMContentLoaded", initializeAuthForms);


