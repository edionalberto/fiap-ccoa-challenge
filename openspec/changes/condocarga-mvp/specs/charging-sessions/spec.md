# Spec Delta

## Purpose

Esta capacidade registra o uso simulado de carregadores e mantém cada sessão vinculada à credencial, ao usuário e à unidade responsável.

## ADDED Requirements

### Requirement: Identificar a unidade pela credencial
O sistema SHALL resolver uma credencial RFID ativa para um usuário e a unidade associada antes de abrir uma sessão.

#### Scenario: Credencial ativa conhecida
- **WHEN** uma credencial ativa associada a um usuário solicita início em carregador disponível e não há fila anterior, ou a solicitação do usuário é a primeira da fila
- **THEN** o sistema abre uma sessão vinculada ao usuário e à unidade registrada no início e marca o pedido correspondente como atendido

#### Scenario: Credencial desconhecida ou inativa
- **WHEN** uma credencial desconhecida ou inativa tenta iniciar uma sessão
- **THEN** o sistema recusa a abertura e informa o motivo sem criar sessão cobrável

#### Scenario: Usuário tenta ultrapassar fila
- **WHEN** há solicitações em espera e um usuário que não está na primeira posição tenta iniciar
- **THEN** o sistema recusa a abertura, mantém a ordem da fila e não cria sessão

### Requirement: Validar o ciclo da sessão
O sistema SHALL manter sessões somente nos estados ativa ou encerrada, validar horários e leituras e impedir mais de uma sessão ativa por carregador.

#### Scenario: Sessão encerrada com leituras válidas
- **WHEN** o encerramento possui horário posterior ou igual ao início e leitura final maior ou igual à inicial
- **THEN** o sistema encerra a sessão e calcula consumo não negativo em kWh

#### Scenario: Encerramento inválido
- **WHEN** horário final precede o início ou leitura final é menor que a inicial
- **THEN** o sistema recusa a tentativa, mostra o erro, mantém a sessão ativa e mantém o carregador ocupado para permitir nova tentativa

#### Scenario: Carregador já ocupado
- **WHEN** uma nova sessão tenta iniciar num carregador que já possui sessão ativa
- **THEN** o sistema recusa a abertura sem criar sessão conflitante

#### Scenario: Sessão sem encerramento
- **WHEN** uma sessão permanece ativa
- **THEN** ela aparece como pendente, mantém o carregador ocupado e não é incluída nos valores do fechamento

### Requirement: Evitar processamento duplicado
O sistema SHALL reconhecer a mesma sessão ou evento de origem já processado e não repetir seus efeitos.

#### Scenario: Reenvio do mesmo identificador
- **WHEN** o sistema recebe novamente um evento ou sessão com identificador de origem já processado
- **THEN** mantém uma única sessão e um único efeito no histórico e no fechamento
