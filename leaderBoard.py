import os
import random
import pandas as pd
import streamlit as st
from datetime import datetime

st.set_page_config(layout="wide")

# Inicialização do estado da aplicação
NUM_PENALTIES = 45
NUM_FICTITIOUS = 99
MAX_PLAYERS = 100

if 'initialized' not in st.session_state:
    st.session_state.fictitious_ids = [f"P{random.randint(1, MAX_PLAYERS):03d}" for _ in range(NUM_FICTITIOUS)]
    st.session_state.fictitious_scores = [150] * NUM_FICTITIOUS
    st.session_state.participant_score = 150
    st.session_state.penalties_taken = 0
    st.session_state.gk_scores = [150, 150, 150]
    st.session_state.gk_defeated = [0, 0, 0]
    st.session_state.initialized = True

if 'penalty_data' not in st.session_state:
    st.session_state.penalty_data = pd.DataFrame(columns=["Indice", "Guarda-Redes", "Hora", "Resultado"])

# Entrada do nome do participante
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

# Entrada para a sequência dos Guarda-Redes
if 'gk_sequence' not in st.session_state:
    with st.form("form_gk_sequence"):
        st.write("Cole a sequência de Guarda-Redes (separada por quebras de linha):")
        gk_sequence = st.text_area("Sequência de GRs", height=150)
        submitted = st.form_submit_button("Enviar")
        if submitted:
            if gk_sequence.strip() == "":
                st.error("A sequência não pode estar vazia!")
            else:
                st.session_state.gk_sequence = gk_sequence.strip().split("\n")
                st.success(f"Sequência de Guarda-Redes definida! {len(st.session_state.gk_sequence)} GRs na sequência.")
    st.stop()

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

# Exibição dos Rankings Lado a Lado
col1, col2 = st.columns(2)

with col1:
    st.subheader("Jogadores")
    ranking_players = get_player_ranking()
    empty_row = pd.DataFrame([["", "", ""]], columns=ranking_players.columns)
    top_10 = ranking_players.head(10)
    participant_row = ranking_players[ranking_players["Jogador"] == st.session_state.participant_name]
    if participant_row["Classificação"].values[0] > 10:
        ranking_display = pd.concat([top_10, empty_row, participant_row])
    else:
        ranking_display = top_10
    ranking_display = ranking_display.set_index("Classificação")
    
    def highlight_row(row):
        if row.name == 1:
            return ['background-color: #a8d5ba; color: #000000'] * len(row)
        elif row["Jogador"] == st.session_state.participant_name:
            return ['background-color: #f8e0a1; color: #000000'] * len(row)
        return [''] * len(row)
    
    st.table(ranking_display.style.apply(highlight_row, axis=1))

with col2:
    st.subheader("GR")
    
    # Se houver sequência de GRs, mostrar quem é o próximo
    if len(st.session_state.gk_sequence) > 0:
        current_gk = st.session_state.gk_sequence[st.session_state.penalties_taken % len(st.session_state.gk_sequence)]
        st.write(f"**Guarda-Redes a seguir**: {current_gk}")
        
    st.write(f"Participante: **{st.session_state.participant_name}**")
    st.write(f"Penalties realizados: **{st.session_state.penalties_taken}/{NUM_PENALTIES}**")
    
    # Seleção do guarda-redes a partir da sequência
    selected_gk = current_gk

    result = st.radio("O jogador marcou o penalty?", ("Sim", "Não"), key=f"result_{st.session_state.penalties_taken}")

    if st.button("Confirmar Penalty", key=f"confirm_{st.session_state.penalties_taken}"):
        gk_index = st.session_state.gk_names.index(selected_gk)
        
        if result == "Sim":
            st.session_state.participant_score += 2
            st.session_state.gk_scores[gk_index] -= 2
        else:
            st.session_state.participant_score -= 8
            st.session_state.gk_scores[gk_index] += 8
        st.session_state.gk_defeated[gk_index] += 1

        for i in range(NUM_FICTITIOUS):
            if random.random() < 0.8:
                st.session_state.fictitious_scores[i] += 2
            else:
                st.session_state.fictitious_scores[i] -= 8
        
        penalty_time = datetime.now().strftime("%H:%M:%S")
        result_value = 1 if result == "Sim" else 0
        penalty_record = pd.DataFrame([{
            "Indice": st.session_state.penalties_taken + 1,
            "Guarda-Redes": selected_gk,
            "Hora": penalty_time,
            "Resultado": "Golo" if result_value == 1 else "Falhou"
        }])
        st.session_state.penalty_data = pd.concat([st.session_state.penalty_data, penalty_record], ignore_index=True)
        
        st.session_state.penalties_taken += 1

    if st.session_state.penalties_taken >= NUM_PENALTIES:
        st.write("### Fim do Jogo!")
        st.write(f"Você completou todos os {NUM_PENALTIES} penalties.")
        file_path = f"/tmp/PenaltyTask_{st.session_state.participant_name}.csv"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        st.session_state.penalty_data.to_csv(file_path, index=False, sep=",")
    
        with open(file_path, "r") as f:
            st.download_button(
                label="Download Resultados",
                data=f,
                file_name=f"PenaltyTask_{st.session_state.participant_name}.csv",
                mime="text/csv"
            )
        st.stop()
