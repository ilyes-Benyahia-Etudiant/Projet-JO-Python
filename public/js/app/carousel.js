"use strict";
// Compat: éviter ReferenceError si un ancien appel persiste
// eslint-disable-next-line @typescript-eslint/no-empty-function
function updateCarousel() { }
document.addEventListener("DOMContentLoaded", () => {
    class Carousel {
        constructor(selector = ".carousel-img", intervalMs = 5000) {
            this.currentIndex = 0;
            this.bootstrap = () => {
                if (!this.slides.length)
                    return;
                this.show(this.currentIndex);
                setInterval(this.next, this.intervalMs);
            };
            this.animateZoom = (el, from = 1, to = 1.1, duration = 1500) => {
                let scale = from;
                const start = performance.now();
                const step = (now) => {
                    const progress = Math.min((now - start) / duration, 1);
                    scale = from + (to - from) * progress;
                    el.style.transform = `scale(${scale})`;
                    if (progress < 1)
                        requestAnimationFrame(step);
                    else
                        el.style.transform = `scale(${to})`;
                };
                requestAnimationFrame(step);
            };
            this.show = (index) => {
                this.slides.forEach((slide) => {
                    slide.style.opacity = "0";
                    slide.style.transform = "scale(1)";
                    slide.style.zIndex = "0";
                });
                const active = this.slides[index];
                if (!active)
                    return;
                active.style.opacity = "1";
                active.style.transform = "scale(1)";
                active.style.zIndex = "1";
                this.animateZoom(active);
            };
            this.next = () => {
                if (!this.slides.length)
                    return;
                this.currentIndex = (this.currentIndex + 1) % this.slides.length;
                this.show(this.currentIndex);
            };
            this.slides = Array.from(document.querySelectorAll(selector));
            this.intervalMs = intervalMs;
            this.bootstrap();
        }
    }
    new Carousel(".carousel-img", 5000);
});
//# sourceMappingURL=carousel.js.map