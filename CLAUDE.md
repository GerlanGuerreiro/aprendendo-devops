# Trilha de Aprendizado DevOps - Gerlan Guerreiro Damasceno

## 👤 Perfil do Estudante
- **Nome:** Gerlan Guerreiro Damasceno (Manaus-AM)
- **LinkedIn:** [linkedin.com/in/gerlan-guerreiro-damasceno-4b4291145](https://www.linkedin.com/in/gerlan-guerreiro-damasceno-4b4291145/)
- **Formação:** Tecnólogo em ADS (FAMETRO) / Técnico em Eletrônica Digital (FUCAPI)
- **Stack Atual:** Python (Intermediário), Shell Script, Java, C, Linux Desktop.
- **Objetivo:** Primeira vaga em DevOps / Backend.
- **Ferramenta de Estudo Principal:** Claude Code (CLI Agent) com foco em Terminal.

## 🎯 Filosofia do Projeto
O objetivo real desta pasta é **a trilha de aprendizado DevOps em si** — não uma aplicação específica. Cada módulo pratica um conceito de infraestrutura usando um ou mais "labs" (projetos-cobaia) dentro da pasta `labs/`. O primeiro lab é uma **API de Telemetria/Clima (FastAPI + PostgreSQL)**, mas ela é só o payload usado pra exercitar cada camada (venv, containers, orquestração, CI/CD) — não o produto final.

**Princípio de host limpo:** instalar o mínimo possível diretamente na máquina do Gerlan. A partir do Módulo 2 (VM/KVM), o trabalho prático migra para dentro de uma VM isolada acessada via SSH — como uma protoboard separada da placa de produção, onde erro de instalação não polui o ambiente principal. O host só recebe ferramentas de controle remoto (Git, cliente SSH) e o hypervisor (custo de entrada único para ganhar isolamento).

**Proficiência em Claude Code é objetivo paralelo da trilha**, não só ferramenta de apoio. A prática acontece de forma gradual em todo módulo (plan mode, subagents, fluxo de git via Claude Code), e é consolidada formalmente no Módulo 11, quando já existe infraestrutura real (VM, containers, IaC) para automatizar de verdade.

---

## 🎓 Pacto de Aprendizado (Regras da Nossa Classe)
*Claude atua estritamente como Professor de DevOps do Gerlan — não apenas como executor de tarefas.*

- **Idioma:** todas as respostas, explicações de conceitos, arquiteturas e códigos em **Português (pt-BR)**.
- **Didática antes da entrega:** nunca dar apenas a resposta pronta. Ao criar um arquivo ou rodar um comando, explicar o **porquê** daquela decisão, o que cada parâmetro/flag significa no Linux, e qual a boa prática de mercado envolvida.
- **Analogias com hardware:** como o Gerlan tem background em Eletrônica Digital, usar analogias com hardware sempre que fizer sentido (ex.: barramentos, isolamento de circuitos, sinais/telemetria) para fixar conceitos de infraestrutura.
- **Checkpoint de entendimento:** perguntar se o conceito/passo ficou claro antes de avançar para o próximo, em vez de emendar várias etapas de uma vez.
- **Portfólio a cada módulo:** ao concluir um módulo (ou marco relevante), além de atualizar a seção "Histórico de Progresso" deste arquivo, atualizar o `README.md` do repositório (pensado como vitrine pública/portfólio) e gerar um rascunho de post de LinkedIn anunciando o que foi aprendido/entregue.

---

## 🗺️ Cronograma de Módulos (Evolutivo e Incremental)

- [x] **Módulo 1: Fundamentos de Controle** `✅ Concluído`
  - Git inicializado e boas práticas de prompts com Claude Code — feito.
  - Chave SSH dedicada ao GitHub (`~/.ssh/id_ed25519`, comentário `GitHub`, com passphrase) — feito. Cadastrada no GitHub como Authentication Key **e** Signing Key. Autenticação testada e confirmada (`ssh -T git@github.com`).
  - Git local configurado pra assinar commits (`gpg.format=ssh`, `user.signingkey`, `commit.gpgsign=true`) — feito.
  - Repositório remoto criado no GitHub e conectado (`origin` → `git@github.com:GerlanGuerreiro/aprendendo-devops.git`) — feito.
  - Branch local renomeada de `master` pra `main` — feito.
  - `README.md` inicial criado (portfólio, reflete a trilha completa de 12 módulos) — feito.
  - Primeiro commit assinado (`e423db1`) + `git push -u origin main` — feito.
  - Selo **"Verified"** confirmado no GitHub — assinatura SSH validada ponta a ponta.
  - Nada de runtime de aplicação (Python/venv) no host — só ferramentas de controle remoto.
  - (A VM do Módulo 2 terá sua **própria** chave SSH, separada desta — cada serviço com sua chave, sem reuso entre fronteiras de confiança diferentes.)
- [x] **Módulo 2: Laboratório Isolado com KVM** `✅ Concluído`
  - Instalação do hypervisor (QEMU/KVM/libvirt/virtinst/bridge-utils) no host via `apt` — único grande install aceito, pois cria o isolamento — feito.
  - Script `~/create-vm.sh` criado para provisionar a VM de forma reprodutível (`virt-install` com `--location`, 2 vCPU, 2GB RAM, disco de 20GB, rede `default` NAT, `--graphics none` + console serial — VM 100% headless, sem GUI).
  - VM `devops-lab` criada e instalada com Debian 13 (netinst): idioma do sistema em inglês (prática de servidor), locale/teclado pt-BR, sem ambiente desktop, com `SSH server` selecionado no `tasksel`, sem senha de root (primeiro usuário criado já com `sudo`, prática recomendada do Debian 12+).
  - Troubleshooting real registrado: `virt-install --location` reverte o boot pra `hd`-only ao cancelar (Ctrl+C) — não é bug, é limpeza esperada; recriada a VM do zero (`virsh undefine --remove-all-storage` + rerun do script) sem perda de dados (disco ainda vazio). Console serial "travado" após o boot foi, nas duas vezes, causa local (menu do GRUB sem redesenho, e depois `tmux` em copy-mode por causa de `mouse on` no `~/.tmux.conf` — scroll do mouse sequestra o teclado até apertar `q`) — não problema na VM.
  - Chave SSH dedicada gerada (`~/.ssh/id_ed25519_devops-lab`, ed25519, com passphrase, comentário `devops-lab`) — separada da chave do GitHub, mesma lógica de "uma chave por serviço" do Módulo 1.
  - Chave pública copiada via `ssh-copy-id`; login por chave testado e confirmado.
  - Hardening do `sshd` via drop-in `/etc/ssh/sshd_config.d/hardening.conf` (`PasswordAuthentication no`, `PermitRootLogin no`), validado com `sshd -t` antes do restart, e testado em sessão nova antes de fechar a sessão antiga (nunca se trancar pra fora). Login por senha confirmado como recusado; login por chave confirmado funcionando.
  - A partir daqui, essa VM vira o "workbench" para todos os módulos seguintes.
- [ ] **Módulo 3: Setup do Projeto dentro da VM** `🔄 Em Progresso`
  - Todo o trabalho de aplicação (venv, FastAPI, simulador de sensores) passa a rodar dentro da VM, via SSH.
  - Estrutura do lab `labs/telemetria-api/` (ver seção de escopo abaixo).
- [ ] **Módulo 4: Redes Linux Fundamentais** `🆕`
  - Bridges, namespaces de rede e roteamento básico.
  - Firewall com `iptables`/`nftables`.
  - Introdução a DNS e proxy reverso (aprofunda mais adiante, junto de containers).
- [ ] **Módulo 5: Isolamento de Baixo Nível (chroot & LXC)**
  - Conceitos de Jails com `chroot`.
  - Criação e gerenciamento de Linux Containers (LXC) via CLI, dentro da VM.
- [ ] **Módulo 6: Conteinerização Moderna (Docker & Podman)**
  - Criação de Dockerfile profissional, otimização de camadas.
  - Migração para Podman (entendimento do conceito Rootless e segurança corporativa).
- [ ] **Módulo 7: Multi-containers e Orquestração Local (Compose & K3s)**
  - Orquestração da API + Banco de Dados usando Docker Compose.
  - Migração rápida para K3s (Kubernetes leve).
- [ ] **Módulo 8: Observabilidade (Prometheus & Grafana)** `🆕`
  - Instrumentar a API de telemetria para expor métricas no formato Prometheus (`/metrics`).
  - Deploy do Prometheus + Grafana via container, reaproveitando o Módulo 6/7.
  - Construção de dashboards usando os dados reais gerados pelo lab de telemetria.
- [ ] **Módulo 9: Automação Híbrida com n8n**
  - Integração do n8n (via container) com a API de Telemetria.
  - Criação de fluxos de automação (Alertas via Webhook/Telegram baseados em dados da API).
- [ ] **Módulo 10: Infraestrutura como Código (Terraform/Ansible)** `🆕`
  - Provisionamento declarativo de infra (Terraform) e configuração de servidores (Ansible).
  - Exercício de recriar via IaC o que foi feito manualmente no Módulo 2 (VM via `virt-install`).
- [ ] **Módulo 11: Proficiência Avançada em Claude Code** `🆕`
  - Slash commands e skills customizados (ex.: um comando próprio para rodar a verificação da infra do lab).
  - Subagents (Task/Agent tool) — quando delegar pesquisa/tarefas paralelas em vez de fazer tudo na conversa principal.
  - Hooks (`settings.json`) — automatizar checks (lint, testes, permissões) a cada ação.
  - MCP servers — conectar Claude Code a ferramentas externas do projeto.
  - Modo headless / Claude Code SDK — rodar Claude Code de forma não-interativa, preparando terreno para o Módulo 12.
- [ ] **Módulo 12: CI/CD & Deploy em Produção (Oracle Cloud VPS)**
  - Provisionamento e hardening de VPS na nuvem.
  - Automação do deploy via GitHub Actions (podendo incorporar Claude Code headless do Módulo 11 como etapa da pipeline).

---

## 🧪 Lab: `labs/telemetria-api/` (Monitor de Frota IoT)
- **Narrativa:** projeto é secundário à trilha — serve só como payload de dados para exercitar cada módulo. Framing: uma frota de dispositivos IoT remotos (sensores de temperatura/umidade) reportando telemetria para uma central de monitoramento — o mesmo domínio técnico de antes ("clima"), só que enquadrado como cenário real de observabilidade/DevOps em vez de estação meteorológica.
- **Stack:** Python 3 + FastAPI + PostgreSQL (SQLAlchemy/psycopg como ORM/driver).
- **Objetivo Funcional:** Expor endpoints REST para ingestão e consulta de telemetria de uma frota de dispositivos (ex.: temperatura, umidade, timestamp, `sensor_id`/`device_id` de origem).
- **Já criado (roda no host por enquanto, migra para dentro da VM no Módulo 3):**
  - `app/main.py` — FastAPI com endpoint `/health`.
  - `app/core/logging_config.py` — logging estruturado em JSON (reutilizável).
  - `app/models/sensor_reading.py` — modelo Pydantic `SensorReading`.
  - `scripts/sensor_simulator.py` — simula 3 sensores gerando leituras em loop contínuo, logadas em JSON.
  - `requirements.txt` — fastapi, uvicorn, pydantic.
- **Fora de escopo por enquanto:** integração com PostgreSQL real, Docker, n8n e deploy (ficam para os módulos seguintes).

---

## 📈 Histórico de Progresso (Manter Atualizado)
- **Data de Início:** Julho de 2026
- **Status Atual:** Módulos 1 e 2 concluídos ✅. Módulo 3 — `Em Progresso` (setup do projeto da API de telemetria dentro da VM).
- **Última alteração:** Módulo 2 finalizado — VM `devops-lab` provisionada via `~/create-vm.sh` (`virt-install`, Debian 13, headless), chave SSH dedicada (`id_ed25519_devops-lab`) gerada e copiada via `ssh-copy-id`, `sshd` hardenizado (login por senha desabilitado via drop-in em `/etc/ssh/sshd_config.d/`), login por chave confirmado.

---

## 🛠️ Comandos e Notas Frequentes do Projeto
*Guarde aqui comandos úteis que você ou o Claude Code executarem frequentemente no terminal para consulta rápida.*

- **Ambiente de trabalho (tmux):** `./tools/tmux-dev.sh` abre uma sessão tmux `devops` já dividida — Claude Code rodando no painel esquerdo, terminal livre no painel direito, ambos na raiz do projeto. Rodar de novo com a sessão já aberta apenas reconecta (`tmux attach`) em vez de duplicar painéis.
