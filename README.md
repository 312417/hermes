# Hermes Agent

Local-first control service. Development happens in Ubuntu on WSL; runtime is
the Galaxy S20 FE through Termux and Ubuntu proot.

Endpoints:

- `GET /health`
- `GET /status`
- `GET /tasks`
- `POST /tasks` with JSON `{"title":"..."}`

Telegram commands (enabled after configuring the token on the phone):

- `/status`, `/task título`, `/tasks`
- `/teach título | conteúdo` to add knowledge
- `/ask termos` to search the local knowledge base
- `/tools` to list the explicit tools

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
