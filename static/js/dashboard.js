(function () {
  if (!window.Chart) return;

  const PALETA = {
    primary: "#1e3a5f",
    primarySoft: "rgba(30, 58, 95, 0.16)",
    accent: "#c7923e",
    accentSoft: "rgba(199, 146, 62, 0.20)",
    teal: "#0f7b5f",
    tealSoft: "rgba(15, 123, 95, 0.18)",
    roxo: "#6d5bd0",
    roxoSoft: "rgba(109, 91, 208, 0.18)",
  };

  const filtros = {
    associacao: document.getElementById("filtro-associacao"),
    municipio: document.getElementById("filtro-municipio"),
    igreja: document.getElementById("filtro-igreja"),
  };
  const status = document.getElementById("painel-status");

  const graficos = {
    piramide: new Chart(document.getElementById("grafico-piramide"), {
      type: "bar",
      data: { labels: [], datasets: [{ label: "Membros", data: [], backgroundColor: PALETA.primary, borderRadius: 8 }] },
      options: {
        indexAxis: "y",
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { x: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: "rgba(15,23,42,0.08)" } }, y: { grid: { display: false } } },
      },
    }),
    organizacoes: new Chart(document.getElementById("grafico-organizacoes"), {
      type: "doughnut",
      data: {
        labels: ["HD", "ERV", "Embaixadores do Rei"],
        datasets: [{ data: [0, 0, 0], backgroundColor: [PALETA.primary, PALETA.accent, PALETA.teal], borderWidth: 0, hoverOffset: 8 }],
      },
      options: { responsive: true, cutout: "62%", plugins: { legend: { position: "bottom" } } },
    }),
    vocacional: new Chart(document.getElementById("grafico-vocacional"), {
      type: "bar",
      data: { labels: [], datasets: [{ label: "Voluntários", data: [], backgroundColor: PALETA.roxo, borderRadius: 8 }] },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: "rgba(15,23,42,0.08)" } }, x: { grid: { display: false } } },
      },
    }),
  };

  const ROTULOS_VOCACIONAIS = {
    construcao_civil: "Construção civil",
    saude: "Saúde",
    logistica: "Logística",
    ensino: "Ensino",
    administrativo: "Administrativo",
    outro: "Outro",
  };

  function valor(valorNumerico) {
    return valorNumerico === null || valorNumerico === undefined ? "—" : valorNumerico;
  }

  function parametros() {
    const params = new URLSearchParams();
    Object.entries(filtros).forEach(([chave, campo]) => {
      if (campo && campo.value) params.set(chave, campo.value);
    });
    return params.toString();
  }

  async function carregar() {
    if (status) status.textContent = "Atualizando indicadores…";
    try {
      const resposta = await fetch(`/api/censo/indicadores/?${parametros()}`, {
        headers: { Accept: "application/json" },
      });
      if (!resposta.ok) throw new Error("Falha ao carregar");
      const dados = await resposta.json();

      document.getElementById("kpi-total").textContent = valor(dados.total_membros);
      const cobertura = dados.cobertura_geografica || {};
      document.getElementById("kpi-cobertura").textContent = `${cobertura.percentual ?? 0}%`;
      document.getElementById("kpi-cobertura-hint").textContent =
        `${cobertura.municipios_com_organizacao ?? 0} de ${cobertura.total_municipios ?? 139} municípios`;

      const orgs = dados.por_organizacao || {};
      document.getElementById("kpi-hd").textContent = valor(orgs.HD);
      document.getElementById("kpi-erv").textContent = valor(orgs.ERV);
      document.getElementById("kpi-er").textContent = valor(orgs.ER);

      const piramide = dados.piramide_etaria || {};
      const faixas = ["9-11", "12-17", "18-29", "30-59", "60+"];
      graficos.piramide.data.labels = faixas.map((faixa) => `${faixa} anos`);
      graficos.piramide.data.datasets[0].data = faixas.map((faixa) => piramide[faixa] ?? 0);
      graficos.piramide.update();

      graficos.organizacoes.data.datasets[0].data = [orgs.HD ?? 0, orgs.ERV ?? 0, orgs.ER ?? 0];
      graficos.organizacoes.update();

      const vocacional = dados.banco_vocacional || {};
      const areas = Object.keys(vocacional);
      graficos.vocacional.data.labels = areas.length
        ? areas.map((area) => ROTULOS_VOCACIONAIS[area] || area)
        : ["Sem dados"];
      graficos.vocacional.data.datasets[0].data = areas.length
        ? areas.map((area) => vocacional[area] ?? 0)
        : [0];
      graficos.vocacional.update();

      if (status) {
        status.textContent = `Indicadores atualizados às ${new Date().toLocaleTimeString("pt-BR")}.`;
      }
    } catch (erro) {
      if (status) status.textContent = "Não foi possível carregar os indicadores.";
    }
  }

  Object.values(filtros).forEach((campo) => {
    if (campo) campo.addEventListener("change", carregar);
  });

  carregar();
})();
