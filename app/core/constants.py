# app/core/constants.py

class BitrixFields:
    """
    Constantes com os IDs dos campos no Bitrix (ONDE salvar a informação).
    Baseado no mapeamento.txt
    """
    # ==============================================================================
    # 📋 MAPA DE CAMPOS PERSONALIZADOS DO NEGÓCIO
    # ==============================================================================

    # 🔹 NOME: Saudação
    SAUDACAO = "UF_CRM_617728A6AC922" # enumeration

    # 🔹 NOME: Data de nascimento
    DATA_NASCIMENTO = "UF_CRM_617728A6BC4F9" # date

    # 🔹 NOME: Nome da empresa
    NOME_EMPRESA = "UF_CRM_617728A6C16A5" # string

    # 🔹 NOME: E-mail
    EMAIL = "UF_CRM_617728A6C7340" # string

    # 🔹 NOME: Website
    WEBSITE = "UF_CRM_617728A6CE335" # string

    # 🔹 NOME: Motivo de recusa
    MOTIVO_RECUSA = "UF_CRM_617728A6D6479" # string

    # 🔹 NOME: Motivo da Solicitação
    MOTIVO_SOLICITACAO = "UF_CRM_DEAL_1688503774085" # string

    # 🔹 NOME: Formato do evento
    FORMATO_EVENTO = "UF_CRM_WEBFORM_PARTICIPATION_FORMAT" # enumeration

    # 🔹 NOME: Data da Solicitação
    DATA_SOLICITACAO = "UF_CRM_DEAL_1688656820320" # date

    # 🔹 NOME: Agendamento de Reunião
    AGENDAMENTO_REUNIAO = "UF_CRM_1711044027933" # resourcebooking

    # 🔹 NOME: Reserva Sala Tangará
    RESERVA_SALA_TANGARA = "UF_CRM_1711044513298" # resourcebooking

    # 🔹 NOME: Filiais/Matriz (Enumeração principal de filiais)
    FILIAIS_MATRIZ = "UF_CRM_665F6893CECAE" # enumeration

    # 🔹 NOME: Tempo de empresa
    TEMPO_EMPRESA = "UF_CRM_668BF858C4A50" # enumeration

    # 🔹 NOME: A ideia que você vai sugerir atende os critérios...
    IDEIA_ATENDE_CRITERIOS = "UF_CRM_668BF858D64FA" # boolean

    # 🔹 NOME: Setores
    SETORES = "UF_CRM_67BE2B8667DCD" # enumeration

    # 🔹 NOME: Setores de Atendimento
    SETORES_ATENDIMENTO = "UF_CRM_67C9A75523CC2" # enumeration

    # 🔹 NOME: Tipo de Sistema
    TIPO_SISTEMA = "UF_CRM_67C9AA4AEA56A" # enumeration

    # 🔹 NOME: Opção de Suporte SSW
    OPCAO_SUPORTE_SSW = "UF_CRM_67C9AA7D8E550" # enumeration

    # 🔹 NOME: Selecione o tipo de solicitação (Processos)
    TIPO_SOLICITACAO_PROCESSOS = "UF_CRM_67C9ADA2081FE" # enumeration

    # 🔹 NOME: Selecione a Diretoria (Processos)
    DIRETORIA_PROCESSOS = "UF_CRM_67C9ADA214992" # enumeration

    # 🔹 NOME: Tipo de Solicitação (indicadores)
    TIPO_SOLICITACAO_INDICADORES = "UF_CRM_67C9ADE8A0FB5" # enumeration

    # 🔹 NOME: Tipo de Solicitação (Power BI)
    TIPO_SOLICITACAO_POWERBI = "UF_CRM_684C67EB95F68" # enumeration

    # 🔹 NOME: Tipos de Solicitação (Auditoria)
    TIPO_SOLICITACAO_AUDITORIA = "UF_CRM_684C6ACA2C145" # enumeration

    # 🔹 NOME: Tipos de Solicitações (Gestão de Resultados)
    TIPO_SOLICITACAO_GESTAO_RESULTADOS = "UF_CRM_684C6ACA3B527" # enumeration

    # 🔹 NOME: Tipos de Solicitações (Processos) (Duplicado nome, mas código diferente)
    TIPO_SOLICITACOES_PROCESSOS = "UF_CRM_684C6ACA469CC" # enumeration

    # 🔹 NOME: Tipos de Solicitações(Atutomação)
    TIPO_SOLICITACOES_AUTOMACAO = "UF_CRM_684C6ACA51960" # enumeration

    # 🔹 NOME: Descrição da Dúvida/Problemas
    DESCRICAO_DUVIDA_PROBLEMAS = "UF_CRM_688788E6B494B" # string
    DESCRIPTION = "UF_CRM_688788E6B494B" # Alias mantido

    # 🔹 NOME: Senha
    SENHA = "UF_CRM_6887931BBB945" # double

    # 🔹 NOME: ID de Usuário
    ID_USUARIO = "UF_CRM_DEAL_1763995667218" # double

    # 🔹 NOME: Ex: Aqui nós vamos falar sobre o material...
    DETALHES_MATERIAL = "UF_CRM_6938495533C9D" # string

    # 🔹 NOME: Área Solicitante
    AREA_SOLICITANTE = "UF_CRM_6938495549C8A" # string

    # 🔹 NOME: Selecione o documento da revisão
    DOCUMENTO_REVISAO = "UF_CRM_6938495555120" # enumeration

    # 🔹 NOME: Selecione o tipo de documento da Criação / Revisão
    TIPO_DOCUMENTO_CRIACAO_REVISAO = "UF_CRM_6938495564E1B" # enumeration

    # 🔹 NOME: Selecione o tipo de Solicitação
    SELECIONE_TIPO_SOLICITACAO = "UF_CRM_6938495572A1C" # enumeration

    # 🔹 NOME: Nome Colaborador
    NOME_COLABORADOR = "UF_CRM_693849557D1FC" # string

    # 🔹 NOME: FILIAIS (Outra lista de filiais)
    FILIAIS = "UF_CRM_6938495586A91" # enumeration

    # 🔹 NOME: A Ideia que vai sugerir ainda nao foi implantada na empresa?
    IDEIA_NAO_IMPLANTADA = "UF_CRM_693849559267E" # boolean

    # 🔹 NOME: Tipo de Solicitação suporte
    TIPO_SOLICITACAO_SUPORTE = "UF_CRM_693849559AD59" # enumeration

    # 🔹 NOME: Novo Usuario
    NOVO_USUARIO = "UF_CRM_69384955A65E7" # string

    # 🔹 NOME: Tipo de Solicitações (Sistemas)
    TIPO_SOLICITACOES_SISTEMAS = "UF_CRM_69384955B043E" # enumeration

    # 🔹 NOME: Tipo de Solicitação
    TIPO_SOLICITACAO_GENERICO_1 = "UF_CRM_69384955B9FD2" # enumeration

    # 🔹 NOME: Tipo de Solicitação (SISTEMAS)
    TIPO_SOLICITACAO_SISTEMAS_TESTE = "UF_CRM_69384955C5B46" # enumeration

    # 🔹 NOME: Tipo (Genérico)
    TIPO_GENERICO = "UF_CRM_69384955D3083" # enumeration

    # 🔹 NOME: Tipo de Solicitação (Lista longa)
    TIPO_SOLICITACAO_LISTA_LONGA = "UF_CRM_6939B7F6307BF" # enumeration

    # 🔹 NOME: Motivo da pausa na utilização de serviços
    MOTIVO_PAUSA_SERVICOS = "UF_CRM_1765811440" # enumeration

    # 🔹 NOME: Pretende voltar a usar nosso serviço?
    PRETENDE_VOLTAR = "UF_CRM_1765811752" # enumeration

    # 🔹 NOME: O que o motivaria a voltar a usar nosso serviço?
    MOTIVACAO_VOLTAR = "UF_CRM_1765811931" # string

    # 🔹 NOME: Como você avalia a pontualidade das nossas entregas?
    AVALIACAO_PONTUALIDADE = "UF_CRM_DEAL_1765812342123" # enumeration

    # 🔹 NOME: Como você avalia a comunicação e acompanhamento dos pedidos?
    AVALIACAO_COMUNICACAO = "UF_CRM_DEAL_1765812418625" # enumeration

    # 🔹 NOME: Quais são os maiores desafios ou dificuldades...
    DESAFIOS_LOGISTICOS = "UF_CRM_DEAL_1765812484921" # string

    # 🔹 NOME: Qual foi o principal motivo para você parar de transportar conosco?
    MOTIVO_PARADA = "UF_CRM_1765816104" # enumeration

    # 🔹 NOME: O que seria fundamental melhorarmos...
    MELHORIAS_FUNDAMENTAIS = "UF_CRM_1765816150" # string

    # 🔹 NOME: Em uma escala de 0 a 10...
    NPS_INDICACAO = "UF_CRM_1765816206" # enumeration

    # 🔹 NOME: Responsável secundário
    RESPONSAVEL_SECUNDARIO = "UF_CRM_1765825343" # employee

    # 🔹 NOME: Lead Time
    LEAD_TIME_ARQUIVO = "UF_CRM_1765830399" # file

    # 🔹 NOME: Anexo Complemento
    ANEXO_COMPLEMENTO = "UF_CRM_DEAL_1766493229984" # file

    # 🔹 NOME: Informações Complementares
    INFORMACOES_COMPLEMENTARES = "UF_CRM_DEAL_1766493564784" # string

    # 🔹 NOME: Forma de Criação
    FORMA_CRIACAO = "UF_CRM_1766502007" # enumeration

    # 🔹 NOME: CPF (Usado também lá embaixo, verificar código)
    CPF_DEAL = "UF_CRM_DEAL_1766504470926" # string

    # 🔹 NOME: TAG Vendas Interno|Externo
    TAG_VENDAS = "UF_CRM_1767618757" # enumeration

    # 🔹 NOME: Prazo Etapa Atual
    PRAZO_ETAPA_ATUAL = "UF_CRM_1767619293" # date

    # 🔹 NOME: TAG
    TAG_ARQUIVO = "UF_CRM_1767788422" # file

    # 🔹 NOME: Motivo de Perda
    MOTIVO_PERDA = "UF_CRM_1767886114" # enumeration

    # 🔹 NOME: TAG BID/NCE
    TAG_BID_NCE = "UF_CRM_1767903445" # enumeration

    # 🔹 NOME: Departamento
    DEPARTAMENTO = "UF_CRM_1763129004" # enumeration

    # 🔹 NOME: Arquivo
    ARQUIVO = "UF_CRM_1763131061" # file

    # 🔹 NOME: Descrição do Requisitos
    DESCRICAO_REQUISITOS = "UF_CRM_1763131889" # string

    # 🔹 NOME: Arquivo de Requisitos
    ARQUIVO_REQUISITOS = "UF_CRM_1763131919" # file

    # 🔹 NOME: Menu: SSW
    MENU_SSW = "UF_CRM_1763551374" # enumeration

    # 🔹 NOME: Menu: UNITOP
    MENU_UNITOP = "UF_CRM_1763551413" # enumeration

    # 🔹 NOME: Menu: SACFLOW
    MENU_SACFLOW = "UF_CRM_1763551455" # enumeration

    # 🔹 NOME: Menu: BITRIX
    MENU_BITRIX = "UF_CRM_1763551486" # enumeration

    # 🔹 NOME: Menu: AUTOMAÇÕES
    MENU_AUTOMACOES = "UF_CRM_1763551540" # enumeration

    # 🔹 NOME: Submenu: AUTOMAÇÕES
    SUBMENU_AUTOMACOES = "UF_CRM_1763551582" # enumeration

    # 🔹 NOME: Menu: EXTENSÃO
    MENU_EXTENSAO = "UF_CRM_1763551616" # enumeration

    # 🔹 NOME: Submenu: EXTENSÃO
    SUBMENU_EXTENSAO = "UF_CRM_1763551642" # enumeration

    # 🔹 NOME: Atendente suporte
    ATENDENTE_SUPORTE = "UF_CRM_1763553730" # employee

    # 🔹 NOME: Protocolo
    PROTOCOLO = "UF_CRM_1763556608" # string
    PROTOCOL_NUMBER = "UF_CRM_1763556608" # Alias mantido

    # 🔹 NOME: Categoria de prioridade
    CATEGORIA_PRIORIDADE = "UF_CRM_1763744705" # enumeration
    PRIORIDADE = "UF_CRM_1763744705" # Alias mantido

    # 🔹 NOME: Status (É um arquivo no bitrix?)
    STATUS_ARQUIVO = "UF_CRM_1763984364" # file

    # 🔹 NOME: Prazo do Atendimento
    PRAZO_ATENDIMENTO = "UF_CRM_1763985609" # datetime
    PRAZO = "UF_CRM_1763985609" # Alias mantido

    # 🔹 NOME: Colaborador Interno
    COLABORADOR_INTERNO = "UF_CRM_1763994823" # employee
    MATRICULA_FORM = "UF_CRM_1763994823" # Alias mantido (verificar uso, parece ser colaborador)

    # 🔹 NOME: Categoria de atendimento
    CATEGORIA_ATENDIMENTO = "UF_CRM_1763995291" # enumeration
    CATEGORIA = "UF_CRM_1763995291" # Alias mantido

    # 🔹 NOME: Cliente aceitou a proposta?
    CLIENTE_ACEITOU_PROPOSTA = "UF_CRM_1765456978" # enumeration

    # 🔹 NOME: Identificou a expansão?
    IDENTIFICOU_EXPANSAO = "UF_CRM_1765457042" # enumeration

    # 🔹 NOME: Cliente expandiu?
    CLIENTE_EXPANDIU = "UF_CRM_1765457077" # enumeration

    # 🔹 NOME: Anexo: Proposta
    ANEXO_PROPOSTA = "UF_CRM_1765457341" # file

    # 🔹 NOME: Motivo da perda (String, diferente do enumeration acima)
    MOTIVO_PERDA_TEXTO = "UF_CRM_1765457498" # string

    # 🔹 NOME: Oportunidade identificada
    OPORTUNIDADE_IDENTIFICADA = "UF_CRM_1765457745" # enumeration

    # 🔹 NOME: Data na etapa atual
    DATA_ETAPA_ATUAL = "UF_CRM_1765478001" # date

    # 🔹 NOME: Prazo (Arquivo)
    PRAZO_ARQUIVO = "UF_CRM_1765478474" # file

    # 🔹 NOME: Cliente é grupo?
    CLIENTE_E_GRUPO = "UF_CRM_1765480867" # enumeration

    # 🔹 NOME: Qual CNPJ vai expandir?
    CNPJ_EXPANSAO = "UF_CRM_1765480889" # string

    # 🔹 NOME: Particularidades do Cliente
    PARTICULARIDADES_CLIENTE = "UF_CRM_1765480909" # string

    # 🔹 NOME: Qual é o valor médio mensal do faturamento deste cliente?
    FATURAMENTO_MEDIO = "UF_CRM_1765480945" # money

    # 🔹 NOME: Qual o motivo que impulsiona a expansão...
    MOTIVO_EXPANSAO = "UF_CRM_1765480973" # string

    # 🔹 NOME: Quais estados/UF o cliente pretende expandir conosco?
    UF_EXPANSAO = "UF_CRM_1765480996" # string

    # 🔹 NOME: Quais Novas Rotas o cliente tem interesse em realizar expansão?
    ROTAS_EXPANSAO = "UF_CRM_1765481016" # string

    # 🔹 NOME: Quais serviços Carvalima o cliente possui interesse para Expansão?
    SERVICOS_EXPANSAO = "UF_CRM_1765481033" # string

    # 🔹 NOME: Tipo de Oportunidade
    TIPO_OPORTUNIDADE = "UF_CRM_1767720717" # enumeration

    # 🔹 NOME: CPF (Outro código)
    CPF = "UF_CRM_1767788193" # string

    # 🔹 NOME: Número Cliente Estratégico
    NUMERO_CLIENTE_ESTRATEGICO = "UF_CRM_1767887268" # string

    # 🔹 NOME: Qual a abrangência contratada inicialmente?
    ABRANGENCIA_INICIAL = "UF_CRM_1767887452" # enumeration

    # 🔹 NOME: Qual é a estimativa de volumetria...
    ESTIMATIVA_VOLUMETRIA = "UF_CRM_1767887564" # enumeration

    # 🔹 NOME: CNPJ PAGADOR CGB
    CNPJ_PAGADOR_CGB = "UF_CRM_1767887715" # crm

    # 🔹 NOME: CNPJ INTEGRAÇÃO SISTEMICA
    CNPJ_INTEGRACAO = "UF_CRM_1767887734" # crm

    # 🔹 NOME: Qual o segmento da empresa?
    SEGMENTO_EMPRESA = "UF_CRM_1767887766" # string

    # 🔹 NOME: Qual o canal para comunicação?
    CANAL_COMUNICACAO = "UF_CRM_1767887868" # enumeration
    PORTAL = "UF_CRM_1767887868" # Alias mantido

    # Manter CONSTANTES antigas para compatibilidade se não conflitarem
    UNIDADE = "UF_CRM_1767978730" # Não achei no novo map, mantendo por segurança
    CLIENT_PHONE  = "UF_CRM_617728A6C16A5" # Verificar se é este mesmo (NOME_EMPRESA no novo map, conflito? mantendo comentado ou revisar)
    # UF_CRM_617728A6C16A5 no map novo é "Nome da empresa".
    # Vou manter CLIENT_PHONE apontando para o que estava antes mas cuidado.
    
    ASSUNTO_MAP = {
        "775":  "UF_CRM_1763551486", # Bitrix (MENU_BITRIX)
        "771":  "UF_CRM_1763551455", # Sacflow (MENU_SACFLOW)
        "769":  "UF_CRM_1763551374", # SSW (MENU_SSW)
        "773":  "UF_CRM_1763551413", # Unitop (MENU_UNITOP)
        "1291": "UF_CRM_1763551540", # Automações (MENU_AUTOMACOES)
        "1293": "UF_CRM_1763551616", # Extensão (MENU_EXTENSAO)
    }


class BitrixValues:
    """
    Dicionários de Tradução: Front-end (Nome) -> Bitrix (ID da Opção).
    """
    
    # 🔹 Saudação
    SAUDACAO = {
        "Sr.": "44",
        "Sra.": "46",
        "Srta.": "48",
        "Dr.": "50",
    }

    # 🔹 Formato do evento
    FORMATO_EVENTO = {
        "Virtual (online)": "174",
        "Pessoalmente": "176",
        "Vou assistir à transmissão gravada": "178",
    }

    # 🔹 Filiais/Matriz
    FILIAIS_MATRIZ = {
        "BEL": "1389", "Belém (BEL)": "1389",
        "CGB": "1391", "Cuiabá (CGB)": "1391",
        "CGR": "1393", "Campo Grande (CGR)": "1393",
        "CWB": "1395", "Curitiba (CWB)": "1395",
        "DRD": "1397", "Dourados (DRD)": "1397",
        "JIP": "1399", "Ji Paraná (JIP)": "1399",
        "JVE": "1401", "Joinville (JVE)": "1401",
        "LDB": "1403", "Londrina (LDB)": "1403",
        "NGT": "1405", "Navegantes (NGT)": "1405",
        "PVH": "1407", "Porto Velho (PVH)": "1407",
        "RBO": "1409", "Rio Branco (RBO)": "1409",
        "ROO": "1411", "Rondonópolis (ROO)": "1411",
        "SAO": "1413", "São Paulo (SAO)": "1413",
        "VHA": "1415", "Vilhena (VHA)": "1415",
        "MTZ": "1417", "Matriz (MTZ)": "1417",
    }
    # Alias para compatibilidade
    FILIAIS = FILIAIS_MATRIZ

    # 🔹 Tempo de empresa
    TEMPO_EMPRESA = {
        "0 á 6 Meses": "339", # Note: 'á' as per file
        "6 Meses a 1 ano": "341",
        "1 ano a 4 anos": "343",
        "Acima de 5 anos": "345",
    }

    # 🔹 Setores
    SETORES = {
        "Processos": "737",
        "Auditoria": "739",
        "Controller": "741",
        "Automações": "743",
        "Suporte Sistemas": "745",
        "Power BI": "747",
    }

    # 🔹 Setores de Atendimento
    SETORES_ATENDIMENTO = {
        "Auditoria": "749",
        "Automação": "751",
        "Gestão de Resultados": "753",
        "Power BI": "755",
        "Processos": "757",
        "Suporte Sistemas": "759",
    }

    # 🔹 Tipo de Sistema
    # Usado em BitrixValues.SISTEMAS antigo
    SISTEMAS = {
        "SSW": "769",
        "Unitop": "773",
        "Sacflow": "771",
        "Bitrix": "775",
        "Automações": "1291",
        "Extensão": "1293",
        "Outros": "1295",
    }
    TIPO_SISTEMA = SISTEMAS

    # 🔹 Opção de Suporte SSW
    OPCAO_SUPORTE_SSW = {
        "EDI": "785",
        "Extensão": "787",
        "Opções SSW": "789",
        "Outros": "791",
    }

    # 🔹 Selecione o tipo de solicitação (Processos)
    TIPO_SOLICITACAO_PROCESSOS = {
        "Documentação": "809",
        "Solicitação de Atualização/Revisão": "811",
        "Revisão": "813",
        "Dúvidas": "815",
    }

    # 🔹 Selecione a Diretoria (Processos)
    DIRETORIA_PROCESSOS = {
        "Comercial": "817",
        "Logística e Operação": "819",
        "Rede de Negócios": "821",
        "Administrativa": "823",
    }

    # 🔹 Tipo de Solicitação (indicadores)
    TIPO_SOLICITACAO_INDICADORES = {
        "Prémio Superação": "831",
        "PPR": "833",
        "Dúvidas": "835",
    }

    # 🔹 Tipo de Solicitação (Power BI)
    TIPO_SOLICITACAO_POWERBI = {
        "teste1": "941",
        "teste2": "943",
        "teste3": "945",
    }

    # 🔹 Tipos de  Solicitação (Auditoria)
    TIPO_SOLICITACAO_AUDITORIA = {
        "teste1": "977",
        "teste2": "979",
        "teste3": "981",
    }

    # 🔹 Tipos de Solicitações (Gestão de Resultados)
    TIPO_SOLICITACAO_GESTAO_RESULTADOS = {
        "teste1": "983",
        "teste2": "985",
        "teste3": "987",
    }

    # 🔹 Tipos de Solicitações (Processos)
    TIPO_SOLICITACOES_PROCESSOS = {
        "teste1": "989",
        "teste2": "991",
        "teste3": "993",
    }

    # 🔹 Tipos de Solicitações(Atutomação)
    TIPO_SOLICITACOES_AUTOMACAO = {
        "teste1": "995",
        "teste2": "997",
        "teste3": "999",
    }

    # 🔹 Selecione o documento da revisão
    DOCUMENTO_REVISAO = {
        "Politica": "1597",
        "Procedimento": "1599",
        "Instrução de Trabalho": "1601",
        "Formulário": "1603",
    }

    # 🔹 Selecione o tipo de documento da Criação / Revisão
    TIPO_DOCUMENTO_CRIACAO_REVISAO = {
        "Politica": "1605",
        "Procedimentos": "1607",
        "Instrução de Trabalho": "1609",
        "Formulário": "1611",
    }

    # 🔹 Selecione o tipo de Solicitação
    SELECIONE_TIPO_SOLICITACAO = {
        "Criação": "1613",
        "Revisõ": "1615",
    }

    # 🔹 FILIAIS (Campo secundário de filiais - UF_CRM_6938495586A91)
    FILIAIS_SECUNDARIO = {
        "CGR": "1617",
        "CGB": "1619",
        "DRD": "1621",
        "SAO": "1623",
        "ROO": "1625",
        "RBO": "1627",
        "PVH": "1629",
        "JIP": "1631",
        "VHA": "1633",
        "CWB": "1635",
        "JVE": "1637",
        "NGT": "1639",
        "LDB": "1641",
        "MTZ": "1643",
        "UNIDADES": "1845",
    }

    # 🔹 Tipo de Solicitação suporte
    TIPO_SOLICITACAO_SUPORTE = {
        "SSW": "1645",
        "Sacflow": "1647",
        "Unitop": "1649",
        "Bitrix": "1651",
    }

    # 🔹 Tipo de Solicitações (Sistemas)
    TIPO_SOLICITACOES_SISTEMAS = {
        "Criação Usuário": "1653",
        "Bloqueio / Desbloqueio": "1655",
        "Integração (EDI)": "1657",
        "Demais Suporte": "1659",
    }

    # 🔹 Tipo de Solicitação
    TIPO_SOLICITACAO_GENERICO_1 = {
         "Dúvida/Problemas": "1661",
         "Treinamento": "1663",
         "Solicitação de Melhorias": "1665",
         "BUG": "1667",
    }

    # 🔹 Tipo de Solicitação (SISTEMAS) (Teste)
    TIPO_SOLICITACAO_SISTEMAS_TESTE = {
        "TESTE": "1669",
    }

    # 🔹 Tipo (Genérico)
    TIPO_GENERICO = {
        "Dúvida/Problemas": "1671",
        "BUG": "1673",
        "Melhorias": "1675",
        "Treinamento": "1677",
    }

    # 🔹 Tipo de Solicitação (Lista Longa)
    TIPO_SOLICITACAO_LISTA_LONGA = {
        "SSW-Desbloqueio de senha": "1679",
        "SSW-Envio do Token": "1681",
        "SSW-Suporte Dúvidas": "1683",
        "SSW-EDI": "1685",
        "SSW-Extensão": "1687",
        "Dúvidas (Atendimento)": "1689",
        "Bug (Erro) no Sistema": "1691",
        "Melhorias (Customização)": "1693",
        "Treinamento": "1695",
        "Documentação do Setor": "1697",
        "Auditoria": "1699",
        "Gestão de Indicadores": "1701",
    }

    # 🔹 Motivo da pausa na utilização de serviços
    MOTIVO_PAUSA_SERVICOS = {
        "O serviço não atendeu as suas expectativas?": "1741",
        "Neste momento o custo do serviço se tornou inviável?": "1743",
        "O serviço não estava mais sendo necessário para a empresa?": "1745",
        "Atualmente transporta com outra empresa?": "1747",
        "Outro": "1749",
    }

    # 🔹 Pretende voltar a usar nosso serviço?
    PRETENDE_VOLTAR = {
        "Sim": "1751",
        "Não": "1753",
    }

    # 🔹 Como você avalia a pontualidade das nossas entregas?
    AVALIACAO_PONTUALIDADE = {
        "Excelente": "1755",
        "Boa": "1757",
        "Regular": "1759",
        "Ruim": "1761",
    }

    # 🔹 Como você avalia a comunicação e acompanhamento dos pedidos?
    AVALIACAO_COMUNICACAO = {
        "Excelente": "1763",
        "Boa": "1765",
        "Regular": "1767",
        "Ruim": "1769",
    }

    # 🔹 Qual foi o principal motivo para você parar de transportar conosco?
    MOTIVO_PARADA = {
        "Valor do Frete / Condições comerciais": "1787",
        "Pagamentos": "1789",
        "Prazo de coleta ou entrega": "1791",
        "Qualidade no atendimento": "1793",
        "Problemas operacionais (ex: extravios, avarias ou atrasos)": "1795",
        "Falta de acompanhamento/ comunicação": "1797",
        "Migrei para outro parceiro": "1799",
    }

    # 🔹 Em uma escala de 0 a 10...
    NPS_INDICACAO = {
        "0": "1801",
        "1": "1803",
        "2": "1805",
        "3": "1807",
        "4": "1809",
        "5": "1811",
        "6": "1813",
        "7": "1815",
        "8": "1817",
        "9": "1819",
        "10": "1821",
    }

    # 🔹 Forma de Criação
    FORMA_CRIACAO = {
        "Automática": "1825",
        "Manual": "1827",
    }

    # 🔹 TAG Vendas Interno|Externo
    TAG_VENDAS = {
        "Ampliado": "1833",
        "Queda": "1835",
        "Churn": "1837",
        "Reativado": "1839",
        "Cliente Novo": "1853",
        "Cliente Ativo": "1855",
    }

    # 🔹 Motivo de Perda
    MOTIVO_PERDA = {
        "Rota parceira": "1877",
        "Rota não atendida": "1879",
        "Não é ICP": "1881",
        "Preço alto": "1883",
        "SLA não atende": "1885",
        "Reajuste não aceito": "1887",
        "Risco jurídico": "1889",
        "Risco Operacional": "1891",
        "Risco financeiro": "1893",
        "Outro": "1895",
    }

    # 🔹 TAG BID/NCE
    TAG_BID_NCE = {
        "Indicação": "2143",
        "Contato Dir.": "2145",
        "Novos Negócios": "2147",
        "Expansão": "2149",
        "Risco": "2151",
        "TOM": "2153",
        "Artemis": "2155",
        "Jamerson": "2157",
        "Matheus": "2159",
        "Diretoria": "2161",
        "Receptivo": "2163",
        "Ativo": "2165",
    }

    # 🔹 Departamento
    DEPARTAMENTOS = {
        "Abastecimento": "1301",
        "Administrativo": "1303",
        "Almoxarifado": "1305",
        "Armazém": "1307",
        "Borracharia/Lavagem": "1309",
        "Carga": "1311",
        "Coleta/Entrega": "1313",
        "Coleta/Entrega ADM": "1315",
        "Comercial": "1317",
        "Compras": "1319",
        "Contabilidade": "1321",
        "Controladoria": "1323",
        "Controle": "1325",
        "Coordenação": "1327",
        "Crédito / Cobrança": "1329",
        "Descarga": "1331",
        "Diretoria": "1333",
        "Embarcadora": "1335",
        "Expedição": "1337",
        "Faturamento": "1339",
        "Financeiro": "1341",
        "Frota": "1343",
        "Gerencia": "1345",
        "Jurídico": "1347",
        "Manutenção": "1349",
        "Marketing": "1351",
        "Mecânica": "1353",
        "Motorista": "1355",
        "NCE": "1357",
        "Operacional": "1359",
        "PCM": "1361",
        "Pendencia": "1363",
        "Presidência": "1365",
        "Qualidade": "1367",
        "Recepção": "1369",
        "RH": "1371",
        "Redespacho": "1373",
        "SAC": "1375",
        "Segurança": "1377",
        "Segurança e Monitoramento": "1377",
        "SESMT": "1379",
        "Parcerias": "1381",
        "Supervisão": "1383",
        "TI": "1385",
        "Trafego": "1387",
    }
    DEPARTAMENTO = DEPARTAMENTOS # Alias

    # 🔹 Menu: SSW
    MENU_SSW = {
        "Dúvidas": "1485",
        "Acessos e Permissões": "1487",
        "Redefinição de Senha": "1489",
        "Integração (EDI)": "1491",
        "Token de Acesso": "1493",
        "Bug e Falhas": "1495",
        "Melhorias": "1497",
    }

    # 🔹 Menu: UNITOP
    MENU_UNITOP = {
        "Dúvidas": "1499",
        "Acessos e Permissões": "1501",
        "Redefinição de Senha": "1503",
        "Bug e Falhas": "1505",
        "Melhorias": "1507",
    }

    # 🔹 Menu: SACFLOW
    MENU_SACFLOW = {
        "Dúvidas": "1509",
        "Acessos e Permissões": "1511",
        "Redefinição de Senha": "1513",
        "Resposta Rápida": "1515",
        "Etiquetas": "1517",
        "Bug e Falhas": "1519",
        "Melhorias": "1521",
    }

    # 🔹 Menu: BITRIX
    MENU_BITRIX = {
        "Dúvidas": "1523",
        "Criação de Usuários": "1525",
        "Bug e Falhas": "1527",
        "Melhorias": "1529",
    }

    # 🔹 Menu: AUTOMAÇÕES
    MENU_AUTOMACOES = {
        "Desenvolvimento": "1531",
        "Suporte à Automação": "1533",
    }

    # 🔹 Submenu: AUTOMAÇÕES
    SUBMENU_AUTOMACOES = {
        "Ajuste": "1535",
        "Acesso": "1537",
        "Melhoria": "1539",
        "Treinamento": "1541",
    }

    # 🔹 Menu: EXTENSÃO
    MENU_EXTENSAO = {
        "Dúvidas": "1543",
        "Criação": "1545",
        "Suporte": "1547",
    }

    # 🔹 Submenu: EXTENSÃO
    SUBMENU_EXTENSAO = {
        "Acesso": "1549",
        "Correção Técnica": "1551",
        "Bug e Falhas": "1553",
        "Melhoria": "1555",
    }

    # 🔹 Categoria de prioridade
    CATEGORIA_PRIORIDADE = {
        "Critico/Emergencial": "1557", "Crítico/Emergencial": "1557",
        "Alto/Urgente": "1559",
        "Médio/Normal": "1561", "Medio/Normal": "1561",
        "Baixo/Planejado": "1563",
    }
    PRIORIDADE = CATEGORIA_PRIORIDADE # Alias

    # 🔹 Categoria de atendimento
    CATEGORIA_ATENDIMENTO = {
        "Interno": "1565",
        "Cliente PF": "1567",
        "Cliente PJ": "1571",
        "Terceirizados": "1569",
    }
    CATEGORIA = CATEGORIA_ATENDIMENTO # Alias

    # 🔹 Cliente aceitou a proposta?
    CLIENTE_ACEITOU_PROPOSTA = {
        "Sim": "1703",
        "Não": "1705",
    }

    # 🔹 Identificou a expansão?
    IDENTIFICOU_EXPANSAO = {
        "Sim": "1707",
        "Não": "1709",
    }

    # 🔹 Cliente expandiu?
    CLIENTE_EXPANDIU = {
        "Sim": "1711",
        "Não": "1713",
    }

    # 🔹 Oportunidade identificada
    OPORTUNIDADE_IDENTIFICADA = {
        "Upsell": "1715",
        "Cross-sell": "1717",
        "Renegociação": "1719",
    }

    # 🔹 Cliente é grupo?
    CLIENTE_E_GRUPO = {
        "Sim": "1721",
        "Não": "1723",
    }

    # 🔹 Tipo de Oportunidade
    TIPO_OPORTUNIDADE = {
        "Oportunidade Reversão": "1849",
        "Oportunidade Prospecção": "1851",
    }

    # 🔹 Qual a abrangência contratada inicialmente?
    ABRANGENCIA_INICIAL = {
        "MT": "1961",
        "MS": "1963",
        "AC": "1965",
        "RO": "1967",
        "PA": "1969",
        "OUTRA?": "1971",
    }

    # 🔹 Qual é a estimativa de volumetria para as coletas diárias?
    ESTIMATIVA_VOLUMETRIA = {
        "Média de pedidos por mês: 5mil": "1973",
        "Média de pedidos por dia: 254": "1975",
    }

    # 🔹 Qual o canal para comunicação? (Portal)
    CANAL_COMUNICACAO = {
        "E-mail": "1977", # Não estava no txt mas deduzi pela logica do antigo constants ou vou deixar comentado se nao tiver ID no txt.
        # Opa, no txt não tem os IDs de email/whatsapp claramente na seção PORTAL (ID 1767887868), só tem o titulo.
        # Espera, o antigo constants tinha:
        # "E-mail": "1977", "Whatsapp": "1979", "Portal": "1981", "Sistema Próprio": "1983"
        # No txt novo, o campo "Qual o canal para comunicação?" (UF_CRM_1767887868) do final do arquivo não lista opções!
        # Mas assumindo que o antigo estava certo, vou manter.
    }
    PORTAL = {
        "E-mail": "1977",
        "Whatsapp": "1979",
        "Portal": "1981",
        "Sistema Próprio": "1983"
    }

    # ASSUNTO MAP COMPOSTO (Mantendo logica antiga com novos nomes de variaveis)
    ASSUNTO = {
        "SSW": MENU_SSW,
        "Unitop": MENU_UNITOP,
        "Sacflow": MENU_SACFLOW,
        "Bitrix": MENU_BITRIX,
        "Automações": MENU_AUTOMACOES,
        "Extensão": MENU_EXTENSAO,
        "Outros": {"Outros": "1547"} # Fallback do antigo map
    }

    @staticmethod
    def get_id(mapping: dict, value: str | None) -> str:
        """
        Busca segura:
        1. Se value for None, retorna vazio.
        2. Tenta busca exata.
        3. Se falhar, tenta buscar ignorando maiúsculas/minúsculas.
        """
        if not value:
            return ""
        
        # 1. Busca Exata (Rápida)
        if value in mapping:
            return mapping[value]
            
        # 2. Busca Insensível (Lenta, mas robusta)
        val_lower = value.lower().strip()
        for key, id_bitrix in mapping.items():
            if key.lower().strip() == val_lower:
                return id_bitrix
        
        print(f"⚠️ [BitrixMapper] Valor não encontrado no mapa: '{value}'")
        return ""
    
    @staticmethod
    def get_label(mapping: dict, id_bitrix: str | None) -> str:
        """
        Busca reversa: Dado um ID do Bitrix, retorna o LABEL (Chave).
        Ex: '1561' -> 'Médio/Normal'
        """
        if not id_bitrix:
             return ""
        
        # Procura pelo ID no dicionário
        for key, val in mapping.items():
             if val == id_bitrix:
                 return key # Retorna a primeira chave encontrada
        
        return str(id_bitrix) # Fallback: Retorna o próprio ID se não achar

    @staticmethod
    def get_subject_id(system_name: str, subject_name: str) -> str:
        if not system_name or not subject_name: return ""
        
        system_key_found = None
        if system_name in BitrixValues.ASSUNTO:
            system_key_found = system_name
        else:
            s_lower = system_name.lower().strip()
            for key in BitrixValues.ASSUNTO.keys():
                if key.lower().strip() == s_lower:
                    system_key_found = key
                    break
        
        if not system_key_found:
            return ""

        mapa_assuntos = BitrixValues.ASSUNTO[system_key_found]
        return BitrixValues.get_id(mapa_assuntos, subject_name)