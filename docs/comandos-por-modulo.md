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

## Módulo 4 — Redes Linux Fundamentais

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

### Estágio 1 — namespaces, veth pairs e bridge

```bash
sudo ip netns add ns1
sudo ip netns add ns2
sudo ip link add veth-ns1 type veth peer name veth-br1
sudo ip link add veth-ns2 type veth peer name veth-br2
sudo ip link set veth-ns1 netns ns1
sudo ip link set veth-ns2 netns ns2
sudo ip link add name br-lab type bridge
sudo ip link set veth-br1 master br-lab
sudo ip link set veth-br2 master br-lab
sudo ip netns exec ns1 ip addr add 10.10.10.1/24 dev veth-ns1
sudo ip netns exec ns2 ip addr add 10.10.10.2/24 dev veth-ns2
sudo ip netns exec ns1 ip link set veth-ns1 up
sudo ip netns exec ns1 ip link set lo up
sudo ip netns exec ns2 ip link set veth-ns2 up
sudo ip netns exec ns2 ip link set lo up
sudo ip link set veth-br1 up
sudo ip link set veth-br2 up
sudo ip link set br-lab up
sudo ip addr add 10.10.10.254/24 dev br-lab
```
> `ip link add ... type veth peer name ...`: cria um par de interfaces conectadas ponta-a-ponta (um "cabo" virtual) · `ip link set <if> netns <ns>`: move uma interface pra dentro de um namespace de rede · `type bridge`: cria um switch virtual de camada 2 · `master br-lab`: pluga a interface como porta dessa bridge · `ip netns exec <ns> <cmd>`: roda um comando dentro do namespace de rede · **efêmero** — não sobrevive a reboot da VM; checar `ip netns list` no início de cada sessão e refazer se vier vazio

```bash
sudo ip netns exec ns1 ping -c 3 10.10.10.2
```
> valida que a bridge está encaminhando quadros corretamente entre os dois namespaces

### Estágio 2 — firewall (NAT + bloqueio) com iptables-nft

```bash
sudo apt install iptables
```
> ausente no netinst mínimo, mesmo padrão de `git`/`curl`/`python3-venv` do Módulo 3 · no Debian moderno é na real `iptables-nft`: aceita a sintaxe clássica, mas grava as regras usando o motor `nftables` por baixo — confirmar com `sudo iptables -V` (mostra `(nf_tables)`) e `sudo nft list ruleset` (mesma regra em sintaxe nativa)

```bash
sudo ip netns exec ns1 ip route add default via 10.10.10.254
sudo ip netns exec ns2 ip route add default via 10.10.10.254
sudo iptables -t nat -A POSTROUTING -s 10.10.10.0/24 -o enp1s0 -j MASQUERADE
```
> `-t nat`: tabela de NAT (tradução), não de filtro · `-A POSTROUTING`: regra aplicada depois de decidido o roteamento, na saída · `-s`: filtra pela sub-rede de origem · `-o enp1s0`: só quando sai por essa interface (a "porta pra internet" da VM) · `-j MASQUERADE`: traduz o IP de origem pro IP da própria interface de saída — NAT "empilhado" em cima do NAT que o `virbr0` do Módulo 2 já faz no host

```bash
sudo iptables -A FORWARD -s 10.10.10.2 -j DROP
sudo iptables -L FORWARD -v -n
```
> `-A FORWARD`: chain que decide sobre tráfego "de passagem" (não destinado à própria VM) · descarta silenciosamente (sem avisar o remetente) todo tráfego de `ns2` · `-v`: mostra contador de pacotes/bytes por regra (prova se ela está de fato interceptando) · `-n`: não resolve IP pra nome (mais rápido)

### Estágio 3 — DNS (conceitual, com teste real)

```bash
cat /etc/resolv.conf
sudo ip netns exec ns1 ping -c 2 google.com
```
> confirma qual resolvedor a VM usa e testa resolução de nome de dentro de um namespace — só depende de existir rota até o IP do `nameserver` configurado; se fosse loopback (`127.0.0.53`, comum com `systemd-resolved`) teria falhado, por namespace isolar o `lo`

---

## Módulo 5 — Isolamento de Baixo Nível (chroot & LXC)

### Estágio 1 — chroot puro

```bash
mkdir -p ~/chroot-lab/{bin,lib,lib64,lib/x86_64-linux-gnu}
ldd /bin/bash
```
> `ldd`: lista as bibliotecas dinâmicas (`.so`) que um binário precisa em tempo de execução — sem elas o binário não roda; `linux-vdso.so.1` não é copiado (injetado pelo próprio kernel na memória de todo processo, não é arquivo em disco)

```bash
cp /bin/bash ~/chroot-lab/bin/
cp /lib/x86_64-linux-gnu/libtinfo.so.6 ~/chroot-lab/lib/x86_64-linux-gnu/
cp /lib/x86_64-linux-gnu/libc.so.6 ~/chroot-lab/lib/x86_64-linux-gnu/
cp /lib64/ld-linux-x86-64.so.2 ~/chroot-lab/lib64/
sudo chroot ~/chroot-lab /bin/bash
```
> `chroot` precisa de `sudo` (chamada de sistema privilegiada) · `/lib64/ld-linux-x86-64.so.2` é o linker dinâmico — carrega as outras `.so` antes do binário rodar · dentro do jail, sem `ls` copiado, listar diretório via glob nativo do bash: `echo /*`

```bash
echo $$
kill -0 <PID_de_um_processo_do_host> && echo "eu poderia matar esse processo"
```
> `$$`: PID do processo atual · `kill -0`: não envia sinal nenhum, só testa se haveria permissão — prova (sem risco) que root do jail tem o mesmo alcance de root do host, porque `chroot` não isola nem PID nem UID

```bash
sudo readlink /proc/<PID>/root
```
> rodado de **fora** do jail: mostra pra onde aquele PID específico tem a raiz (`/`) redirecionada — prova que host e processo "isolado" compartilham a mesma tabela de processos, só com metadado de root diferente por processo

### Estágio 3 — LXC via CLI

```bash
sudo apt install lxc
```
> traz `lxc-create`/`lxc-start`/`lxc-attach` + o serviço `lxc-net` (cria a bridge `lxcbr0` sozinho, mesmo papel da `virbr0` do Módulo 2 e da `br-lab` manual do Módulo 4)

```bash
sudo lxc-create -t download -n meucontainer -- -d debian -r trixie -a amd64
```
> `-t download`: template genérico que baixa uma imagem pronta de `images.linuxcontainers.org` (padrão atual do Debian, substituiu os templates por distro) · argumentos depois do `--` vão pro template: distro, release, arquitetura

```bash
sudo lxc-start -n meucontainer -d
sudo lxc-info -n meucontainer
```
> `-d`: roda em background (daemon) · `lxc-info` mostra estado, **PID no host** do processo `init` do container, IP e interface `veth*` (o mesmo mecanismo de veth pair criado manualmente no Módulo 4, aqui automatizado)

```bash
sudo lxc-attach -n meucontainer -- ps aux
ps -p <PID_mostrado_pelo_lxc-info>
```
> compara a visão de dentro (PID 1 = `/sbin/init`) com a de fora (PID real do host) — números diferentes pro mesmo processo físico provam o namespace de PID funcionando, ao contrário do Estágio 1

```bash
sudo lxc-attach -n meucontainer -- hostname
sudo lxc-attach -n meucontainer -- ping -c 3 8.8.8.8
```
> hostname isolado (namespace UTS) · ping funcionando prova NAT em dupla camada: `lxcbr0` (regra `MASQUERADE` que o `lxc-net` já cria sozinho) → `virbr0` (NAT do Módulo 2) → internet

```bash
sudo lxc-cgroup -n meucontainer memory.current
sudo lxc-cgroup -n meucontainer memory.max
sudo lxc-cgroup -n meucontainer memory.max 50M
sudo lxc-cgroup -n meucontainer memory.events
```
> `lxc-cgroup`: lê/escreve direto nos arquivos de controle do cgroup do container, por fora · `memory.max`: teto de memória (cgroup v2) · `memory.events`: contadores — `max` conta quantas vezes o uso bateu no teto e o kernel precisou reclamar memória (ex: swap); `oom_kill` só incrementa se a reclamação falhar e um processo precisar ser morto — teto atingido não é sinônimo de processo morto

---

## Atalhos do projeto

```bash
./tools/tmux-dev.sh
```
> sessão tmux `devops`: Claude Code no painel esquerdo, terminal livre no direito — rodar de novo só reconecta (`tmux attach`), não duplica painéis
