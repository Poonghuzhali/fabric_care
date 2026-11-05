(function () {
  const MESSAGES = {
    required: "This field is required.",
    email: "Enter a valid email address.",
    phone: "Enter a valid phone number (8–15 digits).",
    date: "Choose today or a later date.",
    service: "Please choose a service.",
    message: "Please write at least 8 characters.",
    pickup_address: "Enter the full pickup address (at least 10 characters).",
    pickup_map: "Drop a pin on the map for product pickup.",
  };

  function phoneDigits(value) {
    return (value || "").replace(/\D/g, "");
  }

  function isValidEmail(value) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(value || "").trim());
  }

  function clearFormErrors(form) {
    form.querySelectorAll(".error[data-error-for]").forEach((node) => {
      node.textContent = "";
    });
    form.querySelectorAll(".field, .portal-field").forEach((field) => {
      field.classList.remove("has-error");
    });
    form.querySelectorAll("[aria-invalid]").forEach((input) => {
      input.removeAttribute("aria-invalid");
    });
    const banner = form.querySelector("[data-form-error]");
    if (banner) {
      banner.textContent = "";
      banner.hidden = true;
    }
  }

  function showFieldError(form, name, message) {
    const slot = form.querySelector('[data-error-for="' + name + '"]');
    const control = form.querySelector('[name="' + name + '"]');
    const field = control ? control.closest(".field, .portal-field") : null;
    if (slot) slot.textContent = message;
    if (field) field.classList.add("has-error");
    if (control) control.setAttribute("aria-invalid", "true");
  }

  function showFormError(form, message) {
    const banner = form.querySelector("[data-form-error]");
    if (banner) {
      banner.textContent = message;
      banner.hidden = !message;
      return;
    }
    showFieldError(form, "form", message);
  }

  function applyServerErrors(form, errors) {
    clearFormErrors(form);
    Object.keys(errors).forEach((key) => {
      if (key === "form" || key === "__all__") {
        showFormError(form, errors[key]);
        return;
      }
      if (key === "auth") {
        showFormError(form, errors[key]);
        const note = form.querySelector(".book-auth-note");
        if (note) note.textContent = errors[key];
        return;
      }
      showFieldError(form, key, errors[key]);
    });
    focusFirstError(form);
  }

  function focusFirstError(form) {
    const target = form.querySelector(
      ".field.has-error input, .field.has-error select, .field.has-error textarea, " +
        ".portal-field.has-error input, .portal-field.has-error select, .portal-field.has-error textarea"
    );
    if (target) target.focus();
  }

  function validatePublicForm(form) {
    clearFormErrors(form);
    let valid = true;

    form.querySelectorAll("[required]").forEach((control) => {
      const value = control.type === "select-one" ? control.value : String(control.value || "").trim();
      if (!value) {
        const name = control.name;
        const msg =
          name === "service"
            ? MESSAGES.service
            : name === "preferred_date"
              ? MESSAGES.date
              : MESSAGES.required;
        showFieldError(form, name, msg);
        valid = false;
      }
    });

    form.querySelectorAll('input[type="email"]').forEach((control) => {
      if (control.value.trim() && !isValidEmail(control.value)) {
        showFieldError(form, control.name, MESSAGES.email);
        valid = false;
      }
    });

    form.querySelectorAll('input[name="phone"]').forEach((control) => {
      const digits = phoneDigits(control.value);
      if (control.hasAttribute("required") && !digits) {
        showFieldError(form, control.name, MESSAGES.required);
        valid = false;
      } else if (digits && (digits.length < 8 || digits.length > 15)) {
        showFieldError(form, control.name, MESSAGES.phone);
        valid = false;
      }
    });

    const dateInput = form.querySelector('input[name="preferred_date"]');
    if (dateInput && dateInput.value) {
      const chosen = new Date(dateInput.value + "T00:00:00");
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      if (chosen < today) {
        showFieldError(form, "preferred_date", MESSAGES.date);
        valid = false;
      }
    }

    const messageInput = form.querySelector('textarea[name="message"]');
    if (messageInput && messageInput.hasAttribute("required")) {
      const text = messageInput.value.trim();
      if (text.length < 8) {
        showFieldError(form, "message", MESSAGES.message);
        valid = false;
      }
    }

    const pickupAddress = form.querySelector('textarea[name="pickup_address"]');
    if (pickupAddress && pickupAddress.hasAttribute("required")) {
      const text = pickupAddress.value.trim();
      if (text.length < 10) {
        showFieldError(form, "pickup_address", MESSAGES.pickup_address);
        valid = false;
      }
    }

    const latInput = form.querySelector('input[name="pickup_latitude"]');
    const lngInput = form.querySelector('input[name="pickup_longitude"]');
    if (latInput && lngInput && pickupAddress) {
      const lat = String(latInput.value || "").trim();
      const lng = String(lngInput.value || "").trim();
      if (!lat || !lng) {
        showFieldError(form, "pickup_latitude", MESSAGES.pickup_map);
        valid = false;
      }
    }

    if (!valid) focusFirstError(form);
    return valid;
  }

  async function validatePublicFormAsync(form) {
    if (!validatePublicForm(form)) return false;
    const pickupAddress = form.querySelector('[name="pickup_address"]');
    const latInput = form.querySelector('input[name="pickup_latitude"]');
    if (!pickupAddress || !latInput) return true;
    if (String(latInput.value || "").trim()) return true;
    if (
      window.VastraPickupMap &&
      typeof window.VastraPickupMap.syncFromAddress === "function" &&
      pickupAddress.value.trim().length >= 10
    ) {
      const matched = await window.VastraPickupMap.syncFromAddress();
      if (!String(latInput.value || "").trim()) {
        showFieldError(form, "pickup_latitude", MESSAGES.pickup_map);
        focusFirstError(form);
        return false;
      }
      if (!matched) {
        showFieldError(form, "pickup_address", "We could not match this address on the map. Pick a suggestion or move the pin.");
        focusFirstError(form);
        return false;
      }
    }
    return true;
  }

  window.VastraForms = {
    clearFormErrors,
    applyServerErrors,
    validatePublicForm,
    validatePublicFormAsync,
    showFieldError,
    showFormError,
  };
})();
