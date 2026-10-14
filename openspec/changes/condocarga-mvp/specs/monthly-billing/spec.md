# Spec Delta

## Purpose

Esta capacidade transforma sessões encerradas e válidas em valores transparentes e relatórios mensais agrupados por unidade.

## ADDED Requirements

### Requirement: Calcular energia e valor rastreáveis
O sistema SHALL calcular o consumo como leitura final menos leitura inicial e o valor como consumo multiplicado pela tarifa capturada no início da sessão.

#### Scenario: Sessão com tarifa uniforme
- **WHEN** uma sessão válida encerra com leitura final superior à inicial
- **THEN** o sistema mostra leituras, energia, tarifa aplicada e valor da sessão arredondado a centavos

#### Scenario: Alteração de tarifa futura
- **WHEN** a tarifa configurada muda após uma sessão
- **THEN** a sessão anterior mantém a tarifa capturada no seu início

### Requirement: Consolidar fechamento mensal
O sistema SHALL agrupar sessões encerradas pelo mês local de encerramento, usando fuso horário explícito, e somar valores arredondados por sessão em centavos.

#### Scenario: Relatório mensal por unidade
- **WHEN** o síndico solicita o relatório de um período mensal
- **THEN** o relatório apresenta por unidade as sessões válidas, consumo, tarifa aplicada e total conciliável

#### Scenario: Sessão cruza a virada do mês
- **WHEN** uma sessão começa em um mês e termina no mês seguinte no fuso configurado
- **THEN** toda a sessão entra no mês de encerramento sem rateio entre períodos

#### Scenario: Regerar relatório
- **WHEN** o síndico gera novamente o relatório para o mesmo período
- **THEN** o sistema calcula as mesmas linhas a partir das sessões válidas sem criar lançamentos duplicados

### Requirement: Excluir cobranças não definidas
O sistema SHALL cobrar somente a energia medida multiplicada pela tarifa configurada no MVP, sem acrescentar custos fixos, perdas, margem separada ou pagamento bancário.

#### Scenario: Exemplo de tarifa
- **WHEN** o consumo é 12 kWh e a tarifa fictícia configurada é R$ 1,00/kWh
- **THEN** o valor calculado é R$ 12,00 e a interface identifica a tarifa como dado de demonstração
