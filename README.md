# Terror Voice Studio

Aplicación Python para convertir guiones de terror marcados en audio MP3 multivoz mediante la API de OpenAI. Incluye interfaz Streamlit, CLI, caché para evitar volver a pagar fragmentos ya sintetizados y exportación MP3.

## Windows 11 — instalación

1. Instala Python 3.11+ y **FFmpeg**. Comprueba en PowerShell: `python --version` y `ffmpeg -version`. FFmpeg debe estar disponible en `PATH`.
2. Abre esta carpeta en VS Code o Codex y ejecuta:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

3. Edita `.env` y coloca tu **clave personal** `OPENAI_API_KEY`. No compartas ni subas ese archivo a Git.
4. Inicia la interfaz:

```powershell
streamlit run app.py
```

5. Carga el guion, revisa las voces, deja marcada la validación para revisar el plan y, después, desmarca **Solo validar** para generar el MP3.

## CLI

```powershell
python cli.py guion_ejemplo.md --dry-run
python cli.py guion_ejemplo.md --limit 8 --output prueba
python cli.py guion_ejemplo.md --output salida
```

**Aviso de costes:** la API de OpenAI se factura por separado de ChatGPT. Primero usa `--limit 8` para validar voces y calidad antes de generar toda la historia. No se incluye ninguna clave de API.

## Formato del guion

```text
# CAPÍTULO 1 — LA LLAMADA
[VOZ: JASON | ACTUACIÓN: nervioso, casi susurrando]
No debí aceptar ese trabajo.

[PAUSA: 1.5 s]
[VOZ: SKARD | ACTUACIÓN: grave, impasible]
Empiezas esta noche.

[SFX: puerta metálica cerrándose]
```

Los nombres de voz se configuran en `config.json` o en la barra lateral. El programa no pronuncia las etiquetas. Las líneas `[SFX: ...]` y `[MÚSICA: ...]` son **indicaciones editoriales**, no efectos generados automáticamente. Para insertar un efecto de audio existente, asigna su ruta al índice de segmento correspondiente en `config.json` bajo `effects` (el índice aparece en `plan.json`). Solo utiliza sonidos con derechos adecuados.

## Importante: voces y diálogos

El guion incluido es una adaptación del relato y contiene algunas citas dentro de párrafos narrativos. **Las citas internas no se convierten automáticamente a otro personaje**. Para que un diálogo lo lea Skard, Ryan o Sarah, sepáralo en su propio bloque `[VOZ: ...]`. Comprueba `plan.json` antes de sintetizar. El sistema de caché guarda cada fragmento en `salida/cache/` y permite retomar ejecuciones fallidas sin regenerar los archivos ya completados. Si cambias modelo, texto, voz, velocidad o instrucciones, se genera un archivo nuevo.

El modelo `gpt-4o-mini-tts` permite instrucciones de interpretación. Otros modelos pueden no admitirlas; la aplicación está optimizada para `gpt-4o-mini-tts`.

## Transparencia

Si publicas el video, informa claramente que las voces son generadas por inteligencia artificial. No utilices voces que imiten a personas reales sin autorización. El contenido del relato puede requerir revisar los derechos de adaptación y publicación.
