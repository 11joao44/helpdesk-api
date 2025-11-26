Infra e DevOps: Em conjunto do Desenvolvedor Ben-hur que realizou configurações do DNS e demais necessidade para funcionamento da api para rede aberta segui com auxlio voltado a lógica da API

Banco de Dados: Definição de arquitetura no PostgreSQL para colunas de identificação (CPF e Matrícula), optando por VARCHAR com validações (Constraints) para garantir integridade e performance.

Frontend & UI

Login: Refatoração do componente de Login com tratamento de erros, loading states e validação.

Header: Desenvolvimento do componente Header com botão para acionar a modal da informações do usuário.

Modal: Criação do componente ProfileModal para visualização detalhada dos dados do usuário.

Lógica & Integração

Auth: Integração do formulário com a API (Axios), implementando salvamento de Token e dados de usuário no localStorage.

State Management: Criação do AuthFlowContext para gerenciar a alternância entre telas de Login e Cadastro sem prop drilling.

Routing: Ajuste na lógica de navegação utilizando TanStack Router, incluindo invalidação de cache pós-login.

Correção da (API): Ajuste na validação do Pydantic no endpoint de criação de usuários (Field required), corrigindo a divergência entre password e hashed_password.

Debug de Banco de Dados: Identificação e tratamento de erro de schema no PostgreSQL (UndefinedColumnError), onde o SQLAlchemy buscava uma coluna username inexistente.

Investigação de Criptografia: Diagnóstico do erro de hash (72 bytes limit) no cadastro de usuários.

Gestão de Dependências: Identificada incompatibilidade crítica entre passlib e bcrypt (v5.0.0) e definida estratégia de correção (migração para bcrypt nativo ou downgrade de versão).

