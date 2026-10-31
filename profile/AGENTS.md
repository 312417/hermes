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

- **Modelo Padrão do Hermes (Conversa e Tarefas Gerais):** Gemini 3.8 (`google/gemini-3.8-flash` via OpenRouter).
- **Engenharia de Software e Codificação (via Antigravity CLI / `agy`):**
  - **Planejamento e Tarefas Difíceis:** Sonnet (`claude-sonnet-4-6` / `claude-sonnet-5` / `anthropic/claude-sonnet-5.5`).
  - **Implementação:** Gemini 3.8.
  - **Code Review:** Gemini 3.8.
  - **Testes (Playwright, unitários, validação):** Gemini 3.8.
- **Fallbacks:** Gemini 3.7 Flash, Sonnet 5.5, Luna (OpenCodex).

## Comportamento de conversa

- Sem prefixos automáticos ou assinaturas nas respostas.
- Não adicionar emojis em excesso — usar com moderação.
- Erros de modelo ou timeout: responder com mensagem curta em PT-BR, sem stack
  traces.
