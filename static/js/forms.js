(function () {
  const form = document.querySelector("[data-member-form]");
  if (!form) return;

  const nascimento = document.getElementById("id_data_nascimento");
  const secao = form.querySelector("[data-guardian]");
  if (!nascimento || !secao) return;

  function idade(data) {
    const hoje = new Date();
    let anos = hoje.getFullYear() - data.getFullYear();
    const mes = hoje.getMonth() - data.getMonth();
    if (mes < 0 || (mes === 0 && hoje.getDate() < data.getDate())) anos -= 1;
    return anos;
  }

  function atualizar() {
    if (!nascimento.value) {
      secao.hidden = true;
      return;
    }
    const data = new Date(`${nascimento.value}T00:00:00`);
    if (Number.isNaN(data.getTime())) {
      secao.hidden = true;
      return;
    }
    secao.hidden = idade(data) >= 18;
  }

  nascimento.addEventListener("change", atualizar);
  atualizar();
})();
