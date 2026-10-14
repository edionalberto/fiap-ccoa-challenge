# Spec Delta

## Purpose

Esta capacidade estima a demanda energética por faixa horária e orienta a escolha do morador entre horários futuros de sua preferência, com evidência comparativa e limites visíveis.

## ADDED Requirements

### Requirement: Comparar previsão com referência simples
O sistema SHALL avaliar a regressão por separação temporal e comparar seu erro absoluto médio em kWh com uma referência histórica calculada apenas a partir dos dados de treino.

#### Scenario: Histórico suficiente
- **WHEN** existem dados de treino e períodos posteriores de avaliação
- **THEN** o sistema mostra MAE do modelo e da referência sem usar dados futuros no treino

#### Scenario: Histórico insuficiente
- **WHEN** não há histórico suficiente para a avaliação prevista
- **THEN** o sistema informa a limitação e não apresenta desempenho não medido como fato

### Requirement: Recomendar somente dentro das preferências futuras
O sistema SHALL ordenar por menor demanda estimada as faixas horárias futuras que correspondem às preferências informadas pelo morador. Na demonstração, o morador informa dias da semana e horas do dia preferidos; o sistema gera candidatos de uma hora dentro dos próximos sete dias locais. A recomendação SHALL ser orientação, não agenda, reserva, alocação ou confirmação de disponibilidade.

#### Scenario: Morador informa preferências
- **WHEN** o morador seleciona um ou mais dias da semana e horas do dia para os próximos sete dias
- **THEN** o sistema apresenta as faixas futuras correspondentes em ordem crescente de demanda prevista e mostra estimativa, origem dos dados e motivo

#### Scenario: Nenhuma preferência fornecida
- **WHEN** o morador ainda não escolheu dias e horas de preferência
- **THEN** o sistema solicita essas preferências sem inferir uma reserva ou janela desejada

#### Scenario: Modelo não supera referência
- **WHEN** o modelo não apresenta erro menor que a referência
- **THEN** o sistema usa a referência para ordenar as preferências ou informa que não há base para recomendação

#### Scenario: Horário recomendado não é garantia
- **WHEN** uma opção é exibida como recomendação
- **THEN** a interface indica que é uma estimativa e não garante disponibilidade futura, não cria reserva e não controla potência elétrica
