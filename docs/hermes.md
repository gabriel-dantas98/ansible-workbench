# Hermes Agent por usuário

Instalador opcional para Linux, separado do playbook base. Usa o repositório oficial [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent), release `v2026.9.24`, commit `f97608f178d1ffeca59860195ab7da295f7c8e5f`. O [manifesto](hermes-manifest.json) registra a instalação inicial, não credenciais nem estado vivo do provider.

## Instalar ou repetir

No Linux de destino, como o usuário que utilizará o agente, com Git e uv disponíveis:

```bash
bash scripts/install-hermes-user.sh
~/.local/bin/hermes-homelab --version
~/.local/bin/hermes-homelab --help
```

Execute a partir deste repositório. O script recusa root e macOS. Clona em `~/.hermes/hermes-agent`, verifica o commit e alterações nos arquivos rastreados, e sincroniza `venv` usando `uv sync --python 3.13 --extra all --locked --no-dev`. O Python observado na instalação original foi 3.13.15; a seleção 3.13 permite outra versão patch disponibilizada pelo uv. As dependências vêm do `uv.lock` dessa revisão. É necessário acesso à rede para downloads; não há instalação via sudo.

O comando separado `~/.local/bin/hermes-homelab` preserva o launcher `hermes` do Omarchy. O script recusa um launcher existente que não reconheça e não troca a revisão de um checkout existente. Cria apenas configurações mínimas ausentes, com permissões privadas, preservando `.env` e `config.yaml` já existentes. Não copie esses arquivos para este repositório.

## Primeiro uso

Provider, modelo e autenticação são uma etapa interativa do usuário. Consulte `~/.local/bin/hermes-homelab --help` e conclua a configuração local antes de iniciar conversas. O instalador não escolhe provider, transfere credenciais, instala gateway ou inicia serviços. CLI instalada não comprova uma chamada ao modelo funcionando.

## Evidência inicial e manutenção

Na instalação inicial do Hefesto foram reportados CLI/help funcionais, `uv pip check` com 103 dependências consistentes e repetição do sync sem alterações. Esses resultados descrevem aquela instalação; não são uma garantia para qualquer plataforma ou data. Esta integração no repositório não reinstala o host. O CI verifica sintaxe e ShellCheck do instalador; não autentica provider nem faz chamadas pagas.

Para atualizar, revise juntos release, commit e lockfile upstream, teste em ambiente apropriado e atualize o script e manifesto. Não execute `git reset --hard` sobre trabalho local para satisfazer o pin.
