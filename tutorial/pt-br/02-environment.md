---
title: 02 Configuração do ambiente (venv, ferramentas de gravação e firmware)
description: Antes de começar - crie e ative o .venv do projeto, obtenha o firmware pré-compilado e uma ferramenta de gravação oficial (Flash Download Tool / esptool), PlatformIO opcional, as ferramentas do computador e o MuJoCo, e a porta serial.
---

# 02 Configuração do ambiente (venv, ferramentas de gravação e firmware)

> Faça esta página antes de começar. **Os comandos assumem a raiz do repositório** — a **pasta
> `SR-Support`** que você baixou do GitHub (uma extração de zip pode se chamar `SR-Support-main`; é a
> pasta que contém `firmware/` e `tools/`). **Todo comando Python roda no terminal
> com o `.venv` ativado** (2.3). Gravar o firmware pré-compilado não exige PlatformIO nem
> compilação; o ambiente de desenvolvedor (2.5) serve apenas para alterar o código.

## 2.1 Requisitos

- Windows, Linux ou macOS (cada comando abaixo é fornecido para os três sistemas quando relevante);
- um cabo USB **de dados** (um cabo apenas de carga não enumera a placa);
- ESP32-S3-DevKitC-1 (8 MB de flash).

## 2.2 Obtenha o código e o firmware pré-compilado

- Clone o repositório (ou descompacte o arquivo fornecido) e execute os comandos seguintes a partir
  da **raiz do repositório**:

  ```bash
  git clone https://github.com/Juxi-Technology/SR-Support.git
  cd SR-Support
  ```

  (O repositório é privado — solicite acesso primeiro.)

- A **imagem pré-compilada** fica em `firmware/releases/`:

  | Arquivo | Finalidade |
  |---|---|
  | `sr_support_b_ptk_factory.bin` | firmware principal (grave em 0x0; também usado para a centralização na montagem: ligue até o zero do firmware, `e` opcional) |
  | `SHA256SUMS` | somas de verificação (checksums) |

## 2.3 Crie e ative o ambiente virtual (.venv)

Todas as ferramentas Python do lado do computador (esptool, PlatformIO, as ferramentas MuJoCo)
vão para o **mesmo** `.venv` local do projeto, e esse `.venv` deve ser criado dentro da **pasta
`SR-Support`** baixada do GitHub (uma extração de zip pode se chamar `SR-Support-main`; novamente,
a pasta que contém `firmware/` e `tools/`).

Entre nessa pasta primeiro — os comandos abaixo rodam nela:

**Windows (PowerShell)**

```powershell
cd D:\Project\SR-Support    # replace with where your SR-Support folder lives
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

- Não tem certeza de que está no lugar certo? Execute `dir`; ele deve listar `firmware`, `tools`, `tutorial`;
- Sem Python 3.12, use `py -3 -m venv .venv` (3.10+ funciona);
- Se o PowerShell se recusar a executar scripts, execute
  `Set-ExecutionPolicy -Scope Process Bypass` nesta janela e ative novamente;
- `.\.venv\Scripts\Activate.ps1` é o **script de ativação do PowerShell** que o venv cria:
  o `.\` inicial significa "execute o script na pasta atual" e é obrigatório no
  PowerShell (`Activate.ps1` sozinho não será encontrado). Outros shells usam seu próprio arquivo:
  - **cmd.exe**: `.venv\Scripts\activate.bat`
  - **Git Bash**: `source .venv/Scripts/activate`
  - Saia do venv com `deactivate`

**Windows (cmd.exe)**

```bat
cd /d D:\Project\SR-Support    # cmd needs /d to change drive; plain cd D:\... stays on C:
py -3.12 -m venv .venv
.venv\Scripts\activate.bat
```

> Como distinguir os shells: o prompt do cmd parece `C:\...>`, o do PowerShell parece `PS C:\...>`.
> O tutorial usa PowerShell por padrão; no cmd, basta trocar o comando de ativação por
> `activate.bat`, o resto é idêntico. Não são necessários direitos de administrador.
>
> **O arquivo de ativação deve corresponder ao shell**: o cmd usa `activate.bat`, o PowerShell usa
> `Activate.ps1`. Executar o `.ps1` a partir do cmd não ativa a janela atual (normalmente
> nada acontece, ou uma janela separada é aberta). Confirme também que o `.venv` existe primeiro
> (`dir` deve listar a pasta `.venv`); se não, execute `py -3.12 -m venv .venv` primeiro.

**Linux / macOS**

```bash
cd ~/SR-Support             # replace with where your SR-Support folder lives
python3 -m venv .venv
source .venv/bin/activate
```

- Não tem certeza de que está no lugar certo? Execute `ls`; ele deve listar `firmware`, `tools`, `tutorial`.

Após a ativação, o prompt mostra **`(.venv)`**. Todo comando abaixo e nas páginas seguintes do
tutorial roda neste **terminal ativado**; reative após abrir uma nova janela.
Sem ativação, `pip` / `python` apontam para a instalação do sistema e instalações ou execuções
falharão.

Confirme que a ativação funcionou:

- Windows: `where python` — a primeira linha deve ser `...\SR-Support\.venv\Scripts\python.exe`;
- Linux / macOS: `which python` — deve ser `.../SR-Support/.venv/bin/python`.

> **A tela foi limpa após ativar no cmd?** O `activate.bat` original muda temporariamente a
> página de código do console (`chcp 65001`) e alguns terminais redesenham a tela — **não é um
> novo terminal**. Se o novo prompt começa com `(.venv)` e `where python` aponta para dentro de
> `.venv`, a ativação deu certo. Para evitar o redesenho, use o `Activate.ps1` do PowerShell
> (ele não mexe na página de código) ou chame `.venv\Scripts\python.exe` sem ativar.

> **Requisito de diretório (importante)**: o `.venv` deve ficar na **pasta `SR-Support` (a
> raiz do repositório)**, nunca em uma subpasta. Os comandos de criar/ativar acima usam **caminhos
> relativos**, então devem ser executados a partir dessa pasta — após abrir um novo terminal, entre
> nela primeiro (PowerShell: `cd D:\Project\SR-Support`; cmd: `cd /d D:\Project\SR-Support`, com o seu caminho)
> antes de ativar, ou use um caminho absoluto como
> `C:\path\SR-Support\.venv\Scripts\Activate.ps1` /
> `source /path/SR-Support/.venv/bin/activate`.
>
> Uma vez ativado, você pode usar `cd` para qualquer subpasta e `python` / `pip` / `pio` continuam
> apontando para esse `.venv`; mas os caminhos `tools/...`, `firmware/...` e `hardware/v1/...` do
> tutorial são relativos, então **execute-os a partir da pasta `SR-Support`**. O venv está
> vinculado ao caminho onde foi criado: após mover ou renomear o repositório, exclua o `.venv` e
> recrie-o.

## 2.4 Ferramentas de gravação (todos os clientes — escolha uma)

Uma imagem pré-compilada é um único bin gravado em 0x0 — **sem PlatformIO, sem download de
toolchain**. Certifique-se de que o terminal está na pasta `SR-Support` e o prompt mostra `(.venv)`.

**A. Interface gráfica no Windows: Espressif Flash Download Tool**

1. Abra a página oficial "Other Tools" da Espressif e baixe o Flash Download Tools:
   <https://www.espressif.com/en/support/download/other-tools>
2. Execute-o; selecione **ESP32-S3**, carregue
   `firmware/releases/sr_support_b_ptk_factory.bin` no endereço `0x0`, escolha a porta e
   clique em **START**.

> O Flash Download Tool existe apenas para Windows; no Linux/macOS use o esptool abaixo.

**B. Windows / Linux / macOS: esptool (linha de comando)**

```bash
pip install esptool
```

Rede lenta na China — use um espelho:

```bash
pip install esptool -i https://pypi.tuna.tsinghua.edu.cn/simple
```

Grave (`COM27` é a sua porta; Linux `/dev/ttyACM0`, macOS `/dev/tty.usbmodem*`):

```bash
python -m esptool --chip esp32s3 -p COM27 -b 460800 write_flash 0x0 firmware/releases/sr_support_b_ptk_factory.bin
```

Se a conexão falhar, entre no modo de download: segure **BOOT**, toque em **RST**, solte **BOOT**.

## 2.5 PlatformIO (apenas para desenvolvedores — build a partir do código-fonte)

> Pule esta seção a menos que você altere o código. **Nota**: o PlatformIO (incluindo a
> extensão PlatformIO do VS Code) baixa a plataforma espressif32 e o toolchain Xtensa no
> primeiro uso (~1 GB do registro do PlatformIO e do GitHub). Em muitas redes na China isso é
> lento ou falha e exige proxy/VPN; a extensão do VS Code não evita o download.

Com o terminal na pasta `SR-Support` e `(.venv)` ativo:

```bash
pip install platformio
```

No Windows, você também pode executar `tools/install_platformio.ps1`, que instala nesse mesmo
`.venv`. Verifique:

```bash
pio --version
```

> Versões mais antigas do tutorial instalavam o PlatformIO em um `.venv-pio` separado; agora ele
> fica no único `.venv`. Se `pio` não for encontrado após a atualização, execute
> `pip install platformio` no `.venv` ativado (ou execute novamente `tools/install_platformio.ps1`);
> o antigo `.venv-pio` pode ser excluído.

## 2.6 Ferramentas do computador e ambiente MuJoCo (gêmeo / zeragem / logs)

Não é necessário para gravar. Instale quando você usar a ferramenta de zero com teclas de seta,
o gêmeo MuJoCo ao vivo (`tools/live_twin.py`), a reprodução da simulação ou as ferramentas de
log. Com o terminal na pasta `SR-Support` e `.venv` ativo, instale as dependências (pyserial,
numpy, MuJoCo 3.1+, gymnasium):

```bash
pip install -r tools/requirements.txt
```

No Windows, você também pode executar `tools/install_tools_env.ps1` (cria/reutiliza o `.venv` e
instala o mesmo conjunto). Em uma rede lenta na China, acrescente o espelho da Tsinghua
`-i https://pypi.tuna.tsinghua.edu.cn/simple`; a primeira instalação baixa algumas centenas de MB.

**Verificação: execute o autoteste do ambiente (ele carrega e dá passos no MuJoCo, não apenas importa)**

```bash
python tools/env_check.py
```

A última linha deve ser `env check: PASS`, com uma saída parecida com:

```text
[ok] mujoco 3.16.0
[ok] model hardware\v1\robot_v1.xml: nq=9 nv=8 dt=0.0002s, 200 steps stable ...
```

Sem placa conectada, `[--] no serial port found` é informativo e não afeta o PASS.

> No Linux, um erro de GLFW/OpenGL ao abrir a janela do MuJoCo indica bibliotecas de sistema
> ausentes: instale `libgl1` e `libglew-dev` (por exemplo, `sudo apt install libgl1 libglew-dev`).
> Os wheels do MuJoCo para Windows/macOS trazem o que precisam. A simulação e a reprodução de
> `training/b_line` usam o mesmo ambiente — nada extra a instalar.

## 2.7 Conecte a placa e confirme a porta serial

1. Conecte via USB-C; no Windows, veja o número da COM no Gerenciador de Dispositivos; no Linux,
   geralmente é `/dev/ttyACM0` (adicione seu usuário ao grupo `dialout`); no macOS, geralmente
   `/dev/tty.usbmodem*`;
2. Anote a porta — todo `COM27` nas páginas seguintes é este valor;
3. Um monitor serial ou o `hw_monitor.py` ocupa a porta; feche-o antes de gravar.

## 2.8 Lista de verificação

- [ ] o terminal está na **raiz do repositório** e o prompt mostra `(.venv)` (verifique com
      `pwd` / `Get-Location`);
- [ ] `firmware/releases/sr_support_b_ptk_factory.bin` existe e é verificado
      (`sha256sum -c firmware/releases/SHA256SUMS`);
- [ ] `python -m esptool version` funciona, ou o Flash Download Tool abre;
- [ ] a porta serial da placa está visível;
- [ ] (desenvolvedores) `pio --version` funciona;
- [ ] `python tools/env_check.py` imprime `env check: PASS`.

Só continue quando os itens de que você precisa passarem.

---

[← Voltar ao índice do tutorial](./index.md)
