# Narrative Contracts — estado del proyecto

Primera alpha funcional: **0.1.0a1**. Proyecto independiente de Lifecard, con licencia MIT.

## Estado de publicación

- **Repositorio público**: [pablomate4b/narrative-contracts](https://github.com/pablomate4b/narrative-contracts)
- **CI / GitHub Actions**: [Workflow test-and-build](https://github.com/pablomate4b/narrative-contracts/actions) en verde en todas las versiones matriciales (Python 3.11, 3.12, 3.13 y 3.14).
- **GitHub Prerelease**: [v0.1.0a1](https://github.com/pablomate4b/narrative-contracts/releases/tag/v0.1.0a1) publicada con wheels y sdists adjuntos (`dist/` y `packages/pytest-narrative-contracts/dist/`).
- **PyPI**: Pendiente para una etapa posterior tras la evaluación independiente con salidas reales.

## Entregado

- Núcleo Python sin dependencias externas, con ocho tipos de contratos.
- Plugin `pytest-narrative-contracts`, CLI y reportes reproducibles con evidencia.
- Validación de hechos, afirmaciones declaradas por rama y cambios efectivos de estado.
- Heurísticas de texto identificadas como tales, con límites documentados.
- Runner de mutaciones con atribución por regla/código/ubicación, controles positivos y exclusiones.
- Adaptador de Lifecard y ejemplo de integración; el motor original sigue intacto.
- Corpus sintético, baseline simplificado, resultados completos y experimento de mutación de código.
- Borrador de paper en inglés, bibliografía y protocolo para evaluación independiente.
- Paquetes wheel/sdist y workflow de CI verificado en verde.

## Evidencia actual

66 tests pasan; lint, formato y tipado pasan. Las ocho mutaciones de código seleccionadas fueron
detectadas. Se verificó instalación de wheels en un entorno limpio y reproducción idéntica de
los resultados deterministas.

En 720 casos sintéticos: 80% de detección de defectos y 80% de preservación de variantes válidas.
Los supervivientes y falsos positivos quedan publicados dentro del artefacto. Esto demuestra
comportamiento y límites de la implementación; todavía no mide desempeño sobre salidas reales
ni superioridad frente a LLM-as-a-judge.

## Siguiente etapa

El siguiente hito científico es congelar un corpus de salidas reales con etiquetas independientes
según [el protocolo](paper/protocol.md).
La publicación de paquetes en PyPI sigue pendiente para una etapa posterior. El paper es un borrador de factibilidad, no listo para presentarse como estudio concluido.

[Empezar a usar](README.md) · [Verificación](docs/verification.md) ·
[Resultados](benchmarks/results/summary.md) · [Paper](paper/draft.md) · [Roadmap](docs/roadmap.md)
