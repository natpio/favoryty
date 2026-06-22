import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Vorteza Links", page_icon="🔗", layout="wide", initial_sidebar_state="expanded")

# --- STYLE CSS ---
st.markdown("""
<style>
    h1, h2, h3 { color: #00D2FF; font-family: 'Segoe UI', Tahoma, sans-serif; }
    .link-card {
        background: linear-gradient(145deg, #1E212B, #171920);
        border-left: 4px solid #00D2FF;
        border-radius: 8px; padding: 16px; margin-bottom: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.4); transition: transform 0.2s, box-shadow 0.2s;
    }
    .link-card:hover { transform: translateY(-4px); box-shadow: 0 6px 15px rgba(0, 210, 255, 0.2); }
    .link-title { font-size: 1.15rem; font-weight: bold; color: #FFFFFF; margin-bottom: 6px; display: block; }
    .link-url { font-size: 0.8rem; color: #8C98A4; word-break: break-all; }
    .link-cat { font-size: 0.75rem; color: #00D2FF; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; display: block; }
    .btn-open {
        display: inline-block; margin-top: 12px; padding: 6px 14px;
        background-color: rgba(0, 210, 255, 0.1); color: #00D2FF !important;
        border: 1px solid #00D2FF; border-radius: 5px; text-decoration: none !important;
        font-size: 0.85rem; font-weight: bold; transition: 0.2s;
    }
    .btn-open:hover { background-color: #00D2FF; color: #12141A !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# ID TWOJEGO ARKUSZA GOOGLE
# ==========================================
SHEET_ID = "1Xc1OQVUdqzb3GZ8FnrXTm2_bw-duCEzpG23YN1GUy3c"

# --- POŁĄCZENIE Z ARKUSZEM GOOGLE ---
@st.cache_resource
def get_gspread_client():
    try:
        creds_json = st.secrets["GCP_CREDENTIALS"]
        creds_dict = json.loads(creds_json)
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        st.error("Błąd uwierzytelniania. Skonfiguruj poprawnie 'GCP_CREDENTIALS' w Streamlit Secrets.")
        st.stop()

def get_sheet():
    client = get_gspread_client()
    return client.open_by_key(SHEET_ID).sheet1

@st.cache_data(ttl=10)
def load_data():
    try:
        sheet = get_sheet()
        records = sheet.get_all_records()
        return pd.DataFrame(records)
    except Exception as e:
        return pd.DataFrame(columns=["Kategoria", "Nazwa", "URL"])

# --- FUNKCJE BAZODANOWE ---
def add_link(kategoria, nazwa, url):
    sheet = get_sheet()
    sheet.append_row([kategoria, nazwa, url])
    st.cache_data.clear()

def delete_link(pandas_index):
    sheet = get_sheet()
    sheet.delete_rows(pandas_index + 2)
    st.cache_data.clear()

# Ładowanie danych
df = load_data()

# --- PASEK BOCZNY ---
st.sidebar.title("Vorteza Systems")
st.sidebar.markdown("---")
menu = st.sidebar.radio("Zarządzanie:", ["🔍 Przegląd Linków", "➕ Dodaj Nowy", "🗑️ Usuń Linki"])

# --- WIDOK 1: PRZEGLĄD ---
if menu == "🔍 Przegląd Linków":
    st.title("🌌 Baza Zakładek")
    
    search = st.text_input("Wyszukaj:", placeholder="Wpisz słowo kluczowe...")
    st.markdown("<br>", unsafe_allow_html=True)
    
    if not df.empty:
        filtered_df = df.copy()
        if search:
            query = search.lower()
            mask = filtered_df.apply(lambda row: query in str(row.get('Kategoria', '')).lower() or 
                                                 query in str(row.get('Nazwa', '')).lower() or 
                                                 query in str(row.get('URL', '')).lower(), axis=1)
            filtered_df = filtered_df[mask]
        
        if filtered_df.empty:
            st.info("Brak wyników spełniających kryteria.")
        else:
            cols = st.columns(3)
            for idx, row in enumerate(filtered_df.itertuples()):
                with cols[idx % 3]:
                    st.markdown(f"""
                    <div class="link-card">
                        <span class="link-cat">📁 {getattr(row, 'Kategoria', 'Brak')}</span>
                        <span class="link-title">{getattr(row, 'Nazwa', 'Bez nazwy')}</span>
                        <span class="link-url">{str(getattr(row, 'URL', ''))[:40]}...</span><br>
                        <a href="{getattr(row, 'URL', '#')}" target="_blank" class="btn-open">Otwórz stronę 🚀</a>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.info("Baza danych jest pusta. Przejdź do zakładki 'Dodaj Nowy'.")

# --- WIDOK 2: DODAWANIE ---
elif menu == "➕ Dodaj Nowy":
    st.title("➕ Dodaj wpis do bazy")
    
    existing_categories = df['Kategoria'].unique().tolist() if not df.empty and 'Kategoria' in df.columns else []
    
    with st.form("add_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nazwa = st.text_input("Nazwa strony")
            url = st.text_input("Adres URL")
        with col2:
            nowa_kategoria = st.text_input("Nowa kategoria (wpisz tutaj)")
            wybrana_kategoria = st.selectbox("Lub wybierz z istniejących:", ["-- Wybierz --"] + existing_categories)
        
        submit = st.form_submit_button("Dodaj do Arkusza Google", use_container_width=True)
        
        if submit:
            kategoria_docelowa = nowa_kategoria if nowa_kategoria else (wybrana_kategoria if wybrana_kategoria != "-- Wybierz --" else "")
            
            if nazwa and url and kategoria_docelowa:
                if not url.startswith("http"): url = "https://" + url
                with st.spinner("Zapisywanie w bazie Arkuszy Google..."):
                    add_link(kategoria_docelowa, nazwa, url)
                st.success(f"Dodano '{nazwa}' do bazy!")
                st.rerun()
            else:
                st.warning("Wypełnij wszystkie pola (Nazwa, URL, Kategoria).")

# --- WIDOK 3: USUWANIE ---
elif menu == "🗑️ Usuń Linki":
    st.title("🗑️ Czyszczenie bazy")
    
    if df.empty or 'Kategoria' not in df.columns:
        st.info("Baza jest pusta.")
    else:
        categories = df['Kategoria'].unique().tolist()
        cat_to_edit = st.selectbox("Filtruj obszar do usunięcia:", categories)
        
        cat_df = df[df['Kategoria'] == cat_to_edit]
        
        for idx, row in cat_df.iterrows():
            c1, c2 = st.columns([5, 1])
            c1.markdown(f"**{row.get('Nazwa', 'Bez nazwy')}** <br> <small>{row.get('URL', '')}</small>", unsafe_allow_html=True)
            if c2.button("Usuń", key=f"del_{idx}"):
                with st.spinner("Usuwanie z Arkusza Google..."):
                    delete_link(idx)
                st.success("Trwale usunięto z bazy!")
                st.rerun()
