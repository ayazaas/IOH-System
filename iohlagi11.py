import streamlit as st
import pandas as pd
import numpy as np
import io
import requests
import datetime
import json
from fpdf import FPDF
from datetime import datetime as dt

# ==========================================
# CUSTOM FPDF CLASS DENGAN FOOTER
# ==========================================
class FPDF_WithFooter(FPDF):
    """Custom FPDF class dengan footer di setiap halaman"""
    def __init__(self):
        super().__init__()
        self.footer_text = "© 2026 IOH Partner System | Design by Friza&Rizka"
    
    def footer(self):
        """Override footer method untuk tampilkan footer di setiap halaman"""
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, self.footer_text, align="C")

# ==========================================
# 0. KONFIGURASI LINK EXCEL
# ==========================================
URL_MASTER_EXCEL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTXjbBupsr-NmmKsYDc38D9DNfpAFdSfw3Kd9PynDlq01uSRaoyAhnwqWQWM1Jsqw/pub?output=xlsx"

# ==========================================
# 1. KONFIGURASI HALAMAN & CSS
# ==========================================
st.set_page_config(page_title="IOH Super System", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .kpi-card { background-color: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .metric-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; margin-bottom: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
    .card-success { border-left: 5px solid #10b981; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. FUNGSI-FUNGSI UTAMA (LOGIC)
# ==========================================

def format_currency(value):
    if value is None or value == 0: return "Rp 0"
    return f"Rp {int(value):,}".replace(",", ".")

def format_decimal(value):
    return f"{float(value):.2f}"

def format_idr_jt(value):
    return format_currency(value)

def normalize_transaction_id(trx_id):
    if pd.isna(trx_id) or trx_id == "" or str(trx_id).upper() == "NAN": return None
    return str(trx_id).strip().lstrip('0') or '0'

def apply_kpi_cap(kpi_value):
    return max(70, min(110, kpi_value))

def calculate_kpi_percentage(target, actual):
    if target <= 0: return 0
    return (actual / target) * 100

def calculate_weighted_score(trade_supply, m2s_absolute, rgu_ga):
    return (trade_supply * 0.4) + (m2s_absolute * 0.4) + (rgu_ga * 0.2)

def get_score_multiplier(weighted_score, mapping):
    for slab in mapping:
        if slab["min"] <= weighted_score <= slab["max"]:
            return slab["value"]
    return 0

def get_sla_tariff(tertiary_inner_pct, sla_tariff_config):
    for slab in sla_tariff_config:
        if slab["min"] <= tertiary_inner_pct <= slab["max"]:
            return slab["rate"]
    return sla_tariff_config[-1]["rate"]

def calculate_compliance_index(ach_rgu_ga, growth_prepaid_revenue):
    ach_score = 1.0 if ach_rgu_ga >= 0.80 else 0
    growth_score = 0.8 if growth_prepaid_revenue < 0 else 1.0
    return (0.5 * ach_score) + (0.5 * growth_score), ach_score, growth_score

def get_score_compliance(compliance_index):
    if compliance_index < 0.9: return 0
    return 1.0 if compliance_index == 1.0 else 0.9

def calculate_metrics(config, achievement):
    # Extract KPI data
    kpis = ["Trade Supply", "M2S Absolute", "RGU GA FWA"]
    pcts = {}
    for k in kpis:
        data = achievement.get(k, {"target": 0, "actual": 0})
        pcts[k] = calculate_kpi_percentage(data.get("target", 0), data.get("actual", 0)) if isinstance(data, dict) else data

    # Logic
    capped = {k: apply_kpi_cap(pcts[k]) for k in kpis}
    weighted = calculate_weighted_score(capped["Trade Supply"], capped["M2S Absolute"], capped["RGU GA FWA"])
    mult = get_score_multiplier(weighted, config["score_multiplier_mapping"])
    tariff = get_sla_tariff(achievement.get("tertiary_inner_percentage", 0), config["sla_tariff"])
    comp_idx, ach_s, gro_s = calculate_compliance_index(achievement.get("ach_rgu_ga", 0), achievement.get("growth_prepaid_revenue", 0))
    score_comp = get_score_compliance(comp_idx)
    
    final_fee = mult * tariff * config["prepaid_revenue"] * score_comp
    
    return {
        "kpi_percentage": pcts, "kpi_capped": capped, "weighted_score": weighted,
        "score_multiplier": mult, "sla_tariff": tariff, "sla_tariff_pct": tariff*100,
        "compliance_index": comp_idx, "ach_score": ach_s, "growth_score": gro_s,
        "score_compliance": score_comp, "final_fee": final_fee
    }

@st.cache_data(ttl=60)
def load_all_sheets(url):
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return pd.read_excel(io.BytesIO(r.content), sheet_name=None, engine='openpyxl')
    except Exception as e:
        st.error(f"Gagal memuat Excel: {e}")
        return None

def get_sheet_fuzzy(dfs, key):
    if not dfs: return None
    for k in dfs.keys():
        if key.upper() in k.upper().replace(" ", ""): return dfs[k]
    return None

def get_kpi_values(df, region, keyword):
    # Dummy logic for example (replace with your existing complex logic if needed)
    return 1000, 850 

def calculate_transaction_match(dfs, region, transaction_types):
    # Simplified placeholder
    return 100, 5000000, 4800000

def get_daily_saldo_data_indosat(df, region, target_month_idx):
    return pd.DataFrame(), 10000000, pd.DataFrame()

def calculate_cost_shortfall(config, achievement):
    total_cost = 0
    breakdown = {}
    for metric in config["kpi_metrics"]:
        m_name = metric["name"]
        target = metric["target"]
        cost_unit = metric.get("cost_per_unit", 0)
        actual = achievement.get(m_name, {}).get("actual", 0) if isinstance(achievement.get(m_name), dict) else 0
        shortfall = max(0, target - actual)
        cost = cost_unit if m_name == "Trade Supply" and shortfall > 0 else shortfall * cost_unit
        breakdown[m_name] = {"shortfall": shortfall, "cost_per_unit": cost_unit, "total_cost": cost}
        total_cost += cost
    return {"total_cost": total_cost, "breakdown": breakdown}

def calculate_income_gain_from_kpi_improvement(config, achievement, metric_name):
    return 500000 # Dummy

def generate_pdf_report_comprehensive(wilayah, mitra, session_data):
    pdf = FPDF_WithFooter()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"REPORT IOH - {wilayah}", ln=True, align="C")
    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# 3. INITIALIZATION & DATA LOADING
# ==========================================
if "calculator_achievement" not in st.session_state: st.session_state.calculator_achievement = {}
if "monthly_total_benefits" not in st.session_state: st.session_state.monthly_total_benefits = {k.upper(): 0 for k in ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]}
if "kpi_interventions" not in st.session_state: st.session_state.kpi_interventions = {}
if "tds_growth_brackets" not in st.session_state: st.session_state.tds_growth_brackets = [{"min_growth": 3.0, "max_growth": 5.0, "fee_percent": 2.5}]
if "third_income_items" not in st.session_state: st.session_state.third_income_items = []
if "third_income_enabled" not in st.session_state: st.session_state.third_income_enabled = False

DEFAULT_REGION_CONFIG = {
    "kpi_metrics": [
        {"name": "Trade Supply", "weight": 0.40, "target": 1000, "cost_per_unit": 0},
        {"name": "M2S Absolute", "weight": 0.40, "target": 500, "cost_per_unit": 0},
        {"name": "RGU GA FWA", "weight": 0.20, "target": 200, "cost_per_unit": 0}
    ],
    "score_multiplier_mapping": [
        {"min": 105, "max": 999, "value": 1.05, "label": "≥ 105"},
        {"min": 80, "max": 104.99, "value": 1.0, "label": "80 – <105"},
        {"min": 70, "max": 79.99, "value": 0.8, "label": "70 – <80"},
        {"min": 0, "max": 69.99, "value": 0, "label": "< 70"}
    ],
    "sla_tariff": [
        {"min": 0.50, "max": 1.0, "rate": 0.0125, "label": "> 50%"},
        {"min": 0, "max": 0.40, "rate": 0.0080, "label": "< 40%"}
    ],
    "prepaid_revenue": 0
}

if "kpi_calculator_config" not in st.session_state:
    st.session_state.kpi_calculator_config = {"month": "FEBRUARI 2026", "regions": {"DAWARBLANDONG": DEFAULT_REGION_CONFIG.copy()}}

# ==========================================
# 4. SIDEBAR
# ==========================================
with st.sidebar:
    st.header("🔄 Sinkronisasi")
    if st.button("Refresh Data Excel"): st.cache_data.clear(); st.rerun()
    dfs = load_all_sheets(URL_MASTER_EXCEL)
    if not dfs: st.stop()
    
    wilayah = "DAWARBLANDONG"
    operator_choice = st.radio("📡 Pilih Operator", ["🔴 Indosat", "🔵 Tri (3)"], horizontal=True)
    st.session_state.selected_operator = "Indosat" if "Indosat" in operator_choice else "Tri"
    
    pilih_bulan = st.selectbox("Pilih Bulan", ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"], index=1)
    bulan_idx = {"Januari": 1, "Februari": 2, "Maret": 3, "April": 4, "Mei": 5, "Juni": 6, "Juli": 7, "Agustus": 8, "September": 9, "Oktober": 10, "November": 11, "Desember": 12}[pilih_bulan]

    st.divider()
    config = st.session_state.kpi_calculator_config["regions"][wilayah]
    config["prepaid_revenue"] = st.number_input("Prepaid Revenue (Rp)", value=config["prepaid_revenue"], step=100_000_000)

# ==========================================
# 5. MAIN TABS
# ==========================================
st.title("🏢 IOH Partner Super System")

tab_sla, tab_fix, tab_tactical, tab_total, tab_biaya = st.tabs(["💰 SLA/KPI Insentif", "📈 Fix Income", "🎯 Tactical Income", "💵 Total Income", "⚡ Biaya + Strategi"])

# --- TAB 1: SLA/KPI ---
with tab_sla:
    st.subheader(f"🧮 Kalkulator Strategi: {wilayah}")
    
    # PERBAIKAN DI SINI: Definisikan result_maksimal di awal scope tab_sla
    maksimal_achievement_data = {}
    for metric in config["kpi_metrics"]:
        m_name = metric["name"]
        maksimal_achievement_data[m_name] = {"target": metric["target"], "actual": int(metric["target"] * 1.1)}
    
    maksimal_achievement_data.update({
        "tertiary_inner_percentage": 0.55,
        "ach_rgu_ga": 0.85,
        "growth_prepaid_revenue": 0.05
    })
    
    # Hitung scenario maksimal agar variabel result_maksimal SELALU ada
    result_maksimal = calculate_metrics(config, maksimal_achievement_data)

    calc_mode = st.radio("Mode", ["🎯 Skenario Maksimal", "⚙️ Skenario Custom"], horizontal=True)

    if calc_mode == "🎯 Skenario Maksimal":
        st.write("Menampilkan perhitungan jika pencapaian 110%.")
        st.metric("Final Fee Maksimal", format_currency(result_maksimal['final_fee']))
        # Simpan untuk session
        current_result = result_maksimal
    else:
        st.markdown("#### Input Custom")
        kpi_inputs = {}
        for m in config["kpi_metrics"]:
            k_name = m["name"]
            c1, c2 = st.columns(2)
            with c1: target_val = st.number_input(f"Target {k_name}", value=m["target"], key=f"t_{k_name}")
            with c2: actual_val = st.number_input(f"Actual {k_name}", value=0, key=f"a_{k_name}")
            kpi_inputs[k_name] = {"target": target_val, "actual": actual_val}
        
        # Tambahan input compliance
        kpi_inputs["tertiary_inner_percentage"] = st.slider("Tertiary Inner %", 0.0, 1.0, 0.5)
        kpi_inputs["ach_rgu_ga"] = st.slider("ACH RGU GA %", 0.0, 1.0, 0.8)
        kpi_inputs["growth_prepaid_revenue"] = st.number_input("Growth %", value=0.0) / 100
        
        st.session_state.calculator_achievement = kpi_inputs
        current_result = calculate_metrics(config, kpi_inputs)
        st.metric("Final Fee Custom", format_currency(current_result['final_fee']))

    # Bagian simpan session state (Tidak akan NameError lagi)
    st.session_state.tab1_result_maksimal = result_maksimal
    st.session_state.tab1_final_fee_maksimal = result_maksimal.get("final_fee", 0)
    st.session_state.final_fee = current_result['final_fee']
    st.session_state.tab1_final_fee_custom = current_result['final_fee']

# --- TAB-TAB LAIN (Placeholder Sesuai Struktur Anda) ---
with tab_fix: st.write("Tab Fix Income")
with tab_tactical: st.write("Tab Tactical Income")
with tab_total: 
    total_fix = st.session_state.monthly_total_benefits.get(pilih_bulan.upper(), 0)
    st.metric("Total Income (SLA + Fix)", format_currency(st.session_state.get("final_fee", 0) + total_fix))

with tab_biaya:
    st.write("Biaya & Strategi")
    if st.button("📄 EXPORT PDF"):
        st.success("PDF Generated (Simulasi)")

# ==========================================
# FOOTER
# ==========================================
st.markdown('<div style="text-align:center; padding:20px; color:#666;">© 2026 IOH Partner System</div>', unsafe_allow_html=True)
