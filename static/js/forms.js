(function () {
  const MESSAGES = {
    required: "This field is required.",
    email: "Enter a valid email address.",
    phone: "Enter a valid phone number (8–15 digits).",
    message: "Please write at least 8 characters.",
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
    form.querySelectorAll(".field").forEach((field) => {
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
    const field = control ? control.closest(".field") : null;
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
      showFieldError(form, key, errors[key]);
    });
    focusFirstError(form);
  }

  function focusFirstError(form) {
    const target = form.querySelector(
      ".field.has-error input, .field.has-error select, .field.has-error textarea"
    );
    if (target) target.focus();
  }

  function validatePublicForm(form) {
    clearFormErrors(form);
    let valid = true;

    form.querySelectorAll("[required]").forEach((control) => {
      const value = control.type === "select-one" ? control.value : String(control.value || "").trim();
      if (!value) {
        showFieldError(form, control.name, MESSAGES.required);
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

    const messageInput = form.querySelector('textarea[name="message"]');
    if (messageInput && messageInput.hasAttribute("required")) {
      const text = messageInput.value.trim();
      if (text.length < 8) {
        showFieldError(form, "message", MESSAGES.message);
        valid = false;
      }
    }

    if (!valid) focusFirstError(form);
    return valid;
  }

  window.VastraForms = {
    clearFormErrors,
    applyServerErrors,
    validatePublicForm,
    showFieldError,
    showFormError,
  };
})();
