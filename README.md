# Documentação Técnica Completa da API - Carvalima Helpdesk

Esta documentação detalha de forma abrangente a API Backend do sistema de Helpdesk, incluindo arquitetura, endpoints, modelos de dados, integrações, e boas práticas de desenvolvimento.

---

## 📋 Sumário Executivo

O **Carvalima Helpdesk** é um sistema de gerenciamento de chamados técnicos de grande escala que integra o Bitrix24 CRM como backend de tickets, com uma camada de API própria construída em FastAPI para orquestração, persistência local e exposição de dados para o frontend React.

**Stack Tecnológico:**

- **Framework:** FastAPI (Python 3.x)
- **Validação de Dados:** Pydantic v2
- **ORM:** SQLAlchemy 2.x (Async)
- **Banco de Dados:** PostgreSQL (AsyncSession)
- **Storage de Arquivos:** MinIO (S3-Compatible)
- **CRM Externo:** Bitrix24 (via API REST)
- **Autenticação:** JWT com Cookies HTTP-Only
- **Real-Time:** WebSockets (para notificações e atualizações de tickets)
- **Email:** SMTP para recuperação de senha e envio de emails vinculados a tickets

---

## 🏗️ 1. Arquitetura e Estrutura do Projeto

### 1.1 Padrão Arquitetural: 3-Layer Architecture

A aplicação segue rigorosamente a **arquitetura em três camadas** para garantir separação de responsabilidades, testabilidade e escalabilidade:

```
┌─────────────────────────────────────────┐
│         PRESENTATION LAYER              │
│     (Routes / Controllers)              │
│  - Validação via Pydantic               │
│  - Autenticação/Autorização             │
│  - Serialização de Responses            │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│         BUSINESS LOGIC LAYER            │
│          (Services)                     │
│  - Regras de Negócio                    │
│  - Orquestração de Repositórios         │
│  - Integração com Providers             │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│         DATA ACCESS LAYER               │
│    (Repositories + Providers)           │
│  - Repositories: Acesso ao DB Local     │
│  - Providers: Integrações Externas      │
│    • BitrixProvider (CRM)               │
│    • StorageProvider (MinIO)            │
└─────────────────────────────────────────┘
```

---

### 1.2 Estrutura de Pastas

```
app/
├── __init__.py              # Application Factory (create_app)
├── main.py                  # Entry Point (Uvicorn)
│
├── core/                    # Configurações e Utilitários Centrais
│   ├── config.py            # Variáveis de ambiente e Settings
│   ├── constants.py         # Mapeamento de campos Bitrix (31KB)
│   ├── database.py          # Async Engine e SessionLocal
│   ├── security.py          # JWT, Hash, Middlewares de Auth
│   └── interfaces.py        # Protocolos e Type Hints
│
├── models/                  # SQLAlchemy Models (DB Local)
│   ├── users.py             # UserModel
│   ├── deals.py             # DealModel (Tickets)
│   ├── activity.py          # ActivityModel (Timeline)
│   ├── activity_files.py    # Tabela de anexos de atividades
│   └── deal_files.py        # Tabela de anexos de deals
│
├── schemas/                 # Pydantic Schemas (DTOs)
│   ├── users.py             # UserRegister, UserOut, UserLogin
│   ├── deals.py             # DealCardSchema, DealCardCreateSchema
│   ├── tickets.py           # TicketCreateRequest, TicketCloseRequest
│   ├── activity.py          # ActivitySchema
│   ├── bitrix.py            # BitrixWebhookSchema
│   └── upload.py            # FileUploadSchema
│
├── routes/                  # Controllers (Endpoints)
│   ├── __init__.py          # Agregador de routers
│   ├── users.py             # /auth/* (Login, Logout, Me, etc)
│   ├── tickets.py           # /ticket, /tickets/*, /close-ticket
│   ├── webhook.py           # /webhook-bitrix24, /kanban/cards
│   ├── websocket.py         # /ws/{deal_id}/{user_id}
│   └── uploads.py           # Upload de arquivos
│
├── services/                # Regras de Negócio
│   ├── users.py             # UserService (CRUD, Auth, Tokens)
│   ├── deals.py             # DealService (Criação, Fechamento, Comentários)
│   ├── webhook.py           # WebhookService (Sincronização Bitrix→Local)
│   ├── websocket.py         # ConnectionManager (Broadcast WebSocket)
│   ├── send_email.py        # Envio de emails (SMTP)
│   └── upload.py            # UploadService
│
├── repositories/            # Data Access (DB Local)
│   ├── users.py             # UserRepository
│   ├── deals.py             # DealRepository
│   └── activity.py          # ActivityRepository
│
├── providers/               # Integrações Externas
│   ├── bitrix.py            # BitrixProvider (API Bitrix24)
│   └── storage.py           # StorageProvider (MinIO S3)
│
└── utils/                   # Helpers e Utilidades
    └── (validators, formatters, etc)
```

---

### 1.3 Fluxo de Requisição Típico

**Exemplo: Criação de Ticket**

```
1. [Frontend] POST /ticket com TicketCreateRequest
                ↓
2. [Route] tickets.py → Valida Pydantic → Chama DealService.create_ticket()
                ↓
3. [Service] DealService:
   - Valida dados de negócio
   - Chama BitrixProvider.create_deal() → Cria Deal no Bitrix24
   - Chama BitrixProvider.upload_disk_file() → Upload de anexos
   - Chama DealRepository.create() → Salva no DB Local
   - Chama StorageProvider.upload_file() → Salva anexos no MinIO
   - Retorna DealCardCreateSchema
                ↓
4. [Route] Retorna 201 Created com Schema para o Frontend
```

---

## 🔐 2. Autenticação e Segurança

### 2.1 Estratégia de Autenticação

- **Método:** JWT (JSON Web Tokens)
- **Armazenamento:** Cookies HTTP-Only (protegido contra XSS)
- **Tipos de Token:**
  - `access_token`: Expira em 7 dias (604800s)
  - `refresh_token`: Expira em 7 dias (renovável)

### 2.2 Configuração de Cookies

```python
cookie_params = {
    "httponly": True,       # Não acessível via JavaScript
    "secure": True,         # Apenas HTTPS
    "samesite": "None",     # Permite Cross-Origin (Frontend separado)
    "max_age": 604800       # 7 dias
}
```

### 2.3 Fluxo de Autenticação

**Login:**

```
POST /auth/login
Body: { "matricula": "12345678", "password": "****" }
Response: LoginResponse + Set-Cookie (access_token, refresh_token)
```

**Refresh Token:**

```
POST /auth/refresh-token
Cookie: refresh_token
Response: Novo access_token via Set-Cookie
```

**Logout:**

```
POST /auth/logout
Response: Deleta cookies access_token e refresh_token
```

### 2.4 Proteção de Rotas

**Middlewares de Segurança:** ([security.py](file:///c:/Users/10211/Documents/carvalima_helpdesk_api/app/core/security.py))

- `get_current_user_from_cookie`: Extrai e valida JWT do cookie
- `require_admin`: Valida se usuário é admin (is_admin=True)

**Exemplo de Uso:**

```python
@router.get("/me", response_model=UserOut)
async def read_users_me(
    current_user: UserModel = Depends(get_current_user_from_cookie)
):
    return current_user
```

---

## 📡 3. Catálogo Completo de Endpoints

### 3.1 Autenticação e Usuários (`/auth`)

| Método | Endpoint | Descrição | Auth | Request Body | Response |
|--------|----------|-----------|------|--------------|----------|
| **POST** | `/auth/login` | Autentica usuário e define cookies JWT | ❌ | `UserLogin` | `LoginResponse` (200) |
| **POST** | `/auth/logout` | Remove cookies de autenticação | ❌ | - | `{"message": "Logout realizado"}` (200) |
| **POST** | `/auth/refresh-token` | Renova access_token usando refresh_token | ❌ | - | `{"message": "Token atualizado"}` (200) |
| **GET** | `/auth/me` | Retorna dados do usuário autenticado | ✅ | - | `UserOut` (200) |
| **POST** | `/auth/users` | Cria novo usuário (sign-up) | ❌ | `UserRegister` | `UserOut` (201) |
| **GET** | `/auth/users/{user_id}` | Busca usuário por ID | ✅🔒 Admin | - | `UserOut` (200) |
| **PUT** | `/auth/users/{user_id}` | Atualiza usuário | ✅🔒 Admin | `UserRegister` | `UserOut` (200) |
| **DELETE** | `/auth/users/{user_id}` | Desativa usuário | ✅🔒 Admin | - | `UserOut` (200) |
| **POST** | `/auth/forgot-password` | Inicia fluxo de recuperação de senha | ❌ | `ForgotPasswordRequest` | `{"message": "Email enviado"}` (200) |
| **POST** | `/auth/reset-password` | Redefine senha com token | ❌ | `ResetPasswordRequest` | `{"message": "Senha redefinida"}` (200) |
| **GET** | `/auth/check-availability` | Verifica disponibilidade de email/matricula | ❌ | `ChackAvailability` (Query) | `boolean` (200) |
| **POST** | `/auth/users/avatar` | Upload de foto de perfil | ✅ | `file: UploadFile` | `UserOut` (200) |
| **POST** | `/auth/users/me/phone` | Atualiza telefone do usuário | ✅ | `PhoneUpdateRequest` | `UserOut` (200) |

---

### 3.2 Tickets e Chamados (`/ticket`, `/tickets/*`)

| Método | Endpoint | Descrição | Auth | Request Body | Response |
|--------|----------|-----------|------|--------------|----------|
| **POST** | `/ticket` | Cria novo ticket no Bitrix e DB local | ✅ | `TicketCreateRequest` | `DealCardCreateSchema` (201) |
| **POST** | `/close-ticket` | Fecha ticket e salva avaliação | ✅ | `TicketCloseRequest` | `{"status": "success"}` (200) |
| **POST** | `/send-email` | Envia email vinculado ao ticket | ✅ | `TicketSendEmail` | `{"status": "success"}` (200) |
| **POST** | `/ticket/comment` | Adiciona comentário ao ticket | ✅ | `TicketAddCommentRequest` | `{"status": "success"}` (200) |
| **GET** | `/tickets/{user_id}` | Lista TODOS os tickets do usuário | ✅ | - | `List[DealCardSchema]` (200) |
| **GET** | `/tickets-opens/{user_id}` | Lista apenas tickets ABERTOS do usuário | ✅ | - | `List[DealCardSchema]` (200) |
| **GET** | `/tickets-responsible/{user_id}` | Lista tickets onde usuário é RESPONSÁVEL | ✅ | - | `List[DealCardSchema]` (200) |
| **GET** | `/deal/{deal_id}/{user_id}` | Busca ticket específico (marca como lido) | ✅ | - | `List[DealCardSchema]` (200) |

---

### 3.3 Webhooks e Integrações Bitrix24

| Método | Endpoint | Descrição | Auth | Request Body | Response |
|--------|----------|-----------|------|--------------|----------|
| **POST** | `/webhook-bitrix24` | Recebe eventos do Bitrix24 (Deal/Activity) | ❌ | Form Data (Bitrix) | `"OK"` (200) |
| **GET** | `/kanban/cards` | Lista todos os tickets para visualização Kanban | ✅ | - | `List[DealCardSchema]` (200) |

**Eventos Suportados:**

- `ONCRMDEALADD` → Sincroniza novo Deal
- `ONCRMDEALUPDATE` → Atualiza Deal existente
- `ONCRMACTIVITYADD` → Sincroniza nova atividade (comentário/email)
- `ONIMEMAILMESSAGEADD` → Sincroniza email recebido

---

### 3.4 WebSockets (Real-Time)

| Endpoint | Descrição | Parâmetros | Eventos |
|----------|-----------|------------|---------|
| `/ws/{deal_id}/{user_id}` | Conexão para atualizações de ticket específico | `deal_id` (Bitrix ID), `user_id` | `new_comment`, `deal_updated` |
| `/ws/notifications` | Conexão global para notificações do dashboard | - | `new_ticket`, `ticket_updated`, `new_activity` |

**Salas (Rooms):**

- `{deal_id}` → Broadcast para usuários visualizando o ticket específico
- `dashboard` → Broadcast global para todos os usuários conectados

---

## 📊 4. Modelos de Dados

### 4.1 Banco de Dados Local (PostgreSQL)

#### **Tabela: `users`**

**Modelo:** [UserModel](file:///c:/Users/10211/Documents/carvalima_helpdesk_api/app/models/users.py)

| Campo | Tipo | Constraints | Descrição |
|-------|------|-------------|-----------|
| `id` | Integer | PK, Auto | ID interno do usuário |
| `full_name` | String(64) | NOT NULL, Index | Nome completo |
| `matricula` | String(15) | UNIQUE, NOT NULL | Matrícula do funcionário |
| `email` | String(128) | UNIQUE, NOT NULL | Email corporativo |
| `cpf` | String(128) | UNIQUE, NOT NULL | CPF (criptografado) |
| `hashed_password` | String(256) | NOT NULL | Senha com bcrypt |
| `department` | String(64) | NOT NULL | Departamento |
| `filial` | String(64) | NOT NULL | Filial |
| `phone_number` | String(20) | NULL | Telefone |
| `profile_picture` | String(256) | NULL | Chave MinIO da foto |
| `is_active` | Boolean | DEFAULT true | Usuário ativo |
| `is_admin` | Boolean | DEFAULT false | Permissão admin |
| `created_at` | DateTime(TZ) | DEFAULT now() | Data de criação |
| `updated_at` | DateTime(TZ) | ON UPDATE now() | Última atualização |
| `password_reset_token` | Text | NULL | Token de reset de senha |

**Relacionamentos:**

- `deals` → One-to-Many com `DealModel` (Tickets criados pelo usuário)

---

#### **Tabela: `deals` (Tickets)**

**Modelo:** [DealModel](file:///c:/Users/10211/Documents/carvalima_helpdesk_api/app/models/deals.py)

| Campo | Tipo | Constraints | Descrição |
|-------|------|-------------|-----------|
| `id` | Integer | PK, Auto | ID interno (para FKs) |
| `deal_id` | Integer | UNIQUE, NOT NULL | **ID do Bitrix (canal WebSocket)** |
| `title` | String(255) | NULL | Título do ticket |
| `description` | Text | NULL | Descrição detalhada |
| `stage_id` | String(50) | Index | ID da etapa Bitrix (ex: C19:NEW) |
| `opened` | String(1) | Index | Y/N - Ticket aberto |
| `closed` | String(1) | Index | Y/N - Ticket fechado |
| `created_by_id` | String(10) | Index | ID Bitrix do criador |
| `modify_by_id` | String(10) | - | Último modificador |
| `moved_by_id` | String(10) | - | Quem moveu de etapa |
| `last_activity_by_id` | String(10) | - | Última atividade |
| `last_communication_time` | String(19) | - | Timestamp última comunicação |
| `close_date` | DateTime(TZ) | NULL | Data de fechamento |
| `date_deadline` | DateTime(TZ) | NULL | **Prazo calculado por SLA** |
| `begin_date` | DateTime(TZ) | NULL | Data de início |
| `requester_department` | String(100) | Index | Departamento solicitante |
| `assignee_department` | String(100) | Index | Departamento responsável |
| `service_category` | String(50) | Index | Categoria de serviço |
| `system_type` | String(50) | Index | Sistema afetado |
| `priority` | String(50) | Index | Prioridade (Crítico/Alto/Médio/Baixo) |
| `matricula` | String(20) | Index | Matrícula do solicitante |
| `responsible` | String(255) | Index | Nome do responsável |
| `responsible_email` | String(255) | Index | Email do responsável |
| `requester_email` | String(255) | - | Email do solicitante |
| `responsible_id` | Integer | FK → users.id, Index | **FK para usuário responsável** |
| `user_id` | Integer | FK → users.id | FK para usuário criador |
| `file_id` | Integer | NULL | ⚠️ Legacy - Usar `files` |
| `file_url` | Text | NULL | ⚠️ Legacy - Usar `files` |
| `is_unread` | Boolean | DEFAULT false | Notificação não lida |
| `created_at` | DateTime(TZ) | DEFAULT now() | Data de criação |
| `updated_at` | DateTime(TZ) | ON UPDATE now() | Última atualização |

**Relacionamentos:**

- `activities` → One-to-Many com `ActivityModel` (Timeline do ticket)
- `files` → One-to-Many com `DealFileModel` (Anexos do ticket)
- `user` → Many-to-One com `UserModel` (Criador)
- `responsible_user_rel` → Many-to-One com `UserModel` (Responsável)

---

#### **Tabela: `activities` (Timeline)**

**Modelo:** [ActivityModel](file:///c:/Users/10211/Documents/carvalima_helpdesk_api/app/models/activity.py)

| Campo | Tipo | Constraints | Descrição |
|-------|------|-------------|-----------|
| `id` | Integer | PK, Auto | ID interno |
| `activity_id` | Integer | UNIQUE, NOT NULL | **ID Bitrix da atividade** |
| `deal_id` | Integer | FK → deals.id, NOT NULL | Relacionamento com ticket |
| `owner_type_id` | String(5) | NULL | Tipo de proprietário |
| `type_id` | String(5) | NULL | **Tipo de atividade (2=Comentário, 4=Email)** |
| `provider_id` | String(50) | NULL | Provedor (CRM_OWNER, EMAIL) |
| `provider_type_id` | String(50) | NULL | Sub-tipo de provedor |
| `direction` | String(10) | NULL | **Direção (incoming/outgoing)** |
| `subject` | String(255) | NULL | Assunto (para emails) |
| `priority` | String(5) | NULL | Prioridade |
| `responsible_id` | String(20) | NULL | ID Bitrix do responsável |
| `responsible_name` | String(255) | NULL | Nome do responsável |
| `responsible_email` | String(255) | NULL | Email do responsável |
| `description` | Text | NULL | **Conteúdo do comentário/email** |
| `body_html` | Text | NULL | HTML do email |
| `description_type` | String(5) | NULL | Tipo de descrição |
| `sender_email` | String(255) | NULL | Email do remetente |
| `from_email` | String(255) | NULL | Email "From" |
| `to_email` | String(255) | NULL | Email "To" |
| `receiver_email` | String(255) | NULL | Email do destinatário |
| `author_id` | String(20) | NULL | ID do autor |
| `editor_id` | String(20) | NULL | ID do editor |
| `read_confirmed` | Integer | NULL | Confirmação de leitura |
| `file_id` | Integer | NULL | ⚠️ Legacy - Usar `files` |
| `file_url` | Text | NULL | ⚠️ Legacy - Usar `files` |
| `created_at_bitrix` | DateTime(TZ) | NULL | Data de criação no Bitrix |
| `created_at` | DateTime(TZ) | DEFAULT now() | Data de criação local |

**Relacionamentos:**

- `deal` → Many-to-One com `DealModel`
- `files` → One-to-Many com `ActivityFileModel` (Anexos da atividade)
- `responsible_user` → Many-to-One com `UserModel` (via `responsible_email`)

---

#### **Tabela: `deal_files` (Anexos de Tickets)**

**Modelo:** [DealFileModel](file:///c:/Users/10211/Documents/carvalima_helpdesk_api/app/models/deal_files.py)

| Campo | Tipo | Constraints | Descrição |
|-------|------|-------------|-----------|
| `id` | Integer | PK, Auto | ID interno |
| `deal_id` | Integer | FK → deals.id, NOT NULL | Relacionamento com ticket |
| `file_id` | Integer | NULL | ID do arquivo no Bitrix |
| `file_url` | String(500) | NULL | **Chave MinIO** (ex: `attachments/file.pdf`) |
| `filename` | String(255) | NULL | Nome original do arquivo |

---

#### **Tabela: `activity_files` (Anexos de Atividades)**

**Modelo:** [ActivityFileModel](file:///c:/Users/10211/Documents/carvalima_helpdesk_api/app/models/activity_files.py)

| Campo | Tipo | Constraints | Descrição |
|-------|------|-------------|-----------|
| `id` | Integer | PK, Auto | ID interno |
| `activity_id` | Integer | FK → activities.id, NOT NULL | Relacionamento com atividade |
| `file_id` | Integer | NULL | ID do arquivo no Bitrix |
| `file_url` | String(500) | NULL | **Chave MinIO** |
| `filename` | String(255) | NULL | Nome original do arquivo |

---

### 4.2 Schemas Pydantic (DTOs)

#### **Autenticação**

**`UserLogin`** ([users.py](file:///c:/Users/10211/Documents/carvalima_helpdesk_api/app/schemas/users.py))

```json
{
  "matricula": "12345678",
  "password": "SenhaSegura123"
}
```

**`UserRegister`**

```json
{
  "full_name": "João Silva",
  "email": "joao.silva@carvalima.com",
  "password": "SenhaSegura123",
  "department": "TI",
  "filial": "Matriz",
  "cpf": "123.456.789-00",
  "matricula": "12345678"
}
```

**`UserOut`**

```json
{
  "id": 1,
  "full_name": "João Silva",
  "email": "joao.silva@carvalima.com",
  "filial": "Matriz",
  "matricula": "12345678",
  "department": "TI",
  "phone_number": "+55 11 98765-4321",
  "profile_picture_url": "https://minio-url.com/...",  // URL assinada
  "is_active": true,
  "is_admin": false,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**`LoginResponse`**

```json
{
  "token": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer"
  },
  "user": { ...UserOut... }
}
```

---

#### **Tickets**

**`TicketCreateRequest`** ([tickets.py](file:///c:/Users/10211/Documents/carvalima_helpdesk_api/app/schemas/tickets.py))

```json
{
  "full_name": "Maria Santos",
  "title": "Sistema travando ao gerar relatório",
  "description": "Ao clicar em 'Gerar Relatório', o sistema congela...",
  "subject": "Suporte Técnico",
  "user_id": 5,
  "resp_id": "42",  // ID Bitrix do responsável
  "assignee_department": "TI",
  "email": "maria.santos@carvalima.com",
  "filial": "Filial São Paulo",
  "phone": "+55 11 91234-5678",
  "priority": "Alto",
  "matricula": "87654321",
  "requester_department": "Financeiro",
  "service_category": "Sistema Financeiro",
  "system_type": "ERP",
  "attachments": [
    {
      "filename": "screenshot.png",
      "content": "base64EncodedContent=="
    }
  ]
}
```

**`DealCardCreateSchema`** (Retorno de criação)

```json
{
  "id": 123,  // ID interno (PostgreSQL)
  "deal_id": 837,  // ID Bitrix (usado em WebSocket)
  "title": "Sistema travando ao gerar relatório",
  "description": "Ao clicar em 'Gerar Relatório', o sistema congela...",
  "stage_id": "C19:NEW",
  "opened": "Y",
  "closed": "N",
  "created_by_id": "5",
  "requester_department": "Financeiro",
  "assignee_department": "TI",
  "service_category": "Sistema Financeiro",
  "system_type": "ERP",
  "priority": "Alto",
  "matricula": "87654321",
  "date_deadline": "2024-01-15T14:30:00Z"  // Prazo calculado (+4h para Alto)
}
```

**`DealCardSchema`** (Listagem completa com atividades)

```json
{
  // ... todos os campos de DealCardCreateSchema ...
  "modify_by_id": "42",
  "moved_by_id": "42",
  "last_activity_by_id": "42",
  "last_communication_time": "2024-01-15 11:45:30",
  "close_date": null,
  "begin_date": "2024-01-15T10:30:00Z",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:45:30Z",
  "responsible": "João Tech",
  "responsible_email": "joao.tech@carvalima.com",
  "responsible_profile_picture_url": "https://minio.../avatar.jpg",
  "requester_profile_picture_url": "https://minio.../maria-avatar.jpg",
  "is_unread": false,
  "files": [
    {
      "id": 1,
      "file_url": "https://minio-signed-url.../screenshot.png",
      "filename": "screenshot.png"
    }
  ],
  "activities": [
    {
      "id": 456,
      "activity_id": 9876,
      "type_id": "2",  // Comentário
      "direction": "outgoing",
      "subject": null,
      "description": "Estou analisando o problema. Aguarde...",
      "responsible_name": "João Tech",
      "responsible_email": "joao.tech@carvalima.com",
      "responsible_profile_picture_url": "https://...",
      "created_at_bitrix": "2024-01-15T11:00:00Z",
      "created_at": "2024-01-15T11:00:05Z",
      "files": []
    },
    {
      "id": 457,
      "activity_id": 9877,
      "type_id": "4",  // Email
      "direction": "incoming",
      "subject": "Re: Sistema travando",
      "description": "Problema persistindo mesmo após reiniciar...",
      "body_html": "<p>Problema persistindo...</p>",
      "from_email": "maria.santos@carvalima.com",
      "to_email": "suporte@carvalima.com",
      "created_at_bitrix": "2024-01-15T11:45:00Z",
      "created_at": "2024-01-15T11:45:30Z",
      "files": [
        {
          "id": 2,
          "file_url": "https://minio.../log.txt",
          "filename": "error_log.txt"
        }
      ]
    }
  ]
}
```

**`TicketCloseRequest`**

```json
{
  "deal_id": 837,  // Bitrix ID
  "rating": 5,  // Opcional (1-5)
  "comment": "Problema resolvido rapidamente. Excelente atendimento!"  // Opcional
}
```

**`TicketAddCommentRequest`**

```json
{
  "deal_id": 837,
  "message": "Aplicamos o patch 1.2.5 que corrige o problema.",
  "attachments": [
    {
      "filename": "patch_notes.pdf",
      "content": "base64..."
    }
  ]
}
```

**`TicketSendEmail`**

```json
{
  "deal_id": 837,
  "from_email": "suporte@carvalima.com",
  "to_email": "maria.santos@carvalima.com",
  "subject": "Atualização sobre seu chamado #837",
  "message": "Informamos que o sistema já foi corrigido..."
}
```

---

## 🔌 5. Integrações Externas

### 5.1 Bitrix24 CRM

**Provider:** [BitrixProvider](file:///c:/Users/10211/Documents/carvalima_helpdesk_api/app/providers/bitrix.py) (25KB, 597 linhas)

**Configuração:**

```python
# .env
BITRIX_INBOUND_URL=https://sua-empresa.bitrix24.com/rest/1/webhook_token/
```

#### **Principais Métodos**

| Método | Descrição | Endpoint Bitrix |
|--------|-----------|-----------------|
| `create_deal(data)` | Cria negócio no Bitrix | `crm.deal.add` |
| `get_deal(deal_id)` | Busca detalhes de negócio | `crm.deal.get` |
| `close_deal(deal_id, rating, comment)` | Fecha negócio (move para "Ganho") | `crm.deal.update` |
| `add_comment(deal_id, message, attachments)` | Adiciona comentário à timeline | `crm.timeline.comment.add` |
| `list_timeline_comments(deal_id)` | Lista comentários da timeline | `crm.timeline.comment.list` |
| `list_activities(deal_id)` | Lista atividades do negócio | `crm.activity.list` |
| `get_activity(activity_id)` | Busca detalhes de atividade | `crm.activity.get` |
| `send_email(deal_id, subject, message, to_email)` | Envia email vinculado ao deal | `crm.activity.add` (tipo EMAIL) |
| `get_or_create_contact(name, email, phone)` | Busca ou cria contato | `crm.contact.list` / `crm.contact.add` |
| `upload_disk_file(filename, content)` | Upload para Bitrix Disk | `disk.storage.uploadfile` |
| `download_disk_file(file_id)` | Download do Bitrix Disk | `disk.file.get` |
| `get_user(user_id)` | Busca dados de usuário Bitrix | `user.get` |
| `get_responsible(assigned_by_id)` | Busca responsável | `user.get` |

#### **Mapeamento de Campos**

**Arquivo:** [constants.py](file:///c:/Users/10211/Documents/carvalima_helpdesk_api/app/core/constants.py) (31KB)

**Exemplo de Mapeamento:**

```python
class BitrixFields:
    PRIORITY = "UF_CRM_1701707001"
    SERVICE_CATEGORY = "UF_CRM_1701706961"
    SYSTEM_TYPE = "UF_CRM_1701706933"
    ASSIGNEE_DEPARTMENT = "UF_CRM_1736515084"
    # ... +50 campos customizados

class BitrixValues:
    PRIORITY = {
        "Crítico": "1557",
        "Alto": "1559", 
        "Médio": "1561",
        "Baixo": "1563"
    }
    # ... mapeamento de todos os valores
```

#### **Cálculo de SLA (Prazo)**

```python
def _calculate_sla_deadline(priority_id: str) -> str:
    """
    Regras de Prazo:
    - Crítico (1557): +1 Hora
    - Alto (1559): +4 Horas  
    - Médio (1561): +1 Dia (24h)
    - Baixo (1563): +3 Dias (72h)
    """
```

---

### 5.2 MinIO (Storage S3-Compatible)

**Provider:** [StorageProvider](file:///c:/Users/10211/Documents/carvalima_helpdesk_api/app/providers/storage.py)

**Configuração:**

```python
# .env
IP_SERVIDOR_NFS=carvalima-teste.duckdns.org:8086
MINIO_USER=minioadmin
MINIO_SENHA=senhaSegura123
```

**Características:**

- **Bucket:** `anexos-email-bitrix`
- **URL Assinada:** Expiração padrão de 2 horas (renovável até 168h para avatares)
- **Upload Path:** `attachments/{filename}`
- **TLS:** Secure=True (HTTPS obrigatório)

#### **Principais Métodos**

| Método | Descrição | Retorno |
|--------|-----------|---------|
| `upload_file(file_data, filename)` | Faz upload de bytes para MinIO | `object_name` (ex: `attachments/file.pdf`) |
| `get_presigned_url(object_name, expiration_hours)` | Gera URL temporária para acesso | URL assinada (string) |

**Exemplo de Uso:**

```python
storage = StorageProvider()

# Upload
object_name = storage.upload_file(
    file_data=file_bytes, 
    filename="screenshot.png"
)
# Retorna: "attachments/screenshot.png"

# Gerar URL assinada
url = storage.get_presigned_url(
    object_name=object_name,
    expiration_hours=2
)
# Retorna: "https://carvalima-teste.duckdns.org:8086/anexos-email-bitrix/..."
```

---

## 🔄 6. Sincronização Bitrix ↔ Local (Webhooks)

### 6.1 Fluxo de Sincronização

**Service:** [WebhookService](file:///c:/Users/10211/Documents/carvalima_helpdesk_api/app/services/webhook.py) (19KB, 444 linhas)

```
Bitrix24 Webhook → POST /webhook-bitrix24
                        ↓
           WebhookService.process_webhook()
                        ↓
          ┌─────────────┴──────────────┐
          │                            │
    ONCRMDEALADD               ONCRMACTIVITYADD
    ONCRMDEALUPDATE            ONIMEMAILMESSAGEADD
          │                            │
    _sync_deal()               _sync_activity()
          │                            │
    DealRepository              ActivityRepository
      .upsert()                    .upsert()
          │                            │
          └────────────┬───────────────┘
                       │
              WebSocket Broadcast
              (manager.broadcast)
                       │
              ┌────────┴────────┐
              │                 │
         ws/{deal_id}      ws/notifications
```

### 6.2 Eventos Tratados

| Evento Bitrix | Ação | Broadcast |
|---------------|------|-----------|
| `ONCRMDEALADD` | Sincroniza novo Deal → DB Local | ✅ `ws/notifications` (novo ticket) |
| `ONCRMDEALUPDATE` | Atualiza campos do Deal (opened, closed, stage_id) | ✅ `ws/{deal_id}` (deal_updated) |
| `ONCRMACTIVITYADD` | Sincroniza nova atividade (comentário/email) | ✅ `ws/{deal_id}` + `ws/notifications` |
| `ONIMEMAILMESSAGEADD` | Sincroniza email recebido como atividade | ✅ `ws/{deal_id}` + `ws/notifications` |

### 6.3 Processamento de Anexos

**Estratégia de Dual Upload:**

```python
# 1. Upload para Bitrix Disk
bitrix_file_id = bitrix.upload_disk_file(filename, base64_content)

# 2. Upload para MinIO
minio_object_name = storage.upload_file(decoded_bytes, filename)

# 3. Salva ambas as referências no DB
DealFileModel(
    deal_id=deal.id,
    file_id=bitrix_file_id,      # Para referência futura
    file_url=minio_object_name,  # Usado para presigned URLs
    filename=filename
)
```

**Processamento de Anexos de Atividades (Webhook):**

```python
# Quando Bitrix envia evento de nova atividade com anexo
activity_data = bitrix.get_activity(activity_id)
for file_info in activity_data.get('FILES', []):
    # Baixa do Bitrix Disk
    filename, file_bytes = bitrix.download_disk_file(file_info['FILE_ID'])
    
    # Upload para MinIO
    minio_key = storage.upload_file(file_bytes, filename)
    
    # Salva na tabela activity_files
    ActivityFileModel(
        activity_id=activity.id,
        file_id=file_info['FILE_ID'],
        file_url=minio_key,
        filename=filename
    )
```

---

## ⚡ 7. WebSockets e Notificações Real-Time

### 7.1 Arquitetura WebSocket

**Service:** [ConnectionManager](file:///c:/Users/10211/Documents/carvalima_helpdesk_api/app/services/websocket.py)

```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = defaultdict(list)
    
    async def connect(websocket: WebSocket, room: str):
        """Adiciona cliente à sala (room={deal_id} ou 'dashboard')"""
    
    async def disconnect(websocket: WebSocket, room: str):
        """Remove cliente da sala"""
    
    async def broadcast(message: dict, room: str):
        """Envia mensagem para todos os clientes da sala"""
```

### 7.2 Endpoints WebSocket

**1. Atualizações de Ticket Específico**

```javascript
// Frontend
const ws = new WebSocket('wss://api.carvalima.com/ws/837/5');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.event === 'new_comment') {
    // Adiciona novo comentário na timeline
    addCommentToUI(data.activity);
  }
  
  if (data.event === 'deal_updated') {
    // Atualiza status do ticket (ex: fechado)
    updateDealStatus(data.deal);
  }
};
```

**2. Notificações Globais (Dashboard)**

```javascript
const notifWs = new WebSocket('wss://api.carvalima.com/ws/notifications');

notifWs.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.event === 'new_ticket') {
    showToast(`Novo ticket #${data.deal_id}: ${data.title}`);
    incrementBadge();
  }
  
  if (data.event === 'new_activity') {
    if (data.deal_id === currentUserTicket) {
      showNotification(`Nova atividade no ticket #${data.deal_id}`);
    }
  }
};
```

### 7.3 Estrutura de Mensagens

**Evento: `new_comment`**

```json
{
  "event": "new_comment",
  "deal_id": 837,
  "activity": {
    "id": 456,
    "activity_id": 9876,
    "type_id": "2",
    "description": "Estou analisando o problema...",
    "responsible_name": "João Tech",
    "created_at": "2024-01-15T11:00:00Z"
  }
}
```

**Evento: `deal_updated`**

```json
{
  "event": "deal_updated",
  "deal_id": 837,
  "changes": {
    "closed": "Y",
    "stage_id": "C19:WON"
  }
}
```

**Evento: `new_ticket`** (broadcast para `dashboard`)

```json
{
  "event": "new_ticket",
  "deal_id": 840,
  "title": "Erro ao emitir NF-e",
  "priority": "Crítico",
  "requester": "Maria Santos"
}
```

---

## 🧪 8. Regras de Negócio e Validações

### 8.1 Validação de CPF

```python
def is_valid_cpf(cpf: str) -> bool:
    """
    Valida CPF usando algoritmo de dígitos verificadores.
    Remove caracteres não numéricos.
    Rejeita CPFs inválidos (ex: 111.111.111-11)
    """
```

### 8.2 Validação de Matrícula

- **Comprimento máximo:** 8 dígitos
- **Formato:** Numérico sem zeros à esquerda
- **Unicidade:** Validada no banco (UNIQUE constraint)

### 8.3 Regra de CPF em Tickets

**Lógica em** [DealService.create_ticket()](file:///c:/Users/10211/Documents/carvalima_helpdesk_api/app/services/deals.py)

```python
if service_category != "Acessos e Permissões":
    # Se não for categoria "Acessos", usa CPF do usuário logado
    cpf_to_use = current_user.cpf or ""
else:
    # Se for "Acessos", usa CPF informado no form
    cpf_to_use = data.cpf or ""
```

### 8.4 Disponibilidade de Campos (Sign-Up)

**Endpoint:** `GET /auth/check-availability?field=email&value=teste@email.com`

**Campos Validados:**

- `email` → Verifica se já existe
- `matricula` → Verifica se já existe
- `cpf` → Verifica se já existe

**Retorno:**

- `true` → Campo disponível
- `false` → Campo já em uso

---

## 🛡️ 9. Boas Práticas e Padrões de Código

### 9.1 Convenções de Nomenclatura

**Código (INGLÊS):**

```python
# ✅ Correto
async def get_user_by_id(user_id: int) -> UserModel:
    ...

# ❌ Errado
async def buscar_usuario_por_id(id_usuario: int) -> UserModel:
    ...
```

**Comentários e Docstrings (PT-BR):**

```python
async def create_ticket(data: TicketCreateRequest) -> DealCardCreateSchema:
    """
    Cria um novo ticket no Bitrix24 e salva no banco local.
    
    Fluxo:
    1. Valida dados do formulário
    2. Cria contato no Bitrix (se não existir)
    3. Cria Deal no Bitrix
    4. Faz upload de anexos (Bitrix + MinIO)
    5. Salva registro local no PostgreSQL
    6. Retorna Schema para o frontend
    """
```

### 9.2 Tipagem Estrita

```python
# ✅ Correto
def process_data(data: dict[str, Any]) -> TicketResponse:
    ...

# ❌ Errado
def process_data(data):
    ...
```

### 9.3 Tratamento de Erros

```python
# ✅ Correto - Erros semânticos com contexto
if not user:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Usuário com ID {user_id} não encontrado"
    )

# ✅ Captura erros de integração
try:
    deal_data = bitrix.get_deal(deal_id)
except httpx.TimeoutError:
    raise HTTPException(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        detail="Timeout ao buscar dados do Bitrix24"
    )
```

### 9.4 Async/Await Consistente

```python
# ✅ Correto - Usa httpx (async)
import httpx

async def call_external_api():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com")
        return response.json()

# ❌ Errado - requests é bloqueante!
import requests

async def call_external_api():
    response = requests.get("https://api.example.com")  # BLOQUEIA A THREAD
    return response.json()
```

### 9.5 Separação de IDs (Internal vs Bitrix)

**Convenção Crítica:**

```python
# ✅ Correto - Explicita qual ID está usando
internal_deal_id = deal.id          # PK PostgreSQL (para FKs)
bitrix_deal_id = deal.deal_id       # ID Bitrix (para WebSocket/API)

# WebSocket SEMPRE usa Bitrix ID
await manager.broadcast({
    "event": "new_comment",
    "deal_id": bitrix_deal_id  # ✅
}, room=str(bitrix_deal_id))

# Banco de dados SEMPRE usa Internal ID
activity = ActivityModel(
    deal_id=internal_deal_id,  # ✅ FK precisa do ID interno
    ...
)
```

---

## 📦 10. Dependências e Ambiente

### 10.1 Principais Dependências

**Arquivo:** [pyproject.toml](file:///c:/Users/10211/Documents/carvalima_helpdesk_api/pyproject.toml)

```toml
[project]
dependencies = [
    "fastapi>=0.115.6",
    "uvicorn>=0.34.0",
    "sqlalchemy>=2.0.36",
    "asyncpg>=0.30.0",           # Driver async PostgreSQL
    "pydantic>=2.10.5",
    "python-jose[cryptography]",  # JWT
    "passlib[bcrypt]>=1.7.4",    # Hash de senhas
    "httpx>=0.28.1",             # Cliente HTTP async
    "minio>=7.2.11",             # Cliente MinIO S3
    "python-multipart",          # Upload de arquivos
    "loguru>=0.7.3",             # Logging avançado
    "python-dotenv>=1.0.1"       # Variáveis de ambiente
]
```

### 10.2 Variáveis de Ambiente

**Arquivo:** `.env` (exemplo)

```env
# PostgreSQL
PG_CARVALIMA_HELPDESK_DBNAME=carvalima_helpdesk
PG_BOTAPP_HOST=192.168.1.100
PG_BOTAPP_PORT=5432
PG_BOTAPP_USER=postgres
PG_BOTAPP_PASSWORD=senhaSegura123

# Bitrix24
BITRIX_INBOUND_URL=https://sua-empresa.bitrix24.com/rest/1/webhook_token/

# MinIO
IP_SERVIDOR_NFS=carvalima-teste.duckdns.org:8086
MINIO_USER=minioadmin
MINIO_SENHA=senhaMinIO123

# Email (SMTP)
WEBMAIL_USUARIO=suporte@carvalima.com
WEBMAIL_SENHA=senhaEmail123
```

### 10.3 Execução Local

```bash
# Instalar dependências (com uv)
uv sync

# Rodar servidor de desenvolvimento
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Executar migrations (exemplo)
alembic upgrade head
```

---

## 🔍 11. Troubleshooting e FAQs

### 11.1 Erro: "Refresh token não encontrado nos cookies"

**Causa:** Cookie não está sendo enviado pelo frontend.

**Solução:**

```javascript
// Frontend (Fetch/Axios)
fetch('https://api.carvalima.com/auth/me', {
  credentials: 'include'  // ✅ OBRIGATÓRIO para enviar cookies
})
```

### 11.2 URLs do MinIO quebradas (https:///)

**Causa:** Variável `MINIO_ENDPOINT` vazia ou mal configurada.

**Solução:**

```env
# ❌ Errado
IP_SERVIDOR_NFS=

# ✅ Correto
IP_SERVIDOR_NFS=carvalima-teste.duckdns.org:8086
```

### 11.3 Webhook Bitrix não está atualizando o banco

**Diagnóstico:**

1. Verifique os logs do webhook:

```python
# Em webhook.py
await debug_request(request)  # Printa todos os campos recebidos
```

2. Confirme que o Bitrix está enviando o evento:
   - Acesse Bitrix24 → Configurações → Webhooks
   - Verifique se a URL está correta: `https://sua-api.com/webhook-bitrix24`
   - Teste manualmente criando/atualizando um Deal

3. Verifique se o evento está sendo tratado:

```python
# Em WebhookService.process_webhook()
if event_type == "ONCRMDEALADD":
    await self._sync_deal(deal_id)  # ← Certifique-se que está sendo chamado
```

### 11.4 WebSocket não está recebendo mensagens

**Verificações:**

1. **Conexão estabelecida?**

```javascript
ws.onopen = () => console.log('✅ WebSocket conectado');
ws.onerror = (err) => console.error('❌ WebSocket erro:', err);
```

2. **Sala (room) correta?**

```python
# Backend
await manager.broadcast(message, room=str(bitrix_deal_id))  # ← room DEVE ser string

# Frontend
const ws = new WebSocket(`wss://api.com/ws/${dealId}/${userId}`);
// dealId DEVE ser o Bitrix ID (ex: 837), NÃO o internal ID (ex: 123)
```

---

## 📚 12. Referências e Recursos

### 12.1 Documentação de Integrações

- **FastAPI:** <https://fastapi.tiangolo.com/>
- **SQLAlchemy 2.0 (Async):** <https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html>
- **Pydantic V2:** <https://docs.pydantic.dev/latest/>
- **Bitrix24 REST API:** <https://dev.1c-bitrix.ru/rest_help/>
- **MinIO Python SDK:** <https://min.io/docs/minio/linux/developers/python/minio-py.html>

### 12.2 Arquivos de Referência

| Arquivo | Descrição | Linhas |
|---------|-----------|--------|
| [.cursorrules](file:///c:/Users/10211/Documents/carvalima_helpdesk_api/.cursorrules) | Regras de desenvolvimento do projeto | 66 |
| [API_DOCS.md](file:///c:/Users/10211/Documents/carvalima_helpdesk_api/API_DOCS.md) | Documentação resumida de endpoints | 278 |
| [constants.py](file:///c:/Users/10211/Documents/carvalima_helpdesk_api/app/core/constants.py) | Mapeamento completo de campos Bitrix | 31KB |
| [deals.py (service)](file:///c:/Users/10211/Documents/carvalima_helpdesk_api/app/services/deals.py) | Lógica de criação e gerenciamento de tickets | 547 |
| [webhook.py (service)](file:///c:/Users/10211/Documents/carvalima_helpdesk_api/app/services/webhook.py) | Sincronização Bitrix ↔ Local | 444 |
| [bitrix.py (provider)](file:///c:/Users/10211/Documents/carvalima_helpdesk_api/app/providers/bitrix.py) | Cliente API Bitrix24 | 597 |

---

## 🚀 13. Roadmap e Melhorias Futuras

### 13.1 Curto Prazo

- [ ] Implementar rate limiting (proteção DDoS)
- [ ] Adicionar cache Redis para listagens (tickets, users)
- [ ] Logs estruturados (JSON) para análise

### 13.2 Médio Prazo

- [ ] Autenticação via SSO (SAML/OAuth)
- [ ] API de relatórios (métricas de SLA, tempo de resolução)
- [ ] Sistema de permissões granulares (RBAC)
- [ ] Notificações via push (PWA)

### 13.3 Longo Prazo

- [ ] Machine Learning para categorização automática de tickets
- [ ] Chat em tempo real via WebSocket
- [ ] Integração com Microsoft Teams/Slack
- [ ] Dashboard analítico (BI integrado)

---

**Última Atualização:** 14/01/2026  
**Versão da API:** 1.0.0  
**Autor:** Equipe Carvalima Helpdesk
