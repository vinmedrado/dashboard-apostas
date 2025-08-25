import os
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

# --- 1️⃣ Caminho relativo dos arquivos ---
BASE_DIR = os.path.dirname(__file__)
ARQUIVO_XLSM = os.path.join(BASE_DIR, "Aposta.xlsm")
ARQUIVO_CSV = os.path.join(BASE_DIR, "Previsao_Jogos.csv")

# --- 2️⃣ Ler abas ---
tbl_jogos = pd.read_excel(ARQUIVO_XLSM, sheet_name="tblJogos", engine='openpyxl')
base_ml   = pd.read_excel(ARQUIVO_XLSM, sheet_name="Base ML", engine='openpyxl')

# --- 3️⃣ Função para calcular médias móveis ---
def medias_moveis(df, time, coluna, jogos=[5,10,15]):
    historico = df[df['Time'] == time].sort_values('Date', ascending=False)
    medias = {}
    for n in jogos:
        medias[f'{coluna}_Media{n}'] = historico[coluna].head(n).mean() if not historico.empty else 0
    return medias

# --- 4️⃣ Estatísticas a prever ---
estatisticas = ['Goals_FT', 'Shots', 'ShotsOnTarget', 'Corners_FT']

# --- 5️⃣ Preparar features para cada jogo ---
def gerar_features_jogo(jogo, base):
    casa = jogo['Home']
    fora = jogo['Away']
    features = {}
    
    # Média móvel para o time da casa
    for e in estatisticas:
        medias_casa = medias_moveis(base, casa, e)
        features.update({f'Casa_{k}': v for k,v in medias_casa.items()})
    
    # Média móvel para o time visitante
    for e in estatisticas:
        medias_fora = medias_moveis(base, fora, e)
        features.update({f'Fora_{k}': v for k,v in medias_fora.items()})
    
    # Info do jogo
    features['Time_Casa'] = casa
    features['Time_Fora'] = fora
    features['Liga'] = jogo['League']
    features['Data'] = jogo['Date']
    features['Horario'] = jogo['Hours']
    
    return features

# --- 6️⃣ Criar dataset final para os jogos do dia ---
lista_features = [gerar_features_jogo(j, base_ml) for idx, j in tbl_jogos.iterrows()]
df_final = pd.DataFrame(lista_features)

# --- 7️⃣ Treinar modelo e prever cada estatística ---
for e in estatisticas:
    X, y = [], []
    for t in base_ml['Time'].unique():
        hist = base_ml[base_ml['Time']==t].sort_values('Date')
        if len(hist) < 5:
            continue
        feat = [hist[e].tail(n).mean() for n in [5,10,15]]
        X.append(feat)
        y.append(hist[e].iloc[-1])
    
    if not X:
        continue
    
    modelo = RandomForestRegressor(n_estimators=100, random_state=42)
    modelo.fit(X, y)
    
    # Previsão para jogos do dia
    previsao_casa = [modelo.predict([[row[f'Casa_{e}_Media{n}'] for n in [5,10,15]]])[0] 
                     for idx, row in df_final.iterrows()]
    previsao_fora = [modelo.predict([[row[f'Fora_{e}_Media{n}'] for n in [5,10,15]]])[0] 
                     for idx, row in df_final.iterrows()]
    
    df_final[f'Prev_{e}_Casa'] = previsao_casa
    df_final[f'Prev_{e}_Fora'] = previsao_fora

# --- 8️⃣ Criar alertas ---
alertas = []
for idx, row in df_final.iterrows():
    msgs = []
    if row['Prev_Goals_FT_Casa'] + row['Prev_Goals_FT_Fora'] > 1.5:
        msgs.append('Mais de 1,5 Gols')
    if row['Prev_Corners_FT_Casa'] + row['Prev_Corners_FT_Fora'] > 7.5:
        msgs.append('Mais de 7,5 Escanteios')
    if row['Prev_Shots_Casa'] > 12:
        msgs.append('Chutes Casa Altos')
    if row['Prev_Shots_Fora'] > 12:
        msgs.append('Chutes Fora Altos')
    if row['Prev_ShotsOnTarget_Casa'] > 5:
        msgs.append('Chutes no Alvo Casa Altos')
    if row['Prev_ShotsOnTarget_Fora'] > 5:
        msgs.append('Chutes no Alvo Fora Altos')
    
    alertas.append(', '.join(msgs) if msgs else 'Normal')

df_final['Alerta'] = alertas

# --- 9️⃣ Salvar CSV fixo para BI ---
df_final.to_csv(ARQUIVO_CSV, index=False, sep=';')

print(f"✅ Previsões geradas e salvas em: {ARQUIVO_CSV}")
