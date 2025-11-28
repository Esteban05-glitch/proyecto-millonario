import world_bank_data as wb
import matplotlib.pyplot as plt
import pandas as pd

# Configurar pandas para mostrar más filas y columnas
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 10)

def obtener_datos_banco_mundial():
    # Obtener todos los países disponibles
    print("Obteniendo lista de países...")
    try:
        # Obtener todos los países excepto regiones agregadas
        paises_df = wb.get_countries()
        # Filtrar solo países (excluir regiones, grupos de ingreso, etc.)
        paises = paises_df[paises_df.region != 'Aggregates'].index.tolist()
        print(f"Se encontraron {len(paises)} países/territorios.")
    except Exception as e:
        print(f"Error al obtener la lista de países: {str(e)}")
        print("Usando lista de países por defecto...")
        paises = ['MEX', 'USA', 'CAN', 'BRA', 'ARG', 'COL', 'PER', 'CHL', 'ESP', 'FRA', 'GBR', 'JPN', 'CHN', 'IND']
    
    # Indicador económico (PIB per cápita en USD actuales)
    indicador = 'NY.GDP.PCAP.CD'
    nombre_indicador = 'PIB per cápita (US$ actuales)'

    print(f"=== EconoDash - Panel de Análisis Económico ===\n")
    print(f"Obteniendo datos de {nombre_indicador} del Banco Mundial...\n")
    
    try:
        # Obtener datos usando la API
        print(f"Descargando datos para {len(paises)} países (esto puede tomar un momento)...")
        
        # Descargar en lotes para evitar timeouts
        batch_size = 30
        data_frames = []
        
        for i in range(0, len(paises), batch_size):
            batch = paises[i:i + batch_size]
            print(f"Procesando lote {i//batch_size + 1}/{(len(paises)-1)//batch_size + 1}...")
            try:
                batch_data = wb.get_series(indicador, country=batch, mrv=10)  # Últimos 10 años
                if not batch_data.empty:
                    data_frames.append(batch_data)
            except Exception as e:
                print(f"Advertencia: Error al procesar lote {i//batch_size + 1}: {str(e)}")
        
        if not data_frames:
            print("No se pudieron obtener datos. Verifica tu conexión a internet.")
            return
            
        data = pd.concat(data_frames) if len(data_frames) > 1 else data_frames[0]
        
        # Verificar si obtuvimos datos
        if data.empty:
            print("No se encontraron datos. Verifica la conexión a internet o los parámetros.")
            return
            
        # Mostrar información sobre los datos obtenidos
        print("\nEstructura de los datos crudos:")
        print(f"Tipo de datos: {type(data)}")
        print(f"Primeros registros:\n{data.head()}")
        
        # Convertir a DataFrame para mejor manipulación
        df = data.reset_index()
        print("\nEstructura del DataFrame:")
        print(df.head())
        print(f"\nColumnas del DataFrame: {df.columns.tolist()}")
        
        # Renombrar columnas según la estructura esperada
        if 'Country' in df.columns and 'Year' in df.columns and indicador in df.columns:
            df = df.rename(columns={
                'Country': 'Pais',
                'Year': 'Año',
                indicador: 'Valor'
            })
            
            # Eliminar columnas innecesarias
            columnas_a_mantener = ['Pais', 'Año', 'Valor']
            df = df[columnas_a_mantener]
            
            # Mostrar los datos procesados
            print("\nDatos procesados:")
            print(df.head())
            
            # Verificar si hay datos para graficar
            if df.empty:
                print("No hay datos suficientes para generar el gráfico.")
                return
                
            # Crear un gráfico simple
            plt.figure(figsize=(12, 6))
            
            for pais in df['Pais'].unique():
                pais_data = df[df['Pais'] == pais]
                plt.plot(pais_data['Año'], pais_data['Valor'], label=pais, marker='o')

            plt.title(f'{nombre_indicador} por país')
            plt.xlabel('Año')
            plt.ylabel('US$')
            
            # Mover la leyenda fuera del gráfico
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            
            plt.grid(True)
            plt.xticks(rotation=45)
            plt.tight_layout()

            # Guardar el gráfico
            nombre_archivo = 'pib_per_capita.png'
            plt.savefig(nombre_archivo, bbox_inches='tight')
            print(f"\nGráfico guardado como '{nombre_archivo}'")
            
            # Mostrar el gráfico
            plt.show()
            
            # Mostrar resumen de los datos
            print("\nResumen de datos (mostrando 10 países seleccionados):")
            
            # Seleccionar algunos países representativos para mostrar
            paises_representativos = df['Pais'].drop_duplicates().sample(min(10, len(df['Pais'].unique())))
            df_muestra = df[df['Pais'].isin(paises_representativos)]
            
            # Mostrar tabla pivote con los datos
            tabla = df_muestra.pivot(index='Año', columns='Pais', values='Valor')
            print(tabla)
            
            # Guardar datos completos en un archivo CSV
            try:
                archivo_salida = 'datos_economicos_completos.csv'
                df.to_csv(archivo_salida, index=False)
                print(f"\nDatos completos guardados en: {archivo_salida}")
            except Exception as e:
                print(f"\nNo se pudo guardar el archivo: {str(e)}")
                
            # Mostrar estadísticas descriptivas
            print("\nEstadísticas descriptivas:")
            print(df['Valor'].describe().to_string())
            
        else:
            print("No se pudo procesar la estructura de los datos. Columnas encontradas:")
            print(df.columns.tolist())
        
        # Mostrar algunos indicadores disponibles
        print("\nAlgunos indicadores disponibles (puedes reemplazar el código en la variable 'indicador'):")
        print("- PIB (US$ actuales): NY.GDP.MKTP.CD")
        print("- PIB per cápita (US$ actuales): NY.GDP.PCAP.CD")
        print("- Tasa de inflación: FP.CPI.TOTL.ZG")
        print("- Desempleo: SL.UEM.TOTL.ZS")
        print("- Esperanza de vida: SP.DYN.LE00.IN")
        print("- Población total: SP.POP.TOTL")
        print("- Exportaciones de bienes y servicios: NE.EXP.GNFS.CD")
        print("\nPuedes encontrar más indicadores en: https://data.worldbank.org/indicator")
        print("\nNota: Para analizar un indicador diferente, modifica la variable 'indicador' en el código.")
        
    except Exception as e:
        print(f"\nOcurrió un error al obtener los datos: {str(e)}")
        print("Asegúrate de tener conexión a internet e inténtalo de nuevo.")

if __name__ == "__main__":
    obtener_datos_banco_mundial()
