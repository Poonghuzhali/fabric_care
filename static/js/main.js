(function () {
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
    slides.forEach((slide, slideIndex) => {
      slide.classList.toggle("is-active", slideIndex === index);
    });
    dots.forEach((dot, dotIndex) => {
      dot.classList.toggle("is-active", dotIndex === index);
    });
    restartZoom(slides[index]);
  }

  function queue() {
    if (slides.length < 2) return;
    clearInterval(timer);
    timer = setInterval(function () {
      show(index + 1);
    }, interval);
  }

  const prev = document.querySelector(".hero-arrow--prev");
  const next = document.querySelector(".hero-arrow--next");
  if (prev) {
    prev.addEventListener("click", function () {
      show(index - 1);
      queue();
    });
  }
  if (next) {
    next.addEventListener("click", function () {
      show(index + 1);
      queue();
    });
  }
  dots.forEach((dot) => {
    dot.addEventListener("click", function () {
      show(Number(dot.dataset.slide));
      queue();
    });
  });
  queue();

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

  const sections = ["about", "services", "difference", "testimonials", "contact"]
    .map((id) => document.getElementById(id))
    .filter(Boolean);
  const navAnchors = Array.from(document.querySelectorAll(".nav-links a"));
  if ("IntersectionObserver" in window && sections.length) {
    const observer = new IntersectionObserver(
      function (entries) {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          navAnchors.forEach((anchor) => {
            const current = anchor.getAttribute("href") === "#" + entry.target.id;
            if (current) anchor.setAttribute("aria-current", "true");
            else anchor.removeAttribute("aria-current");
          });
        });
      },
      { rootMargin: "-45% 0px -45% 0px", threshold: 0.01 }
    );
    sections.forEach((section) => observer.observe(section));
  }

  const servicesNode = document.getElementById("services-data");
  const services = servicesNode ? JSON.parse(servicesNode.textContent) : [];
  const detail = document.getElementById("detail-modal");

  function serviceById(id) {
    return services.find((item) => String(item.id) === String(id));
  }

  function paymentsEnabled() {
    return document.body.dataset.paymentsEnabled === "true";
  }

  function updateBookPaySummary() {
    const select = document.getElementById("book-service");
    const summary = document.getElementById("book-pay-summary");
    const amountNode = document.getElementById("book-pay-amount");
    const submitBtn = document.getElementById("book-submit");
    if (!select || !summary || !amountNode) return;
    const item = serviceById(select.value);
    if (item && item.price) {
      summary.hidden = false;
      amountNode.textContent = item.price;
      if (submitBtn) submitBtn.textContent = "Pay " + item.price + " & request booking";
    } else {
      summary.hidden = true;
      if (submitBtn) submitBtn.textContent = "Pay & request booking";
    }
  }

  function loadRazorpayScript() {
    return new Promise(function (resolve, reject) {
      if (window.Razorpay) {
        resolve();
        return;
      }
      const existing = document.querySelector('script[src="https://checkout.razorpay.com/v1/checkout.js"]');
      if (existing) {
        existing.addEventListener("load", function () {
          resolve();
        });
        return;
      }
      const script = document.createElement("script");
      script.src = "https://checkout.razorpay.com/v1/checkout.js";
      script.async = true;
      script.onload = function () {
        resolve();
      };
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }

  function openModal(id) {
    const modal = document.getElementById(id + "-modal");
    if (!modal) return;
    modal.hidden = false;
    document.body.style.overflow = "hidden";
    const form = modal.querySelector("form");
    if (form) clearErrors(form);
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
    if (modal.id === "book-modal") {
      stripBookFromUrl();
    }
  }

  function clearErrors(form) {
    if (window.VastraForms) window.VastraForms.clearFormErrors(form);
  }

  function stripBookFromUrl() {
    const params = new URLSearchParams(window.location.search);
    let changed = false;
    if (params.has("open_book")) {
      params.delete("open_book");
      changed = true;
    }
    if (window.location.hash === "#book") {
      changed = true;
    }
    if (!changed) return;
    const query = params.toString();
    history.replaceState(null, "", window.location.pathname + (query ? "?" + query : ""));
  }

  function openBook(serviceId) {
    const authed = document.body.dataset.customerAuth === "true";
    if (!authed) {
      const loginUrl = document.body.dataset.loginUrl || "/login/";
      const next = window.location.pathname + "?open_book=1";
      window.location.href = loginUrl + "?next=" + encodeURIComponent(next);
      return;
    }
    const form = document.getElementById("book-form");
    if (!form) return;
    form.hidden = false;
    const success = form.parentElement.querySelector(".modal-success");
    if (success) success.hidden = true;
    form.reset();
    clearErrors(form);
    if (serviceId) form.elements.service.value = String(serviceId);
    updateBookPaySummary();
    if (window.VastraPickupMap) window.VastraPickupMap.resetMap();
    openModal("book");
    setTimeout(function () {
      if (window.VastraSavedAddresses) {
        window.VastraSavedAddresses.reset();
        window.VastraSavedAddresses.applyDefault();
      }
      if (window.VastraPickupMap && window.VastraPickupMap.refreshMapSize) {
        window.VastraPickupMap.refreshMapSize();
      }
    }, 120);
  }

  document.addEventListener("click", function (event) {
    const opener = event.target.closest("[data-open-modal]");
    if (opener) {
      event.preventDefault();
      const which = opener.getAttribute("data-open-modal");
      if (which === "book") openBook(opener.getAttribute("data-service") || "");
      else openModal(which);
      return;
    }
    const detailButton = event.target.closest("[data-service-detail]");
    if (detailButton && detail) {
      const item = serviceById(detailButton.getAttribute("data-service-detail"));
      if (!item) return;
      detail.querySelector("#detail-image").src = item.image;
      detail.querySelector("#detail-image").alt = item.name;
      detail.querySelector("#detail-title").textContent = item.name;
      detail.querySelector("#detail-meta").textContent = item.price + " · " + item.duration;
      detail.querySelector("#detail-copy").textContent = item.description;
      detail.querySelector("#detail-book").setAttribute("data-service", item.id);
      detail.hidden = false;
      document.body.style.overflow = "hidden";
      return;
    }
    if (event.target.id === "detail-book") {
      const serviceId = event.target.getAttribute("data-service");
      if (detail) detail.hidden = true;
      openBook(serviceId);
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

  const dateInput = document.getElementById("book-date");
  if (dateInput) {
    const today = new Date();
    const month = String(today.getMonth() + 1).padStart(2, "0");
    const day = String(today.getDate()).padStart(2, "0");
    dateInput.min = today.getFullYear() + "-" + month + "-" + day;
  }

  function showBookingPlacedRedirect(modal) {
    if (!modal) return;
    const form = modal.querySelector("#book-form");
    const success = modal.querySelector(".modal-success");
    if (form) form.hidden = true;
    if (success) {
      const title = success.querySelector("h2");
      const text = success.querySelector("[data-success-text]");
      if (title) title.textContent = "Order placed";
      if (text) {
        text.textContent = "Payment received. Taking you to your confirmation page…";
      }
      success.hidden = false;
    }
  }

  async function completeBooking(form, modal, body) {
    const button = form.querySelector("[type=submit]");
    showBookingPlacedRedirect(modal);
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
        window.VastraForms.showFormError(
          form,
          "Payment succeeded but we could not finish the booking. Please contact the studio with your payment receipt."
        );
      }
      if (button) button.disabled = false;
      return;
    }
    if (!response.ok || !payload.ok) {
      if (payload.redirect) {
        window.location.href = payload.redirect;
        return;
      }
      if (window.VastraForms) {
        window.VastraForms.applyServerErrors(form, payload.errors || {});
      }
      if (button) button.disabled = false;
      return;
    }
    if (payload.redirect) {
      window.location.replace(payload.redirect);
      return;
    }
    form.reset();
    updateBookPaySummary();
    form.hidden = true;
    const success = modal.querySelector(".modal-success");
    const text = success.querySelector("[data-success-text]");
    if (text && payload.message) text.textContent = payload.message;
    success.hidden = false;
    if (button) button.disabled = false;
  }

  async function submitContactForm(form, modal) {
    if (window.VastraForms && !window.VastraForms.validatePublicForm(form)) {
      return;
    }
    const button = form.querySelector("[type=submit]");
    button.disabled = true;
    const body = Object.fromEntries(new FormData(form).entries());
    try {
      await completeBooking(form, modal, body);
    } catch (error) {
      if (window.VastraForms) {
        window.VastraForms.showFormError(form, "Something went wrong. Please try again.");
      }
    } finally {
      button.disabled = false;
    }
  }

  async function submitBookingForm(form, modal) {
    if (window.VastraForms && window.VastraForms.validatePublicFormAsync) {
      const ok = await window.VastraForms.validatePublicFormAsync(form);
      if (!ok) return;
    } else if (window.VastraForms && !window.VastraForms.validatePublicForm(form)) {
      return;
    }
    if (!paymentsEnabled()) {
      if (window.VastraForms) {
        window.VastraForms.showFormError(
          form,
          "Online payment is not set up yet. Please contact the studio to book."
        );
      }
      return;
    }
    const button = form.querySelector("[type=submit]");
    const body = Object.fromEntries(new FormData(form).entries());
    const orderUrl = form.dataset.paymentOrderUrl;
    if (!orderUrl) {
      if (window.VastraForms) {
        window.VastraForms.showFormError(form, "Payment could not be started.");
      }
      return;
    }
    button.disabled = true;
    try {
      const orderResponse = await fetch(orderUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": form.querySelector("[name=csrfmiddlewaretoken]").value,
          "X-Requested-With": "XMLHttpRequest",
        },
        body: JSON.stringify({ service: body.service }),
      });
      const orderPayload = await orderResponse.json();
      if (!orderResponse.ok || !orderPayload.ok) {
        if (window.VastraForms) {
          window.VastraForms.applyServerErrors(form, orderPayload.errors || {});
        }
        button.disabled = false;
        return;
      }
      await loadRazorpayScript();
      const brand = document.body.dataset.brand || orderPayload.brand || "Vastra Care";
      const phoneDigits = String(body.phone || "").replace(/\D/g, "");
      const contact =
        phoneDigits.length >= 10 ? phoneDigits.slice(-10) : phoneDigits || undefined;
      await new Promise(function (resolve, reject) {
        const checkout = new window.Razorpay({
          key: orderPayload.key_id,
          amount: orderPayload.amount,
          currency: orderPayload.currency || "INR",
          name: brand,
          description: orderPayload.service_name,
          order_id: orderPayload.order_id,
          prefill: {
            name: body.name || "",
            email: body.email || "",
            contact: contact,
          },
          theme: { color: "#741F3F" },
          handler: function (paymentResponse) {
            body.razorpay_order_id = paymentResponse.razorpay_order_id;
            body.razorpay_payment_id = paymentResponse.razorpay_payment_id;
            body.razorpay_signature = paymentResponse.razorpay_signature;
            completeBooking(form, modal, body)
              .then(resolve)
              .catch(reject);
          },
          modal: {
            ondismiss: function () {
              button.disabled = false;
              reject(new Error("payment dismissed"));
            },
          },
        });
        checkout.on("payment.failed", function () {
          if (window.VastraForms) {
            window.VastraForms.showFormError(form, "Payment failed. Please try again.");
          }
          button.disabled = false;
        });
        checkout.open();
      });
    } catch (error) {
      if (error && error.message !== "payment dismissed" && window.VastraForms) {
        window.VastraForms.showFormError(form, "Something went wrong. Please try again.");
      }
      button.disabled = false;
    }
  }

  const bookServiceSelect = document.getElementById("book-service");
  if (bookServiceSelect) {
    bookServiceSelect.addEventListener("change", updateBookPaySummary);
  }

  const bookForm = document.getElementById("book-form");
  if (bookForm) {
    bookForm.addEventListener("submit", function (event) {
      event.preventDefault();
      submitBookingForm(bookForm, bookForm.closest(".modal"));
    });
  }

  const contactForm = document.getElementById("contact-form");
  if (contactForm) {
    contactForm.addEventListener("submit", function (event) {
      event.preventDefault();
      submitContactForm(contactForm, contactForm.closest(".modal"));
    });
  }

  (function handleBookDeepLink() {
    const params = new URLSearchParams(window.location.search);
    const openOnce = params.get("open_book") === "1";
    stripBookFromUrl();
    if (openOnce) {
      openBook();
    }
  })();
})();
