/* Radar Contábil — painel. Sem bibliotecas externas. */
(function () {
  "use strict";

  const POR_PAGINA = 60;
  const DIA = 86400000;

  // ---------- armazenamento local (tolerante a falhas, ex.: aba anônima) ----------
  const guardar = {
    ler(chave, padrao) {
      try { const v = localStorage.getItem("radar." + chave); return v == null ? padrao : JSON.parse(v); }
      catch (e) { return padrao; }
    },
    gravar(chave, valor) {
      try { localStorage.setItem("radar." + chave, JSON.stringify(valor)); } catch (e) { /* sem espaço/bloqueado */ }
    },
  };

  const estado = {
    indice: null,
    itens: [],              // todos os itens carregados
    mesesCarregados: new Set(),
    areas: [],
    corDaArea: {},
    nomeDaArea: {},
    lidos: new Set(guardar.ler("lidos", [])),
    favoritos: guardar.ler("favoritos", {}),   // id -> item (guarda o item inteiro)
    visitaAnterior: null,
    pagina: 1,
    filtros: Object.assign(
      { areas: [], fonte: "", tipo: "", periodo: "30", mostrar: "todos", esconderOutros: true, busca: "" },
      guardar.ler("filtros", {}),
      { busca: "" }
    ),
  };

  // "Novo desde a última visita": a referência vale para a sessão inteira.
  (function () {
    let anterior = null;
    try { anterior = sessionStorage.getItem("radar.visitaAnterior"); } catch (e) { /* ignora */ }
    if (anterior === null) {
      anterior = guardar.ler("ultimaVisita", "");
      try { sessionStorage.setItem("radar.visitaAnterior", anterior); } catch (e) { /* ignora */ }
    }
    estado.visitaAnterior = anterior || null;
    guardar.gravar("ultimaVisita", new Date().toISOString().slice(0, 19) + "Z");
  })();

  const $ = (id) => document.getElementById(id);
  const el = {
    atualizado: $("atualizado"), areas: $("areas"), busca: $("busca"), lista: $("lista"),
    mais: $("btn-mais"), vazio: $("vazio"), resumo: $("resumo-lista"), painel: $("painel-filtros"),
    btnFiltros: $("btn-filtros"), contadorFiltros: $("contador-filtros"), fonte: $("f-fonte"),
    tipo: $("f-tipo"), periodo: $("f-periodo"), mostrar: $("f-mostrar"), outros: $("f-outros"),
    fontesStatus: $("fontes-status"),
  };

  // ---------- utilidades ----------
  function semAcento(t) {
    return (t || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  }
  function escapar(t) {
    return String(t == null ? "" : t).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }
  function linkSeguro(u) {
    return /^https?:\/\//i.test(u || "") ? u : "#";
  }
  function formatarData(iso) {
    const d = new Date(iso);
    if (isNaN(d)) return "";
    const hoje = new Date(); hoje.setHours(0, 0, 0, 0);
    const hora = d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
    if (d >= hoje) return "hoje, " + hora;
    if (d >= new Date(hoje - DIA)) return "ontem, " + hora;
    return d.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric" });
  }
  function rotuloDia(iso) {
    const d = new Date(iso);
    const hoje = new Date(); hoje.setHours(0, 0, 0, 0);
    if (d >= hoje) return "Hoje";
    if (d >= new Date(hoje - DIA)) return "Ontem";
    const t = d.toLocaleDateString("pt-BR", { weekday: "long", day: "2-digit", month: "long" });
    return t.charAt(0).toUpperCase() + t.slice(1);
  }
  function hora(iso) {
    return new Date(iso).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
  }
  function ehNovo(item) {
    return !!estado.visitaAnterior && item.coletado_em > estado.visitaAnterior;
  }
  function salvarFiltros() {
    const f = Object.assign({}, estado.filtros); delete f.busca;
    guardar.gravar("filtros", f);
  }

  // ---------- carregar dados ----------
  async function buscarJSON(caminho) {
    const r = await fetch(caminho, { cache: "no-cache" });
    if (!r.ok) throw new Error(caminho + ": " + r.status);
    return r.json();
  }

  function mesesNecessarios() {
    const meses = (estado.indice && estado.indice.meses) || [];
    if (estado.filtros.periodo === "tudo" || estado.filtros.mostrar === "favoritos") return meses;
    const limite = new Date(Date.now() - 32 * DIA).toISOString().slice(0, 7);
    return meses.filter((m) => m >= limite);
  }

  async function carregarMeses() {
    const faltando = mesesNecessarios().filter((m) => !estado.mesesCarregados.has(m));
    if (!faltando.length) return;
    const lotes = await Promise.all(faltando.map((m) => buscarJSON("dados/" + m + ".json").catch(() => [])));
    faltando.forEach((m) => estado.mesesCarregados.add(m));
    const vistos = new Set(estado.itens.map((i) => i.id));
    lotes.flat().forEach((i) => { if (!vistos.has(i.id)) { vistos.add(i.id); estado.itens.push(i); } });
    estado.itens.sort((a, b) => (a.data < b.data ? 1 : a.data > b.data ? -1 : 0));
  }

  async function iniciar() {
    try {
      estado.indice = await buscarJSON("dados/indice.json");
    } catch (e) {
      el.atualizado.textContent = "Ainda não há dados. Aguarde a primeira coleta.";
      el.vazio.hidden = false;
      el.vazio.textContent = "Os dados aparecem aqui depois da primeira coleta automática.";
      return;
    }
    estado.areas = estado.indice.areas || [];
    estado.areas.forEach((a) => { estado.corDaArea[a.id] = a.cor; estado.nomeDaArea[a.id] = a.nome; });
    const at = new Date(estado.indice.atualizado_em);
    el.atualizado.textContent = "Atualizado " + formatarData(at.toISOString()) + " · " + (estado.indice.total || 0) + " itens";
    mostrarStatusFontes();
    await carregarMeses();
    atualizarFavoritosGuardados();
    preencherFontes();
    aplicarFiltrosNaTela();
    desenhar();
  }

  // Mantém a cópia dos favoritos em dia (áreas podem mudar com a reclassificação).
  function atualizarFavoritosGuardados() {
    let mudou = false;
    estado.itens.forEach((i) => { if (estado.favoritos[i.id]) { estado.favoritos[i.id] = i; mudou = true; } });
    if (mudou) guardar.gravar("favoritos", estado.favoritos);
  }

  function mostrarStatusFontes() {
    const fontes = (estado.indice && estado.indice.fontes) || [];
    el.fontesStatus.innerHTML = fontes.map((f) => {
      const situacao = f.ok
        ? '<span class="ok">✓ funcionando</span> · ' + f.lidos + " lidos, " + f.novos + " novos"
        : '<span class="erro">✗ com erro</span> · ' + escapar(f.erro);
      return "<li><strong>" + escapar(f.nome) + "</strong> — " + situacao + '<br><span class="sutil">' + escapar(f.url) + "</span></li>";
    }).join("") || "<li>Nenhuma informação ainda.</li>";
  }

  function preencherFontes() {
    const nomes = new Set(estado.itens.map((i) => i.fonte));
    ((estado.indice && estado.indice.fontes) || []).forEach((f) => nomes.add(f.nome));
    const atual = estado.filtros.fonte;
    el.fonte.innerHTML = '<option value="">Todas as fontes</option>' +
      [...nomes].sort((a, b) => a.localeCompare(b, "pt-BR")).map((n) => '<option value="' + escapar(n) + '">' + escapar(n) + "</option>").join("");
    el.fonte.value = nomes.has(atual) ? atual : "";
    estado.filtros.fonte = el.fonte.value;
  }

  function aplicarFiltrosNaTela() {
    el.tipo.value = estado.filtros.tipo;
    el.periodo.value = estado.filtros.periodo;
    el.mostrar.value = estado.filtros.mostrar;
    el.outros.checked = estado.filtros.esconderOutros;
  }

  // ---------- filtrar ----------
  function filtrarSemArea() {
    const f = estado.filtros;
    let base = estado.itens;
    if (f.mostrar === "favoritos") {
      const carregados = new Set(base.map((i) => i.id));
      base = base.filter((i) => estado.favoritos[i.id])
        .concat(Object.values(estado.favoritos).filter((i) => !carregados.has(i.id)));
      base.sort((a, b) => (a.data < b.data ? 1 : -1));
    }
    let desde = null;
    if (f.periodo === "hoje") { const h = new Date(); h.setHours(0, 0, 0, 0); desde = h.toISOString(); }
    else if (f.periodo !== "tudo") desde = new Date(Date.now() - Number(f.periodo) * DIA).toISOString();
    const termos = semAcento(f.busca).split(/\s+/).filter(Boolean);

    return base.filter((i) => {
      if (desde && f.mostrar !== "favoritos" && i.data < desde) return false;
      if (f.fonte && i.fonte !== f.fonte) return false;
      if (f.tipo && i.tipo !== f.tipo) return false;
      if (f.mostrar === "novos" && !ehNovo(i)) return false;
      if (f.mostrar === "naolidos" && estado.lidos.has(i.id)) return false;
      if (f.esconderOutros && !f.areas.includes("outros") && i.areas.length === 1 && i.areas[0] === "outros") return false;
      if (termos.length) {
        const alvo = semAcento(i.titulo + " " + i.resumo + " " + i.fonte + " " + (i.categorias_fonte || []).join(" "));
        if (!termos.every((t) => alvo.includes(t))) return false;
      }
      return true;
    });
  }

  function filtrar(semArea) {
    const sel = estado.filtros.areas;
    if (!sel.length) return semArea;
    return semArea.filter((i) => i.areas.some((a) => sel.includes(a)));
  }

  // ---------- desenhar ----------
  function desenharChips(semArea) {
    const contagem = {};
    semArea.forEach((i) => i.areas.forEach((a) => { contagem[a] = (contagem[a] || 0) + 1; }));
    const sel = estado.filtros.areas;
    let html = '<button class="chip" data-area="" aria-pressed="' + (sel.length === 0) + '" style="--cor:#1f5a85">Todas</button>';
    estado.areas.forEach((a) => {
      if (a.id === "outros" && estado.filtros.esconderOutros && !sel.includes("outros")) return;
      html += '<button class="chip" data-area="' + escapar(a.id) + '" aria-pressed="' + sel.includes(a.id) +
        '" style="--cor:' + escapar(a.cor) + '"><span class="ponto"></span>' + escapar(a.nome) +
        ' <span class="qtd">' + (contagem[a.id] || 0) + "</span></button>";
    });
    el.areas.innerHTML = html;
  }

  function cartao(i) {
    const lido = estado.lidos.has(i.id);
    const fav = !!estado.favoritos[i.id];
    const etiquetas = i.areas.map((a) =>
      '<span class="etiqueta" style="--cor:' + escapar(estado.corDaArea[a] || "#7f8c8d") + '">' + escapar(estado.nomeDaArea[a] || a) + "</span>").join("");
    const corPrincipal = estado.corDaArea[i.areas[0]] || "#7f8c8d";
    return '<li class="item' + (lido ? " lido" : "") + '" data-id="' + escapar(i.id) + '" style="--cor-area:' + escapar(corPrincipal) + '">' +
      '<div class="item-meta">' +
        (ehNovo(i) ? '<span class="selo-novo">NOVO</span>' : "") +
        (i.tipo === "projeto" ? '<span class="selo-pl">Projeto de lei</span>' : "") +
        '<span class="fonte">' + escapar(i.fonte) + "</span><span>·</span><time datetime=\"" + escapar(i.data) + '">' + hora(i.data) + "</time>" +
      "</div>" +
      '<a class="item-titulo" href="' + escapar(linkSeguro(i.link)) + '" target="_blank" rel="noopener noreferrer">' + escapar(i.titulo) + "</a>" +
      (i.resumo ? '<p class="item-resumo">' + escapar(i.resumo) + "</p>" : "") +
      '<div class="item-rodape"><div class="etiquetas">' + etiquetas + "</div>" +
        '<div class="acoes">' +
          '<button class="btn-fav" aria-pressed="' + fav + '" title="' + (fav ? "Tirar dos favoritos" : "Favoritar") + '" aria-label="Favorito">' +
            '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path d="M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 16.9l-5.2 2.7 1-5.8L3.5 9.7l5.9-.9z" fill="' + (fav ? "currentColor" : "none") + '" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg></button>' +
          '<button class="btn-lido" aria-pressed="' + lido + '" title="' + (lido ? "Marcar como não lido" : "Marcar como lido") + '" aria-label="Lido">' +
            '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path d="M4 12.5l5 5L20 6.5" fill="none" stroke="currentColor" stroke-width="' + (lido ? "2.6" : "1.8") + '" stroke-linecap="round" stroke-linejoin="round"/></svg></button>' +
        "</div></div></li>";
  }

  function desenhar() {
    const semArea = filtrarSemArea();
    const lista = filtrar(semArea);
    desenharChips(semArea);
    const visiveis = lista.slice(0, estado.pagina * POR_PAGINA);
    let diaAtual = "", html = "";
    visiveis.forEach((i) => {
      const dia = rotuloDia(i.data);
      if (dia !== diaAtual) { diaAtual = dia; html += '<li class="dia" aria-hidden="false"><h2>' + escapar(dia) + "</h2></li>"; }
      html += cartao(i);
    });
    el.lista.innerHTML = html;
    el.mais.hidden = visiveis.length >= lista.length;
    el.vazio.hidden = lista.length > 0;
    const novos = lista.filter(ehNovo).length;
    el.resumo.textContent = lista.length + (lista.length === 1 ? " item" : " itens") + (novos ? " · " + novos + " novos desde a última visita" : "");
    const f = estado.filtros;
    const ativos = [f.fonte, f.tipo, f.mostrar !== "todos", f.periodo !== "30", !f.esconderOutros].filter(Boolean).length;
    el.contadorFiltros.hidden = !ativos;
    el.contadorFiltros.textContent = ativos;
  }

  // ---------- ações ----------
  function gravarLidos() {
    guardar.gravar("lidos", [...estado.lidos].slice(-8000));
  }
  function marcarLido(id, valor) {
    if (valor) estado.lidos.add(id); else estado.lidos.delete(id);
    gravarLidos();
  }
  function acharItem(id) {
    return estado.itens.find((i) => i.id === id) || estado.favoritos[id];
  }

  el.lista.addEventListener("click", (ev) => {
    const li = ev.target.closest(".item");
    if (!li) return;
    const id = li.dataset.id;
    if (ev.target.closest(".item-titulo")) { marcarLido(id, true); li.classList.add("lido"); return; }
    if (ev.target.closest(".btn-fav")) {
      if (estado.favoritos[id]) delete estado.favoritos[id]; else estado.favoritos[id] = acharItem(id);
      guardar.gravar("favoritos", estado.favoritos);
      desenhar();
    } else if (ev.target.closest(".btn-lido")) {
      marcarLido(id, !estado.lidos.has(id));
      desenhar();
    }
  });
  // Clique com botão do meio também conta como lido
  el.lista.addEventListener("auxclick", (ev) => {
    const a = ev.target.closest(".item-titulo");
    if (a) { const li = a.closest(".item"); marcarLido(li.dataset.id, true); li.classList.add("lido"); }
  });

  el.areas.addEventListener("click", (ev) => {
    const b = ev.target.closest(".chip");
    if (!b) return;
    const id = b.dataset.area;
    const sel = estado.filtros.areas;
    if (!id) estado.filtros.areas = [];
    else if (sel.includes(id)) estado.filtros.areas = sel.filter((a) => a !== id);
    else estado.filtros.areas = sel.concat(id);
    estado.pagina = 1; salvarFiltros(); desenhar();
  });

  let espera;
  el.busca.addEventListener("input", () => {
    clearTimeout(espera);
    espera = setTimeout(() => { estado.filtros.busca = el.busca.value; estado.pagina = 1; desenhar(); }, 150);
  });

  async function aoMudarFiltro() {
    Object.assign(estado.filtros, {
      fonte: el.fonte.value, tipo: el.tipo.value, periodo: el.periodo.value,
      mostrar: el.mostrar.value, esconderOutros: el.outros.checked,
    });
    estado.pagina = 1; salvarFiltros();
    await carregarMeses();
    preencherFontes();
    desenhar();
  }
  [el.fonte, el.tipo, el.periodo, el.mostrar, el.outros].forEach((c) => c.addEventListener("change", aoMudarFiltro));

  el.btnFiltros.addEventListener("click", () => {
    const abrir = !el.painel.classList.contains("aberto");
    el.painel.classList.toggle("aberto", abrir);
    el.btnFiltros.setAttribute("aria-expanded", String(abrir));
  });
  $("btn-limpar").addEventListener("click", () => {
    estado.filtros = { areas: [], fonte: "", tipo: "", periodo: "30", mostrar: "todos", esconderOutros: true, busca: "" };
    el.busca.value = "";
    aplicarFiltrosNaTela(); el.fonte.value = ""; aoMudarFiltro();
  });
  $("btn-ler-todos").addEventListener("click", () => {
    filtrar(filtrarSemArea()).forEach((i) => estado.lidos.add(i.id));
    gravarLidos(); desenhar();
  });
  el.mais.addEventListener("click", () => { estado.pagina += 1; desenhar(); });

  // ---------- app instalável (funciona offline com a última versão baixada) ----------
  if ("serviceWorker" in navigator && location.protocol !== "file:") {
    window.addEventListener("load", () => { navigator.serviceWorker.register("sw.js").catch(() => {}); });
  }

  iniciar();
})();
