# Spec 00 — Proyecto EarHero AI

> Fuente: documento de diseño "EarHero AI — Codiseño con IA (Unidad 4)".
> Este archivo es la VERDAD que deben respetar los agentes generadores.

## Qué es
App de **entrenamiento auditivo musical**. El usuario escucha un sonido
(notas, intervalos o acordes) y debe identificarlo. La IA valida y propone el
siguiente desafío, ajustando la dificultad.

## Problema
El entrenamiento auditivo suele ser monótono y teórico → alta tasa de abandono.
EarHero lo vuelve un juego (estética Cyber-Arcade tipo Melodics).

## Usuarios
Estudiantes de música y aficionados que quieren "sacar canciones de oído".
Uso casual desde el móvil o dashboard web.

## Requisitos Funcionales
- **RF-01 (Acceso):** registro y login de usuarios para guardar progreso.
- **RF-02 (Fundamentos):** entrenar Notas, Intervalos o Acordes por separado.
- **RF-03 (Evaluación):** tras cada sonido el usuario elige y pulsa "Aceptar";
  la IA valida y genera el siguiente desafío.
- **RF-04 (Dificultad Adaptativa):** la IA ajusta cantidad de notas y velocidad
  según el nivel (niveles bajos = menos notas / menos opciones).

## Requisitos No Funcionales
- **RNF-01 (Rendimiento):** procesar la respuesta y cargar el siguiente
  ejercicio en **< 2 segundos** (clave para el flujo de aprendizaje).

## Alcance del MVP a generar
Implementar RF-01, RF-02 (módulo Notas), RF-03 y RF-04 con persistencia real.
El Laboratorio de Hits (Spotify) y el MotorAudioIA quedan como extensión
documentada, no implementada en el MVP.
