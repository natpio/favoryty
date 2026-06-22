import streamlit as st
import json
import pandas as pd

# Konfiguracja strony
st.set_page_config(page_title="Tablica Linków SQM", page_icon="🔗", layout="wide")

# Wczytywanie danych z pliku JSON
@st.cache_data
def load_links():
    try:
        with open("links.json", "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        st.error("Nie znaleziono pliku links.json!")
        return {}

def main():
    st.title("🔗 Centrala Zakładek Logistycznych")
    
    links_data = load_links()
    
    if not links_data:
        return

    categories = list(links_data.keys())

    # Pasek boczny
    st.sidebar.header("📂 Kategorie")
    selected_category = st.sidebar.radio("Wybierz sekcję:", categories)

    st.subheader(f"{selected_category}")

    # Wyświetlanie linków
    current_links = links_data[selected_category]
    
    if current_links:
        # Tworzymy estetyczną listę klikalnych kart
        for link in current_links:
            st.markdown(
                f"""
                <div style="padding: 10px; border-radius: 5px; border: 1px solid #ddd; margin-bottom: 10px;">
                    <strong>{link['title']}</strong><br>
                    <a href="{link['url']}" target="_blank" style="text-decoration: none; color: #0066cc;">Otwórz link 🚀</a>
                </div>
                """, 
                unsafe_allow_html=True
            )
    else:
        st.info("Brak linków w tej kategorii.")

if __name__ == "__main__":
    main()
