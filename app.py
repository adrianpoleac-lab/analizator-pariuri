import math
import pandas as pd
import requests
import streamlit as st

# 🔑 INTRODUCE CHEIA TA API AICI ÎNTRE GHILIMELE
API_KEY = "INTRODUCE_AICI_CHEIA_TA"

LIGI_DISPONIBILE = {
    "🌐 Toate Meciurile Viitoare (Fotbal Global)": "soccer",
    "🇷🇴 Superliga (România)": "soccer_romania_liga1",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League (Anglia)": "soccer_epl",
    "🇪🇸 La Liga (Spania)": "soccer_spain_la_liga",
    "🇮🇹 Serie A (Italia)": "soccer_italy_serie_a",
    "🇩🇪 Bundesliga (Germania)": "soccer_germany_bundesliga",
    "🇫🇷 Ligue 1 (Franța)": "soccer_france_ligue_one",
    "🇵🇹 Primeira Liga (Portugalia)": "soccer_portugal_primeira_liga",
    "🇹🇷 Süper Lig (Turcia)": "soccer_turkey_super_lig",
    "🇧🇪 First Division A (Belgia)": "soccer_belgium_first_div",
    "🇳🇱 Eredivisie (Olanda)": "soccer_netherlands_eredivisie",
    "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Premiership (Scoția)": "soccer_spl",
    "🇬🇷 Super League (Grecia)": "soccer_greece_super_league",
    "🏆 UEFA Champions League": "soccer_uefa_champs_league",
    "🇪🇺 UEFA Europa League": "soccer_uefa_europa_league",
    "🇪🇺 UEFA Conference League": "soccer_uefa_conference_league",
}


def poisson_probability(lmbda, k):
    return (lmbda**k * math.exp(-lmbda)) / math.factorial(k)


def preia_meciuri_si_cote_odds_api(sport_key):
    """Preia meciurile și cotele curente din liga selectată via The Odds API."""
    if API_KEY == "INTRODUCE_AICI_CHEIA_TA" or not API_KEY.strip():
        st.warning("⚠️ Introdu cheia API în fișierul app.py la linia API_KEY!")
        return []

    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={API_KEY}&regions=eu,uk&markets=h2h,totals&oddsFormat=decimal"

    try:
        response = requests.get(url, timeout=10)

        requests_remaining = response.headers.get("x-requests-remaining")
        requests_used = response.headers.get("x-requests-used")
        if requests_remaining is not None:
            st.sidebar.caption(
                f"📊 Apeluri API rămase: **{requests_remaining}** (Utilizate: {requests_used})"
            )

        if response.status_code != 200:
            st.error(f"Eroare API [{response.status_code}]: {response.text}")
            return []

        data = response.json()

        if not isinstance(data, list) or len(data) == 0:
            return []

        meciuri = []
        for event in data:
            home = event.get("home_team")
            away = event.get("away_team")
            sport_title = event.get("sport_title", "")

            cota_1, cota_X, cota_2, cota_over = 1.85, 3.40, 3.80, 1.90

            if event.get("bookmakers"):
                bookmaker = event["bookmakers"][0]
                for market in bookmaker.get("markets", []):
                    if market["key"] == "h2h":
                        for outcome in market["outcomes"]:
                            if outcome["name"] == home:
                                cota_1 = outcome["price"]
                            elif outcome["name"] == away:
                                cota_2 = outcome["price"]
                            elif outcome["name"] in ["Draw", "Egal"]:
                                cota_X = outcome["price"]

                    elif market["key"] == "totals":
                        for outcome in market["outcomes"]:
                            if (
                                outcome.get("point") == 2.5
                                and outcome.get("name") == "Over"
                            ):
                                cota_over = outcome["price"]

            label_meci = (
                f"[{sport_title}] {home} vs {away}"
                if sport_key == "soccer"
                else f"{home} vs {away}"
            )

            meciuri.append(
                {
                    "label": label_meci,
                    "gazda": home,
                    "oaspete": away,
                    "cota_1": cota_1,
                    "cota_X": cota_X,
                    "cota_2": cota_2,
                    "cota_over25": cota_over,
                    "cota_gg": 1.85,
                }
            )

        return meciuri
    except Exception as e:
        st.error(f"Eroare la conectare: {e}")
        return []


st.set_page_config(
    page_title="Analizator Pariuri +EV (Multi-Ligă)", page_icon="⚽", layout="wide"
)

st.title("⚽ Analizator Automatic de Pariuri (+EV)")
st.caption(
    "Preluare automată cotații pe ligi multiple prin The Odds API & Model Poisson."
)

st.divider()

# Selector Ligă
st.sidebar.header("⚙️ Selectare Competiție")
liga_numenume = st.sidebar.selectbox(
    "Alege Campionatul:", list(LIGI_DISPONIBILE.keys())
)
sport_key = LIGI_DISPONIBILE[liga_numenume]

if st.sidebar.button("🔄 Reîmprospătează Datele"):
    st.cache_data.clear()

meciuri_disponibile = preia_meciuri_si_cote_odds_api(sport_key)

if meciuri_disponibile:
    opțiuni = [m["label"] for m in meciuri_disponibile]
    meci_selectat = st.selectbox(f"Alege meciul din {liga_numenume}:", opțiuni)

    meci = next(m for m in meciuri_disponibile if m["label"] == meci_selectat)

    echipa_h_def = meci["gazda"]
    echipa_a_def = meci["oaspete"]
    cota_1_def = meci["cota_1"]
    cota_X_def = meci["cota_X"]
    cota_2_def = meci["cota_2"]
    cota_over_def = meci["cota_over25"]
    cota_gg_def = meci["cota_gg"]
    st.success(f"S-au încărcat automat cotele pentru **{meci_selectat}**!")
else:
    st.warning(
        f"Nu s-au găsit meciuri active pentru competiția **{liga_numenume}**."
    )
    echipa_h_def, echipa_a_def = "Gazdă", "Oaspete"
    cota_1_def, cota_X_def, cota_2_def = 1.85, 3.60, 4.20
    cota_over_def, cota_gg_def = 1.95, 1.85

col1, col2 = st.columns(2)

with col1:
    st.subheader("🏠 Gazde")
    echipa_h = st.text_input("Echipa Gazdă", echipa_h_def)
    xg_h = st.number_input(
        f"xG estimat ({echipa_h})",
        min_value=0.1,
        max_value=6.0,
        value=1.55,
        step=0.05,
    )
    cota_1 = st.number_input(
        f"Cotă 1 ({echipa_h})", min_value=1.0, value=float(cota_1_def)
    )

with col2:
    st.subheader("✈️ Oaspeți")
    echipa_a = st.text_input("Echipa Oaspete", echipa_a_def)
    xg_a = st.number_input(
        f"xG estimat ({echipa_a})",
        min_value=0.1,
        max_value=6.0,
        value=1.15,
        step=0.05,
    )
    cota_2 = st.number_input(
        f"Cotă 2 ({echipa_a})", min_value=1.0, value=float(cota_2_def)
    )

st.subheader("🎲 Cote Piețe Secundare")
col3, col4, col5 = st.columns(3)

with col3:
    cota_X = st.number_input(
        "Cotă X (Egalitate)", min_value=1.0, value=float(cota_X_def)
    )
with col4:
    cota_over = st.number_input(
        "Cotă Peste 2.5 Goluri", min_value=1.0, value=float(cota_over_def)
    )
with col5:
    cota_gg = st.number_input(
        "Cotă Ambele Marchează (GG)", min_value=1.0, value=float(cota_gg_def)
    )

st.divider()

# Matrice Poisson
max_g = 7
p_1, p_X, p_2, p_over25, p_gg = 0.0, 0.0, 0.0, 0.0, 0.0

for g in range(max_g):
    prob_g = poisson_probability(xg_h, g)
    for o in range(max_g):
        prob_o = poisson_probability(xg_a, o)
        prob_scor = prob_g * prob_o

        if g > o:
            p_1 += prob_scor
        elif g == o:
            p_X += prob_scor
        else:
            p_2 += prob_scor

        if (g + o) > 2.5:
            p_over25 += prob_scor

        if g > 0 and o > 0:
            p_gg += prob_scor

p_under25 = 1.0 - p_over25
p_ng = 1.0 - p_gg

optiuni = [
    {
        "Piață / Opțiune": f"1 (Victorie {echipa_h})",
        "Șansă Reușită": p_1,
        "Cotă Casa": cota_1,
    },
    {"Piață / Opțiune": "X (Egalitate)", "Șansă Reușită": p_X, "Cotă Casa": cota_X},
    {
        "Piață / Opțiune": f"2 (Victorie {echipa_a})",
        "Șansă Reușită": p_2,
        "Cotă Casa": cota_2,
    },
    {
        "Piață / Opțiune": "Peste 2.5 Goluri",
        "Șansă Reușită": p_over25,
        "Cotă Casa": cota_over,
    },
    {
        "Piață / Opțiune": "Sub 2.5 Goluri",
        "Șansă Reușită": p_under25,
        "Cotă Casa": 0,
    },
    {
        "Piață / Opțiune": "Ambele Marchează (GG)",
        "Șansă Reușită": p_gg,
        "Cotă Casa": cota_gg,
    },
    {
        "Piață / Opțiune": "Nu Marchează Ambele (NG)",
        "Șansă Reușită": p_ng,
        "Cotă Casa": 0,
    },
]

optiuni_procesate = []
for opt in optiuni:
    prob = opt["Șansă Reușită"]
    cota = opt["Cotă Casa"]
    ev = (prob * cota) - 1 if cota > 1.0 else -1.0
    cota_corecta = 1 / prob if prob > 0 else 0

    optiuni_procesate.append(
        {
            "Opțiune": opt["Piață / Opțiune"],
            "Șansă Reușită (%)": f"{prob * 100:.1f}%",
            "Cotă Oferită": f"{cota:.2f}" if cota > 1.0 else "N/A",
            "Cotă Corectă (Fără Marjă)": f"{cota_corecta:.2f}",
            "Valoare (+EV)": f"+{ev * 100:.1f}%" if ev > 0 else "Fără Valoare",
            "is_ev": ev > 0.02,
            "raw_prob": prob,
        }
    )

st.subheader("🟢 Oportunități de Pariu Valoroase (+EV)")
recomandari_ev = [item for item in optiuni_procesate if item["is_ev"]]

if recomandari_ev:
    for rec in recomandari_ev:
        st.info(
            f"**{rec['Opțiune']}** | Șansă: **{rec['Șansă Reușită (%)']}** | "
            f"Cotă: **{rec['Cotă Oferită']}** | Valoare (+EV): **{rec['Valoare (+EV)']}**"
        )
else:
    st.warning("Nicio opțiune nu oferă valoare matematică (+EV) la cotele curente.")

st.subheader("📋 Tablou Complet")
df = pd.DataFrame(optiuni_procesate).drop(columns=["is_ev", "raw_prob"])
st.dataframe(df, use_container_width=True)
