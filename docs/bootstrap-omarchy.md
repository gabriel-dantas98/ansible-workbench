# Fluxo reproduzível: mídia → instalação → Ansible

Este registro versiona o procedimento, os metadados da mídia e o provisionamento. **Não inclui ISO binária, disco de VM, credenciais nem instalador unattended.** O código Ansible continua separado da instalação do sistema operacional.

## 1. Mídia oficial preparada

| Campo | Valor |
| --- | --- |
| Versão | Omarchy 4.0.4, x86_64 |
| Origem | https://iso.omarchy.org/omarchy-4.0.4.iso |
| Tamanho | 6.185.304.064 bytes |
| SHA256 | `ddeded2758c48318d201dfdac905ecb28f570441883f0c052ea3cd5d05acf92d` |
| Customização | Nenhuma; ISO oficial, sem configuração unattended embutida |

Os mesmos metadados estão em [media/omarchy-4.0.4.json](../media/omarchy-4.0.4.json). Esse é um registro da mídia preparada, não um mecanismo para baixar automaticamente a versão mais nova. Para outra versão, obtenha ISO/checksum oficiais e registre os novos metadados após verificar o arquivo completo.

Em 30/09/2026, o fluxo de preparação da mídia informou que leu **todo o arquivo ISO no Ventoy** e confirmou esse SHA256. O arquivo `.sha256` oficial foi colocado ao lado da ISO. Para repetir a verificação, execute no diretório contendo os dois arquivos:

```bash
# Tamanho, Linux ou macOS:
wc -c < omarchy-4.0.4.iso
# Linux:
sha256sum omarchy-4.0.4.iso
# macOS:
shasum -a 256 omarchy-4.0.4.iso
```

Compare o resultado integral com o manifesto acima e com o checksum oficial acompanhante. Se o arquivo oficial estiver no formato padrão `HASH  nome-do-arquivo`, também pode usar `sha256sum -c ARQUIVO.sha256` (Linux) ou `shasum -a 256 -c ARQUIVO.sha256` (macOS). O checksum valida a integridade do arquivo, não comprova boot nem compatibilidade do hardware.

Teste já realizado no fluxo de mídia: QEMU 11.0.2, firmware UEFI x86_64, emulação TCG num Mac arm64 iniciou o **carregador EFI da ISO**. Não validou o instalador gráfico completo, instalação em disco, drivers GPU nem boot físico via Ventoy. O primeiro teste físico previsto é no HP.

## 2. Instalação interativa e escolha do disco

- Destinos planejados: HP EliteDesk com **8 GB RAM** e desktop com aproximadamente **16 GB ainda não confirmados**. GPU possivelmente **GTX 1060, não confirmada**. Não derivar driver ou requisito de hardware a partir dessas hipóteses.
- O usuário informou três discos SSD/HDD e deseja escolher um SSD para instalação limpa. Isso **não identifica o dispositivo**: não há `/dev/sda`, serial, IP ou capacidade inventados no repositório.
- No menu de boot físico, escolha o pendrive/UEFI e, no Ventoy, a ISO Omarchy 4.0.4. Prossiga interativamente no instalador oficial.
- Confira no próprio instalador modelo e capacidade do SSD pretendido antes de confirmar a instalação limpa, que apaga o disco escolhido. A escolha do disco e a confirmação pertencem ao usuário, no console.
- Conclua a instalação, reinicie no sistema instalado e verifique rede, vídeo e acesso ao console. Faça as atualizações pelo fluxo próprio do Omarchy antes do provisionamento adicional.

Não há script deste repositório que particione discos, altere BIOS/bootloader, selecione automaticamente um SSD ou modifique o pendrive. Unattended foi explorado como possibilidade futura; não foi implementado e exigirá projeto e autorização específicos para o alvo correto.

## 3. Bootstrap de acesso remoto

Em cada Omarchy instalado, no console:

```bash
sudo pacman -Syu --needed python openssh sudo
sudo systemctl enable --now sshd
```

Use a conta criada na instalação, com sudo. Adicione apenas a **chave pública** do controlador ao `authorized_keys` desse usuário. Confira a identidade SSH no console e permita acesso SSH pela rede de administração confiável caso o firewall local esteja bloqueando; a sub-rede e as regras ainda precisam ser definidas, sem expor portas indiscriminadamente.

Do controlador, confirme SSH e sudo. Copie `inventories/homelab.example.yml` para `inventories/private.yml`, substitua os dois IPs e usuários reais. Os dois hosts do exemplo usam `omarchy_desktop`; dados privados ficam fora do Git.

## 4. Provisionamento e avaliação

Com Ansible e as collections já disponíveis no controlador:

```bash
ansible-playbook -i inventories/private.yml site.yml --limit elitedesk --check -K
ansible-playbook -i inventories/private.yml site.yml --limit elitedesk -K
ansible-playbook -i inventories/private.yml validate.yml --limit elitedesk -K
# Repita para gpu_desktop depois de instalar/testar o segundo host.
```

Consulte o [README](../README.md) para dependências do controlador e variáveis. O perfil preserva a base Omarchy, adiciona ferramentas selecionadas e Tailscale estável atual, e aplica a [política 24/7](always-on.md). Tailscale requer atualização completa dos pacotes Arch para evitar partial upgrade; planeje manutenção e eventual reboot manual após updates.

Autenticação é separada: execute `sudo tailscale up` no alvo e conclua o login interativo. Não coloque auth key no repo/logs. Confirme conectividade da tailnet antes de trocar o endereço de administração para ela.

Depois do apply, confirme os checks de serviços e logind na máquina real. Observe um período de inatividade maior que o timeout do desktop: a tela pode bloquear/apagar, enquanto SSH e serviços devem continuar disponíveis. Não use suspensão como teste remoto. O CI prova instalação/idempotência e política systemd em ambientes descartáveis; não substitui essa avaliação de boot, GPU e idle no hardware final.
