#!/usr/bin/env python3
"""
Agente Autônomo com Ollama
Um agente que pode executar ações e usar ferramentas
"""

import requests
import json
import subprocess
import os
from datetime import datetime

class AgenteAutonomo:
    def __init__(self, modelo="llama3.2"):
        self.modelo = modelo
        self.url = "http://localhost:11434/api/generate"
        self.historico_acoes = []
        
        # Ferramentas disponíveis para o agente
        self.ferramentas = {
            "listar_arquivos": self.listar_arquivos,
            "criar_arquivo": self.criar_arquivo,
            "ler_arquivo": self.ler_arquivo,
            "executar_comando": self.executar_comando,
            "criar_pasta": self.criar_pasta,
            "data_hora": self.obter_data_hora
        }
    
    def listar_arquivos(self, caminho="."):
        """Lista arquivos em um diretório"""
        try:
            arquivos = os.listdir(caminho)
            return f"Arquivos em {caminho}: {', '.join(arquivos)}"
        except Exception as e:
            return f"Erro ao listar arquivos: {e}"
    
    def criar_arquivo(self, nome, conteudo):
        """Cria um arquivo com conteúdo"""
        try:
            with open(nome, 'w') as f:
                f.write(conteudo)
            return f"Arquivo '{nome}' criado com sucesso"
        except Exception as e:
            return f"Erro ao criar arquivo: {e}"
    
    def ler_arquivo(self, nome):
        """Lê conteúdo de um arquivo"""
        try:
            with open(nome, 'r') as f:
                conteudo = f.read()
            return f"Conteúdo de '{nome}':\n{conteudo}"
        except Exception as e:
            return f"Erro ao ler arquivo: {e}"
    
    def executar_comando(self, comando):
        """Executa um comando shell (use com cuidado!)"""
        # Lista de comandos permitidos (segurança básica)
        comandos_seguros = ['ls', 'pwd', 'date', 'whoami', 'echo']
        
        cmd_base = comando.split()[0]
        if cmd_base not in comandos_seguros:
            return f"Comando '{cmd_base}' não permitido por segurança"
        
        try:
            resultado = subprocess.run(
                comando, 
                shell=True, 
                capture_output=True, 
                text=True,
                timeout=5
            )
            return f"Resultado:\n{resultado.stdout}"
        except Exception as e:
            return f"Erro ao executar comando: {e}"
    
    def criar_pasta(self, nome):
        """Cria uma pasta"""
        try:
            os.makedirs(nome, exist_ok=True)
            return f"Pasta '{nome}' criada com sucesso"
        except Exception as e:
            return f"Erro ao criar pasta: {e}"
    
    def obter_data_hora(self):
        """Retorna data e hora atual"""
        agora = datetime.now()
        return f"Data e hora atual: {agora.strftime('%d/%m/%Y %H:%M:%S')}"
    
    def descrever_ferramentas(self):
        """Retorna descrição das ferramentas disponíveis"""
        descricao = """
Ferramentas disponíveis:

1. listar_arquivos(caminho) - Lista arquivos em um diretório
   Exemplo: listar_arquivos("/tmp")

2. criar_arquivo(nome, conteudo) - Cria um arquivo
   Exemplo: criar_arquivo("teste.txt", "Olá mundo")

3. ler_arquivo(nome) - Lê conteúdo de um arquivo
   Exemplo: ler_arquivo("teste.txt")

4. executar_comando(comando) - Executa comando shell seguro
   Exemplo: executar_comando("ls -la")

5. criar_pasta(nome) - Cria uma pasta
   Exemplo: criar_pasta("minha_pasta")

6. data_hora() - Retorna data e hora atual
   Exemplo: data_hora()
"""
        return descricao
    
    def executar_ferramenta(self, nome_ferramenta, parametros):
        """Executa uma ferramenta"""
        if nome_ferramenta not in self.ferramentas:
            return f"Ferramenta '{nome_ferramenta}' não existe"
        
        try:
            ferramenta = self.ferramentas[nome_ferramenta]
            
            # Executa com ou sem parâmetros
            if parametros:
                if isinstance(parametros, list):
                    resultado = ferramenta(*parametros)
                else:
                    resultado = ferramenta(parametros)
            else:
                resultado = ferramenta()
            
            # Registra ação
            self.historico_acoes.append({
                "ferramenta": nome_ferramenta,
                "parametros": parametros,
                "resultado": resultado,
                "timestamp": datetime.now().isoformat()
            })
            
            return resultado
        except Exception as e:
            return f"Erro ao executar ferramenta: {e}"
    
    def pensar(self, tarefa):
        """Agente pensa sobre a tarefa e decide próximos passos"""
        
        prompt = f"""Você é um agente autônomo que pode executar ações usando ferramentas.

{self.descrever_ferramentas()}

Tarefa: {tarefa}

Pense sobre como resolver esta tarefa passo a passo.
Para cada passo, você deve:
1. Explicar o que vai fazer
2. Escolher uma ferramenta
3. Especificar os parâmetros

Responda APENAS no seguinte formato JSON:
{{
  "raciocinio": "Sua explicação do que vai fazer",
  "ferramenta": "nome_da_ferramenta",
  "parametros": ["param1", "param2"]
}}

Se a tarefa estiver completa, responda:
{{
  "raciocinio": "Tarefa concluída",
  "ferramenta": "CONCLUIDO",
  "parametros": []
}}

Resposta:"""
        
        payload = {
            "model": self.modelo,
            "prompt": prompt,
            "stream": False
        }
        
        try:
            response = requests.post(self.url, json=payload)
            resultado = response.json()
            resposta_texto = resultado['response']
            
            # Tenta extrair JSON da resposta
            # O modelo pode adicionar texto antes/depois
            inicio = resposta_texto.find('{')
            fim = resposta_texto.rfind('}') + 1
            
            if inicio != -1 and fim > inicio:
                json_str = resposta_texto[inicio:fim]
                return json.loads(json_str)
            else:
                return {
                    "raciocinio": "Não consegui gerar resposta válida",
                    "ferramenta": "ERRO",
                    "parametros": []
                }
        except Exception as e:
            return {
                "raciocinio": f"Erro ao pensar: {e}",
                "ferramenta": "ERRO",
                "parametros": []
            }
    
    def executar_tarefa(self, tarefa, max_passos=5):
        """Executa uma tarefa completa"""
        print(f"\n🎯 Tarefa: {tarefa}")
        print("=" * 60 + "\n")
        
        for passo in range(max_passos):
            print(f"📍 Passo {passo + 1}:")
            
            # Agente pensa sobre próxima ação
            decisao = self.pensar(tarefa)
            
            print(f"💭 Raciocínio: {decisao['raciocinio']}")
            
            # Verifica se terminou
            if decisao['ferramenta'] == 'CONCLUIDO':
                print("\n✅ Tarefa concluída!\n")
                break
            
            if decisao['ferramenta'] == 'ERRO':
                print("\n❌ Erro no agente\n")
                break
            
            # Executa ferramenta
            print(f"🔧 Ferramenta: {decisao['ferramenta']}")
            print(f"📋 Parâmetros: {decisao['parametros']}")
            
            resultado = self.executar_ferramenta(
                decisao['ferramenta'],
                decisao['parametros']
            )
            
            print(f"📤 Resultado: {resultado}\n")
            
            # Atualiza tarefa com resultado
            tarefa = f"{tarefa}\n\nÚltima ação: {decisao['ferramenta']}\nResultado: {resultado}"
        
        return self.historico_acoes
    
    def mostrar_historico(self):
        """Mostra histórico de ações"""
        if not self.historico_acoes:
            print("Nenhuma ação executada ainda")
            return
        
        print("\n📜 Histórico de Ações:")
        print("=" * 60)
        
        for i, acao in enumerate(self.historico_acoes, 1):
            print(f"\n{i}. {acao['ferramenta']}")
            print(f"   Parâmetros: {acao['parametros']}")
            print(f"   Resultado: {acao['resultado'][:100]}...")
            print(f"   Timestamp: {acao['timestamp']}")


def exemplo_tarefas():
    """Exemplos de tarefas que o agente pode executar"""
    
    agente = AgenteAutonomo()
    
    print("=" * 60)
    print("  Agente Autônomo com Ollama")
    print("=" * 60)
    
    # Tarefa 1: Organizar arquivos
    print("\n" + "=" * 60)
    print("EXEMPLO 1: Verificar data e hora")
    print("=" * 60)
    
    agente.executar_tarefa(
        "Me diga que horas são agora",
        max_passos=2
    )
    
    # Tarefa 2: Criar estrutura de projeto
    print("\n" + "=" * 60)
    print("EXEMPLO 2: Criar estrutura de projeto")
    print("=" * 60)
    
    agente.executar_tarefa(
        "Crie uma pasta chamada 'meu_projeto' e dentro dela crie um arquivo 'README.md' com o texto 'Meu Projeto'",
        max_passos=5
    )
    
    # Mostra histórico
    agente.mostrar_historico()


def modo_interativo():
    """Modo interativo com o agente"""
    agente = AgenteAutonomo()
    
    print("\n" + "=" * 60)
    print("  Modo Interativo - Agente Autônomo")
    print("=" * 60)
    print("\nDescreva uma tarefa e o agente tentará executá-la.")
    print("Digite 'sair' para encerrar.\n")
    
    while True:
        tarefa = input("🎯 Tarefa: ").strip()
        
        if tarefa.lower() == 'sair':
            print("Até logo! 👋")
            break
        
        if not tarefa:
            continue
        
        agente.executar_tarefa(tarefa, max_passos=5)


if __name__ == "__main__":
    import sys
    
    try:
        requests.get("http://localhost:11434/api/tags")
        
        if len(sys.argv) > 1 and sys.argv[1] == "--interativo":
            modo_interativo()
        else:
            exemplo_tarefas()
            print("\n💡 Execute com --interativo para modo interativo")
    
    except requests.exceptions.ConnectionError:
        print("❌ Ollama não está rodando!")
        print("Inicie com: ollama serve")
