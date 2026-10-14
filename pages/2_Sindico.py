import pandas as pd
import streamlit as st

from condocarga.bootstrap import ensure_demo_loaded
from condocarga.domain import DomainError
from condocarga.services import (
    active_sessions, available_report_periods, current_tariff,
    list_chargers, monthly_report, queue_for_charger, report_csv, update_tariff,
)

st.set_page_config(page_title="Síndico | CondoCarga", page_icon="📊", layout="wide")
ensure_demo_loaded()
st.title("Visão do síndico")
st.caption("Relatórios calculados a partir das sessões simuladas; não representam cobrança bancária.")

current = float(current_tariff())
with st.form("tariff-form"):
    new_tariff = st.number_input("Tarifa para novas sessões (R$/kWh)", min_value=0.0, value=current, step=0.05, format="%.4f")
    save_tariff = st.form_submit_button("Salvar tarifa")
if save_tariff:
    try:
        applied = update_tariff(str(new_tariff))
        st.success(f"Nova tarifa aplicada às sessões iniciadas daqui em diante: R$ {float(applied):.4f}/kWh.")
    except DomainError as exc:
        st.error(str(exc))

active = active_sessions()
col1, col2, col3 = st.columns(3)
col1.metric("Carregadores", len(list_chargers()))
col2.metric("Sessões ativas", len(active))
col3.metric("Pedidos em espera", sum(len(queue_for_charger(charger["id"])) for charger in list_chargers()))

st.markdown("### Operação atual")
if active:
    st.dataframe(pd.DataFrame([{"Morador": row["user_name"], "Unidade": row["unit_number"],
                                "Veículo": row["vehicle_label"] or "—", "Carregador": row["charger_name"],
                                "Início": row["started_at"], "Leitura inicial (kWh)": row["meter_start_kwh"]}
                               for row in active]), hide_index=True, width="stretch")
else:
    st.write("Nenhuma sessão está ativa.")

for charger in list_chargers():
    queue = queue_for_charger(charger["id"])
    if queue:
        with st.expander(f"Fila — {charger['name']}", expanded=False):
            st.dataframe(pd.DataFrame([{"Posição": idx, "Morador": row["user_name"], "Unidade": row["unit_number"],
                                        "Solicitado em": row["created_at"]} for idx, row in enumerate(queue, start=1)]),
                         hide_index=True, width="stretch")

st.markdown("### Fechamento mensal por unidade")
periods = available_report_periods()
selected_period = st.selectbox("Mês de encerramento", periods)
year, month = (int(part) for part in selected_period.split("-"))
report = monthly_report(year, month)
unit_rows = [{"Unidade": row["unit_number"], "Sessões": len(row["sessions"]),
              "Consumo (kWh)": f"{row['energy_kwh']:.3f}", "Valor variável (R$)": f"{row['amount_brl']:.2f}"}
             for row in report["units"]]
st.dataframe(pd.DataFrame(unit_rows), hide_index=True, width="stretch")
col_energy, col_amount = st.columns(2)
col_energy.metric("Consumo do período", f"{report['energy_kwh']:.3f} kWh")
col_amount.metric("Total variável", f"R$ {report['amount_brl']:.2f}")

with st.expander("Memória de cálculo por sessão", expanded=True):
    details = []
    for unit in report["units"]:
        for row in unit["sessions"]:
            details.append({"Unidade": row["unit_number"], "Morador": row["user_name"], "Veículo": row["vehicle_label"] or "—",
                            "Sessão": row["id"], "Carregador": row["charger_name"], "Encerrada": row["ended_at"],
                            "Leituras (kWh)": f"{row['meter_start_kwh']} → {row['meter_end_kwh']}",
                            "Consumo (kWh)": f"{row['energy_kwh']:.3f}", "Tarifa (R$/kWh)": row["tariff_brl_per_kwh"],
                            "Valor (R$)": f"{row['amount_brl']:.2f}"})
    if details:
        st.dataframe(pd.DataFrame(details), hide_index=True, width="stretch")
    else:
        st.write("Nenhuma sessão válida foi encerrada neste mês. As unidades sem uso ficam com valor variável zero.")

st.download_button("Baixar fechamento CSV", data="\ufeff" + report_csv(report), file_name=f"condocarga-fechamento-{selected_period}.csv",
                   mime="text/csv; charset=utf-8", width="content")
st.caption("Regra: energia = leitura final − inicial; valor por sessão = energia × tarifa capturada no início, arredondado em centavos. O mês segue a data local de encerramento em America/Sao_Paulo.")

