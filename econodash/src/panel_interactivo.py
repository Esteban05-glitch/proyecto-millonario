import world_bank_data as wb
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import os
from datetime import datetime

# Configuración de directorios
OUTPUT_DIR = '../output'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Definición de indicadores
INDICADORES = {
    'NY.GDP.PCAP.CD': {
        'nombre': 'PIB per cápita',
        'unidad': 'US$',
        'es_porcentaje': False
    },
    'FP.CPI.TOTL.ZG': {
        'nombre': 'Inflación anual',
        'unidad': '%',
        'es_porcentaje': True
    },
    'SL.UEM.TOTL.ZS': {
        'nombre': 'Tasa de desempleo',
        'unidad': '%',
        'es_porcentaje': True
    },
    'NY.GDP.MKTP.KD.ZG': {
        'nombre': 'Crecimiento del PIB',
        'unidad': '%',
        'es_porcentaje': True
    }
}

def obtener_datos_banco_mundial(paises, indicadores, anios=10):
    """Obtiene datos del Banco Mundial para los países e indicadores especificados."""
    print("\nDescargando datos del Banco Mundial...")
    
    datos_completos = {}
    
    for codigo, info in indicadores.items():
        try:
            print(f"Obteniendo datos para {info['nombre']}...")
            data = wb.get_series(codigo, country=paises, mrv=anios)
            
            if not data.empty:
                df = data.reset_index()
                df = df.rename(columns={
                    'Country': 'Pais',
                    'Year': 'Año',
                    codigo: 'Valor'
                })
                
                # Filtrar solo las columnas necesarias
                df = df[['Pais', 'Año', 'Valor']].dropna()
                
                # Guardar los datos
                datos_completos[info['nombre']] = df
                print(f"  [OK] Datos obtenidos para {info['nombre']}")
            else:
                print(f"  [X] No se encontraron datos para {info['nombre']}")
                
        except Exception as e:
            print(f"  [ERROR] Error al obtener datos para {info['nombre']}: {str(e)}")
    
    return datos_completos

def generar_grafico_interactivo(datos, indicador_info, ruta_guardado):
    """Genera un gráfico interactivo con Plotly."""
    # Crear figura
    fig = px.line(datos, 
                 x='Año', 
                 y='Valor', 
                 color='Pais',
                 title=f"{indicador_info['nombre']} por país",
                 labels={'Valor': indicador_info['nombre'] + f" ({indicador_info['unidad']})"},
                 template='plotly_white')
    
    # Mejorar el diseño
    fig.update_layout(
        xaxis_title='Año',
        yaxis_title=indicador_info['nombre'] + f" ({indicador_info['unidad']})",
        hovermode='x unified',
        legend_title='País',
        font=dict(family="Arial", size=12, color="black")
    )
    
    # Añadir línea de promedio
    if indicador_info['es_porcentaje']:
        fig.add_hline(y=datos['Valor'].mean(), 
                     line_dash="dash", 
                     line_color="red",
                     annotation_text=f"Promedio: {datos['Valor'].mean():.2f}{indicador_info['unidad']}",
                     annotation_position="bottom right")
    
    # Guardar el gráfico
    nombre_archivo = f"{indicador_info['nombre'].lower().replace(' ', '_')}_interactivo.html"
    ruta_completa = os.path.join(ruta_guardado, nombre_archivo)
    fig.write_html(ruta_completa, include_plotlyjs='cdn')
    
    # También guardar como imagen estática
    ruta_imagen = os.path.join(ruta_guardado, f"{indicador_info['nombre'].lower().replace(' ', '_')}.png")
    fig.write_image(ruta_imagen, scale=2)
    
    return ruta_completa, ruta_imagen

def generar_dashboard(datos_por_indicador, ruta_guardado):
    """Genera un dashboard HTML con todos los gráficos."""
    print("\nGenerando dashboard interactivo...")
    
    # Crear lista de figuras
    figuras = []
    
    for indicador, datos in datos_por_indicador.items():
        if datos is not None and not datos.empty:
            info = next((v for k, v in INDICADORES.items() if v['nombre'] == indicador), None)
            if info:
                print(f"  Procesando gráfico para {indicador}...")
                
                # Crear figura
                fig = px.line(datos, 
                            x='Año', 
                            y='Valor', 
                            color='Pais',
                            title=f"{indicador} ({info['unidad']})",
                            labels={'Valor': indicador},
                            template='plotly_white')
                
                # Mejorar diseño
                fig.update_layout(
                    height=400,
                    margin=dict(l=50, r=50, t=80, b=50),
                    showlegend=True
                )
                
                figuras.append(fig)
    
    # Crear dashboard con subplots
    from plotly.subplots import make_subplots
    import plotly.graph_objects as go
    
    # Crear layout de 2x2
    fig = make_subplots(rows=2, cols=2, 
                       subplot_titles=[f"{k} ({v['unidad']})" for k, v in INDICADORES.items()])
    
    # Añadir cada gráfico al dashboard
    for i, (indicador, datos) in enumerate(datos_por_indicador.items(), 1):
        if datos is not None and not datos.empty:
            info = next((v for k, v in INDICADORES.items() if v['nombre'] == indicador), None)
            if info:
                # Obtener fila y columna
                row = (i-1) // 2 + 1
                col = (i-1) % 2 + 1
                
                # Añadir trazas
                for pais in datos['Pais'].unique():
                    df_pais = datos[datos['Pais'] == pais]
                    fig.add_trace(
                        go.Scatter(
                            x=df_pais['Año'], 
                            y=df_pais['Valor'],
                            name=pais,
                            mode='lines+markers',
                            showlegend=(i==1)  # Mostrar leyenda solo en el primer gráfico
                        ),
                        row=row, col=col
                    )
    
    # Actualizar diseño del dashboard
    fig.update_layout(
        title_text='Panel Económico Interactivo',
        height=1000,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    # Guardar dashboard
    ruta_dashboard = os.path.join(ruta_guardado, 'dashboard_economico.html')
    fig.write_html(ruta_dashboard, include_plotlyjs='cdn')
    
    print(f"\n[OK] Dashboard interactivo generado en: {ruta_dashboard}")
    return ruta_dashboard

def main():
    print("=== EconoDash - Panel de Analisis Economico Interactivo ===\n")
    
    # Configuración
    paises = ['MEX', 'USA', 'CAN', 'BRA', 'ESP']
    
    # Obtener datos
    datos_por_indicador = {}
    for codigo, info in INDICADORES.items():
        datos = obtener_datos_banco_mundial(paises, {codigo: info})
        if datos:
            datos_por_indicador.update(datos)
    
    # Generar gráficos individuales
    print("\nGenerando gráficos individuales...")
    for indicador, datos in datos_por_indicador.items():
        if datos is not None and not datos.empty:
            info = next((v for k, v in INDICADORES.items() if v['nombre'] == indicador), None)
            if info:
                ruta_html, ruta_imagen = generar_grafico_interactivo(datos, info, OUTPUT_DIR)
                print(f"  [OK] Gráfico interactivo guardado en: {ruta_html}")
                print(f"  [OK] Imagen estática guardada en: {ruta_imagen}")
    
    # Generar dashboard completo
    ruta_dashboard = generar_dashboard(datos_por_indicador, OUTPUT_DIR)
    
    print("\n¡Análisis completado exitosamente!")
    print(f"\nPuedes abrir el dashboard interactivo en tu navegador web:")
    print(f"  {os.path.abspath(ruta_dashboard)}")

if __name__ == "__main__":
    main()
