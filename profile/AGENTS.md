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
| MCP (Notion, etc.) | ❌ bloqueado | liberar em fase posterior |
| Escrita de arquivos | ❌ bloqueado | liberar em fase posterior |

## Modelo padrão

- Provedor: Groq (compatibilidade OpenAI)
- Troca a qualquer momento via `hermes model`
- Modelos configurados no `~/.hermes/.env` no celular

## Comportamento de conversa

- Sem prefixos automáticos ou assinaturas nas respostas.
- Não adicionar emojis em excesso — usar com moderação.
- Erros de modelo ou timeout: responder com mensagem curta em PT-BR, sem stack
  traces.
