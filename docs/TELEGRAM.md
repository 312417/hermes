# Telegram — Hermes Agent

## Visão geral

O Hermes Agent usa o **Gateway Telegram oficial** da Nous Research. Não há mais
polling próprio nem bot customizado — o gateway gerencia a conexão, fila de
mensagens e entrega de notificações automaticamente.

## Configuração

1. Criar bot no [@BotFather](https://t.me/BotFather) (ou reutilizar o existente)
2. Copiar o token gerado
3. Obter seu Telegram user ID (enviar `/start` para [@userinfobot](https://t.me/userinfobot))
4. Configurar no celular:

```bash
# Em ~/.hermes/.env
TELEGRAM_BOT_TOKEN=<token-do-botfather>
TELEGRAM_ALLOWED_USERS=<seu-user-id>
```

## Segurança

- `TELEGRAM_ALLOWED_USERS` restringe o acesso ao seu user ID.
- Nenhum grupo é permitido.
- Nenhum acesso público.
- O gateway oficial protege contra mensagens de terceiros.

## Comandos disponíveis

O Hermes oficial reconhece linguagem natural e comandos internos. As interações
anteriores (`/task`, `/remind`, `/teach`, etc.) são substituídas por conversa
livre:

| Antes (Python caseiro) | Agora (Hermes oficial) |
|---|---|
| `/task título` | "crie uma tarefa: título" |
| `/remind 10 \| texto` | "me lembre de texto em 10 minutos" |
| `/teach título \| conteúdo` | "anote que conteúdo" |
| `/status` | "como você está?" |
| `/tasks` | "quais são minhas tarefas?" |
| `/done id` | "conclua a tarefa X" |

## Troubleshooting

- **Bot não responde**: verificar `hermes gateway telegram` via SSH e o log em
  `~/hermes-gateway.log`
- **"Unauthorized"**: confirmar que `TELEGRAM_ALLOWED_USERS` contém seu user ID
- **Timeout**: verificar conexão à internet do celular e `termux-wake-lock`
