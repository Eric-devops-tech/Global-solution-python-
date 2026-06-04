def avaliar_sinais_vitais(sinais: dict) -> tuple[int, list]:
    pontos = 0
    alertas = []

    temperatura = sinais["temperatura"]
    saturacao = sinais["saturacao"]
    frequencia = sinais["frequencia_cardiaca"]
    pressao_sistolica = sinais["pressao_sistolica"]
    pressao_diastolica = sinais["pressao_diastolica"]

    if temperatura >= 39 or temperatura < 35:
        pontos += 3
        alertas.append("temperatura critica")
    elif temperatura >= 38:
        pontos += 1
        alertas.append("febre")

    if saturacao < 90:
        pontos += 4
        alertas.append("saturacao muito baixa")
    elif saturacao < 94:
        pontos += 2
        alertas.append("saturacao reduzida")

    if frequencia > 130 or frequencia < 45:
        pontos += 3
        alertas.append("frequencia cardiaca critica")
    elif frequencia > 110 or frequencia < 55:
        pontos += 1
        alertas.append("frequencia cardiaca alterada")

    if pressao_sistolica >= 180 or pressao_diastolica >= 120:
        pontos += 4
        alertas.append("crise hipertensiva possivel")
    elif pressao_sistolica >= 140 or pressao_diastolica >= 90:
        pontos += 1
        alertas.append("pressao arterial elevada")

    if pressao_sistolica < 90:
        pontos += 3
        alertas.append("hipotensao")

    return pontos, alertas


def avaliar_sintomas(sintomas: dict) -> tuple[int, list]:
    pontos = 0
    alertas = []

    pesos = {
        "dor_peito": (4, "dor no peito"),
        "falta_ar": (4, "falta de ar"),
        "confusao": (4, "confusao mental"),
        "desmaio": (4, "desmaio"),
        "sangramento": (3, "sangramento relevante"),
        "febre_persistente": (2, "febre persistente"),
        "vomitos": (2, "vomitos intensos"),
        "dor_forte": (2, "dor forte"),
    }

    for chave, (peso, alerta) in pesos.items():
        if sintomas.get(chave):
            pontos += peso
            alertas.append(alerta)

    return pontos, alertas


def avaliar_contexto(contexto: dict) -> tuple[int, list]:
    pontos = 0
    alertas = []

    if contexto["distancia_hospital_km"] >= 100:
        pontos += 2
        alertas.append("distancia extrema de suporte medico")
    elif contexto["distancia_hospital_km"] >= 30:
        pontos += 1
        alertas.append("distancia relevante de suporte medico")

    if not contexto["internet_disponivel"]:
        pontos += 1
        alertas.append("sem internet para teleconsulta imediata")

    if not contexto["medicamentos_basicos"]:
        pontos += 1
        alertas.append("estoque basico indisponivel")

    return pontos, alertas


def classificar_risco(pontuacao: int) -> str:
    if pontuacao >= 10:
        return "EMERGENCIA"
    if pontuacao >= 6:
        return "URGENTE"
    if pontuacao >= 3:
        return "ATENCAO"
    return "BAIXO"


def gerar_recomendacao(nivel: str) -> str:
    recomendacoes = {
        "EMERGENCIA": "Acionar evacuacao/resgate, manter monitoramento continuo e contato medico remoto prioritario.",
        "URGENTE": "Priorizar teleconsulta, repetir sinais vitais em curto intervalo e preparar possivel remocao.",
        "ATENCAO": "Manter observacao, registrar evolucao e agendar avaliacao remota.",
        "BAIXO": "Orientar autocuidado, registrar caso e reavaliar se houver piora.",
    }
    return recomendacoes[nivel]


def calcular_risco(sinais: dict, sintomas: dict, contexto: dict) -> dict:
    pontos_sinais, alertas_sinais = avaliar_sinais_vitais(sinais)
    pontos_sintomas, alertas_sintomas = avaliar_sintomas(sintomas)
    pontos_contexto, alertas_contexto = avaliar_contexto(contexto)

    pontuacao = pontos_sinais + pontos_sintomas + pontos_contexto
    nivel = classificar_risco(pontuacao)

    return {
        "pontuacao": pontuacao,
        "nivel": nivel,
        "alertas": alertas_sinais + alertas_sintomas + alertas_contexto,
        "recomendacao": gerar_recomendacao(nivel),
    }

