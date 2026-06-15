**ARQUITECTURA.md**
=====================

**Arquitectura del Proyecto EarHero AI**

El proyecto EarHero AI se implementa utilizando una arquitectura monolítica modular. Este documento describe las capas, los módulos del monolito y la estructura de carpetas.

**Capas del Monolito**
----------------------

*   **Autenticación JWT**: gestiona el registro y login de usuarios.
*   **TutorIA**: valida la respuesta del usuario e imprime el siguiente desafío.
*   **GestorDificultadAdaptativa**: ajusta la dificultad en función del nivel del usuario.
*   **Progreso**: almacena la información de progreso y niveles del usuario.
*   **MotorAudioIA**: se utiliza para generar audio (en el MVP, se sintetiza client-side).
*   **LaboratorioSpotify**: es una extensión futura que interactúa con la API de Spotify.

**Estructura de Carpetas**
-------------------------

La estructura de carpetas está definida en `04_estructura.md`. Se resalta la importancia del monolito en `src/earhero/`, donde se encuentra todo el dominio. La persistencia es PostgreSQL en docker-compose y SQLite en tests.

**Decisiones Clave**
----------------------

Se decidió utilizar una arquitectura monolítica modular para cumplir con el requisito de rendimiento (RNF-01 < 2s). Esto permite que las operaciones críticas se realicen en el mismo proceso, sin overhead de red entre módulos.

**Módulos del Monolito Modular**
-------------------------------

*   `auth.py`: Autenticación JWT
*   `tutor.py`: TutorIA
*   `dificultad.py`: GestorDificultadAdaptativa
*   `progreso.py`: Progreso
*   `motor.py`: MotorAudioIA (en el MVP, se sintetiza client-side)
*   `laboratorio.py`: LaboratorioSpotify (extensión futura)

**Conclusión**
----------

La arquitectura monolítica modular permite un mejor rendimiento y una implementación más eficiente de los requisitos del proyecto EarHero AI.