# Hermes Agent

Local-first control service. Development happens in Ubuntu on WSL; runtime is
the Galaxy S20 FE through Termux and Ubuntu proot.

Endpoints:

- `GET /health`
- `GET /status`
- `GET /tasks`
- `POST /tasks` with JSON `{"title":"..."}`

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
enough for the phone. Add external AI providers and integrations as explicit
modules once their requirements are known.
