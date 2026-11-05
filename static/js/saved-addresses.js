(function () {
  function readSavedAddresses() {
    const node = document.getElementById("saved-addresses-data");
    if (!node) return [];
    try {
      const data = JSON.parse(node.textContent || "[]");
      return Array.isArray(data) ? data : [];
    } catch (error) {
      return [];
    }
  }

  function bindBookingSavedAddresses() {
    const select = document.getElementById("book-saved-address");
    const addressInput = document.getElementById("book-address");
    if (!select) return;

    const addresses = readSavedAddresses();
    const byId = new Map(addresses.map(function (item) { return [String(item.id), item]; }));

    select.addEventListener("change", function () {
      const id = select.value;
      if (!id) return;
      const saved = byId.get(id);
      if (saved && window.VastraPickupMap && window.VastraPickupMap.applySavedAddress) {
        window.VastraPickupMap.applySavedAddress(saved);
      }
    });

    if (addressInput) {
      addressInput.addEventListener("input", function () {
        if (select.value) select.value = "";
      });
    }

    window.VastraSavedAddresses = {
      addresses: addresses,
      reset: function () {
        select.value = "";
      },
      applyDefault: function () {
        if (!addresses.length) return;
        const preferred = addresses.find(function (item) { return item.is_default; }) || addresses[0];
        if (!preferred) return;
        select.value = String(preferred.id);
        select.dispatchEvent(new Event("change"));
      },
    };
  }

  document.addEventListener("DOMContentLoaded", bindBookingSavedAddresses);
})();
