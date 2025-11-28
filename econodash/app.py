import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
import world_bank_data as wb
from datetime import datetime
import os
from streamlit_option_menu import option_menu

# Configuración de la página
st.set_page_config(
    page_title="EconoDash - Panel Económico Interactivo",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuración de directorios
OUTPUT_DIR = 'output'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Definición de indicadores
INDICADORES = {
    # Indicadores macroeconómicos básicos
    'NY.GDP.PCAP.CD': {
        'nombre': 'PIB per cápita',
        'unidad': 'US$',
        'es_porcentaje': False,
        'descripcion': 'Producto Interno Bruto per cápita en dólares estadounidenses actuales. Mide el valor económico por persona y es un indicador clave del nivel de vida.'
    },
    'NY.GDP.MKTP.KD.ZG': {
        'nombre': 'Crecimiento del PIB',
        'unidad': '%',
        'es_porcentaje': True,
        'descripcion': 'Tasa de crecimiento anual del PIB basada en moneda local a precios constantes. Indica la velocidad de crecimiento económico de un país.'
    },
    'FP.CPI.TOTL.ZG': {
        'nombre': 'Inflación anual',
        'unidad': '%',
        'es_porcentaje': True,
        'descripcion': 'Tasa de inflación porcentual anual basada en el índice de precios al consumidor. Mide la variación porcentual en el costo de vida.'
    },
    'SL.UEM.TOTL.ZS': {
        'nombre': 'Tasa de desempleo',
        'unidad': '%',
        'es_porcentaje': True,
        'descripcion': 'Porcentaje de la población activa que no tiene empleo pero busca trabajo y está disponible para trabajar. Un indicador clave del mercado laboral.'
    },
    
    # Indicadores fiscales y de deuda
    'GC.DOD.TOTL.GD.ZS': {
        'nombre': 'Deuda Pública',
        'unidad': '% del PIB',
        'es_porcentaje': True,
        'descripcion': 'Deuda bruta del gobierno general como porcentaje del PIB. Indica la sostenibilidad de la deuda pública de un país.'
    },
    
    # Comercio exterior
    'NE.EXP.GNFS.ZS': {
        'nombre': 'Exportaciones',
        'unidad': '% del PIB',
        'es_porcentaje': True,
        'descripcion': 'Exportaciones de bienes y servicios como porcentaje del PIB. Mide la importancia del sector exportador en la economía.'
    },
    'NE.IMP.GNFS.ZS': {
        'nombre': 'Importaciones',
        'unidad': '% del PIB',
        'es_porcentaje': True,
        'descripcion': 'Importaciones de bienes y servicios como porcentaje del PIB. Indica la dependencia de bienes y servicios del exterior.'
    },
    'BX.KLT.DINV.WD.GD.ZS': {
        'nombre': 'Inversión Extranjera Directa',
        'unidad': '% del PIB',
        'es_porcentaje': True,
        'descripcion': 'Inversión Extranjera Directa, entradas netas como porcentaje del PIB. Mide la confianza de los inversores extranjeros en la economía.'
    },
    
    # Gasto social
    'SE.XPD.TOTL.GD.ZS': {
        'nombre': 'Gasto en Educación',
        'unidad': '% del PIB',
        'es_porcentaje': True,
        'descripcion': 'Gasto público en educación como porcentaje del PIB. Indica la prioridad que da un país a la educación.'
    },
    'SH.XPD.CHEX.GD.ZS': {
        'nombre': 'Gasto en Salud',
        'unidad': '% del PIB',
        'es_porcentaje': True,
        'descripcion': 'Gasto en salud como porcentaje del PIB. Refleja la inversión en servicios de salud pública y privada.'
    },
    
    # Indicadores demográficos
    'SP.DYN.LE00.IN': {
        'nombre': 'Esperanza de Vida',
        'unidad': 'años',
        'es_porcentaje': False,
        'descripcion': 'Esperanza de vida al nacer, total en años. Un indicador clave del nivel de desarrollo y calidad de vida de un país.'
    },
    'SP.POP.TOTL': {
        'nombre': 'Población Total',
        'unidad': 'personas',
        'es_porcentaje': False,
        'descripcion': 'Población total basada en la definición de facto de población, que cuenta a todos los residentes independientemente de su estatus legal o ciudadanía.'
    },
    
    # Indicadores de desarrollo
    'SI.POV.GINI': {
        'nombre': 'Coeficiente de Gini',
        'unidad': 'índice',
        'es_porcentaje': False,
        'descripcion': 'Mide la desigualdad en la distribución del ingreso, donde 0 representa igualdad perfecta y 1 representa desigualdad perfecta.'
    },
    'NY.GDP.PCAP.PP.CD': {
        'nombre': 'PIB per cápita (PPA)',
        'unidad': 'US$',
        'es_porcentaje': False,
        'descripcion': 'PIB per cápita ajustado por paridad de poder adquisitivo. Permite comparar el nivel de vida entre países.'
    }
}

# Diccionario de países (código: nombre)
PAISES = {
    'MEX': 'México',
    'USA': 'Estados Unidos',
    'CAN': 'Canadá',
    'BRA': 'Brasil',
    'ESP': 'España',
    'ARG': 'Argentina',
    'CHL': 'Chile',
    'COL': 'Colombia',
    'PER': 'Perú',
    'DEU': 'Alemania',
    'FRA': 'Francia',
    'GBR': 'Reino Unido',
    'JPN': 'Japón',
    'CHN': 'China',
    'IND': 'India'
}

@st.cache_data(ttl=86400)  # Cachear por 24 horas
def obtener_datos_banco_mundial(paises, indicadores, anio_inicio=None, anio_fin=None):
    """Obtiene datos del Banco Mundial para los países e indicadores especificados."""
    datos_completos = {}
    
    # Mostrar barra de progreso
    progress_text = "Descargando datos del Banco Mundial..."
    progress_bar = st.progress(0, text=progress_text)
    total_indicadores = len(indicadores)
    
    # Verificar si hay países seleccionados
    if not paises:
        st.error("❌ No se han seleccionado países.")
        progress_bar.empty()
        return {}
        
    # Verificar si hay indicadores seleccionados
    if not indicadores:
        st.error("❌ No se han seleccionado indicadores.")
        progress_bar.empty()
        return {}
    
    try:
        for i, (codigo, info) in enumerate(indicadores.items(), 1):
            # Actualizar barra de progreso
            progress_percent = int((i / total_indicadores) * 100)
            progress_bar.progress(
                progress_percent, 
                text=f"{progress_text} ({i}/{total_indicadores}) {info['nombre']}"
            )
            
            try:
                # Obtener datos con un tiempo de espera mayor
                with st.spinner(f"Obteniendo datos para {info['nombre']}..."):
                    # Intentar obtener los datos con un timeout
                    try:
                        data = wb.get_series(codigo, country=paises, mrv=30)  # Últimos 30 años
                    except Exception as e:
                        st.warning(f"⚠️ Error al obtener datos para {info['nombre']}: {str(e)}")
                        continue
                
                if data is None or data.empty:
                    st.warning(f"⚠️ No hay datos disponibles para {info['nombre']}")
                    continue
                    
                try:
                    df = data.reset_index()
                    # Verificar si las columnas esperadas están presentes
                    if 'Country' not in df.columns or 'Year' not in df.columns or codigo not in df.columns:
                        st.warning(f"⚠️ Formato inesperado en los datos para {info['nombre']}")
                        continue
                        
                    df = df.rename(columns={
                        'Country': 'Pais',
                        'Year': 'Año',
                        codigo: 'Valor'
                    })
                    
                    # Filtrar por rango de años si se especifica
                    if anio_inicio and anio_fin:
                        df = df[(df['Año'] >= anio_inicio) & (df['Año'] <= anio_fin)]
                    
                    # Convertir códigos de país a nombres
                    df['Pais'] = df['Pais'].map({k: v for k, v in PAISES.items() if k in paises})
                    
                    # Verificar si hay datos después del filtrado
                    if df.empty:
                        st.warning(f"⚠️ No hay datos disponibles para {info['nombre']} en el rango de años seleccionado")
                        continue
                        
                    # Eliminar filas con valores faltantes
                    df = df.dropna(subset=['Valor'])
                    
                    # Solo guardar si hay datos válidos
                    if not df.empty:
                        datos_completos[info['nombre']] = df[['Pais', 'Año', 'Valor']]
                    else:
                        st.warning(f"⚠️ No hay datos válidos para {info['nombre']} después de filtrar valores faltantes")
                        
                except Exception as e:
                    st.warning(f"⚠️ Error al procesar datos para {info['nombre']}: {str(e)}")
                    continue
                    
            except Exception as e:
                st.warning(f"⚠️ No se pudieron obtener datos para {info['nombre']}: {str(e)}")
                continue
                
    except Exception as e:
        st.error(f"❌ Error inesperado al obtener datos: {str(e)}")
    finally:
        # Asegurarse de que la barra de progreso se complete
        progress_bar.empty()
    
    # Mostrar resumen de datos obtenidos
    if datos_completos:
        st.success(f"✅ Se obtuvieron {len(datos_completos)} de {total_indicadores} indicadores correctamente.")
    else:
        st.error("❌ No se pudieron obtener datos para ningún indicador. Por favor verifica lo siguiente:")
        st.markdown("""
        - Tu conexión a Internet está activa
        - Los códigos de país e indicadores son válidos
        - El servicio de datos del Banco Mundial está disponible
        - Intenta con un rango de años diferente
        """)
    
    return datos_completos

def mostrar_grafico(df, indicador_info, paises_seleccionados):
    """Muestra un gráfico interactivo con los datos proporcionados."""
    if df is None or df.empty:
        st.warning("No hay datos disponibles para el indicador seleccionado.")
        return
    
    # Filtrar por países seleccionados
    df = df[df['Pais'].isin(paises_seleccionados)]
    
    # Determinar el tipo de gráfico basado en el indicador
    if 'PIB' in indicador_info['nombre'] or 'crecimiento' in indicador_info['nombre'].lower():
        # Gráfico de área para PIB y crecimiento
        fig = px.area(
            df, 
            x='Año', 
            y='Valor', 
            color='Pais',
            title=f"{indicador_info['nombre']} ({indicador_info['unidad']})",
            labels={'Valor': f"{indicador_info['nombre']} ({indicador_info['unidad']})"},
            template='plotly_white',
            height=500,
            line_shape='spline',
            color_discrete_sequence=px.colors.qualitative.Plotly
        )
    elif 'población' in indicador_info['nombre'].lower():
        # Gráfico de barras para población
        fig = px.bar(
            df, 
            x='Año', 
            y='Valor', 
            color='Pais',
            title=f"{indicador_info['nombre']} ({indicador_info['unidad']})",
            labels={'Valor': f"{indicador_info['nombre']} ({indicador_info['unidad']})"},
            template='plotly_white',
            height=500,
            barmode='group'
        )
    else:
        # Gráfico de líneas estándar para otros indicadores
        fig = px.line(
            df, 
            x='Año', 
            y='Valor', 
            color='Pais',
            title=f"{indicador_info['nombre']} ({indicador_info['unidad']})",
            labels={'Valor': f"{indicador_info['nombre']} ({indicador_info['unidad']})"},
            template='plotly_white',
            height=500,
            line_shape='spline',
            markers=True
        )
    
    # Mejorar el diseño
    fig.update_layout(
        xaxis_title='Año',
        yaxis_title=indicador_info['nombre'] + f" ({indicador_info['unidad']})",
        hovermode='x unified',
        legend_title='País',
        font=dict(family="Arial", size=12, color="black"),
        margin=dict(l=50, r=50, t=80, b=50),
        plot_bgcolor='rgba(0,0,0,0.02)',
        xaxis=dict(showgrid=True, gridwidth=1, gridcolor='LightGrey'),
        yaxis=dict(showgrid=True, gridwidth=1, gridcolor='LightGrey')
    )
    
    # Personalizar tooltips
    if indicador_info['es_porcentaje']:
        hovertemplate = '%{y:.2f}%<extra>%{x}</extra>'
    else:
        if 'US$' in indicador_info['unidad'] or 'dólar' in indicador_info['unidad'].lower():
            hovertemplate = 'US$ %{y:,.2f}<extra>%{x}</extra>'
        elif 'personas' in indicador_info['unidad'].lower():
            hovertemplate = '%{y:,.0f} personas<extra>%{x}</extra>'
        else:
            hovertemplate = '%{y:,.2f}<extra>%{x}</extra>'
    
    for trace in fig.data:
        trace.hovertemplate = f'<b>%{{data.name}}</b><br>{hovertemplate}'
    
    # Añadir línea de promedio si es relevante
    if len(paises_seleccionados) > 1 and not df.empty and not 'población' in indicador_info['nombre'].lower():
        promedio = df.groupby('Año')['Valor'].mean().reset_index()
        fig.add_scatter(
            x=promedio['Año'],
            y=promedio['Valor'],
            mode='lines',
            line=dict(dash='dash', color='red', width=2),
            name='Promedio',
            hovertemplate=f"<b>Promedio</b><br>{hovertemplate}",
            showlegend=True
        )
    
    # Mostrar estadísticas resumidas
    with st.expander("📊 Estadísticas descriptivas", expanded=False):
        stats = df.groupby('Pais')['Valor'].agg(['mean', 'min', 'max', 'std']).reset_index()
        stats.columns = ['País', 'Promedio', 'Mínimo', 'Máximo', 'Desv. Estándar']
        
        # Formatear valores según el tipo de indicador
        if indicador_info['es_porcentaje'] or 'US$' in indicador_info['unidad']:
            for col in ['Promedio', 'Mínimo', 'Máximo', 'Desv. Estándar']:
                if indicador_info['es_porcentaje']:
                    stats[col] = stats[col].apply(lambda x: f"{x:.2f}%")
                else:
                    stats[col] = stats[col].apply(lambda x: f"${x:,.2f}")
        
        st.dataframe(
            stats,
            use_container_width=True,
            hide_index=True,
            column_config={
                'País': st.column_config.TextColumn("País"),
                'Promedio': st.column_config.NumberColumn("Promedio"),
                'Mínimo': st.column_config.NumberColumn("Mínimo"),
                'Máximo': st.column_config.NumberColumn("Máximo"),
                'Desv. Estándar': st.column_config.NumberColumn("Desv. Estándar")
            }
        )
    
    # Mostrar el gráfico
    st.plotly_chart(fig, use_container_width=True)
    
    # Opciones de descarga
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="📥 Descargar datos",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name=f"datos_{indicador_info['nombre'].lower().replace(' ', '_')}.csv",
            mime='text/csv',
            use_container_width=True
        )
    with col2:
        # Botón para expandir/contraer el gráfico
        if st.button("🔄 Actualizar vista", use_container_width=True):
            st.rerun()

def mostrar_resumen(datos_por_indicador, indicadores_seleccionados):
    """Muestra un resumen con los últimos datos disponibles de manera visual."""
    st.subheader("📊 Resumen de Datos")
    st.caption("Comparación de los últimos datos disponibles para los indicadores seleccionados.")
    
    # Verificar si hay datos para mostrar
    if not any(indicador in datos_por_indicador and not datos_por_indicador[indicador].empty 
              for indicador in indicadores_seleccionados):
        st.warning("No hay datos disponibles para los indicadores seleccionados.")
        return
    
    # Crear pestañas para cada indicador
    tabs = st.tabs([f"📈 {indicador}" for indicador in indicadores_seleccionados 
                   if indicador in datos_por_indicador and not datos_por_indicador[indicador].empty])
    
    for idx, indicador in enumerate([i for i in indicadores_seleccionados 
                                   if i in datos_por_indicador and not datos_por_indicador[i].empty]):
        with tabs[idx]:
            df = datos_por_indicador[indicador]
            info = next((v for k, v in INDICADORES.items() if v['nombre'] == indicador), None)
            
            if info is None:
                continue
                
            # Obtener el último año con datos para cada país
            ultimos_datos = df.sort_values('Año').groupby('Pais').last().reset_index()
            ultimo_anio = ultimos_datos['Año'].max()
            
            # Mostrar título y descripción
            st.markdown(f"### {indicador} ({info['unidad']})")
            st.caption(info['descripcion'])
            
            # Crear dos columnas para métricas y gráfico
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.markdown("#### 📌 Datos del último año")
                st.caption(f"Año más reciente con datos: {int(ultimo_anio)}")
                
                # Mostrar métricas clave
                if not ultimos_datos.empty:
                    # Calcular estadísticas
                    max_val = ultimos_datos['Valor'].max()
                    min_val = ultimos_datos['Valor'].min()
                    avg_val = ultimos_datos['Valor'].mean()
                    
                    # Formatear valores según el tipo de indicador
                    def formatear_valor(valor, es_porcentaje, unidad):
                        if es_porcentaje:
                            return f"{valor:.2f}%"
                        elif 'US$' in unidad or 'dólar' in unidad.lower():
                            return f"${valor:,.2f}"
                        elif 'personas' in unidad.lower():
                            return f"{valor:,.0f}"
                        return f"{valor:,.2f}"
                    
                    # Mostrar métricas
                    st.metric(
                        label="País con el valor más alto",
                        value=ultimos_datos.loc[ultimos_datos['Valor'].idxmax()]['Pais'],
                        delta=formatear_valor(max_val, info['es_porcentaje'], info['unidad'])
                    )
                    
                    st.metric(
                        label="País con el valor más bajo",
                        value=ultimos_datos.loc[ultimos_datos['Valor'].idxmin()]['Pais'],
                        delta=formatear_valor(min_val, info['es_porcentaje'], info['unidad'])
                    )
                    
                    st.metric(
                        label="Promedio entre países",
                        value=formatear_valor(avg_val, info['es_porcentaje'], info['unidad'])
                    )
                    
                    # Mostrar tabla con todos los datos
                    st.markdown("#### 📋 Datos por país")
                    
                    # Formatear valores para la tabla
                    datos_tabla = ultimos_datos[['Pais', 'Año', 'Valor']].copy()
                    datos_tabla['Año'] = datos_tabla['Año'].astype(int)
                    
                    if info['es_porcentaje']:
                        datos_tabla['Valor'] = datos_tabla['Valor'].apply(lambda x: f"{x:.2f}%")
                    else:
                        if 'US$' in info['unidad'] or 'dólar' in info['unidad'].lower():
                            datos_tabla['Valor'] = datos_tabla['Valor'].apply(lambda x: f"${x:,.2f}")
                        else:
                            datos_tabla['Valor'] = datos_tabla['Valor'].apply(lambda x: f"{x:,.2f}")
                    
                    st.dataframe(
                        datos_tabla.rename(columns={
                            'Pais': 'País',
                            'Año': 'Año',
                            'Valor': info['unidad']
                        }),
                        use_container_width=True,
                        hide_index=True,
                        height=300
                    )
                    
                    # Botón de descarga
                    st.download_button(
                        label=f"💾 Descargar datos de {indicador}",
                        data=df.to_csv(index=False).encode('utf-8'),
                        file_name=f"datos_{indicador.lower().replace(' ', '_')}.csv",
                        mime='text/csv',
                        use_container_width=True,
                        key=f"download_{indicador}"
                    )
            
            with col2:
                st.markdown("#### 📈 Evolución histórica")
                
                # Mostrar gráfico de evolución
                if len(df['Año'].unique()) > 1:
                    fig = px.line(
                        df, 
                        x='Año', 
                        y='Valor', 
                        color='Pais',
                        labels={'Valor': info['unidad']},
                        template='plotly_white',
                        height=400,
                        line_shape='spline',
                        markers=True
                    )
                    
                    # Mejorar diseño del gráfico
                    fig.update_layout(
                        xaxis_title='Año',
                        yaxis_title=info['unidad'],
                        hovermode='x unified',
                        legend_title='País',
                        margin=dict(l=0, r=0, t=30, b=0),
                        plot_bgcolor='rgba(0,0,0,0.02)',
                        xaxis=dict(showgrid=True, gridwidth=1, gridcolor='LightGrey'),
                        yaxis=dict(showgrid=True, gridwidth=1, gridcolor='LightGrey')
                    )
                    
                    # Personalizar tooltips
                    if info['es_porcentaje']:
                        hovertemplate = '%{y:.2f}%<extra>%{x}</extra>'
                    else:
                        if 'US$' in info['unidad'] or 'dólar' in info['unidad'].lower():
                            hovertemplate = 'US$ %{y:,.2f}<extra>%{x}</extra>'
                        elif 'personas' in info['unidad'].lower():
                            hovertemplate = '%{y:,.0f} personas<extra>%{x}</extra>'
                        else:
                            hovertemplate = '%{y:,.2f}<extra>%{x}</extra>'
                    
                    for trace in fig.data:
                        trace.hovertemplate = f'<b>%{{data.name}}</b><br>{hovertemplate}'
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Se requiere más de un año de datos para mostrar la evolución histórica.")
                    
                    # Mostrar gráfico de barras si solo hay un año
                    fig = px.bar(
                        df, 
                        x='Pais', 
                        y='Valor',
                        color='Pais',
                        labels={'Valor': info['unidad']},
                        template='plotly_white',
                        height=400
                    )
                    
                    fig.update_layout(
                        xaxis_title='País',
                        yaxis_title=info['unidad'],
                        showlegend=False,
                        margin=dict(l=0, r=0, t=30, b=0),
                        plot_bgcolor='rgba(0,0,0,0.02)',
                        xaxis=dict(showgrid=False),
                        yaxis=dict(showgrid=True, gridwidth=1, gridcolor='LightGrey')
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
            
            st.divider()

def analizar_correlacion(datos_por_indicador, indicadores_seleccionados, pais):
    """Analiza la correlación entre diferentes indicadores para un país específico."""
    if len(indicadores_seleccionados) < 2:
        st.warning("Selecciona al menos dos indicadores para analizar su correlación.")
        return None
    
    # Crear un DataFrame combinado con todos los indicadores para el país seleccionado
    df_combinado = None
    
    for indicador in indicadores_seleccionados:
        if indicador in datos_por_indicador:
            df = datos_por_indicador[indicador].copy()
            df = df[df['Pais'] == pais]  # Filtrar por país
            
            if df.empty:
                continue
                
            # Renombrar la columna de valor al nombre del indicador
            df = df.rename(columns={'Valor': indicador})
            
            if df_combinado is None:
                df_combinado = df[['Año', indicador]]
            else:
                df_combinado = pd.merge(
                    df_combinado, 
                    df[['Año', indicador]], 
                    on='Año', 
                    how='outer'
                )
    
    if df_combinado is None or len(df_combinado) < 3:  # Mínimo 3 puntos para correlación
        st.warning("No hay suficientes datos para analizar la correlación.")
        return None
    
    # Calcular matriz de correlación
    corr_matrix = df_combinado.select_dtypes(include=['float64', 'int64']).corr()
    
    return df_combinado, corr_matrix

def mostrar_analisis_correlacion(datos_por_indicador, indicadores_seleccionados, paises_seleccionados):
    """Muestra el análisis de correlación entre indicadores."""
    st.subheader("🔍 Análisis de Correlación")
    st.caption("Analiza las relaciones entre diferentes indicadores económicos.")
    
    if len(paises_seleccionados) == 0:
        st.warning("Selecciona al menos un país para analizar la correlación.")
        return
    
    # Seleccionar país para el análisis
    pais_analisis = st.selectbox(
        "Selecciona un país para el análisis de correlación:",
        options=paises_seleccionados,
        key="pais_correlacion"
    )
    
    # Obtener datos para el análisis de correlación
    resultado = analizar_correlacion(
        datos_por_indicador, 
        indicadores_seleccionados,
        pais_analisis
    )
    
    if resultado is None:
        return None
        
    df_combinado, corr_matrix = resultado
    
    # Mostrar matriz de correlación
    st.markdown("### Matriz de Correlación")
    st.caption("Valores cercanos a 1 indican correlación positiva fuerte, cercanos a -1 indican correlación negativa fuerte, y cercanos a 0 indican poca o ninguna correlación.")
    
    # Crear un heatmap de la matriz de correlación
    fig = px.imshow(
        corr_matrix,
        text_auto=True,
        color_continuous_scale='RdBu',
        zmin=-1,
        zmax=1,
        labels=dict(color="Correlación"),
        x=corr_matrix.columns,
        y=corr_matrix.columns
    )
    
    fig.update_layout(
        width=800,
        height=700,
        title=f"Matriz de Correlación - {pais_analisis}",
        xaxis_title="Indicadores",
        yaxis_title="Indicadores"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Mostrar las correlaciones más fuertes
    st.markdown("### Correlaciones Significativas")
    
    # Crear un DataFrame con las correlaciones
    corr_pairs = corr_matrix.unstack().sort_values(ascending=False)
    corr_pairs = corr_pairs[corr_pairs < 0.999]  # Eliminar correlación consigo mismo
    
    # Mostrar las 5 correlaciones más fuertes (positivas y negativas)
    top_positivas = corr_pairs.head(5)
    top_negativas = corr_pairs[corr_pairs < 0].tail(5)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔼 Mayores Correlaciones Positivas")
        if not top_positivas.empty:
            for idx, ((ind1, ind2), valor) in enumerate(top_positivas.items(), 1):
                st.metric(
                    label=f"{ind1} ↔ {ind2}",
                    value=f"{valor:.2f}",
                    delta="Alta correlación positiva" if valor > 0.7 else "Correlación positiva"
                )
        else:
            st.info("No se encontraron correlaciones positivas fuertes.")
    
    with col2:
        st.markdown("#### 🔽 Mayores Correlaciones Negativas")
        if not top_negativas.empty:
            for idx, ((ind1, ind2), valor) in enumerate(top_negativas.items(), 1):
                st.metric(
                    label=f"{ind1} ↔ {ind2}",
                    value=f"{valor:.2f}",
                    delta="Alta correlación negativa" if valor < -0.7 else "Correlación negativa"
                )
        else:
            st.info("No se encontraron correlaciones negativas fuertes.")
    
    # Mostrar gráfico de dispersión para las dos variables con mayor correlación
    if not top_positivas.empty:
        st.markdown("### Gráfico de Dispersión")
        ind1, ind2 = top_positivas.index[0]
        
        # Obtener datos para el gráfico de dispersión
        df_scatter = df_combinado[[ind1, ind2]].dropna()
        
        if not df_scatter.empty and len(df_scatter) >= 3:
            # Calcular línea de tendencia
            z = np.polyfit(df_scatter[ind1], df_scatter[ind2], 1)
            p = np.poly1d(z)
            
            fig = px.scatter(
                df_scatter, 
                x=ind1, 
                y=ind2,
                trendline="ols",
                title=f"Relación entre {ind1} y {ind2}",
                labels={
                    ind1: f"{ind1} ({INDICADORES.get(ind1, {}).get('unidad', '')})",
                    ind2: f"{ind2} ({INDICADORES.get(ind2, {}).get('unidad', '')})",
                },
                trendline_color_override="red"
            )
            
            # Mejorar diseño
            fig.update_layout(
                xaxis_title=f"{ind1} ({INDICADORES.get(ind1, {}).get('unidad', '')})",
                yaxis_title=f"{ind2} ({INDICADORES.get(ind2, {}).get('unidad', '')})",
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Mostrar ecuación de la línea de tendencia
            r = np.corrcoef(df_scatter[ind1], df_scatter[ind2])[0, 1]
            st.caption(f"Coeficiente de correlación (r): {r:.2f}")
            
            # Interpretación de la correlación
            st.markdown("#### Interpretación de la Correlación")
            if abs(r) > 0.7:
                relacion = "fuerte"
            elif abs(r) > 0.3:
                relacion = "moderada"
            else:
                relacion = "débil o nula"
                
            if r > 0:
                st.info(f"Existe una correlación {relacion} positiva entre {ind1} y {ind2}. Cuando uno aumenta, el otro tiende a hacerlo también.")
            elif r < 0:
                st.info(f"Existe una correlación {relacion} negativa entre {ind1} y {ind2}. Cuando uno aumenta, el otro tiende a disminuir.")
            else:
                st.info(f"No hay una correlación clara entre {ind1} y {ind2}.")

def main():
    # Configuración de la página
    st.set_page_config(
        page_title="Panel Económico Interactivo",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Estilos CSS personalizados
    st.markdown("""
        <style>
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .stProgress > div > div > div > div {
            background-color: #4CAF50;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.write("🔍 Iniciando aplicación...")
    
    # Barra lateral
    with st.sidebar:
        st.title("⚙️ Configuración")
        st.write("🔧 Configura los parámetros de visualización")
        
        # Mostrar versión de las dependencias
        st.caption("Versiones:")
        st.code(f"""
        pandas: {pd.__version__}
        world_bank_data: {wb.__version__}
        plotly: {pd.__version__}  # Usamos pandas para obtener la versión
        streamlit: {st.__version__}
        """)
        
        # Selector de países
        st.subheader("Países")
        paises_seleccionados = st.multiselect(
            "Selecciona uno o más países:",
            options=list(PAISES.values()),
            default=["México", "Estados Unidos"],
            key="paises"
        )
        
        # Selector de indicadores
        st.subheader("Indicadores Económicos")
        opciones_indicadores = [v['nombre'] for k, v in INDICADORES.items()]
        # Usar códigos de los indicadores en lugar de nombres para evitar problemas de codificación
        default_indicadores = [
            next((v['nombre'] for k, v in INDICADORES.items() if k == 'NY.GDP.PCAP.CD'), ''),  # PIB per cápita
            next((v['nombre'] for k, v in INDICADORES.items() if k == 'NY.GDP.MKTP.KD.ZG'), ''),  # Crecimiento del PIB
            next((v['nombre'] for k, v in INDICADORES.items() if k == 'FP.CPI.TOTL.ZG'), '')  # Inflación
        ]
        
        indicadores_seleccionados = st.multiselect(
            "Selecciona uno o más indicadores:",
            options=opciones_indicadores,
            default=default_indicadores,
            key="indicadores"
        )
        
        # Rango de años
        st.subheader("Rango de Años")
        anio_actual = datetime.now().year
        anio_inicio, anio_fin = st.slider(
            "Selecciona el rango de años:",
            min_value=1990,
            max_value=anio_actual,
            value=(2000, anio_actual - 1),
            key="rango_anios"
        )
        
        # Botón para actualizar datos
        actualizar_datos = st.button("🔄 Actualizar Datos", use_container_width=True)
        
        # Información sobre los datos
        st.markdown("---")
        st.caption("ℹ️ Datos proporcionados por el Banco Mundial")
        st.caption(f"Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    # Título principal
    st.title("🌍 Panel Económico Interactivo")
    st.caption("Visualiza y analiza indicadores económicos de diferentes países.")
    
    # Verificar si se han seleccionado países e indicadores
    st.write(f"🌍 Países seleccionados: {paises_seleccionados}")
    st.write(f"📊 Indicadores seleccionados: {indicadores_seleccionados}")
    
    if not paises_seleccionados or not indicadores_seleccionados:
        st.warning("⚠️ Por favor, selecciona al menos un país y un indicador para continuar.")
        st.write("❌ No se pueden obtener datos sin selección de países e indicadores")
        return
    
    # Obtener datos del Banco Mundial
    with st.status("🌐 Conectando al Banco Mundial...", expanded=True) as status:
        try:
            paises_codigos = [k for k, v in PAISES.items() if v in paises_seleccionados]
            indicadores_filtrados = {k: v for k, v in INDICADORES.items() if v['nombre'] in indicadores_seleccionados}
            
            st.write(f"🔍 Buscando datos para países: {', '.join(paises_seleccionados)}")
            st.write(f"📊 Indicadores seleccionados: {', '.join(indicadores_seleccionados)}")
            st.write(f"📅 Rango de años: {anio_inicio} - {anio_fin}")
            
            # Verificar conexión inicial
            st.write("🔌 Probando conexión con la API...")
            test_data = wb.get_series('NY.GDP.PCAP.CD', country='MEX', mrv=1)
            if not test_data.empty:
                st.success("✅ Conexión exitosa con la API del Banco Mundial")
            
            # Obtener los datos
            st.write("📥 Descargando datos...")
            with st.spinner("Obteniendo datos del Banco Mundial..."):
                datos_por_indicador = obtener_datos_banco_mundial(
                    paises_codigos,
                    indicadores_filtrados,
                    anio_inicio,
                    anio_fin
                )
                
            if not datos_por_indicador:
                st.error("❌ No se pudieron obtener datos. Por favor verifica tu conexión e inténtalo de nuevo.")
                return
                
            st.success(f"✅ Datos obtenidos correctamente para {len(datos_por_indicador)} de {len(indicadores_seleccionados)} indicadores")
            
            # Mostrar resumen de datos obtenidos
            st.markdown("### Resumen de datos")
            for indicador, df in datos_por_indicador.items():
                st.write(f"- {indicador}: {len(df)} registros")
            
            status.update(label="¡Listo! Datos cargados correctamente.", state="complete", expanded=False)
            
        except Exception as e:
            st.error(f"❌ Error al obtener datos: {str(e)}")
            st.exception(e)
            st.markdown("""
            ### Solución de problemas
            1. Verifica tu conexión a Internet
            2. Intenta con menos países o indicadores
            3. Verifica que los códigos de país e indicadores sean correctos
            4. Intenta nuevamente en unos minutos
            """)
            return
    
    # Mostrar pestañas
    tab1, tab2, tab3 = st.tabs(["📊 Gráficos", "📋 Resumen", "🔍 Análisis"])
    
    with tab1:
        # Mostrar gráficos para cada indicador
        for indicador in indicadores_seleccionados:
            if indicador in datos_por_indicador and not datos_por_indicador[indicador].empty:
                mostrar_grafico(
                    datos_por_indicador[indicador],
                    next((v for k, v in INDICADORES.items() if v['nombre'] == indicador), None),
                    paises_seleccionados
                )
    
    with tab2:
        # Mostrar resumen de datos
        mostrar_resumen(datos_por_indicador, indicadores_seleccionados)
    
    with tab3:
        # Mostrar análisis de correlación
        mostrar_analisis_correlacion(datos_por_indicador, indicadores_seleccionados, paises_seleccionados)

if __name__ == "__main__":
    main()
