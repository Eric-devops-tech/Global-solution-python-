from datetime import datetime


def linha(tamanho: int = 72) -> str:
    return "-" * tamanho


def titulo(texto: str) -> None:
    print()
    print(linha())
    print(texto.upper().center(72))
    print(linha())


def pausar() -> None:
    input("\nPressione ENTER para continuar...")


def ler_texto(rotulo: str, obrigatorio: bool = True) -> str:
    while True:
        valor = input(f"{rotulo}: ").strip()
        if valor or not obrigatorio:
            return valor
        print("Campo obrigatorio. Tente novamente.")


def ler_inteiro(rotulo: str, minimo: int | None = None, maximo: int | None = None) -> int:
    while True:
        try:
            valor = int(input(f"{rotulo}: ").strip())
            if minimo is not None and valor < minimo:
                print(f"Informe um valor maior ou igual a {minimo}.")
                continue
            if maximo is not None and valor > maximo:
                print(f"Informe um valor menor ou igual a {maximo}.")
                continue
            return valor
        except ValueError:
            print("Entrada invalida. Digite um numero inteiro.")


def ler_float(rotulo: str, minimo: float | None = None, maximo: float | None = None) -> float:
    while True:
        try:
            valor = float(input(f"{rotulo}: ").strip().replace(",", "."))
            if minimo is not None and valor < minimo:
                print(f"Informe um valor maior ou igual a {minimo}.")
                continue
            if maximo is not None and valor > maximo:
                print(f"Informe um valor menor ou igual a {maximo}.")
                continue
            return valor
        except ValueError:
            print("Entrada invalida. Digite um numero valido.")


def confirmar(rotulo: str) -> bool:
    while True:
        resposta = input(f"{rotulo} (s/n): ").strip().lower()
        if resposta in ("s", "sim"):
            return True
        if resposta in ("n", "nao", "não"):
            return False
        print("Resposta invalida. Digite s ou n.")


def agora_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def formatar_data(data_iso: str) -> str:
    try:
        return datetime.fromisoformat(data_iso).strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return data_iso

