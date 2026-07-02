"""
Gerador de instâncias para o Problema de Atribuição de Papéis em RSSF.
Baseado nos parâmetros descritos em Souza e Mateus (SBPO 2006).
"""

import json
import math
import random
import os



# Parâmetros físicos baseados no sensor Mica 2 (Crossbow Technology, 2005)
CAPACIDADE_BATERIA_MAH    = 2000          # mAhr
CAPACIDADE_BATERIA_MAMS   = 7.2e9         # mAms (2000 mAhr * 3600 * 1000)
CORRENTE_RADIO_LIGADO_MA  = 12            # mA (rádio em standby)
CORRENTE_ATIVACAO_MA      = 5             # mA
TEMPO_ATIVACAO_MS         = 10            # ms
CUSTO_ATIVACAO_MAMS       = CORRENTE_ATIVACAO_MA * TEMPO_ATIVACAO_MS  # 50 mAms

# Tempo de transmissão e custo de manutenção do rádio por papel (índice = papel)
TEMPO_TRANSMISSAO_MS      = [1.8, 12.0, 27.0]   # ms por papel
CUSTO_RADIO_LIGADO_MAMS   = [21.6, 136.0, 316.0] # mAms por papel




# @params:
#   - coordA (tuple): Coordenadas (x, y) do ponto A.
#   - coordB (tuple): Coordenadas (x, y) do ponto B.
# @output:
#   - float: Distância euclidiana entre os dois pontos.
def _calcularDistancia(coordA: tuple, coordB: tuple) -> float:
    return math.sqrt((coordA[0] - coordB[0])**2 + (coordA[1] - coordB[1])**2)


# @params:
#   - distancia (float): Distância euclidiana entre os dois nós.
#   - indicePapel (int): Índice do papel assumido pelo nó.
# @output:
#   - float: Custo de energia total (mAms) para transmissão.
def _calcularCustoRoteamento(distancia: float, indicePapel: int) -> float:
    """
    Calcula o custo de energia (mAms) para transmitir um pacote entre dois nós,
    dado o índice do papel e a distância entre eles.

    Custo = custo_radio_ligado + corrente_transmissao * tempo_transmissao
    A corrente de transmissão cresce linearmente com a distância.
    """
    correnteTx = CORRENTE_RADIO_LIGADO_MA + distancia * 0.5  
    custoTx    = correnteTx * TEMPO_TRANSMISSAO_MS[indicePapel]
    return CUSTO_RADIO_LIGADO_MAMS[indicePapel] + custoTx




# @params:
#   - numSensores (int): Número de sensores a serem gerados.
#   - dimensaoArea (float): Tamanho do lado da área quadrada.
#   - semente (int): Semente para o gerador de números pseudoaleatórios.
# @output:
#   - list: Lista de tuplas (x, y) com as coordenadas dos sensores.
def _gerarSensores(numSensores: int, dimensaoArea: float, semente: int) -> list:
    random.seed(semente)
    sensores = [
        (round(random.uniform(0, dimensaoArea), 4),
         round(random.uniform(0, dimensaoArea), 4))
        for _ in range(numSensores)
    ]
    return sensores


# @params:
#   - dimensaoArea (float): Tamanho do lado da área quadrada.
# @output:
#   - list: Lista de tuplas (x, y) contendo as coordenadas dos 4 sorvedouros nos cantos.
def _gerarSorvedouros(dimensaoArea: float) -> list:
    """
    Posiciona os 4 sorvedouros nas extremidades da área, conforme o artigo.
    """
    return [
        (0.0, 0.0),
        (dimensaoArea, 0.0),
        (0.0, dimensaoArea),
        (dimensaoArea, dimensaoArea)
    ]


# @params:
#   - numPontos (int): Número de pontos de demanda a serem gerados.
#   - dimensaoArea (float): Tamanho do lado da área quadrada.
# @output:
#   - list: Lista de tuplas (x, y) com as coordenadas dos pontos de demanda dispostos em grade.
def _gerarPontosDemanda(numPontos: int, dimensaoArea: float) -> list:
    
    ladoGrade = math.ceil(math.sqrt(numPontos))
    passo     = dimensaoArea / ladoGrade
    pontos    = []

    for i in range(ladoGrade):
        for j in range(ladoGrade):
            if len(pontos) >= numPontos:
                break
            x = passo * (i + 0.5)
            y = passo * (j + 0.5)
            pontos.append((round(x, 4), round(y, 4)))

    return pontos[:numPontos]


# @params:
#   - numPontos (int): Número de pontos de demanda.
#   - numPapeis (int): Quantidade de papéis possíveis.
#   - semente (int): Semente para geração pseudoaleatória.
# @output:
#   - list: Lista de índices de papéis atribuídos a cada ponto de demanda.
def _atribuirPapeisDemanda(numPontos: int, numPapeis: int, semente: int) -> list:
    """Atribui aleatoriamente um papel exigido a cada ponto de demanda."""
    random.seed(semente + 1)
    return [random.randint(0, numPapeis - 1) for _ in range(numPontos)]




# @params:
#   - sensores (list): Lista de coordenadas dos sensores.
#   - sorvedouros (list): Lista de coordenadas dos sorvedouros.
#   - pontosDemanda (list): Lista de coordenadas dos pontos de demanda.
#   - raioComunicacao (float): Raio de comunicação dos sensores.
#   - raioSensoriamento (float): Raio de sensoriamento dos sensores.
#   - numPapeis (int): Quantidade de papéis.
# @output:
#   - dict: Dicionário contendo arcosS, arcosM, arcosC e a matriz de custoRoteamento.
def _construirArcos(sensores: list, sorvedouros: list, pontosDemanda: list,
                    raioComunicacao: float, raioSensoriamento: float,
                    numPapeis: int) -> dict:
    """
    Constrói todos os subconjuntos de arcos e a matriz de custos de roteamento.

    Retorna um dicionário com:
        arcosS  : arcos sensor -> sensor (dentro do raio de comunicação)
        arcosM  : arcos sensor -> sorvedouro (dentro do raio de comunicação)
        arcosC  : arcos sensor -> ponto de demanda (dentro do raio de sensoriamento)
        custoRoteamento : dict (i, j, papel) -> custo em mAms
    """
    numSensores    = len(sensores)
    numSorvedouros = len(sorvedouros)
    numPontos      = len(pontosDemanda)

    arcosS          = []  # (sensor_i, sensor_j)
    arcosM          = []  # (sensor_i, sorvedouro_j)
    arcosC          = []  # (sensor_l, ponto_j)
    custoRoteamento = {}  # (i, j, papel) -> float

    # Arcos entre sensores
    for i in range(numSensores):
        for j in range(numSensores):
            if i == j:
                continue
            dist = _calcularDistancia(sensores[i], sensores[j])
            if dist <= raioComunicacao:
                arcosS.append((i, j))
                for p in range(numPapeis):
                    custoRoteamento[(i, j, p)] = _calcularCustoRoteamento(dist, p)

    # Arcos de sensores para sorvedouros
    for i in range(numSensores):
        for j in range(numSorvedouros):
            dist = _calcularDistancia(sensores[i], sorvedouros[j])
            if dist <= raioComunicacao:
                arcosM.append((i, j))
                for p in range(numPapeis):
                    custoRoteamento[('m', i, j, p)] = _calcularCustoRoteamento(dist, p)

    # Arcos de sensores para pontos de demanda (cobertura)
    for l in range(numSensores):
        for j in range(numPontos):
            dist = _calcularDistancia(sensores[l], pontosDemanda[j])
            if dist <= raioSensoriamento:
                arcosC.append((l, j))

    return {
        'arcosS':          arcosS,
        'arcosM':          arcosM,
        'arcosC':          arcosC,
        'custoRoteamento': custoRoteamento
    }




# @params:
#   - numSensores (int): Número de nós sensores.
#   - numPontos (int): Número de pontos de demanda.
#   - raioComunicacao (float): Raio de comunicação.
#   - raioSensoriamento (float): Raio de sensoriamento.
#   - dimensaoArea (float): Tamanho da área quadrada (lado).
#   - numPapeis (int): Quantidade de papéis.
#   - custoNaoCobertura (float): Custo de penalização por não cobertura.
#   - semente (int): Semente geradora para posições e papéis.
# @output:
#   - dict: Dicionário com todos os dados e arcos que descrevem a instância gerada.
def gerarInstancia(numSensores: int, numPontos: int, raioComunicacao: float,
                   raioSensoriamento: float, dimensaoArea: float,
                   numPapeis: int, custoNaoCobertura: float,
                   semente: int) -> dict:
    """
    Gera uma instância completa do problema e retorna um dicionário com
    todos os dados necessários para a construção do modelo de otimização.
    """
    sensores      = _gerarSensores(numSensores, dimensaoArea, semente)
    sorvedouros   = _gerarSorvedouros(dimensaoArea)
    pontosDemanda = _gerarPontosDemanda(numPontos, dimensaoArea)
    papeisDemanda = _atribuirPapeisDemanda(numPontos, numPapeis, semente)

    arcos = _construirArcos(sensores, sorvedouros, pontosDemanda,
                            raioComunicacao, raioSensoriamento, numPapeis)

    custoAtivacao = [CUSTO_ATIVACAO_MAMS] * numSensores
    energiaSensor = [CAPACIDADE_BATERIA_MAMS] * numSensores

    instancia = {
        'semente':          semente,
        'numSensores':      numSensores,
        'numSorvedouros':   len(sorvedouros),
        'numPontos':        numPontos,
        'numPapeis':        numPapeis,
        'dimensaoArea':     dimensaoArea,
        'raioComunicacao':  raioComunicacao,
        'raioSensoriamento':raioSensoriamento,
        'custoNaoCobertura':custoNaoCobertura,
        'sensores':         sensores,
        'sorvedouros':      sorvedouros,
        'pontosDemanda':    pontosDemanda,
        'papeisDemanda':    papeisDemanda,
        'arcosS':           arcos['arcosS'],
        'arcosM':           arcos['arcosM'],
        'arcosC':           arcos['arcosC'],
        'custoAtivacao':    custoAtivacao,
        'energiaSensor':    energiaSensor,
        'custoRoteamento':  {str(k): v for k, v in arcos['custoRoteamento'].items()}
    }

    return instancia


# @params:
#   - instancia (dict): Dados da instância a serem serializados.
#   - caminhoArquivo (str): Caminho do arquivo de destino (formato JSON).
# @output:
#   - None: Serializa e salva o arquivo em disco.
def salvarInstancia(instancia: dict, caminhoArquivo: str) -> None:
    """Serializa a instância em formato JSON."""
    os.makedirs(os.path.dirname(caminhoArquivo), exist_ok=True)
    with open(caminhoArquivo, 'w', encoding='utf-8') as arquivo:
        json.dump(instancia, arquivo, indent=2)


# @params:
#   - caminhoArquivo (str): Caminho do arquivo JSON da instância.
# @output:
#   - dict: Dicionário correspondente à instância, com tuplas convertidas.
def carregarInstancia(caminhoArquivo: str) -> dict:
    """Carrega uma instância previamente salva em JSON."""
    with open(caminhoArquivo, 'r', encoding='utf-8') as arquivo:
        instancia = json.load(arquivo)

    # Restaura as chaves da matriz de custoRoteamento para tuplas
    instancia['custoRoteamento'] = {
        eval(k): v for k, v in instancia['custoRoteamento'].items()
    }
    return instancia



CONJUNTOS_ARTIGO = {
    'conjunto1': {
        'numSensores':       10,
        'numPontos':        100,
        'raioComunicacao':  7.5,
        'raioSensoriamento':7.5,
        'dimensaoArea':    10.0,
        'numPapeis':          3,
        'custoNaoCobertura': 100000.0,
        'sementes':         list(range(1, 11))      # inst1 a inst10
    },
    'conjunto2': {
        'numSensores':       20,
        'numPontos':        100,
        'raioComunicacao':  5.0,
        'raioSensoriamento':5.0,
        'dimensaoArea':    10.0,
        'numPapeis':          3,
        'custoNaoCobertura': 100000.0,
        'sementes':         list(range(11, 21))     # inst11 a inst20
    },
    'conjunto3': {
        'numSensores':       36,
        'numPontos':        100,
        'raioComunicacao':  2.5,
        'raioSensoriamento':2.5,
        'dimensaoArea':    10.0,
        'numPapeis':          3,
        'custoNaoCobertura': 100000.0,
        'sementes':         list(range(21, 26))     # inst21 a inst25
    }
}


# @params:
#   - diretorioSaida (str): Diretório onde as instâncias JSON serão armazenadas (padrão: 'instancias').
# @output:
#   - None: Gera e escreve os arquivos JSON das instâncias do artigo no disco.
def gerarTodosConjuntos(diretorioSaida: str = 'instancias') -> None:
    """Gera e salva todas as 25 instâncias dos 3 conjuntos do artigo."""
    contadorInstancia = 1
    for nomeConjunto, params in CONJUNTOS_ARTIGO.items():
        sementes = params['sementes']
        for semente in sementes:
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
            nomeArquivo = f"{diretorioSaida}/inst{contadorInstancia}.json"
            salvarInstancia(instancia, nomeArquivo)
            print(f"  Gerada: inst{contadorInstancia}.json "
                  f"({nomeConjunto}, semente={semente})")
            contadorInstancia += 1