# Ansible Workbench

Provisionamento explícito por perfil, com avaliação funcional separada. O controlador pode ser o Mac; as instalações Linux acontecem por SSH nos alvos. Nenhum host é selecionado pelo inventário padrão. O inventário de exemplo prepara **dois Omarchy 24/7**: EliteDesk e desktop GPU; Ubuntu Server permanece como alternativa suportada.

| Perfil | Escopo |
| --- | --- |
| `ubuntu_server` | Ubuntu 24.04/26.04, utilitários mínimos, SSH, Docker Engine + Compose/Buildx opcional; sem GUI |
| `omarchy_desktop` | Omarchy já instalado sobre Arch; acrescenta git-lfs, ShellCheck, uv, GitHub CLI e Tailscale estável, preservando desktop, shell, Neovim, mise e Docker existentes |
| `macos` | Fórmulas e casks pessoais via Homebrew, sem sobrescrever dotfiles, iniciar VM automaticamente ou instalar runtimes por scripts remotos |

Ambos os perfis Linux têm **always-on habilitado**: não suspendem nem hibernam através de systemd. Bloqueio de tela, screensaver, monitor, shutdown e reboot deliberados continuam sob a configuração existente. Veja [política 24/7](docs/always-on.md).

## Bootstrap das máquinas novas

1. Nas duas máquinas, conclua a instalação e atualização pelo fluxo próprio do Omarchy, com um usuário que tenha sudo. Para optar pelo Ubuntu Server, altere somente esse host para `workbench_profile: ubuntu_server` e habilite OpenSSH no instalador.
2. No console Ubuntu, caso falte: `sudo apt update && sudo apt install python3 python3-apt openssh-server sudo`; depois `sudo systemctl enable --now ssh`.
3. No console Omarchy, caso falte: `sudo pacman -Syu --needed python openssh sudo`; depois `sudo systemctl enable --now sshd`. A atualização completa evita partial upgrades de Arch.
4. Instale **sua chave pública** no `authorized_keys` do usuário remoto. Confira a impressão digital SSH no console da máquina antes de aceitar a conexão. Não envie chaves privadas ao repositório.
5. Confirme `ssh usuario@IP` e `sudo -v` no alvo. Os playbooks exigem um usuário existente; não inferem o usuário/home do Mac.

No controlador, use Ansible Core 2.20.x (Python 3.12+) e as collections de `requirements.yml`. Se não estiverem disponíveis, prepare um ambiente isolado no controlador conscientemente; `setup.sh` nunca instala dependências. A implementação foi testada em CI com Core 2.20.3.

```bash
ansible-galaxy collection install -r requirements.yml
cp inventories/homelab.example.yml inventories/private.yml
# Edite IPs, ansible_user e workbench_user. Não coloque senhas/tokens no arquivo.
ansible-inventory -i inventories/private.yml --graph
ansible-playbook -i inventories/private.yml site.yml --limit elitedesk --check -K
ansible-playbook -i inventories/private.yml site.yml --limit elitedesk -K
ansible-playbook -i inventories/private.yml validate.yml --limit elitedesk -K
# Depois repita --limit gpu_desktop.
```

`setup.sh INVENTORY HOST [opções]` é apenas um wrapper da execução explícita. Não aplica no localhost por padrão. O inventário de exemplo usa nomes de IP inválidos intencionais até serem preenchidos.

## Configuração

Variáveis no inventário privado por host:

| Variável | Default | Efeito |
| --- | --- | --- |
| `workbench_profile` | obrigatório | Seleciona um dos três perfis |
| `workbench_user` | obrigatório | Conta existente no alvo; home consultado via banco local de usuários |
| `workbench_manage_docker` | `true` | Ubuntu instala Engine; macOS instala clientes; Omarchy só verifica a base existente |
| `workbench_docker_group` | `false` | Ubuntu: concede ao usuário acesso equivalente a root pelo socket Docker; exige novo login |
| `workbench_manage_services` | `true` | Linux exige systemd e valida serviços; `false` é apenas teste de pacotes/container, sem garantia operacional |
| `workbench_always_on` | `true` | Linux: bloqueia sleep; `false` remove somente os dois drop-ins deste projeto |
| `workbench_extra_packages` | `[]` | Pacotes adicionais explícitos do gerenciador de cada perfil |
| `workbench_allow_local_macos` | `false` | Exigido para aplicar o perfil macOS com conexão local |
| `workbench_macos_start_colima` | `false` | Opt-in para iniciar a VM; não aplicado ao Mac durante este desenvolvimento |

Pacotes ficam em `profiles/`. A maioria usa state `present`; **Omarchy faz atualização completa dos pacotes Arch antes de convergir Tailscale estável**, conforme o requisito de versão atual e sem partial upgrade. Não fixa versões antigas do Mac. A versão disponível vem do repositório assinado da distribuição/Homebrew. Não há mais variáveis de versão que pareçam ser respeitadas mas sejam ignoradas.

Node, Python de projeto, Ruby, Java e outros runtimes devem ser fixados **por projeto**, usando o mise já presente no Omarchy ou o gerenciador escolhido. Este bootstrap não altera NVM/pyenv/rbenv existentes no Mac, não clona ASDF incompleto e não instala seis gerenciadores simultaneamente. CLIs cloud/IA adicionais e SDKs entram depois por necessidade, com versão, origem e teste definidos; não importamos as 197 dependências do Mac.

### Tailscale nos dois Omarchy

Usa `extra/tailscale`, pacote oficial estável do Arch, sem pin obsoleto, AUR ou script curl|shell. A role atualiza o conjunto de pacotes Arch (`pacman -Syu` via módulo) antes de instalar/convergir Tailscale, para não produzir partial upgrade. Isso pode atualizar kernel e outros pacotes: execute previamente as atualizações/migrações próprias do Omarchy e escolha uma janela de manutenção. Não há reboot automático. Se o espelho estiver atrasado em relação ao upstream, o limite é a versão estável publicada nesse repositório; a avaliação compara instalada com o catálogo sincronizado.

`tailscaled` fica enabled/started quando serviços são gerenciados. A avaliação retorna a versão numérica, verifica que coincide com o repositório estável e verifica o serviço e se a versão do daemon em execução coincide com a CLI. A role reinicia tailscaled quando seu pacote muda. **Instalado não significa autenticado.** Depois do apply, execute `sudo tailscale up` em cada máquina e conclua o login interativo no navegador. Não inserir auth keys, tokens ou estado `/var/lib/tailscale` no inventário/repo. A avaliação marca autenticação como `skip` e não lê peers ou credenciais; confirme o acesso à tailnet separadamente antes de depender dela para SSH.

Fontes: [pacote oficial Arch](https://archlinux.org/packages/extra/x86_64/tailscale/), [canal estável Tailscale](https://pkgs.tailscale.com/stable/), [atualizações Omarchy](https://omarchy.org/manual/updates/).

O Docker Ubuntu vem do repositório oficial com chave restrita por `Signed-By`, arquitetura detectada e plugins Compose/Buildx. Pacotes de engines conflitantes causam falha explícita; não são removidos automaticamente. A configuração de firewall/exposição de portas requer desenho dos serviços: portas publicadas pelo Docker precisam de política apropriada, não basta supor que UFW as bloqueia.

## Avaliação e limites

`validate.yml` executa `scripts/evaluate.py` no alvo, sem instalar pacotes nem editar configurações. Ansible ainda usa arquivos temporários para transportar módulos/scripts. O relatório JSON vai ao stdout e contém apenas nomes dos checks e `pass`/`fail`/`skip`; não lista containers, kubecontexts, variáveis de ambiente ou conteúdo de configs pessoais.

Valida plataforma, conta/home, pacotes, comandos, ausência de payloads GUI conhecidos no servidor, Compose/Buildx nos Linux (Compose standalone no macOS), serviços quando habilitados, engine local e política 24/7. Qualquer falha retorna código não zero. Não verifica todas as dependências transitivas, aplicações web, workloads ou extensões de IDE. A detecção de GUI é uma lista explícita, não uma prova de ausência de qualquer software gráfico.

No primeiro `--check`, a instalação Docker pode ser adiada porque seu repositório ainda não existe. Check-mode não instala e **não comprova funcionamento**. `site.yml` só faz avaliação final depois de apply; rode `validate.yml` separadamente quando quiser avaliar o estado atual.

CI verifica YAML/Ansible/shell, testes unitários e containers descartáveis Ubuntu 24.04, Ubuntu 26.04 e Arch: check inicial, instalação real, segunda execução com `changed=0`, check posterior, avaliação, remoção/restauração de always-on e injeção de drift. O fixture Arch apenas representa pré-requisitos já fornecidos pelo Omarchy. **Não é uma instalação Omarchy completa.** Containers sem systemd PID 1 validam pacotes e configuração efetiva em disco; não hardware, boot, GPU ou sessão gráfica. Um job adicional em VM descartável Ubuntu com systemd ativo verifica a role always-on e D-Bus logind sem efetuar sleep; isso não equivale ao hardware final. O daemon Tailscale é exercitado em userspace no container Arch, sem autenticação ou conectividade real à tailnet.

Após acesso às máquinas reais: avaliar com serviços habilitados, conferir SSH após reinício autorizado, manter uma sessão remota durante um período superior ao timeout de idle e confirmar tela bloqueada/apagada com host acessível. Não executar suspensão como teste remoto. Modelo GPU, drivers, CUDA/ROCm e workloads serão decididos após identificação do hardware.

## Histórico da auditoria

Veja [auditoria e escopo](docs/audit-2026-09-30.md) e [decisões de implementação](docs/design.md). As alterações do checkout original foram preservadas; o PR incorpora explicitamente sua seleção macOS e a separação por plataforma, substituindo os instaladores inseguros por perfis.
