// Compat: éviter ReferenceError si un ancien appel persiste
// eslint-disable-next-line @typescript-eslint/no-empty-function
function updateCarousel() {}

/**
 * carousel.ts - Carrousel très léger avec effet de zoom progressif:
 * - cycling automatique toutes les N secondes
 * - animation CSS-like via requestAnimationFrame
 */

document.addEventListener("DOMContentLoaded", () => {
  /**
   * Carousel d’images:
   * - show(index) affiche la slide active et relance l’animation de zoom
   * - next() passe à la slide suivante (boucle)
   */
  class Carousel {
    private readonly slides: HTMLElement[];
    private currentIndex = 0;
    private readonly intervalMs: number;

    constructor(selector = ".carousel-img", intervalMs = 5000) {
      this.slides = Array.from(document.querySelectorAll(selector)) as HTMLElement[];
      this.intervalMs = intervalMs;
      this.bootstrap();
    }

    private bootstrap = () => {
      if (!this.slides.length) return;
      this.show(this.currentIndex);
      setInterval(this.next, this.intervalMs);
    };

    /**
     * Anime un zoom progressif de “from” à “to” sur la durée donnée.
     */
    private animateZoom = (el: HTMLElement, from = 1, to = 1.1, duration = 1500) => {
      let scale = from;
      const start = performance.now();
      const step = (now: number) => {
        const progress = Math.min((now - start) / duration, 1);
        scale = from + (to - from) * progress;
        el.style.transform = `scale(${scale})`;
        if (progress < 1) requestAnimationFrame(step);
        else el.style.transform = `scale(${to})`;
      };
      requestAnimationFrame(step);
    };

    show = (index: number) => {
      this.slides.forEach((slide) => {
        slide.style.opacity = "0";
        slide.style.transform = "scale(1)";
        slide.style.zIndex = "0";
      });
      const active = this.slides[index];
      if (!active) return;
      active.style.opacity = "1";
      active.style.transform = "scale(1)";
      active.style.zIndex = "1";
      this.animateZoom(active);
    };

    next = () => {
      if (!this.slides.length) return;
      this.currentIndex = (this.currentIndex + 1) % this.slides.length;
      this.show(this.currentIndex);
    };
  }

  new Carousel(".carousel-img", 5000);
});