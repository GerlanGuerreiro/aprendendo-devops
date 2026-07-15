# Comandos por Módulo — Guia de Consulta Rápida

Cola de comandos que funcionaram em cada módulo da trilha, na ordem em que foram
usados. Só o "mundo feliz" — sem os becos sem saída e correções de bugs (esses
ficam documentados no histórico do `CLAUDE.md` e em `docs/module-2-vm-rebuild.md`,
para quem quiser o contexto completo de troubleshooting). Cada bloco de comando
vem seguido de uma linha curta explicando as flags usadas e, quando fizer
sentido, outras opções comuns pro mesmo contexto.

---

## Módulo 1 — Fundamentos de Controle (Git + SSH + assinatura)

```bash
ssh-keygen -t ed25519 -C "GitHub"
```
> `-t ed25519`: tipo de chave (mais moderno, rápido e seguro que RSA) · `-C`: comentário/label da chave (não é senha, só identifica o uso — aparece no GitHub) · outras opções comuns: `-f <caminho>` (nome/local do arquivo, senão pergunta interativo) · `-N ""` (sem passphrase — não usado aqui de propósito, essa é chave de uso interativo)

```bash
ssh -T git@github.com
```
> `-T`: desabilita alocação de pseudo-terminal — só testando autenticação, não abrindo shell

```bash
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
git config --global commit.gpgsign true
```
> `--global`: aplica pro usuário inteiro, em todos os repositórios (contraste com `--local`, que valeria só pra este repo)

```bash
git branch -M main
```
> `-M`: renomeia forçando (sobrescreve se já existir um branch com esse nome — "move" no sentido do Git)

```bash
git push -u origin main
```
> `-u`: seta upstream (linka o branch local ao remoto; próximos `git push` não precisam mais especificar `origin main`)

---

## Módulo 2 — Laboratório Isolado com KVM

```bash
sudo apt install qemu-kvm libvirt-daemon-system virtinst bridge-utils
```
> pacotes: `qemu-kvm` (motor de virtualização) · `libvirt-daemon-system` (API/daemon de gerência) · `virtinst` (utilitário `virt-install`) · `bridge-utils` (ferramentas de bridge de rede)

```bash
virt-install \
  --name devops-lab \
  --memory 2048 \
  --vcpus 2 \
  --cpu qemu64,-svm \
  --rng /dev/urandom \
  --disk path=/var/lib/libvirt/images/devops-lab.qcow2,size=20,format=qcow2 \
  --location /var/lib/libvirt/images/debian-13.5.0-amd64-netinst.iso \
  --network network=default,model=virtio \
  --graphics none \
  --console pty,target_type=serial \
  --extra-args "console=ttyS0,115200n8 serial" \
  --osinfo debian13
```
> `--cpu qemu64,-svm`: perfil de CPU genérico, com a extensão `svm` (virtualização AMD) desligada — necessário porque o host é Intel · `--rng /dev/urandom`: fonte de entropia pra VM (evita boot lento por falta de aleatoriedade) · `--disk ...,format=qcow2`: disco alocado sob demanda (thin-provisioned), não ocupa os 20GB de uma vez · `--location`: instala a partir do kernel/initrd da ISO, em vez de bootar a ISO inteira · `--network network=default,model=virtio`: usa a rede NAT padrão do libvirt, com driver de rede paravirtualizado (mais rápido que emular uma NIC física) · `--graphics none`: sem interface gráfica (headless) · `--console pty,target_type=serial`: expõe console serial, acessível via `virsh console` · `--extra-args`: parâmetros extras pro kernel do instalador (aqui, redireciona saída pro console serial) · `--osinfo`: perfil de otimização do libvirt pro SO alvo (não muda o resultado, só os defaults aplicados) · outras opções comuns: `--cpu host-passthrough` (expõe a CPU real 1:1, mais rápido porém menos portável) · `--graphics spice` (se quisesse GUI)

```bash
sudo virsh list --all
sudo virsh console devops-lab
```
> `--all`: inclui VMs desligadas (por padrão `virsh list` só mostra as rodando) · sair do console serial: `Ctrl+]`

Dentro da VM, console serial permanente (senão todo boot seguinte fica mudo):
```bash
sudo update-grub
sudo reboot
```

Sudo funcionando + root travado:
```bash
su -
apt install sudo
usermod -aG sudo gerlan
exit
# (abrir sessão SSH nova — grupo só atualiza em login novo)
sudo passwd -l root
```
> `su -`: troca pra root com ambiente completo (o `-` recarrega variáveis como se fosse login novo, não só troca de usuário) · `-aG`: `-a` = append (mantém os grupos que o usuário já tinha, só adiciona) + `-G` = lista de grupos secundários — sem o `-a`, `usermod -G` **substitui** todos os grupos do usuário · `passwd -l`: lock, trava a senha (não apaga — `passwd -u` destrava se precisar)

Chave SSH dedicada à VM + hardening do `sshd`:
```bash
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_devops-lab -C devops-lab
ssh-copy-id -i ~/.ssh/id_ed25519_devops-lab.pub gerlan@<IP_DA_VM>
```
> `-f`: caminho/nome do arquivo de saída da chave (senão pergunta interativo) · `ssh-copy-id -i`: especifica qual chave pública copiar (sem isso, tenta todas as chaves default do `~/.ssh`)

`/etc/ssh/sshd_config.d/hardening.conf`:
```
PasswordAuthentication no
PermitRootLogin no
```
```bash
sudo sshd -t
sudo systemctl restart ssh
```
> `sshd -t`: valida a sintaxe do config sem aplicar (dry-run — sempre rodar antes de reiniciar o serviço, pra não se trancar pra fora)

---

## Módulo 3 — Setup do Projeto dentro da VM

```bash
sudo apt install -y git python3-venv curl
```
> `-y`: confirma prompts automaticamente (assume "sim" pra tudo, sem pausar)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
> `python3 -m venv`: `-m` roda um módulo da biblioteca padrão como script (aqui, o módulo `venv`) · `pip install -r`: lê a lista de pacotes de um arquivo, em vez de listar um a um na linha de comando

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
> `--host 0.0.0.0`: escuta em todas as interfaces de rede da VM, não só `localhost` — necessário pra acessar de fora dela · `--port`: porta TCP · `--reload`: reinicia sozinho ao detectar mudança no código (só pra desenvolvimento, nunca em produção — consome mais recurso vigiando arquivos)

```bash
curl http://localhost:8000/health
python scripts/sensor_simulator.py
```
> outras opções comuns do `curl`: `-s` (silencioso, sem barra de progresso — útil em scripts) · `-i` (mostra os headers da resposta, não só o corpo)

```bash
scp -i ~/.ssh/id_ed25519_devops-lab tools/provision-devops-lab.sh gerlan@<IP_DA_VM>:~
ssh -i ~/.ssh/id_ed25519_devops-lab gerlan@<IP_DA_VM>
chmod +x ~/provision-devops-lab.sh
~/provision-devops-lab.sh
```
> `-i` (em `scp`/`ssh`): especifica qual chave privada usar (`IdentitiesOnly` no `~/.ssh/config` reforça isso pro `git`, evitando o SSH tentar outras chaves antes) · `chmod +x`: adiciona permissão de execução (sem isso, `./script.sh` é recusado com "Permission denied")

Testar o portão do `claude-ro` (acesso só-leitura, comando forçado):
```bash
ssh -i ~/.ssh/id_ed25519_claude-ro claude-ro@<IP_DA_VM> "journalctl -n 50"   # funciona
ssh -i ~/.ssh/id_ed25519_claude-ro claude-ro@<IP_DA_VM> "bash"              # recusado
```
> o comando depois do `ssh usuário@host` vira `$SSH_ORIGINAL_COMMAND`, filtrado pelo script em `command=` no `authorized_keys` — só passa o que está na allowlist

---

## Módulo 4 — Redes Linux Fundamentais `🔄 em andamento`

```bash
ip link show type bridge
```
> `type bridge`: filtra a listagem só pras interfaces do tipo bridge (senão `ip link show` lista todas)

```bash
virsh domiflist devops-lab
```
> sem flags — mostra a interface virtual da VM, o modelo (`virtio`) e a bridge a que está conectada

```bash
ip addr show
ip route
ip netns list
```
> sem flags — `ip netns list` vazio confirma que a VM isola por ter kernel próprio (KVM), não por namespace; namespace de verdade só aparece quando existirem containers rodando dentro da VM

Extra (achado real durante o módulo — serviço órfão consumindo recurso no
host, contra o princípio de host limpo):
```bash
dpkg -l | grep -i docker
systemctl status docker --no-pager
systemctl is-enabled docker.socket
sudo systemctl disable docker.socket
sudo systemctl disable docker.service
```
> `dpkg -l`: `-l` lista pacotes instalados (combinado com `grep` pra filtrar) · `--no-pager`: evita abrir o `less` interno do `systemctl`, imprime direto no terminal · Docker usa **socket activation** — `docker.socket` "acorda" o `docker.service` sob demanda mesmo com o serviço desabilitado, por isso os dois precisam ser desabilitados, não só um

---

## Atalhos do projeto

```bash
./tools/tmux-dev.sh
```
> sessão tmux `devops`: Claude Code no painel esquerdo, terminal livre no direito — rodar de novo só reconecta (`tmux attach`), não duplica painéis
