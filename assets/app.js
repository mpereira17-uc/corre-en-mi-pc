/* ¿Corre en mi PC? — comparador en el navegador.
   El PC del visitante se guarda solo en su navegador (localStorage). No se envía a ningún lado.
   Todo el texto se pone con textContent: nunca innerHTML con datos. */
(function () {
  "use strict";
  var CLAVE = "cemp-pc-v1";
  var enMemoria = null; // si el navegador bloquea localStorage
  var hardware = null;

  function leerPC() {
    try {
      var v = JSON.parse(localStorage.getItem(CLAVE));
      if (v && typeof v === "object") return v;
    } catch (e) { /* almacenamiento bloqueado */ }
    return enMemoria;
  }
  function guardarPC(pc) {
    enMemoria = pc;
    try { localStorage.setItem(CLAVE, JSON.stringify(pc)); } catch (e) { /* sigue en memoria */ }
  }

  function normalizar(t) {
    t = String(t || "").normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase();
    t = t.replace(/\(tm\)|\(r\)|™|®/g, " ").replace(/[^a-z0-9]+/g, " ");
    t = t.replace(/([a-z])(\d)/g, "$1 $2").replace(/(\d)([a-z])/g, "$1 $2");
    return " " + t.replace(/\s+/g, " ").trim() + " ";
  }

  // Busca el modelo en la tabla: primero igual, luego el nombre más largo contenido en lo escrito.
  function buscarModelo(texto, tabla) {
    if (!texto || !tabla) return null;
    var n = normalizar(texto), mejor = null;
    Object.keys(tabla).forEach(function (k) {
      var nk = normalizar(k);
      if (nk === n) mejor = { nombre: k, pts: tabla[k], largo: 9999 };
      else if (n.indexOf(nk) !== -1 && (!mejor || nk.length > mejor.largo)) mejor = { nombre: k, pts: tabla[k], largo: nk.length };
    });
    return mejor;
  }

  function num(v) { return v === undefined || v === "" ? null : Number(v); }

  function nivel(el, cual, pc) {
    var conocidos = 0, falla = false;
    [["G", pc.gpuPts], ["C", pc.cpuPts], ["R", pc.ram]].forEach(function (par) {
      var req = num(el.dataset[cual + par[0]]);
      if (req === null || par[1] === null || par[1] === undefined) return;
      conocidos++;
      if (par[1] < req) falla = true;
    });
    return conocidos ? (falla ? "no" : "si") : null;
  }

  function veredicto(el, pc) {
    var r = nivel(el, "rec", pc), m = nivel(el, "min", pc);
    if (m === "no") return "no";
    if (r === "si") return "rec";
    if (m === "si") return "min";
    return "?";
  }

  var ETIQUETA = { rec: "Corre en alto", min: "Corre en bajo", no: "No corre", "?": "Sin datos" };

  function resumenPC(pc) {
    var partes = [];
    if (pc.gpu) partes.push(pc.gpu);
    if (pc.cpu) partes.push(pc.cpu);
    if (pc.ram) partes.push(pc.ram + " GB");
    return partes.join(" · ");
  }

  // ---------- Cabecera ----------
  function pintarChip(pc) {
    var chip = document.querySelector("[data-mipc-chip]");
    if (!chip) return;
    if (pc) { chip.textContent = resumenPC(pc) || "Mi PC"; chip.setAttribute("data-listo", ""); chip.title = "Cambiar mi PC"; }
    else { chip.textContent = "Configura tu PC"; chip.removeAttribute("data-listo"); }
  }

  // ---------- Listas de juegos ----------
  var filtroActual = "todos";
  function pintarListas(pc) {
    document.querySelectorAll(".fila").forEach(function (fila) {
      var chip = fila.querySelector("[data-veredicto]");
      if (!pc) { fila.removeAttribute("data-v"); chip.removeAttribute("data-v"); chip.textContent = "Ver"; return; }
      var v = veredicto(fila, pc);
      fila.setAttribute("data-v", v);
      chip.setAttribute("data-v", v);
      chip.textContent = ETIQUETA[v];
    });
    var aviso = document.querySelector("[data-sin-pc]");
    if (aviso) aviso.hidden = !!pc;
    document.querySelectorAll("[data-filtro]").forEach(function (b) {
      if (b.dataset.filtro !== "todos") b.disabled = !pc;
    });
    if (!pc) filtroActual = "todos";
    filtrar();
  }

  function filtrar() {
    var lista = document.querySelector("[data-lista]");
    if (!lista) return;
    var caja = document.querySelector("[data-buscar]");
    var q = caja ? normalizar(caja.value).trim() : "";
    var visibles = 0;
    lista.querySelectorAll(".fila").forEach(function (fila) {
      var v = fila.getAttribute("data-v");
      var okFiltro = filtroActual === "todos" ||
        (filtroActual === "si" && (v === "rec" || v === "min")) ||
        (filtroActual === "rec" && v === "rec") ||
        (filtroActual === "no" && v === "no");
      var okTexto = !q || normalizar(fila.dataset.n).indexOf(q) !== -1;
      fila.hidden = !(okFiltro && okTexto);
      if (!fila.hidden) visibles++;
    });
    var vacio = document.querySelector("[data-vacio]");
    if (vacio) vacio.hidden = visibles > 0;
    document.querySelectorAll("[data-filtro]").forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.dataset.filtro === filtroActual));
    });
  }

  // ---------- Ficha de un juego ----------
  var TEXTOS = {
    rec: ["Sí, lo corre en calidad alta", "Tu PC iguala o supera los requisitos recomendados."],
    min: ["Sí, lo corre en calidad baja", "Cumples los mínimos pero no los recomendados: baja la resolución o la calidad gráfica."],
    no: ["No, tu PC se queda corto", "Al menos un componente está por debajo del mínimo. Abajo ves cuál."],
    "?": ["No pudimos comparar", "No reconocemos los modelos que pide este juego o no nos diste ese dato. Revisa la tabla con el texto de Steam."]
  };

  function pintarMedidor(med, juicio, pc) {
    var k = med.dataset.medidor; // g, c o r
    var K = k.toUpperCase();
    var mn = num(juicio.dataset["min" + K]), rc = num(juicio.dataset["rec" + K]);
    var tuyo = k === "g" ? pc.gpuPts : k === "c" ? pc.cpuPts : pc.ram;
    tuyo = tuyo === undefined ? null : tuyo;
    var estado = med.querySelector("[data-estado]"), detalle = med.querySelector("[data-detalle]");
    var relleno = med.querySelector("[data-relleno]");
    var mMin = med.querySelector("[data-marca-min]"), mRec = med.querySelector("[data-marca-rec]");
    var nombreTuyo = k === "g" ? pc.gpu : k === "c" ? pc.cpu : (pc.ram ? pc.ram + " GB" : "");
    var nMin = k === "r" ? (mn !== null ? mn + " GB" : "") : med.dataset.minNombre;
    var nRec = k === "r" ? (rc !== null ? rc + " GB" : "") : med.dataset.recNombre;

    var partes = [];
    partes.push(nombreTuyo ? "Tú: " + nombreTuyo : "Tú: sin dato");
    if (nMin) partes.push("mín. " + nMin);
    if (nRec) partes.push("rec. " + nRec);
    detalle.textContent = partes.join(" · ");

    var v;
    if (tuyo === null) v = "?";
    else if (mn === null && rc === null) v = "?";
    else if (rc !== null && tuyo >= rc) v = "rec";
    else if (mn !== null && tuyo >= mn) v = rc === null ? "rec" : "min";
    else if (mn === null) v = "min";
    else v = "no";
    med.setAttribute("data-v", v);
    estado.textContent = tuyo === null ? "Falta tu dato" : (mn === null && rc === null) ? "Sin dato del juego" :
      { rec: "Alto", min: "Mínimo", no: "Por debajo" }[v];

    var tope = Math.max(mn || 0, rc || 0, tuyo || 0) * 1.12 || 1;
    function marca(el, valor) {
      if (valor === null) { el.hidden = true; return; }
      el.hidden = false;
      el.style.setProperty("--p", Math.min(100, valor / tope * 100).toFixed(1));
    }
    marca(mMin, mn); marca(mRec, rc);
    relleno.style.setProperty("--p", "0");
    var final = tuyo === null ? 0 : Math.min(100, tuyo / tope * 100);
    requestAnimationFrame(function () { requestAnimationFrame(function () { relleno.style.setProperty("--p", final.toFixed(1)); }); });
  }

  function pintarJuicio(pc) {
    var juicio = document.querySelector("[data-juicio]");
    if (!juicio) return;
    var form = juicio.querySelector("[data-juicio-form]");
    var meds = juicio.querySelector("[data-medidores]");
    var cambiar = juicio.querySelector("[data-cambiar-pc]");
    if (!pc) {
      juicio.removeAttribute("data-v");
      form.hidden = false; meds.hidden = true; cambiar.hidden = true;
      return;
    }
    var v = veredicto(juicio, pc);
    juicio.setAttribute("data-v", v);
    juicio.querySelector("[data-juicio-titulo]").textContent = TEXTOS[v][0];
    juicio.querySelector("[data-juicio-texto]").textContent = TEXTOS[v][1];
    form.hidden = true; meds.hidden = false; cambiar.hidden = false;
    meds.querySelectorAll("[data-medidor]").forEach(function (m) { pintarMedidor(m, juicio, pc); });
  }

  function pintarTodo() {
    var pc = leerPC();
    pintarChip(pc);
    pintarListas(pc);
    pintarJuicio(pc);
  }

  // ---------- Formularios ----------
  function cargarHardware() {
    if (hardware) return Promise.resolve(hardware);
    return fetch("assets/hardware.json", { credentials: "same-origin" })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (d) { hardware = d; return d; });
  }

  function llenarListas(d) {
    [["lista-gpu", d.gpus], ["lista-cpu", d.cpus]].forEach(function (par) {
      document.querySelectorAll("#" + par[0]).forEach(function (dl) {
        if (dl.childElementCount) return;
        var frag = document.createDocumentFragment();
        Object.keys(par[1]).sort().forEach(function (k) {
          var op = document.createElement("option");
          op.value = k;
          frag.appendChild(op);
        });
        dl.appendChild(frag);
      });
    });
  }

  function prepararFormulario(form) {
    var pc = leerPC();
    if (pc) {
      form.elements.gpu.value = pc.gpu || "";
      form.elements.cpu.value = pc.cpu || "";
      form.elements.ram.value = pc.ram ? String(pc.ram) : "";
    }
    var estado = form.querySelector("[data-pc-estado]");
    function avisar(texto, tono) { estado.textContent = texto; estado.setAttribute("data-tono", tono || ""); }

    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      if (!hardware) { avisar("Cargando la lista de modelos, intenta de nuevo en un segundo.", "error"); return; }
      var gpuTxt = form.elements.gpu.value.trim(), cpuTxt = form.elements.cpu.value.trim();
      var ram = form.elements.ram.value ? Number(form.elements.ram.value) : null;
      var gpu = gpuTxt ? buscarModelo(gpuTxt, hardware.gpus) : null;
      var cpu = cpuTxt ? buscarModelo(cpuTxt, hardware.cpus) : null;
      form.elements.gpu.setAttribute("aria-invalid", String(!!gpuTxt && !gpu));
      form.elements.cpu.setAttribute("aria-invalid", String(!!cpuTxt && !cpu));
      if (gpuTxt && !gpu) { avisar("No reconocemos esa tarjeta gráfica. Elige la más parecida de la lista.", "error"); form.elements.gpu.focus(); return; }
      if (cpuTxt && !cpu) { avisar("No reconocemos ese procesador. Elige el más parecido de la lista.", "error"); form.elements.cpu.focus(); return; }
      if (!gpu && !cpu && !ram) { avisar("Escribe al menos tu tarjeta gráfica o tu RAM.", "error"); return; }
      var nuevo = {
        gpu: gpu ? gpu.nombre : "", gpuPts: gpu ? gpu.pts : null,
        cpu: cpu ? cpu.nombre : "", cpuPts: cpu ? cpu.pts : null,
        ram: ram
      };
      form.elements.gpu.value = nuevo.gpu;
      form.elements.cpu.value = nuevo.cpu;
      guardarPC(nuevo);
      avisar("Guardado: " + resumenPC(nuevo) + ".", "ok");
      pintarTodo();
      var juicio = form.closest("[data-juicio]");
      if (juicio) {
        var titulo = juicio.querySelector("[data-juicio-titulo]");
        titulo.setAttribute("tabindex", "-1");
        titulo.focus({ preventScroll: true });
      }
    });
  }

  function iniciar() {
    var forms = document.querySelectorAll("[data-pc-form]");
    if (forms.length) {
      cargarHardware().then(llenarListas).catch(function () {
        forms.forEach(function (f) {
          var e = f.querySelector("[data-pc-estado]");
          e.textContent = "No se pudo cargar la lista de modelos. Recarga la página.";
          e.setAttribute("data-tono", "error");
        });
      });
      forms.forEach(prepararFormulario);
    }

    var caja = document.querySelector("[data-buscar]");
    if (caja) {
      var q = new URLSearchParams(location.search).get("q");
      if (q) caja.value = q.slice(0, 80);
      caja.addEventListener("input", filtrar);
    }
    document.querySelectorAll("[data-filtro]").forEach(function (b) {
      b.addEventListener("click", function () { filtroActual = b.dataset.filtro; filtrar(); });
    });
    var cambiar = document.querySelector("[data-cambiar-pc]");
    if (cambiar) cambiar.addEventListener("click", function () {
      var juicio = cambiar.closest("[data-juicio]");
      juicio.querySelector("[data-juicio-form]").hidden = false;
      cambiar.hidden = true;
      var input = juicio.querySelector("input[name=gpu]");
      if (input) input.focus();
    });
    pintarTodo();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", iniciar);
  else iniciar();
})();
