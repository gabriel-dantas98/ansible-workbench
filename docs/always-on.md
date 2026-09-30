# Linux 24/7: política e verificação

`workbench_always_on: true` é o default dos dois perfis Linux. A role escreve somente:

- `/etc/systemd/sleep.conf.d/90-ansible-workbench.conf`: `AllowSuspend`, `AllowHibernation`, `AllowHybridSleep` e `AllowSuspendThenHibernate` com `no`.
- `/etc/systemd/logind.conf.d/90-ansible-workbench.conf`: `IdleAction`, teclas de suspensão/hibernação (incluindo pressão longa) e eventos de tampa com `ignore`.

Não altera `HandlePowerKey`/`HandleRebootKey`, timers de lock, DPMS, brilho, screensaver, política de desempenho ou BIOS. O `systemd-sleep` também verifica Allow* antes de executar a operação: não dependemos apenas de esconder um botão no desktop. Não são necessários masks de unidades compartilhadas, que poderiam pertencer a uma política anterior do usuário.

Com systemd real, o handler envia SIGHUP ao processo principal de logind para reler a política, sem reiniciar sessões. `false` remove somente nossos dois arquivos e recarrega logind; não força sleep a ficar disponível contra restrições de hardware ou outros administradores. Nenhum reboot é automático.

## Omarchy

Na documentação atual (consulta em 30/09/2026), o idle manager da shell gerencia screensaver e bloqueio; o toggle de suspend controla a opção do menu. Não chamar `omarchy toggle idle`: isso desabilitaria bloqueio por inatividade, não resolveria o requisito corretamente. Não sobrescrever `shell.json`, Hyprland ou hypridle. Em versões anteriores com hypridle ou customizações que chamam `systemctl suspend`, a política systemd é a barreira comum; o compositor e os timers permanecem intactos. Scripts customizados privilegiados que escrevem diretamente no kernel não estão cobertos.

A base atual pode ficar em `/usr/share/omarchy`; instalações antigas em `~/.local/share/omarchy` também são reconhecidas. O fixture CI comprova compatibilidade de pacotes Arch, não a sessão Omarchy.

## Avaliação

O avaliador usa `systemd-analyze cat-config` para verificar os valores efetivos, respeitando overrides posteriores; a simples presença do drop-in não basta. Com `workbench_manage_services: true`, consulta por D-Bus os quatro métodos `Can*` de sleep e propriedades efetivas de logind. Nunca chama suspend/hibernate como teste.

Em containers sem init: checks de configuração em disco passam/falham; o check de logind vivo fica **skip**. Na máquina real: todos os checks de logind devem passar, e a sessão desktop precisa de observação após timeout de idle para confirmar bloqueio/tela apagada mantendo SSH e serviços acessíveis. A política não garante disponibilidade diante de queda de energia, falha de hardware ou desligamento explícito.

BIOS “power on after AC loss” é uma decisão manual separada para recuperação de energia, não parte de impedir sleep. Não será alterada pelo Ansible.

## Fontes oficiais

- [systemd-sleep.conf — Arch](https://man.archlinux.org/man/systemd-sleep.conf.5.en): Allow* e precedência de drop-ins.
- [logind.conf — Arch](https://man.archlinux.org/man/logind.conf.5.en): idle, lid e teclas; diferença de política do desktop.
- [systemd-logind — Arch](https://man.archlinux.org/man/systemd-logind.service.8.en): recarga por SIGHUP.
- [systemd v255 — Ubuntu 24.04, suporte a SIGHUP](https://github.com/systemd/systemd/blob/v255/src/login/logind.c) e [verificação de Allow*](https://github.com/systemd/systemd/blob/v255/src/sleep/sleep.c).
- [Omarchy: idle e screensaver](https://omarchy.org/manual/toggles-idle-screensaver/) e [system sleep](https://omarchy.org/manual/system-sleep/).
