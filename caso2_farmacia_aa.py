import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os

# ─────────────────────────────────────────────
# CONFIGURACIÓN DE PÁGINA
# ─────────────────────────────────────────────
st.set_page_config(
    page_title='FarmaData Dashboard',
    page_icon='💊',
    layout='wide',
    initial_sidebar_state='expanded'
)

st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1a6b4a 0%, #2ecc8a 100%);
        padding: 1rem; border-radius: 12px; color: white; text-align: center;
    }
    .alert-card {
        background: linear-gradient(135deg, #c0392b 0%, #e74c3c 100%);
        padding: 1rem; border-radius: 12px; color: white; text-align: center;
    }
    h1 { color: #1a6b4a; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CARGA DE DATOS
# ─────────────────────────────────────────────
@st.cache_data
def cargar_datos():
    ruta = os.path.join(os.path.dirname(__file__), 'caso2_farmacia_dataset.csv')
    df = pd.read_csv(ruta)
    df['fecha_venta'] = pd.to_datetime(df['fecha_venta'])
    return df

df = cargar_datos()

# ─────────────────────────────────────────────
# SIDEBAR — FILTROS
# ─────────────────────────────────────────────
st.sidebar.title('🔎 Filtros')

ciudades = ['Todas'] + sorted(df['ciudad'].unique().tolist())
ciudad_sel = st.sidebar.selectbox('🏙️ Ciudad', ciudades)

regimenes = ['Todos'] + sorted(df['regimen'].unique().tolist())
regimen_sel = st.sidebar.selectbox('🏥 Régimen', regimenes)

categorias = ['Todas'] + sorted(df['categoria'].unique().tolist())
categoria_sel = st.sidebar.selectbox('💊 Categoría', categorias)

st.sidebar.markdown('---')
solo_criticos = st.sidebar.checkbox('⚠️ Solo stock crítico (venc. < 90 días y stock < 50)')

# Aplicar filtros
df_filtrado = df.copy()
if ciudad_sel != 'Todas':
    df_filtrado = df_filtrado[df_filtrado['ciudad'] == ciudad_sel]
if regimen_sel != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['regimen'] == regimen_sel]
if categoria_sel != 'Todas':
    df_filtrado = df_filtrado[df_filtrado['categoria'] == categoria_sel]
if solo_criticos:
    df_filtrado = df_filtrado[
        (df_filtrado['dias_vencimiento'] < 90) &
        (df_filtrado['stock_disponible'] < 50)
    ]

# ─────────────────────────────────────────────
# ENCABEZADO
# ─────────────────────────────────────────────
st.title('💊 FarmaData — Dashboard de Ventas')
st.caption('FarmaPlus · Cadena de droguerías · 5 ciudades colombianas')
st.markdown('---')

# ─────────────────────────────────────────────
# KPIs
# ─────────────────────────────────────────────
total_ventas    = df_filtrado['total_venta_cop'].sum()
promedio_ventas = df_filtrado['total_venta_cop'].mean()
total_unidades  = df_filtrado['cantidad_unidades'].sum()
num_productos   = df_filtrado['medicamento'].nunique()

col1, col2, col3, col4 = st.columns(4)
col1.metric('💰 Ventas Totales', f'${total_ventas:,.0f}')
col2.metric('📊 Venta Promedio', f'${promedio_ventas:,.0f}')
col3.metric('📦 Unidades Vendidas', f'{total_unidades:,}')
col4.metric('💊 Medicamentos únicos', num_productos)

st.markdown('---')

# ─────────────────────────────────────────────
# FILA 1: Top 5 + Pie categorías
# ─────────────────────────────────────────────
col_izq, col_der = st.columns(2)

with col_izq:
    top5 = (
        df_filtrado.groupby('medicamento')
        .agg(ventas_totales=('total_venta_cop', 'sum'),
             unidades=('cantidad_unidades', 'sum'))
        .sort_values('ventas_totales', ascending=False)
        .head(5)
        .reset_index()
    )
    fig1 = px.bar(
        top5,
        x='ventas_totales',
        y='medicamento',
        orientation='h',
        title='🏆 Top 5 Medicamentos por Ventas',
        labels={'ventas_totales': 'Ventas (COP)', 'medicamento': 'Medicamento'},
        color='ventas_totales',
        color_continuous_scale='Teal',
        text_auto=True
    )
    fig1.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False)
    st.plotly_chart(fig1, use_container_width=True)

with col_der:
    ventas_cat = df_filtrado.groupby('categoria')['total_venta_cop'].sum().reset_index()
    ventas_cat['porcentaje'] = (ventas_cat['total_venta_cop'] / ventas_cat['total_venta_cop'].sum() * 100).round(1)
    fig2 = px.treemap(
        ventas_cat,
        path=['categoria'],
        values='total_venta_cop',
        title='💊 Distribución por Categoría',
        color='total_venta_cop',
        color_continuous_scale='Teal',
        custom_data=['porcentaje']
    )
    fig2.update_traces(
        texttemplate='<b>%{label}</b><br>%{customdata[0]}%',
        textposition='middle center'
    )
    fig2.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig2, use_container_width=True)

# ─────────────────────────────────────────────
# FILA 2: Serie de tiempo
# ─────────────────────────────────────────────
ventas_mes = (
    df_filtrado.groupby(df_filtrado['fecha_venta'].dt.to_period('M'))['total_venta_cop']
    .sum()
    .reset_index()
)
ventas_mes['fecha_venta'] = ventas_mes['fecha_venta'].astype(str)

fig3 = px.line(
    ventas_mes,
    x='fecha_venta',
    y='total_venta_cop',
    markers=True,
    title='📅 Evolución Mensual de Ventas (COP)',
    labels={'fecha_venta': 'Mes', 'total_venta_cop': 'Ventas (COP)'}
)
fig3.update_traces(line_color='#1a6b4a', line_width=2)
st.plotly_chart(fig3, use_container_width=True)

# ─────────────────────────────────────────────
# FILA 3: Scatter + Heatmap
# ─────────────────────────────────────────────
col_izq2, col_der2 = st.columns(2)

with col_izq2:
    fig4 = px.scatter(
        df_filtrado,
        x='precio_unitario_cop',
        y='cantidad_unidades',
        color='categoria',
        hover_data=['medicamento', 'farmacia'],
        title='💰 Precio Unitario vs Cantidad Vendida',
        labels={
            'precio_unitario_cop': 'Precio Unitario (COP)',
            'cantidad_unidades': 'Unidades Vendidas'
        }
    )
    st.plotly_chart(fig4, use_container_width=True)

with col_der2:
    try:
        pivot = df_filtrado.pivot_table(
            values='total_venta_cop',
            index='ciudad',
            columns='trimestre',
            aggfunc='sum'
        ).round(0)
        fig5 = px.imshow(
            pivot,
            title='🌡️ Ventas por Ciudad y Trimestre (COP)',
            color_continuous_scale='Blues',
            text_auto=True
        )
        st.plotly_chart(fig5, use_container_width=True)
    except Exception:
        st.info('No hay suficientes datos para el heatmap con los filtros actuales.')

# ─────────────────────────────────────────────
# VENTAS POR CIUDAD — Barras
# ─────────────────────────────────────────────
st.markdown('---')
ventas_ciudad = (
    df_filtrado.groupby('ciudad')
    .agg(total_ventas=('total_venta_cop', 'sum'),
         num_ventas=('id_venta', 'count'))
    .reset_index()
    .sort_values('total_ventas', ascending=False)
)
fig6 = px.bar(
    ventas_ciudad,
    x='ciudad',
    y='total_ventas',
    title='🏙️ Ventas Totales por Ciudad',
    labels={'ciudad': 'Ciudad', 'total_ventas': 'Ventas (COP)'},
    color='total_ventas',
    color_continuous_scale='Greens',
    text_auto=True
)
st.plotly_chart(fig6, use_container_width=True)

# ─────────────────────────────────────────────
# TABLA STOCK CRÍTICO
# ─────────────────────────────────────────────
st.markdown('---')
st.subheader('⚠️ Alerta de Stock Crítico')
st.caption('Medicamentos con vencimiento < 90 días Y stock disponible < 50 unidades')

stock_critico = df[
    (df['dias_vencimiento'] < 90) &
    (df['stock_disponible'] < 50)
][['medicamento', 'farmacia', 'ciudad', 'regimen', 'stock_disponible', 'dias_vencimiento']].sort_values('dias_vencimiento')

if len(stock_critico) > 0:
    st.error(f'🚨 {len(stock_critico)} productos en estado crítico')
    st.dataframe(
        stock_critico.reset_index(drop=True),
        use_container_width=True,
        hide_index=True
    )
else:
    st.success('✅ No hay productos en estado crítico con los filtros actuales.')

# ─────────────────────────────────────────────
# DATOS CRUDOS (expandible)
# ─────────────────────────────────────────────
st.markdown('---')
with st.expander('📋 Ver datos completos filtrados'):
    st.dataframe(df_filtrado.reset_index(drop=True), use_container_width=True, hide_index=True)
    st.caption(f'{len(df_filtrado)} registros mostrados')
