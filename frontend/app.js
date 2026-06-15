// EarHero AI - cliente. Sin frameworks ni build: vanilla JS.

const NOTAS = ["Do", "Re", "Mi", "Fa", "Sol", "La", "Si"];
const FRECUENCIAS = {
  Do: 261.63, Re: 293.66, Mi: 329.63, Fa: 349.23,
  Sol: 392.0, La: 440.0, Si: 493.88,
};

let token = null;
let secuenciaActual = [];   // lo que devolvió el server (para reproducir)
let respuestaUsuario = [];

const $ = (id) => document.getElementById(id);

// ---------- Audio ----------
let audioCtx = null;
function tono(frecuencia, inicio, duracion = 0.45) {
  const osc = audioCtx.createOscillator();
  const gain = audioCtx.createGain();
  osc.type = "sine";
  osc.frequency.value = frecuencia;
  gain.gain.setValueAtTime(0.0001, inicio);
  gain.gain.exponentialRampToValueAtTime(0.25, inicio + 0.03);
  gain.gain.exponentialRampToValueAtTime(0.0001, inicio + duracion);
  osc.connect(gain).connect(audioCtx.destination);
  osc.start(inicio);
  osc.stop(inicio + duracion);
}
function reproducir(secuencia) {
  if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  let t = audioCtx.currentTime + 0.1;
  secuencia.forEach((nota) => {
    tono(FRECUENCIAS[nota], t);
    t += 0.55;
  });
}

// ---------- API ----------
async function api(path, { method = "GET", body, auth = false } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth && token) headers["Authorization"] = `Bearer ${token}`;
  const r = await fetch(path, {
    method, headers, body: body ? JSON.stringify(body) : undefined,
  });
  const data = await r.json().catch(() => ({}));
  return { ok: r.ok, status: r.status, data };
}

// ---------- Auth UI ----------
function modo(registro) {
  $("tab-login").classList.toggle("active", !registro);
  $("tab-register").classList.toggle("active", registro);
  $("btn-login").classList.toggle("hidden", registro);
  $("btn-register").classList.toggle("hidden", !registro);
  $("auth-msg").textContent = "";
}
$("tab-login").onclick = () => modo(false);
$("tab-register").onclick = () => modo(true);

function setMsg(el, texto, tipo) {
  el.textContent = texto;
  el.className = `msg ${tipo || ""}`;
}

$("btn-register").onclick = async () => {
  const email = $("email").value.trim();
  const password = $("password").value;
  const { ok, data } = await api("/api/register", { method: "POST", body: { email, password } });
  if (ok) {
    setMsg($("auth-msg"), "Cuenta creada. Ya podés ingresar.", "ok");
    modo(false);
  } else {
    setMsg($("auth-msg"), traducirError(data.detail), "err");
  }
};

$("btn-login").onclick = async () => {
  const email = $("email").value.trim();
  const password = $("password").value;
  const { ok, data } = await api("/api/login", { method: "POST", body: { email, password } });
  if (ok) {
    token = data.token;
    await iniciarApp();
  } else {
    setMsg($("auth-msg"), "Credenciales inválidas", "err");
  }
};

$("btn-logout").onclick = () => {
  token = null;
  $("app").classList.add("hidden");
  $("auth").classList.remove("hidden");
};

function traducirError(detail) {
  const mapa = {
    EmailInvalidoError: "El email no es válido.",
    PasswordDebilError: "La contraseña no cumple el mínimo (8+, letras y números).",
    UsuarioYaExisteError: "Ya existe una cuenta con ese email.",
  };
  return mapa[detail] || "No se pudo crear la cuenta.";
}

// ---------- App de entrenamiento ----------
function construirTeclado() {
  const cont = $("teclado");
  cont.innerHTML = "";
  NOTAS.forEach((nota) => {
    const b = document.createElement("button");
    b.className = "nota";
    b.textContent = nota;
    b.onclick = () => {
      respuestaUsuario.push(nota);
      if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      tono(FRECUENCIAS[nota], audioCtx.currentTime + 0.01, 0.3);
      pintarRespuesta();
    };
    cont.appendChild(b);
  });
}

function pintarRespuesta() {
  $("respuesta").textContent = respuestaUsuario.join(" · ");
  $("btn-responder").disabled = respuestaUsuario.length === 0;
}

async function refrescarStats() {
  const { ok, data } = await api("/api/me", { auth: true });
  if (ok) {
    $("nivel").textContent = data.nivel;
    $("xp").textContent = data.xp;
  }
}

async function nuevoEjercicio() {
  respuestaUsuario = [];
  pintarRespuesta();
  $("resultado").textContent = "";
  const { ok, data } = await api("/api/ejercicio/siguiente", { method: "POST", auth: true });
  if (ok) {
    secuenciaActual = data.secuencia;
    await refrescarStats();
  }
}

$("btn-play").onclick = () => reproducir(secuenciaActual);
$("btn-borrar").onclick = () => { respuestaUsuario = []; pintarRespuesta(); };
$("btn-nuevo").onclick = nuevoEjercicio;

$("btn-responder").onclick = async () => {
  const { ok, data } = await api("/api/ejercicio/responder", {
    method: "POST", auth: true, body: { respuesta: respuestaUsuario.join(",") },
  });
  if (ok) {
    const el = $("resultado");
    if (data.correcto) {
      el.textContent = `¡Correcto! +${data.xp_ganado} XP`;
      el.className = "resultado ok";
    } else {
      el.textContent = "Casi... probá de nuevo.";
      el.className = "resultado err";
    }
    await refrescarStats();
    setTimeout(nuevoEjercicio, 1200);
  }
};

async function iniciarApp() {
  $("auth").classList.add("hidden");
  $("app").classList.remove("hidden");
  construirTeclado();
  await nuevoEjercicio();
}
