import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE LA PÁGINA
# ═══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title='TransCargo Dashboard',
    page_icon='🚚',
    layout='wide',
    initial_sidebar_state='expanded'
)

# Estilos personalizados
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d6a9f 100%);
        padding: 1rem; border-radius: 12px; color: white; text-align: center;
    }
    .block-container { padding-top: 1rem; }
    h1 { color: #1e3a5f; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# CARGA DE DATOS (con caché para mejor rendimiento)
# ═══════════════════════════════════════════════════════════════
@st.cache_data
def cargar_datos():
    ruta = os.path.join(os.path.dirname(__file__), 'caso1_logistica_dataset.csv')
    df = pd.read_csv(ruta)
    df['fecha_despacho'] = pd.to_datetime(df['fecha_despacho'])
    return df

df = cargar_datos()

# ═══════════════════════════════════════════════════════════════
# SIDEBAR — FILTROS (patrón F: panel izquierdo siempre visible)
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    st.image("https://via.placeholder.com/200x60/1e3a5f/ffffff?text=TransCargo", width=200)
    st.markdown("---")
    st.header("🔧 Filtros")

    transportistas_sel = st.multiselect(
        "Transportista",
        options=sorted(df['transportista'].unique()),
        default=list(df['transportista'].unique())
    )

    tipos_carga_sel = st.multiselect(
        "Tipo de Carga",
        options=sorted(df['tipo_carga'].unique()),
        default=list(df['tipo_carga'].unique())
    )

    estado_sel = st.selectbox(
        "Estado del Envío",
        options=['Todos'] + sorted(df['estado'].unique())
    )

    origen_sel = st.multiselect(
        "Ciudad Origen",
        options=sorted(df['ciudad_origen'].unique()),
        default=list(df['ciudad_origen'].unique())
    )

    st.markdown("---")
    st.caption("📅 Datos: Año 2024 | 160 envíos")

# ═══════════════════════════════════════════════════════════════
# APLICAR FILTROS
# ═══════════════════════════════════════════════════════════════
df_f = df.copy()
if transportistas_sel:
    df_f = df_f[df_f['transportista'].isin(transportistas_sel)]
if tipos_carga_sel:
    df_f = df_f[df_f['tipo_carga'].isin(tipos_carga_sel)]
if estado_sel != 'Todos':
    df_f = df_f[df_f['estado'] == estado_sel]
if origen_sel:
    df_f = df_f[df_f['ciudad_origen'].isin(origen_sel)]

# ═══════════════════════════════════════════════════════════════
# TÍTULO PRINCIPAL
# ═══════════════════════════════════════════════════════════════
st.title("🚚 TransCargo — Dashboard de Operaciones Logísticas")
st.markdown("**Panel de control de envíos y desempeño de transportistas · 2024**")
st.markdown("---")

# ═══════════════════════════════════════════════════════════════
# FILA DE KPIs (patrón F: escaneo horizontal de métricas)
# ═══════════════════════════════════════════════════════════════
k1, k2, k3, k4, k5 = st.columns(5)

total = len(df_f)
entregados = len(df_f[df_f['estado'] == 'Entregado'])
tasa = round(entregados / total * 100, 1) if total > 0 else 0
costo_prom = df_f['costo_envio_cop'].mean() if total > 0 else 0
retraso_prom = df_f['retraso_dias'].mean() if total > 0 else 0
calificacion = df_f['calificacion_cliente'].mean() if total > 0 else 0

k1.metric("📦 Total Envíos", f"{total:,}", delta=f"{total - len(df)} vs total")
k2.metric("✅ Tasa de Entrega", f"{tasa}%", delta=f"{tasa-70:.1f}% vs meta 70%")
k3.metric("💰 Costo Promedio", f"${costo_prom:,.0f}", delta=None)
k4.metric("⏰ Retraso Promedio", f"{retraso_prom:.1f} días")
k5.metric("⭐ Calificación", f"{calificacion:.1f}/5")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════
# FILA 1 DE GRÁFICAS (patrón Z: gráfica grande izq + pequeña der)
# ═══════════════════════════════════════════════════════════════
col_izq, col_der = st.columns([1.5, 1])

with col_izq:
    # Envíos por mes (línea de tiempo)
    envios_mes = df_f.groupby(df_f['fecha_despacho'].dt.to_period('M')).agg(
        total=('id_envio', 'count')
    ).reset_index()
    envios_mes['fecha_despacho'] = envios_mes['fecha_despacho'].astype(str)

    fig_linea = px.line(
        envios_mes, x='fecha_despacho', y='total',
        markers=True,
        title='📅 Envíos por Mes',
        labels={'fecha_despacho': 'Mes', 'total': 'Envíos'},
        color_discrete_sequence=['#2d6a9f']
    )
    fig_linea.update_traces(line_width=3, marker_size=8)
    fig_linea.update_layout(height=320, margin=dict(t=40, b=20))
    st.plotly_chart(fig_linea, use_container_width=True)

with col_der:
    # Distribución de estados (pie)
    estado_counts = df_f['estado'].value_counts().reset_index()
    fig_pie = px.pie(
        estado_counts, names='estado', values='count',
        title='📦 Estado de Envíos',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig_pie.update_layout(height=320, margin=dict(t=40, b=20))
    st.plotly_chart(fig_pie, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
# FILA 2 DE GRÁFICAS (patrón Z: pequeña izq + grande der)
# ═══════════════════════════════════════════════════════════════
col_izq2, col_der2 = st.columns([1, 1.5])

with col_izq2:
    # Costo promedio por transportista
    cost_trans = df_f.groupby('transportista')['costo_envio_cop'].mean().reset_index()
    cost_trans.columns = ['transportista', 'costo_promedio']
    cost_trans = cost_trans.sort_values('costo_promedio', ascending=True)

    fig_bar = px.bar(
        cost_trans, y='transportista', x='costo_promedio',
        orientation='h',
        title='💰 Costo Promedio por Transportista',
        labels={'costo_promedio': 'COP', 'transportista': ''},
        color='costo_promedio',
        color_continuous_scale='Blues',
        text_auto='.2s'
    )
    fig_bar.update_layout(height=320, margin=dict(t=40, b=20), showlegend=False)
    st.plotly_chart(fig_bar, use_container_width=True)

with col_der2:
    # Scatter: Peso vs Costo
    fig_scatter = px.scatter(
        df_f, x='peso_kg', y='costo_envio_cop',
        color='tipo_carga', size='distancia_km',
        hover_data=['transportista', 'ciudad_origen', 'ciudad_destino'],
        title='⚖️ Peso vs Costo por Tipo de Carga',
        labels={'peso_kg': 'Peso (Kg)', 'costo_envio_cop': 'Costo (COP)', 'tipo_carga': 'Tipo'},
        trendline='ols'
    )
    fig_scatter.update_layout(height=320, margin=dict(t=40, b=20))
    st.plotly_chart(fig_scatter, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
# FILA 3 — HEATMAP COMPLETO
# ═══════════════════════════════════════════════════════════════
st.markdown("### 🌡️ Mapa de Calor — Retraso por Origen y Tipo de Carga")
pivot = df_f.pivot_table(
    values='retraso_dias', index='ciudad_origen',
    columns='tipo_carga', aggfunc='mean'
).round(1)

fig_heat = px.imshow(
    pivot,
    color_continuous_scale='RdYlGn_r',
    text_auto=True,
    title='Retraso Promedio (días) — Rojo = Mayor retraso'
)
fig_heat.update_layout(height=300, margin=dict(t=40, b=20))
st.plotly_chart(fig_heat, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
# TABLA DE DATOS FILTRADOS
# ═══════════════════════════════════════════════════════════════
with st.expander("📋 Ver datos filtrados"):
    cols_show = ['id_envio', 'fecha_despacho', 'ciudad_origen', 'ciudad_destino',
                 'transportista', 'tipo_carga', 'peso_kg', 'costo_envio_cop',
                 'estado', 'retraso_dias', 'calificacion_cliente']
    st.dataframe(df_f[cols_show].sort_values('fecha_despacho', ascending=False), use_container_width=True)
    st.download_button("⬇️ Descargar CSV", df_f.to_csv(index=False), "logistica_filtrado.csv")

st.caption("🔧 Desarrollado con Streamlit + Plotly | Clase de Visualización de Datos")
