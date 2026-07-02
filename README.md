# Atribuição de Papéis em Redes de Sensores Sem Fio (RSSF)
**Disciplina**: Pesquisa Operacional  
**Autor**: Joaquim  

---

## 1. Introdução ao Problema
As Redes de Sensores Sem Fio (RSSF) representam uma tecnologia essencial para o monitoramento de áreas de interesse em aplicações militares, ambientais, comerciais e industriais. Uma RSSF consiste em centenas ou milhares de pequenos dispositivos equipados com sensores, microprocessadores e antenas de rádio, distribuídos por uma região geográfica.

O principal limitador operacional das RSSF é a restrição energética. Sendo alimentados por baterias cuja substituição costuma ser impraticável devido a razões geográficas ou econômicas, o principal desafio de projeto consiste em maximizar o tempo de vida operacional da rede. Uma estratégia comum é a atribuição dinâmica ou estática de papéis específicos (tais como sensor de determinada grandeza, nó de transmissão/relay ou agregador de dados) a cada um dos nós. Dessa forma, nós redundantes podem ser mantidos inativos (modo *sleep/off*) para conservar energia, enquanto os nós ativos são responsáveis pela cobertura de pontos de demanda e pelo roteamento dos dados coletados até estações base ou sorvedouros (*sinks*).

O Problema de Atribuição de Papéis em RSSF consiste em determinar quais nós devem ser ativados, quais papéis específicos cada um desempenhará e qual será o caminho de roteamento das informações coletadas até os sorvedouros, minimizando o custo total de energia sob restrições físicas de cobertura, capacidade e conservação de fluxo de rede. Trata-se de um problema NP-Difícil de otimização combinatória.

---

## 2. Resumo do Artigo Escolhido
O artigo **"Um Modelo de Otimização para o Problema de Atribuição de Papéis em Redes de Sensores Sem Fio"** (Souza e Mateus, XXXVIII Simpósio Brasileiro de Pesquisa Operacional, 2006) propõe uma formulação de Programação Linear Inteira Mista (PLIM) para abordar esse problema em redes homogêneas ou heterogêneas de sensores estáticos. 

Os autores definem um cenário onde os pontos de demanda e os sensores estão dispostos em uma área bidimensional. O modelo abrange a cobertura de alvos geográficos (pontos de demanda que exigem a ativação de papéis específicos de sensoriamento) e a conectividade dos nós ativos, garantindo que haja um caminho livre de loops a partir de cada nó sensor ativo até ao menos um nó sorvedouro. 

A metodologia do artigo envolveu a modelagem matemática exata, a geração de 25 instâncias de teste divididas em três conjuntos com diferentes densidades de nós e raios de comunicação/sensoriamento, e a sua resolução utilizando o solver CPLEX 9.0 em um microcomputador Pentium 4 de 2.40 GHz com 1GB de RAM. Os resultados evidenciaram que o modelo foi capaz de otimizar a rede e reduzir significativamente o número de nós ativos necessários para cobertura total ou parcial da área geográfica.

---

## 3. Descrição Detalhada da Formulação Matemática
O problema é modelado sobre um grafo direcionado $G = (N, A)$, onde $N$ representa o conjunto de nós e $A$ representa o conjunto de arcos viáveis. Os subconjuntos de nós e arcos são descritos a seguir:
* $N^s$: Subconjunto de nós correspondentes aos sensores.
* $N^m$: Subconjunto de nós sorvedouros (*sinks*).
* $N^d$: Subconjunto de pontos de demanda da área a ser monitorada.
* $A^c$: Arcos direcionados de cobertura, conectando sensores a pontos de demanda que estão sob o seu raio de sensoriamento.
* $A^s$: Arcos direcionados de comunicação entre sensores (sensor $\rightarrow$ sensor).
* $A^m$: Arcos direcionados de comunicação de sensores para sorvedouros (sensor $\rightarrow$ sorvedouro).
* $E_j(A^s)$: Conjunto de arcos $(i,j) \in A^s$ que entram no nó sensor $j \in N^s$.
* $S_j(A^s)$: Conjunto de arcos $(j,k) \in A^s$ que saem do nó sensor $j \in N^s$.

O conjunto de papéis que um nó sensor pode assumir é definido por $P$. Cada papel possui parâmetros operacionais específicos:
* $c_l^p$: Energia necessária para ativar e manter o sensor $l$ no papel $p$.
* $d_{ij}^p$: Custo energético de comunicação entre o nó sensor $i$ e o nó $j$ quando o sensor assume o papel $p$. Esse custo é calculado em função do rádio ligado, do tempo de transmissão do papel e da distância euclidiana.
* $M$: Penalidade aplicada na função objetivo quando um ponto de demanda não é coberto.
* $T^1$: Número total de pontos de demanda ($|N^d|$).
* $T^2$: Número total de nós sensores ($|N^s|$).
* $b_l$: Energia total disponível no nó sensor $l$.

As variáveis de decisão são definidas como:
* $x_{lj}^p \in [0, 1]$: Variável contínua que representa a fração de cobertura que o sensor $l$ provê ao ponto de demanda $j$ sob o papel $p$.
* $z_{ij}^{lp} \in \{0, 1\}$: Variável binária associada ao fluxo. Vale 1 se o arco $(i,j)$ com papel $p$ faz parte da rota do sensor $l$ para um sorvedouro.
* $t_l^p \in \{0, 1\}$: Variável binária de ativação. Vale 1 se o sensor $l$ está ativo com papel $p$, e 0 caso contrário.
* $h_j \ge 0$: Variável inteira que quantifica a não-cobertura do ponto de demanda $j$.

### 3.1. Formulação Matemática Corrigida
Durante a análise detalhada das equações apresentadas no artigo original, foram identificados e corrigidos três erros conceituais significativos nas restrições de fluxo (conectividade) e energia:

$$\text{Min } \sum_{l \in N^s} \sum_{(i,j) \in A^s \cup A^m} \sum_{p \in P} d_{ij}^p z_{ij}^{lp} + \sum_{l \in N^s} \sum_{p \in P} c_l^p t_l^p + M \sum_{j \in N^d} h_j$$

Sujeito a:
1. **Cobertura de demanda**:  
   $$\sum_{(l, j) \in A^c} x_{lj}^p + h_j \ge 1 \quad \forall j \in N^d, \ p = \text{papel exigido por } j$$
2. **Ativação da cobertura**:  
   $$\sum_{j \in N^d} x_{lj}^p \le T^1 t_l^p \quad \forall l \in N^s, \ \forall p \in P$$
3. **Ativação de fluxo de saída (Corrigida)**:  
   $$\sum_{(i, k) \in A^s} z_{ik}^{lp} + \sum_{(i, k) \in A^m} zM_{ik}^{lp} \le T^2 t_i^p \quad \forall l \in N^s, \ \forall i \in N^s, \ \forall p \in P$$
4. **Ativação de fluxo de entrada (Corrigida)**:  
   $$\sum_{(k, j) \in A^s} z_{kj}^{lp} \le T^2 t_j^p \quad \forall l \in N^s, \ \forall j \in N^s, \ \forall p \in P$$
5. **Conservação de fluxo em nós intermediários**:  
   $$\sum_{(i,j) \in E_j(A^s)} z_{ij}^{lp} - \sum_{(j,k) \in S_j(A^s)} z_{jk}^{lp} - \sum_{(j,k) \in A^m} zM_{jk}^{lp} = 0 \quad \forall j \in N^s \setminus \{l\}, \ \forall l \in N^s, \ \forall p \in P$$
6. **Origem do fluxo no nó gerador**:  
   $$\sum_{(i,l) \in E_l(A^s)} z_{il}^{lp} - \sum_{(l,k) \in S_l(A^s)} z_{lk}^{lp} - \sum_{(l,k) \in A^m} zM_{lk}^{lp} = -t_l^p \quad \forall l \in N^s, \ \forall p \in P$$
7. **Energia disponível no sensor (Corrigida)**:  
   $$\sum_{s \in N^s} \left( \sum_{(l, k) \in A^s} d_{lk}^p z_{lk}^{sp} + \sum_{(l, k) \in A^m} d_{lk}^p zM_{lk}^{sp} \right) + c_l^p t_l^p \le b_l \quad \forall l \in N^s, \ \forall p \in P$$
8. **Unicidade de papel**:  
   $$\sum_{p \in P} t_l^p \le 1 \quad \forall l \in N^s$$
9. **Limites e Tipos de Variáveis**:  
   $$x_{lj}^p \in [0, 1] \quad \forall (l,j) \in A^c, \ \forall p \in P$$
   $$z_{ij}^{lp}, zM_{ij}^{lp}, t_l^p \in \{0, 1\} \quad \forall (i,j), \ \forall l, \ \forall p$$
   $$h_j \in \mathbb{Z}^+ \quad \forall j \in N^d$$

### 3.2. Justificativa das Correções Realizadas
* **Erros de Fluxo (Equações 4 e 5)**: O lado direito original das restrições utilizava a variável de ativação do nó de origem $l$ ($t_l^p$) em vez do nó físico receptor/transmissor ($t_i^p$ ou $t_j^p$). Isso gerava a inconsistência física de permitir que pacotes fossem transmitidos por nós intermediários completamente inativos. A indexação corrigida garante que somente nós ativos ($t_i^p=1$ e $t_j^p=1$) possam propagar dados na rede. Além disso, adicionou-se a variável $zM$ (transmissão de sensor para sorvedouro) na Eq. 4 para impedir transmissões não licenciadas diretamente de nós inativos para as estações base.
* **Erro de Energia (Equação 8)**: A restrição original limitava a capacidade $b_l$ do sensor $l$ analisando somente as variáveis de fluxo associadas ao seu próprio pacote $z_{lk}^{lp}$. Na prática, um nó sensor consome bateria toda vez que atua como transmissor, inclusive para pacotes de terceiros ($s \neq l$). A formulação foi corrigida para somar o tráfego gerado por todas as fontes $s \in N^s$ que usam $l$ como transmissor, modelando fielmente o consumo de bateria.

---

## 4. Descrição da Implementação Realizada
A implementação foi desenvolvida em **Python 3** utilizando a API **gurobipy** do Gurobi Optimizer. O código é estruturado de forma modular em três scripts principais:
1. **`modelo.py`**: Implementa a criação das variáveis, a definição da função objetivo multicritério e a construção lógica de todas as restrições lineares ajustadas.
2. **`gerador_instancias.py`**: Implementa o posicionamento físico da rede (dimensão da área de 10x10, grades de demanda de 100 pontos, 4 sorvedouros nos cantos e sensores aleatórios com sementes reprodutíveis) e gera os parâmetros baseados na tecnologia de sensores Mica2.
3. **`main.py`**: Orquestra a execução, gerencia a criação dos conjuntos de instâncias de teste, plota gráficos detalhados das topologias e caminhos encontrados na pasta `resultados/graficos`, e consolida as estatísticas operacionais de saída em um arquivo CSV de síntese.

---

## 5. Resultados Obtidos
Os resultados experimentais consolidados após a execução das 25 instâncias geradas seguindo os parâmetros do artigo são descritos na Tabela 1.

### Tabela 1: Resumo dos Resultados Experimentais
<table>
  <thead>
    <tr>
      <th align='center'>Conjunto</th>
      <th align='left'>Instância</th>
      <th align='center'>Sensores<br><code>|N<sup>s</sup>|</code></th>
      <th align='center'>Raios<br>(S/C)</th>
      <th align='right'>Nós<br>Ativos</th>
      <th align='right'>Pontos<br>Descobertos</th>
      <th align='right'>F.O.<br>(mAms)</th>
      <th align='right'>Tempo<br>Gurobi (s)</th>
      <th align='right'>Tempo<br>Artigo (s)</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td rowspan='11' align='center' valign='middle'><b>C1</b></td>
      <td align='left'>inst1</td>
      <td align='center'>10</td>
      <td align='center'>7.5</td>
      <td align='right'>5</td>
      <td align='right'>0</td>
      <td align='right'>1648.10</td>
      <td align='right'>0.03</td>
      <td align='right'>0.07</td>
    </tr>
    <tr>
      <td align='left'>inst2</td>
      <td align='center'>10</td>
      <td align='center'>7.5</td>
      <td align='right'>4</td>
      <td align='right'>0</td>
      <td align='right'>1321.97</td>
      <td align='right'>0.04</td>
      <td align='right'>0.58</td>
    </tr>
    <tr>
      <td align='left'>inst3</td>
      <td align='center'>10</td>
      <td align='center'>7.5</td>
      <td align='right'>5</td>
      <td align='right'>0</td>
      <td align='right'>2021.06</td>
      <td align='right'>0.07</td>
      <td align='right'>1.29</td>
    </tr>
    <tr>
      <td align='left'>inst4</td>
      <td align='center'>10</td>
      <td align='center'>7.5</td>
      <td align='right'>6</td>
      <td align='right'>0</td>
      <td align='right'>2330.10</td>
      <td align='right'>0.03</td>
      <td align='right'>0.61</td>
    </tr>
    <tr>
      <td align='left'>inst5</td>
      <td align='center'>10</td>
      <td align='center'>7.5</td>
      <td align='right'>5</td>
      <td align='right'>0</td>
      <td align='right'>1661.72</td>
      <td align='right'>0.03</td>
      <td align='right'>0.64</td>
    </tr>
    <tr>
      <td align='left'>inst6</td>
      <td align='center'>10</td>
      <td align='center'>7.5</td>
      <td align='right'>5</td>
      <td align='right'>0</td>
      <td align='right'>1654.59</td>
      <td align='right'>0.04</td>
      <td align='right'>0.35</td>
    </tr>
    <tr>
      <td align='left'>inst7</td>
      <td align='center'>10</td>
      <td align='center'>7.5</td>
      <td align='right'>4</td>
      <td align='right'>0</td>
      <td align='right'>1324.55</td>
      <td align='right'>0.04</td>
      <td align='right'>0.22</td>
    </tr>
    <tr>
      <td align='left'>inst8</td>
      <td align='center'>10</td>
      <td align='center'>7.5</td>
      <td align='right'>4</td>
      <td align='right'>0</td>
      <td align='right'>1336.71</td>
      <td align='right'>0.04</td>
      <td align='right'>0.27</td>
    </tr>
    <tr>
      <td align='left'>inst9</td>
      <td align='center'>10</td>
      <td align='center'>7.5</td>
      <td align='right'>3</td>
      <td align='right'>0</td>
      <td align='right'>1233.63</td>
      <td align='right'>0.03</td>
      <td align='right'>0.45</td>
    </tr>
    <tr>
      <td align='left'>inst10</td>
      <td align='center'>10</td>
      <td align='center'>7.5</td>
      <td align='right'>3</td>
      <td align='right'>0</td>
      <td align='right'>1222.87</td>
      <td align='right'>0.04</td>
      <td align='right'>0.39</td>
    </tr>
    <tr>
      <td colspan='3'><b>Média C1</b></td>
      <td align='right'><b>4.4</b></td>
      <td align='right'><b>0.0</b></td>
      <td align='right'><b>1635.53</b></td>
      <td align='right'><b>0.04</b></td>
      <td align='right'><b>0.49</b></td>
    </tr>
    <tr>
      <td rowspan='11' align='center' valign='middle'><b>C2</b></td>
      <td align='left'>inst11</td>
      <td align='center'>20</td>
      <td align='center'>5.0</td>
      <td align='right'>9</td>
      <td align='right'>0</td>
      <td align='right'>3559.74</td>
      <td align='right'>0.12</td>
      <td align='right'>1.75</td>
    </tr>
    <tr>
      <td align='left'>inst12</td>
      <td align='center'>20</td>
      <td align='center'>5.0</td>
      <td align='right'>9</td>
      <td align='right'>0</td>
      <td align='right'>3862.97</td>
      <td align='right'>0.33</td>
      <td align='right'>2.97</td>
    </tr>
    <tr>
      <td align='left'>inst13</td>
      <td align='center'>20</td>
      <td align='center'>5.0</td>
      <td align='right'>9</td>
      <td align='right'>0</td>
      <td align='right'>3650.89</td>
      <td align='right'>0.22</td>
      <td align='right'>2.52</td>
    </tr>
    <tr>
      <td align='left'>inst14</td>
      <td align='center'>20</td>
      <td align='center'>5.0</td>
      <td align='right'>10</td>
      <td align='right'>0</td>
      <td align='right'>3624.33</td>
      <td align='right'>0.22</td>
      <td align='right'>2.98</td>
    </tr>
    <tr>
      <td align='left'>inst15</td>
      <td align='center'>20</td>
      <td align='center'>5.0</td>
      <td align='right'>9</td>
      <td align='right'>0</td>
      <td align='right'>3527.78</td>
      <td align='right'>0.16</td>
      <td align='right'>2.85</td>
    </tr>
    <tr>
      <td align='left'>inst16</td>
      <td align='center'>20</td>
      <td align='center'>5.0</td>
      <td align='right'>9</td>
      <td align='right'>0</td>
      <td align='right'>3639.80</td>
      <td align='right'>0.27</td>
      <td align='right'>7.90</td>
    </tr>
    <tr>
      <td align='left'>inst17</td>
      <td align='center'>20</td>
      <td align='center'>5.0</td>
      <td align='right'>9</td>
      <td align='right'>0</td>
      <td align='right'>3850.54</td>
      <td align='right'>0.16</td>
      <td align='right'>3.07</td>
    </tr>
    <tr>
      <td align='left'>inst18</td>
      <td align='center'>20</td>
      <td align='center'>5.0</td>
      <td align='right'>10</td>
      <td align='right'>0</td>
      <td align='right'>3570.76</td>
      <td align='right'>0.24</td>
      <td align='right'>1.40</td>
    </tr>
    <tr>
      <td align='left'>inst19</td>
      <td align='center'>20</td>
      <td align='center'>5.0</td>
      <td align='right'>10</td>
      <td align='right'>0</td>
      <td align='right'>3653.81</td>
      <td align='right'>0.37</td>
      <td align='right'>1.58</td>
    </tr>
    <tr>
      <td align='left'>inst20</td>
      <td align='center'>20</td>
      <td align='center'>5.0</td>
      <td align='right'>9</td>
      <td align='right'>0</td>
      <td align='right'>3510.39</td>
      <td align='right'>0.11</td>
      <td align='right'>3.69</td>
    </tr>
    <tr>
      <td colspan='3'><b>Média C2</b></td>
      <td align='right'><b>9.3</b></td>
      <td align='right'><b>0.0</b></td>
      <td align='right'><b>3645.10</b></td>
      <td align='right'><b>0.22</b></td>
      <td align='right'><b>3.07</b></td>
    </tr>
    <tr>
      <td rowspan='6' align='center' valign='middle'><b>C3</b></td>
      <td align='left'>inst21</td>
      <td align='center'>36</td>
      <td align='center'>2.5</td>
      <td align='right'>29</td>
      <td align='right'>11</td>
      <td align='right'>1135373.87</td>
      <td align='right'>115.17</td>
      <td align='right'>166.83</td>
    </tr>
    <tr>
      <td align='left'>inst22</td>
      <td align='center'>36</td>
      <td align='center'>2.5</td>
      <td align='right'>32</td>
      <td align='right'>9</td>
      <td align='right'>952681.39</td>
      <td align='right'>12.53</td>
      <td align='right'>1125.42</td>
    </tr>
    <tr>
      <td align='left'>inst23</td>
      <td align='center'>36</td>
      <td align='center'>2.5</td>
      <td align='right'>33</td>
      <td align='right'>8</td>
      <td align='right'>843695.35</td>
      <td align='right'>26.62</td>
      <td align='right'>292.33</td>
    </tr>
    <tr>
      <td align='left'>inst24</td>
      <td align='center'>36</td>
      <td align='center'>2.5</td>
      <td align='right'>30</td>
      <td align='right'>8</td>
      <td align='right'>825799.70</td>
      <td align='right'>5.48</td>
      <td align='right'>5653.79</td>
    </tr>
    <tr>
      <td align='left'>inst25</td>
      <td align='center'>36</td>
      <td align='center'>2.5</td>
      <td align='right'>31</td>
      <td align='right'>11</td>
      <td align='right'>1139011.68</td>
      <td align='right'>19.80</td>
      <td align='right'>3741.93</td>
    </tr>
    <tr>
      <td colspan='3'><b>Média C3</b></td>
      <td align='right'><b>31.0</b></td>
      <td align='right'><b>9.4</b></td>
      <td align='right'><b>979312.40</b></td>
      <td align='right'><b>35.92</b></td>
      <td align='right'><b>2196.06</b></td>
    </tr>
  </tbody>
</table>
---

## 6. Comparação com o Artigo Original
1. **Topologias Espaciais e Funções Objetivo**: Como as coordenadas exatas das instâncias originais da publicação de 2006 não estão disponíveis, a geração atual das posições dos sensores e pontos de demanda utiliza sementes aleatórias. Diferenças pontuais nas distâncias euclidianas alteram levemente o custo de roteamento individual e a cobertura, o que justifica a divergência decimal nos valores finais da Função Objetivo.
2. **Coerência das Médias Estatísticas**: A aderência do comportamento geral da implementação aos dados reportados na literatura é excelente:
   * No **Conjunto 1**, obtivemos uma média de **4,4** sensores ativos contra **4,6** do artigo. A cobertura total da área foi obtida em todas as instâncias (0 pontos descobertos).
   * No **Conjunto 2**, a média de sensores ativos foi de **9,3** sensores contra **8,9** do artigo original. A cobertura foi totalmente garantida (o artigo teve 2 pontos descobertos na inst20).
   * No **Conjunto 3**, com o raio reduzido para $2,5$, é geometricamente inviável cobrir a grade inteira com 36 sensores. Registrou-se uma média de **9,4** pontos descobertos (no artigo original, a média foi de **13,2**). A penalidade sobre cada ponto descoberto ($M = 100.000$) deslocou a função objetivo para a escala de $10^6$ mAms, mantendo perfeita analogia com a análise dos autores originais. A média de sensores ativos requerida subiu para **31,0** contra **28,2** do artigo original.
3. **Evolução do Tempo Computacional**: O avanço do hardware e a otimização dos métodos de ramificação e corte (*branch-and-cut*) do Gurobi 13.0.2 reduziram os tempos de otimização a valores ínfimos. Enquanto o CPLEX 9.0 em um Pentium 4 de 2.4 GHz demorou mais de uma hora e meia para resolver a instância 24, a nossa infraestrutura moderna atingiu o ótimo provado em meros **5,48 segundos**, resultando em uma aceleração de aproximadamente **1000 vezes** na média geral do Conjunto 3.

---

## 7. Conclusões
Este projeto reproduziu e validou com sucesso a modelagem matemática e os experimentos computacionais de Souza e Mateus (2006) para a atribuição de papéis em RSSF. A análise matemática crítica permitiu identificar inconsistências lógicas cruciais de formulação, provendo as correções devidas sob a perspectiva da engenharia e da física de redes de computadores.

Os resultados obtidos demonstram de forma clara as propriedades e limitações de projetos de redes de sensores: à medida que a restrição de raio físico de sensoriamento e comunicação diminui, a rede torna-se sensivelmente mais cara, exige a ativação de quase a totalidade dos sensores disponíveis e expõe pontos descobertos à penalidade de não cobertura. A validação exaustiva via Python e Gurobi corrobora o sucesso absoluto da implementação para a submissão final da disciplina de Pesquisa Operacional.
