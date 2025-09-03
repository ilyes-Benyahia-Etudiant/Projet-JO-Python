"use strict";
document.addEventListener("DOMContentLoaded", () => {
    class Navbar {
        constructor() {
            this.init = () => {
                if (!this.hamburger || !this.navLinks)
                    return;
                const toggle = () => {
                    const opened = this.navLinks.classList.toggle("open");
                    this.hamburger.setAttribute("aria-expanded", opened ? "true" : "false");
                };
                this.hamburger.setAttribute("aria-controls", "primary-navigation");
                this.hamburger.setAttribute("aria-expanded", "false");
                this.hamburger.addEventListener("click", toggle);
                this.navLinks.querySelectorAll("a").forEach((a) => a.addEventListener("click", () => {
                    if (this.navLinks.classList.contains("open")) {
                        this.navLinks.classList.remove("open");
                        this.hamburger.setAttribute("aria-expanded", "false");
                    }
                }));
            };
            this.hamburger = document.querySelector(".hamburger");
            this.navLinks = document.querySelector(".navbar-links");
            this.init();
        }
    }
    new Navbar();
});
//# sourceMappingURL=navbar.js.map