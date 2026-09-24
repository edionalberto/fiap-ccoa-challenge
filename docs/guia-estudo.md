# Guia de estudo e fala de 3 minutos

Édion Alberto Torres — RM 570560 — CondoCarga

Este guia acompanha a pesquisa da Sprint 01. O slide apresenta uma proposta, não um sistema já implementado. Para o pitch posterior de validação técnica, atualizar a fala com o que tiver sido desenvolvido e medido até a prova.

## O que estudar primeiro

| Tema | Entendimento necessário | Onde consultar |
|---|---|---|
| Problema | Medição precisa ser vinculada a uma unidade para produzir cobrança conferível | README, seções 1 e 2 |
| Mercado | ChargePoint, Wallbox e NeoCharge já possuem ofertas; o projeto não reivindica ineditismo | README, comparação de mercado e fontes 2–5 |
| Energia | kW mede potência; kWh mede energia. 6 kW constantes durante 2 horas correspondem a 12 kWh | Modelo matemático do README |
| Identificação | RFID identifica credencial. O vínculo com apartamento será uma regra do CondoCarga | README, interfaces e modelo de dados |
| Regulação | Art. 550 tem condições; art. 552 não cita OCPP nominalmente; art. 554 admite exploração comercial | README, seção regulatória e fontes 8–9 |
| Integração | Portal SEMS e conexões do equipamento não comprovam contrato público de API | README, pesquisa GoodWe |
| Rateio | Energia × tarifa por sessão; somar centavos por unidade; explicar as exceções | README, seção 4 |
| IA | Prever energia por intervalo requer dados por intervalo; comparar com média histórica | README, seção 5 e fontes 18–20 |

## Sequência da fala

| Tempo | Bloco no slide | Ideia principal |
|---|---|---|
| 0:00–0:35 | Problema | Identificar uso e justificar valores por apartamento |
| 0:35–1:30 | Solução e rateio | Fluxo, fórmula e exceções |
| 1:30–2:25 | IA e decisões | Regressão, referência e limitações |
| 2:25–3:00 | Pesquisa e próxima sprint | Evidências e ordem de implementação |

## Texto para ensaio

### 0:00–0:35

Meu projeto é o CondoCarga, uma proposta de gestão de recargas compartilhadas em condomínios. O problema é relacionar o uso do carregador ao apartamento responsável e justificar os valores do fechamento mensal. O morador precisa compreender seu consumo, e o síndico precisa conferir as sessões. A pesquisa de ChargePoint, Wallbox e NeoCharge mostrou que essas necessidades já são atendidas por diferentes modelos comerciais. Meu recorte acadêmico é construir um fluxo simples e verificável para o Challenge GoodWe.

### 0:35–1:30

A arquitetura separa carregador, conectividade, aplicação e interface. O identificador RFID será vinculado ao usuário e à unidade. A sessão registrará horários, leituras e a tarifa aplicada. O consumo será a diferença entre leitura final e inicial, em quilowatts-hora.

No exemplo fictício, doze quilowatts-hora a um real por quilowatt-hora geram doze reais. O relatório soma as sessões por apartamento. Dois veículos da mesma unidade terão sessões separadas, mas um total consolidado. Sem consumo, o valor variável será zero. Uma sessão interrompida só entrará no cálculo quando houver medição confiável.

Escolhi cobrar apenas o componente medido nesta versão. Custos fixos e perdas exigiriam outra política. O fechamento usará o mês de encerramento, com essa regra explícita.

### 1:30–2:25

Para a aplicação, proponho Python, Streamlit e SQLite, combinando processamento, interface local e persistência. A integração real depende de documentação e acesso GoodWe. Na próxima sprint, o protótipo começará com dados sintéticos identificados.

A IA terá uma função específica: recomendar horários de menor demanda entre as preferências do morador. Comparei regressão e detecção de anomalias, e escolhi regressão como primeiro desenvolvimento. A avaliação comparará o erro do modelo com uma média histórica, sempre usando dados anteriores para prever períodos posteriores.

Essa análise exige medições por intervalo. A previsão não será usada para cobrar consumo, reservar vaga ou comandar potência. Sem histórico suficiente, a aplicação informará a limitação e manterá as regras convencionais de uso.

### 2:25–3:00

A Sprint 01 reúne pesquisa de mercado, contexto técnico e regulatório, arquitetura, rateio e papel da IA. A pesquisa também identificou limites: a existência do SEMS não comprova acesso público aos dados necessários, e o software não substitui a verificação da instalação elétrica.

Na Sprint 02, a ordem será organizar os dados, implementar sessões e fechamento, construir as interfaces e avaliar a previsão. A contribuição do CondoCarga é permitir que cada valor seja explicado por sessões e que o histórico apoie uma decisão de uso.

## Perguntas para conferir o entendimento

1. Por que tarifa por kWh? Porque mantém relação direta com energia medida. Tempo conectado pode incluir ociosidade e velocidades diferentes.
2. O rateio quita toda a conta do condomínio? Não. A proposta calcula apenas o componente medido da recarga e declara a exclusão de custos fixos e perdas.
3. A IA é necessária para cobrar? Não. Ela participa da recomendação de horários; cobrança é determinística.
4. Por que não apresentar endpoints SEMS? Porque não foi obtido contrato público oficial verificável nas fontes consultadas.
5. O que uma previsão horária exige? Dados por intervalo, com unidades, horário e origem confiáveis. O total de uma sessão longa não revela sua distribuição por hora.
6. Por que consultar APIs que não serão implementadas agora? O aprofundamento pesquisa alternativas; a decisão de adiar integrações evita ampliar o MVP sem melhorar o núcleo.
7. O sistema já funciona? Nesta entrega há pesquisa e proposta. A implementação está planejada para a Sprint 02.

## Como ensaiar

Leia o README e abra as fontes principais antes de decorar a fala. Explique o exemplo numérico sem ler. Grave um ensaio com cronômetro e ajuste pausas para 3 minutos; o tempo real ainda não foi validado em gravação. Use o slide para lembrar a sequência, sem ler todo o conteúdo. Na prova posterior, substituir promessas por evidências do desenvolvimento realizado.
