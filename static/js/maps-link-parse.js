(function (global) {
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

  global.VastraMapsLink = { parseGoogleMapsUrl };
})(window);
