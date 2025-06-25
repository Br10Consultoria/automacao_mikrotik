#!/usr/bin/env python3
"""
Módulo de Interfaces - Mikrotik Automation
Responsável por listar e gerenciar interfaces L2TP
"""

import logging
import re
from typing import List, Dict, Optional
from .mikrotik_connection import MikrotikConnection

logger = logging.getLogger(__name__)

class MikrotikInterfaces:
    """Classe para gerenciar interfaces L2TP em dispositivos Mikrotik"""
    
    def __init__(self, connection: MikrotikConnection):
        self.connection = connection
    
    def list_l2tp_server_interfaces(self) -> List[Dict[str, str]]:
        """
        Lista todas as interfaces L2TP Server ativas
        
        Returns:
            List[Dict]: Lista de interfaces com suas informações
        """
        if not self.connection.is_connected():
            logger.error("❌ Conexão não estabelecida")
            return []
        
        try:
            # Comando para listar interfaces L2TP Server
            command = "/interface l2tp-server print"
            output = self.connection.execute_command(command)
            
            if not output:
                logger.warning("⚠️  Nenhuma resposta do comando l2tp-server print")
                return []
            
            interfaces = self._parse_l2tp_server_output(output)
            
            logger.info(f"📡 Encontradas {len(interfaces)} interfaces L2TP Server")
            
            # Log das interfaces encontradas
            for interface in interfaces:
                logger.info(f"  🔗 {interface['name']} - Cliente: {interface['client_address']} - Usuário: {interface['user']}")
            
            return interfaces
            
        except Exception as e:
            logger.error(f"❌ Erro ao listar interfaces L2TP Server: {e}")
            return []
    
    def list_l2tp_client_interfaces(self) -> List[Dict[str, str]]:
        """
        Lista todas as interfaces L2TP Client
        
        Returns:
            List[Dict]: Lista de interfaces cliente L2TP
        """
        if not self.connection.is_connected():
            logger.error("❌ Conexão não estabelecida")
            return []
        
        try:
            command = "/interface l2tp-client print"
            output = self.connection.execute_command(command)
            
            if not output:
                logger.warning("⚠️  Nenhuma resposta do comando l2tp-client print")
                return []
            
            interfaces = self._parse_l2tp_client_output(output)
            
            logger.info(f"📡 Encontradas {len(interfaces)} interfaces L2TP Client")
            
            return interfaces
            
        except Exception as e:
            logger.error(f"❌ Erro ao listar interfaces L2TP Client: {e}")
            return []
    
    def _parse_l2tp_server_output(self, output: str) -> List[Dict[str, str]]:
        """
        Faz parse da saída do comando l2tp-server print
        
        Args:
            output: Saída do comando RouterOS
            
        Returns:
            List[Dict]: Lista de interfaces parseadas
        """
        interfaces = []
        lines = output.split('\n')
        
        # Encontrar linha com headers
        header_line = -1
        for i, line in enumerate(lines):
            if 'NAME' in line and 'USER' in line and 'CLIENT-ADDRESS' in line:
                header_line = i
                break
        
        if header_line == -1:
            logger.warning("⚠️  Headers não encontrados na saída l2tp-server")
            return []
        
        # Processar linhas de dados
        for line in lines[header_line + 1:]:
            line = line.strip()
            
            # Pular linhas vazias
            if not line:
                continue
            
            # Buscar padrão: número, flags, nome da interface
            match = re.match(r'\s*(\d+)\s+([DRX\s]+)\s*<([^>]+)>\s+(\S+)\s+(\d+)\s+([\d\.]+)', line)
            
            if match:
                interface_info = {
                    'id': match.group(1).strip(),
                    'flags': match.group(2).strip(),
                    'name': match.group(3).strip(),
                    'user': match.group(4).strip(),
                    'mtu': match.group(5).strip(),
                    'client_address': match.group(6).strip(),
                    'status': 'running' if 'R' in match.group(2) else 'disabled'
                }
                
                # Apenas interfaces ativas
                if 'R' in interface_info['flags']:
                    interfaces.append(interface_info)
        
        return interfaces
    
    def _parse_l2tp_client_output(self, output: str) -> List[Dict[str, str]]:
        """
        Faz parse da saída do comando l2tp-client print
        
        Args:
            output: Saída do comando RouterOS
            
        Returns:
            List[Dict]: Lista de interfaces client parseadas
        """
        interfaces = []
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Buscar linhas com interfaces L2TP
            if 'l2tp-' in line.lower():
                # Extrair nome da interface
                parts = line.split()
                for part in parts:
                    if part.startswith('l2tp-') or 'l2tp-' in part:
                        interface_name = part.strip('<>')
                        
                        interface_info = {
                            'name': interface_name,
                            'type': 'client'
                        }
                        
                        interfaces.append(interface_info)
                        break
        
        return interfaces
    
    def get_interface_details(self, interface_name: str) -> Optional[Dict[str, str]]:
        """
        Obtém detalhes específicos de uma interface
        
        Args:
            interface_name: Nome da interface
            
        Returns:
            Dict: Detalhes da interface ou None se não encontrada
        """
        if not self.connection.is_connected():
            logger.error("❌ Conexão não estabelecida")
            return None
        
        try:
            # Buscar na lista de interfaces L2TP Server
            server_interfaces = self.list_l2tp_server_interfaces()
            for interface in server_interfaces:
                if interface['name'] == interface_name:
                    return interface
            
            # Buscar na lista de interfaces L2TP Client
            client_interfaces = self.list_l2tp_client_interfaces()
            for interface in client_interfaces:
                if interface['name'] == interface_name:
                    return interface
            
            logger.warning(f"⚠️  Interface {interface_name} não encontrada")
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter detalhes da interface {interface_name}: {e}")
            return None
    
    def check_interface_exists(self, interface_name: str) -> bool:
        """
        Verifica se uma interface existe
        
        Args:
            interface_name: Nome da interface
            
        Returns:
            bool: True se a interface existe, False caso contrário
        """
        return self.get_interface_details(interface_name) is not None 