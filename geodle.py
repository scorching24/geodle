import streamlit as st
import pandas as pd
import random
import plotly.graph_objects as go
import pydeck as pdk

@st.cache_data
def load_data():
    return pd.read_csv('final_data.csv')

df = load_data()

if 'HDI_actual' not in st.session_state:
    st.session_state.HDI_actual = None

if 'GII_actual' not in st.session_state:
    st.session_state.GII_actual = None

st.title("🌍 geodle: a human geography guessing game")

st.markdown("can you guess a country's **HDI** (human development index) and **GII** (gender inequality index)?")
st.markdown("(you must be within 0.03 of the actual values)")

if 'current_country' not in st.session_state:
    st.session_state.current_country = random.choice(df['country'].tolist())

if 'attempts_left' not in st.session_state:
    st.session_state.attempts_left = None

if 'game_over' not in st.session_state:
    st.session_state.game_over = False

if 'difficulty_selected' not in st.session_state:
    st.session_state.difficulty_selected = False

if not st.session_state.difficulty_selected:
    st.markdown("### 🎯 choose your difficulty:")
    difficulty = st.selectbox("select:", ['🟢 easy (5 attempts)', '🟠 medium (3 attempts)', '🔴 hard (1 attempt)'])
    if st.button("🚀 start game"):
        st.session_state.difficulty_selected = True
        if 'easy' in difficulty.lower():
            st.session_state.attempts_left = 5
        elif 'medium' in difficulty.lower():
            st.session_state.attempts_left = 3
        else:
            st.session_state.attempts_left = 1
        st.rerun()

if st.session_state.difficulty_selected and not st.session_state.game_over:
    country = st.session_state.current_country
    country_row = df[df['country'] == country].iloc[0]

    st.markdown(f"## 🗺️ country to guess: **{country}**")

    try:
        flag_code = country_row['country_code'].strip().lower()
        flag_url = f"https://flagcdn.com/w320/{flag_code}.png"
        st.image(flag_url, width=200)
    except Exception as e:
        st.warning(f"⚠️ could not load flag for this country: {e}")

    st.info(f"🧠 you have **{st.session_state.attempts_left}** attempt(s) left")

    HDI_guess = st.slider("📍 guess HDI (0.00 - 1.00)", min_value=0.0, max_value=1.0, step=0.01, key="HDI_guess")
    GII_guess = st.slider("📍 guess GII (0.00 - 1.00)", min_value=0.0, max_value=1.0, step=0.01, key="GII_guess")

    if st.button("📨 submit guess"):
        st.session_state.HDI_actual = country_row['HDI']
        st.session_state.GII_actual = country_row['GII']

        HDI_actual = st.session_state.HDI_actual
        GII_actual = st.session_state.GII_actual

        HDI_correct = abs(HDI_guess - HDI_actual) < 0.03
        GII_correct = abs(GII_guess - GII_actual) < 0.03

        st.markdown("### 🧾 results:")
        if HDI_correct:
            st.success("✅ HDI correct!")
        else:
            st.warning("❌ HDI too high!" if HDI_guess > HDI_actual else "❌ HDI too low!")

        if GII_correct:
            st.success("✅ GII correct!")
        else:
            st.warning("❌ GII too high!" if GII_guess > GII_actual else "❌ GII too low!")

        if HDI_correct and GII_correct:
            st.balloons()
            st.success("🎉 you guessed both correctly!")
            st.session_state.game_over = True
        else:
            st.session_state.attempts_left -= 1
            if st.session_state.attempts_left == 0:
                st.error("💥 out of guesses! game over.")
                st.session_state.game_over = True

if st.session_state.game_over:
    country_row = df[df['country'] == st.session_state.current_country].iloc[0]

if st.session_state.game_over:
    st.markdown("## 📊 country stats")
    st.markdown(f"**{st.session_state.current_country}'s** indicators:")
    st.markdown(f"**✔️ correct HDI:** `{st.session_state.HDI_actual:.2f}`")
    st.markdown(f"**✔️ correct GII:** `{st.session_state.GII_actual:.2f}`")
    
    try:
        map_data = pd.DataFrame({
            'lat': [country_row['latitude']],
            'lon': [country_row['longitude']],
        })

        st.pydeck_chart(pdk.Deck(
            initial_view_state=pdk.ViewState(
                latitude=map_data['lat'][0],
                longitude=map_data['lon'][0],
                zoom=3
            ),
            layers=[
                pdk.Layer(
                    'ScatterplotLayer',
                    data=map_data,
                    get_position='[lon, lat]',
                    get_radius=50000,
                    get_color=[255,0,0],
                    pickable=True
                )
            ]
        ))
    except:
        st.warning("⚠️ could not load map for this country")

    def show_country_stats(row):
        labels = ['Life Expectancy', 'Mean Years of Schooling', 'GNI per Capita (×1000)']
        country_values = [
            row['life expectancy'],
            row['mean years of schooling'],
            row['GNI per capita'] / 1000
        ]

        avg_values = [
            73.6,
            8.7,
            12.8
        ]

        fig = go.Figure(data=[
            go.Bar(name=row['country'], x=labels, y=country_values, marker_color='royalblue'),
            go.Bar(name='Global Average', x=labels, y=avg_values, marker_color='lightgray')
        ])

        fig.update_layout(title=f"{row['country']} vs Global Average", barmode='group')
        st.plotly_chart(fig)

    show_country_stats(df[df['country'] == st.session_state.current_country].iloc[0])

    if st.button("🔁 play again"):
        st.session_state.clear()
        st.rerun()