from enum import Enum
from typing import Annotated
from pydantic import BaseModel, Field, ConfigDict, BeforeValidator


class BitrixEventType(str, Enum):
    TASK_ADD = "ONCRMDEALADD"
    DEAL_UPDATE = "ONCRMDEALUPDATE"
    TASK_DELETE = "ONCRMDEALDELETE"

    COMMENT_ADD = "ONCRMDEALCOMMENTADD"
    UNKNOWN = "UNKNOWN"


# Helper para converter timestamp string para int, se necessário
def coerce_to_int(v):
    if isinstance(v, str) and v.isdigit():
        return int(v)
    return v


TsInt = Annotated[int, BeforeValidator(coerce_to_int)]


class BitrixWebhookSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    event: str
    event_handler_id: int | str
    data_fields_id: int = Field(alias="data[FIELDS][ID]")
    ts: TsInt
    auth_domain: str = Field(alias="auth[domain]")
    auth_client_endpoint: str = Field(alias="auth[client_endpoint]")
    auth_server_endpoint: str = Field(alias="auth[server_endpoint]")
    auth_member_id: str = Field(alias="auth[member_id]")
    auth_application_token: str = Field(alias="auth[application_token]")
