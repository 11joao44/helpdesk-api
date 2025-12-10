class BitrixFields:
    """
    Mapeamento COMPLETO de campos personalizados (User Fields - UF) do Bitrix24.
    Baseado no log de 2025.
    """

    # ==========================================
    # 1. IDs DOS CAMPOS (Chaves do Payload)
    # ==========================================

    # --- CAMPOS DE TEXTO/STRING CONFIRMADOS ---
    PROTOCOL_NUMBER = "UF_CRM_1763556608"  # String
    DESCRIPTION     = "UF_CRM_688788E6B494B"  # String (Texto Longo)
    
    # --- CAMPO DE VÍNCULO DE USUÁRIO (Employee) ---
    # Atenção: Este campo NÃO aceita texto "MAT-123". 
    # Ele espera o ID numérico de um usuário do Bitrix (ex: 5807).
    MATRICULA_USER_ID = "UF_CRM_1763994823" 

    # --- CAMPOS DE LISTA (Enumeration) ---
    FILIAL_FIELD      = "UF_CRM_665F6893CECAE" # Lista de Filiais
    DEPARTMENT_FIELD  = "UF_CRM_1763129004" # Lista de Departamentos
    SYSTEM_TYPE_FIELD = "UF_CRM_67C9AA4AEA56A" # Qual sistema? (SSW, Bitrix...)
    PRIORITY_FIELD    = "UF_CRM_1763744705"    # Urgente, Normal...
    SERVICE_CAT_FIELD = "UF_CRM_1763995291"    # Interno, Cliente PF...
    CLIENT_PHONE      = "UF_CRM_617728A6C16A5" # Telefone que o cliente preenche

    # --- CAMPOS DE ARQUIVO ---
    ATTACHMENT_FILE   = "UF_CRM_1763984364"
    
    # --- CAMPOS MISTERIOSOS (Candidatos ao Telefone) ---
    # Use estes no script "Detetive" para descobrir qual é qual
    UNKNOWN_STRING_2 = "UF_CRM_617728A6C7340"
    UNKNOWN_STRING_3 = "UF_CRM_617728A6CE335"
    UNKNOWN_STRING_4 = "UF_CRM_617728A6D6479"
    UNKNOWN_STRING_5 = "UF_CRM_DEAL_1688503774085"
    UNKNOWN_STRING_6 = "UF_CRM_1763131889"

    # ==========================================
    # 2. MAPAS REVERSOS (Label do Front -> ID do Bitrix)
    # ==========================================

    # --- PRIORIDADE ---
    PRIORITY_CATEGORY = { # Categoria de prioridade
        "Crítico/Emergencial": "1557",
        "Critico/Emergencial": "1557",
        "Alto/Urgente":        "1559",
        "Médio/Normal":        "1561",
        "Baixo/Planejado":     "1563"
    }

    # --- TIPO DE SISTEMA ---
    SYSTEM_TYPE_REVERSE = {
        "SSW":        "769",
        "Sacflow":    "771",
        "Unitop":     "773",
        "Bitrix":     "775",
        "Automações": "1291",
        "Extensão":   "1293",
        "Outros":     "1295"
    }

    # --- CATEGORIA DE ATENDIMENTO ---
    SERVICE_CAT_REVERSE = {
        "Interno":       "1565",
        "Cliente PF":    "1567",
        "Terceirizados": "1569",
        "Cliente PJ":    "1571"
    }

    # --- FILIAIS (Mapeamento Completo do Log) ---
    FILIAL_REVERSE = {
        "Belém (BEL)":        "1389",
        "Cuiabá (CGB)":       "1391",
        "Campo Grande (CGR)": "1393",
        "Curitiba (CWB)":     "1395",
        "Dourados (DRD)":     "1397",
        "Ji Paraná (JIP)":    "1399",
        "Joinville (JVE)":    "1401",
        "Londrina (LDB)":     "1403",
        "Navegantes (NGT)":   "1405",
        "Porto Velho (PVH)":  "1407",
        "Rio Branco (RBO)":   "1409",
        "Rondonópolis (ROO)": "1411",
        "São Paulo (SAO)":    "1413",
        "Vilhena (VHA)":      "1415",
        "Matriz (MTZ)":       "1417"
    }

    # --- DEPARTAMENTOS (Mapeamento Completo do Log) ---
    DEPARTMENT_REVERSE = {
        "Abastecimento":      "1301",
        "Administrativo":     "1303",
        "Almoxarifado":       "1305",
        "Armazém":            "1307",
        "Borracharia/Lavagem":"1309",
        "Carga":              "1311",
        "Coleta/Entrega":     "1313",
        "Coleta/Entrega ADM": "1315",
        "Comercial":          "1317",
        "Compras":            "1319",
        "Contabilidade":      "1321",
        "Controladoria":      "1323",
        "Controle":           "1325",
        "Coordenação":        "1327",
        "Crédito / Cobrança": "1329",
        "Descarga":           "1331",
        "Diretoria":          "1333",
        "Embarcadora":        "1335",
        "Expedição":          "1337",
        "Faturamento":        "1339",
        "Financeiro":         "1341",
        "Frota":              "1343",
        "Gerencia":           "1345",
        "Jurídico":           "1347",
        "Manutenção":         "1349",
        "Marketing":          "1351",
        "Mecânica":           "1353",
        "Motorista":          "1355",
        "NCE":                "1357",
        "Operacional":        "1359",
        "PCM":                "1361",
        "Pendencia":          "1363",
        "Presidência":        "1365",
        "Qualidade":          "1367",
        "Recepção":           "1369",
        "RH":                 "1371",
        "Redespacho":         "1373",
        "SAC":                "1375",
        "Segurança":          "1377", # Segurança e Monitoramento
        "SESMT":              "1379",
        "Parcerias":          "1381",
        "Supervisão":         "1383",
        "TI":                 "1385",
        "Trafego":            "1387"
    }