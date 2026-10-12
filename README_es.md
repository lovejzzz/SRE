[English](README.md) · [简体中文](README_zh.md) · [日本語](README_ja.md) · [Español](README_es.md) · [Français](README_fr.md) · [Deutsch](README_de.md) · [Português (Brasil)](README_pt-BR.md)

# SRE — Software Resynthesis Engine

[![Tests](https://github.com/lovejzzz/SRE/actions/workflows/test.yml/badge.svg)](https://github.com/lovejzzz/SRE/actions/workflows/test.yml)

**Indica qué software quieres reconstruir, en qué plataforma y qué debería mejorar.**

SRE es una skill para agentes que investigan software existente y construyen un sucesor: conservar comportamientos, adaptarlos a otra plataforma y añadir o mejorar funciones. La ambición abarca juegos, aplicaciones de escritorio, CLI, web y móvil. La viabilidad depende de las evidencias disponibles, las dependencias y la plataforma de destino.

**v0.2: una skill con herramientas ejecutables de investigación y validación.** El agente anfitrión investiga y programa. No garantiza reconstruir íntegramente cualquier software con un clic.

## Instalación

Necesitas un anfitrión compatible con skills locales y **Python 3.10+**, sin dependencias Python externas. [REA](https://github.com/morluto/rea) es opcional y no se instala automáticamente.

```bash
git clone https://github.com/lovejzzz/SRE.git
python3 SRE/scripts/install.py
```

El instalador usa `$CODEX_HOME/skills` o `~/.codex/skills` y no sobrescribe instalaciones existentes. Puedes cambiarlo con `--skills-dir /path/to/skills`. Conserva tus modificaciones al actualizar y recarga la skill en el anfitrión.

> Usa $software-resynthesis para investigar esta aplicación de escritorio y reconstruirla como aplicación web sin conexión. Conserva el flujo documental, añade operaciones por lotes y valida contra el original. Entrega un primer hito probado sin perder el alcance completo solicitado.

## Capacidades implementadas

- Inventarios de funciones a partir de varias fuentes, correspondencias, dependencias, detección de omisiones y bases de referencia versionadas.
- Hipótesis alternativas, predicciones, priorización de experimentos que las distinguen y detección de contradicciones.
- Ejecución explícita de adaptadores con directorio propio, contrato de reinicio/acción/observación/finalización, hashes, registros y tiempo límite.
- Errores de imágenes normalizadas, conservación semántica al guardar y reabrir archivos, trazas de interacción y presupuestos de rendimiento por dispositivo y carga.
- Aceptación que exige tanto evidencias de comportamiento como auditoría de investigación. Los registros obsoletos y las cuestiones bloqueantes impiden aprobar.

REA puede aportar análisis; SRE conecta la investigación con especificaciones, implementación y aceptación. No incluye un cliente REA ni afirma una superioridad medida frente a REA.

## Ejemplo ejecutable

```bash
cd SRE
python3 -m unittest discover -s tests -v
python3 examples/posix-path/run.py --workspace work/posix-run-1
```

Ejecuta realmente `posixpath.normpath` de Python y una implementación independiente en JavaScript con **417 entradas**. Resuelve una pregunta mediante observaciones y detecta un defecto introducido deliberadamente. Requiere Node.js 18+ y un directorio de salida nuevo. No es una evaluación independiente de reconstrucción autónoma de aplicaciones completas.

## Comandos y límites

`sre.py`: `init`, `fingerprint`, `seal`, `audit`, `plan`, `run-adapter`, `compare`, `domain-check`, `check`. Consulta `--help`. No sobrescribe salidas. Códigos: 0 éxito, 1 comparación/aceptación/ejecución no aprobada, 2 error de entrada o ejecución. Los espacios v0.1 necesitan registros reales de descubrimiento y una base sellada para aprobar `check`.

No demuestra que se hayan descubierto todas las funciones ni autentica experimentos. Un hito no equivale al producto completo. No incluye un rastreador universal, un planificador permanente ni adaptadores de ejecución para PZ/Photoshop. El agente recopila fuentes y diseña hipótesis. Los adaptadores ejecutan con los permisos del anfitrión, no en un sandbox. Los validadores consumen JSON normalizado; el análisis PSD, la decodificación de imágenes, la operación de GUI y la medición de dispositivos requieren adaptadores específicos. Tampoco recupera implementaciones de servidor inaccesibles ni garantiza cualquier carga en cualquier plataforma.

No se han realizado evaluaciones independientes de agentes. Mantén muestras privadas, credenciales y datos personales fuera del repositorio público; respeta las licencias del código reutilizado.

[Investigación](skills/software-resynthesis/references/research-protocol.md) · [Adaptadores](skills/software-resynthesis/references/adapters.md) · [Validación por dominio](skills/software-resynthesis/references/domain-validation.md) · [Evaluación](evals/behavioral.md)

Se agradecen fallos reproducibles y anonimizados, con versiones, entradas, resultados esperados/reales y evidencias, así como mejoras de traducción. Los protocolos técnicos detallados están actualmente en inglés.

Actualización de integridad: las validaciones del destino y las observaciones de investigación requieren SHA-256. Consulta la [migración y sus límites](skills/software-resynthesis/references/validation.md#recorded-evidence-integrity) y el [historial de cambios](CHANGELOG.md).
