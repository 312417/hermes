# Segurança — Hermes Agent

## Princípios

1. **Segredos nunca entram no GitHub.** Tokens, chaves de API e IDs de usuário
   ficam em `~/.hermes/.env` no celular, com permissão `600`.
2. **Usuário único.** Apenas o Telegram user ID do Caio é autorizado.
3. **Sem modo YOLO.** Todas as ações com consequência pedem confirmação.
4. **Menor privilégio.** Ferramentas são desabilitadas por padrão e liberadas
   progressivamente.

## O que está desabilitado

| Ferramenta | Status | Condição para liberar |
|---|---|---|
| Terminal | ❌ | Isolamento configurado (Docker, sandbox) |
| Browser/web | ❌ | Avaliação de risco concluída |
| MCP (Notion, etc.) | ❌ | Conta dedicada + OAuth + filtro de ferramentas |
| Escrita de arquivos | ❌ | Caso de uso definido com aprovação |

## Postura para Notion (fase futura)

1. Criar conta Notion dedicada para o Hermes.
2. Compartilhar apenas a área Hermes (não o workspace inteiro).
3. Conectar via OAuth/MCP com escopo mínimo.
4. Liberar inicialmente apenas busca e leitura.
5. Escrita somente com confirmação prévia + log de auditoria.
6. Mover e apagar páginas permanecem desabilitados.

## Checklist de segurança

- [ ] `~/.hermes/.env` existe com permissão `600`
- [ ] `.gitignore` bloqueia `*.env`, `.env`, `*.key`, `*.pem`
- [ ] `git log --all -- "*.env"` retorna vazio
- [ ] `TELEGRAM_ALLOWED_USERS` contém apenas um ID
- [ ] Modo YOLO está desativado
- [ ] Auto-aprovação de cron está desativada
