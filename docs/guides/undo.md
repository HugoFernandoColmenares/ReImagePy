# Deshacer

Cada carpeta tiene un solo registro JSON. Una ejecución nueva, ya confirmada, sustituye el registro de esa carpeta. El archivo vive en el directorio de datos del usuario (`platformdirs`), dentro de `undo/`, y no se escribe dentro de la carpeta de imágenes.

El registro guarda la ruta absoluta del nombre original y la del nombre nuevo, solo para los movimientos que terminaron bien. Se crea antes del primer movimiento y se actualiza después de cada uno.

Aplicar mueve cada archivo a un nombre temporal en la misma carpeta y después al nombre final. Así `a_002.jpg` puede pasar a `a_001.jpg` mientras `a_001.jpg` todavía existe. Deshacer recorre el registro y usa el mismo esquema de dos pasos para devolver los archivos.

## Desde la TUI

En la pantalla de resultado, **Undo** aparece cuando el registro tiene movimientos. La tecla `u` hace lo mismo en Setup (para la carpeta del campo) y en Resultado. Un archivo bloqueado o ausente se muestra en su propia fila; los que ya se renombraron siguen renombrados y el registro permite devolver esos.

## Desde la terminal

```bash
python -m reimage --undo --folder RUTA
python -m reimage --undo
```

Con `--folder`, se deshace la última aplicación de esa carpeta. Sin carpeta, se usa el registro más reciente. La salida es una línea `nombre-actual -> nombre-original` por cada archivo restaurado.

Si un destino ya no está, ese movimiento queda en el registro y el resto se restaura.
