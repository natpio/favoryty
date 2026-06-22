import streamlit as st
import json
import base64

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Vorteza Links", page_icon="🔗", layout="wide", initial_sidebar_state="expanded")

# --- STYLE CSS ---
st.markdown("""
<style>
    /* Nowoczesny, ciemny motyw z akcentami */
    h1, h2, h3 {
        color: #00D2FF;
        font-family: 'Segoe UI', Tahoma, sans-serif;
    }
    .link-card {
        background: linear-gradient(145deg, #1E212B, #171920);
        border-left: 4px solid #00D2FF;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.4);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .link-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 6px 15px rgba(0, 210, 255, 0.2);
    }
    .link-title {
        font-size: 1.15rem;
        font-weight: bold;
        color: #FFFFFF;
        margin-bottom: 6px;
        display: block;
    }
    .link-url {
        font-size: 0.8rem;
        color: #8C98A4;
        word-break: break-all;
    }
    .btn-open {
        display: inline-block;
        margin-top: 12px;
        padding: 6px 14px;
        background-color: rgba(0, 210, 255, 0.1);
        color: #00D2FF !important;
        border: 1px solid #00D2FF;
        border-radius: 5px;
        text-decoration: none !important;
        font-size: 0.85rem;
        font-weight: bold;
        transition: 0.2s;
    }
    .btn-open:hover {
        background-color: #00D2FF;
        color: #12141A !important;
    }
</style>
""", unsafe_allow_html=True)

# --- ŁADOWANIE DANYCH ---
FILE_NAME = "moje_zakladki.json"

def load_data():
    try:
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"Ogólne": []}

# Używamy session_state, aby aplikacja pamiętała zmiany w locie
if "links_db" not in st.session_state:
    st.session_state.links_db = load_data()

def save_data():
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        json.dump(st.session_state.links_db, f, ensure_ascii=False, indent=4)

# --- PASEK BOCZNY ---
st.sidebar.title("Vorteza Systems")
st.sidebar.markdown("---")
menu = st.sidebar.radio("Zarządzanie:", ["🌌 Baza Linków", "➕ Dodaj Nowy", "⚙️ Edycja Struktur", "💾 Zapisz do GitHub"])

# --- WIDOK 1: PRZEGLĄDANIE ---
if menu == "🌌 Baza Linków":
    st.title("🌌 Centralna Baza Zakładek")
    
    categories = list(st.session_state.links_db.keys())
    if not categories:
        st.info("Brak zakładek. Przejdź do sekcji 'Dodaj Nowy'.")
    else:
        # Wyszukiwarka na pełną szerokość
        search = st.text_input("🔍 Wyszukaj (nazwa portalu, system awizacyjny, targi...)", placeholder="Zacznij pisać...")
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Wykorzystanie zakładek (Tabs) z natywnego Streamlita do estetycznego podziału
        tabs = st.tabs(categories)
        
        for i, cat in enumerate(categories):
            with tabs[i]:
                links = st.session_state.links_db[cat]
                
                if search:
                    links = [l for l in links if search.lower() in l['title'].lower() or search.lower() in l['url'].lower()]
                
                if not links:
                    st.write("*Brak linków w tej kategorii.*")
                else:
                    # Układamy linki w zgrabną siatkę 3-kolumnową
                    cols = st.columns(3)
                    for idx, link in enumerate(links):
                        with cols[idx % 3]:
                            st.markdown(f"""
                            <div class="link-card">
                                <span class="link-title">{link['title']}</span>
                                <span class="link-url">{link['url'][:45]}...</span><br>
                                <a href="{link['url']}" target="_blank" class="btn-open">Otwórz stronę 🚀</a>
                            </div>
                            """, unsafe_allow_html=True)

# --- WIDOK 2: DODAWANIE ---
elif menu == "➕ Dodaj Nowy":
    st.title("➕ Dodaj do bazy")
    
    categories = list(st.session_state.links_db.keys())
    
    with st.form("add_link_form"):
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("Nazwa strony")
            url = st.text_input("Adres URL")
        with col2:
            if categories:
                category = st.selectbox("Przypisz do kategorii", categories)
            else:
                category = None
                st.warning("Najpierw utwórz kategorię w zakładce Edycja Struktur.")
        
        submitted = st.form_submit_button("Zapisz Link", use_container_width=True)
        
        if submitted and title and url and category:
            if not url.startswith("http"):
                url = "https://" + url
            st.session_state.links_db[category].append({"title": title, "url": url})
            save_data()
            st.success(f"Pomyślnie dodano '{title}'!")

# --- WIDOK 3: ZARZĄDZANIE KATEGORIAMI I USUWANIE ---
elif menu == "⚙️ Edycja Struktur":
    st.title("⚙️ Edycja zawartości")
    
    with st.expander("➕ Utwórz nową kategorię", expanded=True):
        new_cat = st.text_input("Nazwa nowego folderu:")
        if st.button("Utwórz"):
            if new_cat and new_cat not in st.session_state.links_db:
                st.session_state.links_db[new_cat] = []
                save_data()
                st.success(f"Folder '{new_cat}' został utworzony!")
                st.rerun()
                
    st.divider()
    st.markdown("### 🗑️ Usuń nieaktualne linki")
    categories = list(st.session_state.links_db.keys())
    cat_to_edit = st.selectbox("Wybierz obszar roboczy:", categories)
    
    if cat_to_edit:
        links = st.session_state.links_db[cat_to_edit]
        for idx, link in enumerate(links):
            c1, c2 = st.columns([5, 1])
            c1.markdown(f"**{link['title']}** <br> <small>{link['url']}</small>", unsafe_allow_html=True)
            if c2.button("Usuń", key=f"del_{cat_to_edit}_{idx}"):
                st.session_state.links_db[cat_to_edit].pop(idx)
                save_data()
                st.rerun()

# --- WIDOK 4: EXPORT ---
elif menu == "💾 Zapisz do GitHub":
    st.title("💾 Trwały zapis w repozytorium")
    st.info("Jako że aplikacja działa chmurowo, po zamknięciu sesji najnowsze dane mogą zostać utracone. Aby trwale zaktualizować linki, pobierz wygenerowany kod i podmień plik `moje_zakladki.json` w swoim repozytorium.")
    
    json_str = json.dumps(st.session_state.links_db, ensure_ascii=False, indent=4)
    
    st.download_button(
        label="📥 Pobierz aktualny moje_zakladki.json",
        data=json_str,
        file_name="moje_zakladki.json",
        mime="application/json",
        use_container_width=True
    )
