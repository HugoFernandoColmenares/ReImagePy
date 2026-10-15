# Instalar desde el código

ReImage necesita Python 3.11 o superior. En esta máquina de desarrollo se usa Python 3.13.

Desde la raíz del repositorio:

```bash
python -m pip install -e ".[dev]"
pytest
python -m reimage
```

El extra `dev` instala pytest y PyInstaller. Para usar solo el programa:

```bash
python -m pip install -e .
reimage
```

`reimage` sin argumentos abre la TUI. El comando `python -m reimage` hace lo mismo.

Los ajustes y el registro de deshacer se guardan en el directorio de datos del usuario que calcula `platformdirs` (por ejemplo, en Windows, bajo `%LOCALAPPDATA%\reimage`). Las pruebas usan la variable `REIMAGE_DATA_DIR` para no escribir ahí.
