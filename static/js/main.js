(function () {
  const body = document.body;
  const heroAuto = body && body.getAttribute("data-hero-auto") !== "false";
  const hero = document.querySelector(".hero");
  const slides = Array.from(document.querySelectorAll(".hero-slide"));
  const dots = Array.from(document.querySelectorAll(".hero-dot"));
  let index = Math.max(0, slides.findIndex((slide) => slide.classList.contains("is-active")));
  let timer = null;
  const seconds = Number(hero && hero.dataset.interval) || 5;
  const interval = seconds * 1000;

  function restartZoom(slide) {
    const image = slide.querySelector(".hero-slide__media img");
    if (!image) return;
    image.style.animation = "none";
    image.style.transform = "";
    void image.offsetWidth;
    image.style.animation = "";
  }

  function show(next) {
    if (!slides.length) return;
    const current = slides[index];
    const currentImage = current && current.querySelector(".hero-slide__media img");
    if (currentImage && next !== index) {
      currentImage.style.animation = "none";
      currentImage.style.transform = "scale(1.12)";
    }
    index = (next + slides.length) % slides.length;
    slides.forEach(function (slide, slideIndex) {
      slide.classList.toggle("is-active", slideIndex === index);
    });
    dots.forEach(function (dot, dotIndex) {
      dot.classList.toggle("is-active", dotIndex === index);
    });
    restartZoom(slides[index]);
  }

  function queue() {
    if (!heroAuto || slides.length < 2) return;
    clearInterval(timer);
    timer = setInterval(function () {
      show(index + 1);
    }, interval);
  }

  const prev = document.querySelector(".hero-arrow--prev");
  const nextBtn = document.querySelector(".hero-arrow--next");
  if (prev) {
    prev.addEventListener("click", function () {
      show(index - 1);
      queue();
    });
  }
  if (nextBtn) {
    nextBtn.addEventListener("click", function () {
      show(index + 1);
      queue();
    });
  }
  dots.forEach(function (dot) {
    dot.addEventListener("click", function () {
      show(Number(dot.dataset.slide));
      queue();
    });
  });
  queue();

  const heroNav = document.querySelector(".hero-nav");
  if (heroNav && heroNav.getAttribute("data-sticky") !== "false") {
    const syncNav = function () {
      heroNav.classList.toggle("is-stuck", window.scrollY > 12);
    };
    syncNav();
    window.addEventListener("scroll", syncNav, { passive: true });
  }

  const toggle = document.querySelector(".nav-toggle");
  const links = document.querySelector("#nav-links");
  if (toggle && links) {
    toggle.addEventListener("click", function () {
      const open = links.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    links.addEventListener("click", function (event) {
      if (event.target.closest("a")) {
        links.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  const sections = ["about", "services", "pricing", "difference", "how-it-works", "testimonials", "contact"]
    .map(function (id) {
      return document.getElementById(id);
    })
    .filter(Boolean);
  const navAnchors = Array.from(document.querySelectorAll(".nav-links a"));
  if ("IntersectionObserver" in window && sections.length) {
    const observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          navAnchors.forEach(function (anchor) {
            const current = anchor.getAttribute("href") === "#" + entry.target.id;
            if (current) anchor.setAttribute("aria-current", "true");
            else anchor.removeAttribute("aria-current");
          });
        });
      },
      { rootMargin: "-45% 0px -45% 0px", threshold: 0.01 }
    );
    sections.forEach(function (section) {
      observer.observe(section);
    });
  }

  const uiCopyNode = document.getElementById("ui-copy-data");
  const uiCopy = uiCopyNode ? JSON.parse(uiCopyNode.textContent) : {};
  const contactGenericError = uiCopy.contactFormGenericError || "Something went wrong. Please try again.";
  const contactNetworkError = uiCopy.contactFormNetworkError || contactGenericError;

  function openModal(id) {
    const modal = document.getElementById(id + "-modal");
    if (!modal) return;
    modal.hidden = false;
    document.body.style.overflow = "hidden";
    const form = modal.querySelector("form");
    if (form && window.VastraForms) window.VastraForms.clearFormErrors(form);
    const focusable = modal.querySelector("input, select, textarea");
    if (focusable) focusable.focus();
  }

  function closeModal(modal) {
    modal.hidden = true;
    const form = modal.querySelector("form");
    const success = modal.querySelector(".modal-success");
    if (form) form.hidden = false;
    if (success) success.hidden = true;
    if (!document.querySelector(".modal:not([hidden])")) {
      document.body.style.overflow = "";
    }
  }

  function scrollToContact() {
    const el = document.getElementById("contact");
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    } else {
      window.location.hash = "contact";
    }
  }

  document.addEventListener("click", function (event) {
    const contactScroll = event.target.closest("[data-contact-scroll]");
    if (contactScroll) {
      event.preventDefault();
      scrollToContact();
      return;
    }

    const opener = event.target.closest("[data-open-modal]");
    if (opener) {
      event.preventDefault();
      const which = opener.getAttribute("data-open-modal");
      if (which) openModal(which);
      return;
    }

    if (event.target.classList.contains("modal")) {
      closeModal(event.target);
      return;
    }
    if (event.target.closest("[data-close-modal]")) {
      const modal = event.target.closest(".modal");
      if (modal) closeModal(modal);
    }
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      document.querySelectorAll(".modal:not([hidden])").forEach(closeModal);
    }
  });

  async function submitContactForm(form, modal) {
    if (window.VastraForms && !window.VastraForms.validatePublicForm(form)) {
      return;
    }
    const button = form.querySelector("[type=submit]");
    button.disabled = true;
    const body = Object.fromEntries(new FormData(form).entries());
    try {
      const response = await fetch(form.action, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": form.querySelector("[name=csrfmiddlewaretoken]").value,
          "X-Requested-With": "XMLHttpRequest",
        },
        body: JSON.stringify(body),
      });
      let payload = {};
      try {
        payload = JSON.parse(await response.text());
      } catch (parseError) {
        if (window.VastraForms) {
          window.VastraForms.showFormError(form, contactGenericError);
        }
        button.disabled = false;
        return;
      }
      if (!response.ok || !payload.ok) {
        if (window.VastraForms) {
          window.VastraForms.applyServerErrors(form, payload.errors || {});
        }
        button.disabled = false;
        return;
      }
      form.reset();
      if (window.VastraForms) window.VastraForms.clearFormErrors(form);
      form.hidden = true;
      const success = modal.querySelector(".modal-success");
      const text = success && success.querySelector("[data-success-text]");
      if (text && payload.message) text.textContent = payload.message;
      if (success) success.hidden = false;
    } catch (error) {
      if (window.VastraForms) {
        window.VastraForms.showFormError(form, contactNetworkError);
      }
    } finally {
      button.disabled = false;
    }
  }

  const contactForm = document.getElementById("contact-form");
  if (contactForm) {
    contactForm.addEventListener("submit", function (event) {
      event.preventDefault();
      submitContactForm(contactForm, contactForm.closest(".modal"));
    });
  }
})();
