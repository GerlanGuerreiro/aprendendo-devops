# 🛠️ Trilha de Aprendizado DevOps

> Diário técnico da minha jornada prática rumo à primeira vaga em DevOps/Backend — do controle de versão à infraestrutura em produção.

**Gerlan Guerreiro Damasceno** · Manaus, AM · [GitHub](https://github.com/GerlanGuerreiro) · [LinkedIn](https://www.linkedin.com/in/gerlan-guerreiro-damasceno-4b4291145/)

---

## 📌 Sobre

Este repositório **não é uma aplicação — é a trilha em si**. Cada módulo exercita uma camada real de infraestrutura (VM, redes, containers, orquestração, observabilidade, IaC, CI/CD), usando um projeto-cobaia apenas como payload de dados para praticar: uma **API de Telemetria IoT** (FastAPI + PostgreSQL) simulando uma frota de sensores remotos.

Ponto de partida: Python intermediário, Shell Script, Java, C e Linux — a trilha constrói DevOps sobre essa base.

## 🗺️ Trilha (12 módulos)

- [ ] **01. Fundamentos de Controle** 🔄 — Git, SSH, GPG (commits assinados)
- [ ] **02. Laboratório Isolado (KVM)** 🔄 — VM isolada via QEMU/KVM/libvirt
- [ ] **03. Setup do Projeto na VM** — ambiente da aplicação isolado do host
- [ ] **04. Redes Linux Fundamentais** — bridges, namespaces, iptables/nftables, DNS
- [ ] **05. Isolamento de Baixo Nível** — chroot, LXC
- [ ] **06. Conteinerização Moderna** — Docker, Podman (rootless)
- [ ] **07. Orquestração Local** — Docker Compose, K3s
- [ ] **08. Observabilidade** — Prometheus + Grafana
- [ ] **09. Automação Híbrida** — n8n + webhooks
- [ ] **10. Infraestrutura como Código** — Terraform + Ansible
- [ ] **11. Proficiência Avançada em Claude Code** — subagents, hooks, MCP, modo headless
- [ ] **12. CI/CD & Deploy em Produção** — GitHub Actions + VPS (Oracle Cloud)

## 🧪 Lab: Monitor de Frota IoT

Payload usado para exercitar cada módulo: API REST de ingestão/consulta de telemetria (temperatura, umidade, `device_id`, timestamp) de uma frota simulada de sensores.

**Stack:** Python 3 · FastAPI · PostgreSQL · SQLAlchemy

📂 [`labs/telemetria-api/`](labs/telemetria-api/)

## 🧰 Ferramentas & Práticas

Git · SSH · GPG · KVM/libvirt · Docker · Podman · Kubernetes (K3s) · Prometheus · Grafana · Terraform · Ansible · GitHub Actions · Claude Code

---

*Progresso detalhado, decisões e notas de aula: [`CLAUDE.md`](CLAUDE.md)*
