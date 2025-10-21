import os
import io
import json
import streamlit as st
import openai
from PIL import Image

# ──────────────────────────────────────────────────────────────
# KONFIGURACJA APLIKACJI
# ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="🎨 Generator kolorowanek", page_icon="🖍️", layout="centered")
st.title("🎨 Generator kolorowanek dla dzieci")
st.caption("Podaj temat przewodni i wygeneruj kolorowanki w formacie PNG do druku.")

# Inicjalizacja klienta OpenAI
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("Brak klucza OPENAI_API_KEY w sekcji Secrets.")
    st.stop()
openai.api_key = OPENAI_API_KEY

# ──────────────────────────────────────────────────────────────
# FUNKCJE
# ──────────────────────────────────────────────────────────────

def generuj_pomysly(temat: str, liczba: int) -> list:
    """Generuje listę pomysłów na kolorowanki w zadanym temacie."""
    prompt = (
        f"Podaj {liczba} pomysłów na czarno-białe kolorowanki dla dzieci na temat: {temat}. "
        f"Każdy pomysł w formie krótkiego opisu sceny (np. 'kot bawiący się kłębkiem wełny')."
    )
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
    )
    text = response.choices[0].message.content.strip()
    return [line.strip("-• ") for line in text.split("\n") if line.strip()]


def generuj_kolorowanke(opis: str) -> Image.Image:
    """Generuje kolorowankę na podstawie opisu."""
    prompt = f"simple black and white line art coloring page for kids: {opis}"
    result = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1024x1024"
    )
    image_url = result.data[0].url
    image = Image.open(io.BytesIO(client.images.retrieve_content(image_url)))
    return image


def zapisz_sesje(temat, pomysly):
    """Zapisuje bieżącą sesję jako JSON."""
    data = {"temat": temat, "pomysly": pomysly}
    st.download_button(
        "💾 Pobierz sesję",
        data=json.dumps(data, ensure_ascii=False),
        file_name="sesja_kolorowanki.json",
        mime="application/json"
    )


def wczytaj_sesje():
    """Wczytuje sesję z pliku JSON."""
    uploaded = st.file_uploader("📂 Wczytaj zapisaną sesję (JSON)", type=["json"])
    if uploaded:
        data = json.load(uploaded)
        st.session_state.temat = data["temat"]
        st.session_state.pomysly = data["pomysly"]
        st.success(f"Wczytano sesję: {data['temat']}")
        return True
    return False


# ──────────────────────────────────────────────────────────────
# LOGIKA GŁÓWNA
# ──────────────────────────────────────────────────────────────

if "pomysly" not in st.session_state:
    st.session_state.pomysly = []
if "temat" not in st.session_state:
    st.session_state.temat = ""

try:
    st.header("1️⃣ Podaj temat kolorowanek")
    temat = st.text_input("Temat przewodni:", st.session_state.temat)

    st.header("2️⃣ Wybierz ilość rysunków")
    liczba = st.slider("Liczba kolorowanek do wygenerowania:", 1, 10, 3)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✨ Generuj pomysły"):
            st.session_state.pomysly = generuj_pomysly(temat, liczba)
            st.session_state.temat = temat
            st.success("Wygenerowano pomysły!")

    with col2:
        if st.button("📂 Wczytaj poprzednią sesję"):
            wczytaj_sesje()

    if st.session_state.pomysly:
        st.subheader("🧠 Pomysły na kolorowanki:")
        for i, p in enumerate(st.session_state.pomysly, start=1):
            st.write(f"{i}. {p}")

        zapisz_sesje(st.session_state.temat, st.session_state.pomysly)

        if st.button("🎨 Generuj kolorowanki (PNG)"):
            for opis in st.session_state.pomysly:
                with st.spinner(f"Generuję kolorowankę: {opis}..."):
                    try:
                        obraz = client.images.generate(
                            model="gpt-image-1",
                            prompt=f"black and white outline coloring page for kids, {opis}",
                            size="1024x1024"
                        )
                        img_url = obraz.data[0].url
                        st.image(img_url, caption=opis)
                        st.download_button(
                            label="⬇️ Pobierz kolorowankę",
                            data=requests.get(img_url).content,
                            file_name=f"{opis}.png",
                            mime="image/png",
                        )
                    except Exception as e:
                        st.error(f"Błąd podczas generowania: {e}")

except Exception as e:
    st.error(f"❌ Błąd: {e}")
