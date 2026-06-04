from armazenamento import carregar_atendimentos, carregar_pacientes, salvar_relatorio_texto
from util import formatar_data, pausar, titulo


def contar_por_nivel(atendimentos: list) -> dict:
    contagem = {"BAIXO": 0, "ATENCAO": 0, "URGENTE": 0, "EMERGENCIA": 0}
    for atendimento in atendimentos:
        nivel = atendimento["avaliacao"]["nivel"]
        contagem[nivel] = contagem.get(nivel, 0) + 1
    return contagem


def filtrar_casos_criticos(atendimentos: list) -> list:
    return [
        atendimento
        for atendimento in atendimentos
        if atendimento["avaliacao"]["nivel"] in ("URGENTE", "EMERGENCIA")
    ]


def localizar_nome_paciente(pacientes: list, paciente_id: int) -> str:
    for paciente in pacientes:
        if paciente["id"] == paciente_id:
            return paciente["nome"]
    return "Paciente nao localizado"


def gerar_relatorio() -> str:
    pacientes = carregar_pacientes()
    atendimentos = carregar_atendimentos()
    contagem = contar_por_nivel(atendimentos)
    criticos = filtrar_casos_criticos(atendimentos)

    linhas = [
        "ASTRACARE REMOTE HEALTH - RELATORIO OPERACIONAL",
        "=" * 72,
        f"Pacientes cadastrados: {len(pacientes)}",
        f"Atendimentos registrados: {len(atendimentos)}",
        "",
        "Distribuicao de risco:",
        f"- BAIXO: {contagem['BAIXO']}",
        f"- ATENCAO: {contagem['ATENCAO']}",
        f"- URGENTE: {contagem['URGENTE']}",
        f"- EMERGENCIA: {contagem['EMERGENCIA']}",
        "",
        "Casos criticos:",
    ]

    if not criticos:
        linhas.append("- Nenhum caso urgente ou emergencial registrado.")
    else:
        for atendimento in criticos:
            nome = localizar_nome_paciente(pacientes, atendimento["paciente_id"])
            avaliacao = atendimento["avaliacao"]
            linhas.append(
                f"- {formatar_data(atendimento['data'])} | {nome} | "
                f"{avaliacao['nivel']} | {avaliacao['pontuacao']} pontos | "
                f"{avaliacao['recomendacao']}"
            )

    return "\n".join(linhas)


def tela_resumo_riscos() -> None:
    titulo("Resumo de riscos")
    atendimentos = carregar_atendimentos()
    contagem = contar_por_nivel(atendimentos)
    print(f"Baixo: {contagem['BAIXO']}")
    print(f"Atencao: {contagem['ATENCAO']}")
    print(f"Urgente: {contagem['URGENTE']}")
    print(f"Emergencia: {contagem['EMERGENCIA']}")
    pausar()


def tela_casos_criticos() -> None:
    titulo("Casos criticos")
    pacientes = carregar_pacientes()
    criticos = filtrar_casos_criticos(carregar_atendimentos())

    if not criticos:
        print("Nenhum caso urgente ou emergencial registrado.")
    else:
        for atendimento in criticos:
            nome = localizar_nome_paciente(pacientes, atendimento["paciente_id"])
            avaliacao = atendimento["avaliacao"]
            print(f"Paciente: {nome}")
            print(f"Data: {formatar_data(atendimento['data'])}")
            print(f"Nivel: {avaliacao['nivel']} ({avaliacao['pontuacao']} pontos)")
            print(f"Alertas: {', '.join(avaliacao['alertas'])}")
            print(f"Recomendacao: {avaliacao['recomendacao']}")
            print("-" * 72)
    pausar()


def tela_gerar_relatorio_txt() -> None:
    titulo("Gerar relatorio TXT")
    conteudo = gerar_relatorio()
    if salvar_relatorio_texto(conteudo):
        print(conteudo)
        print("\nRelatorio salvo em astracare/dados/relatorio.txt")
    else:
        print("Nao foi possivel salvar o relatorio.")
    pausar()


def menu_relatorios() -> None:
    while True:
        titulo("Menu de relatorios")
        print("1. Ver resumo por nivel de risco")
        print("2. Ver casos criticos")
        print("3. Gerar relatorio em TXT")
        print("0. Voltar")

        opcao = input("\nOpcao: ").strip()
        if opcao == "1":
            tela_resumo_riscos()
        elif opcao == "2":
            tela_casos_criticos()
        elif opcao == "3":
            tela_gerar_relatorio_txt()
        elif opcao == "0":
            return
        else:
            print("Opcao invalida.")
            pausar()

