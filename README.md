# CondoCarga

Pesquisa e proposta de gestão de recargas compartilhadas em condomínios

**Autor:** Édion Alberto Torres · **RM:** 570560  
**Curso:** Ciência da Computação on-line, FIAP  
**Challenge:** GoodWe 2026, trilha EV ChargeOps  
**Etapa:** Sprint 01 — pesquisa e documentação  
**Data da pesquisa:** 24 de setembro de 2026

O CondoCarga propõe relacionar cada sessão de recarga ao apartamento responsável, calcular seu consumo e produzir um fechamento mensal conferível. A inteligência artificial apoiará a escolha de horários de menor demanda. Nesta sprint, apresento a pesquisa e as decisões que orientarão um protótipo na Sprint 02. Ainda não há sistema funcional, integração GoodWe validada ou resultados de um modelo treinado.

Material de apoio à preparação: [guia de estudo e fala de 3 minutos](docs/guia-estudo.md) e [slide editável](docs/slide-3-minutos.pptx). Esses arquivos apoiam o estudo e não substituem a documentação da Sprint 01. O pitch posterior de validação técnica deverá refletir a implementação existente na data da prova.

## 1. Problema e recorte

Um carregador compartilhado reúne usuários com necessidades diferentes em uma infraestrutura limitada. A gestão precisa saber quem utilizou o equipamento, quanto consumiu e como distribuir os valores. O morador precisa compreender sua cobrança e organizar o uso. Ter energia medida no carregador não basta: é necessário vincular a medição a uma sessão e a uma unidade.

O desafio FIAP/GoodWe propõe transformar esses registros em gestão e inteligência operacional [1]. A documentação de soluções comerciais já oferece cobrança individual e relatórios, confirmando que o problema possui respostas no mercado [2–5]. Portanto, não apresento a proposta como uma invenção inédita. O objetivo acadêmico é projetar um fluxo explicável, adequado ao ecossistema do desafio e aos conhecimentos estudados.

Delimito a primeira versão a um condomínio, usuários fictícios, identificação RFID simulada e fechamento por unidade. Os públicos são o morador e o síndico. Pagamentos bancários, instalação elétrica, aplicativo nativo, autenticação de produção e comando remoto de potência ficam fora do primeiro protótipo. As mesmas questões podem ocorrer em edifícios corporativos e campi, mas esses ambientes não serão implementados nesta versão.

Os desafios operacionais considerados são identificação, disputa pelo uso, registros incompletos, conciliação dos valores e dependência de dados confiáveis. Não realizei entrevistas com moradores: essas necessidades resultam do enunciado e da pesquisa documental, devendo ser validadas em campo antes de uma implantação.

## 2. Frente 1 — Contexto e análise de mercado

**Aprofundamento escolhido: opção A, análise de três soluções existentes.**

### Como uma sessão gera dados

O modelo lógico adotado tem cinco momentos: conexão do veículo, identificação/autorização, início da transferência, acompanhamento e encerramento. Conectar o cabo não significa necessariamente que a energia já esteja sendo transferida. Na proposta, o registro terá estados próprios para distinguir sessão aberta de encerrada.

O HCA G2 oferece início por aplicativo, RFID ou modo automático, conforme a ficha técnica [6]. No kickoff, a GoodWe explicou o registro do cartão e da energia utilizada [1]. A plataforma proposta vinculará o identificador a usuário e unidade, preservando essa associação na sessão.

| Momento | Dado necessário ao CondoCarga | Transformação proposta |
|---|---|---|
| Identificação | Credencial, usuário e unidade | Resolver o vínculo autorizado |
| Início | Sessão, carregador, horário e leitura inicial | Fixar unidade e tarifa da sessão |
| Acompanhamento | Estado e medições por intervalo, se disponíveis | Histórico operacional e análise temporal |
| Encerramento | Horário e leitura final ou energia total documentada | Validar e normalizar consumo |
| Fechamento | Sessões válidas, unidade e tarifa | Somar consumo e valores por mês |

O caminho de captura real pode ser uma API autorizada ou uma interface documentada do equipamento. A existência física dessas conexões não confirma quais dados terceiros podem consultar. Na Sprint 02, eventos sintéticos exercitarão o mesmo modelo interno, sem simular uma API oficial inexistente.

### Soluções pesquisadas

| Solução e mercado da fonte | Problema e funcionalidades documentadas | Modelo de negócio observado | Limites e consequência para a proposta |
|---|---|---|---|
| ChargePoint, página para condomínios | Gestão de vagas atribuídas e compartilhadas, controle de acesso, relatórios de energia e custos, cobrança e compartilhamento de potência [2] | Oferta integrada de equipamento, software e suporte; a propriedade configura políticas de cobrança | Exige avaliar contratação e implantação. A página não comprova compatibilidade com o HCA G2 nem oferta equivalente no Brasil. Aproveito a separação entre políticas de uso e cobrança |
| Wallbox Business Portal, oferta internacional | Gestão de carregadores, locais e usuários; estatísticas e pagamentos por sessão ou fechamento mensal [3] | Portal associado ao ecossistema de carregadores; opções de monetização. A documentação de cobrança mensal consultada descreve comissão por sessão [4] | Portal e processamento de pagamento não têm necessariamente o mesmo custo. Condições variam por serviço/mercado; não extrapolo valores ao Brasil. Aproveito a transparência do histórico por usuário |
| NeoCharge, oferta brasileira para condomínios | Operação por aplicativo, instalação e manutenção pelo fornecedor, reembolso mensal da energia ao condomínio [5] | Recarga como serviço, com cobrança do motorista e contrato de operação | A oferta depende de avaliação da infraestrutura e menciona contrato de 60 meses. É uma proposta comercial específica, não uma regra geral do setor. Aproveito a distinção entre gasto do condomínio e valor cobrado ao usuário |

**Análise:** as três soluções mostram que o desafio não se resume a construir uma tela. É preciso conectar identidade, medição, operação e prestação de contas. Para o CondoCarga, adoto esse fluxo completo, mas deixo a liquidação financeira fora do protótipo. O diferencial acadêmico será tornar os cálculos e as decisões de IA verificáveis, não alegar superioridade sobre plataformas comerciais.

### Modelos de cobrança e seus efeitos

As políticas documentadas pela ChargePoint incluem gratuidade, energia, tempo e taxas por sessão [7]. A cobrança mensal da Wallbox admite tarifa e/ou assinatura [4]. No Brasil, a oferta NeoCharge exemplifica operação com reembolso ao condomínio [5]. Esses casos mostram possibilidades comerciais; não demonstram frequência ou predominância de cada modelo.

| Modelo | Vantagem para gestão | Limitação no condomínio |
|---|---|---|
| Gratuito ao usuário | Pouca fricção de pagamento | O custo precisa ser absorvido por alguém; não distingue consumo individual |
| Por kWh | Relação direta com energia medida | Exige medição e vínculo confiáveis |
| Por tempo conectado | Pode incentivar liberação da vaga | Tempo conectado e energia recebida não são equivalentes |
| Assinatura mensal | Previsibilidade do valor | Uso desigual pode gerar subsídios cruzados |
| Rateio por consumo na cobrança condominial | Permite explicar o valor a partir das sessões | Requer política explícita para exceções e custos não medidos |

**Escolha:** rateio do componente variável por consumo medido. Duas unidades com uso diferente devem receber valores diferentes. Não escolho divisão igual entre apartamentos porque ela desconsidera a energia efetivamente utilizada. Também não escolho cobrança por tempo no MVP porque velocidades de recarga diferentes poderiam produzir custos diferentes para a mesma energia.

## 3. Frente 2 — Ecossistema técnico e regulatório

**Aprofundamento escolhido: opção C, mapeamento de duas APIs complementares.** A pesquisa básica de regulação, HCA G2 e SEMS permanece incluída.

### RN ANEEL 1.000/2021

A página da ANEEL atualizada em abril de 2026 remete ao Capítulo V da RN 1.000/2021 e confirma a exploração comercial com preços negociados [8]. Consultei os artigos em reprodução da norma hospedada pela SEMA/RS, datada de janeiro de 2025 [9]. O texto consolidado direto retornou erro de acesso; essa cópia não permite certificar todas as alterações posteriores.

| Dispositivo | Síntese do texto consultado | Decisão para o projeto |
|---|---|---|
| Art. 550 | Comunicação prévia em caso de nova conexão, mudança de carga ou tensão | Registrar essa verificação na implantação; não generalizar para qualquer situação |
| Art. 552 | Equipamentos não exclusivos de uso privado devem admitir protocolos abertos para comunicação e supervisão/controle remoto | Confirmar enquadramento e compatibilidade antes de integração real |
| Art. 553 | Aplicam-se normas da distribuidora e de órgãos competentes | Software não comprova conformidade da instalação |
| Art. 554 | Admite recarga de veículos de terceiros e exploração comercial | Justifica estudar modelos de cobrança, sem impor uma tarifa |

Não interpreto o art. 552 como imposição nominal de OCPP, nem considero um condomínio automaticamente enquadrado sem análise. A proposta não é um projeto elétrico aprovado. Normas estaduais/municipais e de segurança precisam de verificação específica em uma implantação; o aprofundamento escolhido nesta frente é de APIs, não um laudo regulatório completo.

### Interfaces do HCA G2

A ficha técnica lista Bluetooth, Wi-Fi, duas interfaces RS-485, LAN e RFID como método de início [6]. A página do produto informa integração com SEMS+ para monitoramento e programação [10]. A tabela distingue a capacidade geral da interface da operação específica ainda dependente de documentação.

| Interface | Papel técnico | Utilização possível e limite |
|---|---|---|
| RFID | Identificação por cartão | Vincular credencial à unidade. Não é rede de telemetria nem cadastro de apartamento pronto |
| LAN | Conexão cabeada à rede local | Caminho de conectividade; não prova endpoint ou comando disponível |
| Wi-Fi | Conexão sem fio à rede | Alternativa de conectividade sujeita à cobertura e configuração |
| Bluetooth | Comunicação local de curta distância | Possível configuração/interação próxima, a confirmar no manual da versão |
| RS-485 | Interface serial diferencial | Possível comunicação entre equipamentos; protocolo, registradores e permissões precisam ser documentados |

Escolho separar o adaptador de dados das regras de negócio. Assim, a confirmação posterior da interface real não obriga alterar as fórmulas ou a consolidação por apartamento. A ficha técnica não comprova um contrato público de API.

### Resultado da pesquisa sobre API GoodWe e SEMS

Consultei a página de produto, o catálogo oficial de downloads e o endereço SEMS+ indicado no enunciado [10–12]. A documentação de produto confirma monitoramento, mas o portal não expôs um contrato de API legível na consulta. O catálogo lista manual; as tentativas de abertura do PDF falharam. Não encontrei nessas fontes um contrato público oficial verificável de endpoints de sessões HCA G2, autenticação, paginação e limites. Isso é uma limitação da pesquisa, não prova de inexistência da API.

| Informação desejada | Evidência disponível | Situação para desenvolvimento |
|---|---|---|
| Identificação RFID e energia de recarga | Explicação do kickoff [1] | Confirmar campos e acesso autorizados |
| Monitoramento e programação | Página oficial do produto [10] | Capacidade do produto confirmada; interface de terceiros não confirmada |
| Status, potência e timestamps | Necessidades do modelo propostas pelo enunciado | Esquema e frequência não verificados em API oficial |
| Eventos de início/fim e medições horárias | Necessários ao fluxo e à IA proposta | Dependência de documentação; usar simulação declarada na Sprint 02 |

Antes de integrar, preciso obter da GoodWe/FIAP o contrato autorizado, identificação do modelo/firmware, exemplo anonimizado de resposta, unidades, fuso, limites e política de acesso. Os nomes de campos do CondoCarga serão internos, nunca apresentados como campos oficiais SEMS.

### APIs complementares

| API | Dados e acesso documentados | Uso considerado | Limitação e decisão |
|---|---|---|---|
| Open Charge Map | Localizações de recarga e contribuições como comentários; acesso por chave. O provedor exige atribuição das fontes e licenças [13–14] | Apresentar alternativas próximas quando o morador preferir recarga externa | O FAQ informa que o status não é garantia de disponibilidade ao vivo [14]. A rota de documentação detalhada redirecionou para login. Fica como evolução, sem depender dela no fechamento |
| Google Places API (New) | `evChargeOptions`, quantidade/tipo de conectores, potência máxima, contagens disponíveis e horário da atualização quando fornecidos [15]. Place Details usa `GET https://places.googleapis.com/v1/places/PLACE_ID`, chave e máscara de campos [16]; uso requer faturamento habilitado [17] | Consultar opções e características de recarga externas | Campo ausente não significa zero; contagem de conectores não equivale necessariamente a carros simultâneos. Cobertura, atualização e custos exigem avaliação. Não reservar vagas nem prometer disponibilidade |

**Análise:** as APIs enriquecem localização, mas não resolvem identidade e rateio no condomínio. Implementá-las antes do núcleo aumentaria dependências sem melhorar a conferência da cobrança. Por isso, pesquiso ambas nesta sprint e postergo a integração. Nenhuma chamada autenticada foi executada; os resultados são de consulta à documentação.

## 4. Frente 3 — Arquitetura e modelo de rateio

**Aprofundamento escolhido: opção B, comparação de duas abordagens de IA**, detalhada na próxima seção.

### Arquitetura proposta

![Arquitetura proposta do CondoCarga com quatro camadas e caminhos distintos para cobrança e recomendação](docs/arquitetura.png)

*Figura 1 — Arquitetura proposta. Elaboração para o CondoCarga. A integração física é futura; o protótipo utilizará dados sintéticos.*

| Camada | Responsabilidade | Decisão |
|---|---|---|
| Física | Carregador, cartão e medições | HCA G2 como referência do Challenge; sem comando real no MVP |
| Conectividade | Receber dados e normalizar origem, unidade e horário | Adaptador simulado primeiro; conexão GoodWe condicionada a documentação |
| Aplicação | Validar sessão, persistir, calcular rateio e analisar histórico | Python com módulos separados e SQLite local |
| Apresentação | Histórico do morador, relatório do síndico e recomendação | Streamlit para demonstrar as jornadas com menor esforço de interface |

O fluxo proposto é: identificar a credencial, resolver a unidade, abrir sessão, guardar tarifa, registrar leitura final, validar consumo, calcular valor e agregar no relatório mensal. O histórico alimenta a IA em outro caminho. A previsão orienta horários; nunca substitui energia medida para cobrança.

Escolho um único aplicativo modular porque o projeto é individual. Serviços distribuídos e infraestrutura de produção não são necessários para testar as regras. A seleção de perfil será demonstrativa, sem alegação de autenticação segura. Dados reais de moradores e cartões não integram esta pesquisa.

### Modelo de dados mínimo

| Entidade | Atributos principais | Relação |
|---|---|---|
| Unidade | ID, número | Possui usuários e sessões |
| Usuário/credencial | ID, unidade, credencial opaca fictícia, ativo | Identifica quem inicia uso |
| Carregador | ID, estado simulado | Possui sessões e fila |
| Sessão | ID, unidade no início, usuário, veículo fictício, carregador, horários, leituras, tarifa, estado | Unidade histórica preservada mesmo após mudança cadastral |
| Medição por intervalo | Sessão, início/fim do intervalo, energia em kWh, origem | Alimenta agregação horária; soma conciliada em cenários completos |
| Solicitação | ID, usuário, carregador, criação, estado | Fila cronológica, com ID como desempate |
| Fechamento | Unidade, mês, sessões e totais calculados | Relatório derivado, sem liquidação bancária |

### Fórmulas e política de rateio

Para cada sessão válida `s`:

```text
E_s = leitura_final_kWh - leitura_inicial_kWh
V_s = arredondar_centavos(E_s × tarifa_s)
F_unidade,mês = soma(V_s das sessões válidas da unidade encerradas no mês)
```

`E_s` é energia, em kWh. `tarifa_s` é o preço configurado por kWh, registrado no início da sessão. `V_s` é o valor da sessão, e `F` é o total variável da unidade. Usarei cálculo decimal e arredondamento de meio centavo para cima por sessão; os totais somarão centavos inteiros. A tarifa uniforme pode mudar para sessões futuras, sem reescrever o histórico.

O mês é o de encerramento em `America/Sao_Paulo`. Não divido sessões entre meses no MVP: a regra simplifica conciliação, mas pode deslocar todo o consumo de uma sessão para o mês seguinte. Essa limitação será visível no relatório.

Exemplo inteiramente fictício com tarifa de R$ 1,00/kWh:

| Unidade | Veículo/sessão | Leitura inicial | Leitura final | Energia | Valor |
|---|---|---:|---:|---:|---:|
| 101 | V1 / S1 | 100 kWh | 112 kWh | 12 kWh | R$ 12,00 |
| 101 | V2 / S2 | 112 kWh | 115 kWh | 3 kWh | R$ 3,00 |
| 202 | V3 / S3 | 115 kWh | 123 kWh | 8 kWh | R$ 8,00 |
| 303 | Sem sessão | — | — | 0 kWh | R$ 0,00 |
| Total | | | | 23 kWh | R$ 23,00 |

A unidade 101 recebe R$ 15,00, mesmo com dois veículos. O relatório conserva o detalhe de cada sessão. Esse exemplo não informa uma tarifa de mercado nem economia obtida.

### Exceções e limites

| Caso | Tratamento proposto |
|---|---|
| Sessão interrompida com leitura válida | Cobrar somente energia efetivamente registrada até a interrupção |
| Interrupção sem leitura final confiável | Deixar pendente; não estimar cobrança com IA |
| Unidade sem uso no mês | Valor variável zero, pois não há taxa fixa no modelo |
| Dois veículos da mesma unidade | Sessões distintas, total consolidado no apartamento |
| Evento reenviado | Identificador único impede duplicar consumo e valor |
| Leitura decrescente ou horário inválido | Recusar encerramento e manter sessão ativa para correção |
| Carregador livre com fila | Somente o primeiro pedido pode iniciar; cancelamento libera a ordem |

Não distribuo custos fixos nem perdas neste primeiro cálculo. Logo, o fechamento é do componente medido de recarga, não uma conciliação integral da conta elétrica do condomínio. Uma futura política poderá separar investimento, manutenção e diferença de medição, após decisão explícita de gestão. A tarifa configurada também não deve ser confundida automaticamente com o custo de aquisição de energia.

## 5. IA como apoio à gestão

A aplicação precisa transformar o histórico em uma orientação útil. Pesquisei regressão linear e Isolation Forest nas documentações dos métodos [18–19].

| Abordagem | Problema e técnica | Dados necessários | Impacto esperado e limites |
|---|---|---|---|
| Previsão por regressão | Estimar energia agregada em uma hora futura; ajustar relação entre características e consumo [18] | Energia horária, hora cíclica, dia da semana e histórico anterior | Ordenar faixas preferidas pelo morador por menor demanda prevista. Relações podem ser não lineares; não prevê disponibilidade física com certeza |
| Detecção de anomalias por Isolation Forest | Identificar sessões com combinações incomuns por isolamento em árvores aleatórias [19] | Duração, energia, potência média derivada e contexto de uso | Priorizar revisão do síndico. Uma sessão incomum pode ser legítima; alerta não comprova erro, fraude ou defeito |

**Escolha para a Sprint 02:** regressão como abordagem principal, por sua relação com os conteúdos de modelagem estudados e por apoiar a organização de uso. Detecção de anomalias fica como evolução pesquisada. Não utilizarei um chatbot genérico como substituto da análise de consumo.

O alvo será energia em kWh em intervalos regulares de uma hora. Para evitar inventar distribuição temporal, o conjunto sintético deverá conter medições por intervalo conciliáveis com as sessões. Se a integração real disponibilizar apenas totais, a previsão horária exigirá outra fonte de medição ou revisão do alvo.

O processo de avaliação utilizará treino anterior ao teste, conforme a orientação de validação temporal [20]. A referência será a média histórica por faixa calculada apenas no treino. Compararei o erro absoluto médio em kWh. Variáveis e estatísticas não poderão incluir dados futuros; previsões negativas terão tratamento documentado e avaliado. O teste final será separado da seleção de alternativas, evitando escolher o modelo com base no mesmo período usado para relatar seu desempenho.

O morador informará janelas de preferência. A recomendação ordenará essas faixas e explicará a estimativa, sem reserva nem alteração automática da fila. Se o modelo não superar a referência na validação, a aplicação usará a referência identificada como tal; sem histórico suficiente, informará indisponibilidade de previsão.

**Papel estrutural:** a saída analítica participa da decisão de quando tentar recarregar. Retirar a IA elimina essa recomendação baseada em previsão, embora o registro e a cobrança continuem funcionando. Isso preserva o uso operacional mesmo quando a análise falha. Ainda não há MAE medido, redução de picos demonstrada ou economia comprovada.

## 6. Plano da Sprint 02

| Ordem | Desenvolvimento | Tecnologia proposta | Evidência de conclusão |
|---|---|---|---|
| 1 | Estrutura local, esquema e dados demonstrativos | Python, SQLite, JSON interno | Carga reproduzível sem duplicação e histórico após reinício |
| 2 | Identificação, início/fim e fila | Funções Python e transações SQLite | Credencial válida, um uso por carregador e respeito à fila |
| 3 | Cálculo, exceções e fechamento | Decimal, relatório CSV | Soma por unidade conciliada com sessões, inclusive virada do mês |
| 4 | Jornadas de morador e síndico | Streamlit | Percurso completo sem editar dados manualmente no código |
| 5 | Histórico horário, referência e regressão | Python e scikit-learn | Avaliação temporal reproduzível e recomendação identificada |
| 6 | Verificação integrada e documentação | Testes de regras e execução documentada | Cenários de erro, duplicação, duas unidades e ausência de histórico conferidos |

Integração real GoodWe depende de documentação e acesso. APIs de localização, pagamentos e detecção de anomalias ficam em evolução posterior, sem impedir o aceite do protótipo.

As decisões aplicam conteúdos das fases estudadas: lógica para autorização e validação, listas/dicionários para organizar registros, modelagem matemática para energia e valores, regressão para previsão e conceitos de energia para distinguir kW de kWh. SQLite e Streamlit complementam a implementação proposta, sem serem apresentados como exigências do curso.

## 7. Método, autoria e limites

Esta pesquisa é documental. As páginas comerciais descrevem ofertas dos próprios fornecedores, não testes independentes. Diferencio capacidades publicadas, inferências para o projeto e funcionalidades planejadas. Fontes com acesso incompleto estão identificadas; não listo entrevistas inexistentes nem medições que não realizei.

Utilizei apoio de IA para organizar a pesquisa, comparar alternativas e revisar a redação. As opções de aprofundamento e as decisões estão expostas para leitura crítica e defesa do autor. A proposta deve ser compreendida e revisada antes da submissão, especialmente os limites do rateio e da integração.

## 8. Fontes consultadas

Consultas realizadas em 24/09/2026. Os links a documentação de bibliotecas usam a versão publicada no momento da consulta; a versão instalada será fixada na Sprint 02.

1. FIAP/GoodWe. Enunciado da Sprint 01 fornecido no AVA; playbook “1CC — EV Challenge GoodWe+FIAP 2026”, p. 7–10 e 13; apresentação GoodWe, p. 16; transcrição do kickoff de 08/04/2026, especialmente 39:30–40:25 e 45:33–50:04. Materiais fornecidos pelo aluno, não redistribuídos neste repositório.
2. [ChargePoint — EV charging for condo properties](https://www.chargepoint.com/solutions/condos).
3. [Wallbox — Business Portal](https://wallbox.com/en_uk/my-wallbox-business-portal).
4. [Wallbox — Pay per Month](https://support.wallbox.com/na/knowledge-base/how-to-set-the-pay-per-month-billing-solution-for-your-chargers/).
5. [NeoCharge — Eletroposto em condomínio](https://www.neocharge.com.br/eletroposto-condominio).
6. [GoodWe — HCA G2 Datasheet EN](https://en.goodwe.com/Ftp/EN/Downloads/Datasheet/GW_HCA-G2_Datasheet-EN.pdf). Dados técnicos recuperados na consulta indexada do documento oficial.
7. [ChargePoint — Pricing policies and fees](https://www.chargepoint.com/drivers/support/faqs/what-are-pricing-policies-and-fees-i-should-be-aware).
8. [ANEEL — Veículos elétricos](https://www.gov.br/aneel/pt-br/assuntos/veiculos-eletricos). Página atualizada em 30/04/2026.
9. [RN ANEEL 1.000/2021 — reprodução hospedada pela SEMA/RS](https://sema.rs.gov.br/upload/arquivos/202501/24140257-resolucao-aneel-1000.pdf), p. 106, artigos 550–554. Cópia datada de 24/01/2025; limitação de atualização declarada na seção 3.
10. [GoodWe — HCA G2 Series](https://en.goodwe.com/hca-g2).
11. [GoodWe — Catálogo de downloads HCA G2](https://br.goodwe.com/download-hca-g2-series). Catálogo consultado; conteúdo integral do manual não recuperado.
12. [GoodWe — SEMS+](https://semsplus.goodwe.com/). Endereço consultado; não apresentou contrato de API legível na consulta.
13. [Open Charge Map — Developing](https://www.openchargemap.org/develop).
14. [Open Charge Map — FAQ e orientações de acesso](https://community.openchargemap.org/t/frequently-asked-questions-faq/221). Serviço comunitário oficial; observar autoria das respostas e ausência de garantia de disponibilidade ao vivo.
15. [Google Places — EVChargeOptions e ConnectorAggregation](https://developers.google.com/maps/documentation/places/web-service/reference/rest/v1/places#EVChargeOptions).
16. [Google Places — Place Details](https://developers.google.com/maps/documentation/places/web-service/place-details).
17. [Google Places — Usage and Billing](https://developers.google.com/maps/documentation/places/web-service/usage-and-billing).
18. [scikit-learn — LinearRegression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LinearRegression.html).
19. [scikit-learn — IsolationForest](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html).
20. [scikit-learn — TimeSeriesSplit](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html).
