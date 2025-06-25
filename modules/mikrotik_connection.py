#!/usr/bin/env python3
"""
Módulo de Conexão - Mikrotik Automation
Responsável por gerenciar conexões SSH e Telnet com dispositivos Mikrotik
"""

import os
import time
import socket
import telnetlib
import paramiko
import logging
from typing import Union, Optional

logger = logging.getLogger(__name__)

class MikrotikConnection:
    """Classe para gerenciar conexões com dispositivos Mikrotik"""
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.connection = None
        self.connection_type = None
        self.host = None
        
    def connect_ssh(self, host: str, port: int = 22, timeout: int = 30) -> bool:
        """
        Conecta ao dispositivo via SSH
        
        Args:
            host: IP ou hostname do dispositivo
            port: Porta SSH (padrão: 22)
            timeout: Timeout da conexão em segundos
            
        Returns:
            bool: True se conectou com sucesso, False caso contrário
        """
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                hostname=host,
                port=port,
                username=self.username,
                password=self.password,
                timeout=timeout,
                look_for_keys=False,
                allow_agent=False,
                banner_timeout=30
            )
            
            self.connection = ssh
            self.connection_type = 'ssh'
            self.host = host
            
            logger.info(f"✅ Conectado via SSH a {host}")
            return True
            
        except paramiko.AuthenticationException:
            logger.error(f"❌ Erro de autenticação SSH para {host}")
            return False
        except paramiko.SSHException as e:
            logger.error(f"❌ Erro SSH para {host}: {e}")
            return False
        except socket.timeout:
            logger.error(f"❌ Timeout na conexão SSH para {host}")
            return False
        except Exception as e:
            logger.error(f"❌ Erro inesperado SSH para {host}: {e}")
            return False
    
    def connect_telnet(self, host: str, port: int = 23, timeout: int = 30) -> bool:
        """
        Conecta ao dispositivo via Telnet
        
        Args:
            host: IP ou hostname do dispositivo
            port: Porta Telnet (padrão: 23)
            timeout: Timeout da conexão em segundos
            
        Returns:
            bool: True se conectou com sucesso, False caso contrário
        """
        try:
            tn = telnetlib.Telnet(host, port, timeout)
            
            # Aguardar prompt de login
            tn.read_until(b"Login: ", timeout)
            tn.write(self.username.encode('ascii') + b"\n")
            
            # Aguardar prompt de senha
            tn.read_until(b"Password: ", timeout)
            tn.write(self.password.encode('ascii') + b"\n")
            
            # Verificar se logou com sucesso (aguardar prompt)
            response = tn.read_until(b">", timeout).decode('utf-8', errors='ignore')
            
            if ">" in response or "]" in response:
                self.connection = tn
                self.connection_type = 'telnet'
                self.host = host
                
                logger.info(f"✅ Conectado via Telnet a {host}")
                return True
            else:
                logger.error(f"❌ Falha na autenticação Telnet para {host}")
                tn.close()
                return False
                
        except socket.timeout:
            logger.error(f"❌ Timeout na conexão Telnet para {host}")
            return False
        except Exception as e:
            logger.error(f"❌ Erro Telnet para {host}: {e}")
            return False
    
    def execute_command(self, command: str, timeout: int = 30) -> Optional[str]:
        """
        Executa um comando no dispositivo conectado
        
        Args:
            command: Comando RouterOS a ser executado
            timeout: Timeout do comando em segundos
            
        Returns:
            str: Saída do comando ou None em caso de erro
        """
        if not self.connection:
            logger.error("❌ Nenhuma conexão ativa")
            return None
        
        try:
            if self.connection_type == 'ssh':
                return self._execute_ssh_command(command, timeout)
            else:
                return self._execute_telnet_command(command, timeout)
                
        except Exception as e:
            logger.error(f"❌ Erro ao executar comando '{command}': {e}")
            return None
    
    def _execute_ssh_command(self, command: str, timeout: int) -> str:
        """Executa comando via SSH"""
        stdin, stdout, stderr = self.connection.exec_command(command, timeout=timeout)
        
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')
        
        if error and "syntax error" in error.lower():
            logger.warning(f"⚠️  Aviso no comando '{command}': {error}")
        
        return output
    
    def _execute_telnet_command(self, command: str, timeout: int) -> str:
        """Executa comando via Telnet"""
        # Limpar buffer
        try:
            self.connection.read_very_eager()
        except:
            pass
        
        # Enviar comando
        self.connection.write(command.encode('ascii') + b"\n")
        time.sleep(0.5)  # Aguardar processamento
        
        # Ler resposta até prompt
        response = self.connection.read_until(b">", timeout).decode('utf-8', errors='ignore')
        
        # Limpar o comando enviado da resposta
        lines = response.split('\n')
        if len(lines) > 1:
            response = '\n'.join(lines[1:])
        
        return response
    
    def disconnect(self):
        """Fecha a conexão ativa"""
        if self.connection:
            try:
                self.connection.close()
                logger.info(f"🔌 Desconectado de {self.host}")
            except:
                pass
            finally:
                self.connection = None
                self.connection_type = None
                self.host = None
    
    def is_connected(self) -> bool:
        """Verifica se há uma conexão ativa"""
        return self.connection is not None
    
    def get_connection_info(self) -> dict:
        """Retorna informações da conexão atual"""
        return {
            'host': self.host,
            'type': self.connection_type,
            'connected': self.is_connected()
        } 