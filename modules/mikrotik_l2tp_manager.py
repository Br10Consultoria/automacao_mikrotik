#!/usr/bin/env python3
"""
Módulo L2TP Manager - Mikrotik Automation
Especializado em configuração de servidores e clientes L2TP
"""

import logging
import re
from typing import List, Dict, Optional, Tuple
from .mikrotik_connection import MikrotikConnection
from .mikrotik_connectivity_tests import MikrotikConnectivityTests

logger = logging.getLogger(__name__)

class MikrotikL2TPManager:
    """Classe especializada para gerenciar configurações L2TP Server e Client"""
    
    def __init__(self, connection: MikrotikConnection):
        self.connection = connection
    
    def configure_l2tp_server_tunnel(self, tunnel_name: str, server_ip: str, 
                                   client_ip: str, route_network: str, 
                                   route_gateway: str) -> bool:
        """
        Configura túnel L2TP no servidor
        
        Args:
            tunnel_name: Nome do túnel para procurar (ex: "caetite")
            server_ip: IP IPv6 do servidor no túnel (ex: "2804:385c:8700::11")
            client_ip: IP IPv6 do cliente no túnel (ex: "2804:385c:8700::12") 
            route_network: Rede para roteamento (ex: "2804:385c:8700::14/126")
            route_gateway: Gateway da rota (ex: "2804:385c:8700::12")
            
        Returns:
            bool: True se configurado com sucesso
        """
        if not self.connection.is_connected():
            logger.error("❌ Conexão não estabelecida")
            return False
        
        try:
            # 1. Procurar túnel pelo nome
            tunnel_interface = self._find_l2tp_tunnel_by_name(tunnel_name)
            
            if not tunnel_interface:
                logger.error(f"❌ Túnel '{tunnel_name}' não encontrado no servidor")
                return False
            
            logger.info(f"🔍 Túnel encontrado: {tunnel_interface}")
            
            # 2. Adicionar IP IPv6 no servidor (interface do túnel)
            server_ip_with_mask = f"{server_ip}/126"
            add_ip_cmd = f"/ipv6 address add address={server_ip_with_mask} interface={tunnel_interface} advertise=no"
            
            output = self.connection.execute_command(add_ip_cmd)
            if output and ("syntax error" in output.lower() or "failure" in output.lower()):
                if "already have such address" not in output.lower():
                    logger.error(f"❌ Erro ao adicionar IP {server_ip_with_mask}: {output}")
                    return False
                else:
                    logger.info(f"⚠️  IP {server_ip_with_mask} já existe no túnel")
            else:
                logger.info(f"✅ IP {server_ip_with_mask} adicionado ao túnel {tunnel_interface}")
            
            # 3. Criar rota para o segundo bloco
            route_cmd = f"/ipv6 route add dst-address={route_network} gateway={route_gateway} distance=1 check-gateway=ping comment=\"Route-{tunnel_name.upper()}\""
            
            output = self.connection.execute_command(route_cmd)
            if output and ("syntax error" in output.lower() or "failure" in output.lower()):
                if "already have such route" not in output.lower():
                    logger.error(f"❌ Erro ao criar rota {route_network}: {output}")
                    return False
                else:
                    logger.info(f"⚠️  Rota {route_network} já existe")
            else:
                logger.info(f"✅ Rota {route_network} via {route_gateway} criada")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao configurar túnel servidor {tunnel_name}: {e}")
            return False
    
    def configure_l2tp_client(self, bridge_interface: str, bridge_ip: str, 
                            default_gateway: str) -> bool:
        """
        Configura cliente L2TP
        
        Args:
            bridge_interface: Nome da interface bridge (ex: "bridge")
            bridge_ip: IP IPv6 para adicionar na bridge (ex: "2804:385c:8700::15/126")
            default_gateway: Gateway para rota default (ex: "2804:385c:8700::12")
            
        Returns:
            bool: True se configurado com sucesso
        """
        if not self.connection.is_connected():
            logger.error("❌ Conexão não estabelecida")
            return False
        
        try:
            # 1. Verificar se a interface bridge existe
            if not self._interface_exists(bridge_interface):
                # Listar bridges disponíveis para ajudar na configuração
                available_bridges = self._list_available_bridges()
                logger.error(f"❌ Interface {bridge_interface} não encontrada")
                logger.info(f"🔍 Bridges disponíveis: {', '.join(available_bridges) if available_bridges else 'Nenhuma'}")
                return False
            
            # 2. Adicionar IP IPv6 na bridge
            add_ip_cmd = f"/ipv6 address add address={bridge_ip} interface={bridge_interface} advertise=no"
            logger.info(f"🔧 Executando: {add_ip_cmd}")
            
            output = self.connection.execute_command(add_ip_cmd)
            logger.info(f"📤 Saída do comando: {repr(output)}")
            
            if output and ("syntax error" in output.lower() or "failure" in output.lower()):
                if "already have such address" not in output.lower():
                    logger.error(f"❌ Erro ao adicionar IP {bridge_ip}: {output}")
                    return False
                else:
                    logger.info(f"⚠️  IP {bridge_ip} já existe na bridge")
            else:
                # Verificar se o IP foi realmente adicionado
                verify_cmd = f"/ipv6 address print where interface={bridge_interface}"
                verify_output = self.connection.execute_command(verify_cmd)
                
                if verify_output and bridge_ip.split('/')[0] in verify_output:
                    logger.info(f"✅ IP {bridge_ip} confirmado na bridge {bridge_interface}")
                else:
                    logger.warning(f"⚠️  Não foi possível confirmar adição do IP {bridge_ip}")
            
            # 3. Criar rota default
            default_route_cmd = f"/ipv6 route add dst-address=::/0 gateway={default_gateway} distance=1 comment=\"Default-via-L2TP\""
            logger.info(f"🔧 Executando: {default_route_cmd}")
            
            output = self.connection.execute_command(default_route_cmd)
            logger.info(f"📤 Saída do comando: {repr(output)}")
            
            if output and ("syntax error" in output.lower() or "failure" in output.lower()):
                if "already have such route" not in output.lower():
                    logger.error(f"❌ Erro ao criar rota default: {output}")
                    return False
                else:
                    logger.info(f"⚠️  Rota default já existe")
            else:
                # Verificar se a rota foi realmente criada
                verify_route_cmd = "/ipv6 route print where dst-address=::/0"
                verify_route_output = self.connection.execute_command(verify_route_cmd)
                
                if verify_route_output and default_gateway in verify_route_output:
                    logger.info(f"✅ Rota default ::/0 via {default_gateway} confirmada")
                else:
                    logger.warning(f"⚠️  Não foi possível confirmar criação da rota default")
            
            # 4. Executar testes de conectividade
            self._test_connectivity_after_config(bridge_interface, default_gateway)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao configurar cliente L2TP: {e}")
            return False
    
    def _find_l2tp_tunnel_by_name(self, tunnel_name: str) -> Optional[str]:
        """
        Procura túnel L2TP pelo nome no servidor
        
        Args:
            tunnel_name: Nome do túnel para procurar
            
        Returns:
            str: Nome da interface do túnel ou None se não encontrado
        """
        try:
            # Listar interfaces L2TP Server
            command = "/interface l2tp-server print"
            output = self.connection.execute_command(command)
            
            if not output:
                logger.warning("⚠️  Nenhuma resposta do comando l2tp-server print")
                return None
            
            # Procurar túnel pelo nome (case-insensitive)
            lines = output.split('\n')
            
            for line in lines:
                line_lower = line.lower()
                tunnel_name_lower = tunnel_name.lower()
                
                # Procurar o nome do túnel na linha
                if tunnel_name_lower in line_lower and 'l2tp-' in line_lower:
                    # Extrair nome da interface
                    match = re.search(r'<([^>]*l2tp[^>]*)>', line)
                    if match:
                        interface_name = match.group(1)
                        logger.info(f"🎯 Túnel encontrado: {interface_name} para {tunnel_name}")
                        return interface_name
            
            logger.warning(f"⚠️  Túnel '{tunnel_name}' não encontrado")
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao procurar túnel {tunnel_name}: {e}")
            return None
    
    def _interface_exists(self, interface_name: str) -> bool:
        """
        Verifica se uma interface existe
        
        Args:
            interface_name: Nome da interface
            
        Returns:
            bool: True se a interface existe
        """
        try:
            command = f"/interface print where name={interface_name}"
            output = self.connection.execute_command(command)
            
            # Se retornou algo, a interface existe
            return output and interface_name in output
            
        except Exception:
            return False
    
    def _list_available_bridges(self) -> List[str]:
        """
        Lista todas as bridges disponíveis no dispositivo
        
        Returns:
            List[str]: Lista com nomes das bridges
        """
        try:
            command = "/interface bridge print"
            output = self.connection.execute_command(command)
            
            if not output:
                return []
            
            bridges = []
            lines = output.split('\n')
            
            for line in lines:
                # Procurar por padrão: número seguido de flags e name="nome"
                if 'name=' in line and 'R' in line:  # R = running
                    match = re.search(r'name="([^"]+)"', line)
                    if match:
                        bridge_name = match.group(1)
                        bridges.append(bridge_name)
            
            return bridges
            
        except Exception as e:
            logger.error(f"❌ Erro ao listar bridges: {e}")
            return []
    
    def _test_connectivity_after_config(self, bridge_interface: str, gateway: str):
        """
        Executa testes de conectividade após configuração
        
        Args:
            bridge_interface: Interface configurada
            gateway: Gateway configurado
        """
        try:
            logger.info("🧪 Iniciando testes de conectividade pós-configuração...")
            
            # Criar instância de testes
            connectivity_tests = MikrotikConnectivityTests(self.connection)
            
            # Executar testes completos
            test_results = connectivity_tests.test_ipv6_connectivity(
                gateway=gateway,
                test_targets=["2001:4860:4860::8888", "2001:4860:4860::8844"]  # Google DNS IPv6
            )
            
            logger.info("✅ Testes de conectividade concluídos")
            
        except Exception as e:
            logger.error(f"❌ Erro nos testes de conectividade: {e}")
    
    def list_l2tp_server_tunnels(self) -> List[Dict[str, str]]:
        """
        Lista todos os túneis L2TP Server ativos
        
        Returns:
            List[Dict]: Lista de túneis com informações
        """
        try:
            command = "/interface l2tp-server print"
            output = self.connection.execute_command(command)
            
            if not output:
                return []
            
            tunnels = []
            lines = output.split('\n')
            
            for line in lines:
                if 'l2tp-' in line.lower() and ('R' in line or 'running' in line.lower()):
                    # Extrair informações do túnel
                    match = re.search(r'<([^>]*l2tp[^>]*)>', line)
                    if match:
                        tunnel_name = match.group(1)
                        
                        # Tentar extrair usuário e IP cliente
                        parts = line.split()
                        user = ""
                        client_ip = ""
                        
                        for i, part in enumerate(parts):
                            if re.match(r'\d+\.\d+\.\d+\.\d+', part):
                                client_ip = part
                                if i > 0:
                                    user = parts[i-1]
                                break
                        
                        tunnels.append({
                            'interface': tunnel_name,
                            'user': user,
                            'client_ip': client_ip,
                            'status': 'running'
                        })
            
            logger.info(f"📡 Encontrados {len(tunnels)} túneis L2TP ativos")
            return tunnels
            
        except Exception as e:
            logger.error(f"❌ Erro ao listar túneis L2TP: {e}")
            return [] 