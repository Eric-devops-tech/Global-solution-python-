# AstraCare Remote Health

Sistema em Python para apoio a decisao em telemedicina para regioes isoladas e ambientes extremos.

## Como executar

```bash
python main.py
```

Execute o comando dentro da pasta `astracare`.

## Funcionalidades

- Cadastro de pacientes ou tripulantes.
- Listagem e busca por ID.
- Registro de sinais vitais.
- Triagem de sintomas.
- Calculo automatico de risco clinico-operacional.
- Recomendacao de conduta inicial.
- Historico de atendimentos.
- Relatorios de risco e casos criticos.
- Gravacao de dados em JSON.
- Geracao de relatorio em TXT.
- Atualização de arquivos locais para o Banco de Dados
- Conexao demonstrativa com Oracle Database.

## Estrutura

- `main.py`: menu principal.
- `pacientes.py`: cadastro, listagem e busca.
- `atendimentos.py`: sinais vitais, sintomas, contexto e historico.
- `risco.py`: regras de pontuacao e recomendacoes.
- `relatorios.py`: resumo, casos criticos e TXT.
- `database_oracle.py`: teste de conexao, criacao de tabelas demonstrativas e consultas Oracle.
- `armazenamento.py`: leitura e gravacao de arquivos.
- `util.py`: funcoes auxiliares de entrada e formatacao.
- `dados/`: pasta criada automaticamente para persistencia local.

## Banco de dados Oracle

Para usar o menu de banco, instale o driver:

```bash
pip install oracledb
```

No sistema, acesse `Banco de Dados Oracle` para testar conexao, criar tabelas demonstrativas, inserir dados e listar atendimentos por JOIN.
