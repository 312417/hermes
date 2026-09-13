# Hermes Agent

Local-first control service. Development happens in Ubuntu on WSL; runtime is
the Galaxy S20 FE through Termux and Ubuntu proot.

Endpoints:

- `GET /health`
- `GET /status`
- `GET /tasks`
- `POST /tasks` with JSON `{"title":"..."}`

Telegram commands (enabled after configuring the token on the phone):

- `/status`, `/task título | descrição opcional`, `/tasks`, `/done id`
- `/remind minutos | texto`, `/reminders`
- `/teach título | conteúdo` to add knowledge
- `/ask termos` to search the local knowledge base
- `/remember`, `/memory`, `/profile`, `/forget`, `/clear_session`
- `/tools` to list the explicit tools

Common actions also work in Portuguese without commands:

- `crie uma tarefa Publicar Hermes | revisar os testes`
- `tenho que revisar o servidor`
- `me lembre de beber água em 10 minutos`
- `me avise de ligar para João amanhã às 9`
- `quais são minhas tarefas?`, `quais meus lembretes?`, `quem sou eu?`
- `eu sou o Caio`, `anote na memória que prefiro respostas curtas`

The SQLite database persists the chat session, profile, long-term memory, tasks
and reminders across service and phone restarts. Profile entries are always
included in model context; relevant knowledge is added by text search.

Plain text messages use the configured model provider and recent local memory.
The default deployment uses Groq's OpenAI-compatible Chat Completions API.
Its local router selects `openai/gpt-oss-20b` for fast replies,
`llama-3.3-70b-versatile` for writing, `openai/gpt-oss-120b` with high
reasoning for planning/tasks, and `groq/compound` for explicit current-web
research. Prefix a message with `#fast`, `#text`, `#think`, or `#research`
to choose it directly.

On the phone, run `./configure-secrets.sh` from the Hermes directory. It asks
for the Telegram token and Groq model key without echoing it, writes
`/home/hermes/.config/hermes/telegram.env` with mode 600, and prints a
one-time pairing code. Never commit that file.

The service binds to `127.0.0.1:8787` by default. It is intentionally not
publicly exposed until authentication and a precise use case are defined.

## Runtime layout

```text
WSL Ubuntu /home/caio/hermes     development and Git
GitHub                           source backup and collaboration
Galaxy S20 FE                    always-on runtime
  Termux -> Ubuntu proot -> hermes
```

The first version uses only the Python standard library, so it remains light
enough for the phone. `supervisor.py` runs the HTTP service and Telegram
transport together. The real Telegram token belongs in
`/home/hermes/.config/hermes/telegram.env` on the phone and must never enter
GitHub. The first chat is authorized with a one-time `/pair CODE` handshake.
The Telegram polling loop checks pending reminders every 30 seconds. Configure
`HERMES_TIMEZONE=America/Sao_Paulo` for natural date interpretation.
