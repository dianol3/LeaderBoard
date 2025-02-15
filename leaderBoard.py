import os
import random
import pandas as pd
import streamlit as st
from datetime import datetime

st.set_page_config(layout="wide")

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
        # Verde pastel para a primeira linha
        if row.name == 1:
            return ['background-color: #a8d5ba; color: #000000'] * len(row)
        # Amarelo pastel para a linha do participante
        elif row["Jogador"] == st.session_state.participant_name:
            return ['background-color: #f8e0a1; color: #000000'] * len(row)
        return [''] * len(row)
    
    st.table(ranking_display.style.apply(highlight_row, axis=1))

with col2:
    st.subheader("GR")
    ranking_gk = get_gk_ranking()
    
    # Função para destacar a primeira linha dos GR
    def highlight_gk_row(row):
        if row.name == 1:
            return ['background-color: #a8d5ba; color: #000000'] * len(row)
        return [''] * len(row)
    
    st.table(ranking_gk.style.apply(highlight_gk_row, axis=1))
    
    st.write(f"Participante: **{st.session_state.participant_name}**")
    st.write(f"Penalties realizados: **{st.session_state.penalties_taken}/{NUM_PENALTIES}**")
    
    # Seleção automática do GR com base na ordem colada
    gk_order = st.session_state.gk_order
    # Utiliza o índice da penalidade para definir qual GR usar (cíclico, se necessário)
    selected_gk = gk_order[(st.session_state.penalties_taken + 1) % len(gk_order)]
    st.write(f"**Guarda-Redes a seguir:** {selected_gk}")
    
    result = st.radio("O jogador marcou o penalty?", ("Sim", "Não"), key=f"result_{st.session_state.penalties_taken}")
    
    if st.button("Confirmar Penalty", key=f"confirm_{st.session_state.penalties_taken}"):
        try:
            gk_index = st.session_state.gk_names.index(selected_gk)
        except ValueError:
            st.error(f"O GR '{selected_gk}' não está entre os nomes definidos!")
            st.stop()
        
        if result == "Sim":
            st.session_state.participant_score += 2
            st.session_state.gk_scores[gk_index] -= 2
        else:
            st.session_state.participant_score -= 8
            st.session_state.gk_scores[gk_index] += 8
        st.session_state.gk_defeated[gk_index] += 1

        # Atualiza as pontuações fictícias
        for i in range(NUM_FICTITIOUS):
            if random.random() < 0.8:
                st.session_state.fictitious_scores[i] += 2
            else:
                st.session_state.fictitious_scores[i] -= 8
        
        # Registra o resultado do penalty
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
        
        # Salva os dados em um CSV para download
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

    novo_registro = pd.DataFrame({
        "Guarda-Redes": [selected_gk],
        "Golo": [1 if result == "Sim" else 0]
    })
    st.session_state.penalty_results = novo_registro
