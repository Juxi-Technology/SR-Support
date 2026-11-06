---
title: 02 Preparación del entorno (venv, herramientas de flasheo y firmware)
description: Antes de empezar: crear y activar el .venv del proyecto, obtener el firmware precompilado y una herramienta oficial de flasheo (Flash Download Tool / esptool), PlatformIO opcional, las herramientas del lado del PC y MuJoCo, y el puerto serie.
---

# 02 Preparación del entorno (venv, herramientas de flasheo y firmware)

> Haz esta página antes de empezar. **Los comandos suponen la raíz del repositorio**: la
> **carpeta `SR-Support`** que descargaste de GitHub (una extracción de zip puede llamarse
> `SR-Support-main`; es la carpeta que contiene `firmware/` y `tools/`). **Todo comando de
> Python se ejecuta en la terminal con `.venv` activado** (2.3). Flashear el firmware
> precompilado no requiere PlatformIO ni compilación; el entorno de desarrollador (2.5) solo
> sirve para modificar el código.

## 2.1 Requisitos

- Windows, Linux o macOS (cada comando de abajo se da para los tres cuando importa);
- un cable USB **de datos** (un cable solo de carga no enumerará la placa);
- ESP32-S3-DevKitC-1 (8 MB de flash).

## 2.2 Obtener el código y el firmware precompilado

- Clona el repositorio (o descomprime el archivo suministrado) y ejecuta los comandos
  posteriores desde la **raíz del repositorio**:

  ```bash
  git clone https://github.com/Juxi-Technology/SR-Support.git
  cd SR-Support
  ```

  (El repositorio es privado: solicita acceso primero.)

- La **imagen precompilada** está en `firmware/releases/`:

  | Archivo | Propósito |
  |---|---|
  | `sr_support_b_ptk_factory.bin` | firmware principal (flashear en 0x0; también se usa para centrar durante el montaje: encender hasta el cero del firmware, `e` opcional) |
  | `SHA256SUMS` | sumas de verificación |

## 2.3 Crear y activar el entorno virtual (.venv)

Todas las herramientas de Python del lado del PC (esptool, PlatformIO, las herramientas de
MuJoCo) van en el **mismo** `.venv` local del proyecto, y ese `.venv` debe crearse dentro de la
**carpeta `SR-Support`** descargada de GitHub (una extracción de zip puede llamarse
`SR-Support-main`; de nuevo, la carpeta que contiene `firmware/` y `tools/`).

Entra primero en esa carpeta: los comandos de abajo se ejecutan allí:

**Windows (PowerShell)**

```powershell
cd D:\Project\SR-Support    # replace with where your SR-Support folder lives
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

- ¿No sabes si estás en el lugar correcto? Ejecuta `dir`; debe listar `firmware`, `tools`, `tutorial`;
- Sin Python 3.12, usa `py -3 -m venv .venv` (sirve 3.10+);
- Si PowerShell se niega a ejecutar scripts, ejecuta
  `Set-ExecutionPolicy -Scope Process Bypass` en esta ventana y activa de nuevo;
- `.\.venv\Scripts\Activate.ps1` es el **script de activación de PowerShell** que crea venv:
  el `.\` inicial significa «ejecutar el script de la carpeta actual» y es obligatorio en
  PowerShell (un simple `Activate.ps1` no se encontrará). Otras shells usan su propio archivo:
  - **cmd.exe**: `.venv\Scripts\activate.bat`
  - **Git Bash**: `source .venv/Scripts/activate`
  - Sal del venv con `deactivate`

**Windows (cmd.exe)**

```bat
cd /d D:\Project\SR-Support    # cmd needs /d to change drive; plain cd D:\... stays on C:
py -3.12 -m venv .venv
.venv\Scripts\activate.bat
```

> Cómo distinguir las shells: el indicador de cmd se ve como `C:\...>`, el de PowerShell como
> `PS C:\...>`. El tutorial usa PowerShell por defecto; en cmd basta cambiar el comando de
> activación por `activate.bat`, todo lo demás es idéntico. No se necesitan permisos de
> administrador.
>
> **El archivo de activación debe coincidir con la shell**: cmd usa `activate.bat`, PowerShell
> usa `Activate.ps1`. Ejecutar el `.ps1` desde cmd no activa la ventana actual (normalmente no
> ocurre nada, o se abre una ventana aparte). Además, asegúrate de que `.venv` exista antes
> (`dir` debe listar la carpeta `.venv`); si no, ejecuta primero `py -3.12 -m venv .venv`.

**Linux / macOS**

```bash
cd ~/SR-Support             # replace with where your SR-Support folder lives
python3 -m venv .venv
source .venv/bin/activate
```

- ¿No sabes si estás en el lugar correcto? Ejecuta `ls`; debe listar `firmware`, `tools`, `tutorial`.

Tras la activación el indicador muestra **`(.venv)`**. Todos los comandos de abajo y de las
páginas posteriores del tutorial se ejecutan en esta **terminal activada**; vuelve a activar
tras abrir una ventana nueva. Sin activación, `pip` / `python` apuntan a la instalación del
sistema y las instalaciones o ejecuciones fallarán.

Confirma que la activación funcionó:

- Windows: `where python`; la primera línea debe ser `...\SR-Support\.venv\Scripts\python.exe`;
- Linux / macOS: `which python`; debe ser `.../SR-Support/.venv/bin/python`.

> **¿Se limpió la pantalla tras activar en cmd?** El `activate.bat` original cambia
> temporalmente la página de códigos de la consola (`chcp 65001`) y algunos terminales
> redibujan la pantalla; **no es una terminal nueva**. Si el nuevo indicador empieza por
> `(.venv)` y `where python` apunta a `.venv`, la activación se realizó correctamente. Para
> evitar el redibujado, usa `Activate.ps1` de PowerShell (no toca la página de códigos) o
> llama a `.venv\Scripts\python.exe` sin activar.

> **Requisito de directorio (importante)**: `.venv` debe vivir en la **carpeta `SR-Support`
> (la raíz del repositorio)**, nunca en una subcarpeta. Los comandos de creación/activación de
> arriba usan **rutas relativas**, así que deben ejecutarse desde esa carpeta: tras abrir una
> terminal nueva, entra primero en ella (PowerShell: `cd D:\Project\SR-Support`; cmd:
> `cd /d D:\Project\SR-Support`, con tu ruta) antes de activar, o usa una ruta absoluta como
> `C:\path\SR-Support\.venv\Scripts\Activate.ps1` /
> `source /path/SR-Support/.venv/bin/activate`.
>
> Una vez activado puedes hacer `cd` a cualquier subcarpeta y `python` / `pip` / `pio` seguirán
> apuntando a ese `.venv`; pero las rutas `tools/...`, `firmware/...` y `hardware/v1/...` del
> tutorial son relativas, así que **ejecútalas desde la carpeta `SR-Support`**. El venv está
> ligado a la ruta donde se creó: tras mover o renombrar el repositorio, borra `.venv` y
> vuelve a crearlo.

## 2.4 Herramientas de flasheo (todos los clientes: elige una)

Una imagen precompilada es un solo bin que se flashea en 0x0: **sin PlatformIO, sin descargar
toolchain**. Asegúrate de que la terminal está en la carpeta `SR-Support` y el indicador muestra
`(.venv)`.

**A. Windows con GUI: Flash Download Tool de Espressif**

1. Abre la página oficial «Other Tools» de Espressif y descarga Flash Download Tools:
   <https://www.espressif.com/en/support/download/other-tools>
2. Ejecútalo; selecciona **ESP32-S3**, carga
   `firmware/releases/sr_support_b_ptk_factory.bin` en la dirección `0x0`, elige el puerto y
   haz clic en **START**.

> Flash Download Tool es solo para Windows; en Linux/macOS usa esptool, más abajo.

**B. Windows / Linux / macOS: esptool (línea de comandos)**

```bash
pip install esptool
```

Red lenta en China: usa un espejo:

```bash
pip install esptool -i https://pypi.tuna.tsinghua.edu.cn/simple
```

Flashea (`COM27` es tu puerto; Linux `/dev/ttyACM0`, macOS `/dev/tty.usbmodem*`):

```bash
python -m esptool --chip esp32s3 -p COM27 -b 460800 write_flash 0x0 firmware/releases/sr_support_b_ptk_factory.bin
```

Si la conexión falla, entra en modo descarga: mantén **BOOT**, pulsa **RST**, suelta **BOOT**.

## 2.5 PlatformIO (solo desarrolladores: compilar desde fuentes)

> Omite esto salvo que modifiques el código. **Nota**: PlatformIO (incluida la extensión
> PlatformIO de VS Code) descarga la plataforma espressif32 y el toolchain de Xtensa en el
> primer uso (~1 GB desde el registro de PlatformIO y GitHub). En muchas redes de China esto es
> lento o falla y requiere un proxy/VPN; la extensión de VS Code no evita la descarga.

Con la terminal en la carpeta `SR-Support` y `(.venv)` activo:

```bash
pip install platformio
```

En Windows también puedes ejecutar `tools/install_platformio.ps1`, que instala en este mismo
`.venv`. Verifica:

```bash
pio --version
```

> Versiones anteriores del tutorial instalaban PlatformIO en un `.venv-pio` aparte; ahora vive
> en el único `.venv`. Si `pio` no aparece tras la actualización, ejecuta `pip install platformio`
> en el `.venv` activado (o vuelve a ejecutar `tools/install_platformio.ps1`); el antiguo
> `.venv-pio` se puede borrar.

## 2.6 Herramientas del lado del PC y entorno MuJoCo (gemelo / punto cero / registros)

No son necesarias para flashear. Instálalas cuando uses la herramienta de punto cero con
teclas de flecha, el gemelo en vivo de MuJoCo (`tools/live_twin.py`), la repetición de
simulación o las herramientas de registros. Con la terminal en la carpeta `SR-Support` y
`.venv` activo, instala las dependencias (pyserial, numpy, MuJoCo 3.1+, gymnasium):

```bash
pip install -r tools/requirements.txt
```

En Windows también puedes ejecutar `tools/install_tools_env.ps1` (crea/reutiliza `.venv` e
instala el mismo conjunto). Con red lenta en China, añade el espejo de Tsinghua
`-i https://pypi.tuna.tsinghua.edu.cn/simple`; la primera instalación descarga unos cientos de MB.

**Comprobación: ejecuta la autoprueba del entorno (carga y avanza MuJoCo, no solo importa)**

```bash
python tools/env_check.py
```

La última línea debe ser `env check: PASS`, con una salida como:

```text
[ok] mujoco 3.16.0
[ok] model hardware\v1\robot_v1.xml: nq=9 nv=8 dt=0.0002s, 200 steps stable ...
```

Sin ninguna placa conectada, `[--] no serial port found` es informativo y no afecta al PASS.

> En Linux, un error de GLFW/OpenGL al abrir la ventana de MuJoCo significa que faltan
> bibliotecas del sistema: instala `libgl1` y `libglew-dev` (p. ej. `sudo apt install libgl1 libglew-dev`).
> Los wheels de MuJoCo para Windows/macOS incluyen lo necesario. La simulación `training/b_line`
> y la repetición usan el mismo entorno: no hay nada extra que instalar.

## 2.7 Conectar la placa y confirmar el puerto serie

1. Conecta por USB-C; en Windows lee el número de COM en el Administrador de dispositivos, en
   Linux suele ser `/dev/ttyACM0` (añade tu usuario al grupo `dialout`), en macOS normalmente
   `/dev/tty.usbmodem*`;
2. Anota el puerto: cada `COM27` de las páginas siguientes es este valor;
3. Un monitor serie o `hw_monitor.py` ocupa el puerto; ciérralo antes de flashear.

## 2.8 Lista de comprobación

- [ ] la terminal está en la **raíz del repositorio** y el indicador muestra `(.venv)` (compruébalo con
      `pwd` / `Get-Location`);
- [ ] `firmware/releases/sr_support_b_ptk_factory.bin` existe y verifica
      (`sha256sum -c firmware/releases/SHA256SUMS`);
- [ ] `python -m esptool version` funciona, o Flash Download Tool se abre;
- [ ] el puerto serie de la placa es visible;
- [ ] (desarrolladores) `pio --version` funciona;
- [ ] `python tools/env_check.py` imprime `env check: PASS`.

Continúa solo cuando pasen los elementos que necesites.

---

[← Volver al índice del tutorial](./index.md)
