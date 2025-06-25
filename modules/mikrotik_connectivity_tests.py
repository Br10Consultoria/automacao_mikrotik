#!/usr/bin/env python3
"""
Módulo de Testes de Conectividade - Mikrotik Automation
Responsável por executar testes de ping, MTU e conectividade IPv6
"""

import logging
import re
import time
from typing import Dict, List, Optional, Tuple
from .mikrotik_connection import MikrotikConnection

logger = logging.getLogger(__name__)

class MikrotikConnectivityTests:
    """Classe para executar testes de conectividade em dispositivos Mikrotik"""
    
    def __init__(self, connection: MikrotikConnection):
        self.connection = connection
    
    def test_ipv6_connectivity(self, gateway: str, test_targets: List[str] = None) -> Dict[str, Dict]:
        """
        Executa testes completos de conectividade IPv6
        
        Args:
            gateway: IP IPv6 do gateway para teste
            test_targets: Lista de IPs para teste (padrão: Google DNS)
            
        Returns:
            Dict: Resultados dos testes
        """
        if not self.connection.is_connected():
            logger.error("❌ Conexão não estabelecida")
            return {}
        
        if not test_targets:
            test_targets = ["2001:4860:4860::8888"]  # Google DNS IPv6
        
        results = {
            'gateway_test': {},
            'external_tests': {},
            'mtu_test': {},
            'summary': {}
        }
        
        logger.info("🧪 Iniciando testes de conectividade IPv6...")
        
        # 1. Teste de ping para gateway
        logger.info(f"🎯 Testando conectividade com gateway {gateway}")
        results['gateway_test'] = self._ping_ipv6(gateway)
        
        # 2. Testes de ping para alvos externos
        for target in test_targets:
            logger.info(f"🌐 Testando conectividade externa para {target}")
            results['external_tests'][target] = self._ping_ipv6(target)
        
        # 3. Teste de MTU
        logger.info("📏 Testando MTU IPv6")
        results['mtu_test'] = self._test_mtu_ipv6(gateway)
        
        # 4. Gerar resumo
        results['summary'] = self._generate_connectivity_summary(results)
        
        # 5. Log dos resultados
        self._log_test_results(results)
        
        return results
    
    def _ping_ipv6(self, target: str, count: int = 4) -> Dict[str, any]:
        """
        Executa ping IPv6 para um alvo específico
        
        Args:
            target: IP IPv6 de destino
            count: Número de pings
            
        Returns:
            Dict: Resultados do ping
        """
        try:
            command = f"/ping address={target} count={count} ipv6=yes"
            output = self.connection.execute_command(command)
            
            if not output:
                return {
                    'target': target,
                    'success': False,
                    'error': 'Nenhuma resposta do comando ping'
                }
            
            return self._parse_ping_output(output, target)
            
        except Exception as e:
            logger.error(f"❌ Erro no ping para {target}: {e}")
            return {
                'target': target,
                'success': False,
                'error': str(e)
            }
    
    def _parse_ping_output(self, output: str, target: str) -> Dict[str, any]:
        """
        Faz parse da saída do comando ping
        
        Args:
            output: Saída do comando ping
            target: IP de destino
            
        Returns:
            Dict: Resultados parseados
        """
        lines = output.split('\n')
        
        # Inicializar resultados
        result = {
            'target': target,
            'success': False,
            'packets_sent': 0,
            'packets_received': 0,
            'packet_loss_percent': 100,
            'avg_time_ms': 0,
            'min_time_ms': 0,
            'max_time_ms': 0,
            'times': [],
            'raw_output': output
        }
        
        # Parse das linhas individuais de ping
        ping_times = []
        for line in lines:
            # Buscar padrão: 64 bytes from 2001:4860:4860::8888: icmp_seq=1 ttl=119 time=15ms
            if 'time=' in line and 'bytes from' in line:
                time_match = re.search(r'time=(\d+(?:\.\d+)?)ms', line)
                if time_match:
                    ping_times.append(float(time_match.group(1)))
        
        # Parse do resumo final
        for line in lines:
            # Buscar padrão: 4 packets transmitted, 4 received, 0% packet loss
            if 'packets transmitted' in line:
                stats_match = re.search(r'(\d+) packets transmitted, (\d+) received, (\d+)% packet loss', line)
                if stats_match:
                    result['packets_sent'] = int(stats_match.group(1))
                    result['packets_received'] = int(stats_match.group(2))
                    result['packet_loss_percent'] = int(stats_match.group(3))
                    result['success'] = result['packet_loss_percent'] < 100
            
            # Buscar padrão: round-trip min/avg/max = 15/15/16 ms
            if 'round-trip' in line and 'min/avg/max' in line:
                time_stats = re.search(r'min/avg/max = (\d+(?:\.\d+)?)/(\d+(?:\.\d+)?)/(\d+(?:\.\d+)?) ms', line)
                if time_stats:
                    result['min_time_ms'] = float(time_stats.group(1))
                    result['avg_time_ms'] = float(time_stats.group(2))
                    result['max_time_ms'] = float(time_stats.group(3))
        
        # Se não encontrou resumo, usar tempos individuais
        if ping_times and result['avg_time_ms'] == 0:
            result['times'] = ping_times
            result['min_time_ms'] = min(ping_times)
            result['max_time_ms'] = max(ping_times)
            result['avg_time_ms'] = sum(ping_times) / len(ping_times)
            result['packets_received'] = len(ping_times)
            result['packet_loss_percent'] = max(0, 100 - (len(ping_times) / result.get('packets_sent', 4) * 100))
            result['success'] = len(ping_times) > 0
        
        return result
    
    def _test_mtu_ipv6(self, target: str) -> Dict[str, any]:
        """
        Testa MTU IPv6 usando ping com tamanhos crescentes
        
        Args:
            target: IP IPv6 de destino
            
        Returns:
            Dict: Resultados do teste de MTU
        """
        mtu_sizes = [1280, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000]
        max_working_mtu = 0
        
        logger.info("📏 Testando MTU IPv6...")
        
        for size in mtu_sizes:
            try:
                # Ping com tamanho específico (sem fragmentação)
                command = f"/ping address={target} count=1 size={size} do-not-fragment=yes ipv6=yes"
                output = self.connection.execute_command(command)
                
                if output and ('time=' in output or 'received' in output):
                    max_working_mtu = size
                    logger.info(f"✅ MTU {size} bytes: OK")
                else:
                    logger.info(f"❌ MTU {size} bytes: FALHOU")
                    break
                    
            except Exception as e:
                logger.error(f"❌ Erro testando MTU {size}: {e}")
                break
        
        return {
            'max_mtu': max_working_mtu,
            'recommended_mtu': max_working_mtu - 20 if max_working_mtu > 20 else max_working_mtu,
            'tested_sizes': mtu_sizes[:mtu_sizes.index(max_working_mtu) + 1] if max_working_mtu > 0 else []
        }
    
    def _generate_connectivity_summary(self, results: Dict) -> Dict[str, any]:
        """
        Gera resumo dos testes de conectividade
        
        Args:
            results: Resultados dos testes
            
        Returns:
            Dict: Resumo dos testes
        """
        gateway_ok = results.get('gateway_test', {}).get('success', False)
        
        external_tests = results.get('external_tests', {})
        external_ok = any(test.get('success', False) for test in external_tests.values())
        
        mtu_ok = results.get('mtu_test', {}).get('max_mtu', 0) >= 1280
        
        overall_status = "✅ SUCESSO" if (gateway_ok and external_ok and mtu_ok) else "❌ PROBLEMAS"
        
        return {
            'overall_status': overall_status,
            'gateway_reachable': gateway_ok,
            'external_reachable': external_ok,
            'mtu_adequate': mtu_ok,
            'max_mtu': results.get('mtu_test', {}).get('max_mtu', 0)
        }
    
    def _log_test_results(self, results: Dict):
        """
        Registra resultados dos testes no log
        
        Args:
            results: Resultados dos testes
        """
        logger.info("📊 RESULTADOS DOS TESTES DE CONECTIVIDADE")
        logger.info("=" * 50)
        
        # Gateway
        gateway_test = results.get('gateway_test', {})
        if gateway_test:
            status = "✅ OK" if gateway_test.get('success') else "❌ FALHA"
            loss = gateway_test.get('packet_loss_percent', 100)
            avg_time = gateway_test.get('avg_time_ms', 0)
            logger.info(f"🎯 Gateway: {status} | Perda: {loss}% | Latência: {avg_time:.1f}ms")
        
        # Testes externos
        external_tests = results.get('external_tests', {})
        for target, test in external_tests.items():
            status = "✅ OK" if test.get('success') else "❌ FALHA"
            loss = test.get('packet_loss_percent', 100)
            avg_time = test.get('avg_time_ms', 0)
            logger.info(f"🌐 {target}: {status} | Perda: {loss}% | Latência: {avg_time:.1f}ms")
        
        # MTU
        mtu_test = results.get('mtu_test', {})
        max_mtu = mtu_test.get('max_mtu', 0)
        logger.info(f"📏 MTU Máximo: {max_mtu} bytes")
        
        # Resumo
        summary = results.get('summary', {})
        logger.info(f"📊 Status Geral: {summary.get('overall_status', 'DESCONHECIDO')}")
        logger.info("=" * 50) 