# Narrative Contracts — estado del proyecto

Alpha **0.1.0a2**, independiente de Lifecard, con núcleo y plugin bajo licencia MIT.

## Entregado

- Contratos exactos de estado y declaraciones, separados de heurísticas de texto.
- Núcleo sin dependencias externas, plugin pytest, CLI y reportes con evidencia y versiones.
- Integración independiente de soporte al cliente con transición y selección de rama confiables.
- Benchmark sintético original: 720 casos, 384/480 defectos detectados y 192/240 controles preservados.
- Campaña ampliada: 21 casos; 8/13 fallos detectados, 4/5 controles preservados y 3 exclusiones.
- Piloto con **32 respuestas reales** de Qwen3 y Gemma3, sobre escenarios públicos ficticios.
- Protocolo congelado, respuestas crudas, replay offline y reporte técnico actualizado.
- Plantillas para contraejemplos, fallos no detectados y nuevos contratos.

## Límites de la evidencia

Qwen3 respetó la estructura en 16/16 respuestas y sus declaraciones pasaron los invariantes;
ninguna respuesta pasó el perfil estricto. Gemma3 no respetó el envelope en los 16 casos.
Se publican todos los resultados. Son datos del pipeline, no una clasificación de calidad de
modelos ni accuracy semántica: todavía no hay etiquetas independientes.

La revisión humana y las comparaciones con jueces LLM son trabajos futuros opcionales,
no condiciones para lanzar esta alpha. Abrir el código invita a validación comunitaria,
pero no demuestra que ya exista.

## Publicación y verificación

- [Repositorio público](https://github.com/pablomate4b/narrative-contracts).
- [Alpha a2 y artefactos instalables](https://github.com/pablomate4b/narrative-contracts/releases/tag/v0.1.0a2).
- [CI: test-and-build, Python 3.11–3.14](https://github.com/pablomate4b/narrative-contracts/actions/workflows/ci.yml). La procedencia adjunta a la release identifica el commit y run verificados.
- Wheels/sdists se distribuyen por GitHub Releases; PyPI no es necesario para instalarlos.
- Verificación local: 91 tests, Ruff, mypy, ocho mutantes de código y replay reproducible.
- Instalación de wheels y descubrimiento del plugin verificados en un entorno aislado.

[Uso](README.md) · [Verificación](docs/verification.md) ·
[Piloto real](docs/natural-benchmark.md) · [Informe técnico](paper/draft.md) ·
[Contribuir](CONTRIBUTING.md) · [Roadmap](docs/roadmap.md)
