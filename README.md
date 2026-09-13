# Hermes — Operação e Identidade

Repositório de configuração, identidade e deploy do
[Hermes Agent](https://hermes-agent.nousresearch.com/) (Nous Research) para o
Galaxy S20 FE via Termux.

O agente em si é instalado pelo script oficial; este repositório contém apenas o
que é exclusivamente nosso: personalidade, regras, skills e scripts de deploy.

## Estrutura

```
hermes/
├── profile/
│   ├── SOUL.md              # Personalidade: PT-BR, tom direto, fuso horário
│   └── AGENTS.md            # Regras operacionais: sem YOLO, user único
├── config/
│   └── config.template.yaml # Template público (sem segredos)
├── skills/                  # Skills próprias
├── docs/
│   ├── OPERATIONS.md        # Como operar, deploy, rollback
│   ├── TELEGRAM.md          # Gateway Telegram
│   └── SECURITY.md          # Postura de segurança
├── deploy/
│   ├── deploy-phone.sh      # WSL → celular via SSH
│   ├── start-hermes         # Termux:Boot
│   └── health-phone.sh      # Diagnóstico pós-deploy
└── .gitignore
```

## Quick Start

```bash
# 1. Instalar o Hermes oficial no celular (Termux)
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash

# 2. Configurar segredos no celular (nunca no GitHub)
cat > ~/.hermes/.env << 'EOF'
TELEGRAM_BOT_TOKEN=<token>
GROQ_API_KEY=<chave>
TELEGRAM_ALLOWED_USERS=<user-id>
HERMES_TIMEZONE=America/Sao_Paulo
EOF
chmod 600 ~/.hermes/.env

# 3. Deploy do WSL
PHONE_SSH_KEY=~/.ssh/phone PHONE_HOST=<ip> PHONE_USER=<user> bash deploy/deploy-phone.sh
```

## Runtime

```
WSL Ubuntu /home/caio/hermes     desenvolvimento e Git
GitHub 312417/hermes              backup e versionamento
Galaxy S20 FE                     runtime always-on
  Termux → Hermes Agent oficial → hermes gateway telegram
```

## Documentação

- [Operações](docs/OPERATIONS.md)
- [Telegram](docs/TELEGRAM.md)
- [Segurança](docs/SECURITY.md)
- [Hermes Agent (oficial)](https://hermes-agent.nousresearch.com/docs/)

## Runtime antigo

O código Python original (polling próprio, API HTTP, SQLite caseiro) está
preservado na branch `legacy` para referência:

```bash
git checkout legacy
```
