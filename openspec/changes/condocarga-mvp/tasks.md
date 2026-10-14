# Tasks

## 0. Planejamento OpenSpec (concluído; sem código)

- [x] 0.1 Registrar proposta, capacidades, requisitos comportamentais, design e tarefas no formato OpenSpec; conferir os arquivos e a ordem de dependências.
- [x] 0.2 Limitar esta etapa a documentos; confirmar que nenhum código, dependência, repositório Git ou serviço foi criado.

## 1. Preparação da aplicação

- [x] 1.1 Inicializar o projeto Python e sua estrutura modular proposta em `design.md`; verificar a árvore e executar o ponto de entrada mínimo local.
- [x] 1.2 Definir dependências e instruções de execução; verificar instalação em ambiente limpo seguindo o README.
- [x] 1.3 Criar schema SQLite e repositórios mínimos; verificar criação de tabelas e persistência após reinício.

## 2. Entrada sintética e cadastros

- [x] 2.1 Criar cadastros de unidade, usuário, RFID fictício, carregador e tarifa; verificar chaves e relações com os dados de demonstração.
- [x] 2.2 Criar `data/demo.json` com sessões sintéticas válidas em horas completas e medições com `session_id`, `charger_id`, intervalo, energia em kWh e origem; verificar 100→112 kWh conciliado como 4+5+3 kWh entre 10:00 e 13:00.
- [x] 2.3 Implementar validação e carga interna idempotente; verificar duas cargas sem duplicação e rejeição diagnóstica de sessão inválida ou série horária não conciliável.

## 3. Sessões e fila

- [x] 3.1 Implementar resolução de RFID ativo para usuário e unidade; verificar cartão desconhecido/inativo e só criar sessão após autorização.
- [x] 3.2 Implementar início/encerramento com estados `ACTIVE` e `CLOSED`; verificar falha de encerramento que mantém sessão ativa e carregador ocupado, seguida de encerramento corrigido.
- [x] 3.3 Validar horários, leituras, consumo e deduplicação; verificar sessão aberta, leitura decrescente, horário inválido e reenvio de ID sem cobrança indevida.
- [x] 3.4 Implementar fila FIFO por `created_at` e ID crescente, estados `WAITING`/`CANCELLED`/`SERVED` e início só pelo primeiro; verificar empate, tentativa de ultrapassagem, atendimento/cancelamento liberando a próxima posição e ausência de expiração automática.

## 4. Cálculo e fechamento

- [x] 4.1 Implementar energia de cobrança pela diferença das leituras da sessão, tarifa capturada, `Decimal`, arredondamento por sessão e total em centavos; verificar 12 kWh × R$ 1,00/kWh = R$ 12,00 e que medições horárias não duplicam a cobrança.
- [x] 4.2 Implementar relatório mensal por unidade agrupado pelo mês de encerramento em `America/Sao_Paulo`; verificar sessão que cruza virada do mês e sessão ativa excluída.
- [x] 4.3 Exportar relatório conciliável em CSV; verificar soma dos detalhes igual aos totais por unidade e período.

## 5. Interfaces

- [x] 5.1 Construir jornada do morador para iniciar/encerrar sessão simulada, consultar histórico, solicitar uso e escolher dias/horas de preferência; verificar registros do perfil selecionado e preferência sem reserva.
- [x] 5.2 Construir jornada do síndico para acompanhar carregadores, pendências e fechamento; verificar detalhe, conciliação e exportação mensal.
- [x] 5.3 Sinalizar perfis e dados sintéticos; verificar que nenhuma tela apresenta simulação como autenticação, integração real ou disponibilidade garantida.

## 6. IA de demanda

- [x] 6.1 Agregar energia dos registros horários sintéticos ligados por sessão/carregador e construir referência sem vazamento temporal; verificar que treino usa somente intervalos anteriores ao teste e soma por condomínio/hora.
- [x] 6.2 Implementar e avaliar regressão contra referência com MAE em kWh; verificar avaliação reproduzível e recusa de série horária não conciliável.
- [x] 6.3 Ordenar faixas futuras de uma hora nos próximos sete dias que correspondam às preferências de dias/horas do morador; verificar estimativa e motivo, sem reserva/alocação, sem inferir dados horários reais inexistentes e com fallback à referência ou mensagem de insuficiência.

## 7. Integração funcional e documentação do MVP

- [x] 7.1 Verificar ponta a ponta RFID → unidade → sessão → consumo → relatório nas jornadas de morador e síndico; conferir fila, conciliação e ausência de sessões duplicadas.
- [x] 7.2 Documentar configuração, execução, carga JSON, regra de tarifa, mês de encerramento, medições horárias sintéticas, fila, limites da previsão e exclusões do MVP; verificar instruções num ambiente limpo.

## 8. Entrega de apresentação (separada do aceite funcional)

- [ ] 8.1 Preparar apresentação com exatamente 3 slides sobre solução e decisões técnicas; verificar coerência com o estado implementado e identificar simulação versus integração planejada.
- [ ] 8.2 Ensaiar e gravar vídeo de exatamente 5min00s explicando solução e decisões técnicas; verificar duração total e alinhamento com os três slides. Esta tarefa de plano não produz os slides nem grava o vídeo.

## Fora desta mudança

Integração real GoodWe requer documentação e acesso confirmados, incluindo esclarecimento sobre disponibilidade de dados horários. Ela será proposta numa mudança OpenSpec separada; não condiciona nem integra o aceite do MVP.

