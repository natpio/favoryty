import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Vorteza Logistics Terminal", page_icon="✈️", layout="wide", initial_sidebar_state="expanded")

# --- ZARZĄDZANIE SESJĄ (AUTORYZACJA) ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# --- STYLE CSS (PREMIUM LUFTHANSA THEME + WATERMARK) ---
st.markdown("""
<style>
    /* Globalne tło ze strukturą znaku wodnego "vorteza links" (SVG Vector Grid) */
    .stApp {
        background-color: #F4F6F9;
        background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='260' height='260' viewBox='0 0 260 260'><text x='30' y='140' fill='rgba(0, 31, 96, 0.035)' font-size='20' font-family='Helvetica Neue, Helvetica, Arial, sans-serif' font-weight='700' transform='rotate(-25 30 140)'>vorteza links</text></svg>");
        background-repeat: repeat;
    }
    
    /* Nagłówki w klimacie linii lotniczych */
    h1, h2, h3 { 
        color: #001F60 !important; 
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; 
        font-weight: 700;
        letter-spacing: -0.8px;
    }
    
    /* Pasek nawigacji u góry (Tabs) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(218, 224, 233, 0.7);
        padding: 12px 12px 0 12px;
        border-radius: 10px 10px 0 0;
        border-bottom: 4px solid #001F60;
        backdrop-filter: blur(8px);
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        background-color: #FFFFFF;
        border-radius: 6px 6px 0 0;
        color: #001F60;
        font-weight: 600;
        padding: 10px 26px;
        border: 1px solid #CFD6E1;
        border-bottom: none;
        transition: all 0.25s ease;
    }
    .stTabs [aria-selected="true"] {
        background-color: #001F60 !important;
        color: #FFA600 !important;
        border: 1px solid #001F60;
        box-shadow: 0 -4px 12px rgba(0, 31, 96, 0.15);
    }
    
    /* Nowoczesne Karty Systemowe (Lufthansa Gate Design) */
    .link-card {
        background-color: #FFFFFF;
        border-left: 5px solid #001F60;
        border-radius: 6px;
        padding: 24px; 
        margin-bottom: 22px;
        box-shadow: 0 6px 18px rgba(0, 31, 96, 0.04); 
        backdrop-filter: blur(20px);
        transition: all 0.2s ease-in-out;
        position: relative;
        overflow: hidden;
    }
    .link-card::after {
        content: "";
        position: absolute;
        top: 0; right: 0;
        width: 35px; height: 35px;
        background: linear-gradient(135deg, transparent 50%, rgba(0, 31, 96, 0.03) 50%);
    }
    .link-card:hover { 
        transform: translateY(-4px); 
        box-shadow: 0 12px 26px rgba(0, 31, 96, 0.12); 
        border-left: 5px solid #FFA600;
    }
    .link-title { font-size: 1.2rem; font-weight: 700; color: #001F60; margin-bottom: 6px; display: block; }
    .link-url { font-size: 0.8rem; color: #55637A; word-break: break-all; font-family: monospace; }
    .link-cat { font-size: 0.75rem; color: #FFA600; text-transform: uppercase; letter-spacing: 1.8px; margin-bottom: 14px; display: block; font-weight: 700; }
    
    /* Przyciski operacyjne (Lufthansa Yellow Action) */
    .btn-open {
        display: block; margin-top: 18px; padding: 10px 16px;
        background-color: #FFA600; color: #001F60 !important;
        border: none; border-radius: 4px; text-decoration: none !important;
        font-size: 0.85rem; font-weight: bold; transition: 0.2s; text-align: center;
        letter-spacing: 0.5px;
        box-shadow: 0 3px 6px rgba(255, 166, 0, 0.25);
    }
    .btn-open:hover { 
        background-color: #001F60; 
        color: #FFFFFF !important; 
        box-shadow: 0 5px 12px rgba(0, 31, 96, 0.3); 
    }
    
    /* Formularze i kontenery wejściowe */
    div[data-testid="stForm"] { 
        border: 1px solid #D0D7E3; 
        background-color: #FFFFFF; 
        border-radius: 8px; 
        padding: 25px;
        box-shadow: 0 8px 24px rgba(0, 31, 96, 0.04); 
    }
    
    /* Panel Logowania (Zabezpieczony Terminal) */
    .login-container { 
        max-width: 420px; 
        margin: 80px auto 20px auto; 
        padding: 35px; 
        background-color: #FFFFFF; 
        border-top: 6px solid #001F60; 
        border-radius: 8px; 
        box-shadow: 0 15px 35px rgba(0, 31, 96, 0.1); 
        text-align: center; 
    }
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
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        st.error("Błąd uwierzytelniania. Skonfiguruj poprawnie 'GCP_CREDENTIALS' w Streamlit Secrets.")
        st.stop()

# Pobieranie poprawnego hasła z arkusza 'Ustawienia' z usunięciem białych znaków
@st.cache_data(ttl=60)
def get_system_password():
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(SHEET_ID).worksheet("Ustawienia")
        raw_password = str(sheet.acell('B1').value)
        return raw_password.strip()  # Usuwa ukryte spacje i entery
    except gspread.exceptions.WorksheetNotFound:
        st.error("Błąd krytyczny: Brak zakładki 'Ustawienia' w Arkuszu Google. Utwórz ją i dodaj hasło w B1.")
        st.stop()
    except Exception as e:
        st.error(f"Nie można pobrać hasła: {e}")
        st.stop()

# --- EKRAN LOGOWANIA ---
if not st.session_state.authenticated:
    st.markdown("""
        <div class="login-container">
            <h2 style="color: #001F60; margin-bottom: 2px; font-size: 2.2rem;">✈️ VORTEZA</h2>
            <p style="color: #7A8B9E; font-weight: bold; letter-spacing: 3px; font-size: 0.8rem; margin-bottom: 30px;">LOGISTICS TERMINAL</p>
            <div style="background-color: #F0F4F8; padding: 10px; border-radius: 4px; margin-bottom: 10px;">
                <span style="color: #001F60; font-weight: 600; font-size: 0.9rem;">STATUS: SECURE GATEWAY</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.8, 1])
    with col2:
        with st.form("login_form"):
            password_input = st.text_input("Wprowadź kod autoryzacyjny portu:", type="password")
            submit_button = st.form_submit_button("Autoryzuj dostęp ➔", use_container_width=True)
            
            if submit_button:
                correct_password = get_system_password()
                if password_input == correct_password:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("❌ Odmowa dostępu. Nieprawidłowy kod autoryzacyjny.")
    st.stop()

# --- EMISJA DANYCH (TYLKO DLA ZALOGOWANYCH) ---

def get_sheet():
    client = get_gspread_client()
    return client.open_by_key(SHEET_ID).sheet1

@st.cache_data(ttl=10)
def load_data():
    try:
        sheet = get_sheet()
        records = sheet.get_all_records()
        df = pd.DataFrame(records)
        if not df.empty and 'URL' in df.columns:
            df = df.drop_duplicates(subset=['URL'], keep='first')
        return df
    except Exception as e:
        return pd.DataFrame(columns=["Kategoria", "Nazwa", "URL"])

def add_link(kategoria, nazwa, url):
    sheet = get_sheet()
    sheet.append_row([kategoria, nazwa, url])
    st.cache_data.clear()

def delete_link(pandas_index):
    sheet = get_sheet()
    sheet.delete_rows(pandas_index + 2)
    st.cache_data.clear()

def render_cards(dataframe):
    if dataframe.empty:
        st.info("Brak aktywnych systemów w tym sektorze.")
        return
        
    cols = st.columns(3)
    for idx, row in enumerate(dataframe.itertuples()):
        with cols[idx % 3]:
            st.markdown(f"""
            <div class="link-card">
                <span class="link-cat">✈️ {getattr(row, 'Kategoria', 'Brak')}</span>
                <span class="link-title">{getattr(row, 'Nazwa', 'Bez nazwy')}</span>
                <span class="link-url">{str(getattr(row, 'URL', ''))[:48]}...</span><br>
                <a href="{getattr(row, 'URL', '#')}" target="_blank" class="btn-open">Uruchom procedurę ➔</a>
            </div>
            """, unsafe_allow_html=True)

df = load_data()

# --- PREMIUM SIDEBAR ---
st.sidebar.markdown(
    """
    <div style="background-color: #001F60; padding: 22px 15px; border-radius: 6px; margin-bottom: 25px; text-align: center; box-shadow: 0 4px 12px rgba(0,31,96,0.25);">
        <h2 style="color: #FFA600 !important; margin: 0; padding: 0; font-size: 2rem; letter-spacing: -0.5px;">✈️ VORTEZA</h2>
        <span style="color: #FFFFFF; font-size: 0.75rem; letter-spacing: 2.5px; font-weight: bold; display:block; margin-top:2px;">LOGISTICS TERMINAL</span>
    </div>
    """, unsafe_allow_html=True
)

menu = st.sidebar.radio("Nawigacja terminala:", ["🛫 Tablica Odlotów (Rejestr)", "🛬 Odprawa (Nowy System)", "🛠️ Hangar (Modyfikacja Baz)"])

st.sidebar.markdown("<br><hr style='border-color: #CFD6E1;'><br>", unsafe_allow_html=True)
if st.sidebar.button("🔒 Zamknij bezpieczną sesję", use_container_width=True):
    st.session_state.authenticated = False
    st.rerun()

# --- WIDOK 1: TABLICA ODLOTÓW ---
if menu == "🛫 Tablica Odlotów (Rejestr)":
    st.title("🛫 Globalna Tablica Monitoringu Linków")
    search = st.text_input("🔍 Wyszukiwarka operacyjna (targi, portale, spedycje, awizacje):", placeholder="Wpisz szukaną frazę...")
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
            st.info("Brak wyników spełniających kryteria wyszukiwania.")
        else:
            categories = sorted([c for c in filtered_df['Kategoria'].unique() if str(c).strip() != ''])
            tab_titles = ["🌐 Cała Sieć Operacyjna"] + [f"📁 {cat}" for cat in categories]
            
            tabs = st.tabs(tab_titles)
            
            with tabs[0]:
                render_cards(filtered_df)
                
            for i, cat in enumerate(categories):
                with tabs[i + 1]:
                    cat_df = filtered_df[filtered_df['Kategoria'] == cat]
                    render_cards(cat_df)
    else:
        st.info("Baza danych jest pusta. Przejdź do zakładki Odprawa, aby dodać pierwszy link.")

# --- WIDOK 2: ODPRAWA (DODAWANIE) ---
elif menu == "🛬 Odprawa (Nowy System)":
    st.title("🛬 Rejestracja Nowego Systemu w Hubie")
    
    existing_categories = df['Kategoria'].unique().tolist() if not df.empty and 'Kategoria' in df.columns else []
    
    with st.form("add_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nazwa = st.text_input("Nazwa systemu / przeznaczenie")
            url = st.text_input("Adres URL portalu")
        with col2:
            nowa_kategoria = st.text_input("Utwórz nową kategorię")
            wybrana_kategoria = st.selectbox("Lub przypisz do istniejącej:", ["-- Wybierz Sektor --"] + existing_categories)
        
        submit = st.form_submit_button("Zatwierdź i wprowadź do rejestru", use_container_width=True)
        
        if submit:
            kategoria_docelowa = nowa_kategoria if nowa_kategoria else (wybrana_kategoria if wybrana_kategoria != "-- Wybierz Sektor --" else "")
            if nazwa and url and kategoria_docelowa:
                if not url.startswith("http"): 
                    url = "https://" + url
                with st.spinner("Wysyłanie pakietu danych do bazy Google Sheets..."):
                    add_link(kategoria_docelowa, nazwa, url)
                st.success(f"Sukces: System '{nazwa}' został pomyślnie zarejestrowany!")
                st.rerun()
            else:
                st.warning("Błąd: Wszystkie pola (w tym poprawne wskazanie kategorii) są wymagane.")

# --- WIDOK 3: HANGAR (USUWANIE) ---
elif menu == "🛠️ Hangar (Modyfikacja Baz)":
    st.title("🛠️ Hangar Techniczny: Czyszczenie Floty Linków")
    st.markdown("Strefa administracyjna. Usunięcie elementu spowoduje jego natychmiastowe skasowanie z Arkusza Google.")
    
    if df.empty or 'Kategoria' not in df.columns:
        st.info("Brak elementów do modyfikacji.")
    else:
        categories = sorted([c for c in df['Kategoria'].unique() if str(c).strip() != ''])
        cat_to_edit = st.selectbox("Wybierz sektor roboczy bazy danych:", categories)
        
        cat_df = df[df['Kategoria'] == cat_to_edit]
        
        st.markdown("<br>", unsafe_allow_html=True)
        for idx, row in cat_df.iterrows():
            c1, c2 = st.columns([5, 1])
            c1.markdown(f"""
            <div style="background-color: #FFFFFF; padding: 12px 18px; border-radius: 4px; border-left: 3px solid #001F60; box-shadow: 0 2px 5px rgba(0,0,0,0.02);">
                <strong style="color:#001F60;">{row.get('Nazwa', 'Bez nazwy')}</strong><br>
                <code style='color:#55637A; font-size:0.75rem;'>{row.get('URL', '')}</code>
            </div>
            """, unsafe_allow_html=True)
            
            # Unikalny klucz przycisku zapobiegający konfliktom renderowania
            if c2.button("Wyrejestruj", key=f"del_{idx}", use_container_width=True):
                with st.spinner("Aktualizacja rejestru na serwerze..."):
                    delete_link(idx)
                st.success("Wpis został trwale usunięty z bazy danych.")
                st.rerun()
