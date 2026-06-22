import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Terminal Logistyczny", page_icon="✈️", layout="wide", initial_sidebar_state="expanded")

# --- STYLE CSS (MOTYW LUFTHANSA + ZAKŁADKI) ---
st.markdown("""
<style>
    /* Globalne tło i czcionki */
    .stApp {
        background-color: #F4F5F7;
    }
    h1, h2, h3 { 
        color: #05164D !important; 
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; 
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    /* Pasek nawigacji u góry (Tabs) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background-color: #E2E6ED;
        padding: 8px 8px 0 8px;
        border-radius: 8px 8px 0 0;
        border-bottom: 3px solid #05164D;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        background-color: #FFFFFF;
        border-radius: 6px 6px 0 0;
        color: #05164D;
        font-weight: 600;
        padding: 10px 20px;
        border: 1px solid #D1D6E0;
        border-bottom: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: #05164D !important;
        color: #FFB000 !important;
        border: 1px solid #05164D;
    }
    
    /* Karty linków */
    .link-card {
        background-color: #FFFFFF;
        border-top: 4px solid #05164D;
        padding: 20px; 
        margin-bottom: 20px;
        box-shadow: 0 2px 5px rgba(5, 22, 77, 0.05); 
        transition: all 0.2s ease-in-out;
    }
    .link-card:hover { 
        transform: translateY(-2px); 
        box-shadow: 0 8px 15px rgba(5, 22, 77, 0.1); 
        border-top: 4px solid #FFB000;
    }
    .link-title { 
        font-size: 1.15rem; 
        font-weight: bold; 
        color: #05164D; 
        margin-bottom: 8px; 
        display: block; 
    }
    .link-url { 
        font-size: 0.8rem; 
        color: #666666; 
        word-break: break-all; 
    }
    .link-cat { 
        font-size: 0.7rem; 
        color: #7A7A7A; 
        text-transform: uppercase; 
        letter-spacing: 1.5px; 
        margin-bottom: 12px; 
        display: block; 
        font-weight: bold;
    }
    
    /* Przyciski */
    .btn-open {
        display: inline-block; 
        margin-top: 15px; 
        padding: 8px 16px;
        background-color: #FFB000; 
        color: #05164D !important;
        border: none; 
        text-decoration: none !important;
        font-size: 0.85rem; 
        font-weight: bold; 
        transition: 0.2s;
        text-align: center;
    }
    .btn-open:hover { 
        background-color: #05164D; 
        color: #FFFFFF !important; 
    }
    
    div[data-testid="stForm"] { border: 1px solid #E0E0E0; background-color: #FFFFFF; }
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
        df = pd.DataFrame(records)
        
        # USUWANIE DUPLIKATÓW W LOCIE (po adresie URL)
        if not df.empty and 'URL' in df.columns:
            df = df.drop_duplicates(subset=['URL'], keep='first')
            
        return df
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

# Funkcja pomocnicza do renderowania siatki kart
def render_cards(dataframe):
    if dataframe.empty:
        st.info("Brak wpisów w tym sektorze.")
        return
        
    cols = st.columns(3)
    for idx, row in enumerate(dataframe.itertuples()):
        with cols[idx % 3]:
            st.markdown(f"""
            <div class="link-card">
                <span class="link-cat">{getattr(row, 'Kategoria', 'Brak')}</span>
                <span class="link-title">{getattr(row, 'Nazwa', 'Bez nazwy')}</span>
                <span class="link-url">{str(getattr(row, 'URL', ''))[:45]}...</span><br>
                <a href="{getattr(row, 'URL', '#')}" target="_blank" class="btn-open">Zaloguj do systemu ➔</a>
            </div>
            """, unsafe_allow_html=True)

# Ładowanie danych
df = load_data()

# --- PASEK BOCZNY ---
st.sidebar.title("✈️ Terminal")
st.sidebar.markdown("---")
menu = st.sidebar.radio("Nawigacja:", ["🛫 Tablica Odlotów (Linki)", "🛬 Odprawa (Dodaj Nowy)", "🛠️ Hangar (Usuń Linki)"])

# --- WIDOK 1: PRZEGLĄD ---
if menu == "🛫 Tablica Odlotów (Linki)":
    st.title("🛫 Tablica Zakładek")
    
    search = st.text_input("Szukaj w rejestrze:", placeholder="Wpisz portal, system awizacyjny, targi...")
    st.markdown("<br>", unsafe_allow_html=True)
    
    if not df.empty:
        filtered_df = df.copy()
        
        # Filtrowanie po wyszukiwarce
        if search:
            query = search.lower()
            mask = filtered_df.apply(lambda row: query in str(row.get('Kategoria', '')).lower() or 
                                                 query in str(row.get('Nazwa', '')).lower() or 
                                                 query in str(row.get('URL', '')).lower(), axis=1)
            filtered_df = filtered_df[mask]
        
        if filtered_df.empty:
            st.info("Brak wyników w rejestrze.")
        else:
            # Tworzenie dynamicznych zakładek na górze
            categories = sorted([c for c in filtered_df['Kategoria'].unique() if str(c).strip() != ''])
            tab_titles = ["🌐 Wszystko"] + [f"📁 {cat}" for cat in categories]
            
            tabs = st.tabs(tab_titles)
            
            # 1. Zakładka ze wszystkimi linkami
            with tabs[0]:
                render_cards(filtered_df)
                
            # 2. Zakładki dla poszczególnych kategorii
            for i, cat in enumerate(categories):
                with tabs[i + 1]:
                    cat_df = filtered_df[filtered_df['Kategoria'] == cat]
                    render_cards(cat_df)
    else:
        st.info("Brak wpisów. Przejdź do Odprawy.")

# --- WIDOK 2: DODAWANIE ---
elif menu == "🛬 Odprawa (Dodaj Nowy)":
    st.title("🛬 Rejestracja nowego systemu")
    
    existing_categories = df['Kategoria'].unique().tolist() if not df.empty and 'Kategoria' in df.columns else []
    
    with st.form("add_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nazwa = st.text_input("Nazwa operacyjna")
            url = st.text_input("Adres URL")
        with col2:
            nowa_kategoria = st.text_input("Nowa kategoria")
            wybrana_kategoria = st.selectbox("Lub wybierz z bazy:", ["-- Wybierz --"] + existing_categories)
        
        submit = st.form_submit_button("Zatwierdź wpis", use_container_width=True)
        
        if submit:
            kategoria_docelowa = nowa_kategoria if nowa_kategoria else (wybrana_kategoria if wybrana_kategoria != "-- Wybierz --" else "")
            
            if nazwa and url and kategoria_docelowa:
                if not url.startswith("http"): url = "https://" + url
                with st.spinner("Przetwarzanie..."):
                    add_link(kategoria_docelowa, nazwa, url)
                st.success(f"System '{nazwa}' został zarejestrowany!")
                st.rerun()
            else:
                st.warning("Uzupełnij wszystkie dane.")

# --- WIDOK 3: USUWANIE ---
elif menu == "🛠️ Hangar (Usuń Linki)":
    st.title("🛠️ Zarządzanie flotą linków")
    
    if df.empty or 'Kategoria' not in df.columns:
        st.info("Brak aktywnych linków.")
    else:
        categories = sorted([c for c in df['Kategoria'].unique() if str(c).strip() != ''])
        cat_to_edit = st.selectbox("Wybierz sektor roboczy:", categories)
        
        cat_df = df[df['Kategoria'] == cat_to_edit]
        
        for idx, row in cat_df.iterrows():
            c1, c2 = st.columns([5, 1])
            c1.markdown(f"**{row.get('Nazwa', 'Bez nazwy')}** <br> <small style='color:gray;'>{row.get('URL', '')}</small>", unsafe_allow_html=True)
            
            if c2.button("Usuń", key=f"del_{idx}"):
                with st.spinner("Wyrejestrowywanie..."):
                    delete_link(idx)
                st.success("Wpis usunięto z serwera!")
                st.rerun()
