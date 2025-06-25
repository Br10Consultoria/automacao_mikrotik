#!/usr/bin/env python3
"""
Script Especializado L2TP - Mikrotik IPv6 Automation
Configura servidores e clientes L2TP com IPv6
"""

import os
import sys
import logging
from dotenv import load_dotenv
from typing import List, Tuple, Dict

# Importar módulos
from modules import (
    MikrotikConnection,
    MikrotikL2TPManager
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mikrotik_l2tp_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_tunnel_mapping(filename: str = 'tunnel_mapping.txt') -> Dict[str, Dict]:
    """Carrega mapeamento de túneis"""
    mappings = {}
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split(',')
                if len(parts) != 6:
                    logger.warning(f"Linha {line_num} inválida em {filename}: {line}")
                    continue
                
                tunnel_name, client_hostname, server_ip, client_ip, route_network, gateway = [p.strip() for p in parts]
                
                mappings[tunnel_name] = {
                    'client_hostname': client_hostname,
                    'server_ip': server_ip,
                    'client_ip': client_ip,
                    'route_network': route_network,
                    'gateway': gateway
                }
        
        logger.info(f"📋 Carregados {len(mappings)} mapeamentos de túneis")
        return mappings
        
    except FileNotFoundError:
        logger.error(f"❌ Arquivo {filename} não encontrado")
        return {}
    except Exception as e:
        logger.error(f"❌ Erro ao carregar {filename}: {e}")
        return {}

def load_client_mapping(filename: str = 'client_ipv6_mapping.txt') -> Dict[str, Dict]:
    """Carrega mapeamento de clientes"""
    mappings = {}
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split(',')
                if len(parts) != 4:
                    logger.warning(f"Linha {line_num} inválida em {filename}: {line}")
                    continue
                
                hostname, bridge_interface, bridge_ip, gateway = [p.strip() for p in parts]
                
                mappings[hostname] = {
                    'bridge_interface': bridge_interface,
                    'bridge_ip': bridge_ip,
                    'gateway': gateway
                }
        
        logger.info(f"📋 Carregados {len(mappings)} mapeamentos de clientes")
        return mappings
        
    except FileNotFoundError:
        logger.error(f"❌ Arquivo {filename} não encontrado")
        return {}
    except Exception as e:
        logger.error(f"❌ Erro ao carregar {filename}: {e}")
        return {}

def load_hosts(filename: str) -> List[Tuple[str, str, str]]:
    """Carrega lista de hosts"""
    hosts = []
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split(',')
                if len(parts) != 3:
                    logger.warning(f"Linha {line_num} inválida em {filename}: {line}")
                    continue
                
                ip, hostname, method = [part.strip() for part in parts]
                hosts.append((ip, hostname, method))
        
        logger.info(f"📋 Carregados {len(hosts)} hosts de {filename}")
        return hosts
        
    except FileNotFoundError:
        logger.error(f"❌ Arquivo {filename} não encontrado")
        return []
    except Exception as e:
        logger.error(f"❌ Erro ao carregar {filename}: {e}")
        return []

def configure_l2tp_server(username: str, password: str, host: str, 
                         tunnel_mappings: Dict[str, Dict]) -> bool:
    """Configura servidor L2TP"""
    
    logger.info(f"🖥️  Configurando servidor L2TP: {host}")
    
    connection = MikrotikConnection(username, password)
    
    try:
        # Conectar ao servidor
        if not connection.connect_ssh(host):
            logger.error(f"❌ Falha na conexão SSH com servidor {host}")
            return False
        
        l2tp_manager = MikrotikL2TPManager(connection)
        
        # Listar túneis existentes
        tunnels = l2tp_manager.list_l2tp_server_tunnels()
        logger.info(f"📡 Encontrados {len(tunnels)} túneis ativos no servidor")
        
        success_count = 0
        total_count = 0
        
        # Configurar cada túnel baseado no mapeamento
        for tunnel_name, config in tunnel_mappings.items():
            total_count += 1
            
            logger.info(f"🔧 Configurando túnel: {tunnel_name}")
            
            success = l2tp_manager.configure_l2tp_server_tunnel(
                tunnel_name=tunnel_name,
                server_ip=config['server_ip'],
                client_ip=config['client_ip'],
                route_network=config['route_network'],
                route_gateway=config['gateway']
            )
            
            if success:
                success_count += 1
                logger.info(f"✅ Túnel {tunnel_name} configurado com sucesso")
            else:
                logger.error(f"❌ Falha ao configurar túnel {tunnel_name}")
        
        logger.info(f"📊 Servidor L2TP: {success_count}/{total_count} túneis configurados")
        return success_count == total_count
        
    except Exception as e:
        logger.error(f"❌ Erro no servidor L2TP {host}: {e}")
        return False
        
    finally:
        connection.disconnect()

def configure_l2tp_clients(username: str, password: str, client_hosts: List[Tuple[str, str, str]], 
                          client_mappings: Dict[str, Dict]) -> Tuple[int, int]:
    """Configura clientes L2TP"""
    
    logger.info(f"👥 Configurando {len(client_hosts)} clientes L2TP")
    
    success_count = 0
    total_count = len(client_hosts)
    
    for host_ip, hostname, method in client_hosts:
        logger.info(f"🔧 Configurando cliente: {hostname} ({host_ip})")
        
        # Verificar se existe mapeamento para este cliente
        if hostname not in client_mappings:
            logger.warning(f"⚠️  Mapeamento não encontrado para {hostname}")
            continue
        
        config = client_mappings[hostname]
        connection = MikrotikConnection(username, password)
        
        try:
            # Conectar ao cliente
            if method.lower() == 'ssh':
                success = connection.connect_ssh(host_ip)
            else:
                success = connection.connect_telnet(host_ip)
            
            if not success:
                logger.error(f"❌ Falha na conexão com cliente {hostname}")
                continue
            
            l2tp_manager = MikrotikL2TPManager(connection)
            
            # Configurar cliente
            success = l2tp_manager.configure_l2tp_client(
                bridge_interface=config['bridge_interface'],
                bridge_ip=config['bridge_ip'],
                default_gateway=config['gateway']
            )
            
            if success:
                success_count += 1
                logger.info(f"✅ Cliente {hostname} configurado com sucesso")
            else:
                logger.error(f"❌ Falha ao configurar cliente {hostname}")
                
        except Exception as e:
            logger.error(f"❌ Erro no cliente {hostname}: {e}")
            
        finally:
            connection.disconnect()
    
    logger.info(f"📊 Clientes L2TP: {success_count}/{total_count} configurados")
    return success_count, total_count

def main():
    """Função principal"""
    print("🚀 Automação L2TP - Mikrotik IPv6")
    print("=" * 60)
    
    # Carregar variáveis de ambiente
    load_dotenv()
    
    username = os.getenv('MIKROTIK_USERNAME')
    password = os.getenv('MIKROTIK_PASSWORD')
    server_host = os.getenv('L2TP_SERVER_HOST', '1.2.3.4')
    
    if not username or not password:
        logger.error("❌ Credenciais não encontradas no arquivo .env")
        sys.exit(1)
    
    # Carregar mapeamentos
    tunnel_mappings = load_tunnel_mapping()
    client_mappings = load_client_mapping()
    
    if not tunnel_mappings or not client_mappings:
        logger.error("❌ Mapeamentos não carregados")
        sys.exit(1)
    
    # Carregar hosts dos clientes
    client_hosts = load_hosts('hosts_clients_l2tp.txt')
    
    if not client_hosts:
        logger.error("❌ Lista de clientes não carregada")
        sys.exit(1)
    
    print(f"\n🖥️  Servidor L2TP: {server_host}")
    print(f"👥 Clientes L2TP: {len(client_hosts)}")
    print("-" * 60)
    
    # 1. Configurar servidor L2TP
    print("\n🖥️  CONFIGURANDO SERVIDOR L2TP")
    print("-" * 40)
    
    server_success = configure_l2tp_server(username, password, server_host, tunnel_mappings)
    
    # 2. Configurar clientes L2TP
    print("\n👥 CONFIGURANDO CLIENTES L2TP")
    print("-" * 40)
    
    client_success_count, client_total = configure_l2tp_clients(username, password, client_hosts, client_mappings)
    
    # Relatório final
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO FINAL L2TP")
    print("=" * 60)
    print(f"Servidor L2TP: {'✅ Sucesso' if server_success else '❌ Erro'}")
    print(f"Clientes configurados: {client_success_count}/{client_total}")
    print(f"Taxa de sucesso clientes: {(client_success_count/client_total)*100:.1f}%")
    
    overall_success = server_success and (client_success_count == client_total)
    
    if overall_success:
        print("🎉 Configuração L2TP concluída com sucesso!")
        sys.exit(0)
    else:
        print("⚠️  Configuração L2TP concluída com alguns erros.")
        sys.exit(1)

if __name__ == "__main__":
    main() 