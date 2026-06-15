# Spec 03 — Estilo visual

> Estética del documento: **Cyber-Arcade tipo Melodics**, modo oscuro,
> **neon purple + electric blue**, glassmorphism, sensación lúdica y energética.
> El frontend generado DEBE respetar esta paleta y estructura de pantallas.

## Tokens de color (CSS variables)
```
--violeta:     #4A3AB7   /* neon purple, color de marca */
--violeta-osc: #2E1D8F   /* hover / acentos */
--azul:        #2E74B5   /* electric blue, secundario */
--bg:          #0F1020   /* fondo modo oscuro */
--card:        #1B1C33   /* superficie de cards (glassmorphism) */
--texto:       #E8E8F2
--tenue:       #9B9BB5
--ok:          #1F9D55
--err:         #D64545
```

## Principios visuales
- Modo oscuro siempre. Fondo con degradé radial sutil hacia el violeta.
- **Cards** con bordes redondeados (16px) y sombra → separan rutas de aprendizaje.
- Botones grandes e interactivos (las notas son botones grandes tipo "pads").
- Ícono / motivo de onda de sonido (sound-wave) en la marca.
- Tipografía limpia (Segoe UI / Arial). Marca "EarHero" con "AI" en violeta.

## Pantallas (wireframes del documento)
1. **Inicio / Bienvenida:** logo + botones "Ingresar" y "Registrarme".
   Cards grandes: "Módulo de Fundamentos" y "Laboratorio de Hits (Spotify)".
2. **Entrenamiento (principal):** barra de progreso de nivel arriba; botón
   central grande "▶ Reproducir"; grilla de botones de opción (Do, Re, Mi, Fa…);
   botón destacado "Aceptar/Responder".
3. **Perfil:** avatar, nivel por categoría (Notas/Intervalos/Acordes), racha de
   días y gráfico de progreso.

## MVP
Implementar la pantalla de Inicio (login/registro) y la de Entrenamiento con
audio real (Web Audio API sintetiza las notas). Perfil y Laboratorio Spotify
quedan como extensión.
