class BitrixFields:
    """Mapeamento de campos personalizados do Bitrix24."""

    # --- ID DOS CAMPOS (KEYS) ---
    PROTOCOL_NUMBER = "UF_CRM_1763556608"
    DESCRIPTION     = "UF_CRM_688788E6B494B"
    ATTACHMENT_FILE = "UF_CRM_1763984364"
    
    # Novos Campos (Identificados no seu Log)
    FILIAL_FIELD     = "UF_CRM_665F6893CECAE" # Filiais/Matriz
    DEPARTMENT_FIELD = "UF_CRM_1763129004" # Departamento (Qualidade, TI...)
    MATRICULA_FIELD  = "UF_CRM_1763994823" 
    
    # Estes você ainda precisa confirmar o código real:
    PHONE_FIELD      = "UF_CRM_TELEFONE_PENDENTE"
    
    # --- LISTAS (IDs DOS CAMPOS) ---
    SYSTEM_TYPE_FIELD = "UF_CRM_67C9AA4AEA56A" 
    PRIORITY_FIELD    = "UF_CRM_1763744705"    
    SERVICE_CAT_FIELD = "UF_CRM_1763995291"    

    # --- MAPAS REVERSOS (TEXTO DO FRONT -> ID DO BITRIX) ---
    SYSTEM_TYPE_REVERSE = {
        "SSW": "769",
        "Unitop": "773",
        "Sacflow": "771",
        "Bitrix": "775",
        "Automações": "1291",
        "Extensão": "1293",
        "Outros": "1295"
    }

    PRIORITY_REVERSE = {
        "Crítico/Emergencial": "1557",
        "Alto/Urgente": "1559",
        "Médio/Normal": "1561",
        "Baixo/Planejado": "1563",
        "Critico/Emergencial": "1557" # Fallback sem acento
    }

    SERVICE_CAT_REVERSE = {
        "Interno": "1565",
        "Cliente PF": "1567",
        "Cliente PJ": "1571",
        "Terceirizados": "1569"
    }

    # Adicionei com base no seu log (exemplo parcial)
    FILIAL_REVERSE = {
        "Matriz (MTZ)": "1417",
        "Cuiabá (CGB)": "1391",
        "São Paulo (SAO)": "1413"
    }

    DEPARTMENT_REVERSE = {
        "Qualidade": "1367",
        "TI": "1385",
        "Administrativo": "1303"
    }