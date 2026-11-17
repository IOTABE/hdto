(function () {
  const element = document.getElementById("mapa");
  if (!element || !window.L) return;

  const status = document.getElementById("mapa-status");
  const map = L.map(element).setView([-10.18, -48.33], 7);

  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contribuidores',
  }).addTo(map);

  const cluster = L.markerClusterGroup();
  map.addLayer(cluster);

  const svgIgreja = `
    <svg xmlns="http://www.w3.org/2000/svg" width="32" height="44" viewBox="0 0 32 44">
      <path fill="#1e3a5f" stroke="#ffffff" stroke-width="2"
        d="M16 1C8.3 1 2 7.3 2 15c0 10 14 27 14 27s14-17 14-27C30 7.3 23.7 1 16 1z"/>
      <path fill="#ffffff" d="M15 8h2v4h4v2h-4v9h-2v-9h-4v-2h4z"/>
    </svg>`;
  const iconeIgreja = L.icon({
    iconUrl: "data:image/svg+xml;charset=UTF-8," + encodeURIComponent(svgIgreja),
    iconSize: [32, 44],
    iconAnchor: [16, 42],
    popupAnchor: [0, -38],
  });

  function popup(ponto) {
    const organizacoes = (ponto.organizacoes || [])
      .map((org) => `<li>${org.tipo}${org.dia ? " — " + org.dia : ""}</li>`)
      .join("");
    return `
      <strong>${ponto.nome}</strong><br>
      ${ponto.pastor ? "Pastor: " + ponto.pastor + "<br>" : ""}
      ${ponto.municipio} — ${ponto.associacao}
      ${organizacoes ? "<ul>" + organizacoes + "</ul>" : ""}
      <a target="_blank" rel="noopener"
         href="https://www.google.com/maps/dir/?api=1&destination=${ponto.lat},${ponto.lng}">Rotas</a>
    `;
  }

  async function carregar(tipo) {
    status.textContent = "Carregando…";
    const params = new URLSearchParams();
    if (tipo) params.set("tipo", tipo);
    try {
      const resposta = await fetch("/api/mapa/pontos/?" + params.toString());
      const dados = await resposta.json();
      cluster.clearLayers();
      dados.pontos.forEach((ponto) => {
        cluster.addLayer(
          L.marker([ponto.lat, ponto.lng], {
            icon: iconeIgreja,
            alt: ponto.nome,
            title: ponto.nome,
          }).bindPopup(popup(ponto))
        );
      });
      if (dados.pontos.length) map.fitBounds(cluster.getBounds().pad(0.15));
      status.textContent = `${dados.total} congregação(ões) encontrada(s).`;
    } catch (erro) {
      status.textContent = "Não foi possível carregar o mapa.";
    }
  }

  const filtros = document.getElementById("filtros");
  if (filtros) {
    filtros.addEventListener("submit", (evento) => {
      evento.preventDefault();
      carregar(new FormData(filtros).get("tipo"));
    });
  }
  carregar("");
})();
