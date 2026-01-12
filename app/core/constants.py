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
    PORTAL        = "UF_CRM_1767887868"
    
    # Outros
    CLIENT_PHONE  = "UF_CRM_617728A6C16A5" # Verificar se é este mesmo
    ARQUIVO       = "UF_CRM_1763984364"

    ASSUNTO_MAP = {
        "775":  "UF_CRM_1763551486", # Bitrix
        "771":  "UF_CRM_1763551455", # Sacflow
        "769":  "UF_CRM_1763551374", # SSW
        "773":  "UF_CRM_1763551413", # Unitop
        "1291": "UF_CRM_1763551540", # Automações
        "1293": "UF_CRM_1763551616", # Extensão
    }


class BitrixValues:
    """
    Dicionários de Tradução: Front-end (Nome) -> Bitrix (ID da Opção).
    Copiado fielmente do seu mapeamento.
    """
    
    PRIORIDADE = {
        "Crítico/Emergencial": "1557",
        "Alto/Urgente": "1559",
        "Médio/Normal": "1561",
        "Baixo/Planejado": "1563",
    }

    PORTAL = {
        "E-mail": "1977",
        "Whatsapp": "1979",
        "Portal": "1981",
        "Sistema Próprio": "1983"
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

    ASSUNTO = {
        "SSW": {
            "Dúvidas": "1485",
            "Acessos e Permissões":"1487",
            "Redefinição de Senha":"1489",
            "Integração (EDI)":"1491",
            "Token de Acesso":"1493",
            "Bug e Falhas":"1495",
            "Melhorias":"1497",
        },
        "Unitop": {
          "Dúvidas":"1499",
          "Acessos e Permissões":"1501",
          "Redefinição de Senha":"1503",
          "Bug e Falhas":"1505",
          "Melhorias":"1507",
        },
        "Sacflow": {
            "Dúvidas":"1509",
            "Acessos e Permissões":"1511",
            "Redefinição de Senha":"1513",
            "Resposta Rápida":"1515",
            "Etiquetas":"1517",
            "Bug e Falhas":"1519",
            "Melhorias":"1521",
        },
        "Bitrix": {
            "Dúvidas":"1523",
            "Criação de Usuários":"1525",
            "Bug e Falhas":"1527",
            "Melhorias":"1529",
        },
        "Automações": {
            "Desenvolvimento":"1531",
            "Suporte à Automação":"1533",
        },
        "Extensão": {
            "Dúvidas":"1543",
            "Criação":"1545",
            "Suporte":"1547",
            "Outros": "1547" 
        }
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