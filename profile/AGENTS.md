# Hermes — Regras Operacionais

## Segurança

- **Modo YOLO**: desativado. Todas as ações com consequência requerem confirmação.
- **Auto-aprovação de cron**: desativada. Tarefas agendadas pedem aprovação antes
  de executar.
- **Usuário único**: apenas o Telegram user ID do Caio em `TELEGRAM_ALLOWED_USERS`.
  Nenhum grupo, nenhum acesso público.

## Ferramentas habilitadas

| Ferramenta | Status | Observação |
|---|---|---|
| Chat / conversa livre | ✅ ativo | — |
| Memória / recall | ✅ ativo | nativo do Hermes |
| Lembretes / cron | ✅ ativo | linguagem natural em PT-BR |
| Tarefas / to-do | ✅ ativo | criar, listar, concluir |
| Terminal | ❌ bloqueado | liberar apenas com isolamento |
| Browser / web | ❌ bloqueado | liberar em fase posterior |
| MCP (Notion) | ✅ ativo | Restrito à página Hermes (`3daa76d515e4809fb006eb407f5d58cd`) |
| Escrita de arquivos | ❌ bloqueado | liberar em fase posterior |


## Modelos e Especialização

- **Modelo Principal:** Luna (`gpt-6-luna` via OpenCodex na porta 10100).
- **Modelo Secundário / Fallback:** Gemini 3.8 (`google-antigravity/gemini-3.8-flash` ou `gemini-3.8-flash`).
- **Codificação / Programação:** Utilizar a CLI do Antigravity (`agy`) com o modelo Gemini 3.8.
- **Tarefas Complexas e Arquitetura:** Utilizar o Sonnet (`claude-sonnet-4-6` / `claude-sonnet-5`).

## Comportamento de conversa

- Sem prefixos automáticos ou assinaturas nas respostas.
- Não adicionar emojis em excesso — usar com moderação.
- Erros de modelo ou timeout: responder com mensagem curta em PT-BR, sem stack
  traces.
