class AdminScanPage {
  private input: HTMLInputElement | null;
  private btn: HTMLButtonElement | null;
  private result: HTMLElement | null;

  constructor() {
    this.input = document.getElementById("token-input") as HTMLInputElement | null;
    this.btn = document.getElementById("validate-btn") as HTMLButtonElement | null;
    this.result = document.getElementById("result");
    this.init();
  }

  private init() {
    this.btn?.addEventListener("click", () => this.handleValidate());
    // Si l’URL contient ?token=..., on pré-remplit et on valide
    const url = new URL(window.location.href);
    const token = url.searchParams.get("token");
    if (token && this.input) {
      this.input.value = token;
      this.handleValidate();
    }
  }

  private async handleValidate() {
    const token = (this.input?.value || "").trim();
    if (!token) return this.renderInfo("Veuillez saisir un token.", "warn");
    try {
      const HttpAny = (window as any).Http;
      let res: any;
      if (HttpAny?.postJson) {
        res = await HttpAny.postJson("/api/v1/validation/scan", { token });
      } else {
        const csrf = this.getCookie("csrf_token") || "";
        const r = await fetch("/api/v1/validation/scan", {
          method: "POST",
          credentials: "same-origin",
          headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": csrf,
          },
          body: JSON.stringify({ token }),
        });
        if (!r.ok) {
          const errTxt = await r.text().catch(() => "");
          throw new Error(`HTTP ${r.status}: ${errTxt}`);
        }
        res = await r.json();
      }

      if (res.status === "ok") {
        this.renderSuccess(`Succès: billet validé.`);
        this.renderTicket(res.ticket, res.validation);
      } else if (res.status === "already_validated") {
        this.renderInfo(`Info: billet déjà validé.`, "warn");
        this.renderTicket(res.ticket, res.validation);
      } else {
        this.renderError(`Erreur: ${res.message || "Validation impossible"}`);
      }
    } catch (e: any) {
      this.renderError(`Erreur: ${e?.message || e}`);
    }
  }

  private renderTicket(ticket: any, validation: any) {
    if (!this.result) return;
    const offre = (ticket?.offres || {});
    const scannedAt = validation?.scanned_at || "—";
    const scannedBy = validation?.scanned_by || "—";
    this.result.innerHTML = `
      <div class="border rounded p-3 mt-2">
        <div><strong>Référence:</strong> ${ticket?.token || "N/A"}</div>
        <div><strong>Offre:</strong> ${offre?.title || "—"}</div>
        <div><strong>Validé le:</strong> ${scannedAt}</div>
        <div><strong>Validé par:</strong> ${scannedBy}</div>
      </div>
    `;
  }

  private renderSuccess(msg: string) { this.toast(msg, "success"); }
  private renderError(msg: string) { this.toast(msg, "error"); }
  private renderInfo(msg: string, type: "info" | "warn" = "info") {
    this.toast(msg, type === "warn" ? "warn" : "info");
  }

  private toast(message: string, type: "success" | "error" | "info" | "warn" = "info") {
    const el = document.createElement("div");
    el.textContent = message;
    el.style.position = "fixed";
    el.style.right = "16px";
    el.style.bottom = "16px";
    el.style.zIndex = "9999";
    el.style.padding = "10px 14px";
    el.style.borderRadius = "6px";
    el.style.color = "#fff";
    el.style.fontWeight = "600";
    el.style.boxShadow = "0 4px 12px rgba(0,0,0,0.15)";
    el.style.opacity = "0";
    el.style.transition = "opacity 150ms ease";
    const color = type === "success" ? "#16a34a" : type === "error" ? "#dc2626" : type === "warn" ? "#f59e0b" : "#2563eb";
    el.style.background = color;
    document.body.appendChild(el);
    requestAnimationFrame(() => (el.style.opacity = "1"));
    setTimeout(() => {
      el.style.opacity = "0";
      setTimeout(() => el.remove(), 220);
    }, 2500);
  }

  private getCookie(name: string): string | null {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop()!.split(';').shift() || null;
    return null;
  }
}

document.addEventListener("DOMContentLoaded", () => new AdminScanPage());
(window as any).AdminScanPage = AdminScanPage;

// Page Admin Scan - logique front
// Utilise la classe Http exposée globalement (voir src/ts/http.ts)

type ValidationResponse = {
  status: "ok" | "already_validated";
  ticket: {
    id: string;
    token: string;
    user_id: string;
    created_at: string;
    offres?: { title?: string; description?: string; image?: string };
    users?: { full_name?: string; email?: string };
  };
  validation: {
    id: string;
    token: string;
    commande_id: string;
    scanned_at: string;
    scanned_by: string;
    status: string;
  };
  message?: string;
};

function byId<T extends HTMLElement = HTMLElement>(id: string): T {
  const el = document.getElementById(id);
  if (!el) throw new Error(`Element #${id} introuvable`);
  return el as T;
}

function getQueryToken(): string | null {
  const url = new URL(window.location.href);
  const t = url.searchParams.get("token");
  return t && t.trim() ? t.trim() : null;
}

function renderResultOk(container: HTMLElement, data: ValidationResponse) {
  const { status, ticket, validation, message } = data;
  const displayName =
    (ticket.users?.full_name && ticket.users.full_name.trim()) ||
    (ticket.users?.email && ticket.users.email.trim()) ||
    "Utilisateur";

  const offreTitle = ticket.offres?.title || "Offre";
  const badgeClass =
    status === "already_validated"
      ? "bg-yellow-100 text-yellow-800"
      : "bg-green-100 text-green-800";

  const statusText =
    status === "already_validated" ? "Déjà validé" : "Validé";

  container.innerHTML = `
    <div class="border rounded p-4 bg-white">
      <div class="flex items-center justify-between mb-2">
        <h3 class="text-lg font-semibold">${escapeHtml(displayName)}</h3>
        <span class="px-2 py-1 rounded text-sm ${badgeClass}">${statusText}</span>
      </div>
      <p class="text-gray-700 mb-1"><strong>Offre:</strong> ${escapeHtml(offreTitle)}</p>
      <p class="text-gray-700 mb-1"><strong>Token:</strong> <code>${escapeHtml(ticket.token)}</code></p>
      <p class="text-gray-700 mb-1"><strong>Message:</strong> ${escapeHtml(message || "")}</p>
      <p class="text-gray-600 mt-2 text-sm">
        <strong>Horodatage:</strong> ${escapeHtml(validation.scanned_at || "")}
      </p>
    </div>
  `;
}

function renderResultError(container: HTMLElement, err: unknown) {
  const msg = err instanceof Error ? err.message : String(err || "Erreur");
  container.innerHTML = `
    <div class="border rounded p-4 bg-white">
      <div class="px-2 py-1 rounded text-sm bg-red-100 text-red-800 inline-block mb-2">Erreur</div>
      <p class="text-red-700">${escapeHtml(msg)}</p>
    </div>
  `;
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(">", "&gt;")
    .replace('"', "&quot;")
    .replace("'", "&#39;");
}

async function validateToken(token: string): Promise<void> {
  const result = byId("result");
  result.innerHTML = `<div class="text-gray-500">Validation en cours...</div>`;
  try {
    // @ts-expect-error Http est exposé globalement par src/ts/http.ts
    const data = await window.Http.postJson<ValidationResponse>(
      "/api/v1/validation/scan",
      { token }
    );
    renderResultOk(result, data);
  } catch (err) {
    renderResultError(result, err);
  }
}

function setup(): void {
  const input = byId<HTMLInputElement>("token-input");
  const btn = byId<HTMLButtonElement>("validate-btn");
  const result = byId("result");

  btn.addEventListener("click", () => {
    const token = (input.value || "").trim();
    if (!token) {
      renderResultError(result, new Error("Veuillez saisir un token."));
      return;
    }
    validateToken(token);
  });

  // Préremplir depuis l'URL si ?token=...
  const t = getQueryToken();
  if (t) {
    input.value = t;
    // Valide automatiquement si le token est présent dans l'URL
    validateToken(t);
  }
}

document.addEventListener("DOMContentLoaded", setup);