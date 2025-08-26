import os
import pandas as pd
from dash import Dash, dcc, html, Input, Output

# --- Caminho do CSV ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
arquivo = os.path.join(BASE_DIR, "Previsao_Jogos.csv")

df = pd.read_csv(arquivo, sep=';')
df['Data'] = df['Data'].astype(str)
if pd.api.types.is_numeric_dtype(df['Horario']):
    df['Horario'] = df['Horario'].astype(str) + ":00"
df['Jogo'] = df['Time_Casa'] + ' x ' + df['Time_Fora']

# --- Inicializar app ---
app = Dash(__name__)
app.title = 'Dashboard de Apostas'

# --- Layout ---
app.layout = html.Div(style={'fontFamily':'Arial, sans-serif', 'backgroundColor':'#1E1E2F', 'color':'#fff', 'minHeight':'100vh', 'padding':'20px'}, children=[
    html.H1("Dashboard de Apostas", style={'textAlign':'center', 'color':'#FFDC00'}),
    
    html.Div([
        html.Label("Data", style={'marginTop':'10px', 'color':'#fff'}),
        dcc.Dropdown(id='filtro_data', options=[{'label': x, 'value': x} for x in sorted(df['Data'].unique())],
                     placeholder="Selecione a data",
                     style={'borderRadius':'10px','backgroundColor':'#E0E0E0','color':'#000','fontWeight':'bold'}),
        
        html.Label("Campeonato", style={'marginTop':'10px','color':'#fff'}),
        dcc.Dropdown(id='filtro_campeonato', placeholder="Selecione o campeonato",
                     style={'borderRadius':'10px','backgroundColor':'#E0E0E0','color':'#000','fontWeight':'bold'}),
        
        html.Label("Horário", style={'marginTop':'10px','color':'#fff'}),
        dcc.Dropdown(id='filtro_horario', placeholder="Selecione o horário",
                     style={'borderRadius':'10px','backgroundColor':'#E0E0E0','color':'#000','fontWeight':'bold'}),
        
        html.Label("Jogo", style={'marginTop':'10px','color':'#fff'}),
        dcc.Dropdown(id='filtro_jogo', placeholder="Selecione o jogo",
                     style={'borderRadius':'10px','backgroundColor':'#E0E0E0','color':'#000','fontWeight':'bold'}),
    ], style={'maxWidth':'400px', 'margin':'auto'}),
    
    html.Div(id='cards_container', style={'marginTop':'20px'})
])

# --- Callbacks em cascata ---
@app.callback(
    Output('filtro_campeonato', 'options'),
    Input('filtro_data', 'value')
)
def atualizar_campeonatos(data_selecionada):
    if not data_selecionada:
        return []
    campeonatos = sorted(df[df['Data']==data_selecionada]['Liga'].unique())
    return [{'label': x, 'value': x} for x in campeonatos]

@app.callback(
    Output('filtro_horario', 'options'),
    Input('filtro_data', 'value'),
    Input('filtro_campeonato', 'value')
)
def atualizar_horarios(data_selecionada, campeonato):
    if not data_selecionada or not campeonato:
        return []
    horarios = sorted(df[(df['Data']==data_selecionada) & (df['Liga']==campeonato)]['Horario'].unique())
    return [{'label': x, 'value': x} for x in horarios]

@app.callback(
    Output('filtro_jogo', 'options'),
    Input('filtro_data', 'value'),
    Input('filtro_campeonato', 'value'),
    Input('filtro_horario', 'value')
)
def atualizar_jogos(data_selecionada, campeonato, horario):
    if not data_selecionada or not campeonato or not horario:
        return []
    jogos = df[(df['Data']==data_selecionada) & (df['Liga']==campeonato) & (df['Horario']==horario)]['Jogo'].unique()
    return [{'label': x, 'value': x} for x in jogos]

# --- Funções auxiliares ---
def cor_aposta(tipo, valor):
    if tipo == 'gols' and valor >= 1.5:
        return '#2ECC40'
    if tipo == 'chutes' and valor >= 8:
        return '#2ECC40'
    if tipo == 'escanteios' and valor >= 7.5:
        return '#2ECC40'
    return '#FF4136'  # caso abaixo do limite

def seta_tendencia(valores):
    setas = []
    for i in range(len(valores)):
        if i == 0:
            setas.append("→")
        else:
            diff = valores[i] - valores[i-1]
            if abs(diff) < 0.05:
                setas.append("→")
            elif diff > 0:
                setas.append("↑")
            else:
                setas.append("↓")
    return setas

# --- Atualizar cards ---
@app.callback(
    Output('cards_container', 'children'),
    Input('filtro_jogo', 'value')
)
def atualizar_cards(jogo_selecionado):
    if not jogo_selecionado:
        return html.Div("Selecione os filtros para visualizar o jogo.", style={'textAlign':'center', 'padding':'20px'})
    
    linha = df[df['Jogo']==jogo_selecionado].iloc[0]

    # --- Alertas ---
    msgs = []
    if linha['Prev_Goals_FT_Casa'] + linha['Prev_Goals_FT_Fora'] > 1.5: msgs.append("Mais de 1,5 Gols")
    if linha['Prev_Corners_FT_Casa'] + linha['Prev_Corners_FT_Fora'] > 7.5: msgs.append("Mais de 7,5 Escanteios")
    if linha['Prev_Shots_Casa'] > 12: msgs.append("Chutes Casa Altos")
    if linha['Prev_Shots_Fora'] > 12: msgs.append("Chutes Fora Altos")
    if linha['Prev_ShotsOnTarget_Casa'] > 5: msgs.append("Chutes no Alvo Casa Altos")
    if linha['Prev_ShotsOnTarget_Fora'] > 5: msgs.append("Chutes no Alvo Fora Altos")
    alerta_final = ', '.join(msgs) if msgs else "Normal"

    alert_card = html.Div(style={'backgroundColor':'#FF4136','borderRadius':'15px','padding':'15px','textAlign':'center','marginBottom':'20px'}, children=[
        html.H3("Alertas", style={'color':'#fff'}),
        html.P(alerta_final, style={'color':'#fff','fontWeight':'bold','fontSize':'16px'})
    ])

    # --- Estatísticas ---
    estatisticas = [
        ("Gols Casa", ['Casa_Goals_FT_Media5','Casa_Goals_FT_Media10','Casa_Goals_FT_Media15'],'gols'),
        ("Gols Fora", ['Fora_Goals_FT_Media5','Fora_Goals_FT_Media10','Fora_Goals_FT_Media15'],'gols'),
        ("Chutes Casa", ['Casa_Shots_Media5','Casa_Shots_Media10','Casa_Shots_Media15'],'chutes'),
        ("Chutes Fora", ['Fora_Shots_Media5','Fora_Shots_Media10','Fora_Shots_Media15'],'chutes'),
        ("Chutes ao Alvo Casa", ['Casa_ShotsOnTarget_Media5','Casa_ShotsOnTarget_Media10','Casa_ShotsOnTarget_Media15'],'chutes'),
        ("Chutes ao Alvo Fora", ['Fora_ShotsOnTarget_Media5','Fora_ShotsOnTarget_Media10','Fora_ShotsOnTarget_Media15'],'chutes'),
        ("Escanteios Casa", ['Casa_Corners_FT_Media5','Casa_Corners_FT_Media10','Casa_Corners_FT_Media15'],'escanteios'),
        ("Escanteios Fora", ['Fora_Corners_FT_Media5','Fora_Corners_FT_Media10','Fora_Corners_FT_Media15'],'escanteios')
    ]

    cards = []
    for nome, colunas, tipo in estatisticas:
        valores = [round(linha[col],2) for col in colunas]
        setas = seta_tendencia(valores)
        cards.append(html.Div(style={'backgroundColor':'#2E2E3E','borderRadius':'15px','padding':'15px','textAlign':'center'}, children=[
            html.H4(nome, style={'color':'#7FDBFF'}),
            html.P(f"Últimos 5 jogos: {valores[0]} {setas[0]}", style={'color': cor_aposta(tipo, valores[0]), 'fontWeight':'bold'}),
            html.P(f"Últimos 10 jogos: {valores[1]} {setas[1]}", style={'color': cor_aposta(tipo, valores[1]), 'fontWeight':'bold'}),
            html.P(f"Últimos 15 jogos: {valores[2]} {setas[2]}", style={'color': cor_aposta(tipo, valores[2]), 'fontWeight':'bold'})
        ]))

    return html.Div([alert_card, html.Div(style={'display':'grid','gridTemplateColumns':'repeat(auto-fit,minmax(250px,1fr))','gap':'20px'}, children=cards)])

# --- Rodar app ---
if __name__ == '__main__':
    app.run(debug=True)




