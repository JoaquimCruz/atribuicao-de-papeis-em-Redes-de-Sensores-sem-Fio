"""
Modelo de Programação Linear Inteira Mista (PLIM) para o Problema de
Atribuição de Papéis em Redes de Sensores Sem Fio.
Formulação conforme Souza e Mateus (SBPO 2006), implementada com gurobipy.
"""

import time
import gurobipy as gp
from gurobipy import GRB




# @params:
#   - instancia (dict): Dicionário contendo os dados da instância.
#   - tempoLimite (int): Limite de tempo em segundos para a otimização (padrão: 3600).
#   - suprimirLog (bool): Se True, desativa logs de console do Gurobi (padrão: False).
# @output:
#   - gp.Model: Modelo Gurobi construído com variáveis, função objetivo e restrições.
def construirModelo(instancia: dict, tempoLimite: int = 3600,
                    suprimirLog: bool = False) -> gp.Model:
    """
    Constrói e retorna o modelo Gurobi a partir de uma instância do problema.

    Parâmetros
    ----------
    instancia    : dicionário gerado por gerador_instancias.gerarInstancia()
    tempoLimite  : tempo máximo de otimização em segundos (padrão: 3600)
    suprimirLog  : se True, desativa a saída do Gurobi no terminal
    """

    
    numSensores       = instancia['numSensores']
    numSorvedouros    = instancia['numSorvedouros']
    numPontos         = instancia['numPontos']
    numPapeis         = instancia['numPapeis']
    custoNaoCobertura = instancia['custoNaoCobertura']
    custoAtivacao     = instancia['custoAtivacao']     # c^p_l (mesmo para todos os papéis)
    energiaSensor     = instancia['energiaSensor']     # b_l
    papeisDemanda     = instancia['papeisDemanda']     # papel exigido por cada ponto j
    arcosS            = [tuple(a) for a in instancia['arcosS']]
    arcosM            = [tuple(a) for a in instancia['arcosM']]
    arcosC            = [tuple(a) for a in instancia['arcosC']]
    custoRoteamento   = instancia['custoRoteamento']   # d^p_ij

    # Índices dos conjuntos
    indiceSensores    = range(numSensores)
    indiceSorvedouros = range(numSorvedouros)
    indicePontos      = range(numPontos)
    indicePapeis      = range(numPapeis)

    # Subconjuntos de vizinhança para as restrições de fluxo
    # arcosEntrada[j] = arcos (i,j) em arcosS que chegam no sensor j
    arcosEntrada = {j: [(i, j) for (i, j) in arcosS if j == sensorJ]
                    for sensorJ in indiceSensores
                    for j in [sensorJ]}

    # arcosSaida[j] = arcos (j,k) em arcosS + arcosM que saem do sensor j
    arcosSaidaSensor = {j: [(j, k) for (j, k) in arcosS if j == sensorJ]
                        for sensorJ in indiceSensores
                        for j in [sensorJ]}
    arcosSaidaSorvedouro = {j: [(j, k) for (j, k) in arcosM if j == sensorJ]
                            for sensorJ in indiceSensores
                            for j in [sensorJ]}

    
    modelo = gp.Model("AtribuicaoPapeis_RSSF")

    if suprimirLog:
        modelo.setParam('LogToConsole', 0)

    modelo.setParam('TimeLimit', tempoLimite)


    # x[l, j, p] = 1 se sensor l cobre ponto j com papel p  [contínua, 0..1]
    # (restrição 10)
    x = modelo.addVars(
        [(l, j, p)
         for (l, j) in arcosC
         for p in indicePapeis
         if papeisDemanda[j] == p],
        lb=0.0, ub=1.0,
        vtype=GRB.CONTINUOUS,
        name='x'
    )

    # z[l, i, j, p] = 1 se arco (i,j) com papel p está na rota do sensor l  [binária]
    # (restrição 11)
    z = modelo.addVars(
        [(l, i, j, p)
         for l in indiceSensores
         for (i, j) in arcosS
         for p in indicePapeis],
        vtype=GRB.BINARY,
        name='z'
    )

    # zM[l, i, j, p] = 1 se arco (i,j) sensor->sorvedouro está na rota de l  [binária]
    # (restrição 11)
    zM = modelo.addVars(
        [(l, i, j, p)
         for l in indiceSensores
         for (i, j) in arcosM
         for p in indicePapeis],
        vtype=GRB.BINARY,
        name='zM'
    )

    # t[l, p] = 1 se sensor l está ativo com papel p  [binária]
    # (restrição 11)
    t = modelo.addVars(
        [(l, p) for l in indiceSensores for p in indicePapeis],
        vtype=GRB.BINARY,
        name='t'
    )

    # h[j] = quantidade de não-cobertura do ponto j  [inteira >= 0]
    # (restrição 12)
    h = modelo.addVars(
        indicePontos,
        vtype=GRB.INTEGER,
        lb=0.0,
        name='h'
    )

    modelo.update()

    
    # Função objetivo — eq. (1)
    # Minimiza: custo_roteamento + custo_ativacao + penalidade_nao_cobertura
    custoRotTotal = gp.quicksum(
        custoRoteamento.get((i, j, p), custoRoteamento.get(str((i, j, p)), 0.0))
        * z[l, i, j, p]
        for l in indiceSensores
        for (i, j) in arcosS
        for p in indicePapeis
    ) + gp.quicksum(
        custoRoteamento.get(('m', i, j, p), custoRoteamento.get(str(('m', i, j, p)), 0.0))
        * zM[l, i, j, p]
        for l in indiceSensores
        for (i, j) in arcosM
        for p in indicePapeis
    )

    custoAtivTotal = gp.quicksum(
        custoAtivacao[l] * t[l, p]
        for l in indiceSensores
        for p in indicePapeis
    )

    custoPenalidade = custoNaoCobertura * gp.quicksum(h[j] for j in indicePontos)

    modelo.setObjective(custoRotTotal + custoAtivTotal + custoPenalidade, GRB.MINIMIZE)

    # Restrição: cobertura de cada ponto de demanda
    # Soma das coberturas + não-cobertura >= 1, para cada ponto j e papel p exigido
    for j in indicePontos:
        p = papeisDemanda[j]
        varsCoberturaJ = [x[l, j, p] for (lc, jc) in arcosC
                          if jc == j for l in [lc]
                          if (l, j, p) in x]
        if varsCoberturaJ:
            modelo.addConstr(
                gp.quicksum(varsCoberturaJ) + h[j] >= 1,
                name=f'cobertura_j{j}'
            )
        else:
            # Nenhum sensor alcança este ponto; h[j] absorve a penalidade
            modelo.addConstr(h[j] >= 1, name=f'cobertura_j{j}_sem_sensor')

    # Restrição: sensor inativo não pode cobrir ponto de demanda
    # sum_j x[l,j,p] <= T1 * t[l,p]
    T1 = numPontos
    for l in indiceSensores:
        for p in indicePapeis:
            varsXlp = [x[l, j, p] for (lc, jc) in arcosC
                       if lc == l
                       for j in [jc]
                       if (l, j, p) in x]
            if varsXlp:
                modelo.addConstr(
                    gp.quicksum(varsXlp) <= T1 * t[l, p],
                    name=f'ativacao_cobertura_l{l}_p{p}'
                )

    # Restrição: fluxo só sai de sensor ativo (arcos saída) - eq. (4)
    # sum_j z[l,i,j,p] + sum_j zM[l,i,j,p] <= T2 * t[i,p] para todo sensor l, i, p
    T2 = numSensores
    for l in indiceSensores:
        for i in indiceSensores:
            for p in indicePapeis:
                saidaS = [(i, j) for (si, j) in arcosS if si == i]
                saidaM = [(i, j) for (si, j) in arcosM if si == i]
                if saidaS or saidaM:
                    termS = gp.quicksum(z[l, i, j, p] for (_, j) in saidaS)
                    termM = gp.quicksum(zM[l, i, j, p] for (_, j) in saidaM)
                    modelo.addConstr(
                        termS + termM <= T2 * t[i, p],
                        name=f'fluxo_saida_l{l}_i{i}_p{p}'
                    )

    # Restrição: fluxo só entra em sensor ativo - eq. (5)
    # sum_i z[l,i,j,p] <= T2 * t[j,p] para todo sensor l, j, p
    for l in indiceSensores:
        for j in indiceSensores:
            for p in indicePapeis:
                entradaJ = [(i, j) for (i, sj) in arcosS if sj == j]
                if entradaJ:
                    modelo.addConstr(
                        gp.quicksum(z[l, i, j, p] for (i, _) in entradaJ) <= T2 * t[j, p],
                        name=f'fluxo_entrada_l{l}_j{j}_p{p}'
                    )

    # Restrição: conservação de fluxo em nós intermediários
    # sum_(ij) z[l,i,j,p] - sum_(jk) z[l,j,k,p] = 0, para j != l
    for l in indiceSensores:
        for j in indiceSensores:
            if j == l:
                continue
            for p in indicePapeis:
                entradaJ = [(i, j) for (i, sj) in arcosS if sj == j]
                saidaJS  = [(j, k) for (sj, k) in arcosS if sj == j]
                saidaJM  = [(j, k) for (sj, k) in arcosM if sj == j]

                fluxoEntrada = gp.quicksum(z[l, i, j, p] for (i, _) in entradaJ)
                fluxoSaidaS  = gp.quicksum(z[l, j, k, p] for (_, k) in saidaJS)
                fluxoSaidaM  = gp.quicksum(zM[l, j, k, p] for (_, k) in saidaJM)

                modelo.addConstr(
                    fluxoEntrada - fluxoSaidaS - fluxoSaidaM == 0,
                    name=f'conservacao_fluxo_l{l}_j{j}_p{p}'
                )

    # Restrição: roteamento tem origem no sensor l
    # sum_(ij) z[l,i,j,p] - sum_(jk) z[l,j,k,p] = -t[l,p], j = l
    for l in indiceSensores:
        for p in indicePapeis:
            entradaL = [(i, l) for (i, sj) in arcosS if sj == l]
            saidaLS  = [(l, k) for (sl, k) in arcosS if sl == l]
            saidaLM  = [(l, k) for (sl, k) in arcosM if sl == l]

            fluxoEntrada = gp.quicksum(z[l, i, l, p] for (i, _) in entradaL)
            fluxoSaidaS  = gp.quicksum(z[l, l, k, p] for (_, k) in saidaLS)
            fluxoSaidaM  = gp.quicksum(zM[l, l, k, p] for (_, k) in saidaLM)

            modelo.addConstr(
                fluxoEntrada - fluxoSaidaS - fluxoSaidaM == -t[l, p],
                name=f'origem_fluxo_l{l}_p{p}'
            )

    # Restrição: energia disponível do sensor deve ser respeitada - eq. (8)
    # Para ser fisicamente correto, o consumo de energia de l com papel p deve considerar
    # a transmissão de pacotes de todas as origens s e a ativação do próprio sensor l.
    for l in indiceSensores:
        for p in indicePapeis:
            custoRotSaidaS = gp.quicksum(
                custoRoteamento.get((l, k, p), custoRoteamento.get(str((l, k, p)), 0.0))
                * z[s, l, k, p]
                for s in indiceSensores
                for (sl, k) in arcosS if sl == l
            )
            custoRotSaidaM = gp.quicksum(
                custoRoteamento.get(('m', l, k, p), custoRoteamento.get(str(('m', l, k, p)), 0.0))
                * zM[s, l, k, p]
                for s in indiceSensores
                for (sl, k) in arcosM if sl == l
            )

            modelo.addConstr(
                custoRotSaidaS + custoRotSaidaM + custoAtivacao[l] * t[l, p]
                <= energiaSensor[l],
                name=f'capacidade_energia_l{l}_p{p}'
            )

    # Restrição: cada sensor assume no máximo um papel
    for l in indiceSensores:
        modelo.addConstr(
            gp.quicksum(t[l, p] for p in indicePapeis) <= 1,
            name=f'um_papel_l{l}'
        )

    modelo.update()
    return modelo




# @params:
#   - modelo (gp.Model): O objeto do modelo Gurobi a ser resolvido.
# @output:
#   - dict: Dicionário contendo os resultados e estatísticas da otimização.
def resolverModelo(modelo: gp.Model) -> dict:
    """
    Otimiza o modelo e retorna um dicionário com os principais resultados.
    """
    inicio = time.time()
    modelo.optimize()
    tempoExecucao = time.time() - inicio

    status = modelo.Status

    resultado = {
        'status':          status,
        'tempoExecucao':   round(tempoExecucao, 4),
        'valorFO':         None,
        'gap':             None,
        'sensoresAtivos':  [],
        'papelSensor':     {},
        'rotas':           [],
        'pontosCobertos':  [],
        'pontosDescobertos': []
    }

    # Solução viável encontrada 
    if status in (GRB.OPTIMAL, GRB.TIME_LIMIT) and modelo.SolCount > 0:
        resultado['valorFO'] = round(modelo.ObjVal, 4)
        resultado['gap']     = round(modelo.MIPGap * 100, 4)  # em %

        variaveis = modelo.getVars()
        nomeVars  = {v.VarName: v.X for v in variaveis}

        # Identifica sensores ativos e seus papéis
        for v in variaveis:
            if v.VarName.startswith('t[') and v.X > 0.5:
                # Formato: t[l,p]
                partes = v.VarName[2:-1].split(',')
                l, p   = int(partes[0]), int(partes[1])
                resultado['sensoresAtivos'].append(l)
                resultado['papelSensor'][l] = p

        # Identifica rotas ativas (arcos com fluxo)
        for v in variaveis:
            if (v.VarName.startswith('z[') or v.VarName.startswith('zM[')) and v.X > 0.5:
                resultado['rotas'].append(v.VarName)

        # Identifica pontos cobertos e descobertos
        for v in variaveis:
            if v.VarName.startswith('h['):
                j = int(v.VarName[2:-1])
                if v.X > 0.5:
                    resultado['pontosDescobertos'].append(j)
                else:
                    resultado['pontosCobertos'].append(j)

    return resultado


# @params:
#   - resultado (dict): Dicionário contendo os resultados obtidos pelo solver.
#   - nomeInstancia (str): Nome ou identificador opcional da instância (padrão: '').
# @output:
#   - None: Apenas imprime os resultados formatados na saída padrão.
def imprimirResultado(resultado: dict, nomeInstancia: str = '') -> None:
    """Exibe um resumo formatado dos resultados na saída padrão."""
    titulo = f" Resultado: {nomeInstancia} " if nomeInstancia else " Resultado "
    print(f"\n{'='*60}")
    print(titulo.center(60))
    print('='*60)
    print(f"  Status            : {resultado['status']}")
    print(f"  Tempo de execução : {resultado['tempoExecucao']} s")
    print(f"  Função objetivo   : {resultado['valorFO']} mAms")
    print(f"  Gap MIP           : {resultado['gap']} %")
    print(f"  Nº nós ativos     : {len(resultado['sensoresAtivos'])}")
    print(f"  Nós ativos        : {sorted(resultado['sensoresAtivos'])}")
    print(f"  Nº pontos cobertos    : {len(resultado['pontosCobertos'])}")
    print(f"  Nº pontos descobertos : {len(resultado['pontosDescobertos'])}")
    print('='*60)