import os
import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plotly.graph_objects as go

# --- 1️⃣ Caminho dinâmico do CSV ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
arquivo = os.path.join(BASE_DIR, "Previsao_Jogos.csv")

df = pd.read_csv(arquivo, sep=';')

# Garantir que Data seja string para o dropdown
df['Data'] = df['Data'].astype(str)

# Se Horario for numérico, formatar como "HH:00"
if pd.api.types.is_numeric_dtype(df['Horario']):
    df['Horario'] = df['Horario'].astype(str) + ":00"

# --- 2️⃣ Criar coluna com jogo (Casa x Fora) ---
df['Jogo'] = df['Time_Casa'] + ' x ' + df['Time_Fora']

# --- 3️⃣ Inicializar app ---
app = Dash(__name__)
server = app.server  # necessário para Render/Gunicorn
app.title = 'Dashboard de Previsão de Jogos'

# --- 4️⃣ Layout ---
app.layout = html.Div([
    html.H1("Dashboard de Previsão de Jogos", style={'textAlign':'center'}),
    
    html.Div([
        html.Label("Escolha a Data:"),
        dcc.Dropdown(
            id='filtro_data',
            options=[{'label': x, 'value': x} for x in sorted(df['Data'].unique())],
            placeholder="Selecione a data"
        ),
        
        html.Label("Escolha o Campeonato:"),
        dcc.Dropdown(id='filtro_campeonato', placeholder="Selecione o campeonato"),
        
        html.Label("Escolha o Horário:"),
        dcc.Dropdown(id='filtro_horario', placeholder="Selecione o horário"),
        
        html.Label("Escolha o Jogo:"),
        dcc.Dropdown(id='filtro_jogo', placeholder="Selecione o jogo"),
    ], style={'width':'30%', 'display':'inline-block', 'verticalAlign':'top'}),
    
    html.Div([
        html.H2("Previsões", style={'textAlign':'center'}),
        dcc.Graph(id='grafico_prev'),
        html.H3("Alertas", style={'textAlign':'center'}),
        html.Div(id='alertas', style={'fontSize':20, 'textAlign':'center', 'color':'red'})
    ], style={'width':'65%', 'display':'inline-block', 'marginLeft':'5%'})
])

# --- 5️⃣ Callbacks em cascata ---
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
    jogos = df[
        (df['Data']==data_selecionada) & 
        (df['Liga']==campeonato) & 
        (df['Horario']==horario)
    ]['Jogo'].unique()
    return [{'label': x, 'value': x} for x in jogos]

@app.callback(
    Output('grafico_prev', 'figure'),
    Output('alertas', 'children'),
    Input('filtro_jogo', 'value')
)
def atualizar_dashboard(jogo_selecionado):
    if not jogo_selecionado:
        return go.Figure(), ""
    
    linha = df[df['Jogo']==jogo_selecionado].iloc[0]
    
    # Gráfico com barras comparando Casa x Fora
    categorias = ['Gols', 'Escanteios', 'Chutes', 'Chutes no Alvo']
    casa_valores = [
        linha['Prev_Goals_FT_Casa'],
        linha['Prev_Corners_FT_Casa'],
        linha['Prev_Shots_Casa'],
        linha['Prev_ShotsOnTarget_Casa']
    ]
    fora_valores = [
        linha['Prev_Goals_FT_Fora'],
        linha['Prev_Corners_FT_Fora'],
        linha['Prev_Shots_Fora'],
        linha['Prev_ShotsOnTarget_Fora']
    ]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Casa', x=categorias, y=casa_valores, marker_color='blue'))
    fig.add_trace(go.Bar(name='Fora', x=categorias, y=fora_valores, marker_color='orange'))
    fig.update_layout(barmode='group', title=f"Previsões - {jogo_selecionado}")
    
    # Alertas
    msgs = []
    if linha['Prev_Goals_FT_Casa'] + linha['Prev_Goals_FT_Fora'] > 1.5:
        msgs.append('Mais de 1,5 Gols')
    if linha['Prev_Corners_FT_Casa'] + linha['Prev_Corners_FT_Fora'] > 7.5:
        msgs.append('Mais de 7,5 Escanteios')
    if linha['Prev_Shots_Casa'] > 12:
        msgs.append('Chutes Casa Altos')
    if linha['Prev_Shots_Fora'] > 12:
        msgs.append('Chutes Fora Altos')
    if linha['Prev_ShotsOnTarget_Casa'] > 5:
        msgs.append('Chutes no Alvo Casa Altos')
    if linha['Prev_ShotsOnTarget_Fora'] > 5:
        msgs.append('Chutes no Alvo Fora Altos')
    
    alerta_final = ', '.join(msgs) if msgs else 'Normal'
    
    return fig, alerta_final

# --- 6️⃣ Rodar app ---
if __name__ == '__main__':
    app.run_server()
