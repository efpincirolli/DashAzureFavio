import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
from dash import dash_table, State
from flask import Flask
import plotly.graph_objs as go
import pandas as pd
import dash_auth
import dash_mantine_components as dmc
import plotly.express as px



#flask_server = Flask()
#app = dash.Dash(server=flask_server)
#server = app.server 
#----------------------
app = dash.Dash()
#----------------------
USERNAME_PASSWORD = pd.read_csv('USERNAME_PASSWORD.csv',encoding = 'UTF-8',delimiter=',')
user_pass = [[[USERNAME_PASSWORD.loc[i,"username"],USERNAME_PASSWORD.loc[i,"password"]]
              for i in range(len(USERNAME_PASSWORD))]][0]

#print(USERNAME_PASSWORD)
#print(user_pass)
auth = dash_auth.BasicAuth(app, user_pass)
server = app.server
#----------------------
#auth = dash_auth.BasicAuth(app, LISTA_USUARIOS)
#----------------------


#LECTURA DE DATOS FUENTE CSV
df_base = pd.read_csv('productos_20240909.csv',encoding = 'UTF-8',delimiter=',')
df_group_x_prov = df_base.groupby(["tipocanje","provincia"])["descripcion"].agg("count").to_frame(name ="sumaVentasProv").reset_index()

#DEFINO TABLA DE DATOS
dtable = dash_table.DataTable(
    columns=[{"name": i, "id": i} for i in sorted(df_base.columns)],
    sort_action="native",
    page_size=15,
    style_table={"overflowX": "auto"})

#DEFINO BOTON DE DOWNLOAD
download_button = html.Button("Export CSV", style={"marginTop": 20})
download_component = dcc.Download()

#DEFINICIÓN LAYOUT
app.layout = html.Div([
    html.Header([
        html.H1('Smile Dashboard', style={'color': 'white', 'backgroundColor': '#003366', 'textAlign': 'center', 'padding': '1em'})
    ]),
    html.Div([
        html.Div([
            html.H2('Dashboard de Articulos')], className='title'),
        html.Div([
            html.H3('Filtros'),
            # Aquí irán los componentes de filtro de Dash
            html.Div([
                    html.Label('Provincia: '),
                    dcc.Dropdown(id='selector',
                        options=[{'label': i, 'value': i} for i in df_group_x_prov['provincia'].unique()],
                        value='CABA'
                    )],style={'width': '48%', 'display': 'inline-block'}),

                    html.Div([
                    html.Label('Rango de fechas: '),
                    dcc.DatePickerRange(id='selector_fecha',start_date=df_base["fechaemision"].min(),end_date=df_base["fechaemision"].max())
                    ],style={'width': '48%', 'float': 'right', 'display': 'inline-block'}),
        ], className='filters'),
        
        html.Div([
            html.H3('Gráficos'),
            # Aquí irán los gráficos de Dash
            html.Div([
                    dcc.Graph(id='barplot_ventas_seg')
                    ],style={'width': '48%', 'float': 'left', 'display': 'inline-block'}),

                    html.Div([
                    dcc.Graph(id='barplot_beneficio_cat')
                    ],style={'width': '48%', 'float': 'center', 'display': 'inline-block'}),

                    html.Div([
                    dcc.Graph(id='lineplot_cantidad')
                    ],style={'width': '100%', 'float': 'center'}),
        ], className='graphs'),
        
        html.Div([
            html.H3('Grilla de Datos'),
            html.Div([
                    html.H4("Tabla de datos filtrados", style={"marginBottom": 20}),
                    download_component,
                    download_button,
                    dtable
                    ],style={'width': '90%','height': '100%','float': 'center'})
        ], className='data-grid')

    ], className='container'),
    html.Footer([
        html.P('© 2024 Indra Company', style={'color': 'white', 'backgroundColor': '#003366', 'textAlign': 'center', 'padding': '1em'})
    ])
])

# Callback para actualizar gráfico de Segmento en función del dropdown de PROVINCIA y según SELECTOR DE FECHAS
@app.callback(Output('barplot_ventas_seg', 'figure'),
              [Input('selector_fecha', 'start_date'),Input('selector_fecha', 'end_date'),Input('selector', 'value')])
def actualizar_graph_seg(fecha_min, fecha_max, seleccion):
    filtered_df = df_base[(df_base["fechaemision"]>=fecha_min) & (df_base["fechaemision"]<=fecha_max) & (df_base["provincia"]==seleccion)]

# CREACIÓN DE GRÁFICOS Y GROUPBY
    df_group_x_prov = filtered_df.groupby(["tipocanje","provincia"])["descripcion"].agg("count").to_frame(name ="cantidadVentasProv").reset_index()

    return{
        'data': [go.Bar(x=df_group_x_prov["tipocanje"],
                        y=df_group_x_prov["cantidadVentasProv"],
                        marker=dict(color="MediumPurple")
                            )],
        'layout': go.Layout(
            title="Cantidad de productos canjeados X Tipo de producto",
            xaxis={'title': "Provincia :"},
            yaxis={'title': "Cantidad de Ventas"},
            hovermode='closest'
            
        )}

# Callback para actualizar gráfico de Segmento en función del dropdown de País y según selector de fechas
@app.callback(Output('barplot_beneficio_cat', 'figure'),
              [Input('selector_fecha', 'start_date'),Input('selector_fecha', 'end_date')])
def actualizar_graph_seg(fecha_min, fecha_max):
    filtered_df = df_base[(df_base["fechaemision"]>=fecha_min) & (df_base["fechaemision"]<=fecha_max)]

# CREACIÓN DE GRÁFICOS Y GROUPBY
    df_group_x_prov = filtered_df.groupby(["provincia","fechaemision"])["descripcion"].agg("count").to_frame(name ="sumaVentasProv").reset_index()

    return{
        'data': [go.Bar(x=df_group_x_prov["provincia"],
                            y=df_group_x_prov["sumaVentasProv"]
                            )],
        'layout': go.Layout(
            title="¿Suma total de canjes por provincia?",
            xaxis={'title': "Provincia"},
            yaxis={'title': "Monto Total de Ventas"},
            hovermode='closest'
        )}

@app.callback(Output("lineplot_cantidad", "figure"), 
            [Input('selector_fecha', 'start_date'),
             Input('selector_fecha', 'end_date')])
             
def update_line_chart(fecha_min, fecha_max):
    filtered_df = df_base[(df_base["fechaemision"]>=fecha_min) & (df_base["fechaemision"]<=fecha_max)]
    df_group_x_prov = filtered_df.groupby(["provincia","fechaemision"])["descripcion"].agg("count").to_frame(name ="sumaVentasProv").reset_index()
    fig = px.line(df_group_x_prov, x="fechaemision", y="sumaVentasProv", color="provincia")
    return fig


@app.callback(Output(dtable, "data"),
            [Input('selector_fecha', 'start_date'),
             Input('selector_fecha', 'end_date'),
             Input('selector', 'value')])

def update_table(fecha_min, fecha_max, seleccion):
    filtered_df = df_base[(df_base["fechaemision"]>=fecha_min) & (df_base["fechaemision"]<=fecha_max) & (df_base["provincia"]==seleccion)]
    return filtered_df.to_dict("records")

@app.callback(
    Output(download_component, "data"),
    Input(download_button, "n_clicks"),
    State(dtable, "derived_virtual_data"),
    prevent_initial_call=True,
)
def download_data(n_clicks, data):
    filtered_df = pd.DataFrame(data)
    return dcc.send_data_frame(filtered_df.to_csv, "filtered_csv.csv")
    
if __name__ == '__main__':
    app.run_server()