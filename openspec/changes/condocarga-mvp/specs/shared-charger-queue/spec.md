# Spec Delta

## Purpose

Esta capacidade coordena pedidos de uso dos carregadores compartilhados, apresentando disponibilidade e ordem de espera sem acionar equipamento físico.

## ADDED Requirements

### Requirement: Manter fila FIFO determinística
O sistema SHALL registrar solicitações simuladas por carregador e apresentá-las em ordem crescente por horário de criação, desempatando horários iguais pelo identificador estável da solicitação em ordem crescente. A fila SHALL ter somente os estados `WAITING`, `CANCELLED` e `SERVED`.

#### Scenario: Carregador ocupado
- **WHEN** um morador solicita um carregador com sessão ativa
- **THEN** o sistema registra o pedido em espera após pedidos anteriores, segundo ordenação e desempate definidos

#### Scenario: Carregador disponível sem pedidos anteriores
- **WHEN** não há sessão ativa no carregador nem solicitação pendente anterior
- **THEN** o sistema apresenta o carregador como disponível para início simulado

#### Scenario: Somente o primeiro da fila pode iniciar
- **WHEN** o carregador fica disponível e existem solicitações em espera
- **THEN** somente o solicitante na primeira posição pode iniciar; no início aceito, sua solicitação muda para `SERVED`

#### Scenario: Cancelamento libera a próxima posição
- **WHEN** o primeiro solicitante cancela seu pedido ainda em espera
- **THEN** seu pedido muda para `CANCELLED`, permanece no histórico e o próximo pedido em espera torna-se o primeiro elegível

#### Scenario: Atendimento libera a próxima posição
- **WHEN** o primeiro solicitante inicia a sessão e o pedido é marcado `SERVED`
- **THEN** o próximo pedido em espera torna-se o primeiro elegível após o carregador voltar a ficar disponível

### Requirement: Recomendações não alteram a fila
O sistema SHALL manter a fila determinada pelas solicitações e não reorganizá-la automaticamente por recomendação de IA.

#### Scenario: Horário recomendado
- **WHEN** a IA recomenda uma faixa futura de menor demanda
- **THEN** a recomendação é exibida como orientação opcional e não muda a ordem dos pedidos nem reserva o carregador
