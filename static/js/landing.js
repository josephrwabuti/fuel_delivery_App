/* FuelGo – Landing Page JavaScript */

document.addEventListener('DOMContentLoaded', function () {

  /* ---- Navbar scroll effect ---- */
  const nav = document.getElementById('mainNav');
  const onScroll = () => {
    nav.classList.toggle('scrolled', window.scrollY > 60);
  };
  window.addEventListener('scroll', onScroll, { passive: true });

  /* ---- Counter animation ---- */
  const counters = document.querySelectorAll('.stat-num[data-count]');
  const animateCounter = (el) => {
    const target = parseInt(el.dataset.count, 10);
    const suffix = el.dataset.suffix || '';
    const duration = 1800;
    const step = target / (duration / 16);
    let current = 0;
    const timer = setInterval(() => {
      current += step;
      if (current >= target) {
        current = target;
        clearInterval(timer);
      }
      el.textContent = Math.floor(current).toLocaleString() + suffix;
    }, 16);
  };

  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          animateCounter(entry.target);
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.5 });
    counters.forEach(c => observer.observe(c));
  } else {
    counters.forEach(animateCounter);
  }

  /* ---- Add + suffix to stat "97" (percent) ---- */
  const statNums = document.querySelectorAll('.stat-num');
  statNums.forEach(s => {
    const count = parseInt(s.dataset.count, 10);
    if (count === 97) s.dataset.suffix = '%';
    if (count === 1200) s.dataset.suffix = '+';
    if (count === 5) s.dataset.suffix = ' min';
  });

  /* ---- Scroll-in reveal ---- */
  const revealEls = document.querySelectorAll(
    '.feature-card, .step-card, .role-card, .trust-card, .ai-benefit-item'
  );
  const revealObs = new IntersectionObserver((entries) => {
    entries.forEach((entry, i) => {
      if (entry.isIntersecting) {
        setTimeout(() => {
          entry.target.style.opacity = '1';
          entry.target.style.transform = 'translateY(0)';
        }, (i % 4) * 80);
        revealObs.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

  revealEls.forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(28px)';
    el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    revealObs.observe(el);
  });

  /* ---- Active nav link on scroll ---- */
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('.nav-link');
  const activeObs = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        navLinks.forEach(l => l.classList.remove('active'));
        const active = document.querySelector(`.nav-link[href="#${entry.target.id}"]`);
        if (active) active.classList.add('active');
      }
    });
  }, { threshold: 0.4 });
  sections.forEach(s => activeObs.observe(s));

  /* ---- AI chart bar hover interaction ---- */
  const bars = document.querySelectorAll('.acm-bar');
  bars.forEach(bar => {
    bar.addEventListener('mouseenter', () => {
      bar.style.filter = 'brightness(1.3)';
    });
    bar.addEventListener('mouseleave', () => {
      bar.style.filter = '';
    });
  });

});
