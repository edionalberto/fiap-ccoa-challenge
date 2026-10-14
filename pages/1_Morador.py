import pandas as pd
import streamlit as st

from condocarga.analytics import recommend_hours
from condocarga.bootstrap import ensure_demo_loaded
from condocarga.domain import DomainError
from condocarga.services import (
    active_sessions, cancel_queue_request, create_queue_request, latest_meter,
    list_chargers, list_users, list_vehicles, queue_for_charger, resident_sessions,
    start_session, close_session,
)
from condocarga.settings import TIMEZONE
from zoneinfo import ZoneInfo

st.set_page_config(page_title="Morador | CondoCarga", page_icon="🏠", layout="wide")
ensure_demo_loaded()
st.title("Visão do morador")
st.caption("Perfil selecionável apenas para demonstração; não é autenticação.")
users = list_users()
if not users:
    st.warning("Não há perfis demonstrativos cadastrados.")
    st.stop()
user = st.selectbox("Perfil de demonstração", users, format_func=lambda item: f"{item['name']} · Unidade {item['unit_number']}")
st.session_state["resident_id"] = user["id"]

st.markdown(f"### Unidade {user['unit_number']}")
rows = resident_sessions(user["unit_id"])
if rows:
    display = []
    for row in rows:
        display.append({
            "Início": row["started_at"], "Estado": "Em andamento" if row["status"] == "ACTIVE" else "Encerrada",
            "Veículo": row["vehicle_label"] or "—", "Carregador": row["charger_name"],
            "Leitura inicial (kWh)": row["meter_start_kwh"], "Leitura final (kWh)": row["meter_end_kwh"] or "—",
            "Tarifa (R$/kWh)": row["tariff_brl_per_kwh"],
        })
    st.dataframe(pd.DataFrame(display), hide_index=True, width="stretch")
else:
    st.write("Ainda não há sessões nesta unidade.")

st.markdown("### Carregadores compartilhados")
for charger in list_chargers():
    charger_id = charger["id"]
    active = active_sessions(charger_id)
    queue = queue_for_charger(charger_id)
    with st.container(border=True):
        st.markdown(f"#### {charger['name']}")
        if active:
            current = active[0]
            st.warning(f"Em uso por {current['user_name']} · Unidade {current['unit_number']} desde {current['started_at']}.")
        elif queue:
            st.success("Sem sessão ativa; pedidos em espera.")
        else:
            st.success("Sem sessão ativa nem fila de espera.")

        mine = next((item for item in queue if item["user_id"] == user["id"]), None)
        if queue:
            st.write("Fila atual:")
            st.dataframe(pd.DataFrame([{"Posição": idx, "Morador": item["user_name"], "Unidade": item["unit_number"],
                                        "Solicitado em": item["created_at"]} for idx, item in enumerate(queue, start=1)]),
                         hide_index=True, width="stretch")
        if mine:
            position = next(i for i, item in enumerate(queue, start=1) if item["request_id"] == mine["request_id"])
            st.info(f"Sua solicitação está na posição {position}.")
            if st.button("Cancelar minha solicitação", key=f"cancel-{charger_id}"):
                try:
                    cancel_queue_request(mine["request_id"], user["id"])
                    st.success("Solicitação cancelada. A ordem seguinte passa a ser a primeira elegível.")
                    st.rerun()
                except DomainError as exc:
                    st.error(str(exc))
        elif active or queue:
            if st.button("Entrar na fila", key=f"queue-{charger_id}"):
                try:
                    create_queue_request(user["id"], charger_id)
                    st.success("Solicitação registrada no fim da fila.")
                    st.rerun()
                except DomainError as exc:
                    st.error(str(exc))
        elif not active and not queue:
            st.caption("Sem fila: você pode iniciar uma sessão simulada diretamente.")

        eligible_request = queue[0] if queue and not active and queue[0]["user_id"] == user["id"] else None
        has_own_active = next((item for item in active if item["user_id"] == user["id"]), None)
        if has_own_active:
            st.markdown("**Encerrar sua sessão**")
            default_end = str(float(has_own_active["meter_start_kwh"]) + 2.0)
            with st.form(f"close-{charger_id}"):
                meter_end = st.text_input("Leitura final acumulada (kWh)", value=default_end, key=f"end-meter-{charger_id}")
                close_submitted = st.form_submit_button("Tentar encerrar")
            if close_submitted:
                try:
                    quote = close_session(has_own_active["id"], meter_end)
                    st.success(f"Sessão encerrada: {quote['energy_kwh']} kWh · R$ {quote['amount_brl']:.2f}.")
                    st.rerun()
                except DomainError as exc:
                    st.error(f"{exc} A sessão continua ativa e o carregador permanece ocupado.")
        elif not active and (not queue or eligible_request):
            vehicles = list_vehicles(user["unit_id"])
            if not vehicles:
                st.warning("Este perfil não tem veículo fictício cadastrado.")
                continue
            with st.form(f"start-{charger_id}"):
                vehicle = st.selectbox("Veículo da unidade", vehicles, format_func=lambda item: item["label"], key=f"vehicle-{charger_id}")
                meter_start = st.text_input("Leitura inicial acumulada (kWh)", value=latest_meter(charger_id), key=f"start-meter-{charger_id}")
                submitted = st.form_submit_button("Iniciar sessão simulada")
            if submitted:
                try:
                    card_token = f"DEMO-RFID-{user['unit_number']}-{('A' if user['id'] != 'user-bruno' else 'B')}"
                    session_id = start_session(card_token, charger_id, meter_start, vehicle["id"],
                                               started_at=datetime.now(ZoneInfo(TIMEZONE)),
                                               request_id=eligible_request["request_id"] if eligible_request else None)
                    st.success("Sessão aberta e vinculada à unidade.")
                    st.rerun()
                except DomainError as exc:
                    st.error(str(exc))
        elif queue and not active and not eligible_request:
            st.caption("Somente o primeiro morador da fila pode iniciar a próxima sessão.")

st.markdown("### Sugestões entre suas preferências")
st.write("Escolha dias e horas para receber uma estimativa de menor demanda. A sugestão não reserva o carregador nem confirma disponibilidade.")
weekday_labels = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
col_days, col_hours = st.columns(2)
with col_days:
    chosen_days = st.multiselect("Dias preferidos", list(range(7)), format_func=lambda i: weekday_labels[i])
with col_hours:
    chosen_hours = st.multiselect("Horas preferidas", list(range(24)), format_func=lambda hour: f"{hour:02d}:00")
if chosen_days and chosen_hours:
    recommendation = recommend_hours(chosen_days, chosen_hours, limit=8)
    if recommendation["available"]:
        evaluation = recommendation["evaluation"]
        m1, m2, m3 = st.columns(3)
        m1.metric("Método usado", evaluation["selected_method"])
        m2.metric("MAE da regressão", f"{evaluation['model_mae']:.2f} kWh")
        m3.metric("MAE da referência", f"{evaluation['baseline_mae']:.2f} kWh")
        st.dataframe(pd.DataFrame(recommendation["options"]).drop(columns=["method"]), hide_index=True, width="stretch")
        st.caption(recommendation["message"])
    else:
        st.info(recommendation["message"])
else:
    st.info("Selecione pelo menos um dia e uma hora para consultar as estimativas.")

