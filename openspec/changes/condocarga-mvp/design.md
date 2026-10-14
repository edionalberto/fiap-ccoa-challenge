# Design

## Context

O diretório do projeto estava vazio, sem código, specs ou histórico Git. O MVP é uma aplicação local para um condomínio e usa registros sintéticos. A proposta explica a necessidade; este documento registra decisões técnicas para as capacidades especificadas nesta mudança.

## Goals / Non-Goals

**Goals:**
- Separar regra de negócio, persistência, interfaces e análise.
- Demonstrar RFID → unidade → sessão → consumo → relatório mensal.
- Comparar uma previsão horária com referência simples em dados horários suficientes para avaliação temporal.
- Reproduzir cenários sem equipamento físico nem serviço externo.

**Non-Goals:**
- Acesso elétrico ou controle remoto do carregador.
- Reservas, agenda, promessa de disponibilidade futura ou alocação automática.
- Pagamentos, autenticação de produção, múltiplos condomínios, custos fixos, perdas ou rateio.
- Afirmar integração, precisão operacional ou benefício real sem dados e acesso correspondentes.

## Decisions

1. **Aplicação:** Python com Streamlit para as jornadas locais de morador e síndico; SQLite para persistir cadastros, credenciais fictícias, carregadores, sessões, medições, pedidos e tarifa.
2. **Módulos:** `condocarga/domain` guarda estados e validações; `repositories` persiste SQLite; `services` coordena sessões e fechamento; `adapters/simulated` recebe eventos demonstrativos; `analytics` agrega e avalia previsão; `pages` e `app.py` compõem a interface. A integração GoodWe fica fora desta mudança e só poderá ser planejada com documentação confirmada.
3. **Dados demonstrativos:** `data/demo.json` será JSON interno versionado, não importador da interface. IDs de origem permitem repetição idempotente. RFID será fictício. O arquivo contém sessões alinhadas a horas completas para o perfil horário sintético, sem alegar que equipamento real ofereça esse formato.
4. **Medições horárias:** entidade mínima `HourlyMeasurement(session_id, charger_id, interval_start, interval_end, energy_kwh, source)`. `interval_start` e `interval_end` usam timestamp ISO 8601 com offset; `energy_kwh` é decimal não negativo; `source` é `synthetic` no MVP. Cada intervalo sintético é uma hora local completa. Medições ligadas à mesma sessão/carregador não se sobrepõem e sua energia soma exatamente `meter_end_kwh - meter_start_kwh`. Exemplo: sessão 10:00–13:00, leituras 100→112 kWh, intervalos 4+5+3=12 kWh. O cálculo de cobrança continua usando as duas leituras totais da sessão; as medições são usadas para agregação/avaliação horária. Uma futura fonte GoodWe só terá perfil horário quando sua documentação e dados confirmarem essa granularidade; sem isso não haverá distribuição inventada nem previsão horária atribuída a medições reais inexistentes.
5. **Sessões e fila:** sessão só tem estados `ACTIVE` e `CLOSED`. Uma tentativa de encerramento com horário ou leitura inválidos é recusada com mensagem, preserva `ACTIVE` e mantém o carregador ocupado; nenhum processo de correção administrativa é criado. Registro inválido na carga JSON é rejeitado com diagnóstico e não vira sessão cobrável. Solicitações têm estados `WAITING`, `CANCELLED`, `SERVED`, sem expiração. Fila ordena por `created_at` crescente e desempata pelo ID estável crescente. Se houver espera, só a primeira solicitação pode iniciar; ao iniciar, pedido muda para `SERVED`. Cancelar a primeira remove-a da fila ativa e habilita o próximo. Seleção de perfil é somente demonstração.
6. **Tempo e cobrança:** timestamps ISO 8601 com offset e fuso `America/Sao_Paulo` para classificar o mês de encerramento. Guardar tarifa capturada no início como decimal textual, energia com precisão explícita e valores em centavos inteiros; multiplicar com `Decimal` e arredondar por sessão. O relatório mensal agrega pelo mês de encerramento, sem rateio, e é CSV calculado/exportável, não liquidação nem processo de fechamento imutável/reabertura.
7. **IA e preferências:** alvo é consumo horário total previsto a partir da soma de medições sintéticas por intervalo e condomínio. Referência: média histórica por faixa equivalente, calculada somente no treino. Regressão compara-se por MAE em kWh com split temporal. Morador fornece dias da semana e horas do dia preferidos; a aplicação lista candidatos de uma hora nos próximos sete dias locais e os ordena pela demanda estimada. Não há agenda/reserva, controle de duração, promessa de disponibilidade ou mudança automática de fila. Se faltar perfil horário ou histórico suficiente, informar limitação; se regressão não superar a referência, usar referência ou não recomendar.
8. **Exportação:** priorizar CSV conciliável por unidade e período; não inclui pagamento bancário.
9. **Verificação de implementação:** testes de unidade cobrem regras, fila, intervalo e cálculo; integração cobre persistência, idempotência e fechamento. Casos para testes estão descritos nas especificações e tarefas. Os testes serão criados e executados durante implementação, não nesta revisão de planejamento.

## Risks / Trade-offs

- [Dados sintéticos não representam demanda real] → rotular origem e não reivindicar precisão no mundo real.
- [Dados horários sintéticos podem parecer telemetria real] → marcar `source=synthetic`, manter trilha horária separada das leituras usadas para faturar e não inferir granularidade GoodWe.
- [Fila sem prazo de expiração] → simplicidade do MVP; pedido pode ser cancelado pelo solicitante, sem descarte automático.
- [SQLite e execução local não suportam operação multiusuário de produção] → declarar limite acadêmico e evitar exposição pública.
- [Histórico curto prejudica regressão] → avaliar frente à referência e permitir mensagem de insuficiência.
- [Timezone ou precisão decimal inconsistentes] → normalizar timestamps com offset, usar `Decimal` e cobrir virada do mês e arredondamento.
- [Integração GoodWe não documentada] → manter completamente fora do aceite MVP; abrir mudança OpenSpec separada após confirmar documentação e acesso.

## Migration Plan

Não há migração de sistema existente. Na primeira execução, criar o schema SQLite e oferecer ação explícita para carregar o cenário demonstrativo sem duplicar dados. O banco de demonstração pode ser recriado pelo procedimento documentado; dados reais não entram no seed.

## Open Questions

Não há decisão aberta que bloqueie o aceite do MVP descrito. A única dependência material futura é obter documentação e acesso GoodWe para decidir se e como criar mudança OpenSpec separada de integração. A granularidade horária real permanece desconhecida e não é requisito deste MVP.

