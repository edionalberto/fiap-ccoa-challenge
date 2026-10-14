# Spec Delta

## Purpose

Esta capacidade fornece entrada sintética reprodutível que exercita as mesmas validações do fluxo de sessões e contém perfis horários sem alegar granularidade de um equipamento real.

## ADDED Requirements

### Requirement: Carregar demonstração interna validada
O sistema SHALL carregar registros sintéticos versionados em JSON interno e submetê-los às validações normais de sessão e identificador.

#### Scenario: Carga demonstrativa repetida
- **WHEN** o conjunto demonstrativo é carregado mais de uma vez
- **THEN** os registros permanecem únicos e a demonstração pode ser reiniciada de forma reproduzível

#### Scenario: Registro sintético inválido
- **WHEN** um registro de sessão da carga viola uma regra de horário ou leitura
- **THEN** o registro é rejeitado com diagnóstico e não cria sessão cobrável

### Requirement: Representar medições horárias sintéticas conciliáveis
Cada medição horária sintética SHALL conter `session_id`, `charger_id`, `interval_start`, `interval_end`, `energy_kwh` e origem `synthetic`; o intervalo SHALL ser uma hora local completa e identificada com fuso. As medições SHALL estar ligadas à sessão e ao carregador correspondentes, não se sobrepor para o mesmo carregador e somar exatamente à diferença entre as leituras totais da sessão. A cobrança SHALL continuar baseada nas leituras totais de sessão, não na soma das medições horárias.

#### Scenario: Perfil horário de uma sessão
- **WHEN** uma sessão sintética vai de 100 kWh às 10:00 a 112 kWh às 13:00
- **THEN** suas medições ligadas à mesma sessão e carregador podem ser 4 kWh das 10:00–11:00, 5 kWh das 11:00–12:00 e 3 kWh das 12:00–13:00, totalizando 12 kWh

#### Scenario: Soma horária não concilia
- **WHEN** medições horárias de uma sessão não somam à diferença entre sua leitura final e inicial, têm intervalo inválido ou sobreposição
- **THEN** a carga rejeita as medições com diagnóstico e não as usa no conjunto de treino

### Requirement: Não presumir granularidade da integração GoodWe
O sistema SHALL identificar a entrada do MVP como simulada e SHALL não presumir endpoints, credenciais, campos ou medições horárias da GoodWe.

#### Scenario: Sem acesso ou documentação
- **WHEN** não há documentação e acesso GoodWe confirmados
- **THEN** a demonstração usa somente dados sintéticos e descreve a integração como evolução futura

#### Scenario: Dados reais sem perfil horário documentado
- **WHEN** uma integração futura documentada fornecer somente leitura total da sessão, sem medições horárias
- **THEN** o sistema não atribui artificialmente todo o consumo à hora de encerramento nem inventa sua distribuição horária
