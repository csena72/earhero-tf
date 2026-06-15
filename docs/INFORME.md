# Informe — Trabajo Final
## Suite de pruebas automatizadas asistida por IA — EarHero AI

**Alumno:** Cristian José Sena
**Curso:** Inteligencia Artificial para Programadores — UTN BA
**Repositorio:** _(pegá acá el link a GitHub/GitLab)_

---

### 1. Justificación del diseño de pruebas

El módulo elegido continúa el proyecto **EarHero AI** de la Unidad 4. Se testean
cuatro componentes con responsabilidades claras:

- **`auth.py`** (RF-01): registro, login y tokens firmados. Se prioriza la
  seguridad: validación de email/contraseña, hashing PBKDF2 con salt por usuario
  y verificación en tiempo constante.
- **`dificultad.py`** (RF-04): lógica pura de adaptación. Al no tener I/O y
  concentrar las ramas condicionales (subir / bajar / mantener), es el mejor
  objetivo para **cobertura de ramas**.
- **`progreso.py`** (RF-02): XP, niveles y racha, con casos de borde temporales
  (mismo día, día consecutivo, racha cortada, fecha pasada).
- **`tutor.py`**: orquestador; se testea con un RNG sembrado para determinismo.

Se separaron **pruebas unitarias** (lógica aislada) de **pruebas funcionales**
(API end-to-end con `TestClient` y UI en navegador con Playwright). Criterios:
una aserción por concepto, `parametrize` para tablas de equivalencia, y fixtures
para estado limpio entre tests.

### 2. Análisis de cobertura (antes y después)

| Momento | Cobertura | Comentario |
|---|---|---|
| Antes | **70 %** | Solo caminos felices (login OK, ejercicio correcto). |
| Después | **98 %** | Se agregaron errores, expiración de token, umbrales y bordes de racha. |

_(Insertar captura de `docs/coverage_html/index.html`.)_

Los **3 % restantes** corresponden a guardas defensivas de bajo riesgo
(documentadas en el reporte con `--cov-report=term-missing`).

### 3. Uso de herramientas de IA

Se utilizó un **pipeline multi-agente local con Ollama** (`tools/agents.py`) en
lugar de GitHub Copilot, para mantener todo el flujo offline y sin costos de API:

- **Arquitecto (llama3.1:8b)** propuso el mapa inicial de escenarios.
- **Tester (qwen2.5-coder:3b)** generó borradores de tests pytest.
- **Revisor (phi4-mini)** detectó redundancias y casos borde faltantes.
- **Redactor (llama3.1:8b)** asistió esta reflexión.

_(Insertar capturas de `docs/agente_*.md`.)_

### 4. Funcionamiento de CI/CD

Pipeline en **GitHub Actions** (`.github/workflows/ci.yml`): instala
dependencias, instala Chromium para Playwright, corre la suite con cobertura y
**falla si la cobertura baja de 90 %** (`--cov-fail-under=90`). Publica el
reporte HTML como artefacto.

_(Insertar captura de la corrida verde en la pestaña Actions.)_

### 5. Reflexión crítica

_(Acá va la salida del agente Redactor, editada. Puntos a cubrir:)_

- **Dónde brilló la IA:** generar tablas de equivalencia y recordar casos borde
  (token expirado, racha cortada) que es fácil olvidar manualmente.
- **Dónde falló / hubo que corregir:** los modelos chicos a veces inventan APIs
  inexistentes o tests que no compilan; el rol del humano fue validar, ajustar
  imports y descartar redundancias.
- **Cuándo automatizar y cuándo no:** conviene automatizar lógica determinista
  con muchas ramas (dificultad, progreso); para flujos visuales o exploratorios,
  el test automatizado es más costoso de mantener que su valor.
- **Local vs nube:** Ollama da privacidad y costo cero a cambio de modelos más
  chicos; para este alcance fue suficiente.
