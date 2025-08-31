// Attache le bouton "Connexion" pour aller sur /auth
document.addEventListener("DOMContentLoaded", () => {
  const btn = document.querySelector(".btn-login");
  if (btn && (!btn.getAttribute("href") || btn.getAttribute("href") === "#")) {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      window.location.href = "/auth";
    });
  }
});