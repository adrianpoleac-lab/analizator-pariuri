import math
import pandas as pd
import streamlit as st


def poisson_probability(lmbda, k):
    return (lmbda**k * math.exp(-lmbda)) / math.factorial(k)


st.set_page_config(
    page_title="Analizator Pariuri +EV", page_icon="⚽", layout="wide"
)

st.title("⚽ Analizator Statistic de Meciuri & Pariuri (+EV)")
st.caption(
    "Calculează automat probabilitățile de reușită și determină opțiunile cu cea mai mare valoare matematică."
)

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("🏠 Echipa Gazdă")
    echipa_h = st.text_input("Nume echipa gazdă", "Arsenal")
    xg_h = st.number_input(
        f"xG estimat ({echipa_h})",
        min_value=0.1,
        max_value=6.0,
        value=1.85,
        step=0.05,
    )
    cota_1 = st.number_input(f"Cotă 1 ({echipa_h})", min_value=1.0, value=1.65)

with col2:
    st.subheader("✈️ Echipa Oaspete")
    echipa_a = st.text_input("Nume echipa oaspete", "Chelsea")
    xg_a = st.number_input(
        f"xG estimat ({echipa_a})",
        min_value=0.1,
        max_value=6.0,
        value=0.95,
        step=0.05,
    )
    cota_2 = st.number_input(f"Cotă 2 ({echipa_a})", min_value=1.0, value=5.25)

st.subheader("🎲 Cote pentru piețe secundare")
col3, col4, col5 = st.columns(3)

with col3:
    cota_X = st.number_input("Cotă X (Egalitate)", min_value=1.0, value=4.20)
with col4:
    cota_over = st.number_input(
        "Cotă Peste 2.5 Goluri", min_value=1.0, value=1.90
    )
with col5:
    cota_gg = st.number_input(
        "Cotă Ambele Marchează (GG)", min_value=1.0, value=1.80
    )

st.divider()

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

optiune_sigura = max(optiuni_procesate, key=lambda x: x["raw_prob"])

st.subheader("🔥 Top Recomandare - Cea Mai Mare Șansă de Reușită")
st.success(
    f"Piața cu cele mai mari șanse statistice de câștig este **{optiune_sigura['Opțiune']}** "
    f"cu o probabilitate de **{optiune_sigura['Șansă Reușită (%)']}**."
)

st.subheader("🟢 Oportunități de Pariu Valoroase (+EV)")
recomandari_ev = [item for item in optiuni_procesate if item["is_ev"]]

if recomandari_ev:
    for rec in recomandari_ev:
        st.info(
            f"**{rec['Opțiune']}** | Șansă Reușită: **{rec['Șansă Reușită (%)']}** | "
            f"Cotă Jucată: **{rec['Cotă Oferită']}** | Profit Estimat (+EV): **{rec['Valoare (+EV)']}**"
        )
else:
    st.warning(
        "Nicio opțiune nu oferă valoare matematică (+EV) la cotele introduse."
    )

st.subheader("📋 Tablou Complet Probabilități")
df = pd.DataFrame(optiuni_procesate).drop(columns=["is_ev", "raw_prob"])
st.dataframe(df, use_container_width=True)
