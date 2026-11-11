(function () {
  const toggle = document.querySelector(".nav-toggle");
  const nav = document.getElementById("menu-principal");

  if (toggle && nav) {
    toggle.addEventListener("click", () => {
      const aberto = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", String(aberto));
    });
    nav.addEventListener("click", (event) => {
      if (event.target.closest("a")) {
        nav.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
      }
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        nav.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  document.querySelectorAll("details.nav-menu").forEach((menu) => {
    document.addEventListener("click", (event) => {
      if (!menu.contains(event.target)) menu.open = false;
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") menu.open = false;
    });
  });

  document.querySelectorAll(".field .input").forEach((input) => {
    if (input.value) input.classList.add("has-value");
    input.addEventListener("change", () => {
      input.classList.toggle("has-value", Boolean(input.value));
    });
  });

  document.querySelectorAll(".btn").forEach((botao) => {
    botao.addEventListener("click", (event) => {
      const circulo = document.createElement("span");
      const tamanho = Math.max(botao.clientWidth, botao.clientHeight);
      const rect = botao.getBoundingClientRect();
      circulo.className = "ripple";
      circulo.style.width = circulo.style.height = `${tamanho}px`;
      circulo.style.left = `${event.clientX - rect.left - tamanho / 2}px`;
      circulo.style.top = `${event.clientY - rect.top - tamanho / 2}px`;
      botao.appendChild(circulo);
      setTimeout(() => circulo.remove(), 650);
    });
  });

  document.querySelectorAll(".snackbar").forEach((snackbar) => {
    setTimeout(() => {
      snackbar.classList.add("is-hide");
      setTimeout(() => snackbar.remove(), 350);
    }, 6000);
  });
})();
