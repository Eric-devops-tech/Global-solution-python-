from getpass import getpass
# Importamos as funções dos seus outros módulos para ler os dados reais do JSON
from atendimentos import listar_atendimentos
from pacientes import listar_pacientes
from util import confirmar, ler_inteiro, ler_texto, pausar, titulo

CONFIG_ORACLE = None


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


def configurar_conexao() -> dict:
    global CONFIG_ORACLE

    print("Informe os dados da sua conexao Oracle.")
    print("Exemplo FIAP:")
    print("Host: oracle.fiap.com.br")
    print("Porta: 1521")
    print("Service name: ORCL")
    print()

    CONFIG_ORACLE = {
        "usuario": ler_texto("Usuario Oracle"),
        "senha": ler_senha(),
        "host": ler_texto("Host"),
        "porta": ler_inteiro("Porta", 1, 65535),
        "service_name": ler_texto("Service name"),
    }
    return CONFIG_ORACLE


def obtener_configuracao() -> dict:
    if CONFIG_ORACLE is None:
        return configurar_conexao()

    if confirmar("Usar a conexao Oracle ja informada nesta execucao"):
        return CONFIG_ORACLE

    return configurar_conexao()


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


def ejecutar_ddl(cursor, sql: str, nome_tabela: str) -> None:
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
        (
            "ASTRA_SINAL_VITAL_DEMO",
            """
            CREATE TABLE astra_sinal_vital_demo (
                id_atendimento NUMBER NOT NULL,
                temperatura NUMBER(4,1) NOT NULL,
                saturacao NUMBER(3) NOT NULL,
                frequencia_cardiaca NUMBER(3) NOT NULL,
                pressao_sistolica NUMBER(3) NOT NULL,
                pressao_diastolica NUMBER(3) NOT NULL,
                CONSTRAINT pk_astra_sinal_vital_demo PRIMARY KEY (id_atendimento),
                CONSTRAINT fk_astra_sinal_atendimento FOREIGN KEY (id_atendimento) 
                    REFERENCES astra_atendimento_demo(id_atendimento)
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


def obter_id_regiao(cursor, nome_regiao: str, distancia: float = 0, internet: str = "N") -> int:
    cursor.execute(
        "SELECT id_regiao FROM astra_regiao_demo WHERE UPPER(nome) = UPPER(:nome)",
        nome=nome_regiao,
    )
    linha = cursor.fetchone()
    if linha:
        id_regiao = linha[0]
        cursor.execute(
            """
            UPDATE astra_regiao_demo
               SET distancia_hospital_km = :distancia,
                   internet_disponivel = :internet
             WHERE id_regiao = :id_regiao
            """,
            distancia=distancia,
            internet=internet,
            id_regiao=id_regiao,
        )
        return id_regiao

    cursor.execute("SELECT NVL(MAX(id_regiao), 0) + 1 FROM astra_regiao_demo")
    id_regiao = cursor.fetchone()[0]
    cursor.execute(
        """
        INSERT INTO astra_regiao_demo (
            id_regiao, nome, tipo, distancia_hospital_km, internet_disponivel
        ) VALUES (
            :id_regiao, :nome, 'ESTACAO_REMOTA', :distancia, :internet
        )
        """,
        id_regiao=id_regiao,
        nome=nome_regiao,
        distancia=distancia,
        internet=internet,
    )
    return id_regiao


def salvar_paciente_no_oracle(config: dict, paciente: dict) -> bool:
    try:
        with conectar(config) as conexao:
            if conexao is None:
                return False

            with conexao.cursor() as cursor:
                id_regiao = obter_id_regiao(cursor, paciente["localizacao"])
                cursor.execute(
                    """
                    MERGE INTO astra_paciente_demo p
                    USING (
                        SELECT :id_paciente id_paciente,
                               :id_regiao id_regiao,
                               :nome nome,
                               :idade idade,
                               :perfil perfil
                          FROM dual
                    ) d
                    ON (p.id_paciente = d.id_paciente)
                    WHEN MATCHED THEN
                        UPDATE SET p.id_regiao = d.id_regiao,
                                   p.nome = d.nome,
                                   p.idade = d.idade,
                                   p.perfil = d.perfil
                    WHEN NOT MATCHED THEN
                        INSERT (id_paciente, id_regiao, nome, idade, perfil)
                        VALUES (d.id_paciente, d.id_regiao, d.nome, d.idade, d.perfil)
                    """,
                    id_paciente=paciente["id"],
                    id_regiao=id_regiao,
                    nome=paciente["nome"],
                    idade=paciente["idade"],
                    perfil=paciente["funcao"].upper()[:40],
                )
            conexao.commit()
            print(f"Paciente '{paciente['nome']}' sincronizado no Oracle.")
            return True
    except Exception as erro:
        print(f"Erro ao salvar paciente no Oracle: {erro}")
        return False


def salvar_atendimento_no_oracle(config: dict, paciente: dict, atendimento: dict) -> bool:
    try:
        with conectar(config) as conexao:
            if conexao is None:
                return False

            contexto = atendimento["contexto"]
            internet = "S" if contexto["internet_disponivel"] else "N"
            avaliacao = atendimento["avaliacao"]
            sinais = atendimento["sinais"]

            with conexao.cursor() as cursor:
                id_regiao = obter_id_regiao(
                    cursor,
                    paciente["localizacao"],
                    contexto["distancia_hospital_km"],
                    internet,
                )
                cursor.execute(
                    """
                    MERGE INTO astra_paciente_demo p
                    USING (
                        SELECT :id_paciente id_paciente,
                               :id_regiao id_regiao,
                               :nome nome,
                               :idade idade,
                               :perfil perfil
                          FROM dual
                    ) d
                    ON (p.id_paciente = d.id_paciente)
                    WHEN MATCHED THEN
                        UPDATE SET p.id_regiao = d.id_regiao,
                                   p.nome = d.nome,
                                   p.idade = d.idade,
                                   p.perfil = d.perfil
                    WHEN NOT MATCHED THEN
                        INSERT (id_paciente, id_regiao, nome, idade, perfil)
                        VALUES (d.id_paciente, d.id_regiao, d.nome, d.idade, d.perfil)
                    """,
                    id_paciente=paciente["id"],
                    id_regiao=id_regiao,
                    nome=paciente["nome"],
                    idade=paciente["idade"],
                    perfil=paciente["funcao"].upper()[:40],
                )
                cursor.execute(
                    """
                    MERGE INTO astra_atendimento_demo a
                    USING (
                        SELECT :id_atendimento id_atendimento,
                               :id_paciente id_paciente,
                               :nivel_risco nivel_risco,
                               :pontuacao_risco pontuacao_risco,
                               :recomendacao recomendacao
                          FROM dual
                    ) d
                    ON (a.id_atendimento = d.id_atendimento)
                    WHEN MATCHED THEN
                        UPDATE SET a.id_paciente = d.id_paciente,
                                   a.nivel_risco = d.nivel_risco,
                                   a.pontuacao_risco = d.pontuacao_risco,
                                   a.recomendacao = d.recomendacao
                    WHEN NOT MATCHED THEN
                        INSERT (id_atendimento, id_paciente, nivel_risco, pontuacao_risco, recomendacao)
                        VALUES (d.id_atendimento, d.id_paciente, d.nivel_risco, d.pontuacao_risco, d.recomendacao)
                    """,
                    id_atendimento=atendimento["id"],
                    id_paciente=paciente["id"],
                    nivel_risco=avaliacao["nivel"],
                    pontuacao_risco=avaliacao["pontuacao"],
                    recomendacao=avaliacao["recomendacao"][:250],
                )
                cursor.execute(
                    """
                    MERGE INTO astra_sinal_vital_demo s
                    USING (
                        SELECT :id_atendimento id_atendimento,
                               :temperatura temperatura,
                               :saturacao saturacao,
                               :frequencia_cardiaca frequencia_cardiaca,
                               :pressao_sistolica pressao_sistolica,
                               :pressao_diastolica pressao_diastolica
                          FROM dual
                    ) d
                    ON (s.id_atendimento = d.id_atendimento)
                    WHEN MATCHED THEN
                        UPDATE SET s.temperatura = d.temperatura,
                                   s.saturacao = d.saturacao,
                                   s.frequencia_cardiaca = d.frequencia_cardiaca,
                                   s.pressao_sistolica = d.pressao_sistolica,
                                   s.pressao_diastolica = d.pressao_diastolica
                    WHEN NOT MATCHED THEN
                        INSERT (
                            id_atendimento, temperatura, saturacao, frequencia_cardiaca,
                            pressao_sistolica, pressao_diastolica
                        )
                        VALUES (
                            d.id_atendimento, d.temperatura, d.saturacao, d.frequencia_cardiaca,
                            d.pressao_sistolica, d.pressao_diastolica
                        )
                    """,
                    id_atendimento=atendimento["id"],
                    temperatura=sinais["temperatura"],
                    saturacao=sinais["saturacao"],
                    frequencia_cardiaca=sinais["frequencia_cardiaca"],
                    pressao_sistolica=sinais["pressao_sistolica"],
                    pressao_diastolica=sinais["pressao_diastolica"],
                )
            conexao.commit()
            print(f"Atendimento ID {atendimento['id']} sincronizado no Oracle.")
            return True
    except Exception as erro:
        print(f"Erro ao salvar atendimento no Oracle: {erro}")
        return False


def sincronizar_dados_locais(config: dict) -> bool:
    """Le os arquivos JSON locais e sincroniza em lote com o banco Oracle."""
    titulo("Sincronizando JSON -> Oracle")

    pacientes_locais = listar_pacientes()
    atendimentos_locais = listar_atendimentos()

    if not pacientes_locais and not atendimentos_locais:
        print("Nenhum dado local encontrado nos arquivos JSON para sincronizar.")
        return True

    # Garante que as tabelas existam antes de começar a carga
    criar_tabelas_demo(config)

    sucesso_pacientes = True
    sucesso_atendimentos = True

    if pacientes_locais:
        print(f"\nSincronizando {len(pacientes_locais)} pacientes...")
        for paciente in pacientes_locais:
            if not salvar_paciente_no_oracle(config, paciente):
                sucesso_pacientes = False

    if atendimentos_locais:
        print(f"\nSincronizando {len(atendimentos_locais)} atendimentos...")
        for atendimento in atendimentos_locais:
            paciente_correspondente = next(
                (p for p in pacientes_locais if p["id"] == atendimento["paciente_id"]),
                {
                    "id": atendimento["paciente_id"],
                    "nome": f"Paciente {atendimento['paciente_id']}",
                    "localizacao": "Estacao Remota Horizonte",
                    "funcao": "TRIPULANTE",
                },
            )
            if not salvar_atendimento_no_oracle(config, paciente_correspondente, atendimento):
                sucesso_atendimentos = False

    if sucesso_pacientes and sucesso_atendimentos:
        print("\n[OK] Todos os dados do JSON foram salvos/atualizados com sucesso no Oracle!")
        return True
    else:
        print("\n[!] Houve falhas ao sincronizar alguns registros locais.")
        return False


def listar_atendimentos_demo(config: dict) -> bool:
    consulta = """
        SELECT
            p.nome,
            p.idade,
            r.nome AS regiao,
            a.nivel_risco,
            a.pontuacao_risco,
            sv.saturacao,
            sv.temperatura,
            a.recomendacao
        FROM astra_atendimento_demo a
        JOIN astra_paciente_demo p ON p.id_paciente = a.id_paciente
        JOIN astra_regiao_demo r ON r.id_regiao = p.id_regiao
        LEFT JOIN astra_sinal_vital_demo sv ON sv.id_atendimento = a.id_atendimento
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
                    print("Nenhum atendimento encontrado no banco Oracle.")
                    return True

                for nome, idade, regiao, nivel, pontos, saturacao, temperatura, recomendacao in linhas:
                    print("-" * 72)
                    print(f"Paciente: {nome} ({idade} anos)")
                    print(f"Regiao: {regiao}")
                    print(f"Risco: {nivel} | Pontuacao: {pontos}")
                    print(f"Sinais: temperatura {temperatura} C | SpO2 {saturacao}%")
                    print(f"Recomendacao: {recomendacao}")
                return True
    except Exception as erro:
        print(f"Erro ao consultar dados do Oracle: {erro}")
        return False


def menu_oracle() -> None:
    while True:
        titulo("Banco de Dados Oracle")
        print("1. Configurar conexao")
        print("2. Testar conexao")
        print("3. Criar tabelas estruturais")
        print("4. Sincronizar dados locais (JSON -> Oracle)")
        print("5. Listar atendimentos salvos no Oracle")
        print("0. Voltar")

        opcao = input("\nOpcao: ").strip()
        if opcao == "0":
            return

        if opcao == "1":
            configuring = configurar_conexao()
            pausar()
        elif opcao in ("2", "3", "4", "5"):
            config = obter_configuracao()
            if opcao == "2":
                testar_conexao(config)
            elif opcao == "3":
                criar_tabelas_demo(config)
            elif opcao == "4":
                sincronizar_dados_locais(config)
            elif opcao == "5":
                listar_atendimentos_demo(config)
            pausar()
        else:
            print("Opcao invalida.")
            pausar()