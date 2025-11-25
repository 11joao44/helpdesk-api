from httpx import AsyncClient
from typing import List, Dict, Any
from app.core.config import settings, logger

class BitrixProvider:
    """
    Centraliza todas as chamadas para o Bitrix24.
    Segue estritamente as regras de negócio (validações) do Bitrix.
    """
    def __init__(self):
        self.webhook_url = settings.BITRIX_WEBHOOK_URL
        self.timeout = settings.TIMEOUT_REQUEST
        
        self.status_map = {
            "2": "Pendente",
            "3": "Em Andamento",
            "4": "Aguardando Controle",
            "5": "Concluído",
            "6": "Adiado"
        }

    async def _request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Método interno genérico para fazer o POST no Bitrix com tratamento de erro"""
        async with AsyncClient(base_url=self.webhook_url, timeout=self.timeout) as client:
            try:
                response = await client.post(f"/{method}.json", json=params)
                response.raise_for_status()
                data = response.json()
                
                if "error" in data:
                    raise Exception(f"Bitrix API Error: {data['error_description']}")
                    
                return data
            except Exception as e:
                logger.error(f"Erro de conexão com Bitrix: {e}")
                raise e

    async def create_task(self, title: str, description: str, requester_id: int) -> Dict[str, Any]:
        """
        Cria uma tarefa no Bitrix.
        Regra de Negócio: O 'requester_id' deve ser um ID válido no Bitrix.
        """
        payload = {
            "fields": {
                "TITLE": title,
                "DESCRIPTION": description,
                "CREATED_BY": requester_id,
                "RESPONSIBLE_ID": 1,  # Por enquanto, Admin é o responsável
                "PRIORITY": "1",      # 1 = Média
                "STATUS": "2",        # 2 = Pendente (Coluna inicial do Kanban)
                "TAGS": ["Helpdesk"], # Tag para filtrar depois
                "ALLOW_CHANGE_DEADLINE": "N"
            }
        }
        
        result = await self._request("tasks.task.add", payload)
        return {
            "bitrix_id": result['result']['task']['id'],
            "link": f"/company/personal/user/0/tasks/task/view/{result['result']['task']['id']}/"
        }

    async def get_kanban_tasks(self) -> Dict[str, List[Dict]]:
        """
        Busca todas as tarefas para montar o Kanban.
        Retorna organizado por colunas (Status).
        """
        payload = {
            "filter": {"TAG": "Helpdesk"}, 
            "select": ["ID", "TITLE", "STATUS", "RESPONSIBLE_ID", "DEADLINE", "PRIORITY"],
            "order": {"ID": "desc"}
        }
        
        data = await self._request("tasks.task.list", payload)
        tasks = data.get('result', {}).get('tasks', [])
        
        kanban_board = {
            "Pendente": [],
            "Em Andamento": [],
            "Aguardando Controle": [],
            "Concluído": [],
            "Adiado": []
        }
        
        for task in tasks:
            status_code = task.get("status", "2") # Pega o ID numérico do status
            status_name = self.status_map.get(status_code, "Pendente")
            
            card = {
                "id": task["id"],
                "title": task["title"],
                "responsible": task["responsibleId"],
                "deadline": task.get("deadline", "Sem prazo"),
                "priority": task["priority"]
            }
            
            if status_name in kanban_board:
                kanban_board[status_name].append(card)
                
        return kanban_board

    async def move_card(self, task_id: int, new_status_code: str):
        """
        Move o card no Kanban (Atualiza o status no Bitrix)
        """
        payload = {
            "taskId": task_id,
            "fields": {
                "STATUS": new_status_code
            }
        }
        await self._request("tasks.task.update", payload)
        return True