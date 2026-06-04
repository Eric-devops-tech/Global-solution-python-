from armazenamento import carregar_atendimentos, salvar_atendimentos
from pacientes import buscar_paciente_por_id, exibir_paciente
from risco import calcular_risco
from util import agora_iso, confirmar, formatar_data, ler_float, ler_inteiro, pausar, titulo


def gerar_id(atendimentos: list) -> int:
    if not atendimentos:
        return 1
    return max(atendimento["id"] for atendimento in atendimentos) + 1


def registrar_atendimento(paciente_id: int, sinais: dict, sintomas: dict, contexto: dict) -> dict:
    atendimentos = carregar_atendimentos()
    avaliacao = calcular_risco(sinais, sintomas, contexto)
    atendimento = {
        "id": gerar_id(atendimentos),
        "paciente_id": paciente_id,
        "data": agora_iso(),
        "sinais": sinais,
        "sintomas": sintomas,
        "contexto": contexto,
        "avaliacao": avaliacao,
    }
    atendimentos.append(atendimento)
    salvar_atendimentos(atendimentos)
    return atendimento


def listar_atendimentos() -> list:
    return carregar_atendimentos()


def atendimentos_por_paciente(paciente_id: int) -> list:
    return [item for item in carregar_atendimentos() if item["paciente_id"] == paciente_id]


def exibir_atendimento(atendimento: dict) -> None:
    sinais = atendimento["sinais"]
    avaliacao = atendimento["avaliacao"]
    print(f"Atendimento ID: {atendimento['id']}")
    print(f"Data: {formatar_data(atendimento['data'])}")
    print(
        "Sinais: "
        f"{sinais['temperatura']} C | "
        f"SpO2 {sinais['saturacao']}% | "
        f"FC {sinais['frequencia_cardiaca']} bpm | "
        f"PA {sinais['pressao_sistolica']}/{sinais['pressao_diastolica']} mmHg"
    )
    print(f"Risco: {avaliacao['nivel']} | Pontuacao: {avaliacao['pontuacao']}")
    print(f"Alertas: {', '.join(avaliacao['alertas']) or 'Sem alertas criticos'}")
    print(f"Recomendacao: {avaliacao['recomendacao']}")


def coletar_sinais_vitais() -> dict:
    titulo("Sinais vitais")
    return {
        "temperatura": ler_float("Temperatura corporal em Celsius", 30, 45),
        "saturacao": ler_inteiro("Saturacao de oxigenio (%)", 50, 100),
        "frequencia_cardiaca": ler_inteiro("Frequencia cardiaca (bpm)", 20, 220),
        "pressao_sistolica": ler_inteiro("Pressao sistolica", 50, 260),
        "pressao_diastolica": ler_inteiro("Pressao diastolica", 30, 160),
    }


def coletar_sintomas() -> dict:
    titulo("Triagem de sintomas")
    return {
        "dor_peito": confirmar("Dor no peito"),
        "falta_ar": confirmar("Falta de ar"),
        "confusao": confirmar("Confusao mental"),
        "desmaio": confirmar("Desmaio recente"),
        "sangramento": confirmar("Sangramento relevante"),
        "febre_persistente": confirmar("Febre persistente"),
        "vomitos": confirmar("Vomitos intensos"),
        "dor_forte": confirmar("Dor forte"),
    }


def coletar_contexto() -> dict:
    titulo("Contexto operacional")
    return {
        "distancia_hospital_km": ler_float("Distancia ate suporte medico avancado (km)", 0),
        "internet_disponivel": confirmar("Internet disponivel para teleconsulta"),
        "medicamentos_basicos": confirmar("Medicamentos basicos disponiveis"),
    }


def tela_registrar_atendimento() -> None:
    titulo("Novo atendimento remoto")
    paciente_id = ler_inteiro("ID do paciente", 1)
    paciente = buscar_paciente_por_id(paciente_id)

    if paciente is None:
        print("Paciente nao encontrado. Cadastre o paciente antes do atendimento.")
        pausar()
        return

    exibir_paciente(paciente)
    sinais = coletar_sinais_vitais()
    sintomas = coletar_sintomas()
    contexto = coletar_contexto()
    atendimento = registrar_atendimento(paciente_id, sinais, sintomas, contexto)

    titulo("Resultado da avaliacao")
    exibir_atendimento(atendimento)
    pausar()


def tela_historico_paciente() -> None:
    titulo("Historico por paciente")
    paciente_id = ler_inteiro("ID do paciente", 1)
    paciente = buscar_paciente_por_id(paciente_id)

    if paciente is None:
        print("Paciente nao encontrado.")
        pausar()
        return

    historico = atendimentos_por_paciente(paciente_id)
    if not historico:
        print("Nenhum atendimento registrado para este paciente.")
    else:
        exibir_paciente(paciente)
        print()
        for atendimento in historico:
            exibir_atendimento(atendimento)
            print("-" * 72)
    pausar()


def tela_listar_atendimentos() -> None:
    titulo("Todos os atendimentos")
    atendimentos = listar_atendimentos()
    if not atendimentos:
        print("Nenhum atendimento registrado.")
    else:
        for atendimento in atendimentos:
            avaliacao = atendimento["avaliacao"]
            print(
                f"{atendimento['id']:03d} | Paciente {atendimento['paciente_id']:03d} | "
                f"{formatar_data(atendimento['data'])} | {avaliacao['nivel']} | "
                f"{avaliacao['pontuacao']} pontos"
            )
    pausar()


def menu_atendimentos() -> None:
    while True:
        titulo("Menu de atendimentos")
        print("1. Registrar sinais vitais e triagem")
        print("2. Consultar historico por paciente")
        print("3. Listar todos os atendimentos")
        print("0. Voltar")

        opcao = input("\nOpcao: ").strip()
        if opcao == "1":
            tela_registrar_atendimento()
        elif opcao == "2":
            tela_historico_paciente()
        elif opcao == "3":
            tela_listar_atendimentos()
        elif opcao == "0":
            return
        else:
            print("Opcao invalida.")
            pausar()

