import world_bank_data as wb
import matplotlib.pyplot as plt
import pandas as pd
import os
from datetime import datetime

# Configuración de visualización
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 10)
plt.style.use('ggplot')  # Usando 'ggplot' en lugar de 'seaborn' para mejor compatibilidad

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

def generar_grafico_evolucion(datos, indicador_info, ruta_guardado):
    """Genera un gráfico de evolución temporal para un indicador."""
    plt.figure(figsize=(12, 6))
    
    for pais in datos['Pais'].unique():
        datos_pais = datos[datos['Pais'] == pais]
        plt.plot(datos_pais['Año'], datos_pais['Valor'], 
                label=pais, marker='o', markersize=5)
    
    plt.title(f"{indicador_info['nombre']} por país")
    plt.xlabel('Año')
    plt.ylabel(indicador_info['unidad'])
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Guardar el gráfico
    nombre_archivo = f"{indicador_info['nombre'].lower().replace(' ', '_')}.png"
    ruta_completa = os.path.join(ruta_guardado, nombre_archivo)
    plt.savefig(ruta_completa, bbox_inches='tight', dpi=300)
    plt.close()
    
    return ruta_completa

def generar_informe(datos_por_indicador, ruta_guardado):
    """Genera un informe con los datos obtenidos."""
    print("\nGenerando informe...")
    print("  [INFO] Procesando graficos...")
    
    with open(os.path.join(ruta_guardado, 'informe_economico.txt'), 'w', encoding='utf-8') as f:
        f.write("=== INFORME ECONÓMICO ===\n")
        f.write(f"Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for indicador, datos in datos_por_indicador.items():
            if datos is not None and not datos.empty:
                f.write(f"\n=== {indicador.upper()} ===\n")
                f.write("Últimos datos disponibles por país:\n\n")
                
                # Obtener el último año disponible para cada país
                ultimos_datos = datos.loc[datos.groupby('Pais')['Año'].idxmax()]
                f.write(ultimos_datos.to_string(index=False))
                f.write("\n\n")
                
                # Generar gráfico
                ruta_grafico = generar_grafico_evolucion(
                    datos, 
                    {'nombre': indicador, 'unidad': next((v['unidad'] for k, v in INDICADORES.items() 
                                                      if v['nombre'] == indicador), '')},
                    ruta_guardado
                )
                print(f"  [OK] Grafico generado: {ruta_grafico}")
    
    print(f"\n[OK] Informe generado en: {os.path.join(ruta_guardado, 'informe_economico.txt')}")

def main():
    print("=== EconoDash - Panel de Analisis Economico ===\n")
    
    # Configuración
    paises = ['MEX', 'USA', 'CAN', 'BRA', 'ESP']
    
    # Obtener datos
    datos_por_indicador = {}
    for codigo, info in INDICADORES.items():
        datos = obtener_datos_banco_mundial(paises, {codigo: info})
        if datos:
            datos_por_indicador.update(datos)
    
    # Generar informe
    if datos_por_indicador:
        generar_informe(datos_por_indicador, OUTPUT_DIR)
        print("\n¡Análisis completado exitosamente!")
    else:
        print("\nNo se pudieron obtener datos para generar el análisis.")

if __name__ == "__main__":
    main()
