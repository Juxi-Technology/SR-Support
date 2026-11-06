---
title: 02 Preparação do ambiente (venv, ferramentas de gravação e firmware)
description: Antes de começar — crie e ative o .venv do projeto, obtenha o firmware pré-compilado e uma ferramenta oficial de gravação (Flash Download Tool / esptool), o PlatformIO opcional, as ferramentas do lado do computador e o MuJoCo, e a porta série.
---

# 02 Preparação do ambiente (venv, ferramentas de gravação e firmware)

> Faça esta página antes de começar. **Os comandos assumem a raiz do repositório** — a pasta
> **`SR-Support`** que transferiu do GitHub (uma extração de zip pode chamar-se
> `SR-Support-main`; é a pasta que contém `firmware/` e `tools/`). **Todos os comandos Python
> são executados no terminal com o `.venv` ativado** (2.3). Gravar o firmware pré-compilado não
> requer PlatformIO nem compilação; o ambiente de programador (2.5) serve apenas para alterar o
> código.

## 2.1 Requisitos

- Windows, Linux ou macOS (cada comando abaixo é indicado para os três quando relevante);
- um cabo USB **de dados** (um cabo só de carga não enumera a placa);
- ESP32-S3-DevKitC-1 (8 MB de flash).

## 2.2 Obter o código e o firmware pré-compilado

- Clone o repositório (ou descomprima o arquivo fornecido) e execute os comandos seguintes a
  partir da **raiz do repositório**:

  ```bash
  git clone https://github.com/Juxi-Technology/SR-Support.git
  cd SR-Support
  ```

  (O repositório é privado — peça primeiro o acesso.)

- A **imagem pré-compilada** está em `firmware/releases/`:

  | Ficheiro | Finalidade |
  |---|---|
  | `sr_support_b_ptk_factory.bin` | firmware principal (gravar em 0x0; usado também para a centragem na montagem: ligue até ao zero do firmware, `e` opcional) |
  | `SHA256SUMS` | somas de verificação |

## 2.3 Criar e ativar o ambiente virtual (.venv)

Todas as ferramentas Python do lado do computador (esptool, PlatformIO, as ferramentas MuJoCo)
vão para o **mesmo** `.venv` local do projeto, e esse `.venv` tem de ser criado dentro da pasta
**`SR-Support`** transferida do GitHub (uma extração de zip pode chamar-se `SR-Support-main`; de
novo, a pasta que contém `firmware/` e `tools/`).

Entre primeiro nessa pasta — os comandos abaixo são executados aí:

**Windows (PowerShell)**

```powershell
cd D:\Project\SR-Support    # replace with where your SR-Support folder lives
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

- Não tem a certeza de estar no sítio certo? Execute `dir`; deve listar `firmware`, `tools`,
  `tutorial`;
- Sem Python 3.12, use `py -3 -m venv .venv` (3.10+ funciona);
- Se o PowerShell se recusar a executar scripts, execute
  `Set-ExecutionPolicy -Scope Process Bypass` nesta janela e ative de novo;
- `.\.venv\Scripts\Activate.ps1` é o **script de ativação do PowerShell** que o venv cria:
  o `.\` inicial significa «executar o script na pasta atual» e é obrigatório no
  PowerShell (`Activate.ps1` sem mais não será encontrado). Outras shells usam o seu próprio
  ficheiro:
  - **cmd.exe**: `.venv\Scripts\activate.bat`
  - **Git Bash**: `source .venv/Scripts/activate`
  - Saia do venv com `deactivate`

**Windows (cmd.exe)**

```bat
cd /d D:\Project\SR-Support    # cmd needs /d to change drive; plain cd D:\... stays on C:
py -3.12 -m venv .venv
.venv\Scripts\activate.bat
```

> Distinguir as shells: as linhas de comandos do cmd são do tipo `C:\...>`, as do PowerShell
> `PS C:\...>`. O tutorial usa o PowerShell por omissão; no cmd basta trocar o comando de
> ativação por `activate.bat`, tudo o resto é idêntico. Não são necessários direitos de
> administrador.
>
> **O ficheiro de ativação tem de corresponder à shell**: o cmd usa `activate.bat`, o PowerShell
> usa `Activate.ps1`. Executar o `.ps1` a partir do cmd não ativa a janela atual (normalmente
> nada acontece, ou abre-se uma janela separada). Certifique-se também de que o `.venv` já
> existe (`dir` deve listar a pasta `.venv`); se não, execute primeiro
> `py -3.12 -m venv .venv`.

**Linux / macOS**

```bash
cd ~/SR-Support             # replace with where your SR-Support folder lives
python3 -m venv .venv
source .venv/bin/activate
```

- Não tem a certeza de estar no sítio certo? Execute `ls`; deve listar `firmware`, `tools`,
  `tutorial`.

Após a ativação, o prompt mostra **`(.venv)`**. Todos os comandos abaixo e nas páginas seguintes
do tutorial são executados neste **terminal ativado**; reative após abrir uma nova janela. Sem
ativação, o `pip` / `python` apontam para a instalação do sistema e as instalações ou execuções
falham.

Confirme que a ativação funcionou:

- Windows: `where python` — a primeira linha deve ser
  `...\SR-Support\.venv\Scripts\python.exe`;
- Linux / macOS: `which python` — deve ser `.../SR-Support/.venv/bin/python`.

> **Ecrã limpo depois de ativar no cmd?** O `activate.bat` de origem muda temporariamente a
> página de código da consola (`chcp 65001`) e alguns terminais redesenham o ecrã — **não é um
> novo terminal**. Se o novo prompt começar por `(.venv)` e o `where python` apontar para dentro
> do `.venv`, a ativação foi bem-sucedida. Para evitar o redesenho, use o `Activate.ps1` do
> PowerShell (não mexe na página de código) ou invoque `.venv\Scripts\python.exe` sem ativar.

> **Requisito de diretório (importante)**: o `.venv` tem de residir na **pasta `SR-Support` (a
> raiz do repositório)**, nunca numa subpasta. Os comandos de criação/ativação acima usam
> **caminhos relativos**, por isso têm de ser executados a partir dessa pasta — após abrir um
> novo terminal, entre nela primeiro (PowerShell: `cd D:\Project\SR-Support`; cmd:
> `cd /d D:\Project\SR-Support`, com o seu caminho) antes de ativar, ou use um caminho absoluto
> como `C:\path\SR-Support\.venv\Scripts\Activate.ps1` /
> `source /path/SR-Support/.venv/bin/activate`.
>
> Depois de ativado, pode fazer `cd` para qualquer subpasta e `python` / `pip` / `pio` continuam
> a apontar para esse `.venv`; mas os caminhos `tools/...`, `firmware/...` e `hardware/v1/...`
> do tutorial são relativos, por isso **execute-os a partir da pasta `SR-Support`**. O venv está
> ligado ao caminho onde foi criado: após mover ou renomear o repositório, apague o `.venv` e
> recrie-o.

## 2.4 Ferramentas de gravação (todos os clientes — escolha uma)

Uma imagem pré-compilada é um único bin gravado em 0x0 — **sem PlatformIO, sem transferência de
toolchain**. Certifique-se de que o terminal está na pasta `SR-Support` e o prompt mostra
`(.venv)`.

**A. Windows com interface gráfica: Espressif Flash Download Tool**

1. Abra a página oficial «Other Tools» da Espressif e transfira o Flash Download Tools:
   <https://www.espressif.com/en/support/download/other-tools>
2. Execute-o; selecione **ESP32-S3**, carregue
   `firmware/releases/sr_support_b_ptk_factory.bin` no endereço `0x0`, escolha a porta e
   clique em **START**.

> O Flash Download Tool só existe para Windows; no Linux/macOS use o esptool abaixo.

**B. Windows / Linux / macOS: esptool (linha de comandos)**

```bash
pip install esptool
```

Rede lenta na China — use um espelho:

```bash
pip install esptool -i https://pypi.tuna.tsinghua.edu.cn/simple
```

Gravar (`COM27` é a sua porta; Linux `/dev/ttyACM0`, macOS `/dev/tty.usbmodem*`):

```bash
python -m esptool --chip esp32s3 -p COM27 -b 460800 write_flash 0x0 firmware/releases/sr_support_b_ptk_factory.bin
```

Se a ligação falhar, entre no modo de transferência: mantenha **BOOT** premido, toque em
**RST**, liberte **BOOT**.

## 2.5 PlatformIO (apenas programadores — compilar a partir do código-fonte)

> Salte isto a menos que altere o código. **Nota**: o PlatformIO (incluindo a extensão
> PlatformIO do VS Code) transfere a plataforma espressif32 e a toolchain Xtensa na primeira
> utilização (~1 GB do registo do PlatformIO e do GitHub). Em muitas redes na China isto é lento
> ou falha e precisa de proxy/VPN; a extensão do VS Code não evita a transferência.

Com o terminal na pasta `SR-Support` e o `(.venv)` ativo:

```bash
pip install platformio
```

No Windows também pode executar `tools/install_platformio.ps1`, que instala neste mesmo
`.venv`. Verifique:

```bash
pio --version
```

> Versões anteriores do tutorial instalavam o PlatformIO num `.venv-pio` separado; agora reside
> no único `.venv`. Se o `pio` não for encontrado após a atualização, execute
> `pip install platformio` no `.venv` ativado (ou volte a executar
> `tools/install_platformio.ps1`); o antigo `.venv-pio` pode ser apagado.

## 2.6 Ferramentas do lado do computador e ambiente MuJoCo (gémeo / ponto zero / registos)

Não é necessário para gravar o firmware. Instale-o quando usar a ferramenta de ponto zero com
teclas de seta, o gémeo MuJoCo ao vivo (`tools/live_twin.py`), a reprodução da simulação ou as
ferramentas de registo. Com o terminal na pasta `SR-Support` e o `.venv` ativo, instale as
dependências (pyserial, numpy, MuJoCo 3.1+, gymnasium):

```bash
pip install -r tools/requirements.txt
```

No Windows também pode executar `tools/install_tools_env.ps1` (cria/reutiliza o `.venv` e
instala o mesmo conjunto). Numa rede lenta na China, acrescente o espelho Tsinghua
`-i https://pypi.tuna.tsinghua.edu.cn/simple`; a primeira instalação transfere algumas centenas
de MB.

**Verificação: execute o autoteste do ambiente (carrega e avança o MuJoCo, não apenas imports)**

```bash
python tools/env_check.py
```

A última linha deve ser `env check: PASS`, com uma saída semelhante a:

```text
[ok] mujoco 3.16.0
[ok] model hardware\v1\robot_v1.xml: nq=9 nv=8 dt=0.0002s, 200 steps stable ...
```

Sem placa ligada, `[--] no serial port found` é informativo e não afeta o PASS.

> No Linux, um erro GLFW/OpenGL ao abrir a janela do MuJoCo significa bibliotecas de sistema em
> falta: instale `libgl1` e `libglew-dev` (por exemplo,
> `sudo apt install libgl1 libglew-dev`). Os wheels do MuJoCo para Windows/macOS incluem o que
> precisam. A simulação `training/b_line` e a reprodução usam o mesmo ambiente — não há nada
> extra a instalar.

## 2.7 Ligar a placa e confirmar a porta série

1. Ligue por USB-C; no Windows veja o número COM no Gestor de Dispositivos, no Linux é
   normalmente `/dev/ttyACM0` (adicione o seu utilizador ao grupo `dialout`), no macOS
   normalmente `/dev/tty.usbmodem*`;
2. Memorize a porta — cada `COM27` nas páginas seguintes é este valor;
3. Um monitor série ou o `hw_monitor.py` ocupa a porta; feche-o antes de gravar.

## 2.8 Lista de verificação

- [ ] o terminal está na **raiz do repositório** e o prompt mostra `(.venv)` (verifique com
      `pwd` / `Get-Location`);
- [ ] `firmware/releases/sr_support_b_ptk_factory.bin` existe e verifica-se
      (`sha256sum -c firmware/releases/SHA256SUMS`);
- [ ] `python -m esptool version` funciona, ou o Flash Download Tool abre;
- [ ] a porta série da placa está visível;
- [ ] (programadores) `pio --version` funciona;
- [ ] `python tools/env_check.py` imprime `env check: PASS`.

Só continue quando os itens de que precisa passarem.

---

[← Voltar ao índice do tutorial](./index.md)
