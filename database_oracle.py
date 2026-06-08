from getpass import getpass

from util import ler_inteiro, ler_texto, pausar, titulo


def carregar_driver_oracle():
    """Importa o driver Oracle somente quando o usuario usar o menu de banco."""
    try:
        import oracledb

        return oracledb
    except ModuleNotFoundError:
        print("Driver Oracle nao encontrado.")
        print("Instale com: pip install oracledb")
        return None


def ler_senha() -> str:
    try:
        return getpass("Senha Oracle: ")
    except Exception:
        return input("Senha Oracle: ")


def obter_configuracao() -> dict:
    print("Informe os dados da sua conexao Oracle.")
    print("Exemplo de host: oracle.fiap.com.br")
    print("Exemplo de service name: ORCL")
    print()

    return {
        "usuario": ler_texto("Usuario Oracle"),
        "senha": ler_senha(),
        "host": ler_texto("Host"),
        "porta": ler_inteiro("Porta", 1, 65535),
        "service_name": ler_texto("Service name"),
    }


def conectar(config: dict):
    oracledb = carregar_driver_oracle()
    if oracledb is None:
        return None

    dsn = oracledb.makedsn(
        config["host"],
        config["porta"],
        service_name=config["service_name"],
    )
    return oracledb.connect(
        user=config["usuario"],
        password=config["senha"],
        dsn=dsn,
    )


def testar_conexao(config: dict) -> bool:
    try:
        with conectar(config) as conexao:
            if conexao is None:
                return False

            with conexao.cursor() as cursor:
                cursor.execute("SELECT 'CONEXAO OK' AS status FROM dual")
                status = cursor.fetchone()[0]
                print(f"Resultado: {status}")
                return True
    except Exception as erro:
        print(f"Falha ao conectar no Oracle: {erro}")
        return False


def executar_ddl(cursor, sql: str, nome_tabela: str) -> None:
    try:
        cursor.execute(sql)
        print(f"Tabela {nome_tabela} criada com sucesso.")
    except Exception as erro:
        mensagem = str(erro)
        if "ORA-00955" in mensagem:
            print(f"Tabela {nome_tabela} ja existe. Continuando...")
        else:
            raise


def criar_tabelas_demo(config: dict) -> bool:
    tabelas = [
        (
            "ASTRA_REGIAO_DEMO",
            """
            CREATE TABLE astra_regiao_demo (
                id_regiao NUMBER NOT NULL,
                nome VARCHAR2(80) NOT NULL,
                tipo VARCHAR2(30) NOT NULL,
                distancia_hospital_km NUMBER(6,2) NOT NULL,
                internet_disponivel CHAR(1) NOT NULL,
                CONSTRAINT pk_astra_regiao_demo PRIMARY KEY (id_regiao),
                CONSTRAINT uk_astra_regiao_demo_nome UNIQUE (nome),
                CONSTRAINT ck_astra_regiao_demo_net CHECK (internet_disponivel IN ('S', 'N'))
            )
            """,
        ),
        (
            "ASTRA_PACIENTE_DEMO",
            """
            CREATE TABLE astra_paciente_demo (
                id_paciente NUMBER NOT NULL,
                id_regiao NUMBER NOT NULL,
                nome VARCHAR2(100) NOT NULL,
                idade NUMBER(3) NOT NULL,
                perfil VARCHAR2(40) NOT NULL,
                CONSTRAINT pk_astra_paciente_demo PRIMARY KEY (id_paciente),
                CONSTRAINT fk_astra_paciente_regiao FOREIGN KEY (id_regiao)
                    REFERENCES astra_regiao_demo(id_regiao),
                CONSTRAINT ck_astra_paciente_idade CHECK (idade BETWEEN 0 AND 120)
            )
            """,
        ),
        (
            "ASTRA_ATENDIMENTO_DEMO",
            """
            CREATE TABLE astra_atendimento_demo (
                id_atendimento NUMBER NOT NULL,
                id_paciente NUMBER NOT NULL,
                nivel_risco VARCHAR2(20) NOT NULL,
                pontuacao_risco NUMBER(3) NOT NULL,
                recomendacao VARCHAR2(250) NOT NULL,
                CONSTRAINT pk_astra_atendimento_demo PRIMARY KEY (id_atendimento),
                CONSTRAINT fk_astra_atendimento_paciente FOREIGN KEY (id_paciente)
                    REFERENCES astra_paciente_demo(id_paciente),
                CONSTRAINT ck_astra_atendimento_nivel
                    CHECK (nivel_risco IN ('BAIXO', 'ATENCAO', 'URGENTE', 'EMERGENCIA'))
            )
            """,
        ),
    ]

    try:
        with conectar(config) as conexao:
            if conexao is None:
                return False

            with conexao.cursor() as cursor:
                for nome_tabela, sql in tabelas:
                    executar_ddl(cursor, sql, nome_tabela)
            conexao.commit()
            return True
    except Exception as erro:
        print(f"Erro ao criar tabelas demonstrativas: {erro}")
        return False


def inserir_dados_demo(config: dict) -> bool:
    comandos = [
        """
        MERGE INTO astra_regiao_demo r
        USING (SELECT 1 id_regiao, 'Comunidade Ribeirinha Aruana' nome,
                      'RIBEIRINHA' tipo, 86 distancia_hospital_km, 'N' internet_disponivel
               FROM dual) d
        ON (r.id_regiao = d.id_regiao)
        WHEN NOT MATCHED THEN
            INSERT (id_regiao, nome, tipo, distancia_hospital_km, internet_disponivel)
            VALUES (d.id_regiao, d.nome, d.tipo, d.distancia_hospital_km, d.internet_disponivel)
        """,
        """
        MERGE INTO astra_paciente_demo p
        USING (SELECT 1 id_paciente, 1 id_regiao, 'Jose Maciel' nome,
                      15 idade, 'MORADOR' perfil
               FROM dual) d
        ON (p.id_paciente = d.id_paciente)
        WHEN NOT MATCHED THEN
            INSERT (id_paciente, id_regiao, nome, idade, perfil)
            VALUES (d.id_paciente, d.id_regiao, d.nome, d.idade, d.perfil)
        """,
        """
        MERGE INTO astra_atendimento_demo a
        USING (SELECT 1 id_atendimento, 1 id_paciente, 'URGENTE' nivel_risco,
                      7 pontuacao_risco,
                      'Priorizar teleconsulta e repetir sinais vitais.' recomendacao
               FROM dual) d
        ON (a.id_atendimento = d.id_atendimento)
        WHEN NOT MATCHED THEN
            INSERT (id_atendimento, id_paciente, nivel_risco, pontuacao_risco, recomendacao)
            VALUES (d.id_atendimento, d.id_paciente, d.nivel_risco, d.pontuacao_risco, d.recomendacao)
        """,
    ]

    try:
        with conectar(config) as conexao:
            if conexao is None:
                return False

            with conexao.cursor() as cursor:
                for comando in comandos:
                    cursor.execute(comando)
            conexao.commit()
            print("Dados demonstrativos inseridos ou ja existentes.")
            return True
    except Exception as erro:
        print(f"Erro ao inserir dados demonstrativos: {erro}")
        print("Confira se as tabelas demonstrativas ja foram criadas.")
        return False


def listar_atendimentos_demo(config: dict) -> bool:
    consulta = """
        SELECT
            p.nome,
            p.idade,
            r.nome AS regiao,
            a.nivel_risco,
            a.pontuacao_risco,
            a.recomendacao
        FROM astra_atendimento_demo a
        JOIN astra_paciente_demo p ON p.id_paciente = a.id_paciente
        JOIN astra_regiao_demo r ON r.id_regiao = p.id_regiao
        ORDER BY a.pontuacao_risco DESC
    """

    try:
        with conectar(config) as conexao:
            if conexao is None:
                return False

            with conexao.cursor() as cursor:
                cursor.execute(consulta)
                linhas = cursor.fetchall()

                if not linhas:
                    print("Nenhum atendimento demonstrativo encontrado.")
                    return True

                for nome, idade, regiao, nivel, pontos, recomendacao in linhas:
                    print("-" * 72)
                    print(f"Paciente: {nome} ({idade} anos)")
                    print(f"Regiao: {regiao}")
                    print(f"Risco: {nivel} | Pontuacao: {pontos}")
                    print(f"Recomendacao: {recomendacao}")
                return True
    except Exception as erro:
        print(f"Erro ao consultar dados demonstrativos: {erro}")
        return False


def menu_oracle() -> None:
    while True:
        titulo("Banco de Dados Oracle")
        print("1. Testar conexao")
        print("2. Criar tabelas demonstrativas")
        print("3. Inserir dados demonstrativos")
        print("4. Listar atendimentos demonstrativos")
        print("0. Voltar")

        opcao = input("\nOpcao: ").strip()
        if opcao == "0":
            return

        if opcao in ("1", "2", "3", "4"):
            config = obter_configuracao()
            if opcao == "1":
                testar_conexao(config)
            elif opcao == "2":
                criar_tabelas_demo(config)
            elif opcao == "3":
                inserir_dados_demo(config)
            elif opcao == "4":
                listar_atendimentos_demo(config)
            pausar()
        else:
            print("Opcao invalida.")
            pausar()

