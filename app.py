from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st

from condocarga.bootstrap import ensure_demo_loaded, measurement_count
from condocarga.services import active_sessions, all_sessions, list_units
from condocarga.settings import TIMEZONE

st.set_page_config(page_title="CondoCarga", page_icon="⚡", layout="wide")
ensure_demo_loaded()

st.title("⚡ CondoCarga")
st.subheader("Gestão demonstrativa de recargas compartilhadas")
st.info("Este protótipo usa cadastros e medições sintéticas. Não se conecta ao HCA G2 nem controla carregadores.")

units = list_units()
sessions = all_sessions()
active = active_sessions()
closed = sum(row["status"] == "CLOSED" for row in sessions)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Unidades de demonstração", len(units))
col2.metric("Sessões encerradas", closed)
col3.metric("Sessões ativas", len(active))
col4.metric("Medições horárias sintéticas", measurement_count())

st.markdown("### Jornadas")
left, right = st.columns(2)
with left:
    st.markdown("**Morador**")
    st.write("Consulte o histórico da unidade, inicie uma sessão simulada, entre na fila e veja sugestões entre suas preferências horárias.")
    st.page_link("pages/1_Morador.py", label="Abrir visão do morador", icon="🏠")
with right:
    st.markdown("**Síndico**")
    st.write("Acompanhe carregadores e sessões, ajuste a tarifa usada em novas sessões e confira o relatório mensal por unidade.")
    st.page_link("pages/2_Sindico.py", label="Abrir visão do síndico", icon="📊")

st.markdown("### Fluxo")
st.code("RFID simulado → usuário/unidade → sessão → leitura total → consumo × tarifa → relatório mensal\n                                      ↘ medições horárias sintéticas → previsão → sugestão orientativa", language="text")
local_now = datetime.now(ZoneInfo(TIMEZONE)).strftime("%d/%m/%Y %H:%M %Z")
st.caption(f"Fuso de operação: {TIMEZONE}. Horário local agora: {local_now}.")
