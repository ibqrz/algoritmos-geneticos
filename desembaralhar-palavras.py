#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Algoritmo Genético clássico em Python puro (apenas bibliotecas nativas).
Objetivo: descobrir a palavra secreta "ANCHIETA" a partir de strings aleatórias.

Execute no terminal:  python algoritmo_genetico.py
"""

import os
import random
import re
import string
import time

# =============================================================================
# CONFIGURAÇÕES  (altere aqui à vontade)
# =============================================================================
TARGET          = "ANCHIETA"   # Palavra secreta
TAMANHO_POP     = 100          # Tamanho da população
TAXA_MUTACAO    = 0.05         # Probabilidade de mutação POR LETRA (0 a 1). Teste com 0!
TAXA_SELECAO    = 0.50         # Fração da população (os melhores) que vira "pais"
ELITE           = 2            # Nº de melhores indivíduos copiados sem alteração
MAX_GERACOES    = 5000         # Trava de segurança (evita loop infinito com mutação 0)
PAUSA_SEG       = 0.05         # Pausa entre gerações p/ acompanhar a evolução (0 = sem pausa)
USAR_CORES      = True         # False desativa as cores ANSI

ALFABETO = string.ascii_uppercase
TAM = len(TARGET)

# =============================================================================
# LAYOUT DO TERMINAL (cores ANSI, caixas e barra de fitness)
# =============================================================================
if os.name == "nt":
    os.system("")  # habilita sequências ANSI no terminal do Windows

def cor(texto, codigo):
    """Aplica uma cor ANSI ao texto (se as cores estiverem ativas)."""
    return f"\033[{codigo}m{texto}\033[0m" if USAR_CORES else texto


VERDE, VERMELHO, AMARELO, CIANO, CINZA, NEGRITO = "92", "91", "93", "96", "90", "1"


def colorir_palavra(individuo):
    """
    Estilo "Wordle":
      - verde   : letra certa na posição certa
      - amarelo : letra existe na palavra-alvo, mas está na posição errada
      - vermelho: letra não existe (ou já foi totalmente aproveitada)
    Letras repetidas respeitam a quantidade real no alvo (ex.: "A" aparece 2x).
    """
    # Letras do alvo que NÃO foram acertadas na posição exata (disponíveis p/ amarelo)
    restantes = {}
    for letra, alvo in zip(individuo, TARGET):
        if letra != alvo:
            restantes[alvo] = restantes.get(alvo, 0) + 1

    saida = []
    for letra, alvo in zip(individuo, TARGET):
        if letra == alvo:
            saida.append(cor(letra, "1;92"))            # verde
        elif restantes.get(letra, 0) > 0:
            restantes[letra] -= 1
            saida.append(cor(letra, "1;93"))            # amarelo
        else:
            saida.append(cor(letra, VERMELHO))          # vermelho
    return "".join(saida)


def barra_fitness(fit):
    """Barra visual de progresso: ████░░░░"""
    cheio = cor("█" * fit, VERDE if fit == TAM else AMARELO)
    vazio = cor("░" * (TAM - fit), CINZA)
    return cheio + vazio


ANSI_RE = re.compile(r"\033\[[0-9;]*m")


def tam_visivel(texto):
    """Comprimento do texto como aparece na tela (ignora códigos de cor ANSI)."""
    return len(ANSI_RE.sub("", texto))


def campo(rotulo, valor):
    """Linha 'Rótulo : valor' com os dois-pontos sempre alinhados."""
    return f"{rotulo:<18}: {valor}"


def caixa(linhas, largura=58):
    """Imprime um painel com bordas retas. `linhas` = lista de textos (podem ter cor)."""
    print(cor("╔" + "═" * largura + "╗", CIANO))
    for linha in linhas:
        espaco = " " * max(0, largura - 2 - tam_visivel(linha))
        print(cor("║", CIANO) + " " + linha + espaco + " " + cor("║", CIANO))
    print(cor("╚" + "═" * largura + "╝", CIANO))


def cabecalho():
    linhas = [
        cor("ALGORITMO GENÉTICO  -  ADIVINHANDO A PALAVRA SECRETA", "1;96"),
        "",
        campo("Alvo", cor("?" * TAM, AMARELO)),
        campo("População", cor(TAMANHO_POP, NEGRITO)),
        campo("Taxa de mutação", cor(f"{TAXA_MUTACAO:.1%}", NEGRITO)),
        campo("Seleção / Elite", cor(f"{TAXA_SELECAO:.0%} / {ELITE}", NEGRITO)),
    ]
    caixa(linhas)
    legenda = (f"  Legenda: {cor('■', '1;92')} posição certa   "
               f"{cor('■', '1;93')} letra certa, posição errada   {cor('■', VERMELHO)} não existe")
    print(legenda)
    print()
    print(cor(f"  {'GERAÇÃO':<10}{'MELHOR':<10}{'FITNESS':<9}PROGRESSO", NEGRITO))
    print(cor("  " + "─" * 46, CINZA))


# =============================================================================
# NÚCLEO DO ALGORITMO GENÉTICO
# =============================================================================
def criar_individuo():
    """Gera uma string aleatória com TAM letras maiúsculas."""
    return "".join(random.choice(ALFABETO) for _ in range(TAM))


def criar_populacao(tamanho):
    """Gera a população inicial."""
    return [criar_individuo() for _ in range(tamanho)]


def fitness(individuo):
    """Quantidade de letras corretas na posição exata (0 a TAM)."""
    return sum(1 for a, b in zip(individuo, TARGET) if a == b)


def selecionar_pais(populacao_ordenada):
    """Seleção por truncamento: mantém apenas a fração dos melhores indivíduos."""
    corte = max(2, int(len(populacao_ordenada) * TAXA_SELECAO))
    return populacao_ordenada[:corte]


def cruzar(pai1, pai2):
    """Crossover de um ponto: início do pai1 + final do pai2."""
    ponto = random.randint(1, TAM - 1)
    return pai1[:ponto] + pai2[ponto:]


def mutar(individuo):
    """Cada letra tem TAXA_MUTACAO de chance de ser trocada por outra aleatória."""
    if TAXA_MUTACAO <= 0:
        return individuo
    letras = list(individuo)
    for i in range(TAM):
        if random.random() < TAXA_MUTACAO:
            letras[i] = random.choice(ALFABETO)
    return "".join(letras)


def proxima_geracao(populacao_ordenada):
    """Elitismo + seleção + crossover + mutação."""
    nova = populacao_ordenada[:ELITE]            # elitismo: preserva os melhores
    pais = selecionar_pais(populacao_ordenada)
    while len(nova) < TAMANHO_POP:
        p1, p2 = random.sample(pais, 2) if len(pais) >= 2 else (pais[0], pais[0])
        nova.append(mutar(cruzar(p1, p2)))
    return nova


# =============================================================================
# EXECUÇÃO PRINCIPAL
# =============================================================================
def main():
    inicio = time.time()
    populacao = criar_populacao(TAMANHO_POP)
    cabecalho()

    geracao = 0
    melhor, melhor_fit = "", 0
    motivo_parada = None

    while True:
        geracao += 1

        # Ordena do melhor para o pior fitness
        populacao.sort(key=fitness, reverse=True)
        melhor = populacao[0]
        melhor_fit = fitness(melhor)

        fit_txt = cor(f"{melhor_fit}/{TAM}", NEGRITO) + " " * (9 - len(f"{melhor_fit}/{TAM}"))
        print(f"  {geracao:<10}{colorir_palavra(melhor)}{'':<2}{fit_txt}{barra_fitness(melhor_fit)}")

        # Critério de parada principal: palavra encontrada
        if melhor_fit == TAM:
            motivo_parada = "sucesso"
            break

        # Travas de segurança (úteis principalmente com mutação = 0)
        if len(set(populacao)) == 1 and TAXA_MUTACAO == 0:
            motivo_parada = "sem_diversidade"
            break
        if geracao >= MAX_GERACOES:
            motivo_parada = "limite"
            break

        populacao = proxima_geracao(populacao)
        if PAUSA_SEG:
            time.sleep(PAUSA_SEG)

    # ----------------------------- RESUMO FINAL -----------------------------
    tempo = time.time() - inicio
    print(cor("  " + "─" * 46, CINZA))
    print()
    if motivo_parada == "sucesso":
        titulo = cor("✔ PALAVRA SECRETA ENCONTRADA!", "1;92")
    else:
        titulo = cor("✘ NÃO FOI POSSÍVEL ENCONTRAR A PALAVRA", "1;91")

    linhas = [
        titulo,
        "",
        campo("Palavra", colorir_palavra(melhor)),
        campo("Total de gerações", cor(geracao, "1;93")),
        campo("Melhor fitness", cor(f"{melhor_fit}/{TAM}", NEGRITO)),
        campo("Tempo", cor(f"{tempo:.2f}s", NEGRITO)),
    ]
    if motivo_parada == "sem_diversidade":
        linhas.append(cor("Motivo: população idêntica e mutação = 0 (estagnou).", AMARELO))
    elif motivo_parada == "limite":
        linhas.append(cor(f"Motivo: limite de {MAX_GERACOES} gerações atingido.", AMARELO))
    caixa(linhas)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(cor("\n  Execução interrompida pelo usuário.", AMARELO))