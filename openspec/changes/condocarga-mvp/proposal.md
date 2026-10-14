# Proposal

## Why

Condomínios que compartilham pontos de recarga precisam relacionar o uso a uma unidade, conferir o consumo e preparar valores mensais com clareza. O CondoCarga propõe uma demonstração local desse fluxo, com sessões simuladas, memória de cálculo por unidade e orientação de horários baseada em dados horários identificados como sintéticos.

## What Changes

- Criar o núcleo local para simular identificação RFID, sessões, consumo, tarifa e relatório mensal por unidade.
- Oferecer jornadas separadas para morador e síndico em interface Streamlit.
- Incluir fila FIFO simples e recomendações de menor demanda entre preferências horárias futuras informadas pelo morador; não oferecer reserva nem prometer disponibilidade.
- Carregar cenário demonstrativo sintético e repetível por JSON interno, incluindo medições horárias sintéticas conciliáveis com as leituras totais da sessão.
- Registrar a integração GoodWe apenas como evolução fora desta mudança, condicionada a documentação e acesso confirmados; não implementar adaptador real neste MVP.

## Capabilities

### New Capabilities
- `charging-sessions`: registrar, validar e consultar sessões de recarga vinculadas a RFID, usuário, unidade e carregador.
- `shared-charger-queue`: ordenar solicitações de uso e apresentar disponibilidade simulada.
- `monthly-billing`: calcular consumo e valores e emitir relatório mensal conciliável por unidade.
- `resident-admin-views`: apresentar histórico e recomendações ao morador e dados de operação e fechamento ao síndico.
- `demand-recommendations`: avaliar demanda horária sintética e orientar escolha entre preferências futuras do morador.
- `simulated-ingestion`: carregar sessões e medições horárias sintéticas pelo fluxo validado.

### Modified Capabilities

Nenhuma. O diretório não contém especificações anteriores.

## Impact

- Novo projeto local Python/Streamlit com persistência SQLite.
- Novo conjunto de dados de demonstração sintéticos, sem dados pessoais ou credenciais reais.
- Cálculo monetário determinístico baseado nas leituras totais da sessão, separado das medições horárias usadas pela previsão.
- Pagamento bancário, comando elétrico, autenticação de produção e integração GoodWe real ficam fora desta mudança.
- A entrega acadêmica de exatamente 3 slides e vídeo de 5min00s é confirmada e planejada em tarefa própria, separada do aceite funcional do sistema.
