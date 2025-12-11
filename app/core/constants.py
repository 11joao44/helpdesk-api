# app/core/bitrix_map.py

class BitrixFields:
    """
    Constantes com os IDs dos campos no Bitrix (ONDE salvar a informação).
    """
    # Campos de Texto
    PROTOCOL_NUMBER = "UF_CRM_1763556608"
    DESCRIPTION     = "UF_CRM_688788E6B494B"
    
    # Atenção: Campo do tipo 'employee' (vínculo com usuário do Bitrix)
    MATRICULA_USER_ID = "UF_CRM_1763994823" 

    # Campos de Lista (Enumeration)
    FILIAL        = "UF_CRM_665F6893CECAE"
    DEPARTAMENTO  = "UF_CRM_1763129004"
    SISTEMA       = "UF_CRM_67C9AA4AEA56A"
    PRIORIDADE    = "UF_CRM_1763744705"
    CATEGORIA     = "UF_CRM_1763995291"
    
    # Outros
    CLIENT_PHONE  = "UF_CRM_617728A6C16A5" # Verificar se é este mesmo
    ARQUIVO       = "UF_CRM_1763984364"


class BitrixValues:
    """
    Dicionários de Tradução: Front-end (Nome) -> Bitrix (ID da Opção).
    Copiado fielmente do seu mapeamento.
    """
    
    PRIORIDADE = {
        "Crítico/Emergencial": "1557",
        "Critico/Emergencial": "1557",
        "Crítico": "1557", # Caso o front mande simplificado
        "Alto/Urgente": "1559",
        "Alto": "1559",
        "Médio/Normal": "1561",
        "Médio": "1561",
        "Normal": "1561",
        "Baixo/Planejado": "1563",
        "Baixo": "1563"
    }

    SISTEMAS = {
        "SSW": "769",
        "Sacflow": "771",
        "Unitop": "773",
        "Bitrix": "775",
        "Automações": "1291",
        "Extensão": "1293",
        "Outros": "1295"
    }

    CATEGORIA = {
        "Interno": "1565",
        "Cliente PF": "1567",
        "Terceirizados": "1569",
        "Cliente PJ": "1571"
    }

    FILIAIS = {
        "Belém (BEL)": "1389",
        "Cuiabá (CGB)": "1391",
        "Campo Grande (CGR)": "1393",
        "Curitiba (CWB)": "1395",
        "Dourados (DRD)": "1397",
        "Ji Paraná (JIP)": "1399",
        "Joinville (JVE)": "1401",
        "Londrina (LDB)": "1403",
        "Navegantes (NGT)": "1405",
        "Porto Velho (PVH)": "1407",
        "Rio Branco (RBO)": "1409",
        "Rondonópolis (ROO)": "1411",
        "São Paulo (SAO)": "1413",
        "Vilhena (VHA)": "1415",
        "Matriz (MTZ)": "1417"
    }

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
        "Segurança e Monitoramento": "1377", # Variação comum
        "SESMT": "1379",
        "Parcerias": "1381",
        "Supervisão": "1383",
        "TI": "1385",
        "Trafego": "1387"
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