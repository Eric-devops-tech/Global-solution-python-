import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DADOS_DIR = BASE_DIR / "dados"
PACIENTES_ARQUIVO = DADOS_DIR / "pacientes.json"
ATENDIMENTOS_ARQUIVO = DADOS_DIR / "atendimentos.json"
RELATORIO_ARQUIVO = DADOS_DIR / "relatorio.txt"


def garantir_estrutura() -> None:
    """Cria a pasta de dados e os arquivos JSON iniciais."""
    DADOS_DIR.mkdir(exist_ok=True)
    for arquivo in (PACIENTES_ARQUIVO, ATENDIMENTOS_ARQUIVO):
        if not arquivo.exists():
            salvar_json(arquivo, [])


def carregar_json(caminho: Path) -> list:
    try:
        if not caminho.exists():
            return []

        with caminho.open("r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
            return dados if isinstance(dados, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def salvar_json(caminho: Path, dados: list) -> bool:
    try:
        caminho.parent.mkdir(exist_ok=True)
        with caminho.open("w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, ensure_ascii=False, indent=4)
        return True
    except OSError:
        return False


def carregar_pacientes() -> list:
    return carregar_json(PACIENTES_ARQUIVO)


def salvar_pacientes(pacientes: list) -> bool:
    return salvar_json(PACIENTES_ARQUIVO, pacientes)


def carregar_atendimentos() -> list:
    return carregar_json(ATENDIMENTOS_ARQUIVO)


def salvar_atendimentos(atendimentos: list) -> bool:
    return salvar_json(ATENDIMENTOS_ARQUIVO, atendimentos)


def salvar_relatorio_texto(conteudo: str) -> bool:
    try:
        DADOS_DIR.mkdir(exist_ok=True)
        with RELATORIO_ARQUIVO.open("w", encoding="utf-8") as arquivo:
            arquivo.write(conteudo)
        return True
    except OSError:
        return False

