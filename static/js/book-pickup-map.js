(function () {
  const DEFAULT_CENTER = { lat: 11.9139, lng: 79.8145 };
  const GEOCODE_DEBOUNCE_MS = 650;
  let googleMap = null;
  let googleMarker = null;
  let autocomplete = null;
  let geocoder = null;
  let leafletMap = null;
  let leafletMarker = null;
  let initStarted = false;
  let pendingLocate = false;
  let uiBound = false;
  let geocodeTimer = null;
  let addressGeocodeRequest = 0;

  function apiKey() {
    return (document.body.dataset.googleMapsKey || "").trim();
  }

  function els() {
    return {
      mapEl: document.getElementById("book-pickup-map"),
      address: document.getElementById("book-address"),
      lat: document.getElementById("book-lat"),
      lng: document.getElementById("book-lng"),
      mapsUrl: document.getElementById("book-maps-url"),
      mapsOpen: document.getElementById("book-maps-open"),
      mapsPaste: document.getElementById("book-maps-paste"),
      locateBtn: document.getElementById("book-locate-btn"),
      gmapsPickBtn: document.getElementById("book-gmaps-pick-btn"),
      locateStatus: document.getElementById("book-locate-status"),
      form: document.getElementById("book-form"),
    };
  }

  function googleMapsPickerUrl(lat, lng) {
    return (
      "https://www.google.com/maps/@?api=1&map_action=map&center=" +
      encodeURIComponent(lat + "," + lng) +
      "&zoom=18"
    );
  }

  function googleMapsViewUrl(lat, lng) {
    return "https://www.google.com/maps/search/?api=1&query=" + encodeURIComponent(lat + "," + lng);
  }

  function setLocateStatus(message) {
    const node = els().locateStatus;
    if (!node) return;
    if (message) {
      node.textContent = message;
      node.hidden = false;
    } else {
      node.textContent = "";
      node.hidden = true;
    }
  }

  function applyPosition(lat, lng, options) {
    options = options || {};
    const latN = Number(lat);
    const lngN = Number(lng);
    if (!Number.isFinite(latN) || !Number.isFinite(lngN)) return;

    if (googleMarker && googleMap) {
      const pos = { lat: latN, lng: lngN };
      googleMarker.setPosition(pos);
      googleMap.panTo(pos);
      if (options.zoom) googleMap.setZoom(options.zoom);
    }
    if (leafletMarker && leafletMap) {
      leafletMarker.setLatLng([latN, lngN]);
      leafletMap.setView([latN, lngN], options.zoom || Math.max(leafletMap.getZoom(), 15));
    }
    setCoords(latN, lngN);
  }

  function setCoords(lat, lng) {
    const nodes = els();
    if (!nodes.lat || !nodes.lng) return;
    const latN = Number(lat);
    const lngN = Number(lng);
    if (!Number.isFinite(latN) || !Number.isFinite(lngN)) return;
    nodes.lat.value = latN.toFixed(6);
    nodes.lng.value = lngN.toFixed(6);
    const viewUrl = googleMapsViewUrl(latN, lngN);
    if (nodes.mapsUrl) nodes.mapsUrl.value = viewUrl;
    if (nodes.mapsOpen) {
      nodes.mapsOpen.href = viewUrl;
      nodes.mapsOpen.hidden = false;
    }
    if (window.VastraForms && nodes.form) {
      window.VastraForms.clearFormErrors(nodes.form);
    }
  }

  function nominatimHeaders() {
    return {
      Accept: "application/json",
      "Accept-Language": "en",
    };
  }

  function reverseGeocodeFromPin(lat, lng) {
    const nodes = els();
    if (!nodes.address) return;

    if (geocoder && window.google && window.google.maps) {
      geocoder.geocode({ location: { lat: lat, lng: lng } }, function (results, status) {
        if (status === "OK" && results && results[0]) {
          nodes.address.value = results[0].formatted_address;
        }
      });
      return;
    }

    const url =
      "https://nominatim.openstreetmap.org/reverse?format=json&lat=" +
      encodeURIComponent(lat) +
      "&lon=" +
      encodeURIComponent(lng);
    fetch(url, { headers: nominatimHeaders() })
      .then(function (response) {
        return response.json();
      })
      .then(function (data) {
        if (data && data.display_name) {
          nodes.address.value = data.display_name;
        }
      })
      .catch(function () {});
  }

  function forwardGeocodeAddress(query, options) {
    options = options || {};
    const nodes = els();
    const text = (query || "").trim();
    if (!text || text.length < 10) {
      return Promise.resolve(false);
    }

    const requestId = ++addressGeocodeRequest;

    if (geocoder && window.google && window.google.maps) {
      return new Promise(function (resolve) {
        geocoder.geocode(
          { address: text, componentRestrictions: { country: "in" } },
          function (results, status) {
            if (requestId !== addressGeocodeRequest) {
              resolve(false);
              return;
            }
            if (status !== "OK" || !results || !results[0]) {
              if (options.showStatus) {
                setLocateStatus("Could not find that address on the map. Adjust the pin manually.");
              }
              resolve(false);
              return;
            }
            const loc = results[0].geometry.location;
            applyPosition(loc.lat(), loc.lng(), { zoom: 16 });
            if (options.normalizeAddress !== false && results[0].formatted_address) {
              nodes.address.value = results[0].formatted_address;
            }
            setLocateStatus("");
            resolve(true);
          }
        );
      });
    }

    const url =
      "https://nominatim.openstreetmap.org/search?format=json&limit=1&countrycodes=in&q=" +
      encodeURIComponent(text);
    return fetch(url, { headers: nominatimHeaders() })
      .then(function (response) {
        return response.json();
      })
      .then(function (results) {
        if (requestId !== addressGeocodeRequest) return false;
        if (!results || !results.length) {
          if (options.showStatus) {
            setLocateStatus("Could not find that address on the map. Adjust the pin manually.");
          }
          return false;
        }
        const hit = results[0];
        const lat = parseFloat(hit.lat);
        const lng = parseFloat(hit.lon);
        if (!Number.isFinite(lat) || !Number.isFinite(lng)) return false;
        applyPosition(lat, lng, { zoom: 16 });
        if (options.normalizeAddress !== false && hit.display_name) {
          nodes.address.value = hit.display_name;
        }
        setLocateStatus("");
        return true;
      })
      .catch(function () {
        return false;
      });
  }

  function scheduleAddressGeocode(showStatus) {
    clearTimeout(geocodeTimer);
    geocodeTimer = setTimeout(function () {
      const nodes = els();
      if (!nodes.address) return;
      forwardGeocodeAddress(nodes.address.value, { showStatus: !!showStatus, normalizeAddress: false });
    }, GEOCODE_DEBOUNCE_MS);
  }

  function parseGoogleMapsUrl(raw) {
    if (!raw) return null;
    const text = String(raw).trim();
    if (!text) return null;

    const atMatch = text.match(/@(-?\d+\.\d+),(-?\d+\.\d+)/);
    if (atMatch) {
      return { lat: parseFloat(atMatch[1]), lng: parseFloat(atMatch[2]) };
    }

    const bangMatch = text.match(/!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)/);
    if (bangMatch) {
      return { lat: parseFloat(bangMatch[1]), lng: parseFloat(bangMatch[2]) };
    }

    try {
      const url = new URL(text);
      const q = url.searchParams.get("q") || url.searchParams.get("query");
      if (q) {
        const pair = q.match(/^(-?\d+\.?\d*),\s*(-?\d+\.?\d*)$/);
        if (pair) {
          return { lat: parseFloat(pair[1]), lng: parseFloat(pair[2]) };
        }
      }
      const center = url.searchParams.get("center");
      if (center) {
        const pair = center.match(/^(-?\d+\.?\d*),\s*(-?\d+\.?\d*)$/);
        if (pair) {
          return { lat: parseFloat(pair[1]), lng: parseFloat(pair[2]) };
        }
      }
    } catch (error) {
      return null;
    }
    return null;
  }

  function syncInitialLocation() {
    const nodes = els();
    const addressText = nodes.address ? nodes.address.value.trim() : "";
    if (addressText.length >= 10) {
      setLocateStatus("Matching your address on the map…");
      forwardGeocodeAddress(addressText, { showStatus: true, normalizeAddress: false }).then(function (ok) {
        if (ok) {
          setLocateStatus("Address matched on the map.");
          setTimeout(function () {
            setLocateStatus("");
          }, 2500);
        }
      });
      return;
    }
    locateUser();
  }

  function locateUser() {
    const nodes = els();
    if (!navigator.geolocation) {
      setLocateStatus("Location is not available in this browser.");
      if (!nodes.lat.value) applyPosition(DEFAULT_CENTER.lat, DEFAULT_CENTER.lng, { zoom: 14 });
      return;
    }

    setLocateStatus("Detecting your current location…");
    navigator.geolocation.getCurrentPosition(
      function (position) {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;
        applyPosition(lat, lng, { zoom: 16 });
        reverseGeocodeFromPin(lat, lng);
        setLocateStatus("Location detected. Drag the pin if you need to adjust.");
        setTimeout(function () {
          setLocateStatus("");
        }, 4000);
      },
      function () {
        setLocateStatus("Could not detect GPS. Type your address or move the pin on the map.");
        if (!nodes.lat.value) applyPosition(DEFAULT_CENTER.lat, DEFAULT_CENTER.lng, { zoom: 14 });
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
    );
  }

  function openGoogleMapsPicker() {
    const nodes = els();
    let lat = parseFloat(nodes.lat && nodes.lat.value);
    let lng = parseFloat(nodes.lng && nodes.lng.value);
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
      const addressText = nodes.address ? nodes.address.value.trim() : "";
      if (addressText.length >= 10) {
        forwardGeocodeAddress(addressText, { showStatus: true }).then(function (ok) {
          if (ok) openGoogleMapsPicker();
        });
        return;
      }
      lat = DEFAULT_CENTER.lat;
      lng = DEFAULT_CENTER.lng;
    }
    window.open(googleMapsPickerUrl(lat, lng), "_blank", "noopener,noreferrer");
    setLocateStatus("In Google Maps, drop a pin on your pickup spot, copy the link, and paste it below.");
  }

  function onMapsPasteInput() {
    const nodes = els();
    if (!nodes.mapsPaste) return;
    const parsed = parseGoogleMapsUrl(nodes.mapsPaste.value);
    if (!parsed) {
      setLocateStatus("Could not read that Google Maps link. Try copying the full URL from your browser.");
      return;
    }
    applyPosition(parsed.lat, parsed.lng, { zoom: 17 });
    reverseGeocodeFromPin(parsed.lat, parsed.lng);
    setLocateStatus("Location updated from Google Maps link.");
    setTimeout(function () {
      setLocateStatus("");
    }, 3000);
  }

  function bindAddressSync() {
    const nodes = els();
    if (!nodes.address || nodes.address.dataset.syncBound === "true") return;
    nodes.address.dataset.syncBound = "true";

    nodes.address.addEventListener("input", function () {
      scheduleAddressGeocode(false);
    });
    nodes.address.addEventListener("blur", function () {
      clearTimeout(geocodeTimer);
      forwardGeocodeAddress(nodes.address.value, { showStatus: true, normalizeAddress: true });
    });
  }

  function bindUi() {
    if (uiBound) return;
    uiBound = true;
    bindAddressSync();
    const nodes = els();
    if (nodes.locateBtn) {
      nodes.locateBtn.addEventListener("click", function () {
        locateUser();
      });
    }
    if (nodes.gmapsPickBtn) {
      nodes.gmapsPickBtn.addEventListener("click", function () {
        openGoogleMapsPicker();
      });
    }
    if (nodes.mapsPaste) {
      nodes.mapsPaste.addEventListener("change", onMapsPasteInput);
      nodes.mapsPaste.addEventListener("paste", function () {
        setTimeout(onMapsPasteInput, 50);
      });
    }
  }

  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      const existing = document.querySelector('script[src="' + src + '"]');
      if (existing) {
        if (existing.dataset.loaded === "true") {
          resolve();
          return;
        }
        existing.addEventListener("load", function () {
          resolve();
        });
        return;
      }
      const script = document.createElement("script");
      script.src = src;
      script.async = true;
      script.defer = true;
      script.onload = function () {
        script.dataset.loaded = "true";
        resolve();
      };
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }

  function loadGoogleMaps(key) {
    if (window.google && window.google.maps) {
      return Promise.resolve();
    }
    return new Promise(function (resolve, reject) {
      const cb = "__vastraGmapsInit";
      window[cb] = function () {
        delete window[cb];
        resolve();
      };
      const src =
        "https://maps.googleapis.com/maps/api/js?key=" +
        encodeURIComponent(key) +
        "&libraries=places&callback=" +
        cb;
      loadScript(src).catch(reject);
    });
  }

  function onMapReady() {
    bindUi();
    if (pendingLocate) {
      pendingLocate = false;
      syncInitialLocation();
    }
    setTimeout(function () {
      if (googleMap && window.google) {
        google.maps.event.trigger(googleMap, "resize");
      }
      if (leafletMap) leafletMap.invalidateSize();
    }, 200);
  }

  function initGoogle() {
    const nodes = els();
    if (!nodes.mapEl) return;

    googleMap = new google.maps.Map(nodes.mapEl, {
      center: DEFAULT_CENTER,
      zoom: 14,
      mapTypeControl: false,
      streetViewControl: false,
      fullscreenControl: false,
    });
    geocoder = new google.maps.Geocoder();
    googleMarker = new google.maps.Marker({
      map: googleMap,
      position: DEFAULT_CENTER,
      draggable: true,
    });

    googleMarker.addListener("dragend", function () {
      const pos = googleMarker.getPosition();
      if (pos) {
        setCoords(pos.lat(), pos.lng());
        reverseGeocodeFromPin(pos.lat(), pos.lng());
      }
    });
    googleMap.addListener("click", function (event) {
      googleMarker.setPosition(event.latLng);
      setCoords(event.latLng.lat(), event.latLng.lng());
      reverseGeocodeFromPin(event.latLng.lat(), event.latLng.lng());
    });

    if (nodes.address) {
      autocomplete = new google.maps.places.Autocomplete(nodes.address, {
        fields: ["formatted_address", "geometry", "name"],
        componentRestrictions: { country: "in" },
      });
      autocomplete.addListener("place_changed", function () {
        const place = autocomplete.getPlace();
        if (!place.geometry || !place.geometry.location) {
          setLocateStatus("Choose an address from the list so the map can match it.");
          return;
        }
        const loc = place.geometry.location;
        if (place.formatted_address) nodes.address.value = place.formatted_address;
        googleMap.panTo(loc);
        googleMap.setZoom(16);
        googleMarker.setPosition(loc);
        setCoords(loc.lat(), loc.lng());
        setLocateStatus("Address and map are in sync.");
        setTimeout(function () {
          setLocateStatus("");
        }, 2500);
      });
    }
    onMapReady();
  }

  function initLeaflet() {
    const nodes = els();
    if (!nodes.mapEl || !window.L) return;

    leafletMap = window.L.map(nodes.mapEl, { scrollWheelZoom: true }).setView(
      [DEFAULT_CENTER.lat, DEFAULT_CENTER.lng],
      14
    );
    window.L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap",
      maxZoom: 19,
    }).addTo(leafletMap);

    leafletMarker = window.L.marker([DEFAULT_CENTER.lat, DEFAULT_CENTER.lng], {
      draggable: true,
    }).addTo(leafletMap);

    leafletMarker.on("dragend", function () {
      const pos = leafletMarker.getLatLng();
      setCoords(pos.lat, pos.lng);
      reverseGeocodeFromPin(pos.lat, pos.lng);
    });
    leafletMap.on("click", function (event) {
      leafletMarker.setLatLng(event.latlng);
      setCoords(event.latlng.lat, event.latlng.lng);
      reverseGeocodeFromPin(event.latlng.lat, event.latlng.lng);
    });

    onMapReady();
  }

  function ensureMap() {
    if (initStarted) return Promise.resolve();
    const nodes = els();
    if (!nodes.mapEl) return Promise.resolve();
    initStarted = true;

    const key = apiKey();
    if (key) {
      return loadGoogleMaps(key)
        .then(function () {
          initGoogle();
        })
        .catch(function () {
          initStarted = false;
          return fallbackLeaflet();
        });
    }
    return fallbackLeaflet();
  }

  function fallbackLeaflet() {
    if (leafletMap) return Promise.resolve();
    if (!document.querySelector('link[data-leaflet-css="true"]')) {
      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
      link.dataset.leafletCss = "true";
      document.head.appendChild(link);
    }
    return loadScript("https://unpkg.com/leaflet@1.9.4/dist/leaflet.js")
      .then(function () {
        initLeaflet();
      })
      .catch(function () {
        nodesHint();
      });
  }

  function nodesHint() {
    const nodes = els();
    if (nodes.mapEl) {
      nodes.mapEl.innerHTML =
        '<p class="pickup-map-fallback">Map could not load. Type your address, or use <strong>Choose in Google Maps</strong> and paste the link below.</p>';
    }
    bindUi();
    pendingLocate = false;
    syncInitialLocation();
  }

  function resetMap() {
    const nodes = els();
    if (nodes.lat) nodes.lat.value = "";
    if (nodes.lng) nodes.lng.value = "";
    if (nodes.mapsUrl) nodes.mapsUrl.value = "";
    if (nodes.mapsPaste) nodes.mapsPaste.value = "";
    if (nodes.mapsOpen) nodes.mapsOpen.hidden = true;
    setLocateStatus("");
    pendingLocate = true;
    addressGeocodeRequest += 1;
  }

  function onModalOpen() {
    bindUi();
    pendingLocate = true;
    ensureMap().then(function () {
      setTimeout(function () {
        if ((googleMap || leafletMap) && pendingLocate) {
          pendingLocate = false;
          syncInitialLocation();
        }
      }, 350);
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    const bookModal = document.getElementById("book-modal");
    if (!bookModal) return;
    bindUi();

    const observer = new MutationObserver(function () {
      if (!bookModal.hidden) onModalOpen();
    });
    observer.observe(bookModal, { attributes: true, attributeFilter: ["hidden"] });

    document.addEventListener("click", function (event) {
      if (event.target.closest('[data-open-modal="book"]')) {
        setTimeout(onModalOpen, 50);
      }
    });
  });

  window.VastraPickupMap = {
    ensureMap,
    resetMap,
    setCoords,
    locateUser,
    syncFromAddress: function () {
      const nodes = els();
      return forwardGeocodeAddress(nodes.address && nodes.address.value, { showStatus: true });
    },
  };
})();
