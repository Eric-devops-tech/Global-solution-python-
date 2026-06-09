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


def obter_configuracao() -> dict:
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
                print(f"Resultado da conexao: {status}")
                return True
    except Exception as erro:
        print(f"Falha ao conectar no Oracle: {erro}")
        return False


def obter_id_regiao(cursor, nome_regiao: str, distancia: float = 0, internet: str = "N") -> int:
    """Busca o ID da regiao oficial ou insere se nao existir, tratando a UF obrigatoria."""
    cursor.execute(
        "SELECT id_regiao FROM regiao_isolada WHERE UPPER(nome) = UPPER(:nome)",
        nome=nome_regiao,
    )
    linha = cursor.fetchone()
    if linha:
        id_regiao = linha[0]
        cursor.execute(
            """
            UPDATE regiao_isolada
               SET distancia_hospital_km = :distancia,
                   internet_disponivel = :internet
             WHERE id_regiao = :id_regiao
            """,
            distancia=distancia,
            internet=internet,
            id_regiao=id_regiao,
        )
        return id_regiao

    # Se a regiao nao existe, gera um novo ID incremental
    cursor.execute("SELECT NVL(MAX(id_regiao), 0) + 1 FROM regiao_isolada")
    id_regiao = cursor.fetchone()[0]
    
    # Define uma UF padrao de contingencia caso nao consiga deduzir do nome
    uf_padrao = "SP"
    nome_maiusculo = nome_regiao.upper()
    
    # Pequena inteligencia para tentar adivinhar a UF com base nos seus dados do DDL
    if "AMAZONAS" in nome_maiusculo or "ARUANA" in nome_maiusculo or "RIO AZUL" in nome_maiusculo:
        uf_padrao = "AM"
    elif "AURORA" in nome_maiusculo or "SUL" in nome_maiusculo:
        uf_padrao = "RS"
    elif "LUCAS" in nome_maiusculo or "RIO" in nome_maiusculo:
        uf_padrao = "RJ"

    cursor.execute(
        """
        INSERT INTO regiao_isolada (
            id_regiao, nome, tipo, uf, distancia_hospital_km, internet_disponivel
        ) VALUES (
            :id_regiao, :nome, 'ESTACAO_REMOTA', :uf, :distancia, :internet
        )
        """,
        id_regiao=id_regiao,
        nome=nome_regiao,
        uf=uf_padrao,
        distancia=distancia,
        internet=internet,
    )
    return id_regiao


def salvar_paciente_no_oracle(config: dict, paciente: dict) -> bool:
    """Insere ou atualiza o paciente na tabela oficial PACIENTE."""
    try:
        with conectar(config) as conexao:
            if conexao is None:
                return False

            with conexao.cursor() as cursor:
                id_regiao = obter_id_regiao(cursor, paciente["localizacao"])
                cursor.execute(
                    """
                    MERGE INTO paciente p
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
                    perfil=(
                        paciente["funcao"].upper()[:40] 
                        if paciente["funcao"].upper() in ('MORADOR', 'AGENTE_SAUDE', 'PESQUISADOR', 'TRIPULANTE', 'TECNICO') 
                        else 'TRIPULANTE'
),
                )
            conexao.commit()
            print(f"Paciente '{paciente['nome']}' sincronizado nas tabelas oficiais.")
            return True
    except Exception as erro:
        print(f"[ERRO BANCO PACIENTE] Falha ao enviar para tabela oficial: {erro}")
        return False


def salvar_atendimento_no_oracle(config: dict, paciente: dict, atendimento: dict) -> bool:
    """Desmembra e envia o atendimento para ATENDIMENTO e SINAL_VITAL oficiais."""
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
                
                # Sincroniza o dono do atendimento primeiro para evitar quebra de FK
                cursor.execute(
                    """
                    MERGE INTO paciente p
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
                
                # Envia para a tabela oficial de ATENDIMENTO
                cursor.execute(
                    """
                    MERGE INTO atendimento a
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
                    recomendacao=avaliacao["recomendacao"][:300],
                )
                
                # Envia para a tabela oficial de SINAL_VITAL
                cursor.execute(
                    """
                    MERGE INTO sinal_vital s
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
            print(f"Atendimento ID {atendimento['id']} sincronizado nas tabelas oficiais.")
            return True
    except Exception as erro:
        print(f"[ERRO BANCO ATENDIMENTO] Falha ao enviar para tabela oficial: {erro}")
        return False


def sincronizar_dados_locais(config: dict) -> bool:
    """Lê os arquivos JSON locais e joga em lote direto para as tabelas oficiais."""
    titulo("Sincronizando JSON -> Tabelas Oficiais")

    pacientes_locais = listar_pacientes()
    atendimentos_locais = listar_atendimentos()

    if not pacientes_locais and not atendimentos_locais:
        print("Nenhum dado local encontrado nos arquivos JSON para sincronizar.")
        return True

    sucesso_pacientes = True
    sucesso_atendimentos = True

    if pacientes_locais:
        print(f"\nEnviando {len(pacientes_locais)} pacientes...")
        for paciente in pacientes_locais:
            if not salvar_paciente_no_oracle(config, paciente):
                sucesso_pacientes = False

    if atendimentos_locais:
        print(f"\nEnviando {len(atendimentos_locais)} atendimentos...")
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
        print("\n[OK] Sincronizacao em lote com as tabelas oficiais concluida!")
        return True
    else:
        print("\n[!] Houve falhas. Verifique os logs de erro acima.")
        return False


def listar_atendimentos_oficiais(config: dict) -> bool:
    """Busca os dados direto das suas tabelas oficiais via JOIN."""
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
        FROM atendimento a
        JOIN paciente p ON p.id_paciente = a.id_paciente
        JOIN regiao_isolada r ON r.id_regiao = p.id_regiao
        LEFT JOIN sinal_vital sv ON sv.id_atendimento = a.id_atendimento
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
                    print("Nenhum atendimento encontrado nas tabelas oficiais do Oracle.")
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
        print(f"Erro ao consultar dados oficiais do Oracle: {erro}")
        return False


def menu_oracle() -> None:
    while True:
        titulo("Banco de Dados Oracle")
        print("1. Configurar credenciais de conexao")
        print("2. Testar conexao com o servidor")
        print("4. Sincronizar dados locais (JSON -> Tabelas Oficiais)")
        print("5. Listar atendimentos direto do Oracle")
        print("0. Voltar")

        opcao = input("\nOpcao: ").strip()
        if opcao == "0":
            return

        if opcao == "1":
            configurar_conexao()
            pausar()
        elif opcao in ("2", "4", "5"):
            config = obter_configuracao()
            if opcao == "2":
                testar_conexao(config)
            elif opcao == "4":
                sincronizar_dados_locais(config)
            elif opcao == "5":
                listar_atendimentos_oficiais(config)
            pausar()
        else:
            print("Opcao invalida.")
            pausar()