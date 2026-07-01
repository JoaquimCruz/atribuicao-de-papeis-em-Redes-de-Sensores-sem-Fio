"""
Script principal do projeto de Atribuição de Papéis em RSSF.
Orquestra a geração de instâncias, resolução do modelo e exportação dos resultados.
"""

import os
import csv
import json
import time
import argparse
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from gerador_instancias import (
    gerarInstancia,
    salvarInstancia,
    carregarInstancia,
    gerarTodosConjuntos,
    CONJUNTOS_ARTIGO
)
from modelo import construirModelo, resolverModelo, imprimirResultado


DIR_INSTANCIAS = 'instancias'
DIR_RESULTADOS = 'resultados'



# @params:
#   - instancia (dict): Dados da instância correspondente.
#   - resultado (dict): Dicionário contendo os resultados retornados pelo solver.
#   - nomeArquivo (str): Caminho onde o arquivo de imagem (.png) será salvo.
# @output:
#   - None: Gera e salva o gráfico da topologia da rede no disco.
def plotarRede(instancia: dict, resultado: dict, nomeArquivo: str) -> None:
    """
    Gera e salva uma figura com a topologia da rede, destacando sensores ativos,
    pontos cobertos/descobertos e rotas de roteamento.
    """
    fig, ax = plt.subplots(figsize=(8, 8))

    sensores      = instancia['sensores']
    sorvedouros   = instancia['sorvedouros']
    pontosDemanda = instancia['pontosDemanda']
    sensoresAtivos = set(resultado.get('sensoresAtivos', []))
    pontosDescobertos = set(resultado.get('pontosDescobertos', []))

    # Pontos de demanda
    for j, (x, y) in enumerate(pontosDemanda):
        cor = 'red' if j in pontosDescobertos else 'lightblue'
        ax.plot(x, y, 's', color=cor, markersize=4, zorder=2)

    # Sensores
    for l, (x, y) in enumerate(sensores):
        if l in sensoresAtivos:
            papel = resultado['papelSensor'].get(l, 0)
            cores = ['green', 'darkorange', 'purple']
            ax.plot(x, y, '^', color=cores[papel % len(cores)],
                    markersize=10, zorder=4)
            ax.annotate(f'S{l}\nP{papel}', (x, y),
                        textcoords='offset points', xytext=(5, 5), fontsize=7)
        else:
            ax.plot(x, y, '^', color='lightgray', markersize=8,
                    markeredgecolor='gray', zorder=3)

    # Sorvedouros
    for k, (x, y) in enumerate(sorvedouros):
        ax.plot(x, y, 'D', color='black', markersize=12, zorder=5)
        ax.annotate(f'Sink{k}', (x, y),
                    textcoords='offset points', xytext=(5, -12), fontsize=8)

    # Legenda
    legendaItens = [
        mpatches.Patch(color='green',     label='Sensor ativo (papel 0)'),
        mpatches.Patch(color='darkorange',label='Sensor ativo (papel 1)'),
        mpatches.Patch(color='purple',    label='Sensor ativo (papel 2)'),
        mpatches.Patch(color='lightgray', label='Sensor inativo'),
        mpatches.Patch(color='lightblue', label='Ponto coberto'),
        mpatches.Patch(color='red',       label='Ponto descoberto'),
        mpatches.Patch(color='black',     label='Sorvedouro'),
    ]
    ax.legend(handles=legendaItens, loc='upper right', fontsize=8)

    ax.set_xlim(-0.5, instancia['dimensaoArea'] + 0.5)
    ax.set_ylim(-0.5, instancia['dimensaoArea'] + 0.5)
    ax.set_title(f"Topologia da rede — {os.path.basename(nomeArquivo).replace('.png','')}\n"
                 f"FO={resultado['valorFO']} mAms | "
                 f"Ativos={len(sensoresAtivos)} | "
                 f"Descobertos={len(resultado['pontosDescobertos'])}",
                 fontsize=10)
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.grid(True, linestyle='--', alpha=0.4)

    os.makedirs(os.path.dirname(nomeArquivo), exist_ok=True)
    plt.tight_layout()
    plt.savefig(nomeArquivo, dpi=150)
    plt.close()
    print(f"  Figura salva: {nomeArquivo}")




# @params:
#   - listaResultados (list): Lista de dicionários contendo os resultados individuais por instância.
#   - caminhoCSV (str): Caminho onde a tabela final consolidada em CSV será escrita.
# @output:
#   - None: Escreve os resultados consolidados no disco no formato CSV.
def salvarResultadoCSV(listaResultados: list, caminhoCSV: str) -> None:
    """
    Salva os resultados de múltiplas instâncias em um arquivo CSV,
    no mesmo formato das Tabelas 2, 3 e 4 do artigo.
    """
    os.makedirs(os.path.dirname(caminhoCSV), exist_ok=True)
    campos = ['instancia', 'conjunto', 'numSensores', 'valorFO_mAms',
              'tempoExecucao_s', 'numNosAtivos', 'numPontosDescobertos',
              'gap_pct', 'status']

    with open(caminhoCSV, 'w', newline='', encoding='utf-8') as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(listaResultados)

    print(f"\nResultados salvos em: {caminhoCSV}")




# @params:
#   - nomeConjunto (str): Nome do conjunto de instâncias ('conjunto1', 'conjunto2', 'conjunto3').
#   - tempoLimite (int): Limite máximo de tempo (segundos) de otimização por instância (padrão: 3600).
#   - gerarGraficos (bool): Se True, plota e salva os gráficos de topologia da rede (padrão: True).
# @output:
#   - list: Lista contendo os dicionários de resultados consolidados de cada instância do conjunto.
def executarConjunto(nomeConjunto: str, tempoLimite: int = 3600,
                     gerarGraficos: bool = True) -> list:
    """
    Gera, resolve e registra os resultados de todas as instâncias de um conjunto.
    Retorna lista de dicionários com os resultados para exportação.
    """
    params = CONJUNTOS_ARTIGO[nomeConjunto]
    listaResultados = []
    contadorInstancia = {'conjunto1': 1, 'conjunto2': 11, 'conjunto3': 21}
    idxInicio = contadorInstancia[nomeConjunto]

    print(f"\n{'#'*60}")
    print(f"  Executando {nomeConjunto} ({len(params['sementes'])} instâncias)")
    print(f"{'#'*60}")

    for i, semente in enumerate(params['sementes']):
        idInstancia   = idxInicio + i
        nomeInstancia = f"inst{idInstancia}"

        caminhoJson = f"{DIR_INSTANCIAS}/{nomeInstancia}.json"

        # Reutiliza instância salva ou gera nova
        if os.path.exists(caminhoJson):
            instancia = carregarInstancia(caminhoJson)
        else:
            instancia = gerarInstancia(
                numSensores       = params['numSensores'],
                numPontos         = params['numPontos'],
                raioComunicacao   = params['raioComunicacao'],
                raioSensoriamento = params['raioSensoriamento'],
                dimensaoArea      = params['dimensaoArea'],
                numPapeis         = params['numPapeis'],
                custoNaoCobertura = params['custoNaoCobertura'],
                semente           = semente
            )
            salvarInstancia(instancia, caminhoJson)

        print(f"\n  [{nomeInstancia}] Construindo modelo...")
        modelo    = construirModelo(instancia, tempoLimite=tempoLimite, suprimirLog=False)

        print(f"  [{nomeInstancia}] Otimizando...")
        resultado = resolverModelo(modelo)
        imprimirResultado(resultado, nomeInstancia)

        # Gráfico da topologia
        if gerarGraficos and resultado['valorFO'] is not None:
            caminhoPng = f"{DIR_RESULTADOS}/graficos/{nomeInstancia}.png"
            plotarRede(instancia, resultado, caminhoPng)

        # Salva resultado individual em JSON
        caminhoResultJson = f"{DIR_RESULTADOS}/{nomeInstancia}_resultado.json"
        os.makedirs(DIR_RESULTADOS, exist_ok=True)
        with open(caminhoResultJson, 'w', encoding='utf-8') as arq:
            json.dump(resultado, arq, indent=2)

        listaResultados.append({
            'instancia':            nomeInstancia,
            'conjunto':             nomeConjunto,
            'numSensores':          params['numSensores'],
            'valorFO_mAms':         resultado['valorFO'],
            'tempoExecucao_s':      resultado['tempoExecucao'],
            'numNosAtivos':         len(resultado['sensoresAtivos']),
            'numPontosDescobertos': len(resultado['pontosDescobertos']),
            'gap_pct':              resultado['gap'],
            'status':               resultado['status']
        })

    return listaResultados




# @params:
#   Nenhum (usa os argumentos passados via linha de comando).
# @output:
#   - argparse.Namespace: Objeto contendo os argumentos parseados.
def _parsearArgumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Resolve o Problema de Atribuição de Papéis em RSSF via Gurobi.'
    )
    parser.add_argument(
        '--conjuntos', nargs='+',
        choices=['conjunto1', 'conjunto2', 'conjunto3', 'todos'],
        default=['todos'],
        help='Conjuntos de instâncias a executar (padrão: todos)'
    )
    parser.add_argument(
        '--tempoLimite', type=int, default=3600,
        help='Tempo máximo de otimização por instância em segundos (padrão: 3600)'
    )
    parser.add_argument(
        '--semGraficos', action='store_true',
        help='Desativa a geração de gráficos de topologia'
    )
    parser.add_argument(
        '--apenasGerar', action='store_true',
        help='Apenas gera e salva as instâncias, sem otimizar'
    )
    return parser.parse_args()


# @params:
#   Nenhum.
# @output:
#   - None: Executa a orquestração principal (parsing, geração/carregamento, otimização e consolidação).
def main() -> None:
    args = _parsearArgumentos()

    os.makedirs(DIR_INSTANCIAS, exist_ok=True)
    os.makedirs(DIR_RESULTADOS, exist_ok=True)

    # Modo apenas geração de instâncias
    if args.apenasGerar:
        print("Gerando todas as instâncias...")
        gerarTodosConjuntos(DIR_INSTANCIAS)
        print("Concluído.")
        return

    # Define quais conjuntos executar
    conjuntosAlvo = (
        ['conjunto1', 'conjunto2', 'conjunto3']
        if 'todos' in args.conjuntos
        else args.conjuntos
    )

    gerarGraficos = not args.semGraficos
    todosResultados = []

    inicioTotal = time.time()

    for nomeConjunto in conjuntosAlvo:
        resultadosConjunto = executarConjunto(
            nomeConjunto  = nomeConjunto,
            tempoLimite   = args.tempoLimite,
            gerarGraficos = gerarGraficos
        )
        todosResultados.extend(resultadosConjunto)

    # Exporta tabela consolidada
    salvarResultadoCSV(
        todosResultados,
        f"{DIR_RESULTADOS}/tabela_resultados.csv"
    )

    tempoTotal = round(time.time() - inicioTotal, 2)
    print(f"\nExecução total concluída em {tempoTotal} s.")


if __name__ == '__main__':
    main()