# Spec 02 — Entidades (Diagrama de Clases UML)

> Copiado del diagrama del documento. El backend (ORM + dominio) debe mapear
> estas clases. En el MVP se persisten: Usuario, Perfil, NivelCategoria y
> SesionEjercicio.

## Usuario
- `String id`, `String email`, `String passwordHash`, `DateTime creadoEn`
- `Perfil perfil`
- `registrar(email, pass) bool`, `login(email, pass) TokenJWT`, `logout() void`

## Perfil
- `int nivelGlobal`, `int racha`, `DateTime ultimaSesion`
- `Map<String,NivelCategoria> niveles`, `List<Logro> logros`
- `verProgreso() ResumenProgreso`, `actualizarRacha() void`,
  `obtenerLogrosDesbloqueados() List<Logro>`

## NivelCategoria
- `TipoModulo tipo` (Notas | Intervalos | Acordes)
- `int nivel`, `int puntosAcumulados`, `float tasaAcierto`
- `subirNivel() void`, `calcularXP(bool correcto) int`

## ModuloAprendizaje
- `TipoModulo tipo`, `int nivelActual`, `Ejercicio ejercicioActual`
- `iniciarSesion()`, `reproducirSonido() AudioBuffer`,
  `presentarOpciones() List<String>`, `recibirRespuesta(resp) ResultadoEjercicio`

## TutorIA
- `GestorDificultadAdaptativa gestorDificultad`, `MotorAudioIA motorAudio`
- `validarRespuesta(resp, ej) ResultadoEjercicio`
- `generarSiguienteEjercicio(Perfil) Ejercicio`
- `calcularFeedback(ResultadoEjercicio) Feedback`
- `actualizarModeloUsuario(ResultadoEjercicio) void`

## GestorDificultadAdaptativa
- `int ventanaDeRespuestas`, `float umbralSubida`, `float umbralBajada`
- `List<ResultadoEjercicio> historial`

## Mapeo a tablas (PostgreSQL)
- `usuarios(id, email, password_hash, creado_en)`
- `perfiles(usuario_id, nivel_global, racha, ultima_sesion)`
- `progreso(id, usuario_id, tipo, nivel, puntos_acumulados, aciertos,
  intentos, historial)`  ← NivelCategoria + ventana del gestor
- `sesiones_ejercicio(id, usuario_id, tipo, nivel, secuencia, estado, creado_en)`
