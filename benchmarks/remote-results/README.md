# Corrida remota — 29 de septiembre de 2026

Se capturaron 32 respuestas reales de los modelos instalados que indicó el usuario, sin descargas de pesos, APIs pagas, reintentos ni reparaciones. Escenarios públicos ficticios de soporte y ficción interactiva, en inglés y español: 16 por modelo, agrupados en 8 familias. No son sesiones de producción de LifeCard ni 32 escenarios independientes.

| Modelo (tag exacto del servidor) | Respuestas completas | Aceptadas por contratos | Mediana por solicitud |
| --- | ---: | ---: | ---: |
| `gemma4:26b-mlx-hermes` | 16/16 | 16/16 | 4.38 s |
| `qwen3.8:27b` | 16/16 | 16/16 | 12.30 s |

Todas las salidas cumplieron el esquema, las declaraciones tipadas coincidieron con el estado de su rama y ninguna activó las heurísticas configuradas. No hubo truncamientos ni errores de generación. La latencia incluye red y carga cuando corresponde; no es una comparación controlada de rendimiento.

**Aceptación no equivale a corrección semántica.** Los contratos de declaraciones no comprueban que la prosa diga lo mismo. Esta muestra no determina precisión, recall, falsos negativos ni superioridad sobre LLM-as-judge. Tampoco cambia las limitaciones ni los supervivientes del benchmark de mutaciones previo. El siguiente experimento útil sería inyectar degradaciones controladas en estas salidas y medir detecciones atribuidas y controles válidos, con los operadores definidos antes de evaluar.

## Memoria y ejecución

Primero se ejecutaron las 16 solicitudes de `gemma4:26b-mlx-hermes`; luego se envió la descarga explícita y se verificó que `/api/ps` estuviera vacío antes de iniciar `qwen3.8:27b`. Se descargó Qwen al terminar. La comprobación independiente final también devolvió `{"models":[]}`. No se lanzaron solicitudes simultáneas. Esto controla nuestro recolector; otros clientes del servidor quedan fuera de su control.

Ollama 0.34.4. Contexto 4096, máximo 512 tokens de salida, temperatura 0, seed 1729, formato JSON y thinking desactivado. Los digests, plantillas y metadatos exactos están en `manifest.json`. Los tags son nombres locales; no se infiere de ellos una procedencia upstream verificada.

## Protocolo y procedencia

Se reutilizaron escenarios, prompts, reglas y parámetros del piloto anterior. El manifiesto y el código del recolector se congelaron antes de la primera generación. El documento `original-release-protocol.md` corresponde al piloto alpha a2 y todavía nombra Qwen3 1.7b y Gemma3 1b: **esta corrida difiere en los dos modelos elegidos por el usuario, el servidor remoto, timeout de 600 segundos y descarga explícita entre modelos**. Los modelos efectivos constan en el manifiesto; no se presenta el documento anterior como una preregistración específica de esta corrida. Esta nota se redactó después de recolectar, sin alterar el manifiesto ni los datos crudos.

## Archivos y replay

- `outputs.jsonl`: todas las solicitudes y respuestas crudas, tokens y tiempos.
- `manifest.json`: escenarios, configuración y metadatos congelados.
- `collector-source.py.txt`: código exacto utilizado.
- `evaluation/`: informes por salida, resumen y tiempos de evaluación.
- `verification.json`: verificaciones de integridad y replay.
- `SHA256SUMS`: hashes de los archivos del paquete.

Con `narrative-contracts==0.1.0a2` instalado en un entorno Python 3.11 o superior, desde este directorio:

```sh
python collector-source.py.txt replay --input . --output /tmp/narrative-remote-replay-new
cmp evaluation/reports.json /tmp/narrative-remote-replay-new/reports.json
cmp evaluation/summary.json /tmp/narrative-remote-replay-new/summary.json
```

El directorio de salida debe ser nuevo. El replay no necesita Ollama. Se verificó igualdad byte por byte de ambos informes con el código archivado; `latency.json` varía con cada ejecución. Volver a generar textos puede dar otros resultados según hardware y runtime.

Los paquetes instalables de la alpha están en [GitHub Releases](https://github.com/Mate4b/narrative-contracts/releases/tag/v0.1.0a2).
