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
URL_MASTER_EXCEL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSeWh8Uyg4tZaHnHB3YKR1V1B_LF0WYuzNnFfeVChgDu-nBCN_g9ndw0sLhX3lhrlP9ODT9zzwUnAE8/pub?output=xlsx"

# ==========================================
# 1. KONFIGURASI HALAMAN & CSS (TERANG/PUTIH)
# ==========================================
st.set_page_config(page_title="IOH Super System", layout="wide")

st.markdown("""
    <style>
    /* BACKGROUND TERANG + LAYOUT FLEX UNTUK FOOTER */
    html, body { height: 100%; }
    .main { 
        background-color: #ffffff; 
        display: flex;
        flex-direction: column;
        min-height: 100vh;
        padding-bottom: 100px;
    }
    .stApp { background-color: #f8f9fa; }
    
    /* CSS DASHBOARD */
    .kpi-card { background-color: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .card-title { font-size: 12px; font-weight: bold; color: #64748b; text-transform: uppercase; margin-bottom: 5px; }
    .card-value { font-size: 24px; font-weight: 800; color: #1e293b; }
    .card-sub { font-size: 11px; color: #94a3b8; }
    .highlight-yellow { border-left: 5px solid #fbbf24; }
    .highlight-purple { border-left: 5px solid #a855f7; }
    
    /* CSS SALDO & SALES BOX */
    .saldo-box { background-color: #f0fdf4; border: 1px solid #bbf7d0; padding: 15px; border-radius: 8px; text-align: center; }
    .saldo-title { color: #166534; font-weight: 700; font-size: 14px; margin-bottom: 5px; }
    .saldo-value { color: #15803d; font-weight: 800; font-size: 22px; }
    
    .sales-box-nat { background-color: #eff6ff; border: 1px solid #bfdbfe; padding: 10px; border-radius: 8px; text-align: center; }
    .sales-val-nat { color: #1d4ed8; font-weight: 800; font-size: 18px; }
    .sales-box-boost { background-color: #fef2f2; border: 1px solid #fecaca; padding: 10px; border-radius: 8px; text-align: center; }
    .sales-val-boost { color: #b91c1c; font-weight: 800; font-size: 18px; }

    /* CSS KALKULATOR (TERANG) */
    .stNumberInput small, .stTextInput small { display: none; }
    .sidebar-metric-value-red { color: #dc2626; font-weight: 700; }
    .sidebar-metric-value-green { color: #16a34a; font-weight: 700; }
    .kpi-header-cost { background: linear-gradient(135deg, #1f77b4 0%, #2b8cc4 100%); color: #ffffff; font-size: 20px; font-weight: 700; padding: 12px 16px; border-radius: 6px; margin-bottom: 10px; }
    .gap-amount-display { background: linear-gradient(135deg, #f5f7fa 0%, #eef2f7 100%); border: 2px solid #cbd5e1; border-radius: 8px; padding: 10px; text-align: center; min-height: 60px; display: flex; align-items: center; justify-content: center; }
    .gap-value-red { color: #dc2626; font-size: 18px; font-weight: 700; }
    .gap-value-green { color: #16a34a; font-size: 18px; font-weight: 700; }
    .total-cost-container { background-color: #fef2f2; border-left: 5px solid #dc2626; border-radius: 6px; padding: 16px; margin-top: 16px; display: flex; justify-content: space-between; align-items: center; }
    .total-cost-text { color: #991b1b; font-size: 16px; font-weight: 700; }
    
    /* METRIC CARDS (CALCULATOR) */
    .metric-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; margin-bottom: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
    .metric-label { font-size: 12px; color: #64748b; font-weight: 600; text-transform: uppercase; margin-bottom: 8px; }
    .metric-value { font-size: 28px; font-weight: 800; color: #1e293b; margin: 10px 0; }
    .metric-subtext { font-size: 12px; color: #94a3b8; margin-top: 8px; }
    .card-success { border-left: 5px solid #10b981; }
    .card-danger { border-left: 5px solid #ef4444; }
    .card-info { border-left: 5px solid #3b82f6; }
    </style>
""", unsafe_allow_html=True)

st.title("🏢 IOH Partner Super System")

# ==========================================
# 2. ENGINE PEMBACA DATA
# ==========================================
def safe_parse(val):
    if isinstance(val, (int, float)): return float(val)
    if isinstance(val, str):
        clean_val = val.replace(",", "").replace("%", "").strip()
        try:
            num = float(clean_val)
            return num / 100 if "%" in val else num
        except: return 0.0
    return 0.0

if "kpi_interventions" not in st.session_state:
    st.session_state.kpi_interventions = {}

# Default config template untuk setiap region
DEFAULT_REGION_CONFIG = {
    "kpi_metrics": [
        {"name": "Trade Supply", "weight": 0.40, "target": 1000},
        {"name": "M2S Absolute", "weight": 0.40, "target": 500},
        {"name": "RGU GA FWA", "weight": 0.20, "target": 200}
    ],
    "score_multiplier_mapping": [
        {"min": 105, "max": 999, "value": 1.05, "label": "≥ 105"},
        {"min": 80, "max": 104.99, "value": 1.0, "label": "80 – <105"},
        {"min": 70, "max": 79.99, "value": 0.8, "label": "70 – <80"},
        {"min": 0, "max": 69.99, "value": 0, "label": "< 70"}
    ],
    "sla_tariff": [
        {"min": 0.50, "max": 1.0, "rate": 0.0125, "label": "> 50%"},
        {"min": 0.40, "max": 0.50, "rate": 0.0100, "label": "40% – 50%"},
        {"min": 0, "max": 0.40, "rate": 0.0080, "label": "< 40%"}
    ],
    "prepaid_revenue": 1_000_000_000,
    "boost_options": [
        {"name": "Campaign A", "cost": 200_000_000, "impacts": {"Trade Supply": 150, "M2S Absolute": 0, "RGU GA FWA": 0}},
        {"name": "Campaign B", "cost": 350_000_000, "impacts": {"Trade Supply": 0, "M2S Absolute": 100, "RGU GA FWA": 0}},
        {"name": "Campaign C", "cost": 500_000_000, "impacts": {"Trade Supply": 0, "M2S Absolute": 0, "RGU GA FWA": 50}},
        {"name": "Combined A+B", "cost": 550_000_000, "impacts": {"Trade Supply": 150, "M2S Absolute": 100, "RGU GA FWA": 0}}
    ]
}

# All available regions
ALL_REGIONS = {
    "SDP (Indosat)": ["KEDAMEAN", "DAWARBLANDONG", "SANGKAPURA"],
    "3KIOSK (Tri)": ["SIDAYU", "BENJENG", "JATIREJO", "KEMLAGI", "BABAT", "KEDUNGPRING"]
}

if "kpi_calculator_config" not in st.session_state:
    # Build per-region config
    regions_config = {}
    for mitra_type, area_list in ALL_REGIONS.items():
        for area in area_list:
            regions_config[area] = DEFAULT_REGION_CONFIG.copy()
    
    st.session_state.kpi_calculator_config = {
        "month": "FEBRUARI 2026",
        "current_region": "KEDAMEAN",  # default region
        "regions": regions_config
    }

if "calculator_achievement" not in st.session_state:
    st.session_state.calculator_achievement = {
        "Trade Supply": {"target": 1000, "actual": 850},
        "M2S Absolute": {"target": 500, "actual": 425},
        "RGU GA FWA": {"target": 200, "actual": 160},
        "tertiary_inner_percentage": 0.45,
        "ach_rgu_ga": 0.82,
        "growth_prepaid_revenue": 0.05
    }

if "selected_boosts" not in st.session_state:
    st.session_state.selected_boosts = []

if "monthly_total_benefits" not in st.session_state:
    st.session_state.monthly_total_benefits = {
        "JANUARI": 0,
        "FEBRUARI": 0,
        "MARET": 0,
        "APRIL": 0,
        "MEI": 0,
        "JUNI": 0,
        "JULI": 0,
        "AGUSTUS": 0,
        "SEPTEMBER": 0,
        "OKTOBER": 0,
        "NOVEMBER": 0,
        "DESEMBER": 0
    }

if "tds_growth_brackets" not in st.session_state:
    st.session_state.tds_growth_brackets = [
        {"min_growth": 3.0, "max_growth": 5.0, "fee_percent": 2.5},
        {"min_growth": 5.0, "max_growth": None, "fee_percent": 3.0}
    ]

if "third_income_enabled" not in st.session_state:
    st.session_state.third_income_enabled = False

if "third_income_items" not in st.session_state:
    st.session_state.third_income_items = []

def get_region_config(region_name):
    """Get configuration untuk region tertentu"""
    config = st.session_state.kpi_calculator_config
    if region_name in config["regions"]:
        return config["regions"][region_name]
    return DEFAULT_REGION_CONFIG.copy()

@st.cache_data(ttl=60) 
def load_all_sheets(url):
    """Muat semua sheet dari Excel dengan retry logic"""
    import time
    from urllib.error import URLError
    
    max_retries = 3
    timeout_seconds = 30
    
    for attempt in range(max_retries):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Connection': 'keep-alive',
                'Accept-Encoding': 'gzip, deflate'
            }
            
            # Download dengan timeout
            r = requests.get(url, headers=headers, timeout=timeout_seconds, stream=True)
            r.raise_for_status()
            
            # Baca content sepenuhnya
            content = r.content
            
            # Parse dengan openpyxl
            all_dfs = pd.read_excel(
                io.BytesIO(content), 
                sheet_name=None, 
                header=None, 
                engine='openpyxl'
            )
            
            # Debug: Tampilkan sheet yang berhasil dimuat
            sheet_names = list(all_dfs.keys())
            print(f"✅ Berhasil memuat Excel. Total sheet: {len(sheet_names)}")
            print(f"   Sheet yang dimuat: {sheet_names}")
            
            # Validasi sheet SAL
            sal_found = any('SAL' in name.upper() for name in sheet_names)
            if sal_found:
                sal_key = [name for name in sheet_names if 'SAL' in name.upper()][0]
                print(f"✅ Sheet SAL ditemukan: '{sal_key}'")
            else:
                print(f"⚠️  PERINGATAN: Sheet SAL tidak ditemukan!")
                print(f"   Sheet yang tersedia: {sheet_names}")
            
            return all_dfs
            
        except (requests.ConnectionError, requests.Timeout, URLError) as e:
            print(f"❌ Percobaan {attempt + 1}/{max_retries} gagal: {type(e).__name__}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                print(f"   Menunggu {wait_time} detik sebelum retry...")
                time.sleep(wait_time)
            else:
                st.error(f"""
                ❌ **Gagal memuat file Excel setelah {max_retries} percobaan!**
                
                **Error yang terjadi:** {type(e).__name__}
                
                **Kemungkinan penyebab:**
                - Koneksi internet terputus atau lambat
                - Server Google Sheets sedang tidak responsif
                - URL spreadsheet tidak valid
                - Izin akses ke file ditolak
                
                **Saran:**
                1. Periksa koneksi internet Anda
                2. Tunggu beberapa saat dan coba refresh (F5)
                3. Pastikan URL spreadsheet dapat diakses publik
                """)
                return None
                
        except Exception as e:
            st.error(f"""
            ❌ **Gagal membaca file Excel!**
            
            **Error:** {str(e)}
            
            **Kemungkinan penyebab:**
            - Format file bukan Excel (.xlsx)
            - File Excel terkorupsi
            - Sheet kosong atau format tidak standar
            """)
            print(f"❌ Error detail: {e}")
            return None
    
    return None


def get_sheet_fuzzy(dfs, key):
    for k in dfs.keys():
        if key.upper() in k.upper():
            return dfs[k]
    return None

def get_kpi_values(df, region, keyword):
    tgt, act = 0, 0
    col_idx = -1
    for r in range(min(30, len(df))):
        for c in range(len(df.columns)):
            val = str(df.iloc[r,c]).upper()
            if region in val:
                col_idx = c
                break
        if col_idx != -1: break
    if col_idx == -1: return 0, 0

    target_section = False
    for idx, row in df.iterrows():
        lbl = str(row.iloc[0]).upper()
        if "TARGET" in lbl and "DES" in lbl: target_section = True
        
        if keyword in lbl:
            try:
                raw_val = row.iloc[col_idx]
                val = float(str(raw_val).replace(",","").replace("%",""))
            except: val = 0
            if target_section: tgt = val
            else: act = val
    return tgt, act

def get_stock_values(df, region):
    ga, fwa = 0, 0
    key = region.replace("3KIOSK ", "").replace("SDP ", "").strip()
    for idx, row in df.iterrows():
        if key in str(row.iloc[1]).upper():
            try:
                ga = float(row.iloc[2])
                fwa = float(row.iloc[3])
            except: pass
            break
    return ga, fwa

# --- FUNGSI UPFRONT TRI DARI PRIM SHEET ---
def get_upfront_data_tri(df, region, debug=False):
    """
    Baca data dari sheet PRIM untuk TRI Kiosk
    
    Parameters:
    - df: DataFrame dari sheet PRIM
    - region: Wilayah yang dicari (misal: KEDAMEAN)
    - debug: Tampilkan debug info (default: False)
    
    Returns:
    - total_amount: Total Amount yang difilter
    - breakdown_df: DataFrame breakdown per SDP
    """
    
    if df is None or len(df) == 0:
        if debug:
            print("⚠️ Sheet PRIM kosong atau tidak ditemukan")
        return pd.DataFrame(), 0, pd.DataFrame()
    
    header_idx = -1
    col_sdp, col_amount = -1, -1
    
    # Cari header row - identifikasi kolom SDP dan AMOUNT
    for r in range(min(5, len(df))):
        row_vals = [str(x).upper() for x in df.iloc[r].tolist()]
        if "SDP" in row_vals and "AMOUNT" in row_vals:
            header_idx = r
            for i, v in enumerate(row_vals):
                v_upper = str(v).upper()
                if "SDP" in v_upper: col_sdp = i
                if "AMOUNT" in v_upper: col_amount = i
            break
    
    if debug:
        print(f"🔍 DEBUG get_upfront_data_tri:")
        print(f"   Header found at row: {header_idx}")
        print(f"   Kolom: SDP={col_sdp}, Amount={col_amount}")
    
    if header_idx == -1 or col_sdp == -1 or col_amount == -1:
        if debug:
            print("❌ Header row atau kolom penting tidak ditemukan!")
            print("   Cek apakah ada kolom 'SDP' dan 'AMOUNT' di sheet PRIM")
        return 0, pd.DataFrame()
    
    region_key = region.upper().strip()
    total_amount = 0
    sdp_breakdown = {}
    match_count = 0
    
    for idx in range(header_idx + 1, len(df)):
        try:
            row = df.iloc[idx]
            
            # Baca kolom SDP
            val_sdp_raw = str(row[col_sdp]).strip().upper() if col_sdp != -1 else ""
            val_sdp = val_sdp_raw.strip()
            
            # Skip jika SDP tidak cocok dengan wilayah
            if not val_sdp or region_key not in val_sdp:
                continue
            
            # Baca kolom AMOUNT
            val_amount = row[col_amount]
            
            # Skip jika AMOUNT kosong
            if pd.isna(val_amount) or val_amount == "":
                continue
            
            try:
                amount_val = float(val_amount)
                total_amount += amount_val
                
                # Breakdown per SDP
                if val_sdp not in sdp_breakdown:
                    sdp_breakdown[val_sdp] = 0
                sdp_breakdown[val_sdp] += amount_val
                
                match_count += 1
                
                if debug:
                    print(f"   ✓ Row {idx}: SDP={val_sdp}, Amount={amount_val:,.0f}")
                
            except ValueError:
                if debug:
                    print(f"   ✗ Row {idx}: Tidak bisa convert AMOUNT '{val_amount}' ke float")
                continue
        
        except Exception as e:
            if debug:
                print(f"   ✗ Error pada row {idx}: {str(e)}")
            continue
    
    # Create breakdown dataframe
    breakdown_data = []
    for sdp, amount in sdp_breakdown.items():
        breakdown_data.append({
            "SDP": sdp,
            "Amount": amount,
            "Amount (Formatted)": f"Rp {amount:,.0f}"
        })
    breakdown_df = pd.DataFrame(breakdown_data)
    
    if debug:
        print(f"   Total Rows Match: {match_count}")
        print(f"   Total Amount: {total_amount:,.0f}")
        print(f"   Breakdown: {sdp_breakdown}")
    
    return total_amount, breakdown_df

# --- FUNGSI SALDO INDOSAT DENGAN BREAKDOWN PER SDP ---
def get_daily_saldo_data_indosat(df, region, target_month_idx, debug=False):
    """
    Baca data dari sheet SAL dengan filter ESCM Allocation from SAP| |API
    
    Parameters:
    - df: DataFrame dari sheet SAL
    - region: Wilayah yang dicari (misal: KEDAMEAN)
    - target_month_idx: Indeks bulan (misal: 1 untuk Januari)
    - debug: Tampilkan debug info (default: False)
    
    Returns:
    - chart_df: DataFrame tren harian
    - total_filtered: Total Paid In yang difilter
    - breakdown_df: DataFrame breakdown per SDP
    """
    
    if df is None or len(df) == 0:
        if debug:
            print("⚠️  Sheet SAL kosong atau tidak ditemukan")
        return pd.DataFrame(), 0, pd.DataFrame()
    
    daily_data = {} 
    header_idx = -1
    col_sdp, col_detail, col_paid, col_time, col_tgl = -1, -1, -1, -1, -1
    
    # Cari header row - identifikasi kolom penting
    for r in range(min(5, len(df))):
        row_vals = [str(x).upper() for x in df.iloc[r].tolist()]
        if "DETAILS" in row_vals and ("PAID IN" in row_vals or "PAID" in row_vals):
            header_idx = r
            for i, v in enumerate(row_vals):
                v_upper = str(v).upper()
                if "SDP" in v_upper: col_sdp = i
                if "DETAILS" in v_upper: col_detail = i
                if "PAID" in v_upper and "IN" in v_upper: col_paid = i
                if "COMPLETION" in v_upper and "TIME" in v_upper: col_time = i
                if "TGL" in v_upper: col_tgl = i 
            break
    
    if debug:
        print(f"🔍 DEBUG get_daily_saldo_data_indosat:")
        print(f"   Header found at row: {header_idx}")
        print(f"   Kolom: SDP={col_sdp}, Details={col_detail}, Paid In={col_paid}, Completion Time={col_time}, TGL={col_tgl}")
        print(f"   Target Bulan Index: {target_month_idx}")
    
    if header_idx == -1:
        if debug:
            print("❌ Header row tidak ditemukan!")
            print("   Cek apakah ada kolom 'DETAILS' dan 'PAID IN' di sheet SAL")
        return pd.DataFrame(), 0, pd.DataFrame()

    keyword_trx = "ESCM Allocation from SAP| |API".upper()
    region_key = region.upper().strip()
    total_filtered = 0
    sdp_breakdown = {}  # Untuk tracking per SDP
    match_count = 0  # Counter untuk debug
    
    for idx in range(header_idx + 1, len(df)):
        try:
            row = df.iloc[idx]
            
            # Baca kolom SDP
            val_sdp_raw = str(row[col_sdp]).strip().upper() if col_sdp != -1 else ""
            val_sdp = val_sdp_raw.strip()
            
            # Skip jika SDP tidak cocok
            if not val_sdp or region_key not in val_sdp:
                continue
            
            # Baca kolom Details dan filter ESCM
            val_detail = str(row[col_detail]).upper() if col_detail != -1 else ""
            if keyword_trx not in val_detail:
                continue
            
            # IDENTIFIKASI BULAN DAN HARI DARI COMPLETION TIME
            day_key = 0
            month_match = False
            
            if col_time != -1:
                val_time = row[col_time]
                try:
                    if pd.notna(val_time):
                        # Parse datetime dari Completion Time
                        dt_obj = None
                        if isinstance(val_time, str):
                            # Format: 01-01-2026 15:10:18 atau variasi lainnya
                            dt_obj = pd.to_datetime(val_time, dayfirst=True, errors='coerce')
                        else:
                            dt_obj = pd.to_datetime(val_time, errors='coerce')
                        
                        # Cek apakah parsing berhasil dan bulan sesuai
                        if pd.notna(dt_obj) and hasattr(dt_obj, 'month'):
                            if dt_obj.month == target_month_idx:
                                month_match = True
                                day_key = dt_obj.day
                                if debug and match_count < 3:  # Print debug hanya 3 baris pertama
                                    print(f"   Row {idx}: {val_time} -> Day {day_key} (Month {dt_obj.month} ✓)")
                except Exception as e:
                    if debug:
                        print(f"   ⚠️  Error parse Completion Time di row {idx}: {val_time} ({str(e)})")
                    pass
            
            # Jika bulan tidak match, skip baris ini
            if not month_match:
                continue
            
            # Jika hari tidak valid, skip
            if day_key <= 0:
                continue
            
            # Baca Paid In
            val_duit = row[col_paid] if col_paid != -1 else None
            if pd.notna(val_duit):
                try:
                    # Parse nilai nominal
                    nominal_str = str(val_duit).replace(",", "").replace(".", "").strip()
                    nominal = float(nominal_str)
                    
                    # Tambahkan ke daily data
                    daily_data[day_key] = daily_data.get(day_key, 0) + nominal
                    total_filtered += nominal
                    match_count += 1
                    
                    # Breakdown per SDP
                    if val_sdp not in sdp_breakdown:
                        sdp_breakdown[val_sdp] = 0
                    sdp_breakdown[val_sdp] += nominal
                    
                except ValueError as e:
                    if debug:
                        print(f"⚠️  Gagal parse nilai Paid In di row {idx}: {val_duit}")
                    pass
        except Exception as e:
            if debug:
                print(f"⚠️  Error di row {idx}: {str(e)}")
            continue
    
    if debug:
        print(f"\n✅ Proses selesai:")
        print(f"   Total match dengan filter ESCM (Bulan {target_month_idx}): {match_count} baris")
        print(f"   Sum Paid In (filtered): Rp {total_filtered:,.0f}")
        if sdp_breakdown:
            print(f"   Breakdown per SDP:")
            for sdp, amount in sdp_breakdown.items():
                print(f"      - {sdp}: Rp {amount:,.0f}")
        else:
            print(f"   ⚠️  Tidak ada breakdown per SDP")
    
    # Buat chart DF
    chart_df = pd.DataFrame(
        list(daily_data.items()), 
        columns=['Tanggal', 'Pembelian']
    ).sort_values('Tanggal').set_index('Tanggal') if daily_data else pd.DataFrame()
    
    # Buat breakdown DF
    breakdown_df = pd.DataFrame([
        {"SDP": sdp, "Total Paid In": amount, "Upfront 1.5%": amount * 0.015}
        for sdp, amount in sdp_breakdown.items()
    ]) if sdp_breakdown else pd.DataFrame()
    
    return chart_df, total_filtered, breakdown_df

# --- FUNGSI SALDO TRI (PRIM) ---
def get_daily_saldo_data_tri(df, region, target_month_idx):
    daily_data = {}
    total_filtered = 0
    region_map = {"KEDUNGPRING": "KDUNGPRING"}
    search_key = region_map.get(region, region).upper()
    
    header_idx = -1
    col_order, col_amt, col_date = -1, -1, -1
    
    for r in range(5):
        row_vals = [str(x).upper() for x in df.iloc[r].tolist()]
        if "AMOUNT" in row_vals and ("ORDER DATE" in row_vals or "TRANSFER DATE" in row_vals):
            header_idx = r
            for i, v in enumerate(row_vals):
                if "AMOUNT" in v: col_amt = i
                if "ORDER DATE" in v: col_date = i
                if "ORDER FOR" in v: col_order = i
            if col_order == -1:
                for i, v in enumerate(row_vals):
                    if "TRANSFER NUMBER" in v: col_order = i
            break
            
    if header_idx == -1: return pd.DataFrame(), 0
    
    for idx in range(header_idx + 1, len(df)):
        try:
            row = df.iloc[idx]
            val_order = str(row[col_order]).upper() if col_order != -1 else ""
            
            if search_key in val_order:
                val_date = row[col_date]
                dt_obj = None
                
                if isinstance(val_date, str):
                    try: dt_obj = pd.to_datetime(val_date, dayfirst=True)
                    except: pass
                elif isinstance(val_date, (datetime.datetime, pd.Timestamp)):
                    dt_obj = val_date
                    
                if dt_obj and dt_obj.month == target_month_idx:
                    val_amt = row[col_amt]
                    if pd.notna(val_amt):
                        nominal = float(str(val_amt).replace(",",""))
                        day_key = dt_obj.day
                        daily_data[day_key] = daily_data.get(day_key, 0) + nominal
                        total_filtered += nominal
        except: continue
        
    chart_df = pd.DataFrame(list(daily_data.items()), columns=['Tanggal', 'Pembelian']).sort_values('Tanggal').set_index('Tanggal') if daily_data else pd.DataFrame()
    return chart_df, total_filtered

# --- FUNGSI SALES TRI (DENGAN BREAKDOWN SUB-WILAYAH) ---
def get_tri_sales_analysis(df, region):
    total_natural = 0
    total_boosting = 0
    breakdown_data = {}
    
    region_map = {"KEDUNGPRING": "KDUNGPRING"}
    search_key = region_map.get(region, region).upper()
    
    header_idx = -1
    col_type, col_bantu, col_cek, col_amt = -1, -1, -1, -1
    
    for r in range(5):
        row_vals = [str(x).upper() for x in df.iloc[r].tolist()]
        if "TRANSFER SUB TYPE" in row_vals and "AMOUNT(IDR)" in row_vals:
            header_idx = r
            for i, v in enumerate(row_vals):
                if "TRANSFER SUB TYPE" in v: col_type = i
                if "BANTU DSE" in v: col_bantu = i
                if "CEK" in v: col_cek = i
                if "AMOUNT(IDR)" in v: col_amt = i
            break
    
    if header_idx == -1 or col_bantu == -1 or col_cek == -1:
        return 0, 0, pd.DataFrame()
        
    for idx in range(header_idx + 1, len(df)):
        try:
            row = df.iloc[idx]
            
            sub_type = str(row[col_type]).upper() if col_type != -1 else ""
            if "TRANSFER" not in sub_type: continue
            
            bantu_dse = str(row[col_bantu]).upper().strip()
            if search_key not in bantu_dse: continue
            
            val_amt = row[col_amt]
            nominal = 0
            if pd.notna(val_amt):
                nominal = float(str(val_amt).replace(",",""))
                
            cek_val = str(row[col_cek]).upper()
            is_boost = "BMS" in cek_val
            
            if is_boost: total_boosting += nominal
            else: total_natural += nominal
            
            if bantu_dse not in breakdown_data:
                breakdown_data[bantu_dse] = {'Natural': 0, 'Boosting': 0, 'Total': 0}
            
            breakdown_data[bantu_dse]['Total'] += nominal
            if is_boost:
                breakdown_data[bantu_dse]['Boosting'] += nominal
            else:
                breakdown_data[bantu_dse]['Natural'] += nominal
                
        except: continue
        
    if breakdown_data:
        df_breakdown = pd.DataFrame.from_dict(breakdown_data, orient='index')
        df_breakdown.index.name = 'Sub Wilayah'
        df_breakdown = df_breakdown.sort_index()
    else:
        df_breakdown = pd.DataFrame()
        
    return total_natural, total_boosting, df_breakdown

# ==========================================
# CALCULATOR FUNCTIONS (CORRECT KPI CALCULATION)
# ==========================================
def format_currency(value):
    """Format currency dengan pemisah ribuan (titik), tanpa suffix, tampilkan semua angka"""
    if value is None or value == 0:
        return "Rp 0"
    
    # Convert to integer to avoid floating point issues
    value = int(value)
    
    # Add thousands separator
    value_str = str(abs(value))
    
    # Add dots as thousands separator
    parts = []
    for i, digit in enumerate(reversed(value_str)):
        if i > 0 and i % 3 == 0:
            parts.append('.')
        parts.append(digit)
    
    result = ''.join(reversed(parts))
    
    if value < 0:
        result = "-" + result
    
    return f"Rp {result}"

def format_decimal(value):
    """Format decimal dengan 2 angka di belakang koma, jangan hapus trailing zeros"""
    if value is None:
        return "0.00"
    
    # Always show 2 decimal places
    return f"{float(value):.2f}"

def format_idr_jt(value):
    """Format currency dengan pemisah ribuan (titik), tampilkan angka sebenarnya"""
    if value is None or value == 0:
        return "Rp 0"
    
    # Convert to integer to avoid floating point issues
    value = int(value)
    
    # Add thousands separator
    value_str = str(abs(value))
    
    # Add dots as thousands separator
    parts = []
    for i, digit in enumerate(reversed(value_str)):
        if i > 0 and i % 3 == 0:
            parts.append('.')
        parts.append(digit)
    
    result = ''.join(reversed(parts))
    
    if value < 0:
        result = "-" + result
    
    return f"Rp {result}"

# ==========================================
# FUNGSI GENERATE PDF REPORT LENGKAP
# ==========================================
def generate_pdf_report_comprehensive(wilayah, mitra, session_data):
    """
    Generate PDF report lengkap dari semua Tab (Tab 1 hingga Tab 6)
    dengan detail yang komprehensif
    """
    pdf = FPDF_WithFooter()
    pdf.add_page()
    pdf.set_font("Arial", "B", 18)
    
    # Header
    pdf.set_fill_color(31, 119, 180)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 15, "IOH Partner Super System", ln=True, align="C", fill=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, f"Region: {wilayah} | Mitra: {mitra}", ln=True, align="C")
    pdf.cell(0, 8, f"Generated: {dt.now().strftime('%d-%m-%Y %H:%M:%S')}", ln=True, align="C")
    pdf.ln(8)
    
    # ==========================================
    # TAB 1: SLA/KPI INSENTIF
    # ==========================================
    pdf.set_font("Arial", "B", 13)
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(0, 10, "1. SLA/KPI INSENTIF", ln=True, fill=True)
    pdf.set_font("Arial", "", 10)
    
    sla_data = session_data.get("sla_scores", {})
    if sla_data:
        for key, value in sla_data.items():
            if isinstance(value, (int, float)):
                if "sla" in key.lower():
                    pdf.cell(0, 7, f"  - {key}: {value:.2%}", ln=True)
                elif "rate" in key.lower() or "tarif" in key.lower():
                    pdf.cell(0, 7, f"  - {key}: {value:.4f} (Rp {value:,.0f})", ln=True)
                else:
                    pdf.cell(0, 7, f"  - {key}: Rp {value:,.0f}", ln=True)
    else:
        pdf.cell(0, 7, "  (Data Tab 1 belum diisi)", ln=True)
    pdf.ln(5)
    
    # ==========================================
    # TAB 2: FIX INCOME
    # ==========================================
    pdf.set_font("Arial", "B", 13)
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(0, 10, "2. FIX INCOME (Upfront + Inner + Tertiary)", ln=True, fill=True)
    pdf.set_font("Arial", "", 10)
    fix_data = session_data.get("fix_income_data", {})
    if fix_data:
        for key, value in fix_data.items():
            if isinstance(value, (int, float)):
                pdf.cell(0, 7, f"  - {key}: Rp {value:,.0f}", ln=True)
            else:
                pdf.cell(0, 7, f"  - {key}: {value}", ln=True)
    else:
        pdf.cell(0, 7, "  (Data Tab 2 belum diisi)", ln=True)
    pdf.ln(5)
    
    # ==========================================
    # TAB 3: TACTICAL INCOME
    # ==========================================
    pdf.set_font("Arial", "B", 13)
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(0, 10, "3. TACTICAL INCOME (Growth + Bonus + Lainnya)", ln=True, fill=True)
    pdf.set_font("Arial", "", 10)
    tactical_data = session_data.get("tactical_income_data", {})
    if tactical_data:
        for key, value in tactical_data.items():
            if isinstance(value, (int, float)):
                pdf.cell(0, 7, f"  - {key}: Rp {value:,.0f}", ln=True)
            else:
                pdf.cell(0, 7, f"  - {key}: {value}", ln=True)
    else:
        pdf.cell(0, 7, "  (Data Tab 3 belum diisi)", ln=True)
    pdf.ln(5)
    
    # ==========================================
    # TAB 4: TOTAL INCOME SUMMARY
    # ==========================================
    pdf.set_font("Arial", "B", 13)
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(0, 10, "4. TOTAL INCOME SUMMARY", ln=True, fill=True)
    pdf.set_font("Arial", "", 10)
    
    total_income_maks = session_data.get("total_income_maksimal", 0)
    total_income_custom = session_data.get("total_income_custom", 0)
    final_fee_maks = session_data.get("final_fee_maksimal", 0)
    final_fee_custom = session_data.get("final_fee_custom", 0)
    
    pdf.cell(0, 7, f"  Skenario Maksimal (110% Target):", ln=True)
    pdf.cell(0, 7, f"    - Total Income: Rp {total_income_maks:,.0f}", ln=True)
    pdf.cell(0, 7, f"    - Final Fee: Rp {final_fee_maks:,.0f}", ln=True)
    pdf.cell(0, 7, f"  Skenario Custom (Input Manual):", ln=True)
    pdf.cell(0, 7, f"    - Total Income: Rp {total_income_custom:,.0f}", ln=True)
    pdf.cell(0, 7, f"    - Final Fee: Rp {final_fee_custom:,.0f}", ln=True)
    pdf.ln(5)
    
    # ==========================================
    # TAB 5: ANALISIS CUSTOM (ACHIEVEMENT)
    # ==========================================
    pdf.set_font("Arial", "B", 13)
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(0, 10, "5. ANALISIS CUSTOM (Achievement Data)", ln=True, fill=True)
    pdf.set_font("Arial", "", 10)
    
    achievement = session_data.get("calculator_achievement", {})
    if achievement:
        for kpi_name in ["Trade Supply", "M2S Absolute", "RGU GA FWA"]:
            if kpi_name in achievement:
                kpi_data = achievement[kpi_name]
                if isinstance(kpi_data, dict):
                    target = kpi_data.get("target", 0)
                    actual = kpi_data.get("actual", 0)
                    pct = (actual/target*100) if target > 0 else 0
                    pdf.cell(0, 7, f"  - {kpi_name}: {actual:,.0f} / {target:,.0f} ({pct:.1f}%)", ln=True)
        
        rgu_ga = achievement.get("ach_rgu_ga", 0)
        tertiary_pct = achievement.get("tertiary_inner_percentage", 0)
        growth = achievement.get("growth_prepaid_revenue", 0)
        
        if rgu_ga > 0:
            pdf.cell(0, 7, f"  - RGU GA Compliance: {rgu_ga:.2%}", ln=True)
        if tertiary_pct > 0:
            pdf.cell(0, 7, f"  - Tertiary Inner %: {tertiary_pct:.2%}", ln=True)
        if growth != 0:
            pdf.cell(0, 7, f"  - Growth Prepaid Revenue: {growth:.2%}", ln=True)
    else:
        pdf.cell(0, 7, "  (Data Achievement belum diisi)", ln=True)
    pdf.ln(5)
    
    # ==========================================
    # TAB 6: BIAYA & STRATEGI
    # ==========================================
    pdf.set_font("Arial", "B", 13)
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(0, 10, "6. BIAYA & STRATEGI (Setup Cost per Unit)", ln=True, fill=True)
    pdf.set_font("Arial", "", 10)
    
    pdf.cell(0, 7, "  Cost Per Unit Setup:", ln=True)
    config = session_data.get("kpi_calculator_config", {})
    regions = config.get("regions", {})
    if wilayah in regions:
        regional_config = regions[wilayah]
        for metric in regional_config.get("kpi_metrics", []):
            metric_name = metric.get("name", "Unknown")
            cost_per_unit = metric.get("cost_per_unit", 0)
            if cost_per_unit > 0:
                pdf.cell(0, 7, f"    - {metric_name}: Rp {cost_per_unit:,.0f}/unit", ln=True)
            else:
                pdf.cell(0, 7, f"    - {metric_name}: (belum set cost)", ln=True)
    
    cost_breakdown = session_data.get("cost_breakdown", {})
    if cost_breakdown and "breakdown" in cost_breakdown:
        pdf.cell(0, 7, "  Detail Perhitungan Biaya:", ln=True)
        for kpi_name, breakdown in cost_breakdown["breakdown"].items():
            shortfall = breakdown.get("shortfall", 0)
            total_cost = breakdown.get("total_cost", 0)
            if shortfall > 0:
                pdf.cell(0, 7, f"    - {kpi_name}: Shortfall {shortfall} unit >>> Rp {total_cost:,.0f}", ln=True)
            else:
                pdf.cell(0, 7, f"    - {kpi_name}: Sudah tercapai (Cost: Rp 0)", ln=True)
        
        total_cost_all = cost_breakdown.get("total_cost", 0)
        pdf.cell(0, 7, f"  TOTAL COST KESELURUHAN: Rp {total_cost_all:,.0f}", ln=True)
    pdf.ln(5)
    
    # ==========================================
    # SUMMARY KEPUTUSAN
    # ==========================================
    pdf.set_font("Arial", "B", 13)
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(0, 10, "7. SUMMARY & REKOMENDASI", ln=True, fill=True)
    pdf.set_font("Arial", "", 10)
    
    net_maksimal = total_income_maks - session_data.get("cost_maksimal", 0)
    cost_custom = session_data.get("cost_custom", 0)
    net_custom = total_income_custom - cost_custom
    
    pdf.cell(0, 7, f"  Net Profit Maksimal (110%): Rp {net_maksimal:,.0f}", ln=True)
    pdf.cell(0, 7, f"  Net Profit Custom (Input): Rp {net_custom:,.0f}", ln=True)
    pdf.cell(0, 7, f"  Selisih Profit Potential: Rp {net_maksimal - net_custom:,.0f}", ln=True)
    
    pdf.ln(10)
    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 6, "Report ini adalah hasil analisis lengkap dari IOH Partner Super System", ln=True, align="C")
    pdf.cell(0, 6, "Silakan gunakan data ini untuk pengambilan keputusan strategis bisnis Anda", ln=True, align="C")
    
    # Generate PDF ke bytes
    pdf_bytes = pdf.output(dest='S')
    if isinstance(pdf_bytes, str):
        pdf_bytes = pdf_bytes.encode('latin-1')
    elif isinstance(pdf_bytes, bytearray):
        pdf_bytes = bytes(pdf_bytes)
    
    return pdf_bytes

# ==========================================
# FUNGSI NORMALISASI ID (SINGLE RULE - STRIP LEADING ZEROS)
# ==========================================
def normalize_transaction_id(trx_id):
    """
    Normalisasi Transaction ID dengan SINGLE RULE yang konsisten:
    Strip leading zeros dari kedua TRX dan COM
    
    Contoh:
    - "4019200034190289920" → "4019200034190289920"
    - "04031400034344689034" → "4031400034344689034"
    - "0000123" → "123"
    - "0" → "0"
    
    Returns: normalized_id (string) atau None jika invalid
    """
    if pd.isna(trx_id) or trx_id == "" or str(trx_id).upper() == "NAN":
        return None
    
    trx_id = str(trx_id).strip()
    if not trx_id:
        return None
    
    # Strip leading zeros, tapi minimum "0" jika semuanya zeros
    normalized = trx_id.lstrip('0') or '0'
    
    return normalized
def calculate_transaction_match(dfs, region, transaction_types=None, debug=False):
    """
    Hitung jumlah transaksi yang MATCH antara TRX dan COM
    
    LOGIC:
    1. Ambil data TRX dengan filter:
       - Transaction Type (Indosat Reload, Purchase Data Package, dll)
       - Wilayah (SDP)
    2. Ambil data COM dengan filter:
       - Wilayah (SDP)
    3. Normalisasi Transaction ID dan Receipt No
    4. Lakukan INNER JOIN
    5. Hitung jumlah baris hasil join
    
    Args:
        dfs: Dictionary dari semua sheets
        region: Nama wilayah (e.g., 'DAWARBLANDONG')
        transaction_types: List tipe transaksi yg dicari (default: ['Indosat Reload', 'Purchase Data Package'])
        debug: Boolean untuk menampilkan debug info
    
    Returns:
        jumlah_match (int): Jumlah baris hasil inner join
    """
    if transaction_types is None:
        transaction_types = ['Indosat Reload', 'Purchase Data Package']
    
    try:
        if debug:
            st.write("📋 **DEBUG: Coba baca sheets...**")
            st.write(f"Available sheets: {list(dfs.keys())}")
        
        # 1. AMBIL DATA TRX - coba beberapa nama alternatif
        df_trx = None
        trx_sheet_name = None
        for name in dfs.keys():
            if "TRX" in name.upper() or "TRANSACTION" in name.upper():
                df_trx = dfs[name]
                trx_sheet_name = name
                break
        
        if df_trx is None:
            df_trx = get_sheet_fuzzy(dfs, "TRX")
            trx_sheet_name = "TRX (fuzzy)"
        
        if df_trx is None or len(df_trx) < 2:
            if debug: st.error(f"❌ Sheet TRX tidak ditemukan!")
            return 0, 0
        
        if debug:
            st.write(f"✅ TRX Sheet ditemukan: {trx_sheet_name}, rows: {len(df_trx)}")
        
        # Cari header row dan kolom di TRX
        header_row = 0
        col_sdp_trx = -1
        col_trx_type = -1
        col_trx_id = -1
        col_area = -1
        
        # Scan row 0-5 untuk menemukan kolom
        for r in range(min(5, len(df_trx))):
            row_vals = [str(x).upper() for x in df_trx.iloc[r].tolist()]
            
            for i, v in enumerate(row_vals):
                v_clean = str(v).strip()
                if "SDP" in v_clean:
                    col_sdp_trx = i
                    header_row = r
                if "AREA" in v_clean:
                    col_area = i
                    header_row = r
                if "TRANSACTION" in v_clean and "TYPE" in v_clean:
                    col_trx_type = i
                # PENTING: Prioritaskan "TRANSACTION ID" dengan cara: ada "TRANSACTION" dan "ID", tapi TIDAK ada "REVERSAL"
                if "TRANSACTION" in v_clean and "ID" in v_clean and "REVERSAL" not in v_clean:
                    col_trx_id = i
            
            if col_trx_type != -1 and (col_sdp_trx != -1 or col_area != -1) and col_trx_id != -1:
                break
        
        if debug:
            st.write(f"**Header row: {header_row}**")
            st.write(f"Kolom TRX | col_trx_id={col_trx_id}, col_trx_type={col_trx_type}, col_sdp_trx={col_sdp_trx}, col_area={col_area}")
            st.write(f"Header row content: {list(df_trx.iloc[header_row])}")
        
        if col_trx_id == -1 or col_trx_type == -1:
            if debug: st.error(f"❌ Kolom Transaction ID atau Type tidak ditemukan!")
            return 0, 0, 0
        
        # Filter TRX berdasarkan wilayah dan transaction type
        region_upper = region.upper()
        valid_trx_ids = set()  # Set dari ID yang sudah dinormalisasi
        valid_trx_ids_raw = []  # Simpan raw IDs juga untuk debug
        trx_amount_debit_map = {}  # Dictionary: normalized_id -> list of amount_debit values
        count_region_match = 0
        count_type_match = 0
        
        for idx in range(header_row + 1, len(df_trx)):
            try:
                row = df_trx.iloc[idx]
                
                # Cek SDP/Wilayah/Area
                val_sdp = str(row[col_sdp_trx]).upper() if col_sdp_trx != -1 else ""
                val_area = str(row[col_area]).upper() if col_area != -1 else ""
                
                # Match jika region ada di SDP atau AREA
                if region_upper not in val_sdp and region_upper not in val_area:
                    continue
                count_region_match += 1
                
                # Cek Transaction Type
                val_type = str(row[col_trx_type]).upper()
                is_valid_type = any(t.upper() in val_type for t in transaction_types)
                if not is_valid_type:
                    continue
                count_type_match += 1
                
                # Ambil Transaction ID dan normalisasi (SINGLE normalization)
                trx_id = row[col_trx_id]
                normalized = normalize_transaction_id(trx_id)
                
                if normalized:
                    valid_trx_ids.add(normalized)
                    if normalized not in trx_amount_debit_map:
                        trx_amount_debit_map[normalized] = []
                    if len(valid_trx_ids_raw) < 5:  # Hanya simpan 5 sample raw
                        valid_trx_ids_raw.append((str(trx_id), normalized))
                    
            except Exception as e:
                continue
        
        if debug:
            st.write(f"TRX Filtered: region_match={count_region_match}, type_match={count_type_match}, unique_ids={len(valid_trx_ids)}")
            if len(valid_trx_ids_raw) > 0:
                st.write("**Raw IDs → Normalized IDs (TRX):**")
                for raw, norm in valid_trx_ids_raw:
                    st.write(f"  `{raw}` → `{norm}`")
            if len(valid_trx_ids) > 0:
                sample = list(valid_trx_ids)[:5]
                st.write(f"Sample TRX IDs (normalized): {sample}")
        
        if len(valid_trx_ids) == 0:
            if debug: st.warning(f"⚠️ Tidak ada TRX yang cocok dengan wilayah {region} dan tipe transaksi {transaction_types}")
            return 0, 0, 0
        
        # 2. AMBIL DATA COM - coba beberapa nama alternatif
        df_com = None
        com_sheet_name = None
        for name in dfs.keys():
            if "COM" in name.upper() or "COMMISSION" in name.upper() or "COMPLETION" in name.upper():
                df_com = dfs[name]
                com_sheet_name = name
                break
        
        if df_com is None:
            df_com = get_sheet_fuzzy(dfs, "COM")
            com_sheet_name = "COM (fuzzy)"
        
        if df_com is None or len(df_com) < 2:
            if debug: st.error(f"❌ Sheet COM tidak ditemukan!")
            return 0, 0, 0
        
        if debug:
            st.write(f"✅ COM Sheet ditemukan: {com_sheet_name}, rows: {len(df_com)}")
        
        # Cari header row dan kolom di COM
        header_row_com = 0
        col_sdp_com = -1
        col_receipt_no = -1
        col_area_com = -1
        
        for r in range(min(5, len(df_com))):
            row_vals = [str(x).upper() for x in df_com.iloc[r].tolist()]
            
            for i, v in enumerate(row_vals):
                v_clean = str(v).strip()
                if "SDP" in v_clean:
                    col_sdp_com = i
                    header_row_com = r
                if "AREA" in v_clean:
                    col_area_com = i
                    header_row_com = r
                if "RECEIPT" in v_clean and ("NO" in v_clean or "NUMBER" in v_clean):
                    col_receipt_no = i
            
            if col_receipt_no != -1 and (col_sdp_com != -1 or col_area_com != -1):
                break
        
        if debug:
            st.write(f"**Header row COM: {header_row_com}**")
            st.write(f"Kolom COM | col_receipt_no={col_receipt_no}, col_sdp_com={col_sdp_com}, col_area_com={col_area_com}")
            st.write(f"Header row content: {list(df_com.iloc[header_row_com])}")
        
        if col_receipt_no == -1:
            if debug: st.error(f"❌ Kolom Receipt No tidak ditemukan!")
            return 0, 0, 0
        
        # Filter COM berdasarkan wilayah
        valid_com_ids = set()
        valid_com_ids_raw = []  # Simpan raw IDs juga untuk debug
        count_com_region = 0
        
        for idx in range(header_row_com + 1, len(df_com)):
            try:
                row = df_com.iloc[idx]
                
                # Cek SDP/Wilayah/Area
                val_sdp = str(row[col_sdp_com]).upper() if col_sdp_com != -1 else ""
                val_area = str(row[col_area_com]).upper() if col_area_com != -1 else ""
                
                if region_upper not in val_sdp and region_upper not in val_area:
                    continue
                count_com_region += 1
                
                # Ambil Receipt No dan normalisasi
                receipt_no = row[col_receipt_no]
                normalized = normalize_transaction_id(receipt_no)
                
                if normalized:
                    valid_com_ids.add(normalized)
                    if len(valid_com_ids_raw) < 5:  # Hanya simpan 5 sample raw
                        valid_com_ids_raw.append((str(receipt_no), normalized))
                    
            except Exception as e:
                continue
        
        if debug:
            st.write(f"COM Filtered: region_match={count_com_region}, unique_ids={len(valid_com_ids)}")
            st.write(f"*Kolom yang digunakan dari COM: Receipt No (index {col_receipt_no})*")
            if len(valid_com_ids_raw) > 0:
                st.write("**Raw IDs → Normalized IDs (COM):**")
                for raw, norm in valid_com_ids_raw:
                    st.write(f"  `{raw}` → `{norm}`")
            if len(valid_com_ids) > 0:
                sample = list(valid_com_ids)[:5]
                st.write(f"Sample COM IDs (normalized): {sample}")
        
        if len(valid_com_ids) == 0:
            if debug: st.warning(f"⚠️ Tidak ada COM yang cocok dengan wilayah {region}")
            return 0, 0, 0
        
        # 3. INNER JOIN: HITUNG MATCH
        matched_ids = valid_trx_ids & valid_com_ids  # Set intersection
        jumlah_match = len(matched_ids)
        
        if debug:
            st.write(f"**HASIL MATCH:**")
            st.write(f"Set TRX (normalized): {len(valid_trx_ids)} unique IDs")
            st.write(f"Set COM (normalized): {len(valid_com_ids)} unique IDs")
            st.write(f"**Jumlah Match: {jumlah_match}**")
            if len(matched_ids) > 0 and len(matched_ids) <= 20:
                st.write(f"Matched IDs: {sorted(list(matched_ids))}")
            elif len(matched_ids) > 20:
                st.write(f"Sample matched IDs (first 10): {sorted(list(matched_ids))[:10]}")
        
        # 4. AMBIL PAID IN DARI TRANSAKSI YANG MATCH
        # Cari kolom "Paid In" di COM
        col_paid_in = -1
        for i, col_name in enumerate(df_com.iloc[header_row_com]):
            col_name_upper = str(col_name).upper()
            if "PAID" in col_name_upper and "IN" in col_name_upper:
                col_paid_in = i
                break
        
        total_paid_in = 0
        count_paid_in_collected = 0  # Track berapa banyak Paid In yang diambil
        
        if col_paid_in != -1:
            # Loop melalui COM sheet dan ambil Paid In untuk matched IDs
            for idx in range(header_row_com + 1, len(df_com)):
                try:
                    row = df_com.iloc[idx]
                    
                    # Cek SDP/Wilayah/Area
                    val_sdp = str(row[col_sdp_com]).upper() if col_sdp_com != -1 else ""
                    val_area = str(row[col_area_com]).upper() if col_area_com != -1 else ""
                    
                    if region_upper not in val_sdp and region_upper not in val_area:
                        continue
                    
                    # Ambil Receipt No, normalisasi, dan cek apakah ada di matched_ids
                    receipt_no = row[col_receipt_no]
                    normalized = normalize_transaction_id(receipt_no)
                    
                    # CRITICAL GATE: HANYA jika normalized ada di matched_ids
                    if normalized and normalized in matched_ids:
                        # Ambil Paid In dan tambahkan ke total
                        paid_in_val = row[col_paid_in]
                        if pd.notna(paid_in_val):
                            try:
                                paid_in_amount = float(str(paid_in_val).replace(",", ""))
                                total_paid_in += paid_in_amount
                                count_paid_in_collected += 1
                            except:
                                pass
                        
                except Exception as e:
                    continue
        
        if debug:
            st.write(f"**STEP 4: AMBIL PAID IN DARI MATCHED TRANSACTIONS**")
            st.write(f"Kolom 'Paid In' ditemukan: {col_paid_in != -1} (index: {col_paid_in})")
            st.write(f"Total row COM yang diproses untuk match: {len(df_com) - header_row_com - 1}")
            st.write(f"**CRITICAL: Hanya mengambil Paid In dari {count_paid_in_collected} baris yang MATCH dengan matched_ids**")
            st.write(f"**Jumlah Transaksi Match: {jumlah_match}**")
            st.write(f"**Jumlah Paid In berhasil dikumpulkan: {count_paid_in_collected}**")
            if count_paid_in_collected > 0:
                st.write(f"✅ **TOTAL INCOME FIX (Paid In): Rp {total_paid_in:,.0f}**")
                st.write(f"*Rata-rata per transaksi: Rp {total_paid_in/count_paid_in_collected:,.0f}*")
            else:
                st.warning("⚠️ Tidak ada Paid In yang berhasil dikumpulkan dari matched transactions")
        
        # 5. AMBIL AMOUNT DEBIT DARI TRANSAKSI YANG MATCH (TRX)
        col_amount_debit = -1
        for i, col_name in enumerate(df_trx.iloc[header_row]):
            col_name_upper = str(col_name).upper()
            if "AMOUNT" in col_name_upper and "DEBIT" in col_name_upper:
                col_amount_debit = i
                break
        
        total_amount_debit = 0
        count_amount_debit_collected = 0
        
        if col_amount_debit != -1:
            # Loop melalui TRX sheet dan ambil Amount Debit untuk matched IDs
            for idx in range(header_row + 1, len(df_trx)):
                try:
                    row = df_trx.iloc[idx]
                    
                    # Cek SDP/Wilayah/Area
                    val_sdp = str(row[col_sdp_trx]).upper() if col_sdp_trx != -1 else ""
                    val_area = str(row[col_area]).upper() if col_area != -1 else ""
                    
                    if region_upper not in val_sdp and region_upper not in val_area:
                        continue
                    
                    # Cek Transaction Type
                    val_type = str(row[col_trx_type]).upper()
                    is_valid_type = any(t.upper() in val_type for t in transaction_types)
                    if not is_valid_type:
                        continue
                    
                    # Ambil Transaction ID, normalisasi, dan cek apakah ada di matched_ids
                    trx_id = row[col_trx_id]
                    normalized = normalize_transaction_id(trx_id)
                    
                    # CRITICAL GATE: HANYA jika normalized ada di matched_ids
                    if normalized and normalized in matched_ids:
                        # Ambil Amount Debit dan tambahkan ke total
                        amount_debit_val = row[col_amount_debit]
                        if pd.notna(amount_debit_val):
                            try:
                                amount_debit_amount = float(str(amount_debit_val).replace(",", ""))
                                total_amount_debit += amount_debit_amount
                                count_amount_debit_collected += 1
                            except:
                                pass
                        
                except Exception as e:
                    continue
        
        if debug:
            st.write(f"**STEP 5: AMBIL AMOUNT DEBIT DARI MATCHED TRANSACTIONS**")
            st.write(f"Kolom 'Amount Debit' ditemukan: {col_amount_debit != -1} (index: {col_amount_debit})")
            st.write(f"**CRITICAL: Hanya mengambil Amount Debit dari {count_amount_debit_collected} baris yang MATCH dengan matched_ids**")
            if count_amount_debit_collected > 0:
                st.write(f"✅ **TOTAL AMOUNT DEBIT (dari matched): Rp {total_amount_debit:,.0f}**")
                st.write(f"*Rata-rata per transaksi: Rp {total_amount_debit/count_amount_debit_collected:,.0f}*")
            else:
                st.warning("⚠️ Tidak ada Amount Debit yang berhasil dikumpulkan dari matched transactions")
        
        return jumlah_match, total_paid_in, total_amount_debit
        
    except Exception as e:
        if debug:
            st.error(f"❌ Error: {str(e)}")
        return 0, 0, 0

# ==========================================
# STEP 1: KPI CAP (SDP RULE - 70% to 110%)
# ==========================================
def apply_kpi_cap(kpi_value):
    """Apply SDP KPI cap: min 70%, max 110%"""
    return max(70, min(110, kpi_value))

def calculate_kpi_percentage(target, actual):
    """Calculate KPI achievement percentage from target and actual values"""
    if target <= 0:
        return 0
    return (actual / target) * 100

# ==========================================
# STEP 2: WEIGHTED SCORE CALCULATION
# ==========================================
def calculate_weighted_score(trade_supply, m2s_absolute, rgu_ga):
    """
    Hitung Weighted Score dengan cap sudah diterapkan
    Bobot: Trade Supply 0.4, M2S 0.4, RGU-GA 0.2
    """
    return (trade_supply * 0.4) + (m2s_absolute * 0.4) + (rgu_ga * 0.2)

# ==========================================
# STEP 3: SCORE MULTIPLIER MAPPING
# ==========================================
def get_score_multiplier(weighted_score, mapping):
    """
    Map weighted score to multiplier:
    ≥ 105: 1.05
    80 – <105: 1.0
    70 – <80: 0.8
    < 70: 0
    """
    for slab in mapping:
        if slab["min"] <= weighted_score <= slab["max"]:
            return slab["value"]
    return 0

# ==========================================
# STEP 4: SLA TARIFF CALCULATION
# ==========================================
def get_sla_tariff(tertiary_inner_pct, sla_tariff_config):
    """
    Hitung SLA Tariff dari Tertiary #B Inner:
    > 50%: 1.25%
    40-50%: 1.0%
    < 40%: 0.8%
    """
    for slab in sla_tariff_config:
        if slab["min"] <= tertiary_inner_pct <= slab["max"]:
            return slab["rate"]
    return sla_tariff_config[-1]["rate"]

# ==========================================
# STEP 5: COMPLIANCE INDEX (2-LAYER)
# ==========================================
def calculate_compliance_index(ach_rgu_ga, growth_prepaid_revenue):
    """
    5A: ACH RGU-GA Score
        ≥ 80%: 1.0
        < 80%: 0
    
    5B: Growth Prepaid Score
        < 0%: 0.8
        ≥ 0%: 1.0
    
    Compliance Index = (0.5 × ACH Score) + (0.5 × Growth Score)
    """
    ach_score = 1.0 if ach_rgu_ga >= 0.80 else 0
    growth_score = 0.8 if growth_prepaid_revenue < 0 else 1.0
    
    compliance_index = (0.5 * ach_score) + (0.5 * growth_score)
    return compliance_index, ach_score, growth_score

def get_score_compliance(compliance_index):
    """
    5C: Map Compliance Index to Score Compliance
    < 0.9: 0
    ≥ 0.9: 0.9
    = 1.0: 1.0
    """
    if compliance_index < 0.9:
        return 0
    elif compliance_index == 1.0:
        return 1.0
    else:  # 0.9 <= compliance_index < 1.0
        return 0.9

def calculate_metrics(config, achievement):
    """
    MAIN CALCULATION FUNCTION - SDP PARTNERS FEB 2026
    
    Steps:
    0. Input data mentah
    1. Apply KPI Cap (70-110%)
    2. Calculate Weighted Score
    3. Get Score Multiplier (mapping)
    4. Get SLA Tariff (from Tertiary #B Inner)
    5. Calculate Compliance Index (2-layer)
    6. Calculate Final Fee
    """
    
    # Step 0: Input data - Extract KPI percentages from dict structure
    trade_supply_data = achievement.get("Trade Supply", {"target": 1000, "actual": 0})
    m2s_absolute_data = achievement.get("M2S Absolute", {"target": 500, "actual": 0})
    rgu_ga_data = achievement.get("RGU GA FWA", {"target": 200, "actual": 0})
    
    # Calculate percentages
    if isinstance(trade_supply_data, dict):
        trade_supply_pct = calculate_kpi_percentage(trade_supply_data.get("target", 1), trade_supply_data.get("actual", 0))
    else:
        trade_supply_pct = trade_supply_data
    
    if isinstance(m2s_absolute_data, dict):
        m2s_absolute_pct = calculate_kpi_percentage(m2s_absolute_data.get("target", 1), m2s_absolute_data.get("actual", 0))
    else:
        m2s_absolute_pct = m2s_absolute_data
    
    if isinstance(rgu_ga_data, dict):
        rgu_ga_pct = calculate_kpi_percentage(rgu_ga_data.get("target", 1), rgu_ga_data.get("actual", 0))
    else:
        rgu_ga_pct = rgu_ga_data
    
    tertiary_inner_pct = achievement.get("tertiary_inner_percentage", 0)
    ach_rgu_ga = achievement.get("ach_rgu_ga", 0)
    growth_prepaid_revenue = achievement.get("growth_prepaid_revenue", 0)
    
    # Step 1: Apply KPI Cap (70-110%)
    trade_supply_capped = apply_kpi_cap(trade_supply_pct)
    m2s_absolute_capped = apply_kpi_cap(m2s_absolute_pct)
    rgu_ga_capped = apply_kpi_cap(rgu_ga_pct)
    
    # Step 2: Calculate Weighted Score
    weighted_score = calculate_weighted_score(
        trade_supply_capped,
        m2s_absolute_capped,
        rgu_ga_capped
    )
    
    # Step 3: Get Score Multiplier
    score_multiplier = get_score_multiplier(
        weighted_score,
        config["score_multiplier_mapping"]
    )
    
    # Step 4: Get SLA Tariff
    sla_tariff = get_sla_tariff(
        tertiary_inner_pct,
        config["sla_tariff"]
    )
    
    # Step 5: Calculate Compliance Index
    compliance_index, ach_score, growth_score = calculate_compliance_index(
        ach_rgu_ga,
        growth_prepaid_revenue
    )
    score_compliance = get_score_compliance(compliance_index)
    
    # Step 6: Calculate Final Fee
    prepaid_revenue = config["prepaid_revenue"]
    final_fee = score_multiplier * sla_tariff * prepaid_revenue * score_compliance
    
    return {
        "kpi_percentage": {
            "Trade Supply": trade_supply_pct,
            "M2S Absolute": m2s_absolute_pct,
            "RGU GA FWA": rgu_ga_pct
        },
        "kpi_capped": {
            "Trade Supply": trade_supply_capped,
            "M2S Absolute": m2s_absolute_capped,
            "RGU GA FWA": rgu_ga_capped
        },
        "weighted_score": weighted_score,
        "score_multiplier": score_multiplier,
        "sla_tariff": sla_tariff,
        "sla_tariff_pct": sla_tariff * 100,
        "compliance_index": compliance_index,
        "ach_score": ach_score,
        "growth_score": growth_score,
        "score_compliance": score_compliance,
        "score_compliance_pct": score_compliance * 100,
        "prepaid_revenue": prepaid_revenue,
        "final_fee": final_fee
    }

def calculate_cost_shortfall(config, achievement):
    """
    Calculate cost untuk memenuhi shortfall setiap KPI
    
    RUMUS BERBEDA PER KPI:
    - Trade Supply: Cost = Cost Per Unit saja (input langsung, tanpa × Shortfall)
    - M2S Absolute: Cost = Shortfall × Cost Per Unit
    - RGU GA FWA: Cost = Shortfall × Cost Per Unit
    
    Parameters:
    - config: Dictionary config dengan kpi_metrics dan cost_per_unit
    - achievement: Dictionary achievement berisi target dan actual
    
    Return:
    - Dictionary dengan total_cost dan breakdown per KPI
    """
    total_cost = 0
    cost_breakdown = {}
    
    for metric in config["kpi_metrics"]:
        metric_name = metric["name"]
        target = metric["target"]
        cost_per_unit = metric.get("cost_per_unit", 0)
        
        # Ambil actual dari achievement
        achievement_data = achievement.get(metric_name, {"target": target, "actual": 0})
        actual = achievement_data.get("actual", 0) if isinstance(achievement_data, dict) else achievement_data
        
        # Hitung shortfall jika actual < target
        shortfall = max(0, target - actual)
        
        # PERHITUNGAN COST BERBEDA BERDASARKAN JENIS KPI
        if metric_name == "Trade Supply":
            # Trade Supply: COST = Cost Per Unit saja (langsung, tanpa × Shortfall)
            cost = cost_per_unit if shortfall > 0 else 0
            calculation_note = f"Cost Per Unit (tanpa × Shortfall)"
        else:
            # M2S Absolute & RGU GA FWA: COST = Shortfall × Cost Per Unit
            cost = shortfall * cost_per_unit
            calculation_note = f"Shortfall ({shortfall}) × Cost Per Unit ({cost_per_unit:,.0f})"
        
        cost_breakdown[metric_name] = {
            "target": target,
            "actual": actual,
            "shortfall": shortfall,
            "cost_per_unit": cost_per_unit,
            "total_cost": cost,
            "calculation_note": calculation_note
        }
        total_cost += cost
    
    return {
        "total_cost": total_cost,
        "breakdown": cost_breakdown
    }

def calculate_income_gain_from_kpi_improvement(config, current_achievement, metric_name):
    """
    Calculate potential income gain jika satu KPI ditingkatkan ke target
    
    Approach: Hitung berdasarkan KPI weight dan assumed income impact
    - Trade Supply (40% weight): estimate gain ~40% dari base income per 1% improvement
    - M2S Absolute (40% weight): estimate gain ~40% dari base income per 1% improvement  
    - RGU GA FWA (20% weight): estimate gain ~20% dari base income per 1% improvement
    
    Parameters:
    - config: Region config
    - current_achievement: Current achievement dict
    - metric_name: Nama KPI yang akan ditingkatkan
    
    Return:
    - Estimated income gain
    """
    # Define KPI weights dan base assumptions
    kpi_weights = {
        "Trade Supply": 0.40,
        "M2S Absolute": 0.40,
        "RGU GA FWA": 0.20
    }
    
    try:
        # Get base income dari current achievement
        current_result = calculate_metrics(config, current_achievement)
        base_income = current_result.get("final_fee", 0)
        
        if base_income == 0:
            return 0
        
        # Get metric info
        metric_info = next((m for m in config.get("kpi_metrics", []) if m["name"] == metric_name), None)
        if not metric_info:
            return 0
        
        # Get current actual dan target
        metric_data = current_achievement.get(metric_name, {})
        if isinstance(metric_data, dict):
            current_actual = metric_data.get("actual", 0)
            target = metric_data.get("target", metric_info["target"])
        else:
            current_actual = 0
            target = metric_info["target"]
        
        if current_actual >= target:
            # Sudah mencapai target
            return 0
        
        # Calculate improvement needed
        actual_pct = (current_actual / target * 100) if target > 0 else 0
        target_pct = 100
        improvement_pct = target_pct - actual_pct  # berapa persen improvement diperlukan
        
        # Get KPI weight
        kpi_weight = kpi_weights.get(metric_name, 0.33)
        
        # Estimate income gain: (improvement % / 100) * weight * base income
        # Asumsi: setiap KPI improvement proportional dengan weight-nya
        income_gain = (improvement_pct / 100) * kpi_weight * base_income
        
        return max(0, income_gain)
    
    except Exception as e:
        return 0

# ==========================================
# 3. SIDEBAR & DATA LOADING
# ==========================================
with st.sidebar:
    st.header("🔄 Sinkronisasi")
    if st.button("Refresh Data Excel"):
        st.cache_data.clear()
        st.rerun()
    st.divider()
    st.header("📍 Filter Data")
    
    # Load Excel data
    dfs = load_all_sheets(URL_MASTER_EXCEL)
    
    if dfs is None:
        st.error("""
        ❌ **Gagal Memuat Data!**
        
        Aplikasi tidak dapat membaca file Excel. Kemungkinan penyebab:
        
        1️⃣  **Masalah Koneksi Internet**
           - Periksa koneksi WiFi/LAN
           - Coba refresh halaman (tekan F5)
        
        2️⃣  **URL Spreadsheet Tidak Valid**
           - Periksa kembali link Google Sheets
           - Pastikan file dapat diakses publik
        
        3️⃣  **File Excel Rusak**
           - Download file Excel dan periksa strukturnya
           - Pastikan ada sheet bernama: SAL, EST LR IM3, EST LR 3
        
        📞 **Hubungi Admin** jika masalah berlanjut
        """)
        st.stop()
    
    st.success("✅ Data berhasil dimuat!")
    
    mitra = st.selectbox("Tipe Mitra", ["SDP (Indosat)", "3KIOSK (Tri)"])
    if "Indosat" in mitra:
        sheet_kpi = "EST LR IM3"
        areas = ["KEDAMEAN", "DAWARBLANDONG", "SANGKAPURA"]
        theme = "highlight-yellow"
    else:
        sheet_kpi = "EST LR 3"
        areas = ["SIDAYU", "BENJENG", "JATIREJO", "KEMLAGI", "BABAT", "KEDUNGPRING"]
        theme = "highlight-purple"
        
    wilayah = st.selectbox("Wilayah", areas)
    
    # Sync selected region dengan config
    st.session_state.kpi_calculator_config["current_region"] = wilayah
    
    bulan_map = {"Januari": 1, "Februari": 2, "Maret": 3, "April": 4, "Mei": 5, "Juni": 6, 
                 "Juli": 7, "Agustus": 8, "September": 9, "Oktober": 10, "November": 11, "Desember": 12}
    pilih_bulan = st.selectbox("Pilih Bulan (Grafik)", list(bulan_map.keys()))
    bulan_idx = bulan_map[pilih_bulan]
    
    st.divider()
    menu = st.radio("Menu", ["📊 Dashboard Utama", "🧮 Kalkulator Strategi"])
    
    st.divider()
    days = st.number_input("Jml Hari", value=31)
    curr = st.number_input("Hari Ke-", value=18)
    run_rate = days/curr if curr>0 else 0
    
    st.header("⚙️ Konfigurasi KPI")
    kpi_config = []
    def_kpis = [("Trade Supply", 40), ("M2S Absolute", 40), ("RGU FWA", 20)]
    for i, (d_name, d_w) in enumerate(def_kpis):
        c1, c2 = st.columns([3, 1], gap="small")
        with c1: kn = st.text_input(f"KPI {i+1}", value=d_name, key=f"kn{i}", label_visibility="collapsed")
        with c2: kw = st.number_input("W", value=d_w, key=f"kw{i}", label_visibility="collapsed")
        kpi_config.append({"name": kn, "weight": kw/100})
        
        if kn in st.session_state.kpi_interventions:
            inv = st.session_state.kpi_interventions[kn]
            gc = "sidebar-metric-value-red" if inv['gap'] > 0 else "sidebar-metric-value-green"
            with st.container(border=True):
                r1a, r1b = st.columns(2)
                r1a.markdown(f"<span style='font-size:10px'>Tgt</span><br><b>{inv['target']:,.0f}</b>", unsafe_allow_html=True)
                r1b.markdown(f"<span style='font-size:10px'>Act</span><br><b>{inv['actual']:,.0f}</b>", unsafe_allow_html=True)
                st.markdown(f"Gap: <span class='{gc}'>{inv['gap']:,.0f}</span>", unsafe_allow_html=True)
    
    # ========================
    # KONFIGURASI CALCULATOR (BARU)
    # ========================
    st.divider()
    with st.expander("⚙️ Config Calculator (SDP Partners) - Wilayah: " + wilayah, expanded=False):
        st.write(f"**Konfigurasi untuk Wilayah: {wilayah}**")
        
        # Get region config reference
        region_cfg = st.session_state.kpi_calculator_config["regions"][wilayah]
        
        st.write("**Basic Settings**")
        st.session_state.kpi_calculator_config["month"] = st.text_input(
            "Month",
            value=st.session_state.kpi_calculator_config["month"],
            key="calc_month"
        )
        
        region_cfg["prepaid_revenue"] = st.number_input(
            "Prepaid Revenue (Rp)",
            value=region_cfg["prepaid_revenue"],
            step=100_000_000,
            key="calc_prepaid"
        )
        
        st.divider()
        st.write("**KPI Metrics Weight (SDP Rule)**")
        for i, metric in enumerate(region_cfg["kpi_metrics"]):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write(f"**{metric['name']}**")
            with col2:
                metric["weight"] = st.number_input(
                    "Weight",
                    value=float(metric["weight"]),
                    min_value=0.0,
                    max_value=1.0,
                    step=0.01,
                    key=f"calc_weight_{i}_{wilayah}"
                )
        
        st.divider()
        st.write("**Score Multiplier Mapping**")
        st.info("⚠️ SDP Rule: Score Multiplier dihitung otomatis dari Weighted Score (70-110% cap)")
        for i, slab in enumerate(region_cfg["score_multiplier_mapping"]):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**{slab['label']}**")
            with col2:
                st.write(f"Range: {slab['min']}-{slab['max']}")
            with col3:
                slab["value"] = st.number_input(
                    "Multiplier",
                    value=float(slab["value"]),
                    min_value=0.0,
                    max_value=2.0,
                    step=0.01,
                    key=f"calc_mult_{i}_{wilayah}"
                )
        
        st.divider()
        st.write("**SLA Tariff (Tertiary #B Inner)**")
        for i, slab in enumerate(region_cfg["sla_tariff"]):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**{slab['label']}**")
            with col2:
                rate_percent = float(slab["rate"] * 100)
                new_rate_percent = st.number_input(
                    "Tariff (%)",
                    value=rate_percent,
                    min_value=0.0,
                    max_value=5.0,
                    step=0.01,
                    key=f"calc_tariff_{i}_{wilayah}"
                )
                slab["rate"] = new_rate_percent / 100

# PREPARE DATA
df_kpi_sheet = get_sheet_fuzzy(dfs, sheet_kpi.replace(" ", "")) 
if df_kpi_sheet is None: df_kpi_sheet = get_sheet_fuzzy(dfs, sheet_kpi)

t_tr, a_tr, t_m2, a_m2, t_fw, a_fw = 0,0,0,0,0,0
rgu_compliance = 0

# Variable untuk TOTAL INCOME FIX
total_income_fix_paid_in = 0
total_amount_debit = 0

# Untuk Indosat: hitung Jumlah Transaksi Match dengan inner join TRX & COM
if "Indosat" in mitra:
    t_tr, total_income_fix_paid_in, total_amount_debit = calculate_transaction_match(dfs, wilayah, transaction_types=['Indosat Reload', 'Purchase Data Package'])
    # a_tr = Total Paid In dari matched transactions (BUKAN dari KPI sheet lagi)
    a_tr = total_income_fix_paid_in
else:
    # Untuk Tri: gunakan logika lama
    if df_kpi_sheet is not None:
        t_tr, a_tr = get_kpi_values(df_kpi_sheet, wilayah, "TRADE SUPPLY")

if df_kpi_sheet is not None:
    t_m2, a_m2 = get_kpi_values(df_kpi_sheet, wilayah, "M2S")
    t_fw, a_fw = get_kpi_values(df_kpi_sheet, wilayah, "RGU GA")
    rgu_compliance = (a_fw/t_fw*100) if t_fw > 0 else 0

# --- PROSES DATA SALDO ---
saldo_chart_df = pd.DataFrame()
saldo_total_bulan_ini = 0
saldo_breakdown_df = pd.DataFrame()
source_info = ""

if "Indosat" in mitra:
    df_sal = get_sheet_fuzzy(dfs, "SAL")
    if df_sal is not None:
        saldo_chart_df, saldo_total_bulan_ini, saldo_breakdown_df = get_daily_saldo_data_indosat(df_sal, wilayah, bulan_idx)
        source_info = "Sumber: Sheet SAL (Filter: 'ESCM Allocation')"
else: # TRI (3KIOSK)
    df_prim = get_sheet_fuzzy(dfs, "PRIM")
    if df_prim is not None:
        saldo_chart_df, saldo_total_bulan_ini = get_daily_saldo_data_tri(df_prim, wilayah, bulan_idx)
        source_info = "Sumber: Sheet PRIM (Kolom: Amount)"

# --- PROSES SALES TRI (NATURAL VS BOOSTING & BREAKDOWN) ---
tri_sales_nat = 0
tri_sales_boost = 0
df_sales_breakdown = pd.DataFrame()

if "Tri" in mitra:
    df_sec = get_sheet_fuzzy(dfs, "SEC DSE")
    if df_sec is not None:
        tri_sales_nat, tri_sales_boost, df_sales_breakdown = get_tri_sales_analysis(df_sec, wilayah)

# ==========================================
# 4. MENU 1: DASHBOARD UTAMA (ORIGINAL - NO CHANGES)
# ==========================================
if menu == "📊 Dashboard Utama":
    st.subheader(f"Dashboard Monitoring: {wilayah}")
    st.caption("Monitoring Pembelian Saldo / Primary")
    st.markdown("---")
    
    # --- BAGIAN 1: SALDO ---
    c1, c2 = st.columns([1, 2]) 
    
    with c1:
        st.markdown(f"""
        <div class="saldo-box">
            <div class="saldo-title">💰 TOTAL PEMBELIAN SALDO</div>
            <div style="font-size:12px; margin-bottom:5px;">(Bulan {pilih_bulan})</div>
            <div class="saldo-value">Rp {saldo_total_bulan_ini:,.0f}</div>
            <div style="margin-top:10px; font-size:11px; color:#6b7280;">{source_info}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c2:
        st.markdown(f"##### 📈 Tren Pembelian Harian ({pilih_bulan})")
        if not saldo_chart_df.empty:
            st.bar_chart(saldo_chart_df, color="#16a34a", height=250)
        else:
            st.warning(f"Tidak ada data pembelian saldo untuk bulan {pilih_bulan}.")

    # --- BAGIAN 2: SALES TRI (KHUSUS TRI) ---
    if "Tri" in mitra:
        st.markdown("---")
        st.subheader("🛍️ Analisis Penjualan (Secondary)")
        st.caption("Sumber: Sheet SEC DSE (Filter: Transfer)")
        
        c_s1, c_s2, c_s3 = st.columns([1, 1, 2])
        
        with c_s1:
            st.markdown(f"""
            <div class="sales-box-nat">
                <div style="font-size:12px; color:#1e40af; font-weight:700;">NATURAL (NON-BMS)</div>
                <div class="sales-val-nat">Rp {tri_sales_nat:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with c_s2:
            st.markdown(f"""
            <div class="sales-box-boost">
                <div style="font-size:12px; color:#991b1b; font-weight:700;">BOOSTING (BMS)</div>
                <div class="sales-val-boost">Rp {tri_sales_boost:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with c_s3:
            data_sales = pd.DataFrame({
                "Tipe": ["Natural", "Boosting"],
                "Amount": [tri_sales_nat, tri_sales_boost]
            })
            st.bar_chart(data_sales.set_index("Tipe"), color=["#3b82f6"], height=200)
            
        # --- TABEL BREAKDOWN PER BANTU DSE ---
        st.markdown("##### 📋 Rincian per Sub-Wilayah (BANTU DSE)")
        if not df_sales_breakdown.empty:
            st.dataframe(
                df_sales_breakdown.style.format("{:,.0f}"),
                use_container_width=True
            )
        else:
            st.info("Belum ada data penjualan Secondary untuk wilayah ini.")

# ==========================================
# 5. MENU 2: KALKULATOR STRATEGI (SDP PARTNERS FEB 2026)
# ==========================================
elif menu == "🧮 Kalkulator Strategi":
    st.subheader(f"🧮 Kalkulator Strategi (SDP Partners): {wilayah}")
    
    # Get config untuk region yang dipilih saat ini
    full_config = st.session_state.kpi_calculator_config
    current_region = full_config["current_region"]
    region_config = full_config["regions"][current_region]
    
    # Merge config (tambahkan month dan prepaid_revenue ke region config)
    config = {
        **region_config,
        "month": full_config["month"],
        "region": current_region
    }
    
    # ==========================================
    # MENU STRATEGI: 5 PILIHAN MENU
    # ==========================================
    
    tab_sla, tab_fix, tab_tactical, tab_total, tab_biaya = st.tabs([
        "💰 SLA/KPI Insentif",
        "📈 Fix Income",
        "🎯 Tactical Income",
        "💵 Total Income",
        "⚡ Biaya Tambahan + Strategi"
    ])
    
    # ==========================================
    # TAB 1: SLA/KPI INSENTIF
    # ==========================================
    with tab_sla:
        st.markdown("### 💰 SLA/KPI Insentif Calculator")
        st.info("Hitung insentif berdasarkan pencapaian KPI dan SLA metrics dengan formula SDP Partners Feb 2026")
        
        # PILIHAN MODE: MAKSIMAL vs CUSTOM
        calculator_mode = st.radio(
            "Pilih Mode Kalkulator",
            ["🎯 Skenario Maksimal (110% Target)", "⚙️ Skenario Custom (Input Manual)"],
            horizontal=True,
            key="calc_mode"
        )
        
        st.markdown("---")
        
        if calculator_mode == "🎯 Skenario Maksimal (110% Target)":
            # ==========================================
            # MODE 1: SKENARIO MAKSIMAL
            # ==========================================
            st.markdown("### 📊 Skenario Maksimal - Jika Semua KPI 110%")
            st.info("Mode ini menampilkan hasil jika seluruh KPI mencapai 110% target dengan kondisi terbaik")
            
            # Create maksimal achievement scenario (110% achievement untuk semua KPI) - using config targets
            maksimal_achievement = {}
            for metric in config["kpi_metrics"]:
                metric_name = metric["name"]
                target = metric["target"]
                # 110% achievement
                maksimal_achievement[metric_name] = {"target": target, "actual": int(target * 1.1)}
            
            # Add compliance scores
            maksimal_achievement.update({
                "tertiary_inner_percentage": 0.55,  # 55% - kategori terbaik
                "ach_rgu_ga": 0.85,  # 85% - above compliance
                "growth_prepaid_revenue": 0.05  # 5% growth - positive
            })
            
            # Calculate maksimal scenario
            result_maksimal = calculate_metrics(config, maksimal_achievement)
            
            # Display maksimal scenario inputs
            st.markdown("#### 📥 Input Skenario (110% Target)")
            
            input_cols = st.columns(len(config["kpi_metrics"]))
            for idx, metric in enumerate(config["kpi_metrics"]):
                with input_cols[idx]:
                    target = metric["target"]
                    actual = int(target * 1.1)
                    st.metric(metric["name"], f"{actual}/{target}", "Achievement: 110%")
            
            fin_cols = st.columns(3)
            with fin_cols[0]:
                st.metric("Tertiary #B Inner", "55%", "Slab Terbaik")
            with fin_cols[1]:
                st.metric("ACH RGU-GA", "85%", "Above Compliance")
            with fin_cols[2]:
                st.metric("Growth Prepaid", "+5%", "Positive Growth")
            
            st.markdown("---")
            
            # Display calculation breakdown for maksimal
            st.markdown("#### 🧮 Perhitungan Detail")
            
            # STEP 1-2
            st.markdown("**STEP 1-2: KPI Cap & Weighted Score**")
            trade_pct = 110
            m2s_pct = 110
            rgu_pct = 110
            trade_cap = apply_kpi_cap(trade_pct)
            m2s_cap = apply_kpi_cap(m2s_pct)
            rgu_cap = apply_kpi_cap(rgu_pct)
            weighted_score_maks = calculate_weighted_score(trade_cap, m2s_cap, rgu_cap)
            
            calc_cols1 = st.columns(len(config["kpi_metrics"]) + 1)
            for idx, metric in enumerate(config["kpi_metrics"]):
                with calc_cols1[idx]:
                    st.metric(f"{metric['name']} Cap", f"{apply_kpi_cap(110)}%")
            
            with calc_cols1[len(config["kpi_metrics"])]:
                st.metric("Weighted Score", f"{format_decimal(weighted_score_maks)}%")
            
            # STEP 3
            st.markdown("**STEP 3: Score Multiplier Mapping**")
            st.metric("Score Multiplier", f"{format_decimal(result_maksimal['score_multiplier'] * 100)}%")
            
            # STEP 4
            st.markdown("**STEP 4: SLA Tariff**")
            st.metric("SLA Tariff (55% Tertiary)", f"{format_decimal(result_maksimal['sla_tariff_pct'])}%")
            
            # STEP 5
            st.markdown("**STEP 5: Compliance Index**")
            comp_cols_maks = st.columns(3)
            with comp_cols_maks[0]:
                st.metric("ACH Score", f"{format_decimal(result_maksimal['ach_score'])}")
            with comp_cols_maks[1]:
                st.metric("Growth Score", f"{format_decimal(result_maksimal['growth_score'])}")
            with comp_cols_maks[2]:
                st.metric("Compliance Index", f"{format_decimal(result_maksimal['compliance_index'])}")
            
            st.metric("Score Compliance (Final)", f"{format_decimal(result_maksimal['score_compliance'])}")
            
            st.markdown("---")
            
            # FINAL RESULT
            st.markdown("### 💰 FINAL FEE - SKENARIO MAKSIMAL")
            
            final_cols = st.columns(2)
            with final_cols[0]:
                st.markdown(f"""
                <div class="metric-card card-success" style="border-left: 5px solid #10b981; padding: 20px; border-radius: 8px;">
                    <div class="metric-label">FINAL FEE</div>
                    <div style="font-size: 32px; font-weight: 800; color: #059669; margin: 15px 0;">
                        {format_currency(result_maksimal['final_fee'])}
                    </div>
                    <div class="metric-subtext">Jika semua KPI mencapai target maksimal</div>
                </div>
                """, unsafe_allow_html=True)
            
            with final_cols[1]:
                st.markdown(f"""
                <div class="metric-card" style="padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0;">
                    <div class="metric-label">DETAIL PERHITUNGAN</div>
                    <div style="font-size: 14px; margin: 10px 0; line-height: 1.8;">
                        <b>Score Multiplier:</b> {format_decimal(result_maksimal['score_multiplier'] * 100)}%<br/>
                        <b>SLA Tariff:</b> {format_decimal(result_maksimal['sla_tariff_pct'])}%<br/>
                        <b>Prepaid Revenue:</b> {format_currency(config['prepaid_revenue'])}<br/>
                        <b>Score Compliance:</b> {format_decimal(result_maksimal['score_compliance'])}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Formula display
            st.info(f"""
            **FORMULA: Final Fee = Score Multiplier × SLA Tariff × Prepaid Revenue × Score Compliance**
            
            = {format_decimal(result_maksimal['score_multiplier'] * 100)}% × {format_decimal(result_maksimal['sla_tariff'] * 100)}% × {format_currency(config['prepaid_revenue'])} × {format_decimal(result_maksimal['score_compliance'])}
            
            = **{format_currency(result_maksimal['final_fee'])}**
            """)
        
        else:
            # MODE 2: SKENARIO CUSTOM
            # ==========================================
            st.markdown("### 📥 Skenario Custom - Input Capaian Anda")
            st.info("📋 Alur: KPI Cap (70-110%) → Weighted Score → Score Multiplier → SLA Tariff → Compliance Index → Final Fee")
            
            # ==========================================
            # STEP 0 & 1: INPUT DATA MENTAH & KPI CAP
            # ==========================================
            st.markdown("#### STEP 0-1: Input Target & Actual Setiap KPI")
            st.info("💡 Input TARGET (nilai standar) dan ACTUAL (capaian), sistem akan auto-hitung %")
            
            kpi_percentages = {}
            
            for i, metric in enumerate(config["kpi_metrics"]):
                st.markdown(f"**{metric['name']}**")
                
                kpi_name = metric["name"]
                kpi_data = st.session_state.calculator_achievement.get(kpi_name, {"target": metric["target"], "actual": 0})
                
                col_t, col_a, col_p = st.columns(3)
                
                with col_t:
                    target_val = st.number_input(
                        "Target",
                        value=int(kpi_data["target"]) if kpi_data else metric["target"],
                        min_value=1,
                        step=10,
                        key=f"target_{kpi_name}"
                    )
                
                with col_a:
                    actual_val = st.number_input(
                        "Actual",
                        value=int(kpi_data["actual"]) if kpi_data else 0,
                        min_value=0,
                        step=10,
                        key=f"actual_{kpi_name}"
                    )
                
                # Calculate percentage automatically
                percentage = calculate_kpi_percentage(target_val, actual_val)
                kpi_percentages[kpi_name] = percentage
                
                # Show percentage and capped value
                capped_pct = apply_kpi_cap(percentage)
                
                with col_p:
                    st.metric("Achievement %", f"{format_decimal(percentage)}%", "")
                    if percentage != capped_pct:
                        st.warning(f"→ Capped: {format_decimal(capped_pct)}%")
                    else:
                        st.success(f"✓ {format_decimal(capped_pct)}%")
                
                # Save to session state
                st.session_state.calculator_achievement[kpi_name] = {
                    "target": target_val,
                    "actual": actual_val
                }
                
                st.divider()
            
            # ==========================================
            # STEP 2: WEIGHTED SCORE
            # ==========================================
            st.markdown("#### STEP 2: Weighted Score Calculation")
            
            # Apply KPI cap untuk setiap KPI
            trade_pct = kpi_percentages.get("Trade Supply", 0)
            m2s_pct = kpi_percentages.get("M2S Absolute", 0)
            rgu_pct = kpi_percentages.get("RGU GA FWA", 0)
            
            trade_capped = apply_kpi_cap(trade_pct)
            m2s_capped = apply_kpi_cap(m2s_pct)
            rgu_capped = apply_kpi_cap(rgu_pct)
            
            weighted_score = calculate_weighted_score(trade_capped, m2s_capped, rgu_capped)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Trade Supply (Capped)", f"{format_decimal(trade_capped)}%", f"Raw: {format_decimal(trade_pct)}%")
            with col2:
                st.metric("M2S Absolute (Capped)", f"{format_decimal(m2s_capped)}%", f"Raw: {format_decimal(m2s_pct)}%")
            with col3:
                st.metric("RGU GA FWA (Capped)", f"{format_decimal(rgu_capped)}%", f"Raw: {format_decimal(rgu_pct)}%")
            
            st.info(f"**Weighted Score = ({format_decimal(trade_capped)}×0.4) + ({format_decimal(m2s_capped)}×0.4) + ({format_decimal(rgu_capped)}×0.2) = {format_decimal(weighted_score)}**")
            
            st.markdown("---")
            
            # ==========================================
            # Input for Tertiary Inner & Compliance
            # ==========================================
            st.markdown("#### STEP 3-5: Input Finansial & Compliance")
            
            # TERTIARY #B INNER (%)
            st.markdown("**Tertiary #B Inner (%)**")
            tertiary_cols = st.columns(3)
            with tertiary_cols[0]:
                tertiary_b = st.number_input(
                    "Tertiary #B",
                    value=st.session_state.calculator_achievement.get("tertiary_b_value", 0.0),
                    min_value=0.0,
                    step=0.01,
                    key="tertiary_b"
                )
                st.session_state.calculator_achievement["tertiary_b_value"] = tertiary_b
            
            with tertiary_cols[1]:
                tertiary_b_inner = st.number_input(
                    "Tertiary #B Inner",
                    value=st.session_state.calculator_achievement.get("tertiary_b_inner_value", 1.0),
                    min_value=0.01,
                    step=0.01,
                    key="tertiary_b_inner"
                )
                st.session_state.calculator_achievement["tertiary_b_inner_value"] = tertiary_b_inner
            
            with tertiary_cols[2]:
                if tertiary_b > 0:
                    tertiary_inner_pct = (tertiary_b_inner / tertiary_b) * 100
                else:
                    tertiary_inner_pct = 0.0
                st.session_state.calculator_achievement["tertiary_inner_percentage"] = tertiary_inner_pct / 100
                st.metric("Hasil (%)", f"{format_decimal(tertiary_inner_pct)}%")
            
            st.markdown("---")
            
            # ACH RGU-GA (%)
            st.markdown("**ACH RGU-GA (%)**")
            ach_cols = st.columns(3)
            with ach_cols[0]:
                ach_actual = st.number_input(
                    "Actual",
                    value=st.session_state.calculator_achievement.get("ach_actual_value", 0.0),
                    min_value=0.0,
                    step=1.0,
                    key="ach_actual"
                )
                st.session_state.calculator_achievement["ach_actual_value"] = ach_actual
            
            with ach_cols[1]:
                ach_target = st.number_input(
                    "Target",
                    value=st.session_state.calculator_achievement.get("ach_target_value", 1.0),
                    min_value=0.01,
                    step=1.0,
                    key="ach_target"
                )
                st.session_state.calculator_achievement["ach_target_value"] = ach_target
            
            with ach_cols[2]:
                if ach_target > 0:
                    ach_rgu_pct = (ach_actual / ach_target) * 100
                else:
                    ach_rgu_pct = 0.0
                st.session_state.calculator_achievement["ach_rgu_ga"] = ach_rgu_pct / 100
                st.metric("Hasil (%)", f"{format_decimal(ach_rgu_pct)}%")
            
            st.markdown("---")
            
            # GROWTH PREPAID REVENUE (%)
            st.markdown("**Growth Prepaid Revenue (%)**")
            growth_cols = st.columns(3)
            with growth_cols[0]:
                growth_prev_month = st.number_input(
                    "Prepaid Revenue (Bulan Lalu)",
                    value=st.session_state.calculator_achievement.get("growth_prev_month_value", 1.0),
                    min_value=0.01,
                    step=0.01,
                    key="growth_prev_month"
                )
                st.session_state.calculator_achievement["growth_prev_month_value"] = growth_prev_month
            
            with growth_cols[1]:
                growth_curr_month = st.number_input(
                    "Prepaid Revenue (Bulan Ini)",
                    value=st.session_state.calculator_achievement.get("growth_curr_month_value", 1.0),
                    min_value=0.01,
                    step=0.01,
                    key="growth_curr_month"
                )
                st.session_state.calculator_achievement["growth_curr_month_value"] = growth_curr_month
            
            with growth_cols[2]:
                if growth_prev_month > 0:
                    growth_pct = ((growth_curr_month / growth_prev_month) - 1) * 100
                else:
                    growth_pct = 0.0
                st.session_state.calculator_achievement["growth_prepaid_revenue"] = growth_pct / 100
                st.metric("Hasil (%)", f"{format_decimal(growth_pct)}%")
            
            st.markdown("---")
            
            # ==========================================
            # CALCULATE METRICS
            # ==========================================
            result = calculate_metrics(config, st.session_state.calculator_achievement)
            
            # ==========================================
            # STEP 3: SCORE MULTIPLIER
            # ==========================================
            st.markdown("#### STEP 3: Score Multiplier Mapping")
            
            score_mult = result["score_multiplier"]
            st.metric("Score Multiplier", f"{score_mult * 100}%")
            
            col_map_info = st.columns(4)
            for slab in config["score_multiplier_mapping"]:
                with col_map_info[0 if slab["label"] == "≥ 105" else 1 if slab["label"] == "80 – <105" else 2 if slab["label"] == "70 – <80" else 3]:
                    color = "green" if (weighted_score >= slab["min"] and weighted_score <= slab["max"]) else "gray"
                    st.markdown(f"<div style='color:{color}'><b>{slab['label']}</b> → {slab['value']}</div>", unsafe_allow_html=True)
            
            st.markdown("---")
            
            # ==========================================
            # STEP 4: SLA TARIFF
            # ==========================================
            st.markdown("#### STEP 4: SLA Tariff (Tertiary #B Inner)")
            
            tertiary_inner = st.session_state.calculator_achievement.get("tertiary_inner_percentage", 0)
            sla_tariff = result["sla_tariff"]
            
            st.metric("SLA Tariff", f"{format_decimal(result['sla_tariff_pct'])}%")
            
            sla_cols = st.columns(3)
            for slab in config["sla_tariff"]:
                idx = config["sla_tariff"].index(slab)
                with sla_cols[idx]:
                    color = "green" if (tertiary_inner >= slab["min"] and tertiary_inner <= slab["max"]) else "gray"
                    st.markdown(f"<div style='color:{color}'><b>{slab['label']}</b> → {format_decimal(slab['rate']*100)}%</div>", unsafe_allow_html=True)
            
            st.markdown("---")
            
            # ==========================================
            # STEP 5: COMPLIANCE CALCULATION
            # ==========================================
            st.markdown("#### STEP 5: Compliance Index (2-Layer)")
            
            ach_rgu_ga = st.session_state.calculator_achievement.get("ach_rgu_ga", 0)
            growth = st.session_state.calculator_achievement.get("growth_prepaid_revenue", 0)
            
            comp_cols = st.columns(3)
            
            with comp_cols[0]:
                st.write("**5A: Component Score**")
                st.write(f"ACH RGU-GA: {format_decimal(result['ach_score'])} {'✓' if ach_rgu_ga >= 0.80 else '✗'}")
                st.write(f"Growth: {format_decimal(result['growth_score'])} {'✓' if growth >= 0 else '✗'}")
            
            with comp_cols[1]:
                st.write("**5B: Compliance Index**")
                st.metric("Index", f"{format_decimal(result['compliance_index'])}")
            
            with comp_cols[2]:
                st.write("**5C: Score Compliance**")
                st.metric("Final Score", f"{format_decimal(result['score_compliance'])}")
            
            st.markdown("---")
            
            # ==========================================
            # STEP 6: FINAL FEE CALCULATION
            # ==========================================
            st.markdown("#### STEP 6: Final Fee Calculation")
            
            final_fee = result["final_fee"]
            
            # Store final_fee in session state for TOTAL INCOME tab
            st.session_state.final_fee = final_fee
            
            calc_info = st.columns(5)
            with calc_info[0]:
                st.metric("Score Multiplier", f"{format_decimal(score_mult * 100)}%")
            with calc_info[1]:
                st.metric("SLA Tariff", f"{format_decimal(result['sla_tariff_pct'])}%")
            with calc_info[2]:
                st.metric("Prepaid Revenue", format_currency(config["prepaid_revenue"]))
            with calc_info[3]:
                st.metric("Score Compliance", f"{format_decimal(result['score_compliance'])}")
            with calc_info[4]:
                st.metric("Final Fee", format_currency(final_fee), delta=None)
            
            formula_text = f"""
        **FINAL FEE = Score Multiplier × SLA Tariff × Prepaid Revenue × Score Compliance**
        
        = {format_decimal(score_mult)} × {format_decimal(result['sla_tariff'])} × {format_currency(config['prepaid_revenue'])} × {format_decimal(result['score_compliance'])}
        
        = **{format_currency(final_fee)}**
        """
            st.success(formula_text)
    
    # ==========================================
    # TAB 2: FIX INCOME (DENGAN UPFRONT MARGIN SAL)
    # ==========================================
    with tab_fix:
        # ==========================================
        # BAGIAN ATAS: TOTAL BENEFIT PER BULAN
        # ==========================================
        st.markdown("### 📊 TOTAL BENEFIT PER BULAN (RATA-RATA BULAN SEBELUMNYA)")
        st.caption("Rata-rata dari benefit bulan-bulan sebelumnya yang sudah diisi")
        
        # Pilih bulan untuk melihat total benefit
        selected_month_for_avg = st.selectbox(
            "Pilih Bulan untuk Melihat Total Benefit",
            options=list(bulan_map.keys()),
            index=list(bulan_map.keys()).index(pilih_bulan),
            key="selected_month_average"
        )
        
        # Hitung rata-rata dari bulan-bulan sebelumnya
        selected_month_upper = selected_month_for_avg.upper()
        bulan_list = list(bulan_map.keys())
        selected_month_idx = bulan_list.index(selected_month_for_avg)
        
        # Ambil data dari bulan-bulan sebelumnya (index 0 sampai selected_month_idx - 1)
        previous_months_values = []
        if selected_month_idx > 0:  # Ada bulan sebelumnya
            for i in range(selected_month_idx):
                month_upper = bulan_list[i].upper()
                month_value = st.session_state.monthly_total_benefits.get(month_upper, 0)
                if month_value > 0:  # Hanya ambil yang sudah diisi
                    previous_months_values.append(month_value)
        
        # Hitung rata-rata
        if len(previous_months_values) > 0:
            total_benefit_month = sum(previous_months_values) / len(previous_months_values)
        else:
            total_benefit_month = 0
        
        # Tampilkan total benefit
        col_avg1, col_avg2 = st.columns([1, 2])
        
        with col_avg1:
            st.metric(
                "📅 Bulan",
                selected_month_for_avg,
                "Dipilih untuk analisis"
            )
        
        with col_avg2:
            if total_benefit_month > 0:
                st.metric(
                    "💰 Total Benefit Bulan Ini",
                    format_idr_jt(total_benefit_month),
                    f"Rata-rata {len(previous_months_values)} bulan sebelumnya"
                )
            else:
                st.metric(
                    "💰 Total Benefit Bulan Ini",
                    format_idr_jt(total_benefit_month),
                    "Belum ada data bulan sebelumnya"
                )
        
        st.divider()
        
        st.markdown(f"### SLA {pilih_bulan.upper()} 2026")
        st.markdown(f"**Wilayah:** {wilayah} | **Mitra:** {mitra}")
        st.divider()

        if "Indosat" in mitra:
            # ==========================================
            # REPROCESS SAL DATA BERDASARKAN WILAYAH YANG DIPILIH
            # ==========================================
            # Recalculate untuk memastikan mengikuti perubahan wilayah di filter
            upfront_margin_income = 0
            saldo_sum_paid_in = 0
            saldo_breakdown_df_local = pd.DataFrame()
            
            df_sal = get_sheet_fuzzy(dfs, "SAL")
            
            if df_sal is None:
                st.error("""
                ❌ **Sheet SAL tidak ditemukan!**
                
                Pastikan file Excel memiliki sheet bernama "SAL" dengan kolom:
                - SDP (berisi wilayah: KEDAMEAN, DAWARBLANDONG, SANGKAPURA)
                - Details (berisi "ESCM Allocation from SAP| |API")
                - Paid In (berisi nilai nominal)
                """)
            else:
                saldo_chart_df_temp, saldo_sum_paid_in, saldo_breakdown_df_local = get_daily_saldo_data_indosat(
                    df_sal, wilayah, bulan_idx, debug=False
                )
            
            # Hitung upfront margin dari sum paid in
            upfront_margin_income = saldo_sum_paid_in * 0.015
            
            # ==========================================
            # BAGIAN 1: UPFRONT MARGIN 1.5% (DARI SAL SHEET)
            # ==========================================
            st.markdown("### 📌 UPFRONT MARGIN 1.5% (ESCM Allocation from SAP)")
            st.markdown("_Sumber: Sheet SAL | Filter: Details = 'ESCM Allocation from SAP| |API' | Income: Paid In × 1.5%_")
            st.divider()

            # DEBUG SECTION untuk SAL
            with st.expander("🔍 DEBUG: SAL Sheet Processing", expanded=False):
                st.info("**Informasi Detail Pemrosesan Sheet SAL:**")
                
                if df_sal is not None:
                    st.success("✅ Sheet SAL ditemukan")
                    
                    # Show sample data
                    st.write("**Preview 5 Baris Pertama:**")
                    st.dataframe(df_sal.iloc[:5], use_container_width=True, height=200)
                    
                    st.write("**Detail Pemrosesan:**")
                    col_d1, col_d2, col_d3 = st.columns(3)
                    with col_d1:
                        st.metric("Total Baris", len(df_sal))
                    with col_d2:
                        st.metric("Total Kolom", len(df_sal.columns))
                    with col_d3:
                        st.metric("Wilayah Filter", wilayah)
                    
                    # Jalankan debug
                    st.write("**Hasil Filter ESCM Allocation:**")
                    print("\n" + "="*60)
                    print(f"DEBUG: Membaca sheet SAL untuk wilayah {wilayah}")
                    print("="*60)
                    _, debug_sum, debug_breakdown = get_daily_saldo_data_indosat(
                        df_sal, wilayah, bulan_idx, debug=True
                    )
                    print("="*60 + "\n")
                    
                    st.write(f"✅ **Sum Paid In (ESCM):** {format_idr_jt(debug_sum)}")
                    st.write(f"✅ **Upfront Margin 1.5%:** {format_idr_jt(debug_sum * 0.015)}")
                    
                    if not debug_breakdown.empty:
                        st.write("**Breakdown per SDP:**")
                        st.dataframe(debug_breakdown, use_container_width=True)
                else:
                    st.error("❌ Sheet SAL tidak ditemukan di file Excel")

            # Tampilkan Sum Paid In dan Upfront Margin
            col_upfront1, col_upfront2 = st.columns(2)
            
            with col_upfront1:
                st.metric(
                    "💰 Sum Paid In (ESCM Allocation)",
                    format_idr_jt(saldo_sum_paid_in),
                    delta=f"Dari SAL sheet - Wilayah {wilayah}",
                    delta_color="normal"
                )
            
            with col_upfront2:
                st.metric(
                    "📈 Upfront Margin 1.5%",
                    format_idr_jt(upfront_margin_income),
                    delta=f"= {format_idr_jt(saldo_sum_paid_in)} × 1.5%",
                    delta_color="normal"
                )

            st.divider()

            # ==========================================
            # BAGIAN 2: RELOAD & DATA PACK (TIDAK PERLU DIKALIKAN) 
            # ==========================================
            
            # Recalculate transaction match juga
            t_tr_reload, total_paid_in_reload, total_debit_reload = calculate_transaction_match(dfs, wilayah, transaction_types=['Indosat Reload', 'Purchase Data Package'])
            reload_income = 0
            
            # HITUNG: Total Amount_Debit (SEMUA TRANSAKSI dengan status "completed")
            total_amount_debit_all_completed = 0
            try:
                df_trx = None
                for name in dfs.keys():
                    if "TRX" in name.upper() or "TRANSACTION" in name.upper():
                        df_trx = dfs[name]
                        break
                
                if df_trx is None:
                    df_trx = get_sheet_fuzzy(dfs, "TRX")
                
                if df_trx is not None and len(df_trx) > 2:
                    header_row = 0
                    col_sdp_trx = -1
                    col_area = -1
                    col_amount_debit = -1
                    col_status = -1
                    
                    for r in range(min(5, len(df_trx))):
                        row_vals = [str(x).upper() for x in df_trx.iloc[r].tolist()]
                        for i, v in enumerate(row_vals):
                            v_clean = str(v).strip()
                            if "SDP" in v_clean:
                                col_sdp_trx = i
                                header_row = r
                            if "AREA" in v_clean:
                                col_area = i
                                header_row = r
                            if "AMOUNT" in v_clean and "DEBIT" in v_clean:
                                col_amount_debit = i
                            if "TRANSACTION" in v_clean and "STATUS" in v_clean:
                                col_status = i
                        
                        if (col_sdp_trx != -1 or col_area != -1) and col_amount_debit != -1 and col_status != -1:
                            break
                    
                    if col_amount_debit != -1 and col_status != -1:
                        region_upper = wilayah.upper()
                        for idx in range(header_row + 1, len(df_trx)):
                            try:
                                row = df_trx.iloc[idx]
                                
                                val_sdp = str(row[col_sdp_trx]).upper() if col_sdp_trx != -1 else ""
                                val_area = str(row[col_area]).upper() if col_area != -1 else ""
                                
                                if region_upper not in val_sdp and region_upper not in val_area:
                                    continue
                                
                                val_status = str(row[col_status]).upper()
                                if "COMPLETED" not in val_status:
                                    continue
                                
                                amount_val = row[col_amount_debit]
                                if pd.notna(amount_val):
                                    try:
                                        amount = float(str(amount_val).replace(",", ""))
                                        total_amount_debit_all_completed += amount
                                    except:
                                        pass
                            except:
                                continue
            except:
                total_amount_debit_all_completed = 0
            
            # HITUNG OUTER: Total Amount_Debit (Reload & Data Pack, completed) - Total Paid In
            total_amount_debit_completed = 0
            try:
                df_trx = None
                trx_sheet_name = None
                for name in dfs.keys():
                    if "TRX" in name.upper() or "TRANSACTION" in name.upper():
                        df_trx = dfs[name]
                        trx_sheet_name = name
                        break
                
                if df_trx is None:
                    df_trx = get_sheet_fuzzy(dfs, "TRX")
                
                if df_trx is not None and len(df_trx) > 2:
                    # Cari header row dan kolom
                    header_row = 0
                    col_sdp_trx = -1
                    col_area = -1
                    col_trx_type = -1
                    col_amount_debit = -1
                    col_status = -1
                    
                    # Scan row 0-5 untuk menemukan kolom
                    for r in range(min(5, len(df_trx))):
                        row_vals = [str(x).upper() for x in df_trx.iloc[r].tolist()]
                        for i, v in enumerate(row_vals):
                            v_clean = str(v).strip()
                            if "SDP" in v_clean:
                                col_sdp_trx = i
                                header_row = r
                            if "AREA" in v_clean:
                                col_area = i
                                header_row = r
                            if "TRANSACTION" in v_clean and "TYPE" in v_clean:
                                col_trx_type = i
                            if "AMOUNT" in v_clean and "DEBIT" in v_clean:
                                col_amount_debit = i
                            if "TRANSACTION" in v_clean and "STATUS" in v_clean:
                                col_status = i
                        
                        if col_trx_type != -1 and (col_sdp_trx != -1 or col_area != -1) and col_amount_debit != -1 and col_status != -1:
                            break
                    
                    # Filter dan hitung
                    if col_trx_type != -1 and col_amount_debit != -1 and col_status != -1:
                        region_upper = wilayah.upper()
                        for idx in range(header_row + 1, len(df_trx)):
                            try:
                                row = df_trx.iloc[idx]
                                
                                # Cek wilayah
                                val_sdp = str(row[col_sdp_trx]).upper() if col_sdp_trx != -1 else ""
                                val_area = str(row[col_area]).upper() if col_area != -1 else ""
                                
                                if region_upper not in val_sdp and region_upper not in val_area:
                                    continue
                                
                                # Cek transaction type
                                val_type = str(row[col_trx_type]).upper()
                                if not ("RELOAD" in val_type or "DATA" in val_type):
                                    continue
                                
                                # Cek status
                                val_status = str(row[col_status]).upper()
                                if "COMPLETED" not in val_status:
                                    continue
                                
                                # Ambil Amount Debit
                                amount_val = row[col_amount_debit]
                                if pd.notna(amount_val):
                                    try:
                                        amount = float(str(amount_val).replace(",", ""))
                                        total_amount_debit_completed += amount
                                    except:
                                        pass
                            except:
                                continue
            except:
                total_amount_debit_completed = 0
            
            # Hitung Outer
            outer_reload = total_amount_debit_completed - total_paid_in_reload
            
            with st.expander("🔍 DEBUG: TRX & COM Match", expanded=False):
                st.warning("Klik untuk melihat detail kalkulasi transaksi match...")
                debug_match_count, debug_paid_in, debug_amount_debit = calculate_transaction_match(dfs, wilayah, transaction_types=['Indosat Reload', 'Purchase Data Package'], debug=True)
                st.info(f"✓ Hasil Match: Match={debug_match_count}, Paid In={debug_paid_in}, Amount Debit={debug_amount_debit}")

            # ==========================================
            # URUTKAN METRIK DARI UMUM KE SPESIFIK
            # ==========================================
            
            st.markdown("### 📊 Analisis Reload & Data Pack")
            
            # 1. PALING UMUM: Total Amount Debit (SEMUA transaksi, completed)
            st.markdown("**Level 1 - Overview (Semua Transaksi Completed)**")
            st.metric("💰 Total Amount Debit (Semua Transaksi)", format_idr_jt(total_amount_debit_all_completed))
            
            st.markdown("---")
            
            # 2-3. FILTER SPESIFIK RELOAD & DATA PACK: Match dan Amount Debit
            st.markdown("**Level 2 - Reload & Data Pack Spesifik**")
            c1, c2 = st.columns(2)
            with c1: 
                st.metric("📌 Jumlah Transaksi Match", f"{t_tr_reload:,.0f}")
            with c2:
                st.metric("💳 Total Amount Debit (Match)", format_idr_jt(total_debit_reload))

            st.markdown("---")

            # 4-6. DETAIL: Paid In, Achievement, Outer
            st.markdown("**Level 3 - Detail & Analisis**")
            c_reload1, c_reload2, c_reload3 = st.columns(3)
            with c_reload1:
                st.metric("✅ Total Paid In", format_idr_jt(total_paid_in_reload))
            with c_reload2:
                achievement_pct = (total_paid_in_reload / total_debit_reload * 100) if total_debit_reload > 0 else 0
                st.metric("📈 Achievement %", f"{achievement_pct:.2f}%")
            with c_reload3:
                st.metric("⚠️ Outer", format_idr_jt(outer_reload))

            st.divider()

            # ==========================================
            # BAGIAN 3: VOUCHER REDEMPTION
            # ==========================================
            st.markdown("### 🎫 Voucher Redemption")

            voucher_months = st.multiselect(
                "Pilih Bulan",
                options=list(bulan_map.keys()),
                default=[pilih_bulan],
                max_selections=3,
                key="voucher_months_fix"
            )

            total_voucher_reward = 0

            for m in voucher_months:
                val = st.number_input(f"Nominal {m}", value=0, step=100000, key=f"vc_fix_{m}")
                total_voucher_reward += val
                st.markdown(f"**{m}:** Rp {val:,.0f}")

            avg_voucher = total_voucher_reward / len(voucher_months) if len(voucher_months) > 0 else 0

            st.divider()
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                st.metric("Total Voucher Reward", format_idr_jt(total_voucher_reward))
            with col_v2:
                st.metric("Rata-rata Voucher per Bulan", format_idr_jt(avg_voucher))

            st.divider()

            # ==========================================
            # BAGIAN 4: OUTER TRANSACTION
            # ==========================================
            st.markdown("### 🔗 Outer Transaction")

            outer_months = st.multiselect(
                "Pilih Bulan Outer",
                options=list(bulan_map.keys()),
                default=[pilih_bulan],
                max_selections=3,
                key="outer_months_fix"
            )

            total_outer_benefit = 0

            for m in outer_months:
                v = st.number_input(f"Nominal {m}", value=0, step=100000, key=f"ot_fix_{m}")
                total_outer_benefit += v
                st.markdown(f"**{m}:** Rp {v:,.0f}")

            avg_outer = 0
            if len(outer_months) > 0:
                avg_outer = total_outer_benefit / len(outer_months)

            st.divider()
            col_o1, col_o2 = st.columns(2)
            with col_o1:
                st.metric("Total Outer Benefit", format_idr_jt(total_outer_benefit))
            with col_o2:
                st.metric("Rata-rata Outer per Bulan", format_idr_jt(avg_outer))

            st.divider()

            # ==========================================
            # RINGKASAN TOTAL INCOME FIX
            # ==========================================
            st.markdown("## 💰 SUMMARY TOTAL INCOME FIX")

            summary_cols = st.columns(4)
            with summary_cols[0]:
                st.metric("Upfront (1.5%)", format_idr_jt(upfront_margin_income))
            with summary_cols[1]:
                st.metric("Reload & Data Pack", format_idr_jt(total_paid_in_reload))
            with summary_cols[2]:
                st.metric("Voucher Redemption", format_idr_jt(total_voucher_reward))
            with summary_cols[3]:
                st.metric("Outer Transaction", format_idr_jt(total_outer_benefit))

            # TOTAL KESELURUHAN
            total_income_all = upfront_margin_income + total_paid_in_reload + total_voucher_reward + total_outer_benefit

            # Update session state dengan total benefit bulan ini
            st.session_state.monthly_total_benefits[pilih_bulan.upper()] = total_income_all

            st.success(f"✅ **TOTAL INCOME FIX:** {format_idr_jt(total_income_all)}")
            st.info(f"📊 Komponen: Upfront {format_idr_jt(upfront_margin_income)} + Reload & Data Pack {format_idr_jt(total_paid_in_reload)} + Voucher Redemption {format_idr_jt(total_voucher_reward)} + Outer Transaction {format_idr_jt(total_outer_benefit)}")

        else:
            # ==========================================
            # TRI KIOSK - FIX INCOME (TANPA RELOAD & DATA PACK)
            # ==========================================
            
            # ==========================================
            # BAGIAN 1: UPFRONT MARGIN (DARI PRIM SHEET)
            # ==========================================
            st.markdown("### 📌 UPFRONT MARGIN 1.5% (PRIM Sheet)")
            st.markdown("_Sumber: Sheet PRIM | Filter: SDP sesuai Wilayah | Income: Amount × 1.5%_")
            st.divider()

            # Read PRIM sheet
            upfront_sum_paid_in_tri = 0
            prim_breakdown_df_local = pd.DataFrame()
            
            df_prim = get_sheet_fuzzy(dfs, "PRIM")
            
            if df_prim is None:
                st.error("""
                ❌ **Sheet PRIM tidak ditemukan!**
                
                Pastikan file Excel memiliki sheet bernama "PRIM" dengan kolom:
                - SDP (berisi wilayah: KEDAMEAN, DAWARBLANDONG, SANGKAPURA)
                - AMOUNT (berisi nilai nominal)
                """)
            else:
                upfront_sum_paid_in_tri, prim_breakdown_df_local = get_upfront_data_tri(
                    df_prim, wilayah, debug=False
                )
            
            # Hitung upfront margin dari sum amount
            upfront_margin_income_tri = upfront_sum_paid_in_tri * 0.015

            # DEBUG SECTION untuk TRI UPFRONT
            with st.expander("🔍 DEBUG: TRI PRIM Data", expanded=False):
                st.info("**Informasi Detail Pemrosesan Sheet PRIM:**")
                
                if df_prim is not None:
                    st.success("✅ Sheet PRIM ditemukan")
                    
                    # Show sample data
                    st.write("**Preview 5 Baris Pertama:**")
                    st.dataframe(df_prim.iloc[:5], use_container_width=True, height=200)
                    
                    st.write("**Detail Pemrosesan:**")
                    col_tri_d1, col_tri_d2, col_tri_d3 = st.columns(3)
                    with col_tri_d1:
                        st.metric("Total Baris", len(df_prim))
                    with col_tri_d2:
                        st.metric("Total Kolom", len(df_prim.columns))
                    with col_tri_d3:
                        st.metric("Wilayah Filter", wilayah)
                    
                    # Jalankan debug
                    st.write("**Hasil Filter Berdasarkan Wilayah:**")
                    print("\n" + "="*60)
                    print(f"DEBUG: Membaca sheet PRIM untuk wilayah {wilayah}")
                    print("="*60)
                    debug_sum_tri, debug_breakdown_tri = get_upfront_data_tri(
                        df_prim, wilayah, debug=True
                    )
                    print("="*60 + "\n")
                    
                    st.write(f"✅ **Total Amount (PRIM):** {format_idr_jt(debug_sum_tri)}")
                    st.write(f"✅ **Upfront Margin 1.5%:** {format_idr_jt(debug_sum_tri * 0.015)}")
                    
                    if not debug_breakdown_tri.empty:
                        st.write("**Breakdown per SDP:**")
                        st.dataframe(debug_breakdown_tri, use_container_width=True)
                else:
                    st.error("❌ Sheet PRIM tidak ditemukan di file Excel")

            # Tampilkan Sum Amount dan Upfront Margin TRI
            col_upfront_tri1, col_upfront_tri2 = st.columns(2)
            
            with col_upfront_tri1:
                st.metric(
                    "💰 Total Amount (PRIM)",
                    format_idr_jt(upfront_sum_paid_in_tri),
                    delta=f"Dari PRIM sheet - Wilayah {wilayah}",
                    delta_color="normal"
                )
            
            with col_upfront_tri2:
                st.metric(
                    "📈 Upfront Margin 1.5%",
                    format_idr_jt(upfront_margin_income_tri),
                    delta=f"= {format_idr_jt(upfront_sum_paid_in_tri)} × 1.5%",
                    delta_color="normal"
                )

            st.divider()

            # ==========================================
            # BAGIAN 2: VOUCHER REDEMPTION
            # ==========================================
            st.markdown("### 🎫 Voucher Redemption")

            voucher_months_tri = st.multiselect(
                "Pilih Bulan",
                options=list(bulan_map.keys()),
                default=[pilih_bulan],
                max_selections=3,
                key="voucher_months_tri"
            )

            total_voucher_reward_tri = 0

            for m in voucher_months_tri:
                val = st.number_input(f"Nominal {m}", value=0, step=100000, key=f"vc_tri_{m}")
                total_voucher_reward_tri += val
                st.markdown(f"**{m}:** Rp {val:,.0f}")

            avg_voucher_tri = total_voucher_reward_tri / len(voucher_months_tri) if len(voucher_months_tri) > 0 else 0

            st.divider()
            col_v1_tri, col_v2_tri = st.columns(2)
            with col_v1_tri:
                st.metric("Total Voucher Reward", format_idr_jt(total_voucher_reward_tri))
            with col_v2_tri:
                st.metric("Rata-rata Voucher per Bulan", format_idr_jt(avg_voucher_tri))

            st.divider()

            # ==========================================
            # BAGIAN 3: OUTER TRANSACTION
            # ==========================================
            st.markdown("### 🔗 Outer Transaction")

            outer_months_tri = st.multiselect(
                "Pilih Bulan Outer",
                options=list(bulan_map.keys()),
                default=[pilih_bulan],
                max_selections=3,
                key="outer_months_tri"
            )

            total_outer_benefit_tri = 0

            for m in outer_months_tri:
                v = st.number_input(f"Nominal {m}", value=0, step=100000, key=f"ot_tri_{m}")
                total_outer_benefit_tri += v
                st.markdown(f"**{m}:** Rp {v:,.0f}")

            avg_outer_tri = 0
            if len(outer_months_tri) > 0:
                avg_outer_tri = total_outer_benefit_tri / len(outer_months_tri)

            st.divider()
            col_o1_tri, col_o2_tri = st.columns(2)
            with col_o1_tri:
                st.metric("Total Outer Benefit", format_idr_jt(total_outer_benefit_tri))
            with col_o2_tri:
                st.metric("Rata-rata Outer per Bulan", format_idr_jt(avg_outer_tri))

            st.divider()

            # ==========================================
            # RINGKASAN TOTAL INCOME FIX TRI
            # ==========================================
            st.markdown("## 💰 SUMMARY TOTAL INCOME FIX")
            st.markdown("_Total income dari komponen Upfront, Voucher, dan Outer_")

            summary_cols_tri = st.columns(3)
            with summary_cols_tri[0]:
                st.metric("Upfront", format_idr_jt(upfront_margin_income_tri))
            with summary_cols_tri[1]:
                st.metric("Voucher", format_idr_jt(total_voucher_reward_tri))
            with summary_cols_tri[2]:
                st.metric("Outer", format_idr_jt(total_outer_benefit_tri))

            # TOTAL KESELURUHAN
            total_income_all_tri = upfront_margin_income_tri + total_voucher_reward_tri + total_outer_benefit_tri

            # Update session state dengan total benefit bulan ini
            st.session_state.monthly_total_benefits[pilih_bulan.upper()] = total_income_all_tri

            st.success(f"✅ **TOTAL INCOME FIX:** {format_idr_jt(total_income_all_tri)}")
            st.info(f"📊 Komponen: Upfront {format_idr_jt(upfront_margin_income_tri)} + Voucher {format_idr_jt(total_voucher_reward_tri)} + Outer {format_idr_jt(total_outer_benefit_tri)}")

    # ==========================================
    # TAB 3: TACTICAL INCOME
    # ==========================================
    with tab_tactical:
        st.markdown("### 🎯 Tactical Income Calculator")
        st.info("Hitung tactical income berdasarkan syarat tertentu dari pencapaian KPI & Compliance")
        
        # Get region config
        tactical_config = st.session_state.kpi_calculator_config["regions"][wilayah]
        prepaid_revenue = tactical_config.get("prepaid_revenue", 1_000_000_000)
        
        # ==========================================
        # JENIS 1: ADDITIONAL FEE SLA (+0.9% PREPAID REVENUE)
        # ==========================================
        st.markdown("#### 1️⃣ ADDITIONAL FEE SLA (+0.9% Prepaid Revenue)")
        st.caption("Syarat: Semua KPI score ≥ 100% AND RGU GA Compliance ≥ 80%")
        
        # Get achievement data dari Tab 1
        tactical_achievement = st.session_state.get("calculator_achievement", {})
        
        # Hitung score setiap KPI
        kpi_scores = {}
        for metric in tactical_config["kpi_metrics"]:
            metric_name = metric["name"]
            target = metric["target"]
            achievement_data = tactical_achievement.get(metric_name, {"target": target, "actual": 0})
            actual = achievement_data.get("actual", 0) if isinstance(achievement_data, dict) else achievement_data
            score = (actual / target * 100) if target > 0 else 0
            kpi_scores[metric_name] = score
        
        # Ambil RGU GA Compliance
        rgu_ga_compliance = tactical_achievement.get("ach_rgu_ga", 0) * 100
        
        # Check syarat
        all_kpi_above_100 = all(score >= 100 for score in kpi_scores.values())
        rgu_ga_above_80 = rgu_ga_compliance >= 80
        condition_met = all_kpi_above_100 and rgu_ga_above_80
        
        # Display status syarat
        st.markdown("**📋 Status Syarat:**")
        status_cols = st.columns(2)
        
        with status_cols[0]:
            st.markdown("**Syarat 1: Semua KPI Score ≥ 100%**")
            for kpi_name, score in kpi_scores.items():
                status_icon = "✅" if score >= 100 else "❌"
                st.write(f"{status_icon} {kpi_name}: {format_idr_jt(score) if score != int(score) else f'{score:.2f}'}%")
        
        with status_cols[1]:
            st.markdown("**Syarat 2: RGU GA Compliance**")
            status_icon = "✅" if rgu_ga_above_80 else "❌"
            st.write(f"{status_icon} RGU GA Compliance: {rgu_ga_compliance:.2f}%")
        
        st.markdown("---")
        
        # Hitung income
        if condition_met:
            additional_fee_sla = prepaid_revenue * 0.009
            st.success(f"✅ **Syarat Terpenuhi!**")
            st.markdown(f"""
            **ADDITIONAL FEE SLA:**
            - Tarif: 0.9% × Prepaid Revenue
            - Perhitungan: 0.9% × {format_idr_jt(prepaid_revenue)}
            - **INCOME: {format_idr_jt(additional_fee_sla)}**
            """)
        else:
            additional_fee_sla = 0
            st.warning(f"❌ **Syarat Tidak Terpenuhi**")
            st.markdown(f"""
            Alasan tidak terpenuhi:
            - {'✅ Semua KPI ≥ 100%' if all_kpi_above_100 else '❌ Ada KPI < 100%'}
            - {'✅ RGU GA Compliance ≥ 80%' if rgu_ga_above_80 else '❌ RGU GA Compliance < 80%'}
            
            Income: **Rp 0**
            """)
        
        st.markdown("---")
        
        # ==========================================
        # JENIS 2: TERRITORY DEVELOPMENT SUPPORT (TDS)
        # ==========================================
        st.markdown("#### 2️⃣ TERRITORY DEVELOPMENT SUPPORT (TDS) - Growth-Based Fee")
        st.caption("Income berdasarkan pertumbuhan dari baseline")
        
        with st.expander("⚙️ Setup Growth Brackets (Konfigurasi)", expanded=False):
            st.markdown("**Konfigurasi Growth Bracket dan Fee Percentage**")
            
            brackets = st.session_state.tds_growth_brackets
            new_brackets = []
            
            for idx, bracket in enumerate(brackets):
                st.markdown(f"**Bracket {idx + 1}**")
                col1, col2, col3, col4, col5 = st.columns([1.2, 1.2, 0.8, 1, 0.8])
                
                with col1:
                    min_g = st.number_input(
                        f"Min Growth %",
                        value=bracket["min_growth"],
                        step=0.5,
                        key=f"tds_min_{idx}"
                    )
                
                with col2:
                    has_max = bracket["max_growth"] is not None
                    max_enabled = st.checkbox(
                        "Set Max",
                        value=has_max,
                        key=f"tds_has_max_{idx}"
                    )
                
                with col3:
                    if max_enabled:
                        max_g = st.number_input(
                            f"Max %",
                            value=bracket["max_growth"] if bracket["max_growth"] is not None else 10.0,
                            step=0.5,
                            key=f"tds_max_{idx}"
                        )
                    else:
                        st.markdown("**∞**")
                        max_g = None
                
                with col4:
                    fee_p = st.number_input(
                        f"Fee %",
                        value=bracket["fee_percent"],
                        step=0.1,
                        key=f"tds_fee_{idx}"
                    )
                
                with col5:
                    if len(brackets) > 1:
                        if st.button("❌", key=f"tds_del_{idx}"):
                            st.session_state.tds_growth_brackets.pop(idx)
                            st.rerun()
                
                new_brackets.append({
                    "min_growth": min_g,
                    "max_growth": max_g,
                    "fee_percent": fee_p
                })
            
            st.session_state.tds_growth_brackets = new_brackets
            
            if st.button("➕ Add New Bracket"):
                st.session_state.tds_growth_brackets.append({
                    "min_growth": 0.0,
                    "max_growth": 10.0,
                    "fee_percent": 1.0
                })
                st.rerun()
        
        st.markdown("**📥 Input Growth Data:**")
        tds_input_cols = st.columns(2)
        
        with tds_input_cols[0]:
            baseline_tertiary = st.number_input(
                "Baseline Sales (Rp)",
                value=100_000_000,
                step=10_000_000,
                key="tds_baseline"
            )
        
        with tds_input_cols[1]:
            actual_tertiary = st.number_input(
                "Actual Sales (Rp)",
                value=107_500_000,
                step=10_000_000,
                key="tds_actual"
            )
        
        if baseline_tertiary > 0:
            growth_pct = ((actual_tertiary - baseline_tertiary) / baseline_tertiary) * 100
        else:
            growth_pct = 0
        
        matched_bracket = None
        for bracket in st.session_state.tds_growth_brackets:
            min_g = bracket["min_growth"]
            max_g = bracket["max_growth"]
            
            if max_g is None:
                if growth_pct >= min_g:
                    matched_bracket = bracket
                    break
            else:
                if min_g <= growth_pct <= max_g:
                    matched_bracket = bracket
                    break
        
        st.markdown("**📊 Calculation Result:**")
        result_cols = st.columns(4)
        
        with result_cols[0]:
            st.metric("Baseline", format_idr_jt(baseline_tertiary))
        with result_cols[1]:
            st.metric("Actual", format_idr_jt(actual_tertiary))
        with result_cols[2]:
            st.metric("Growth %", f"{growth_pct:.2f}%")
        with result_cols[3]:
            if matched_bracket:
                st.metric("Fee %", f"{matched_bracket['fee_percent']:.2f}%")
            else:
                st.metric("Fee %", "N/A")
        
        if matched_bracket and actual_tertiary > 0:
            tds_fee_pct = matched_bracket["fee_percent"] / 100
            tds_income = actual_tertiary * tds_fee_pct
            
            st.success(f"✅ **TERRITORY DEVELOPMENT SUPPORT (TDS)**")
            max_display = f"{matched_bracket['max_growth']:.2f}%" if matched_bracket['max_growth'] is not None else "∞"
            st.markdown(f"""
            **Calculation:**
            - Bracket: Growth {matched_bracket['min_growth']:.2f}% - {max_display}
            - Fee Rate: {matched_bracket['fee_percent']:.2f}% × {format_idr_jt(actual_tertiary)}
            - **INCOME: {format_idr_jt(tds_income)}**
            """)
        else:
            tds_income = 0
            st.warning("⚠️ **Tidak ada bracket yang cocok atau data tidak valid**")
            st.markdown(f"Income: **Rp 0**")
        
        st.markdown("---")
        
        # ==========================================
        # JENIS 3: ADDITIONAL INCOME (OPTIONAL/DINAMIS)
        # ==========================================
        st.markdown("#### 3️⃣ ADDITIONAL INCOME (Optional)")
        st.caption("Income tambahan yang bisa ditambahkan sesuai kebutuhan")
        
        enable_third = st.checkbox(
            "✅ Aktifkan Additional Income",
            value=st.session_state.third_income_enabled,
            key="third_income_toggle"
        )
        st.session_state.third_income_enabled = enable_third
        
        third_income_total = 0
        
        if enable_third:
            st.markdown("**📋 Daftar Additional Income Items:**")
            
            items = st.session_state.third_income_items
            new_items = []
            
            for idx, item in enumerate(items):
                col1, col2, col3 = st.columns([2, 1.5, 0.5])
                
                with col1:
                    income_name = st.text_input(
                        "Nama Income",
                        value=item["name"],
                        key=f"third_income_name_{idx}",
                        placeholder="contoh: Bonus Tambahan"
                    )
                
                with col2:
                    income_amount = st.number_input(
                        "Jumlah (Rp)",
                        value=item["amount"],
                        step=1_000_000,
                        key=f"third_income_amount_{idx}"
                    )
                
                with col3:
                    if st.button("❌", key=f"third_income_delete_{idx}"):
                        st.session_state.third_income_items.pop(idx)
                        st.rerun()
                
                new_items.append({
                    "name": income_name,
                    "amount": income_amount
                })
                third_income_total += income_amount
            
            st.session_state.third_income_items = new_items
            
            col_add = st.columns([0.3, 0.7])
            with col_add[0]:
                if st.button("➕ Tambah Income", key="third_income_add"):
                    st.session_state.third_income_items.append({
                        "name": "Income Baru",
                        "amount": 0
                    })
                    st.rerun()
            
            st.markdown("---")
            
            st.markdown("**📊 Summary Additional Income:**")
            if new_items:
                for item in new_items:
                    st.write(f"• **{item['name']}**: {format_idr_jt(item['amount'])}")
                st.markdown(f"**Total Additional Income: {format_idr_jt(third_income_total)}**")
            else:
                st.info("Belum ada item income yang ditambahkan")
        else:
            third_income_total = 0
        
        st.markdown("---")
        
        # ==========================================
        # TOTAL TACTICAL INCOME (SUMMARY)
        # ==========================================
        st.markdown("#### 💰 TOTAL TACTICAL INCOME")
        
        total_tactical_income = additional_fee_sla + tds_income + third_income_total
        
        summary_cols = st.columns(4)
        with summary_cols[0]:
            st.metric("Additional Fee SLA", format_idr_jt(additional_fee_sla))
        with summary_cols[1]:
            st.metric("TDS Income", format_idr_jt(tds_income))
        with summary_cols[2]:
            st.metric("Additional Income", format_idr_jt(third_income_total))
        with summary_cols[3]:
            st.metric("TOTAL", format_idr_jt(total_tactical_income), delta="Tactical")
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; color: white;">
            <div style="font-size: 14px; opacity: 0.9;">TOTAL TACTICAL INCOME</div>
            <div style="font-size: 32px; font-weight: bold; margin-top: 10px;">{format_idr_jt(total_tactical_income)}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Store tactical income ke session state untuk digunakan di Tab Total Income
        st.session_state.total_tactical_income = total_tactical_income
    
    # ==========================================
    # ==========================================
    # TAB 4: TOTAL INCOME
    # ==========================================
    with tab_total:
        st.markdown("### 💵 Total Income Calculator - Dua Skenario")
        
        # Get values from session state
        final_fee_custom = st.session_state.get("final_fee", 0)
        selected_month_upper = pilih_bulan.upper()
        total_income_fix = st.session_state.monthly_total_benefits.get(selected_month_upper, 0)
        
        # Get region config untuk menghitung maksimal scenario
        regional_config = st.session_state.kpi_calculator_config["regions"][wilayah]
        
        # SCENARIO 1: MAKSIMAL (110% Target)
        st.markdown("#### 🎯 SCENARIO 1: Maksimal Achievement (110% Target)")
        
        maksimal_achievement_total = {}
        for metric in regional_config.get("kpi_metrics", []):
            metric_name = metric["name"]
            target = metric["target"]
            maksimal_achievement_total[metric_name] = {"target": target, "actual": int(target * 1.1)}
        
        maksimal_achievement_total.update({
            "tertiary_inner_percentage": 0.55,
            "ach_rgu_ga": 0.85,
            "growth_prepaid_revenue": 0.05
        })
        
        result_maksimal_total = calculate_metrics(regional_config, maksimal_achievement_total)
        final_fee_maksimal = result_maksimal_total["final_fee"]
        total_tactical_income_maksimal = st.session_state.get("total_tactical_income", 0)
        total_income_maksimal = final_fee_maksimal + total_income_fix + total_tactical_income_maksimal
        
        maks_cols = st.columns(4)
        with maks_cols[0]:
            st.metric("Final Fee (Maksimal)", format_currency(final_fee_maksimal))
        with maks_cols[1]:
            st.metric("Fix Income", format_currency(total_income_fix))
        with maks_cols[2]:
            st.metric("Tactical Income", format_currency(total_tactical_income_maksimal))
        with maks_cols[3]:
            st.metric("TOTAL INCOME", format_currency(total_income_maksimal))
        
        st.success(f"✅ Maksimal = {format_currency(final_fee_maksimal)} + {format_currency(total_income_fix)} + {format_currency(total_tactical_income_maksimal)} = **{format_currency(total_income_maksimal)}**")
        
        # Store Maksimal values
        st.session_state.final_fee_maksimal = final_fee_maksimal
        st.session_state.total_income_maksimal = total_income_maksimal
        
        st.markdown("---")
        
        # SCENARIO 2: CUSTOM (dari Tab 1 Input Manual)
        st.markdown("#### 📊 SCENARIO 2: Custom Achievement (Input Manual dari Tab 1)")
        
        if st.session_state.get("calculator_achievement"):
            current_achievement_total = st.session_state.calculator_achievement.copy()
        else:
            current_achievement_total = {m["name"]: {"target": m["target"], "actual": 0} for m in regional_config.get("kpi_metrics", [])}
        
        result_custom_total = calculate_metrics(regional_config, current_achievement_total)
        final_fee_custom = result_custom_total["final_fee"]
        total_tactical_income_custom = st.session_state.get("total_tactical_income", 0)
        total_income_custom = final_fee_custom + total_income_fix + total_tactical_income_custom
        
        custom_cols = st.columns(4)
        with custom_cols[0]:
            st.metric("Final Fee (Custom)", format_currency(final_fee_custom))
        with custom_cols[1]:
            st.metric("Fix Income", format_currency(total_income_fix))
        with custom_cols[2]:
            st.metric("Tactical Income", format_currency(total_tactical_income_custom))
        with custom_cols[3]:
            st.metric("TOTAL INCOME", format_currency(total_income_custom))
        
        if total_income_custom > 0:
            st.info(f"📌 Custom = {format_currency(final_fee_custom)} + {format_currency(total_income_fix)} + {format_currency(total_tactical_income_custom)} = **{format_currency(total_income_custom)}**")
        else:
            st.warning("⚠️ Silakan isi Tab 1 (SLA/KPI Insentif), Tab 2 (Fix Income), dan Tab 3 (Tactical Income) terlebih dahulu")
        
        # Store Custom values
        st.session_state.final_fee_custom = final_fee_custom
        st.session_state.total_income_custom = total_income_custom
        
        if total_income_custom > 0:
            st.info(f"📌 Custom = Rp {final_fee_custom:,.0f} + Rp {total_income_fix:,.0f} = **Rp {total_income_custom:,.0f}**")
        else:
            st.warning("⚠️ Silakan isi Tab 1 (SLA/KPI Insentif) dan Tab 2 (Fix Income) terlebih dahulu")
        
        # Store Custom values
        st.session_state.final_fee_custom = final_fee_custom
        st.session_state.total_income_custom = total_income_custom
        
        st.markdown("---")
        
        # PERBANDINGAN
        st.markdown("#### 🔄 Perbandingan Dua Skenario")
        perbandingan_cols = st.columns(2)
        with perbandingan_cols[0]:
            st.markdown(f"""
            **Maksimal (110%)**
            - Final Fee: Rp {final_fee_maksimal:,.0f}
            - Total Income Fix: Rp {total_income_fix:,.0f}
            - **Total Income: Rp {total_income_maksimal:,.0f}**
            """)
        with perbandingan_cols[1]:
            st.markdown(f"""
            **Custom (Input Manual)**
            - Final Fee: Rp {final_fee_custom:,.0f}
            - Total Income Fix: Rp {total_income_fix:,.0f}
            - **Total Income: Rp {total_income_custom:,.0f}**
            """)
        
        # Selisih
        selisih = total_income_maksimal - total_income_custom
        if selisih > 0:
            st.success(f"✅ Maksimal lebih menguntungkan **Rp {selisih:,.0f}**")
        elif selisih < 0:
            st.success(f"✅ Custom lebih menguntungkan **Rp {abs(selisih):,.0f}**")
        else:
            st.info("ℹ️ Kedua skenario memiliki nilai yang sama")
    
    # ==========================================
    # TAB 6: BIAYA TAMBAHAN + STRATEGI
    # ==========================================
    with tab_biaya:
        st.markdown("### ⚡ Biaya Tambahan + Strategi")
        st.info("💰 Setup cost per unit untuk setiap KPI dalam achieve target")
        
        # Get Total Income dari Tab 3 (Total Income) - baik Maksimal maupun Custom
        total_income_maksimal_biaya = st.session_state.get("total_income_maksimal", 0)
        total_income_custom_biaya = st.session_state.get("total_income_custom", 0)
        final_fee_maksimal_biaya = st.session_state.get("final_fee_maksimal", 0)
        final_fee_custom_biaya = st.session_state.get("final_fee_custom", 0)
        
        # Display Total Income dari tab_total - Dua Skenario
        st.markdown("#### 📊 Total Income (dari Tab 3)")
        
        income_scenario_cols = st.columns(2)
        with income_scenario_cols[0]:
            st.markdown("**Maksimal (110% Target)**")
            st.metric("Total Income", format_idr_jt(total_income_maksimal_biaya))
        with income_scenario_cols[1]:
            st.markdown("**Custom (Input Manual)**")
            st.metric("Total Income", format_idr_jt(total_income_custom_biaya))
        
        if total_income_maksimal_biaya == 0 and total_income_custom_biaya == 0:
            st.warning("⚠️ Silakan isi Tab 1 (SLA/KPI Insentif), Tab 2 (Fix Income), dan Tab 3 (Total Income) terlebih dahulu")
        
        st.divider()
        
        # Get region config dari session state
        regional_config = st.session_state.kpi_calculator_config["regions"][wilayah]
        
        # Ambil data custom dari session state jika ada (untuk digunakan di berbagai section)
        if "calculator_achievement" in st.session_state and st.session_state.calculator_achievement:
            current_achievement_compare = st.session_state.calculator_achievement.copy()
        else:
            # Gunakan default achievement jika belum ada input dari Tab 1
            current_achievement_compare = {
                "Trade Supply": {"target": 1000, "actual": 850},
                "M2S Absolute": {"target": 500, "actual": 425},
                "RGU GA FWA": {"target": 200, "actual": 160},
                "tertiary_inner_percentage": 0.45,
                "ach_rgu_ga": 0.82,
                "growth_prepaid_revenue": 0.05
            }
        
        # =======================================
        # CRITICAL COMPLIANCE CHECK: RGU GA
        # =======================================
        st.markdown("#### 🚨 CRITICAL COMPLIANCE CHECK - RGU GA FWA (Minimum: 80%)")
        
        # Get RGU GA value dari current achievement
        rgu_ga_current_custom = current_achievement_compare.get("ach_rgu_ga", 0.82)
        rgu_ga_threshold = 0.80
        
        # Get RGU GA dari maksimal scenario
        rgu_ga_maksimal = 0.85
        
        st.markdown("**📊 RGU GA Compliance Status:**")
        rgu_cols = st.columns(2)
        
        with rgu_cols[0]:
            st.markdown("**Scenario Custom (Input Manual):**")
            rgu_ga_pct_custom = rgu_ga_current_custom * 100
            
            if rgu_ga_current_custom >= rgu_ga_threshold:
                st.success(f"✅ SAFE - RGU GA: {rgu_ga_pct_custom:.1f}% (≥ 80% threshold)")
                compliance_status_custom = "SAFE"
                compliance_color_custom = "green"
            else:
                st.error(f"🔴 CRITICAL - RGU GA: {rgu_ga_pct_custom:.1f}% (< 80% threshold)")
                st.markdown(f"**⚠️ JIKA RGU GA < 80%, TIDAK AKAN MENDAPAT INSENTIF SAMA SEKALI (Final Fee = Rp 0)**")
                compliance_status_custom = "CRITICAL"
                compliance_color_custom = "red"
        
        with rgu_cols[1]:
            st.markdown("**Scenario Maksimal (110% Target):**")
            rgu_ga_pct_maksimal = rgu_ga_maksimal * 100
            
            if rgu_ga_maksimal >= rgu_ga_threshold:
                st.success(f"✅ SAFE - RGU GA: {rgu_ga_pct_maksimal:.1f}% (≥ 80% threshold)")
                compliance_status_maksimal = "SAFE"
            else:
                st.error(f"🔴 CRITICAL - RGU GA: {rgu_ga_pct_maksimal:.1f}% (< 80% threshold)")
                compliance_status_maksimal = "CRITICAL"
        
        st.divider()
        
        # Jika custom scenario RGU GA critical, tambahkan option untuk push ke 80%
        if compliance_status_custom == "CRITICAL":
            st.markdown("**💼 RGU GA Push Option - Untuk memenuhi 80% threshold:**")
            
            shortage_rgu_ga = max(0, rgu_ga_threshold - rgu_ga_current_custom)
            
            # Asumsi cost untuk push RGU GA (misalnya per 1% RGU GA)
            # Bisa di-customize berdasarkan internal policy
            cost_per_rgu_ga_1pct = st.number_input(
                "Cost untuk push RGU GA per 1% (bisa di-adjust)",
                value=500_000_000,
                min_value=0,
                step=50_000_000,
                key=f"rgu_ga_cost_{wilayah}"
            )
            
            cost_rgu_ga_push = shortage_rgu_ga * cost_per_rgu_ga_1pct * 100  # shortage in percentage, convert to basis point
            
            st.warning(f"""
            **Untuk push RGU GA dari {rgu_ga_pct_custom:.1f}% ke 80%:**
            - Shortfall: {shortage_rgu_ga*100:.2f}%
            - Estimated Cost: Rp {cost_rgu_ga_push:,.0f}
            - **Benefit: Dapat insentif (bukan Rp 0)**
            
            **SANGAT DISARANKAN UNTUK PUSH RGU GA** karena:
            1. Jika tidak push: Final Fee = Rp 0 (RUGI TOTAL)
            2. Jika push: Setidaknya bisa dapat insentif dari Tab 1 & 2
            """)
            
            # Store RGU GA push cost
            st.session_state.rgu_ga_push_cost = cost_rgu_ga_push
            st.session_state.rgu_ga_critical = True
        else:
            st.session_state.rgu_ga_push_cost = 0
            st.session_state.rgu_ga_critical = False
        
        st.markdown("---")
        
        st.markdown("#### 📋 Setup Biaya per Unit KPI")
        st.markdown(f"**Region: {wilayah}**")
        st.caption("Biaya akan dihitung saat ACTUAL < TARGET (untuk fulfill shortfall)")
        
        # Create form untuk input cost per unit
        cost_cols = st.columns(len(regional_config.get("kpi_metrics", [])))
        for idx, metric in enumerate(regional_config.get("kpi_metrics", [])):
            with cost_cols[idx]:
                metric_name = metric["name"]
                current_cost = metric.get("cost_per_unit", 0)
                
                # Tambahkan label deskriptif sesuai tipe KPI
                if metric_name == "Trade Supply":
                    label_desc = "Pembelian Saldo\n(Pra Produk Pulsa/Data)\nCost/Unit"
                elif metric_name == "M2S Absolute":
                    label_desc = "Harga per Picis\nCost/Unit"
                else:
                    label_desc = f"{metric_name}\nCost/Unit"
                
                new_cost = st.number_input(
                    label_desc,
                    value=int(current_cost),
                    min_value=0,
                    step=50000,
                    key=f"cost_per_unit_{wilayah}_{idx}"
                )
                
                # Update config
                if new_cost != current_cost:
                    st.session_state.kpi_calculator_config["regions"][wilayah]["kpi_metrics"][idx]["cost_per_unit"] = new_cost
        
        st.markdown("---")
        
        st.markdown("#### 🎯 Perbandingan Strategi: Total Income vs Biaya")
        
        # Scenario 1: Maksimal (110%)
        st.markdown("**SCENARIO 1: Skenario Maksimal (110% Target) - SEMUA TARGET SUDAH TERCAPAI**")
        st.info("✅ Pada skenario ini, semua KPI mencapai 110% dari target, sehingga tidak ada biaya tambahan yang diperlukan")
        
        maksimal_achievement_compare = {}
        for metric in regional_config.get("kpi_metrics", []):
            metric_name = metric["name"]
            target = metric["target"]
            maksimal_achievement_compare[metric_name] = {"target": target, "actual": int(target * 1.1)}
        
        maksimal_achievement_compare.update({
            "tertiary_inner_percentage": 0.55,
            "ach_rgu_ga": 0.85,
            "growth_prepaid_revenue": 0.05
        })
        
        # Gunakan Total Income dari Tab 3 (Maksimal)
        total_income_maksimal_biaya = st.session_state.get("total_income_maksimal", 0)
        cost_maksimal = calculate_cost_shortfall(regional_config, maksimal_achievement_compare)
        net_maksimal = total_income_maksimal_biaya - cost_maksimal["total_cost"]
        
        # Tampilkan achievement data Maksimal
        st.markdown("**📊 Achievement Data (Skenario Maksimal):**")
        maks_achievement_cols = st.columns(len(regional_config.get("kpi_metrics", [])))
        for idx, metric in enumerate(regional_config.get("kpi_metrics", [])):
            metric_name = metric["name"]
            target = metric["target"]
            actual = int(target * 1.1)
            
            with maks_achievement_cols[idx]:
                st.markdown(f"""
                **{metric_name}**
                - Target: {target}
                - Actual: {actual}
                - Status: ✅ Tercapai (110%)
                """)
        
        st.markdown("---")
        
        # Cost calculation untuk Maksimal
        st.markdown("**💰 Cost Calculation (Skenario Maksimal):**")
        maks_cost_cols = st.columns(3)
        with maks_cost_cols[0]:
            st.metric("Total Income", format_idr_jt(total_income_maksimal_biaya))
        with maks_cost_cols[1]:
            st.metric("Total Cost (0 - Semua Tercapai)", format_idr_jt(cost_maksimal["total_cost"]))
        with maks_cost_cols[2]:
            st.metric("Net Profit = Income - Cost", format_idr_jt(net_maksimal))
        
        st.success(f"✅ Karena semua target tercapai (110%), Net Profit = Total Income = **Rp {net_maksimal:,.0f}**")
        
        st.markdown("---")
        
        # Scenario 2: Current Custom (dari Tab 1 - Skenario Custom Input)
        st.markdown("**SCENARIO 2: Skenario Custom (Input Manual) - KONDISI SESUAI ACHIEVEMENT ACTUAL**")
        st.info("⚠️ Pada skenario ini, achievement actual mengikuti input di Tab 1. Jika ada KPI yang ACTUAL < TARGET, maka diperlukan biaya untuk fulfill shortfall agar target tercapai")
        
        # current_achievement_compare sudah didefinisikan di awal section Biaya + Strategi
        
        # Gunakan Total Income dari Tab 3 (Custom)
        total_income_custom_biaya = st.session_state.get("total_income_custom", 0)
        cost_custom = calculate_cost_shortfall(regional_config, current_achievement_compare)
        net_custom = total_income_custom_biaya - cost_custom["total_cost"]
        
        # Tampilkan achievement data Custom dengan status
        st.markdown("**📊 Achievement Data (Skenario Custom):**")
        recap_cols = st.columns(len(regional_config.get("kpi_metrics", [])))
        for idx, metric in enumerate(regional_config.get("kpi_metrics", [])):
            metric_name = metric["name"]
            achievement_data = current_achievement_compare.get(metric_name, {"target": metric["target"], "actual": 0})
            actual = achievement_data.get("actual", 0) if isinstance(achievement_data, dict) else achievement_data
            target = achievement_data.get("target", metric["target"]) if isinstance(achievement_data, dict) else metric["target"]
            
            # Hitung shortfall untuk menampilkan status
            shortfall = max(0, target - actual)
            status_text = f"✅ Tercapai" if actual >= target else f"⚠️ Shortfall: {shortfall}"
            status_color = "green" if actual >= target else "orange"
            
            with recap_cols[idx]:
                st.markdown(f"""
                **{metric_name}**
                - Target: {target}
                - Actual: {actual}
                - Status: {status_text}
                """)
        
        st.markdown("---")
        
        # Cost calculation untuk Custom
        st.markdown("**💰 Cost Calculation (Skenario Custom):**")
        st.markdown("Rumus: **Jika Actual < Target** → Cost = (Target - Actual) × Cost/Unit")
        st.markdown("        **Jika Actual ≥ Target** → Cost = 0 (Tidak perlu biaya tambahan)")
        
        # Add RGU GA push cost jika critical
        rgu_ga_push_cost = st.session_state.get("rgu_ga_push_cost", 0)
        rgu_ga_critical = st.session_state.get("rgu_ga_critical", False)
        
        total_cost_custom_with_rgu = cost_custom["total_cost"] + rgu_ga_push_cost
        net_custom_with_rgu = total_income_custom_biaya - total_cost_custom_with_rgu
        
        custom_cost_cols = st.columns(3)
        with custom_cost_cols[0]:
            st.metric("Total Income", format_idr_jt(total_income_custom_biaya))
        with custom_cost_cols[1]:
            cost_display = f"Rp {cost_custom['total_cost']:,.0f}"
            if rgu_ga_critical:
                cost_display += f"\n+ RGU GA Push: Rp {rgu_ga_push_cost:,.0f}\n= Rp {total_cost_custom_with_rgu:,.0f}"
            st.metric("Total Cost", cost_display)
        with custom_cost_cols[2]:
            profit_display = format_idr_jt(net_custom_with_rgu if rgu_ga_critical else net_custom)
            st.metric("Net Profit = Income - Cost", profit_display)
        
        if rgu_ga_critical:
            st.error(f"""
            🔴 **RGU GA CRITICAL - BIAYA PUSH PRIORITAS:**
            - KPI Shortfall Cost: Rp {cost_custom['total_cost']:,.0f}
            - RGU GA Push Cost: Rp {rgu_ga_push_cost:,.0f}
            - **TOTAL COST: Rp {total_cost_custom_with_rgu:,.0f}**
            - **NET PROFIT AFTER PUSH: Rp {net_custom_with_rgu:,.0f}**
            
            **REKOMENDASI: Harus push RGU GA sampai 80%+ agar tidak kehilangan semua insentif!**
            """)
        elif cost_custom["total_cost"] > 0:
            st.warning(f"⚠️ Ada shortfall yang memerlukan biaya **Rp {cost_custom['total_cost']:,.0f}** untuk memenuhi target dan mendapatkan profit maksimal")
            
            # Detail breakdown biaya Custom
            with st.expander("📋 Detail Perhitungan Biaya per KPI"):
                for kpi_name, breakdown in cost_custom["breakdown"].items():
                    if breakdown['shortfall'] > 0:
                        st.write(f"**{kpi_name}** ⚠️ ADA SHORTFALL")
                        st.write(f"  • Target: {breakdown['target']} | Actual: {breakdown['actual']} | Shortfall: {breakdown['shortfall']} unit")
                        
                        # Tampilkan rumus berbeda berdasarkan jenis KPI
                        if kpi_name == "Trade Supply":
                            st.write(f"  • Rumus: Cost = Cost Per Unit (langsung, tanpa × Shortfall)")
                            st.write(f"  • Perhitungan: {format_idr_jt(breakdown['cost_per_unit'])}")
                        else:
                            st.write(f"  • Rumus: (Target - Actual) × Cost Per Unit = ({breakdown['target']} - {breakdown['actual']}) × {format_idr_jt(breakdown['cost_per_unit'])}")
                        
                        st.write(f"  • **Biaya yang diperlukan: Rp {breakdown['total_cost']:,.0f}**")
                    else:
                        st.write(f"**{kpi_name}** ✅ SUDAH TERCAPAI")
                        st.write(f"  • Target: {breakdown['target']} | Actual: {breakdown['actual']}")
                        st.write(f"  • Biaya: Rp 0 (tidak perlu biaya tambahan)")
        else:
            st.success(f"✅ Semua target sudah tercapai! Tidak ada biaya tambahan. Net Profit = **Rp {net_custom:,.0f}**")
        
        st.markdown("---")
        
        st.markdown("#### � Summary & Rekomendasi Strategi")
        st.markdown("Bandingkan kedua skenario untuk memilih strategi yang paling menguntungkan:")
        
        summary_cols = st.columns(2)
        with summary_cols[0]:
            st.markdown(f"""
            ### 🎯 MAKSIMAL (110% Target)
            **Status:** Semua target sudah tercapai
            
            - **Total Income:** Rp {total_income_maksimal_biaya:,.0f}
            - **Biaya Tambahan:** Rp {cost_maksimal['total_cost']:,.0f}
            - **Net Profit:** **Rp {net_maksimal:,.0f}**
            """)
        
        with summary_cols[1]:
            st.markdown(f"""
            ### 📋 CUSTOM (Input Manual)
            **Status:** {'Ada Shortfall' if cost_custom['total_cost'] > 0 else 'Semua Tercapai'}
            
            - **Total Income:** Rp {total_income_custom_biaya:,.0f}
            - **Biaya Tambahan:** Rp {cost_custom['total_cost']:,.0f}
            - **Net Profit:** **Rp {net_custom:,.0f}**
            """)
        
        st.divider()
        
        # =======================================
        # AI STRATEGY RECOMMENDATIONS
        # =======================================
        st.markdown("### 🤖 AI Strategy Recommendations - Optimasi Profit Maksimal")
        
        # Define minimum safe threshold (70% dari target = minimum multiplier masih mendapat value)
        MINIMUM_SAFE_THRESHOLD = 0.70
        SAFE_THRESHOLD_RANGE = (0.70, 1.00)  # 70% - 100% dianggap SAFE
        
        # Analisis setiap KPI untuk Custom scenario
        st.markdown("#### 📊 Analisis per KPI (Skenario Custom)")
        
        kpi_analysis = []
        for metric in regional_config.get("kpi_metrics", []):
            metric_name = metric["name"]
            target = metric["target"]
            cost_per_unit = metric.get("cost_per_unit", 0)
            
            # Get actual dari custom achievement
            achievement_data = current_achievement_compare.get(metric_name, {"target": target, "actual": 0})
            actual = achievement_data.get("actual", 0) if isinstance(achievement_data, dict) else achievement_data
            
            # Calculate percentages
            achievement_pct = (actual / target * 100) if target > 0 else 0
            minimum_safe = int(target * MINIMUM_SAFE_THRESHOLD)
            
            # Calculate shortfall and cost
            shortfall = max(0, target - actual)
            
            # RUMUS BERBEDA PER KPI (sama seperti di calculate_cost_shortfall)
            if metric_name == "Trade Supply":
                # Trade Supply: Cost = Cost Per Unit langsung (tanpa × Shortfall)
                cost_to_achieve = cost_per_unit if shortfall > 0 else 0
            else:
                # M2S Absolute & RGU GA FWA: Cost = Shortfall × Cost Per Unit
                cost_to_achieve = shortfall * cost_per_unit
            
            # Determine status
            if actual >= target:
                status = "✅ ACHIEVED"
                status_desc = "Target SUDAH tercapai"
                action = "MAINTAIN"
            elif actual >= minimum_safe:
                status = "🟢 SAFE"
                status_desc = f"Aman (di atas minimum {MINIMUM_SAFE_THRESHOLD*100:.0f}%)"
                action = "OPTIONAL"
            else:
                status = "🔴 CRITICAL"
                status_desc = "Di bawah minimum safe"
                action = "PUSH"
            
            # Calculate ROI (hanya untuk yang belum achieve)
            roi_benefit = 0
            if actual < target:
                # Hitung actual Final Fee increase jika KPI ini dicapai ke target
                potential_income_gain = calculate_income_gain_from_kpi_improvement(
                    regional_config, 
                    current_achievement_compare, 
                    metric_name
                )
                roi = (potential_income_gain - cost_to_achieve) if cost_to_achieve > 0 else potential_income_gain
            else:
                roi = 0
                potential_income_gain = 0
            
            kpi_analysis.append({
                "name": metric_name,
                "target": target,
                "actual": actual,
                "achievement_pct": achievement_pct,
                "minimum_safe": minimum_safe,
                "status": status,
                "status_desc": status_desc,
                "action": action,
                "shortfall": shortfall,
                "cost_per_unit": cost_per_unit,
                "cost_to_achieve": cost_to_achieve,
                "potential_income_gain": potential_income_gain,
                "roi": roi
            })
        
        # Display KPI Analysis dengan rekomendasi
        analysis_cols = st.columns(len(kpi_analysis))
        for idx, kpi in enumerate(kpi_analysis):
            with analysis_cols[idx]:
                st.markdown(f"**{kpi['name']}**")
                st.markdown(f"{kpi['status']} {kpi['status_desc']}")
                st.markdown(f"")
                st.metric("Achievement", f"{kpi['achievement_pct']:.1f}%", f"(Target: {kpi['target']})")
                st.metric("Actual", f"{kpi['actual']}")
                
                if kpi['action'] == 'MAINTAIN':
                    st.info(f"✅ Maintain saja - sudah tercapai")
                elif kpi['action'] == 'OPTIONAL':
                    st.warning(f"📌 Push jika budget tersedia\nRoi: Rp {kpi['roi']:,.0f}")
                else:  # PUSH
                    st.error(f"⚠️ HARUS Push!\nCost: Rp {kpi['cost_to_achieve']:,.0f}\nROI: Rp {kpi['roi']:,.0f}")
        
        st.divider()
        
        # =======================================
        # SMART RECOMMENDATION ENGINE
        # =======================================
        st.markdown("#### 🎯 Smart Recommendation - Strategi Optimal")
        st.markdown("_Berdasarkan kalkulasi actual Final Fee impact dari setiap KPI improvement_")
        
        # Kategori KPI yang harus push vs bisa maintain
        critical_kpis = [k for k in kpi_analysis if k['action'] == 'PUSH']
        optional_kpis = [k for k in kpi_analysis if k['action'] == 'OPTIONAL']
        achieved_kpis = [k for k in kpi_analysis if k['action'] == 'MAINTAIN']
        
        if critical_kpis:
            st.error("🔴 **KPI KRITIS - HARUS SEGERA DIPUSH!**")
            for kpi in critical_kpis:
                st.markdown(f"""
**⚠️ {kpi['name']}**

**📊 Status Darurat:**
- Pencapaian: **{kpi['achievement_pct']:.1f}%** (⚠️ KRITIS! Di bawah 70% = minimum safe)
- Target: **{kpi['target']} unit** | Yang tercapai: **{kpi['actual']} unit** | Masih kurang: **{kpi['shortfall']} unit**

**💸 Untuk Capai Target:**
- Biaya yang diperlukan: **Rp {kpi['cost_to_achieve']:,.0f}**
- Income yang bakal nambah: **Rp {kpi['potential_income_gain']:,.0f}**
- **Profit setelah push: ✅ Rp {kpi['roi']:,.0f}**

**🚨 ACTION PLAN:**
✅ **PUSH KPI INI ADALAH PRIORITAS!** Tidak ada pilihan lain
- Jika tidak dipush, KPI akan terus jatuh dan merugikan profit keseluruhan
- Dengan push, akan dapat kembali ke zona aman dan nambah income
""")

        
        if optional_kpis:
            st.info("🟢 **KPI AMAN - BOLEH MAINTAIN ATAU PUSH TERGANTUNG BUDGET:**")
            for kpi in optional_kpis:
                roi_status = "💰 MENGUNTUNGKAN" if kpi['roi'] > 0 else "⚠️ RUGI"
                roi_emoji = "✅" if kpi['roi'] > 0 else "❌"
                
                st.markdown(f"""
**🎯 {kpi['name']}**

**📊 Kondisi Saat Ini:**
- Pencapaian: **{kpi['achievement_pct']:.1f}%** (Aman! Sudah melampaui batas minimum 70%)
- Target: **{kpi['target']} unit** | Yang tercapai: **{kpi['actual']} unit** | Masih kurang: **{kpi['shortfall']} unit**

**💸 Jika Di-Push ke Target Penuh:**
- Biaya yang diperlukan: **Rp {kpi['cost_to_achieve']:,.0f}**
- Bonus income yang masuk: **Rp {kpi['potential_income_gain']:,.0f}**
- **Selisih (Profit/Rugi): {roi_emoji} Rp {kpi['roi']:,.0f}** → {roi_status}

**💡 Rekomendasi:**
""")
                
                if kpi['roi'] > 0:
                    st.success(f"""
✅ **WORTH IT UNTUK PUSH!** 
- Jika ada budget Rp {kpi['cost_to_achieve']:,.0f}, push KPI ini akan nambah profit Rp {kpi['roi']:,.0f}
- Ini bagus untuk growth, tidak akan rugi
""")
                else:
                    st.warning(f"""
⚠️ **LEBIH BAIK JANGAN PUSH (ROI Negatif)**
- Push KPI ini butuh Rp {kpi['cost_to_achieve']:,.0f} tapi hanya dapat Rp {kpi['potential_income_gain']:,.0f}
- Akan rugi Rp {abs(kpi['roi']):,.0f}
- Lebih baik pakai budget untuk hal lain yang lebih menguntungkan
""")
        
        if achieved_kpis:
            st.success(f"✅ **KPI TERCAPAI - BAGUS! MAINTAIN SAJA:**")
            for kpi in achieved_kpis:
                st.markdown(f"- **{kpi['name']}:** {kpi['achievement_pct']:.1f}% ✅ Sudah capai target. Tidak perlu biaya tambahan, terus dipertahankan")
        
        st.divider()
        
        # =======================================
        # FINAL STRATEGY RECOMMENDATION
        # =======================================
        st.markdown("#### 📋 REKOMENDASI AKHIR - STRATEGI TERBAIK UNTUK ANDA")
        
        # Calculate total cost if push semua critical
        total_critical_cost = sum(k['cost_to_achieve'] for k in critical_kpis)
        total_critical_income_gain = sum(k['potential_income_gain'] for k in critical_kpis)
        total_critical_roi = total_critical_income_gain - total_critical_cost
        
        # Add RGU GA to total cost if critical
        if rgu_ga_critical:
            total_critical_cost += rgu_ga_push_cost
            total_critical_roi -= rgu_ga_push_cost
        
        # Generate recommendation text
        if rgu_ga_critical:
            # RGU GA critical adalah prioritas TERTINGGI
            recommendation = f"""
🔴 **SITUASI DARURAT - HARUS SEGERA ACTION!**

**❌ MASALAH BESAR:** RGU GA Compliance Kamu KRITIS!

Jika RGU GA tidak dipush ke 80%+:
- **Semua insentif hangus = Profit menjadi Rp 0**
- Berarti semua effort kamu sia-sia tidak dapat apa-apa!

---

**✅ SOLUSI (Action Plan):**

**STEP 1 - EMERGENCY PRIORITY (HARUS DIKERJAKAN DULUAN):**
Push RGU GA ke 80%+
- Biaya yang diperlukan: **Rp {rgu_ga_push_cost:,.0f}**
- Benefit: Dapat kembali menerima insentif (tidak jadi Rp 0)
- Status: **TIDAK ADA PILIHAN LAIN** - Ini mandatory!

**STEP 2 - AFTER RGU GA AMAN (Jika Budget Masih Ada):**
Push KPI yang masih critical lainnya
- Total biaya tambahan: **Rp {sum(k['cost_to_achieve'] for k in critical_kpis):,.0f}**
- Potential income tambahan: **Rp {total_critical_income_gain:,.0f}**

---

**📊 HASIL AKHIR JIKA SEMUA DIKERJAKAN:**
- Total investment: **Rp {total_critical_cost:,.0f}**
- Profit yang didapat: **Rp {net_custom_with_rgu:,.0f}**
"""
            st.error(recommendation)
        
        elif not critical_kpis:
            # Check if profit is positive or negative
            current_profit = net_custom_with_rgu if rgu_ga_critical else net_custom
            
            if current_profit > 0:
                recommendation = f"""
✅ **SITUASI BAIK - SEMUA KPI AMAN & PROFIT POSITIF**

Semua KPI kamu sudah di atas 70% (safe zone) dan profit dalam kondisi positif.
- Status sekarang: **AMAN & HEALTHY ✅**
- Profit yang sudah terjamin: **Rp {current_profit:,.0f}**

---

**PILIH SATU STRATEGI:**

**OPSI 1 - MAINTAIN (SAFE - Tanpa Resiko)**
✅ Pertahankan kondisi sekarang, jangan push apapun
✅ Profit sudah terjamin: Rp {current_profit:,.0f}
✅ Risk level: RENDAH
⏱️ Waktu: Bisa focus di hal lain

**OPSI 2 - PUSH GROWTH (AGGRESSIVE - Medium Risk)**
Jika masih ada budget, push KPI yang ROI-nya positif untuk nambah profit
"""
                if optional_kpis:
                    best_optional = max(optional_kpis, key=lambda x: x['roi'])
                    recommendation += f"""
💡 **Rekomendasi:** {best_optional['name']} adalah pilihan terbaik
- Biaya: Rp {best_optional['cost_to_achieve']:,.0f}
- Yang bakal didapat: Rp {best_optional['potential_income_gain']:,.0f}
- Profit nambah: Rp {best_optional['roi']:,.0f} ✅
- Risk: MEDIUM (tapi ROI positif, jadi okay)
"""
                
                st.success(recommendation)
            
            else:
                # Profit negatif/minus - ini bukan situasi aman!
                recommendation = f"""
⚠️ **SITUASI PERLU PERHATIAN - KPI AMAN TAPI PROFIT MASIH MINUS!**

Meskipun semua KPI di atas 70% (safe), profit kamu masih MINUS (negatif).
- Status KPI: AMAN (≥70%) ✅
- Status Profit: **MINUS - Rp {abs(current_profit):,.0f}** ❌

Ini artinya: Biaya operasional lebih besar dari income yang masuk!

---

**ACTION YANG DIPERLUKAN:**

**OPSI 1 - PUSH GROWTH (Recommended)**
Kamu perlu push KPI untuk nambah income agar profit jadi positif.
"""
                if optional_kpis:
                    best_optional = max(optional_kpis, key=lambda x: x['roi'])
                    if best_optional['roi'] > 0:
                        recommendation += f"""
💡 **Mulai dari sini:** {best_optional['name']} (ROI positif)
- Biaya: Rp {best_optional['cost_to_achieve']:,.0f}
- Income nambah: Rp {best_optional['potential_income_gain']:,.0f}
- Profit berubah dari minus Rp {abs(current_profit):,.0f} → positif Rp {best_optional['roi']:,.0f}
✅ Ini adalah path yang benar untuk break-even
"""
                
                recommendation += f"""

**OPSI 2 - TARGET MAKSIMAL (110%)**
Jika ingin langsung untung banyak, push semua KPI ke 110% target.
- Estimated profit: **Rp {net_maksimal:,.0f}** (dari minus jadi positif Rp {net_maksimal - current_profit:,.0f}!)
- Risk: MEDIUM (perlu invest dan effort lebih)
"""
                st.warning(recommendation)
        else:
            total_profit_after_push = (total_income_custom_biaya + total_critical_income_gain) - (cost_custom['total_cost'] + total_critical_cost)
            
            recommendation = f"""
⚠️ **SITUASI MEMBUTUHKAN ACTION - ADA KPI YANG JATUH!**

Ada {len(critical_kpis)} KPI yang masih di bawah 70% (critical zone).
Jika tidak dipush, KPI akan terus drop dan profit akan berkurang.

---

**✅ REKOMENDASI: PUSH SEMUA CRITICAL KPI**

**Investasi yang diperlukan:**
- Total biaya untuk push semua: **Rp {total_critical_cost:,.0f}**

**Hasil yang didapat:**
- Income tambahan: **Rp {total_critical_income_gain:,.0f}**
- Profit setelah dikurangi cost: **Rp {total_critical_roi:,.0f}**

**Perbandingan:**
- Sebelum push: **Rp {net_custom:,.0f}**
- Sesudah push: **Rp {total_profit_after_push:,.0f}**
- Selisih: **Rp {total_profit_after_push - net_custom:,.0f}** (profit bertambah!)

"""
            
            if total_critical_roi > 0:
                recommendation += f"""**✅ WORTH IT! ROI-nya POSITIF.**
Push semua critical KPI akan nambah profit kamu, bukan rugi!"""
            else:
                recommendation += f"""**⚠️ Hati-hati! ROI-nya NEGATIF.**
Jika push, profit akan berkurang. Pertimbangkan push sebagian saja atau prioritaskan yang ROI-nya positif."""
            
            st.warning(recommendation)
        
        st.divider()
        
        # Additional insights
        st.markdown("#### 💡 TIPS TAMBAHAN UNTUK ANDA")
        insights = []
        
        if net_maksimal > net_custom:
            profit_diff = net_maksimal - net_custom
            insights.append(f"""
🎯 **CEILING POTENTIAL:**
Jika kamu push ke 110% target (maksimal), profit bisa naik **Rp {profit_diff:,.0f}**!
- Kondisi sekarang: Rp {net_custom:,.0f}
- Jika semua sempurna (110%): Rp {net_maksimal:,.0f}
💡 Ini adalah target ideal jika budget & resource memungkinkan.
""")
        
        if optional_kpis:
            best_optional = max(optional_kpis, key=lambda x: x['roi'])
            if best_optional['roi'] > 0:
                insights.append(f"""
💰 **QUICK WIN - ROI POSITIF!**
KPI '{best_optional['name']}' adalah peluang terbaik untuk growth:
- Butuh investment: Rp {best_optional['cost_to_achieve']:,.0f}
- Profit yang masuk: Rp {best_optional['roi']:,.0f}
- Risk level: MEDIUM tapi WORTH IT
💡 Prioritaskan ini jika ada budget tersisa.
""")
        
        for kpi in optional_kpis:
            if kpi['roi'] < 0:
                insights.append(f"""
❌ **AVOID PUSHING - ROI NEGATIF!**
KPI '{kpi['name']}' malah akan mengurangi profit:
- Cost: Rp {kpi['cost_to_achieve']:,.0f}
- Income dapat: Rp {kpi['potential_income_gain']:,.0f}
- Rugi: Rp {abs(kpi['roi']):,.0f}
💡 Jangan push ini kecuali ada alasan khusus dari management.
""")
        
        if not insights:
            insights.append("""
✅ **STATUS HEALTHY!**
KPI kamu dalam kondisi baik, semua dalam kontrol. 
Terus monitor secara rutin dan adjust sesuai kondisi pasar/target yang berubah.
""")
        
        for insight in insights:
            st.info(insight)
    
    # ==========================================
    # EXPORT PDF SECTION (TAB AKHIR SAJA)
    # ==========================================
    st.markdown("---")
    st.markdown("### 📥 EXPORT KE PDF")
    st.info("📄 Klik tombol di bawah untuk mengekspor SEMUA hasil dari Tab 1 hingga akhir ke dalam satu file PDF yang rapi dan lengkap")
    
    if st.button("📄 EXPORT KE PDF", key="export_pdf_btn", use_container_width=True):
        try:
            with st.spinner("⏳ Sedang membuat PDF... Mohon tunggu..."):
                # Kumpulkan semua data dari session state
                export_data = {
                    "sla_scores": st.session_state.get("sla_scores", {}),
                    "fix_income_data": st.session_state.get("fix_income_data", {}),
                    "tactical_income_data": st.session_state.get("tactical_income_data", {}),
                    "total_income_maksimal": st.session_state.get("total_income_maksimal", 0),
                    "total_income_custom": st.session_state.get("total_income_custom", 0),
                    "final_fee_maksimal": st.session_state.get("final_fee_maksimal", 0),
                    "final_fee_custom": st.session_state.get("final_fee_custom", 0),
                    "calculator_achievement": st.session_state.get("calculator_achievement", {}),
                    "kpi_calculator_config": st.session_state.get("kpi_calculator_config", {}),
                    "cost_breakdown": st.session_state.get("cost_breakdown", {}),
                    "cost_maksimal": st.session_state.get("cost_maksimal", 0),
                    "cost_custom": st.session_state.get("cost_custom", 0)
                }
                
                # Generate PDF
                pdf_bytes = generate_pdf_report_comprehensive(wilayah, mitra, export_data)
            
            # Download button
            st.download_button(
                label="⬇️ Download PDF - Report Lengkap",
                data=pdf_bytes,
                file_name=f"IOH_Super_Report_{wilayah}_{dt.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                key="download_pdf"
            )
            st.success("✅ PDF berhasil dibuat! Klik tombol di atas untuk mengunduh file.")
            
        except Exception as e:
            st.error(f"❌ Error saat generate PDF: {str(e)}")

# ==========================================
# FOOTER SECTION (SELALU DI BAWAH)
# ==========================================
st.markdown("""
<div style="
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    text-align: center;
    padding: 15px 20px;
    color: #666;
    font-size: 12px;
    border-top: 1px solid #e0e0e0;
    background-color: #ffffff;
    z-index: 999;
    box-shadow: 0 -2px 10px rgba(0,0,0,0.05);
">
    <p style="margin: 0;">© 2026 IOH Partner System | Design by Friza&Rizka</p>
    <p style="margin: 3px 0 0 0; font-size: 11px; color: #999;">All rights reserved</p>
</div>
""", unsafe_allow_html=True)
