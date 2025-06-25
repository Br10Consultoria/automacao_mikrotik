# 🚀 Mikrotik L2TP IPv6 Automation

Sistema automatizado para configuração de IPv6 em túneis L2TP Mikrotik.

## 🎯 Funcionalidades

### 🖥️ Servidor L2TP
- ✅ Procura túneis pelo nome (ex: "caetite")
- ✅ Configura IPv6 na interface do túnel
- ✅ Cria rotas para redes dos clientes

### 👥 Clientes L2TP  
- ✅ Configura IPv6 na interface bridge
- ✅ Cria rota default via túnel L2TP

## 📋 Configuração

### 1. Credenciais (`.env`)
```env
MIKROTIK_USERNAME=admin
MIKROTIK_PASSWORD=sua_senha
L2TP_SERVER_HOST=1.2.3.4
IPV6_BASE_ADDRESS=2804:385c:8700
```

### 2. Servidor L2TP (`hosts_server_l2tp.txt`)
```
1.2.3.4,SERVER_L2TP_MAIN,SSH
```

### 3. Clientes L2TP (`hosts_clients_l2tp.txt`)
```
177.44.136.153,CAETITE,SSH
177.155.144.109,ADUSTINA,SSH
# ... outros clientes
```

### 4. Mapeamento Túneis (`tunnel_mapping.txt`)
```
caetite,CAETITE,2804:385c:8700:11,2804:385c:8700:12,2804:385c:8700:14/126,2804:385c:8700:12
adustina,ADUSTINA,2804:385c:8700:1,2804:385c:8700:2,2804:385c:8700:4/126,2804:385c:8700:2
```

### 5. Mapeamento Clientes (`client_ipv6_mapping.txt`)
```
CAETITE,bridge,2804:385c:8700:15/126,2804:385c:8700:12
ADUSTINA,bridge,2804:385c:8700:5/126,2804:385c:8700:2
```

## 🚀 Execução

### Docker (Recomendado)
```bash
# Setup inicial
make setup

# Executar automação L2TP
make run

# Ver logs
make logs
```

### Python Direto
```bash
# Instalar dependências
pip install -r requirements.txt

# Executar
python mikrotik_l2tp_automation.py
```

## 📊 Exemplo de Execução

```
🚀 Automação L2TP - Mikrotik IPv6
============================================================

🖥️  CONFIGURANDO SERVIDOR L2TP
----------------------------------------
🔍 Túnel encontrado: l2tp-CAETITE para caetite
✅ IP 2804:385c:8700:11/126 adicionado ao túnel
✅ Rota 2804:385c:8700:14/126 via 2804:385c:8700:12 criada

👥 CONFIGURANDO CLIENTES L2TP
----------------------------------------
✅ IP 2804:385c:8700:15/126 adicionado à bridge
✅ Rota default ::/0 via 2804:385c:8700:12 criada

============================================================
📊 RELATÓRIO FINAL L2TP
============================================================
Servidor L2TP: ✅ Sucesso
Clientes configurados: 12/12
Taxa de sucesso clientes: 100.0%
🎉 Configuração L2TP concluída com sucesso!
```

## 🔧 Fluxo de Configuração

### No Servidor L2TP:
1. Conecta via SSH no servidor (1.2.3.4)
2. Lista túneis L2TP ativos
3. Para cada túnel encontrado:
   - Adiciona IPv6 na interface do túnel
   - Cria rota para rede do cliente

### Nos Clientes L2TP:
1. Conecta via SSH em cada cliente
2. Adiciona IPv6 na interface bridge
3. Cria rota default via túnel

## 📦 Bloco IPv6

**Base:** `2804:385c:8700::/121`
- **Divisão:** 16 blocos `/125` → 32 blocos `/126`
- **Uso:** 2 blocos `/126` por cliente
- **Capacidade:** 12 clientes + 8 blocos reserva

## 🛡️ Segurança

- ✅ Conexões SSH preferenciais
- ✅ Credenciais em arquivo `.env`
- ✅ Container isolado
- ✅ Usuário não-root no Docker

## 🎁 Pronto para Produção

- ✅ Logs detalhados
- ✅ Tratamento de erros
- ✅ Docker containerizado
- ✅ CI/CD GitHub Actions
- ✅ Configuração flexível