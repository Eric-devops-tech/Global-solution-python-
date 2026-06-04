from armazenamento import carregar_pacientes, salvar_pacientes
from util import agora_iso, ler_inteiro, ler_texto, pausar, titulo


def gerar_id(pacientes: list) -> int:
    if not pacientes:
        return 1
    return max(paciente["id"] for paciente in pacientes) + 1


def cadastrar_paciente(nome: str, idade: int, localizacao: str, funcao: str, condicoes: list) -> dict:
    pacientes = carregar_pacientes()
    paciente = {
        "id": gerar_id(pacientes),
        "nome": nome,
        "idade": idade,
        "localizacao": localizacao,
        "funcao": funcao,
        "condicoes": condicoes,
        "criado_em": agora_iso(),
    }
    pacientes.append(paciente)
    salvar_pacientes(pacientes)
    return paciente


def buscar_paciente_por_id(paciente_id: int) -> dict | None:
    pacientes = carregar_pacientes()
    for paciente in pacientes:
        if paciente["id"] == paciente_id:
            return paciente
    return None


def listar_pacientes() -> list:
    return carregar_pacientes()


def exibir_paciente(paciente: dict) -> None:
    condicoes = ", ".join(paciente.get("condicoes", [])) or "Nenhuma informada"
    print(f"ID: {paciente['id']}")
    print(f"Nome: {paciente['nome']}")
    print(f"Idade: {paciente['idade']}")
    print(f"Localizacao: {paciente['localizacao']}")
    print(f"Funcao/Perfil: {paciente['funcao']}")
    print(f"Condicoes relevantes: {condicoes}")


def tela_cadastrar_paciente() -> None:
    titulo("Cadastro de paciente ou tripulante")
    nome = ler_texto("Nome completo")
    idade = ler_inteiro("Idade", 0, 120)
    localizacao = ler_texto("Localizacao remota/base/comunidade")
    funcao = ler_texto("Funcao ou perfil (ex: morador, agente, pesquisador)")
    condicoes_texto = ler_texto("Condicoes previas separadas por virgula", obrigatorio=False)
    condicoes = [item.strip() for item in condicoes_texto.split(",") if item.strip()]

    paciente = cadastrar_paciente(nome, idade, localizacao, funcao, condicoes)
    print("\nPaciente cadastrado com sucesso.")
    exibir_paciente(paciente)
    pausar()


def tela_listar_pacientes() -> None:
    titulo("Pacientes cadastrados")
    pacientes = listar_pacientes()
    if not pacientes:
        print("Nenhum paciente cadastrado.")
    else:
        for paciente in pacientes:
            print(f"{paciente['id']:03d} | {paciente['nome']} | {paciente['idade']} anos | {paciente['localizacao']}")
    pausar()


def tela_buscar_paciente() -> None:
    titulo("Buscar paciente")
    paciente_id = ler_inteiro("ID do paciente", 1)
    paciente = buscar_paciente_por_id(paciente_id)
    if paciente is None:
        print("Paciente nao encontrado.")
    else:
        exibir_paciente(paciente)
    pausar()


def menu_pacientes() -> None:
    while True:
        titulo("Menu de pacientes")
        print("1. Cadastrar paciente/tripulante")
        print("2. Listar pacientes")
        print("3. Buscar paciente por ID")
        print("0. Voltar")

        opcao = input("\nOpcao: ").strip()
        if opcao == "1":
            tela_cadastrar_paciente()
        elif opcao == "2":
            tela_listar_pacientes()
        elif opcao == "3":
            tela_buscar_paciente()
        elif opcao == "0":
            return
        else:
            print("Opcao invalida.")
            pausar()

