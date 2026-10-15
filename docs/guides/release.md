# Ejecutable

PyInstaller congela el intérprete, Textual y ReImage en el sistema donde se ejecuta. No compila para otro sistema operativo. Un `.exe` de Windows se construye en Windows, el binario de macOS en macOS y el de Linux en Linux. Cada artefacto es un paquete de una carpeta (`onedir`), que arranca más rápido y evita descomprimir el CSS de Textual en cada inicio.

```text
dist/
├── windows/reimage/reimage.exe
├── macos/reimage/reimage
└── linux/reimage/reimage
```

El spec `packaging/reimage.spec` llama a `collect_all("textual")` para incluir el CSS y los recursos de los widgets. El ejecutable es una aplicación de consola, porque la TUI necesita una terminal.

## Pasos

1. `python -m pip install -e ".[dev]"`
2. `pytest`
3. `pyinstaller packaging/reimage.spec`
4. Ejecuta el binario, abre Setup, previsualiza una carpeta de imágenes de prueba, aplica, deshaz y sal.
5. Guarda tres capturas en `docs/screenshots/`:
   - `setup.png`: cabecera `ReImage`, campos de carpeta y prefijo, pie `p Preview   q Quit`.
   - `preview-collision.png`: la tabla con una fila en colisión.
   - `result.png`: el resumen de renombrados, omitidos y fallos.

Para provocar la colisión de la captura, crea una carpeta cuyo nombre sea el primer destino (por ejemplo `vacation_001.jpg`) junto a una imagen `.jpg`. La vista previa marca esa fila y deja Apply desactivado.

Abre el binario desde una terminal. En Windows es `dist\windows\reimage\reimage.exe`.
