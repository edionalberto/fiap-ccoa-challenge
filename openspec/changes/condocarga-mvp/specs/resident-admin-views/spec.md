# Spec Delta

## Purpose

Esta capacidade apresenta informações pertinentes ao morador e ao síndico para acompanhar sessões compartilhadas e conferir o fechamento mensal.

## ADDED Requirements

### Requirement: Mostrar ao morador seu próprio histórico demonstrativo
O sistema SHALL apresentar sessões, consumo, valores e solicitações ligados ao perfil de morador selecionado na demonstração.

#### Scenario: Morador consulta histórico
- **WHEN** o morador abre sua visão
- **THEN** vê apenas registros associados à unidade do perfil selecionado e suas recomendações disponíveis

### Requirement: Mostrar ao síndico operação e fechamento
O sistema SHALL apresentar ao síndico o estado simulado dos carregadores, sessões pendentes, consumo e relatório mensal por unidade.

#### Scenario: Síndico confere fechamento
- **WHEN** o síndico seleciona um mês
- **THEN** pode conferir unidades, sessões incluídas, leituras, tarifa, valores e totais

### Requirement: Identificar limites do protótipo
O sistema SHALL identificar dados sintéticos e deixar claro que a seleção de perfil não constitui autenticação segura.

#### Scenario: Perfil de demonstração
- **WHEN** o usuário alterna entre perfis de morador e síndico
- **THEN** a interface informa que a troca de perfil é apenas demonstrativa
