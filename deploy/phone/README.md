# Hermes High-Availability Stack — Samsung Galaxy S20 FE

Solução 100% autônoma executada localmente no Samsung Galaxy S20 FE via Termux e PRoot Ubuntu. Mantém o OpenCodex, o Hermes Agent Gateway e o Dashboard Web supervisionados, resilientes contra encerramentos inesperados e com recuperação automática inteligente.

---

## 1. Arquitetura

- **Supervisor Principal:** `runit` gerenciado via `service-daemon` (`termux-services`).
  - Reinício imediato de processos caídos com parada controlada (SIGTERM → SIGKILL).
  - Logs rotacionados automaticamente via `svlogd` (1 MB por arquivo, limite por serviço).
- **Serviços Supervisionados (`$PREFIX/var/service/`):**
  1. `opencodex`: Proxy local do OpenCodex escutando em `http://127.0.0.1:10100`.
  2. `hermes-gateway`: Gateway de mensagens (Telegram/Slack) do Hermes Agent.
  3. `hermes-dashboard`: Interface web do Hermes na porta local `http://127.0.0.1:9119`.
  4. `dashboard-tunnel`: Túnel Cloudflare seguro expondo o Dashboard publicamente.
  5. `hermes-watchdog`: Monitor periódico de saúde (ciclos de 60s) e disparador de recuperação e backup.
- **Motor de Recuperação (`hermes-recover`):**
  - Proteção contra concorrência via `flock`.
  - Diagnóstico em cadeia respeitando dependências.
  - Distinção entre queda de internet externa (`EXTERNAL_INTERNET_OUTAGE`) e falha local (não reinicia serviços locais se apenas o Wi-Fi/4G oscilar).
  - Backoff progressivo (máximo 5 reinícios em 30 min) e proteção térmica contra aquecimento do aparelho.
- **Backups Diários (`hermes-backup`):**
  - Diário (~03:30 AM): Snapshot rápido das configurações, `.env`, banco SQLite `state.db` e sessões.
  - Semanal (Domingos): Backup completo compactado.
  - Armazenamento privado em `~/hermes-backups` (`chmod 600`) com retenção de 7 diários e 4 semanais.

---

## 2. Caminhos e Permissões

| Caminho | Permissão | Função |
|---|---|---|
| `$PREFIX/bin/hermes` | `755` | CLI unificada de controle e operações |
| `~/.termux/boot/00-supervisor` | `700` | Script de inicialização automática no boot do Android |
| `~/.hermes-ops/bin/hermes-health` | `755` | Diagnóstico real de saúde com timeout |
| `~/.hermes-ops/bin/hermes-recover` | `755` | Motor de recuperação automática com flock e backoff |
| `~/.hermes-ops/bin/hermes-backup` | `755` | Criador e gestor de retenção de backups locais |
| `~/.hermes-ops/state/` | `700` | Locks e contadores de tentativas |
| `~/.hermes-ops/logs/events.log` | `600` | Histórico auditável de eventos e recuperações |
| `~/hermes-backups/` | `700` | Armazenamento de arquivos `.zip` de backup |
| `$PREFIX/var/service/` | `755` | Definições dos serviços supervisionados pelo runit |
| `$PREFIX/var/log/sv/` | `755` | Logs rotacionados de cada serviço |

---

## 3. Guia de Comandos no Termux

O comando `hermes` no Termux gerencia toda a infraestrutura local:

```bash
# Iniciar todos os serviços
hermes up

# Reinicialização limpa forçada (destrava locks, zera backoff e reinicia em ordem)
hermes --force up

# Verificar saúde de toda a pilha (Internet, PRoot, OpenCodex, Gateway, Dashboard, Túnel)
hermes health

# Listar status e PIDs dos serviços no supervisor
hermes ps

# Ver logs de um serviço em tempo real
hermes logs hermes-gateway -f
hermes logs opencodex -f
hermes logs hermes-dashboard -f

# Ver histórico de falhas e recuperações
hermes events

# Obter URL local e pública do Dashboard
hermes url

# Disparar backup imediato
hermes backup
hermes backup --full

# Parar todos os serviços
hermes down

# Desativar ou reativar supervisão automática
hermes disable
hermes enable
```

*Qualquer outro subcomando (ex: `hermes doctor`, `hermes models`, `hermes tools`) é automaticamente repassado ao Hermes Agent no container Ubuntu.*

---

## 4. Inicialização no Boot e Configurações no Android

1. **Termux:Boot:** O script `~/.termux/boot/00-supervisor` é executado na inicialização.
2. **Desativação do Phantom Process Killer (via ADB):**
   ```bash
   device_config set_sync_disabled_for_tests persistent
   device_config put activity_manager max_phantom_processes 2147483647
   settings put global settings_enable_monitor_phantom_procs false
   ```
3. **Whitelist de Bateria (via ADB):**
   ```bash
   dumpsys deviceidle whitelist +com.termux
   dumpsys deviceidle whitelist +com.termux.boot
   ```
4. **Configurações Manuais no Samsung S20 FE:**
   - *Configurações* → *Aplicativos* → *Termux* e *Termux:Boot* → *Bateria* → selecionar **Irrestrito**.
   - *Assistência do aparelho* → *Bateria* → *Limites de uso em 2º plano* → adicionar o Termux em **Aplicativos nunca suspensos**.

---

## 5. Limitações Conhecidas

- **Primeiro Desbloqueio após Reboot (Direct Boot):** Por segurança de criptografia do Android, o Termux só inicia seus processos em segundo plano após o usuário inserir o PIN/senha pela primeira vez após o celular ligar.
- **Encerramento Forçado pelo Usuário:** Se o usuário fechar o Termux via multitarefa ("Fechar Tudo"), o Android envia SIGKILL para todos os processos filhos. A solução se recupera ao reabrir o app Termux ou no próximo boot.
