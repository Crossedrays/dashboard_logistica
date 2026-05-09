import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os

# ─────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────
st.set_page_config(
    page_title='Dashboard Producción',
    page_icon='🏭',
    layout='wide',
    initial_sidebar_state='expanded'
)

st.markdown("""
<style>
    [data-testid="stMetricValue"] { font-size: 1.6rem; font-weight: 700; }
    [data-testid="stMetricDelta"] { font-size: 0.85rem; }
    .section-title { font-size: 1.1rem; font-weight: 600; color: #1f4e79;
                     border-left: 4px solid #1f4e79; padding-left: 10px; margin: 1rem 0 0.5rem 0; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DATOS
# ─────────────────────────────────────────────
@st.cache_data
def cargar_datos():
    ruta = os.path.join(os.path.dirname(__file__), 'caso3_produccion_dataset.csv')
    df = pd.read_csv(ruta)
    df['fecha_produccion'] = pd.to_datetime(df['fecha_produccion'])
    df['mes'] = df['fecha_produccion'].dt.to_period('M').astype(str)
    df['unidades_buenas'] = df['unidades_producidas'] - df['unidades_defectuosas']
    return df

df = cargar_datos()

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
st.sidebar.title('🏭 Filtros')

lineas = ['Todas'] + sorted(df['linea_produccion'].unique())
linea_sel = st.sidebar.multiselect('📋 Línea de producción', df['linea_produccion'].unique(),
                                    default=df['linea_produccion'].unique())

turnos = ['Todos'] + sorted(df['turno'].unique())
turno_sel = st.sidebar.multiselect('🕐 Turno', df['turno'].unique(),
                                    default=df['turno'].unique())

productos = sorted(df['producto'].unique())
producto_sel = st.sidebar.multiselect('🔩 Producto', productos, default=productos)

maquinas = sorted(df['maquina'].unique())
maquina_sel = st.sidebar.multiselect('⚙️ Máquina', maquinas, default=maquinas)

st.sidebar.markdown('---')
fecha_min = df['fecha_produccion'].min().date()
fecha_max = df['fecha_produccion'].max().date()
fecha_rango = st.sidebar.date_input('📅 Rango de fechas', [fecha_min, fecha_max],
                                     min_value=fecha_min, max_value=fecha_max)

# Aplicar filtros
dff = df[
    df['linea_produccion'].isin(linea_sel) &
    df['turno'].isin(turno_sel) &
    df['producto'].isin(producto_sel) &
    df['maquina'].isin(maquina_sel)
]
if len(fecha_rango) == 2:
    dff = dff[
        (dff['fecha_produccion'].dt.date >= fecha_rango[0]) &
        (dff['fecha_produccion'].dt.date <= fecha_rango[1])
    ]

# ─────────────────────────────────────────────
# ENCABEZADO
# ─────────────────────────────────────────────
st.title('🏭 Dashboard de Producción Industrial')
st.caption(f'Mostrando {len(dff)} órdenes de producción · {dff["fecha_produccion"].min().strftime("%d/%m/%Y") if len(dff) else "—"} → {dff["fecha_produccion"].max().strftime("%d/%m/%Y") if len(dff) else "—"}')
st.markdown('---')

if len(dff) == 0:
    st.warning('No hay datos con los filtros seleccionados.')
    st.stop()

# ─────────────────────────────────────────────
# KPIs PRINCIPALES
# ─────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)

eficiencia_prom  = dff['eficiencia_pct'].mean()
defectos_prom    = dff['tasa_defectos_pct'].mean()
unidades_prod    = dff['unidades_producidas'].sum()
paro_prom        = dff['tiempo_paro_min'].mean()
costo_total      = dff['costo_produccion_cop'].sum()

k1.metric('⚡ Eficiencia Promedio',   f'{eficiencia_prom:.1f}%')
k2.metric('🔴 Tasa Defectos Prom.',   f'{defectos_prom:.1f}%')
k3.metric('📦 Unidades Producidas',   f'{unidades_prod:,}')
k4.metric('⏱️ Paro Promedio (min)',    f'{paro_prom:.1f}')
k5.metric('💰 Costo Total (COP)',      f'${costo_total/1e6:.1f}M')

st.markdown('---')

# ═══════════════════════════════════════════
# SECCIÓN 1 — EFICIENCIA Y DEFECTOS
# ═══════════════════════════════════════════
st.markdown('<div class="section-title">📊 Eficiencia y Calidad por Variable</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(['Por Línea', 'Por Turno', 'Por Máquina', 'Por Producto'])

def graf_eficiencia_defectos(grupo, titulo_grupo):
    agg = dff.groupby(grupo).agg(
        eficiencia=('eficiencia_pct', 'mean'),
        defectos=('tasa_defectos_pct', 'mean'),
        ordenes=('id_orden', 'count')
    ).reset_index().round(2)

    fig = go.Figure()
    fig.add_bar(name='Eficiencia (%)', x=agg[grupo], y=agg['eficiencia'],
                marker_color='#1f77b4', text=agg['eficiencia'].map('{:.1f}%'.format),
                textposition='outside')
    fig.add_bar(name='Tasa Defectos (%)', x=agg[grupo], y=agg['defectos'],
                marker_color='#d62728', text=agg['defectos'].map('{:.1f}%'.format),
                textposition='outside')
    fig.update_layout(barmode='group', title=f'Eficiencia vs Defectos por {titulo_grupo}',
                      yaxis_title='%', legend=dict(orientation='h', y=1.12),
                      height=380)
    return fig

with tab1:
    st.plotly_chart(graf_eficiencia_defectos('linea_produccion', 'Línea'), use_container_width=True)
with tab2:
    st.plotly_chart(graf_eficiencia_defectos('turno', 'Turno'), use_container_width=True)
with tab3:
    st.plotly_chart(graf_eficiencia_defectos('maquina', 'Máquina'), use_container_width=True)
with tab4:
    st.plotly_chart(graf_eficiencia_defectos('producto', 'Producto'), use_container_width=True)

# ═══════════════════════════════════════════
# SECCIÓN 2 — EVOLUCIÓN TEMPORAL
# ═══════════════════════════════════════════
st.markdown('<div class="section-title">📅 Evolución Mensual</div>', unsafe_allow_html=True)

metrica_tiempo = st.selectbox('Variable a graficar en el tiempo:', [
    ('eficiencia_pct', 'Eficiencia (%)'),
    ('tasa_defectos_pct', 'Tasa de Defectos (%)'),
    ('tiempo_paro_min', 'Tiempo de Paro (min)'),
    ('consumo_energia_kwh', 'Consumo de Energía (kWh)'),
    ('costo_produccion_cop', 'Costo de Producción (COP)'),
], format_func=lambda x: x[1])

col_var, col_agg_by = st.columns(2)
with col_var:
    color_by = st.selectbox('Desglosar por:', ['(ninguno)', 'linea_produccion', 'turno', 'producto', 'maquina'],
                             format_func=lambda x: {'(ninguno)': 'Sin desglose', 'linea_produccion': 'Línea',
                                                    'turno': 'Turno', 'producto': 'Producto', 'maquina': 'Máquina'}.get(x, x))

campo, etiqueta = metrica_tiempo

if color_by == '(ninguno)':
    evol = dff.groupby('mes')[campo].mean().reset_index()
    fig_evol = px.line(evol, x='mes', y=campo, markers=True,
                       title=f'Evolución mensual · {etiqueta}',
                       labels={'mes': 'Mes', campo: etiqueta})
else:
    evol = dff.groupby(['mes', color_by])[campo].mean().reset_index()
    etiq_color = {'linea_produccion': 'Línea', 'turno': 'Turno',
                  'producto': 'Producto', 'maquina': 'Máquina'}.get(color_by, color_by)
    fig_evol = px.line(evol, x='mes', y=campo, color=color_by, markers=True,
                       title=f'Evolución mensual · {etiqueta} por {etiq_color}',
                       labels={'mes': 'Mes', campo: etiqueta, color_by: etiq_color})

fig_evol.update_layout(height=380)
st.plotly_chart(fig_evol, use_container_width=True)

# ═══════════════════════════════════════════
# SECCIÓN 3 — COMPARACIÓN ENTRE VARIABLES
# ═══════════════════════════════════════════
st.markdown('<div class="section-title">🔍 Relación entre Variables</div>', unsafe_allow_html=True)

opciones_var = {
    'eficiencia_pct': 'Eficiencia (%)',
    'tasa_defectos_pct': 'Tasa Defectos (%)',
    'tiempo_paro_min': 'Tiempo Paro (min)',
    'consumo_energia_kwh': 'Consumo Energía (kWh)',
    'costo_produccion_cop': 'Costo Producción (COP)',
    'temperatura_c': 'Temperatura (°C)',
    'tiempo_ciclo_min': 'Tiempo Ciclo (min)',
    'unidades_producidas': 'Unidades Producidas',
    'unidades_defectuosas': 'Unidades Defectuosas',
}

c1, c2, c3 = st.columns(3)
with c1:
    eje_x = st.selectbox('Eje X', list(opciones_var.keys()), index=0,
                          format_func=lambda x: opciones_var[x])
with c2:
    eje_y = st.selectbox('Eje Y', list(opciones_var.keys()), index=1,
                          format_func=lambda x: opciones_var[x])
with c3:
    color_scatter = st.selectbox('Color por', ['linea_produccion', 'turno', 'producto', 'maquina'],
                                  format_func=lambda x: {'linea_produccion': 'Línea', 'turno': 'Turno',
                                                         'producto': 'Producto', 'maquina': 'Máquina'}.get(x))

fig_scatter = px.scatter(
    dff, x=eje_x, y=eje_y, color=color_scatter,
    hover_data=['id_orden', 'operador', 'fecha_produccion'],
    trendline='ols',
    title=f'{opciones_var[eje_x]} vs {opciones_var[eje_y]}',
    labels={eje_x: opciones_var[eje_x], eje_y: opciones_var[eje_y],
            color_scatter: color_scatter.replace('_', ' ').title()},
    height=420
)
st.plotly_chart(fig_scatter, use_container_width=True)

# ═══════════════════════════════════════════
# SECCIÓN 4 — PAROS Y CAUSAS
# ═══════════════════════════════════════════
st.markdown('<div class="section-title">⛔ Análisis de Paros</div>', unsafe_allow_html=True)

col_p1, col_p2 = st.columns(2)

with col_p1:
    paros = dff.groupby('causa_paro').agg(
        total_min=('tiempo_paro_min', 'sum'),
        frecuencia=('id_orden', 'count')
    ).reset_index().sort_values('total_min', ascending=True)

    fig_paros = px.bar(paros, x='total_min', y='causa_paro', orientation='h',
                       title='⏱️ Tiempo Total de Paro por Causa (min)',
                       labels={'total_min': 'Minutos totales', 'causa_paro': 'Causa'},
                       color='total_min', color_continuous_scale='Reds', text_auto=True)
    fig_paros.update_layout(showlegend=False, height=320)
    st.plotly_chart(fig_paros, use_container_width=True)

with col_p2:
    paros_linea = dff.groupby(['linea_produccion', 'causa_paro'])['tiempo_paro_min'].sum().reset_index()
    fig_paros2 = px.bar(paros_linea, x='linea_produccion', y='tiempo_paro_min',
                        color='causa_paro', title='⛔ Paros por Línea y Causa',
                        labels={'linea_produccion': 'Línea', 'tiempo_paro_min': 'Minutos',
                                'causa_paro': 'Causa'},
                        barmode='stack', height=320)
    st.plotly_chart(fig_paros2, use_container_width=True)

# ═══════════════════════════════════════════
# SECCIÓN 5 — HEATMAPS
# ═══════════════════════════════════════════
st.markdown('<div class="section-title">🌡️ Heatmaps de Rendimiento</div>', unsafe_allow_html=True)

col_h1, col_h2 = st.columns(2)

with col_h1:
    pivot_ef = dff.pivot_table(values='eficiencia_pct', index='linea_produccion',
                                columns='turno', aggfunc='mean').round(1)
    fig_h1 = px.imshow(pivot_ef, title='Eficiencia (%) · Línea vs Turno',
                        color_continuous_scale='RdYlGn', text_auto=True,
                        labels=dict(x='Turno', y='Línea', color='Eficiencia (%)'))
    fig_h1.update_layout(height=300)
    st.plotly_chart(fig_h1, use_container_width=True)

with col_h2:
    pivot_def = dff.pivot_table(values='tasa_defectos_pct', index='maquina',
                                 columns='turno', aggfunc='mean').round(2)
    fig_h2 = px.imshow(pivot_def, title='Tasa Defectos (%) · Máquina vs Turno',
                        color_continuous_scale='RdYlGn_r', text_auto=True,
                        labels=dict(x='Turno', y='Máquina', color='Defectos (%)'))
    fig_h2.update_layout(height=300)
    st.plotly_chart(fig_h2, use_container_width=True)

# ═══════════════════════════════════════════
# SECCIÓN 6 — ENERGÍA Y COSTOS
# ═══════════════════════════════════════════
st.markdown('<div class="section-title">💡 Energía y Costos</div>', unsafe_allow_html=True)

col_e1, col_e2 = st.columns(2)

with col_e1:
    energia_linea = dff.groupby('linea_produccion').agg(
        energia=('consumo_energia_kwh', 'sum'),
        costo=('costo_produccion_cop', 'sum')
    ).reset_index()
    fig_e1 = px.bar(energia_linea, x='linea_produccion', y='energia',
                    title='⚡ Consumo Total de Energía por Línea (kWh)',
                    labels={'linea_produccion': 'Línea', 'energia': 'kWh'},
                    color='energia', color_continuous_scale='Oranges', text_auto=True)
    fig_e1.update_layout(showlegend=False, height=320)
    st.plotly_chart(fig_e1, use_container_width=True)

with col_e2:
    costo_prod = dff.groupby('producto')['costo_produccion_cop'].mean().reset_index().sort_values('costo_produccion_cop', ascending=False)
    fig_e2 = px.bar(costo_prod, x='producto', y='costo_produccion_cop',
                    title='💰 Costo Promedio de Producción por Producto (COP)',
                    labels={'producto': 'Producto', 'costo_produccion_cop': 'COP promedio'},
                    color='costo_produccion_cop', color_continuous_scale='Purples', text_auto=True)
    fig_e2.update_layout(showlegend=False, height=320)
    st.plotly_chart(fig_e2, use_container_width=True)

# ═══════════════════════════════════════════
# SECCIÓN 7 — RANKING DE OPERADORES
# ═══════════════════════════════════════════
st.markdown('<div class="section-title">👷 Ranking de Operadores</div>', unsafe_allow_html=True)

ranking = dff.groupby('operador').agg(
    eficiencia=('eficiencia_pct', 'mean'),
    defectos=('tasa_defectos_pct', 'mean'),
    ordenes=('id_orden', 'count'),
    unidades=('unidades_producidas', 'sum'),
    paro_prom=('tiempo_paro_min', 'mean')
).round(2).reset_index().sort_values('eficiencia', ascending=False)

fig_rank = px.bar(ranking, x='operador', y='eficiencia',
                  error_y=ranking['defectos'],
                  title='👷 Eficiencia promedio por Operador (barras de error = tasa defectos)',
                  labels={'operador': 'Operador', 'eficiencia': 'Eficiencia (%)'},
                  color='eficiencia', color_continuous_scale='Blues', text_auto=True)
fig_rank.update_layout(showlegend=False, height=380)
st.plotly_chart(fig_rank, use_container_width=True)

# Tabla ranking
st.dataframe(
    ranking.rename(columns={
        'operador': 'Operador', 'eficiencia': 'Eficiencia (%)',
        'defectos': 'Defectos (%)', 'ordenes': 'Órdenes',
        'unidades': 'Unidades prod.', 'paro_prom': 'Paro prom. (min)'
    }).reset_index(drop=True),
    use_container_width=True, hide_index=True
)

# ─────────────────────────────────────────────
# DATOS CRUDOS
# ─────────────────────────────────────────────
st.markdown('---')
with st.expander('📋 Ver datos completos filtrados'):
    st.dataframe(dff.reset_index(drop=True), use_container_width=True, hide_index=True)
    st.caption(f'{len(dff)} registros')
