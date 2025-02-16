import streamlit as st
st.set_page_config(layout="wide")

import os
import random
import pandas as pd
from datetime import datetime


# Constantes
NUM_PENALTIES = 45
NUM_FICTITIOUS = 99
MAX_PLAYERS = 100

# Inicialização do estado da aplicação
if 'initialized' not in st.session_state:
    st.session_state.fictitious_ids = [f"P{random.randint(1, MAX_PLAYERS):03d}" for _ in range(NUM_FICTITIOUS)]
    st.session_state.fictitious_scores = [150] * NUM_FICTITIOUS
    st.session_state.participant_score = 150
    st.session_state.penalties_taken = 0
    # Esses valores serão usados para o ranking dos GR (a ordem de atualização é definida na ordem colhida)
    st.session_state.gk_scores = [150, 150, 150]
    st.session_state.gk_defeated = [0, 0, 0]
    st.session_state.initialized = True

if 'penalty_data' not in st.session_state:
    st.session_state.penalty_data = pd.DataFrame(columns=["Indice", "Guarda-Redes", "Hora", "Resultado"])

# 1. Formulário para entrada do nome do participante
if 'participant_name' not in st.session_state:
    with st.form("form_participant"):
        participant_name = st.text_input("Digite o nome do participante (Jogador):")
        submitted = st.form_submit_button("Enviar")
        if submitted:
            if participant_name.strip() == "":
                st.error("Nome não pode ser vazio!")
            else:
                st.session_state.participant_name = participant_name.strip()
                st.success(f"Bem-vindo, {st.session_state.participant_name}!")
    st.stop()

# 2. Formulário para entrada dos nomes dos Guarda-Redes
if 'gk_names' not in st.session_state:
    with st.form("form_gk"):
        st.write("Insira os nomes dos Guarda-Redes:")
        gk_a = st.text_input("Guarda-Redes Branco")
        gk_b = st.text_input("Guarda-Redes Azul")
        gk_c = st.text_input("Guarda-Redes Laranja")
        submitted = st.form_submit_button("Enviar")
        if submitted:
            if gk_a.strip() == "" or gk_b.strip() == "" or gk_c.strip() == "":
                st.error("Todos os nomes devem ser preenchidos!")
            else:
                st.session_state.gk_names = [gk_a.strip(), gk_b.strip(), gk_c.strip()]
                st.success("Guarda-redes definidos!")
    st.stop()

# 3. Formulário para colar a ordem dos GR (cada linha indica o GR para a vez)
if 'gk_order' not in st.session_state:
    with st.form("form_gk_order"):
        st.write("Cole a ordem dos GR (cada linha deve conter o nome do GR a ser utilizado na vez):")
        gk_order_input = st.text_area("Ordem dos GR", height=150)
        submitted = st.form_submit_button("Enviar")
        if submitted:
            if gk_order_input.strip() == "":
                st.error("A ordem não pode estar vazia!")
            else:
                st.session_state.gk_order = gk_order_input.strip().splitlines()
                st.success("Ordem dos GR definida!")
    st.stop()

# Exibição do Guarda-Redes atual e próximo
gk_order = st.session_state.gk_order
penalties_taken = st.session_state.penalties_taken

if gk_order:
    gk_atual = gk_order[penalties_taken % len(gk_order)]
    gk_proximo = gk_order[(penalties_taken + 1) % len(gk_order)]
    
    st.subheader(f"Agora: {gk_atual} | Próximo: {gk_proximo}")

# Funções para calcular os rankings
def get_player_ranking():
    all_scores = st.session_state.fictitious_scores + [st.session_state.participant_score]
    all_names = st.session_state.fictitious_ids + [st.session_state.participant_name]
    ranking_df = pd.DataFrame({"Jogador": all_names, "Pontos": all_scores})
    ranking_df.sort_values(by="Pontos", ascending=False, inplace=True)
    ranking_df["Classificação"] = range(1, len(ranking_df) + 1)
    ranking_df = ranking_df[["Classificação", "Jogador", "Pontos"]]
    return ranking_df

def get_gk_ranking():
    ranking_df = pd.DataFrame({
        "Guarda-Redes": st.session_state.gk_names,
        "Pontos": st.session_state.gk_scores,
        "Penalties Enfrentados": st.session_state.gk_defeated
    })
    ranking_df.sort_values(by="Pontos", ascending=False, inplace=True)
    ranking_df.reset_index(drop=True, inplace=True)
    ranking_df.index += 1
    return ranking_df
