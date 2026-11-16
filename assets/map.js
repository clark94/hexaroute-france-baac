(() => {
  'use strict';

  const payloadNode = document.getElementById('payload');
  const notice = document.getElementById('map-notice');
  const fmt = new Intl.NumberFormat('fr-FR');
  const state = { mode: 'clusters', gravity: 'all', dark: false };

  const available = window.L && L.markerClusterGroup && L.heatLayer;
  if (!available) {
    notice.textContent =
      'Impossible de charger Leaflet. Vérifiez la connexion Internet ou utilisez la carte Plotly de secours.';
    notice.classList.remove('is-hidden');
    return;
  }

  let data;
  try {
    data = JSON.parse(payloadNode.textContent);
  } catch {
    notice.textContent = 'Les données cartographiques ne peuvent pas être lues.';
    notice.classList.remove('is-hidden');
    return;
  }

  const points = data.points || [];
  const colors = data.color || {};

  document.getElementById('sampling-count').textContent = fmt.format(points.length);
  document.getElementById('sampling-sub').textContent = data.sampled
    ? 'points échantillonnés'
    : 'points géolocalisés';

  document.getElementById('sample-disclaimer').textContent = data.sampled
    ? `${fmt.format(data.total_metro_geocoded)} accidents géolocalisés ; ${fmt.format(points.length)} points échantillonnés (seed 42).`
    : `${fmt.format(points.length)} points géolocalisés du filtre Streamlit.`;

  const map = L.map('map', {
    preferCanvas: true,
    zoomControl: false,
    scrollWheelZoom: false
  });

  L.control.zoom({ position: 'bottomright' }).addTo(map);

  const basemap = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map);

  const basemapToggle = document.getElementById('basemap-toggle');

  function updateBasemapTheme() {
    const tiles = basemap.getContainer();
    if (tiles) {
      tiles.style.filter = state.dark
        ? 'grayscale(1) invert(1) brightness(0.85)'
        : '';
    }
    basemapToggle.setAttribute('aria-label', 'Fond de carte sombre');
    basemapToggle.setAttribute('aria-pressed', String(state.dark));
    basemapToggle.title = state.dark ? 'Passer au fond clair' : 'Passer au fond sombre';
  }

  basemapToggle.addEventListener('click', () => {
    state.dark = !state.dark;
    updateBasemapTheme();
  });
  updateBasemapTheme();

  const clusterGroup = L.markerClusterGroup({
    chunkedLoading: true,
    chunkInterval: 120,
    chunkDelay: 30,
    removeOutsideVisibleBounds: true,
    showCoverageOnHover: false,
    maxClusterRadius: 46,
    iconCreateFunction(cluster) {
      return L.divIcon({
        html: `<div><span>${fmt.format(cluster.getChildCount())}</span></div>`,
        className: 'marker-cluster',
        iconSize: L.point(44, 44)
      });
    }
  });

  let activeLayer = null;

  function htmlEscape(value) {
    return String(value ?? '—')
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
  }

  function pointColor(severity) {
    const color = colors[severity];
    return typeof color === 'string' && /^#[0-9a-f]{6}$/i.test(color)
      ? color
      : '#a4aec6';
  }

  function popup(point) {
    const color = pointColor(point.severity);
    const severity = point.severity === 'Mortel' ? 'Accident mortel' : point.severity;
    const row = (label, value) => `<span>${label}</span><strong>${htmlEscape(value)}</strong>`;

    return `<div class="popup-head"><i class="popup-dot" style="--pc:${color}"></i>${htmlEscape(severity)}</div>` +
      `<div class="popup-meta">${row('Date', point.date)}${row('Département', point.dep)}` +
      `${row('Véhicules', point.vehicles)}${row('Usagers', point.users)}` +
      `${row('Personnes tuées', point.killed)}</div>`;
  }

  function visiblePoints() {
    return state.gravity === 'all'
      ? points
      : points.filter(point => point.severity === state.gravity);
  }

  function zoomToFiltered(selection) {
    if (!selection.length || (selection.length > 1100 && state.gravity === 'all')) {
      map.setView([46.6, 2.1], 5);
      return;
    }

    const bounds = L.latLngBounds(selection.map(point => [point.lat, point.lng]));
    if (bounds.isValid()) {
      map.fitBounds(bounds.pad(0.13), { maxZoom: 11, animate: true });
    }
  }

  function draw() {
    if (activeLayer) map.removeLayer(activeLayer);
    clusterGroup.clearLayers();

    const selection = visiblePoints();
    const fatal = selection.filter(point => point.severity === 'Mortel').length;
    const departments = new Set(selection.map(point => point.dep)).size;
    const modeLabels = { clusters: 'REGROUPEMENTS', points: 'POINTS', heat: 'DENSITÉ' };

    document.getElementById('visible-number').textContent = fmt.format(selection.length);
    document.getElementById('visible-label').textContent = state.gravity === 'all'
      ? 'points sélectionnés'
      : 'points de la gravité choisie';
    document.getElementById('fatal-count').textContent = fmt.format(fatal);
    document.getElementById('dep-count').textContent = fmt.format(departments);
    document.getElementById('active-mode').textContent = modeLabels[state.mode];

    if (state.mode === 'heat') {
      const heat = selection.map(point => [
        point.lat,
        point.lng,
        point.severity === 'Mortel' ? 0.9 : 0.45
      ]);
      activeLayer = L.heatLayer(heat, {
        radius: 21,
        blur: 17,
        minOpacity: 0.28,
        maxZoom: 11,
        gradient: { 0.15: '#307c9b', 0.4: '#59d8db', 0.7: '#fbd08c', 1: '#f17185' }
      }).addTo(map);
    } else if (state.mode === 'points') {
      const group = L.layerGroup();
      selection.forEach(point => {
        L.circleMarker([point.lat, point.lng], {
          radius: 3,
          weight: 0.7,
          color: '#f5ffff',
          fillColor: pointColor(point.severity),
          fillOpacity: 0.75
        }).bindPopup(popup(point), { maxWidth: 260 }).addTo(group);
      });
      activeLayer = group.addTo(map);
    } else {
      const markers = selection.map(point =>
        L.marker([point.lat, point.lng], {
          icon: L.divIcon({
            className: '',
            html: `<div class="marker" style="--mk:${pointColor(point.severity)}"></div>`,
            iconSize: [14, 14],
            iconAnchor: [7, 7]
          })
        }).bindPopup(popup(point), { maxWidth: 260 })
      );
      clusterGroup.addLayers(markers);
      activeLayer = clusterGroup.addTo(map);
    }

    if (!selection.length) {
      notice.textContent = 'Aucun point cartographique dans ce filtre de gravité.';
    }
    notice.classList.toggle('is-hidden', selection.length > 0);
  }

  const modeButtons = document.querySelectorAll('.tool');
  modeButtons.forEach(button => {
    button.addEventListener('click', () => {
      state.mode = button.dataset.mode;
      modeButtons.forEach(other => {
        const selected = other.dataset.mode === state.mode;
        other.classList.toggle('is-active', selected);
        other.setAttribute('aria-pressed', String(selected));
      });
      draw();
    });
  });

  document.getElementById('severity').addEventListener('change', event => {
    state.gravity = event.target.value;
    draw();
    zoomToFiltered(visiblePoints());
  });

  document.getElementById('recenter').addEventListener('click', () => {
    zoomToFiltered(visiblePoints());
  });

  map.setView([46.6, 2.1], 5);
  draw();
  zoomToFiltered(visiblePoints());
  setTimeout(() => map.invalidateSize(), 250);
})();