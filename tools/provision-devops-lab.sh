#!/usr/bin/env bash
set -euo pipefail

# Roda DENTRO da VM devops-lab, como usuário gerlan (já com sudo funcionando
# e já logado via chave SSH — ver docs/module-2-vm-rebuild.md passos 2 e 3).
# Idempotente: pode ser executado de novo sem duplicar nada se parar no meio.

echo "== 1/4: Hardening do sshd =="
HARDENING_FILE=/etc/ssh/sshd_config.d/hardening.conf
if [ ! -f "$HARDENING_FILE" ]; then
    sudo tee "$HARDENING_FILE" > /dev/null <<'EOF'
PasswordAuthentication no
PermitRootLogin no
EOF
    sudo sshd -t
    sudo systemctl restart ssh
    echo "Hardening aplicado. NÃO feche esta sessão antes de confirmar login por chave numa sessão nova."
else
    echo "Hardening já aplicado, ok."
fi

echo
echo "== 2/4: Pacotes base (git, python3-venv) =="
sudo apt update
sudo apt install -y git python3-venv

echo
echo "== 3/4: Deploy key para o GitHub + clone do repositório =="
DEPLOY_KEY=~/.ssh/id_ed25519_deploy
if [ ! -f "$DEPLOY_KEY" ]; then
    ssh-keygen -t ed25519 -f "$DEPLOY_KEY" -C "deploy-key-devops-lab-readonly" -N ""
fi

SSH_CONFIG=~/.ssh/config
if ! grep -q "^Host github.com$" "$SSH_CONFIG" 2>/dev/null; then
    cat >> "$SSH_CONFIG" <<EOF
Host github.com
    HostName github.com
    User git
    IdentityFile $DEPLOY_KEY
    IdentitiesOnly yes
EOF
    chmod 600 "$SSH_CONFIG"
fi

if ! ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
    echo "Chave pública da deploy key (cole em GitHub → repositório → Settings → Deploy keys →"
    echo "Add deploy key, com 'Allow write access' DESMARCADO — read-only):"
    echo
    cat "${DEPLOY_KEY}.pub"
    echo
    echo "Lembre também de apagar a deploy key órfã da VM antiga, se ainda não apagou."
    read -r -p "Pressione Enter depois de cadastrar a chave no GitHub... "
    ssh -T git@github.com || true
fi

if [ ! -d ~/aprendendo-devops ]; then
    git clone git@github.com:GerlanGuerreiro/aprendendo-devops.git
else
    echo "Repositório já clonado, ok."
fi

echo
echo "== 4/4: Usuário claude-ro (acesso somente leitura para o Claude Code) =="
if ! id claude-ro &>/dev/null; then
    sudo useradd -m -s /bin/bash claude-ro
    sudo usermod -aG adm,systemd-journal claude-ro
    sudo passwd -l claude-ro
fi

sudo tee /usr/local/bin/claude-ro-gate.sh > /dev/null <<'EOF'
#!/bin/bash
set -eu

case "$SSH_ORIGINAL_COMMAND" in
  "journalctl -n 50"|"journalctl -n 100")
    exec $SSH_ORIGINAL_COMMAND
    ;;
  "systemctl status telemetria-api")
    exec $SSH_ORIGINAL_COMMAND
    ;;
  "curl -s http://localhost:8000/health")
    exec $SSH_ORIGINAL_COMMAND
    ;;
  *)
    echo "Comando não permitido para claude-ro." >&2
    exit 1
    ;;
esac
EOF
sudo chown root:root /usr/local/bin/claude-ro-gate.sh
sudo chmod 755 /usr/local/bin/claude-ro-gate.sh

sudo mkdir -p /home/claude-ro/.ssh
sudo touch /home/claude-ro/.ssh/authorized_keys
sudo chown -R claude-ro:claude-ro /home/claude-ro/.ssh
sudo chmod 700 /home/claude-ro/.ssh
sudo chmod 600 /home/claude-ro/.ssh/authorized_keys

if [ ! -s /home/claude-ro/.ssh/authorized_keys ]; then
    echo "Cole a chave PÚBLICA do claude-ro, gerada no HOST com:"
    echo '  ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_claude-ro -C claude-ro@devops-lab -N ""'
    echo
    read -r -p "Chave pública: " CLAUDE_RO_PUBKEY
    echo "command=\"/usr/local/bin/claude-ro-gate.sh\",no-agent-forwarding,no-X11-forwarding,no-port-forwarding,no-pty ${CLAUDE_RO_PUBKEY}" \
        | sudo tee /home/claude-ro/.ssh/authorized_keys > /dev/null
else
    echo "authorized_keys do claude-ro já preenchido, ok."
fi

echo
echo "Provisionamento concluído."
