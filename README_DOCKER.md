# 🐳 Docker Setup - Mikrotik IPv6 Automation

## 🚀 Quick Start

### 1. Configurar ambiente
```bash
# Copiar arquivos de exemplo
cp .env.example .env
cp hosts.txt.example hosts.txt

# Editar com suas configurações
nano .env
nano hosts.txt
```

### 2. Executar com Docker Compose
```bash
# Executar uma vez
docker-compose up --build

# Executar em background
docker-compose up -d --build

# Ver logs
docker-compose logs -f
```

### 3. Usar Makefile (mais fácil)
```bash
# Executar
make run

# Executar em background  
make run-detached

# Ver logs
make logs

# Parar
make stop
```

## 📋 Comandos Disponíveis

```bash
# Build
make build                 # Construir imagem
make build-no-cache        # Construir sem cache

# Run
make run                   # Executar com docker-compose
make run-detached          # Executar em background
make run-once              # Executar uma vez apenas

# Development 