from armazenamento import garantir_estrutura
from atendimentos import menu_atendimentos
from pacientes import menu_pacientes
from relatorios import menu_relatorios
from util import pausar, titulo


def exibir_sobre() -> None:
    titulo("Sobre o AstraCare")
    print("AstraCare Remote Health e um sistema de apoio a decisao em saude remota.")
    print("Ele foi pensado para bases isoladas, comunidades distantes e ambientes extremos.")
    print("O sistema registra pacientes, sinais vitais, sintomas e contexto operacional.")
    print("A partir desses dados, calcula um nivel de risco e recomenda uma conduta inicial.")
    print("Os dados ficam persistidos em arquivos JSON e os relatorios podem ser salvos em TXT.")
    pausar()


def menu_principal() -> None:
    garantir_estrutura()

    while True:
        titulo("AstraCare Remote Health")
        print("1. Pacientes e tripulantes")
        print("2. Atendimentos, sinais vitais e triagem")
        print("3. Relatorios e casos criticos")
        print("4. Sobre o sistema")
        print("0. Sair")

        opcao = input("\nOpcao: ").strip()
        if opcao == "1":
            menu_pacientes()
        elif opcao == "2":
            menu_atendimentos()
        elif opcao == "3":
            menu_relatorios()
        elif opcao == "4":
            exibir_sobre()
        elif opcao == "0":
            print("\nEncerrando o AstraCare. Dados locais preservados.")
            break
        else:
            print("Opcao invalida.")
            pausar()


if __name__ == "__main__":
    menu_principal()

