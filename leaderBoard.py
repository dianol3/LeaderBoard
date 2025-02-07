import os
import base64
import requests
import time
import random
import pandas as pd
import streamlit as st
from datetime import datetime

# Função para tocar o áudio automaticamente
def autoplay_audio(audio_url: str):
    """Reproduz o áudio automaticamente usando a URL."""
    response = requests.get(audio_url)
    
    if response.status_code == 200:
        audio_data = base64.b64encode(response.content).decode()
        md = f"""
            <audio autoplay="true">
            <source src="data:audio/mp3;base64,{audio_data}" type="audio/mp3">
            </audio>
            """
        st.markdown(md, unsafe_allow_html=True)
    else:
        st.error("Não foi possível carregar o áudio.")
        
# Caminho do áudio hospedado no GitHub
audio_url = "https://raw.githubusercontent.com/dianol3/LeaderBoard/main/whistle.mp3.mp3"

# Usar a função para tocar o áudio
autoplay_audio(audio_url)

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
    # Criação do DataFrame vazio para armazenar os resultados
    st.session_state.penalty_data = pd.DataFrame(columns=["Indice", "Guarda-Redes", "Hora", "Resultado"])

# Configuração do layout em wide mode
st.set_page_config(layout="wide")

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

# Entrada dos nomes dos guarda-redes
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
col1, col2, col3 = st.columns([2, 2, 1])

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
        # Verde pastel para a primeira linha
        if row.name == 1:  # Verifica se é a primeira linha (Classificação 1)
            return ['background-color: #a8d5ba; color: #000000'] * len(row)  # Verde pastel e texto preto
        # Amarelo pastel para a linha do jogador
        elif row["Jogador"] == st.session_state.participant_name:
            return ['background-color: #f8e0a1; color: #000000'] * len(row)  # Amarelo pastel e texto preto
        return [''] * len(row)
    
    st.table(ranking_display.style.apply(highlight_row, axis=1))


with col2:
    st.subheader("GR")
    ranking_gk = get_gk_ranking()
    
    # Função para destacar a primeira linha dos guarda-redes
    def highlight_gk_row(row):
        # Verde pastel para a primeira linha
        if row.name == 1:  # Verifica se é a primeira linha (Classificação 1)
            return ['background-color: #a8d5ba; color: #000000'] * len(row)  # Verde pastel e texto preto
        return [''] * len(row)
    
    # Aplica o estilo na tabela dos guarda-redes
    st.table(ranking_gk.style.apply(highlight_gk_row, axis=1))


with col3:
    st.write(f"Participante: **{st.session_state.participant_name}**")
    st.write(f"Penalties realizados: **{st.session_state.penalties_taken}/{NUM_PENALTIES}**")
    
    selected_gk = st.selectbox("Escolha o Guarda-Redes que vai defender o penalty:", 
                               options=st.session_state.gk_names,
                               key=f"gk_select_{st.session_state.penalties_taken}")
    
    st.write("### Apitos")
    audio_path = "https://raw.githubusercontent.com/dianol3/LeaderBoard/main/whistle.mp3.mp3"


    if 'time_for_second_whistle' not in st.session_state:
        st.session_state.time_for_second_whistle = None

    if st.button("Tocar o Primeiro Apito", key=f"apito1_{st.session_state.penalties_taken}"):
        autoplay_audio(audio_path)
        st.session_state.time_for_second_whistle = time.time()
    
    if st.session_state.time_for_second_whistle:
        countdown_placeholder = st.empty()
        while True:
            elapsed_time = time.time() - st.session_state.time_for_second_whistle
            remaining_time = max(0, 10 - int(elapsed_time))
            countdown_placeholder.markdown(f"**{remaining_time} segundos**")
            if remaining_time <= 0:
                autoplay_audio(audio_path)
                del st.session_state.time_for_second_whistle
                break

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
        
        # Registra o resultado do penalty no DataFrame
        penalty_time = datetime.now().strftime("%H:%M:%S")  # Hora atual no formato HH:MM:SS
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
        # Salvar dados em CSV
        file_path = f"PenaltyTask_{st.session_state.participant_name}.csv"
        st.session_state.penalty_data.to_csv(file_path, index=False, sep=",")
        st.write(f"Resultados salvos em {file_path}.")
        st.stop()

    novo_registro = pd.DataFrame({
        "Guarda-Redes": [selected_gk],
        "Golo": [1 if result == "Sim" else 0]
    })
    st.session_state.penalty_results = novo_registro
