# Regra: Consultar a Doc Oficial do Hermes Antes de Qualquer Mudança

## Obrigação

Antes de implementar **qualquer** funcionalidade, configuração, skill ou integração
neste projeto, você **DEVE** verificar na documentação oficial do Hermes Agent se
o recurso já existe nativamente.

Site oficial: https://hermes-agent.nousresearch.com/docs/

## Como Verificar

A doc é renderizada via JavaScript (Docusaurus). Use `read_url_content` com as
rotas corretas da sidebar. As seções mais relevantes são:

| Seção | URL |
|-------|-----|
| Features Overview | `/docs/user-guide/features/overview` |
| Curator (sumarização) | `/docs/user-guide/features/curator` |
| Persistent Memory | `/docs/user-guide/features/memory` |
| Context Files | `/docs/user-guide/features/context-files` |
| Skills System | `/docs/user-guide/features/skills-system` |
| Toolsets | `/docs/user-guide/features/core-tools` |
| Config Reference | `/docs/reference/cli-commands` |
| Messaging / Telegram | `/docs/user-guide/messaging/` |

> **Nota técnica:** o site é Docusaurus com JS client-side. O conteúdo textual
> não é extraído via HTTP simples. Use `read_url_content` para capturar o HTML
> bruto e extrair o texto com `python3 -c "import re; ..."` ou `grep`.
> O browser subagent (`open_browser_url`) pode falhar por dependência do Playwright.

## Regra de Decisão

```
Preciso de funcionalidade X?
  └── Verificar se já existe na doc oficial
        ├── SIM → Usar o parâmetro/feature nativo (sem reinventar)
        └── NÃO → Implementar como skill/config/script, documentado aqui
```

## Exemplos do Que Checar Antes de Implementar

- **Sumarização de contexto** → `curator` (já existe nativamente)
- **Memória entre sessões** → `memory: enabled: true` (já existe)
- **Limitar histórico** → `model.max_history` (já existe)
- **Agendamento** → `cronjob` toolset (já existe)
- **Execução de scripts sem LLM** → `hermes --script --no-agent` (já existe)
- **Múltiplos perfis** → profiles feature (já existe)

## Contexto do Projeto

Este repositório **não contém o runtime do Hermes** — só o que é exclusivamente
nosso: personalidade (`SOUL.md`), regras, skills e scripts de deploy.
O Hermes oficial é instalado no Galaxy S20 FE via Termux:

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
```

A config é aplicada via `deploy/deploy-phone.sh` (WSL → celular via SSH/rsync).
