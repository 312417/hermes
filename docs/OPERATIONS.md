# Operações — Hermes Agent

## Pré-requisitos

- **WSL (Ubuntu)**: Git, SSH, rsync, bash
- **Celular (Galaxy S20 FE)**: Termux, Termux:Boot, SSH (porta 8022)

## Instalar o Hermes oficial no celular

```bash
# No Termux do celular (não no proot)
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
source ~/.bashrc
hermes --version
```

## Configurar segredos no celular

```bash
# Criar o arquivo de segredos (nunca entra no Git)
cat > ~/.hermes/.env << 'EOF'
TELEGRAM_BOT_TOKEN=<token-do-botfather>
GROQ_API_KEY=<chave-groq>
TELEGRAM_ALLOWED_USERS=<seu-telegram-user-id>
HERMES_TIMEZONE=America/Sao_Paulo
EOF
chmod 600 ~/.hermes/.env
```

## Deploy do WSL para o celular

```bash
# No WSL, a partir do diretório do repositório
export PHONE_SSH_KEY=~/.ssh/phone
export PHONE_HOST=<ip-do-celular>
export PHONE_USER=<usuario-termux>
bash deploy/deploy-phone.sh
```

## Diagnóstico

```bash
bash deploy/health-phone.sh
```

## Inicialização manual do gateway

```bash
# No celular, via SSH ou diretamente no Termux
source ~/.hermes/.env
hermes gateway telegram
```

## Trocar modelo

```bash
# No celular
hermes model
```

## Rollback para o runtime Python antigo

O código Python está preservado na branch `legacy`:

```bash
git checkout legacy
# Seguir o README.md da branch legacy para deploy
```

## Logs

```bash
# Ver log do gateway no celular
ssh -p 8022 -i ~/.ssh/phone user@phone 'tail -50 ~/hermes-gateway.log'
```
