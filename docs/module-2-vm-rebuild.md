# Runbook: Recriação da VM `devops-lab`

**Contexto:** em 2026-07-09, durante o Módulo 3 (criação do usuário `claude-ro`), a VM `devops-lab` travou de forma irrecuperável no boot (kernel parava logo após "Loading initial ramdisk...", processo QEMU consumindo ~80-90% de CPU por vários minutos sem nunca produzir prompt de login — nem no console serial, nem via SSH). Diagnóstico descartou: processos `virsh console` zumbis (matados, não resolveu), feature de CPU via `host-passthrough` (trocado pra `host-model` na VM já instalada, não resolveu). Causa raiz não identificada — decisão: recriar a VM do zero em vez de continuar investigando um bug de baixo nível sem garantia de solução rápida. VM antiga apagada (`virsh undefine --remove-all-storage`).

Este arquivo é o roteiro pra recriar tudo, na ordem, com os comandos exatos que já validamos funcionar (extraídos do histórico real do Módulo 2 e 3 no `CLAUDE.md`). Idealmente executar com o Claude Code do lado, ministrando cada passo como já vem sendo feito.

---

## 0. Antes de começar

Confirmar que a VM antiga foi mesmo removida:
```
sudo virsh list --all
```
Não deve aparecer `devops-lab` na lista.

---

## 1. Recriar a VM (script atualizado) — ✅ RESOLVIDO em 2026-07-13

**Conclusão final:** não havia travamento de CPU/hardware nenhum. O sistema **sempre terminava de bootar com sucesso** — o problema era que o kernel instalado nunca recebia `console=ttyS0,115200n8` no cmdline, então todo o boot ficava mudo no console serial logo depois da última mensagem do GRUB ("Loading initial ramdisk..."). Indistinguível de uma trava real sem inspecionar por fora (confirmado comparando o consumo de CPU do processo QEMU via `top`: 0% = ocioso esperando, não girando à toa).

**Como foi descoberto:** o host reiniciou sozinho (rotina, sem relação com a investigação), o que matou o processo QEMU que estava "travado" sem tocar no disco — economizou o `virsh destroy` manual planejado abaixo. Com o disco intacto e a VM desligada, foi feito um backup de segurança (`cp` pra `devops-lab-STUCK-BACKUP.qcow2`) e o disco foi inspecionado **offline**, sem tentar bootar, usando `qemu-nbd --connect=/dev/nbd0 --read-only` (não precisou instalar `guestfish` — o `qemu-nbd` já vem com o `qemu-utils` do Módulo 2):

```bash
sudo modprobe nbd max_part=8
sudo qemu-nbd --connect=/dev/nbd0 --read-only /var/lib/libvirt/images/devops-lab.qcow2
sudo partprobe /dev/nbd0
lsblk /dev/nbd0                      # revelou nbd0p1 (raiz ext4), p2 (extended), p5 (swap)
sudo mkdir -p /mnt/devops-lab-disk
sudo mount -o ro,norecovery /dev/nbd0p1 /mnt/devops-lab-disk   # norecovery: journal sujo (crash), mount read-only puro precisa disso
```

Dentro do disco montado, `grep -A15 "menuentry 'Debian GNU/Linux'" boot/grub/grub.cfg` mostrou a linha `linux /boot/vmlinuz-... root=UUID=... ro quiet` **sem `console=`**, enquanto `/etc/default/grub` tinha `GRUB_TERMINAL=serial` certo (por isso o GRUB em si sempre conseguia falar) mas `GRUB_CMDLINE_LINUX=""` vazio (por isso o kernel nunca continuava a conversa).

**Testes que NÃO foram a causa** (documentados como aprendizado, não repetir):
- Hipótese de falta de entropia (`--rng /dev/urandom`) — descartada.
- `--osinfo debian13` explícito em vez do fallback `generic` — testado numa instalação 100% nova, **não resolveu** (mesmo travamento idêntico). Descarta osinfo como causa.
- Flags de CPU (`host-model`, `qemu64,-svm`) — necessárias por outros motivos (compatibilidade Intel/AMD), mas não relacionadas ao "travamento".

**Correção aplicada:**
1. Confirmada a hipótese com uma edição manual e temporária no menu do GRUB (`e` no boot, `Ctrl+N`/`Ctrl+E` pra navegar em vez de setas — mais confiável em console serial puro — adicionando `console=ttyS0,115200n8` na linha `linux`, `Ctrl+X` pra bootar só dessa vez). Boot mostrou mensagens de kernel normalmente e chegou no prompt de login.
2. Tornado permanente: `GRUB_CMDLINE_LINUX="console=ttyS0,115200n8"` em `/etc/default/grub` (não em `GRUB_CMDLINE_LINUX_DEFAULT`, que já tem o `quiet` — colocar na variável base garante que até o modo de recuperação herde o console serial) + `sudo update-grub`.
3. Testado com `sudo reboot` completo: boot inteiro (GRUB, kernel, login) visível automaticamente, sem qualquer edição manual.

Bug do `sudo`/root (usuário fora do grupo `sudo`, root com senha ativa) apareceu de novo nessa instalação — corrigido com a mesma receita da seção 2 abaixo.

**Estado anterior, mantido como referência histórica:** o travamento **voltou a acontecer**, mesmo depois de duas tentativas de correção. Domínio `devops-lab` ficou parado, ainda "executando" no `virsh` (não foi destruído de propósito, pra permitir inspeção offline do disco na próxima sessão — ver "Próximo passo sugerido" abaixo).

### Linha do tempo de diagnóstico desta sessão

1. **Tentativa com `--cpu host-model` + `--rng /dev/urandom`** (hipótese: falta de entropia no boot do initramfs travando o kernel cedo) → **travou de novo**, exatamente no mesmo ponto ("Loading initial ramdisk..."). Log do QEMU (`/var/log/libvirt/qemu/devops-lab.log`) sem nenhum erro/warning; `virsh domstats` mostrou `insn_emulation.sum` gigante (258 mil) pra poucos segundos de vida — indício de emulação pesada de instrução, não de falta de entropia. Hipótese de entropia **descartada**.
2. **Tentativa com `--cpu qemu64`** (perfil de CPU totalmente genérico, sem nenhuma feature do processador físico) → `virt-install` recusou **antes mesmo de instalar**, com erro `CPU de host não fornece recursos requeridos: svm`. Causa: o modelo `qemu64` do QEMU inclui por padrão a flag `svm` (extensão de virtualização da AMD); o host é Intel, então fisicamente não tem esse recurso. Corrigido desligando a flag: `--cpu qemu64,-svm`.
3. **Com `--cpu qemu64,-svm` + `--rng /dev/urandom`**: o boot do **instalador** (kernel/initrd temporários extraídos pelo `virt-install --location`) passou direto pelo ponto que antes travava — instalação completa do zero até o fim (idioma, locale, usuário, `tasksel`) sem nenhum travamento.
4. **Porém**, ao final da instalação, o `virt-install` detectou a conclusão e trocou a definição da VM de `<kernel>/<initrd>` temporários para `<boot dev='hd'/>` (boot real via GRUB do disco instalado) — e nesse boot, pela primeira vez usando o **initramfs gerado pela própria instalação** (diferente do initrd genérico do instalador), **o travamento voltou**, no mesmo ponto exato ("Loading initial ramdisk...").

### Conclusão desta sessão

A hipótese de CPU (`--cpu qemu64,-svm`) resolveu o boot do **instalador**, mas **não** resolveu o boot do **sistema já instalado** — mesmo processo QEMU, mesmas flags de CPU, dois initrds diferentes, dois resultados diferentes. Isso indica que a causa provavelmente não é (só) a flag de CPU: tem algo específico no initramfs/GRUB gerado pela instalação em si que está contribuindo, e ainda não foi isolado.

### Próximo passo sugerido (executado e resolvido em 2026-07-13)

O passo abaixo (registrado como referência histórica de como a investigação foi planejada) foi exatamente o que resolveu — só que o `virsh destroy` manual acabou sendo feito de graça por um reboot do host no meio do caminho:
```
virsh destroy devops-lab   # desliga sem apagar o disco
```
A inspeção offline do disco (via `qemu-nbd`, ver seção "✅ RESOLVIDO" acima) confirmou a causa: `grub.cfg` sem `console=ttyS0` na linha do kernel. O teste do `--osinfo debian13` explícito foi feito **antes** da inspeção, como teste barato — não resolveu sozinho, mas não foi desperdiçado: descartou definitivamente o osinfo como causa, direcionando o esforço pra investigação offline que achou o problema de verdade.

Script `~/create-vm.sh` atual (no host, fora do repo), já refletindo o estado final:
```bash
#!/bin/bash
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
Depois da instalação, o console serial só continua falando sozinho após o boot se `/etc/default/grub` tiver `GRUB_CMDLINE_LINUX="console=ttyS0,115200n8"` + `sudo update-grub` rodado dentro da VM — isso não é algo que o `virt-install` configura sozinho, precisa ser feito manualmente uma vez após a instalação (ver seção 2 abaixo).

---

## 2. Instalação (interativa, via console serial)

Durante o instalador Debian:
- Idioma do sistema: **inglês** (prática de servidor).
- Locale/teclado: **pt-BR**.
- **Sem** ambiente desktop.
- No `tasksel`: marcar **apenas** `SSH server` (nada de desktop/GUI).
- Usuário: `gerlan`, com senha.

**⚠️ Ponto de atenção (bug real da vez passada):** da última vez, mesmo aparentemente configurado "padrão", a instalação terminou com o **root com senha ativa** e o usuário **fora** do grupo `sudo` (pacote `sudo` nem instalado) — o oposto do que o instalador deveria fazer (usuário com sudo, root travado). Não se sabe se foi escolha durante a instalação ou comportamento do instalador. **Depois de instalar, verificar logo:**
```
groups
sudo -n true && echo "sudo OK" || echo "sudo NAO funciona"
```
Se `sudo` não funcionar, seguir a receita já validada (via `su -`, que funcionou da última vez):
```
su -
apt install sudo
usermod -aG sudo gerlan
exit
```
Abrir uma **sessão SSH nova** (grupo só atualiza em login novo), testar `sudo whoami` → deve responder `root` pedindo sua própria senha. Depois, travar o root de novo (fecha a porta lateral, força tudo via `sudo`):
```
sudo passwd -l root
```

**⚠️ Passo obrigatório (não é automático do instalador): console serial permanente.** Sem isso, todo boot seguinte fica mudo no console serial mesmo tendo sucesso (ver investigação completa na seção 1 acima). Dentro da VM:
```
sudo nano /etc/default/grub
```
Trocar `GRUB_CMDLINE_LINUX=""` por `GRUB_CMDLINE_LINUX="console=ttyS0,115200n8"` (na variável base, não na `_DEFAULT`, pra valer também no modo de recuperação). Depois:
```
sudo update-grub
sudo reboot
```
Reconectar com `sudo virsh console devops-lab` (do host) e confirmar que o boot inteiro aparece sozinho, sem precisar editar nada no menu do GRUB.

---

## 3. Chave SSH do host pra VM (Módulo 2)

No **host**:
```
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_devops-lab -C devops-lab
```
(com passphrase, mesma lógica de sempre — chave de acesso interativo, não de automação)

```
ssh-copy-id -i ~/.ssh/id_ed25519_devops-lab.pub gerlan@<IP_DA_VM>
```
Testar login por chave antes de prosseguir.

---

## 4-7. Hardening, pacotes, deploy key e usuário `claude-ro` — via script

Esses quatro blocos (hardening do sshd, pacotes base, deploy key + clone do
repo, criação do `claude-ro`) foram consolidados num script único e
idempotente: `tools/provision-devops-lab.sh` (versionado no repo, no host).

Antes de rodá-lo, gerar no **HOST** o par de chaves do `claude-ro` (não dá
pra gerar de dentro da VM, o script vai pedir a chave pública no passo 4):
```
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_claude-ro -C "claude-ro@devops-lab" -N ""
```

Copiar o script pro VM (usando a chave do passo 3) e rodar lá:
```
scp -i ~/.ssh/id_ed25519_devops-lab tools/provision-devops-lab.sh gerlan@<IP_DA_VM>:~
ssh -i ~/.ssh/id_ed25519_devops-lab gerlan@<IP_DA_VM>
chmod +x ~/provision-devops-lab.sh
~/provision-devops-lab.sh
```

O script pausa em dois pontos que precisam de ação manual fora do terminal:
- **Deploy key:** ele gera a chave e mostra a pública — cadastrar no GitHub
  (`aprendendo-devops` → **Settings → Deploy keys → Add deploy key**, com
  **Allow write access desmarcado**, read-only). Aproveitar pra apagar a
  deploy key órfã da VM antiga.
- **`claude-ro`:** ele pede pra colar a chave pública gerada no host acima.

**Atenção no passo do hardening (primeira parte do script):** depois que ele
reinicia o `sshd`, **não fechar a sessão atual** antes de confirmar login por
chave numa sessão nova — mesma regra de sempre, nunca se trancar pra fora.

Ao final, testar o bloqueio do `claude-ro` do host:
```
ssh -i ~/.ssh/id_ed25519_claude-ro claude-ro@<IP_DA_VM> "journalctl -n 50"
```
Deve funcionar. E:
```
ssh -i ~/.ssh/id_ed25519_claude-ro claude-ro@<IP_DA_VM> "bash"
```
Deve recusar.

---

## 8. Depois disso

Com tudo acima refeito, a VM volta ao ponto exato de onde paramos antes do travamento: repositório clonado, `claude-ro` funcional. Próximo passo real do Módulo 3 (ainda não feito nem antes do incidente): migrar o `venv`/execução da API de telemetria pra dentro da VM.

Atualizar o `CLAUDE.md` (Histórico de Progresso) conforme cada bloco acima for concluído.
