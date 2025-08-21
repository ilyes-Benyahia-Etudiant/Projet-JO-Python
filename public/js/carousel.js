// Compat: éviter ReferenceError si un ancien appel persiste
function updateCarousel() {}

const slides = Array.from(document.querySelectorAll('.carousel-img'));
let currentIndex = 0;

function showSlide(index) {
  slides.forEach((slide, idx) => {
    slide.style.opacity = '0';
    slide.style.transform = 'scale(1)';
    slide.style.zIndex = '0';
  });
  const active = slides[index];
  active.style.opacity = '1';
  active.style.transform = 'scale(1)';
  active.style.zIndex = '1';

  // Animation JS : zoom avant à partir de scale 1
  let scale = 1;
  const target = 1.1;
  const duration = 1500;
  const start = performance.now();

  function animate(now) {
    const progress = Math.min((now - start) / duration, 1);
    scale = 1 + (target - 1) * progress;
    active.style.transform = `scale(${scale})`;
    if (progress < 1) {
      requestAnimationFrame(animate);
    } else {
      active.style.transform = `scale(${target})`;
    }
  }
  requestAnimationFrame(animate);
}

function nextSlide() {
  currentIndex = (currentIndex + 1) % slides.length;
  showSlide(currentIndex);
}

// Affiche la première image et lance le défilement automatique si des images existent
if (slides.length > 0) {
  showSlide(currentIndex);
  setInterval(nextSlide, 5000);
}