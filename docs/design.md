# Preparação do homelab

Pedido atualizado: preparar Omarchy no HP EliteDesk e no desktop GPU, ambos 24/7; preservar Ubuntu Server como alternativa; testar, abrir PR e integrar se os checks passarem. Não aplicar no Mac nem em máquinas reais nesta etapa.

## Decisões

- Um play para o grupo `workbench`, inventário vazio por padrão, perfil e conta remota obrigatórios. Validar plataforma antes de mudanças. SSH verifica identidade do host.
- Três políticas de pacotes, sem generalizar Ubuntu para todo Linux. Ubuntu tem Engine nativo; Omarchy mantém seu sistema desktop/runtimes; macOS mantém seleção pessoal de pacotes e apps.
- Conta deve existir: evita assumir dados do controlador e não cria usuário/senha com defaults desconhecidos.
- Não gerenciar dotfiles, credenciais, aliases corporativos, partições, BIOS, GPU desconhecida ou firewall sem topologia definida. Não reproduzir instalações duplicadas de runtimes do Mac.
- Remover scripts curl|shell, URLs de GUI sem procedência, TLS inseguro, erros ignorados e configurações mortas. Pacotes presentes não implicam upgrade; versões de projeto ficam explícitas nos projetos.
- Política always-on declarativa, reversível e exclusiva de systemd Linux. Configuração efetiva e API viva validadas separadamente. Não desativar idle lock.
- Avaliador independente que não retorna stdout/stderr de ferramentas. Testes de falha com saída sensível, comando ausente, timeout, GUI no servidor e precedência de configuração.

## Sequência de implementação e aceitação

1. Transferir explicitamente arquivos relevantes do checkout sujo ao worktree; não copiar relatório gerado, venv ou estado local.
2. Implementar preflight e perfis, depois avaliação, política 24/7 e bootstrap documentado.
3. Checks estáticos locais com ferramentas existentes; nenhum playbook aplicado ao Mac.
4. Instalação/idempotência e testes negativos em containers CI. Não usar o daemon local parado nem consumir os ~2,4 GiB restantes.
5. Revisar diff, abrir PR e aguardar todos os checks; merge somente com evidência verde e escopo documentado.

Critério de pronto: código e CI integrados, sem alegar validação de hosts reais. IPs, conta SSH e GPU são informações futuras, não defaults inventados.

Requisito posterior: instalar Tailscale estável atual nos dois Omarchy. Usa extra/tailscale e sincronização + upgrade completo Arch; habilita tailscaled, verifica versão contra o catálogo estável e mantém login na tailnet como etapa interativa, sem auth key.
