document.addEventListener('DOMContentLoaded', function() {
  const hamburger = document.querySelector('.hamburger');
  const navLinks = document.querySelector('.navbar-links');
  if (hamburger && navLinks) {
    const toggle = () => {
      const opened = navLinks.classList.toggle('open');
      hamburger.setAttribute('aria-expanded', opened ? 'true' : 'false');
    };
    hamburger.setAttribute('aria-controls', 'primary-navigation');
    hamburger.setAttribute('aria-expanded', 'false');
    hamburger.addEventListener('click', toggle);

    // Fermer au clic sur un lien (mobile)
    navLinks.querySelectorAll('a').forEach(a => a.addEventListener('click', () => {
      if (navLinks.classList.contains('open')) {
        navLinks.classList.remove('open');
        hamburger.setAttribute('aria-expanded', 'false');
      }
    }));
  }
});