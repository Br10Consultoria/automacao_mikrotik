#!/usr/bin/env python3
"""
Módulo de Rotas IPv6 - Mikrotik Automation
Responsável por configurar rotas IPv6
"""

import logging
import re
from typing import List, Dict, Optional, Tuple
from .mikrotik_connection import MikrotikConnection

logger = logging.getLogger(__name__)

class MikrotikRoutes:
    """Classe para gerenciar rotas IPv6 em dispositivos Mikrotik"""
    
    def __init__(self, connection: MikrotikConnection):
        self.connection = connection
    
    def add_ipv6_route(self, dst_address: str, gateway: str, distance: int = 1, 
                       check_gateway: str = "ping", comment: str = None) -> bool:
        """
        Adiciona uma rota IPv6
        
        Args:
            dst_address: Endereço de destino (ex: 2804:385c:8700::14/126)
            gateway: Gateway da rota (ex: 2804:385c:8700::12)
            distance: Distância da rota (padrão: 1)
            check_gateway: Método de verificação do gateway (padrão: "ping")
            comment: Comentário opcional
            
        Returns:
            bool: True se configurado com sucesso, False caso contrário
        """
        if not self.connection.is_connected():
            logger.error("❌ Conexão não estabelecida")
            return False
        
        try:
            # Verificar se a rota já existe
            if self._route_exists(dst_address, gateway):
                logger.warning(f"⚠️  Rota para {dst_address} via {gateway} já existe")
                return True
            
            # Construir comando
            command = f"/ipv6 route add dst-address={dst_address} gateway={gateway} distance={distance}"
            
            if check_gateway:
                command += f" check-gateway={check_gateway}"
            
            if comment:
                command += f" comment=\"{comment}\""
            
            # Executar comando
            output = self.connection.execute_command(command)
            
            # Verificar se houve erro
            if output and ("syntax error" in output.lower() or "failure" in output.lower()):
                logger.error(f"❌ Erro ao adicionar rota {dst_address} via {gateway}: {output}")
                return False
            
            logger.info(f"✅ Rota IPv6 {dst_address} via {gateway} adicionada")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar rota {dst_address} via {gateway}: {e}")
            return False
    
    def remove_ipv6_route(self, dst_address: str, gateway: str = None) -> bool:
        """
        Remove uma rota IPv6
        
        Args:
            dst_address: Endereço de destino
            gateway: Gateway específico (opcional)
            
        Returns:
            bool: True se removido com sucesso, False caso contrário
        """
        if not self.connection.is_connected():
            logger.error("❌ Conexão não estabelecida")
            return False
        
        try:
            # Encontrar ID da rota
            route_id = self._find_route_id(dst_address, gateway)
            
            if not route_id:
                logger.warning(f"⚠️  Rota {dst_address} não encontrada")
                return True  # Já não existe
            
            # Remover rota
            command = f"/ipv6 route remove {route_id}"
            output = self.connection.execute_command(command)
            
            if output and ("syntax error" in output.lower() or "failure" in output.lower()):
                logger.error(f"❌ Erro ao remover rota {dst_address}: {output}")
                return False
            
            logger.info(f"🗑️  Rota IPv6 {dst_address} removida")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao remover rota {dst_address}: {e}")
            return False
    
    def list_ipv6_routes(self, dst_address: str = None) -> List[Dict[str, str]]:
        """
        Lista rotas IPv6 configuradas
        
        Args:
            dst_address: Filtrar por endereço de destino específico (opcional)
            
        Returns:
            List[Dict]: Lista de rotas IPv6
        """
        if not self.connection.is_connected():
            logger.error("❌ Conexão não estabelecida")
            return []
        
        try:
            # Comando para listar rotas IPv6
            command = "/ipv6 route print"
            if dst_address:
                command += f" where dst-address={dst_address}"
            
            output = self.connection.execute_command(command)
            
            if not output:
                logger.warning("⚠️  Nenhuma resposta do comando ipv6 route print")
                return []
            
            routes = self._parse_ipv6_routes(output)
            
            if dst_address:
                logger.info(f"📋 Encontradas {len(routes)} rotas para {dst_address}")
            else:
                logger.info(f"📋 Encontradas {len(routes)} rotas IPv6 total")
            
            return routes
            
        except Exception as e:
            logger.error(f"❌ Erro ao listar rotas IPv6: {e}")
            return []
    
    def _route_exists(self, dst_address: str, gateway: str) -> bool:
        """Verifica se uma rota IPv6 já existe"""
        try:
            routes = self.list_ipv6_routes()
            
            for route in routes:
                if (route.get('dst_address') == dst_address and 
                    route.get('gateway') == gateway):
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _find_route_id(self, dst_address: str, gateway: str = None) -> Optional[str]:
        """Encontra o ID de uma rota IPv6 específica"""
        try:
            routes = self.list_ipv6_routes()
            
            for route in routes:
                if route.get('dst_address') == dst_address:
                    if gateway is None or route.get('gateway') == gateway:
                        return route.get('id')
            
            return None
            
        except Exception:
            return None
    
    def _parse_ipv6_routes(self, output: str) -> List[Dict[str, str]]:
        """
        Faz parse da saída do comando ipv6 route print
        
        Args:
            output: Saída do comando RouterOS
            
        Returns:
            List[Dict]: Lista de rotas parseadas
        """
        routes = []
        lines = output.split('\n')
        
        current_route = {}
        
        for line in lines:
            line = line.strip()
            
            # Pular linhas vazias e headers
            if not line or 'Flags:' in line:
                continue
            
            # Nova entrada de rota (linha com número)
            if re.match(r'^\s*\d+', line):
                # Salvar rota anterior se existir
                if current_route:
                    routes.append(current_route)
                    current_route = {}
                
                # Parse da nova linha
                parts = line.split()
                if len(parts) >= 1:
                    current_route = {
                        'id': parts[0],
                        'flags': '',
                        'dst_address': '',
                        'gateway': '',
                        'distance': '',
                        'comment': ''
                    }
                
                # Extrair informações da linha
                if 'dst-address=' in line:
                    dst_match = re.search(r'dst-address=([^\s]+)', line)
                    if dst_match:
                        current_route['dst_address'] = dst_match.group(1)
                
                if 'gateway=' in line:
                    gw_match = re.search(r'gateway=([^\s]+)', line)
                    if gw_match:
                        current_route['gateway'] = gw_match.group(1)
                
                if 'distance=' in line:
                    dist_match = re.search(r'distance=([^\s]+)', line)
                    if dist_match:
                        current_route['distance'] = dist_match.group(1)
                
                if 'comment=' in line:
                    comment_match = re.search(r'comment=([^\s]+)', line)
                    if comment_match:
                        current_route['comment'] = comment_match.group(1).strip('"')
            
            # Linha de continuação
            elif line and current_route:
                # Procurar por informações de rota que podem estar em linhas separadas
                if 'dst-address=' in line:
                    dst_match = re.search(r'dst-address=([^\s]+)', line)
                    if dst_match:
                        current_route['dst_address'] = dst_match.group(1)
                
                if 'gateway=' in line:
                    gw_match = re.search(r'gateway=([^\s]+)', line)
                    if gw_match:
                        current_route['gateway'] = gw_match.group(1)
        
        # Adicionar última rota
        if current_route:
            routes.append(current_route)
        
        return routes
    
    def bulk_configure_routes(self, route_configs: List[Dict]) -> Tuple[int, int]:
        """
        Configura múltiplas rotas IPv6
        
        Args:
            route_configs: Lista de configurações de rotas
                [{'dst_address': '2804:385c:8700::14/126', 'gateway': '2804:385c:8700::12', 'comment': 'CAETITE'}]
        
        Returns:
            Tuple[int, int]: (sucessos, falhas)
        """
        success_count = 0
        failure_count = 0
        
        for config in route_configs:
            dst_address = config.get('dst_address')
            gateway = config.get('gateway')
            distance = config.get('distance', 1)
            check_gateway = config.get('check_gateway', 'ping')
            comment = config.get('comment')
            
            if not dst_address or not gateway:
                logger.error(f"❌ Configuração de rota inválida: {config}")
                failure_count += 1
                continue
            
            success = self.add_ipv6_route(dst_address, gateway, distance, check_gateway, comment)
            
            if success:
                success_count += 1
            else:
                failure_count += 1
        
        logger.info(f"📊 Configuração de rotas em lote: {success_count} sucessos, {failure_count} falhas")
        return success_count, failure_count 