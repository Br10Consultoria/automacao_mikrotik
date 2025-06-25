#!/usr/bin/env python3
"""
Módulo de Configuração IPv6 - Mikrotik Automation
Responsável por configurar endereços IPv6 em interfaces
"""

import logging
import re
from typing import List, Dict, Optional, Tuple
from .mikrotik_connection import MikrotikConnection

logger = logging.getLogger(__name__)

class MikrotikIPv6Config:
    """Classe para configurar endereços IPv6 em dispositivos Mikrotik"""
    
    def __init__(self, connection: MikrotikConnection):
        self.connection = connection
    
    def add_ipv6_address(self, interface: str, address: str, advertise: bool = False, comment: str = None) -> bool:
        """
        Adiciona endereço IPv6 a uma interface
        
        Args:
            interface: Nome da interface
            address: Endereço IPv6 (ex: 2804:385c:8700::11/126)
            advertise: Se deve anunciar o endereço (padrão: False)
            comment: Comentário opcional
            
        Returns:
            bool: True se configurado com sucesso, False caso contrário
        """
        if not self.connection.is_connected():
            logger.error("❌ Conexão não estabelecida")
            return False
        
        try:
            # Verificar se o endereço já existe
            if self._address_exists(interface, address):
                logger.warning(f"⚠️  Endereço {address} já existe na interface {interface}")
                return True
            
            # Construir comando
            advertise_flag = "yes" if advertise else "no"
            command = f"/ipv6 address add address={address} interface={interface} advertise={advertise_flag}"
            
            if comment:
                command += f" comment=\"{comment}\""
            
            # Executar comando
            output = self.connection.execute_command(command)
            
            # Verificar se houve erro
            if output and ("syntax error" in output.lower() or "failure" in output.lower()):
                logger.error(f"❌ Erro ao adicionar IPv6 {address} na interface {interface}: {output}")
                return False
            
            logger.info(f"✅ IPv6 {address} adicionado na interface {interface}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar IPv6 {address} na interface {interface}: {e}")
            return False
    
    def remove_ipv6_address(self, interface: str, address: str) -> bool:
        """
        Remove endereço IPv6 de uma interface
        
        Args:
            interface: Nome da interface
            address: Endereço IPv6 a ser removido
            
        Returns:
            bool: True se removido com sucesso, False caso contrário
        """
        if not self.connection.is_connected():
            logger.error("❌ Conexão não estabelecida")
            return False
        
        try:
            # Encontrar ID do endereço
            address_id = self._find_address_id(interface, address)
            
            if not address_id:
                logger.warning(f"⚠️  Endereço {address} não encontrado na interface {interface}")
                return True  # Já não existe
            
            # Remover endereço
            command = f"/ipv6 address remove {address_id}"
            output = self.connection.execute_command(command)
            
            if output and ("syntax error" in output.lower() or "failure" in output.lower()):
                logger.error(f"❌ Erro ao remover IPv6 {address}: {output}")
                return False
            
            logger.info(f"🗑️  IPv6 {address} removido da interface {interface}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao remover IPv6 {address} da interface {interface}: {e}")
            return False
    
    def list_ipv6_addresses(self, interface: str = None) -> List[Dict[str, str]]:
        """
        Lista endereços IPv6 configurados
        
        Args:
            interface: Interface específica (opcional)
            
        Returns:
            List[Dict]: Lista de endereços IPv6
        """
        if not self.connection.is_connected():
            logger.error("❌ Conexão não estabelecida")
            return []
        
        try:
            # Comando para listar endereços IPv6
            command = "/ipv6 address print"
            if interface:
                command += f" where interface={interface}"
            
            output = self.connection.execute_command(command)
            
            if not output:
                logger.warning("⚠️  Nenhuma resposta do comando ipv6 address print")
                return []
            
            addresses = self._parse_ipv6_addresses(output)
            
            if interface:
                logger.info(f"📋 Encontrados {len(addresses)} endereços IPv6 na interface {interface}")
            else:
                logger.info(f"📋 Encontrados {len(addresses)} endereços IPv6 total")
            
            return addresses
            
        except Exception as e:
            logger.error(f"❌ Erro ao listar endereços IPv6: {e}")
            return []
    
    def _address_exists(self, interface: str, address: str) -> bool:
        """Verifica se um endereço IPv6 já existe na interface"""
        try:
            addresses = self.list_ipv6_addresses(interface)
            
            # Normalizar endereço para comparação (remover /prefixo se necessário)
            check_address = address.split('/')[0] if '/' in address else address
            
            for addr in addresses:
                existing_address = addr.get('address', '').split('/')[0]
                if existing_address == check_address:
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _find_address_id(self, interface: str, address: str) -> Optional[str]:
        """Encontra o ID de um endereço IPv6 específico"""
        try:
            addresses = self.list_ipv6_addresses(interface)
            
            check_address = address.split('/')[0] if '/' in address else address
            
            for addr in addresses:
                existing_address = addr.get('address', '').split('/')[0]
                if existing_address == check_address:
                    return addr.get('id')
            
            return None
            
        except Exception:
            return None
    
    def _parse_ipv6_addresses(self, output: str) -> List[Dict[str, str]]:
        """
        Faz parse da saída do comando ipv6 address print
        
        Args:
            output: Saída do comando RouterOS
            
        Returns:
            List[Dict]: Lista de endereços parseados
        """
        addresses = []
        lines = output.split('\n')
        
        current_entry = {}
        
        for line in lines:
            line = line.strip()
            
            # Pular linhas vazias e headers
            if not line or 'Flags:' in line or '#' in line and 'ADDRESS' in line:
                continue
            
            # Nova entrada (linha com número)
            if re.match(r'^\s*\d+', line):
                # Salvar entrada anterior se existir
                if current_entry:
                    addresses.append(current_entry)
                    current_entry = {}
                
                # Parse da nova linha
                parts = line.split()
                
                # Verificar se é uma nova entrada ou continuação de uma existente
                if len(parts) > 1:
                    current_entry = {
                        'id': parts[0],
                        'flags': parts[1],
                        'address': parts[2],
                        'interface': parts[3],
                        'advertise': parts[4] == 'yes',
                        'comment': parts[5] if len(parts) > 5 else None
                    }
                else:
                    current_entry = {}
        
        return addresses 