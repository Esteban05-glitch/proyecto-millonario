import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
import world_bank_data as wb
import io
import base64
import plotly.io as pio
from typing import Optional, Union, Dict, List, Tuple
from typing import Dict, List, Optional, Tuple, Union, Any
from datetime import datetime
from functools import lru_cache

# Configuración de la aplicación
def configurar_pagina():
    st.set_page_config(
        page_title="Panel Económico",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

# Diccionario de regiones con sus países (ISO3)
REGIONES = {
    'Mundo': ['WLD'],
    'América Latina y el Caribe': ['LCN', 'LAC', 'TLA', 'TSA', 'LTE', 'TEA', 'TEC', 'TOT'],
    'Europa': ['ECS', 'EMU', 'EUU'],
    'Asia': ['EAS', 'SAS', 'TSA', 'TEA'],
    'África': ['SSF', 'MEA'],
    'Oriente Medio y Norte de África': ['MEA'],
    'América del Norte': ['NAC', 'USA', 'MEX', 'CAN'],
    'Asia del Sur': ['SAS'],
    'América Central': ['BLZ', 'CRI', 'SLV', 'GTM', 'HND', 'NIC', 'PAN'],
    'Caribe': ['ATG', 'BHS', 'BRB', 'CUB', 'DMA', 'DOM', 'GRD', 'HTI', 'JAM', 'KNA', 'LCA', 'VCT', 'TTO'],
    'América del Sur': ['ARG', 'BOL', 'BRA', 'CHL', 'COL', 'ECU', 'GUY', 'PRY', 'PER', 'SUR', 'URY', 'VEN'],
    'Europa Occidental': ['AUT', 'BEL', 'FRA', 'DEU', 'LIE', 'LUX', 'MCO', 'NLD', 'CHE'],
    'Europa del Este': ['BLR', 'BGR', 'CZE', 'HUN', 'MDA', 'POL', 'ROU', 'RUS', 'SVK', 'UKR'],
    'Asia Oriental': ['CHN', 'JPN', 'PRK', 'KOR'],
    'Sudeste Asiático': ['BRN', 'KHM', 'IDN', 'LAO', 'MYS', 'MMR', 'PHL', 'SGP', 'THA', 'VNM'],
    'Medio Oriente': ['ARE', 'BHR', 'IRN', 'IRQ', 'ISR', 'JOR', 'KWT', 'LBN', 'OMN', 'PSE', 'QAT', 'SAU', 'SYR', 'YEM'],
    'África del Norte': ['DZA', 'EGY', 'LBY', 'MAR', 'SDN', 'TUN', 'ESH'],
    'África Subsahariana': ['AGO', 'BEN', 'BWA', 'BFA', 'BDI', 'CPV', 'CMR', 'CAF', 'TCD', 'COM', 'COG', 'COD', 'CIV', 'GNQ', 'ERI', 'SWZ', 'ETH', 'GAB', 'GMB', 'GHA', 'GIN', 'GNB', 'KEN', 'LSO', 'LBR', 'MDG', 'MWI', 'MLI', 'MRT', 'MUS', 'MOZ', 'NAM', 'NER', 'NGA', 'RWA', 'STP', 'SEN', 'SYC', 'SLE', 'SOM', 'ZAF', 'SSD', 'SHN', 'SDN', 'TZA', 'TGO', 'UGA', 'ZMB', 'ZWE'],
    'Oceanía': ['AUS', 'FJI', 'KIR', 'MHL', 'FSM', 'NRU', 'NZL', 'PLW', 'PNG', 'WSM', 'SLB', 'TON', 'TUV', 'VUT']
}

def obtener_region_pais(codigo_pais: str) -> str:
    """Obtiene la región a la que pertenece un país."""
    for region, paises in REGIONES.items():
        if codigo_pais in paises:
            return region
    return 'Otra'

def obtener_paises_region(codigo_pais: str) -> List[str]:
    """Obtiene todos los países de la misma región que el país dado."""
    region = obtener_region_pais(codigo_pais)
    if region == 'Otra':
        return [codigo_pais]  # Si no encontramos la región, devolvemos solo el país
    return REGIONES[region]

def obtener_promedio_region(region: str, df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula el promedio de un indicador para una región específica.
    
    Args:
        region: Nombre de la región (debe estar en las claves de REGIONES)
        df: DataFrame con los datos de los países
        
    Returns:
        DataFrame con el promedio por año para la región especificada
    """
    if region not in REGIONES or df.empty or 'codigo_pais' not in df.columns:
        return pd.DataFrame()
        
    try:
        # Obtener códigos de países de la región
        codigos_region = REGIONES[region]
        
        # Filtrar datos de la región
        df_region = df[df['codigo_pais'].isin(codigos_region)]
        
        if df_region.empty:
            return pd.DataFrame()
        
        # Asegurarse de que tenemos la columna de valor
        valor_col = 'valor' if 'valor' in df_region.columns else 'pib_per_capita_usd'
        if valor_col not in df_region.columns:
            return pd.DataFrame()
        
        # Calcular promedio por año
        promedio_region = df_region.groupby('anio')[valor_col].mean().reset_index()
        promedio_region['pais'] = f'Promedio {region}'
        promedio_region['codigo_pais'] = region.upper()
        promedio_region['indicador'] = df['indicador'].iloc[0] if 'indicador' in df.columns and not df.empty else ''
        promedio_region['codigo_indicador'] = df['codigo_indicador'].iloc[0] if 'codigo_indicador' in df.columns and not df.empty else ''
        
        # Asegurarse de que la columna de valor tenga el nombre correcto
        promedio_region[valor_col] = promedio_region[valor_col].round(2)
        
        return promedio_region
    except Exception as e:
        st.warning(f"Error al calcular promedio para {region}: {str(e)}")
        return pd.DataFrame()

def agregar_promedios(df: pd.DataFrame, incluir_mundo: bool = True, incluir_regiones: bool = True) -> pd.DataFrame:
    """
    Agrega promedios regionales y mundiales al DataFrame de países.
    
    Args:
        df: DataFrame con los datos de los países
        incluir_mundo: Si se debe incluir el promedio mundial
        incluir_regiones: Si se deben incluir promedios regionales
        
    Returns:
        DataFrame con los datos originales más los promedios calculados
    """
    try:
        if df.empty or 'codigo_pais' not in df.columns:
            return df
            
        # Asegurarse de que tenemos la columna de valor
        valor_col = 'valor' if 'valor' in df.columns else 'pib_per_capita_usd' if 'pib_per_capita_usd' in df.columns else None
        if valor_col is None:
            return df
            
        dfs = [df]
        
        if incluir_mundo:
            promedio_mundo = obtener_promedio_region('Mundo', df)
            if not promedio_mundo.empty:
                # Asegurar que el promedio tenga la columna de valor
                if valor_col in promedio_mundo.columns:
                    dfs.append(promedio_mundo)
        
        if incluir_regiones and 'codigo_pais' in df.columns:
            # Determinar regiones relevantes basadas en los países en los datos
            paises = df['codigo_pais'].unique()
            regiones_relevantes = []
            
            for region, codigos in REGIONES.items():
                if region != 'Mundo' and any(pais in codigos for pais in paises):
                    regiones_relevantes.append(region)
            
            for region in regiones_relevantes:
                promedio_region = obtener_promedio_region(region, df)
                if not promedio_region.empty and valor_col in promedio_region.columns:
                    dfs.append(promedio_region)
        
        if len(dfs) > 1:  # Si se agregaron promedios
            # Asegurar que todos los DataFrames tengan las mismas columnas
            columnas_comunes = set.intersection(*(set(df.columns) for df in dfs))
            dfs = [df[list(columnas_comunes)] for df in dfs]
            return pd.concat(dfs, ignore_index=True)
            
        return df
    except Exception as e:
        st.warning(f"Error al agregar promedios: {str(e)}")
        return df

# Diccionario de indicadores económicos
INDICADORES = {
    'NY.GDP.PCAP.CD': {
        'nombre': 'PIB per cápita (US$)',
        'descripcion': 'Producto Interno Bruto per cápita en dólares estadounidenses actuales',
        'unidad': 'US$'
    },
    'NY.GDP.MKTP.CD': {
        'nombre': 'PIB (US$ actuales)',
        'descripcion': 'Producto Interno Bruto en dólares estadounidenses actuales',
        'unidad': 'US$'
    },
    'FP.CPI.TOTL.ZG': {
        'nombre': 'Inflación anual (%)',
        'descripcion': 'Inflación, precios al consumidor (% interanual)',
        'unidad': '%'
    },
    'SL.UEM.TOTL.ZS': {
        'nombre': 'Tasa de desempleo (% de la población activa)',
        'descripcion': 'Desempleo, total (% de la población activa total)',
        'unidad': '%'
    },
    'NE.EXP.GNFS.ZS': {
        'nombre': 'Exportaciones de bienes y servicios (% del PIB)',
        'descripcion': 'Exportaciones de bienes y servicios como porcentaje del PIB',
        'unidad': '%'
    },
    'NE.IMP.GNFS.ZS': {
        'nombre': 'Importaciones de bienes y servicios (% del PIB)',
        'descripcion': 'Importaciones de bienes y servicios como porcentaje del PIB',
        'unidad': '%'
    }
}

# Función para obtener todos los países del Banco Mundial
@st.cache_data(ttl=86400)  # Cachear por 24 horas
def obtener_paises_mundo():
    paises_base = {
        'MEX': {'nombre': 'México', 'nombre_ingles': 'Mexico', 'iso2': 'MX'},
        'USA': {'nombre': 'Estados Unidos', 'nombre_ingles': 'United States', 'iso2': 'US'},
        'CAN': {'nombre': 'Canadá', 'nombre_ingles': 'Canada', 'iso2': 'CA'},
        'BRA': {'nombre': 'Brasil', 'nombre_ingles': 'Brazil', 'iso2': 'BR'},
        'ARG': {'nombre': 'Argentina', 'nombre_ingles': 'Argentina', 'iso2': 'AR'},
        'COL': {'nombre': 'Colombia', 'nombre_ingles': 'Colombia', 'iso2': 'CO'},
        'PER': {'nombre': 'Perú', 'nombre_ingles': 'Peru', 'iso2': 'PE'},
        'CHL': {'nombre': 'Chile', 'nombre_ingles': 'Chile', 'iso2': 'CL'},
        'ESP': {'nombre': 'España', 'nombre_ingles': 'Spain', 'iso2': 'ES'},
        'FRA': {'nombre': 'Francia', 'nombre_ingles': 'France', 'iso2': 'FR'},
        'GBR': {'nombre': 'Reino Unido', 'nombre_ingles': 'United Kingdom', 'iso2': 'GB'},
        'DEU': {'nombre': 'Alemania', 'nombre_ingles': 'Germany', 'iso2': 'DE'},
        'ITA': {'nombre': 'Italia', 'nombre_ingles': 'Italy', 'iso2': 'IT'},
        'JPN': {'nombre': 'Japón', 'nombre_ingles': 'Japan', 'iso2': 'JP'},
        'CHN': {'nombre': 'China', 'nombre_ingles': 'China', 'iso2': 'CN'},
        'IND': {'nombre': 'India', 'nombre_ingles': 'India', 'iso2': 'IN'},
        # Agrega más países según sea necesario
        'RUS': {'nombre': 'Rusia', 'nombre_ingles': 'Russia', 'iso2': 'RU'},
        'ZAF': {'nombre': 'Sudáfrica', 'nombre_ingles': 'South Africa', 'iso2': 'ZA'},
        'AUS': {'nombre': 'Australia', 'nombre_ingles': 'Australia', 'iso2': 'AU'},
        'IDN': {'nombre': 'Indonesia', 'nombre_ingles': 'Indonesia', 'iso2': 'ID'},
        'NGA': {'nombre': 'Nigeria', 'nombre_ingles': 'Nigeria', 'iso2': 'NG'},
        'EGY': {'nombre': 'Egipto', 'nombre_ingles': 'Egypt', 'iso2': 'EG'},
        'PAK': {'nombre': 'Pakistán', 'nombre_ingles': 'Pakistan', 'iso2': 'PK'},
        'BGD': {'nombre': 'Bangladés', 'nombre_ingles': 'Bangladesh', 'iso2': 'BD'},
        'RUS': {'nombre': 'Rusia', 'nombre_ingles': 'Russia', 'iso2': 'RU'},
        'MYS': {'nombre': 'Malasia', 'nombre_ingles': 'Malaysia', 'iso2': 'MY'},
        'PHL': {'nombre': 'Filipinas', 'nombre_ingles': 'Philippines', 'iso2': 'PH'},
        'VNM': {'nombre': 'Vietnam', 'nombre_ingles': 'Vietnam', 'iso2': 'VN'},
        'THA': {'nombre': 'Tailandia', 'nombre_ingles': 'Thailand', 'iso2': 'TH'},
        'SAU': {'nombre': 'Arabia Saudita', 'nombre_ingles': 'Saudi Arabia', 'iso2': 'SA'},
        'ARE': {'nombre': 'Emiratos Árabes Unidos', 'nombre_ingles': 'United Arab Emirates', 'iso2': 'AE'},
        'TUR': {'nombre': 'Turquía', 'nombre_ingles': 'Turkey', 'iso2': 'TR'},
        'IRN': {'nombre': 'Irán', 'nombre_ingles': 'Iran', 'iso2': 'IR'},
        'DZA': {'nombre': 'Argelia', 'nombre_ingles': 'Algeria', 'iso2': 'DZ'},
        'EGY': {'nombre': 'Egipto', 'nombre_ingles': 'Egypt', 'iso2': 'EG'},
        'ZAF': {'nombre': 'Sudáfrica', 'nombre_ingles': 'South Africa', 'iso2': 'ZA'},
        'NGA': {'nombre': 'Nigeria', 'nombre_ingles': 'Nigeria', 'iso2': 'NG'},
        'KEN': {'nombre': 'Kenia', 'nombre_ingles': 'Kenya', 'iso2': 'KE'},
        'ETH': {'nombre': 'Etiopía', 'nombre_ingles': 'Ethiopia', 'iso2': 'ET'},
        'DZA': {'nombre': 'Argelia', 'nombre_ingles': 'Algeria', 'iso2': 'DZ'},
        'UKR': {'nombre': 'Ucrania', 'nombre_ingles': 'Ukraine', 'iso2': 'UA'},
        'POL': {'nombre': 'Polonia', 'nombre_ingles': 'Poland', 'iso2': 'PL'},
        'NLD': {'nombre': 'Países Bajos', 'nombre_ingles': 'Netherlands', 'iso2': 'NL'},
        'BEL': {'nombre': 'Bélgica', 'nombre_ingles': 'Belgium', 'iso2': 'BE'},
        'SWE': {'nombre': 'Suecia', 'nombre_ingles': 'Sweden', 'iso2': 'SE'},
        'CHE': {'nombre': 'Suiza', 'nombre_ingles': 'Switzerland', 'iso2': 'CH'},
        'AUT': {'nombre': 'Austria', 'nombre_ingles': 'Austria', 'iso2': 'AT'},
        'PRT': {'nombre': 'Portugal', 'nombre_ingles': 'Portugal', 'iso2': 'PT'},
        'GRC': {'nombre': 'Grecia', 'nombre_ingles': 'Greece', 'iso2': 'GR'},
        'CZE': {'nombre': 'República Checa', 'nombre_ingles': 'Czech Republic', 'iso2': 'CZ'},
        'ROU': {'nombre': 'Rumanía', 'nombre_ingles': 'Romania', 'iso2': 'RO'},
        'HUN': {'nombre': 'Hungría', 'nombre_ingles': 'Hungary', 'iso2': 'HU'},
        'PRY': {'nombre': 'Paraguay', 'nombre_ingles': 'Paraguay', 'iso2': 'PY'},
        'URY': {'nombre': 'Uruguay', 'nombre_ingles': 'Uruguay', 'iso2': 'UY'},
        'BOL': {'nombre': 'Bolivia', 'nombre_ingles': 'Bolivia', 'iso2': 'BO'},
        'ECU': {'nombre': 'Ecuador', 'nombre_ingles': 'Ecuador', 'iso2': 'EC'},
        'VEN': {'nombre': 'Venezuela', 'nombre_ingles': 'Venezuela', 'iso2': 'VE'},
        'CRI': {'nombre': 'Costa Rica', 'nombre_ingles': 'Costa Rica', 'iso2': 'CR'},
        'PAN': {'nombre': 'Panamá', 'nombre_ingles': 'Panama', 'iso2': 'PA'},
        'DOM': {'nombre': 'República Dominicana', 'nombre_ingles': 'Dominican Republic', 'iso2': 'DO'},
        'GTM': {'nombre': 'Guatemala', 'nombre_ingles': 'Guatemala', 'iso2': 'GT'},
        'HND': {'nombre': 'Honduras', 'nombre_ingles': 'Honduras', 'iso2': 'HN'},
        'SLV': {'nombre': 'El Salvador', 'nombre_ingles': 'El Salvador', 'iso2': 'SV'},
        'NIC': {'nombre': 'Nicaragua', 'nombre_ingles': 'Nicaragua', 'iso2': 'NI'}
    }
    
    try:
        # Obtener todos los países del Banco Mundial
        paises_wb = wb.get_countries()
        
        # Si hay datos, actualizar el diccionario con los países del Banco Mundial
        if paises_wb is not None and not paises_wb.empty:
            # Filtrar solo países (excluir regiones agregadas que no tienen código de región)
            paises_wb = paises_wb[~paises_wb.region.isna()]
            
            for iso3, row in paises_wb.iterrows():
                # El índice ya es el código ISO3
                nombre_ingles = row['name']
                iso2 = row['iso2Code']
                
                # Si el país no está en la lista base, agregarlo
                if iso3 not in paises_base and pd.notna(iso2) and len(iso3) == 3:
                    paises_base[iso3] = {
                        'nombre': nombre_ingles,  # Usar el nombre en inglés si no hay traducción
                        'nombre_ingles': nombre_ingles,
                        'iso2': iso2
                    }
        
        return paises_base
    except Exception as e:
        st.error(f"Error al obtener la lista de países: {str(e)}")
        # Si hay un error, devolver la lista base de países
        return paises_base

# Obtener el diccionario de países
PAISES = obtener_paises_mundo()

# Función para obtener el código ISO2 a partir del código ISO3
def obtener_codigo_iso2(codigo_iso3: str) -> str:
    """Obtiene el código ISO2 a partir del código ISO3 del país."""
    return PAISES.get(codigo_iso3, {}).get('iso2', '')

# Utilidades de datos
def limpiar_datos(datos: Union[pd.DataFrame, pd.Series]) -> pd.DataFrame:
    """Limpia y formatea los datos de entrada de la API del Banco Mundial."""
    if datos is None or datos.empty:
        return pd.DataFrame()
    
    # Convertir a DataFrame si es una Serie
    if isinstance(datos, pd.Series):
        df = datos.reset_index()
        # Verificar si las columnas son las esperadas
        if 'Country' not in df.columns or 'Year' not in df.columns:
            # Si no son las columnas esperadas, manejar diferentes formatos de índice
            df = datos.reset_index()
            
            # Verificar si el índice contiene información de año
            if len(df.columns) == 2:  # Si hay dos columnas (índice y valores)
                df.columns = ['anio', 'pib_per_capita_usd']
                # El código del país está en el nombre de la serie
                if hasattr(datos, 'name') and isinstance(datos.name, tuple) and len(datos.name) > 1:
                    df['codigo_pais'] = datos.name[0]  # Asumimos que el primer elemento es el código de país
                elif hasattr(datos, 'name') and isinstance(datos.name, str):
                    df['codigo_pais'] = datos.name
                else:
                    df['codigo_pais'] = 'DESCONOCIDO'
            else:
                # Si hay más columnas, intentar identificar las correctas
                if 'Country' in df.columns and 'Year' in df.columns:
                    df = df.rename(columns={'Country': 'codigo_pais', 'Year': 'anio'})
                    if len(df.columns) > 3:  # Si hay más columnas de las necesarias
                        df = df[['codigo_pais', 'anio', datos.name if 'value' not in df.columns else 'value']]
                        df.columns = ['codigo_pais', 'anio', 'pib_per_capita_usd']
                else:
                    # Si no podemos identificar las columnas, asumir que son [código_pais, anio, valor]
                    if len(df.columns) >= 3:
                        df = df.iloc[:, :3]  # Tomar solo las primeras 3 columnas
                        df.columns = ['codigo_pais', 'anio', 'pib_per_capita_usd']
                    else:
                        # Si no hay suficientes columnas, crear las que faltan
                        if len(df.columns) == 1:
                            df['anio'] = df.index
                            df['codigo_pais'] = 'DESCONOCIDO'
                            df['pib_per_capita_usd'] = df.iloc[:, 0]
                            df = df[['codigo_pais', 'anio', 'pib_per_capita_usd']]
        else:
            # Si ya tiene las columnas esperadas, renombrar
            df = df.rename(columns={
                'Country': 'codigo_pais',
                'Year': 'anio',
                'value': 'pib_per_capita_usd'
            })
    else:
        # Ya es un DataFrame
        df = datos.copy()
        # Verificar y renombrar columnas si es necesario
        if 'Country' in df.columns and 'Year' in df.columns:
            df = df.rename(columns={
                'Country': 'codigo_pais',
                'Year': 'anio',
                'NY.GDP.PCAP.CD': 'pib_per_capita_usd'
            })
    
    # Asegurar que tenemos las columnas necesarias
    if 'pib_per_capita_usd' not in df.columns:
        # Si no está la columna de valor, usar la primera columna numérica
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            df['pib_per_capita_usd'] = df[numeric_cols[0]]
    
    # Convertir tipos de datos
    if 'anio' in df.columns:
        df['anio'] = pd.to_numeric(df['anio'], errors='coerce')
    
    if 'pib_per_capita_usd' in df.columns:
        df['pib_per_capita_usd'] = pd.to_numeric(df['pib_per_capita_usd'], errors='coerce')
    
    # Mapear códigos de país a nombres
    if 'codigo_pais' in df.columns:
        # Si el código del país es NY.GDP.PCAP.CD, intentar obtener el código del país del nombre de la serie
        if (df['codigo_pais'] == 'NY.GDP.PCAP.CD').any() and hasattr(datos, 'name'):
            if isinstance(datos.name, tuple) and len(datos.name) > 0:
                # El código del país podría estar en el primer elemento de la tupla
                codigo_pais = datos.name[0]
                df['codigo_pais'] = codigo_pais
            elif isinstance(datos.name, str) and len(datos.name) == 3:
                # O podría ser el nombre mismo de la serie
                df['codigo_pais'] = datos.name
        
        # Aplicar el mapeo de códigos a nombres
        df['pais'] = df['codigo_pais'].apply(obtener_nombre_pais)
    
    # Eliminar filas con valores faltantes
    columnas_requeridas = ['pais', 'anio', 'pib_per_capita_usd']
    columnas_disponibles = [col for col in columnas_requeridas if col in df.columns]
    
    if columnas_disponibles:
        df = df.dropna(subset=columnas_disponibles)
    
    # Seleccionar solo las columnas necesarias
    columnas_finales = [col for col in ['pais', 'anio', 'pib_per_capita_usd'] if col in df.columns]
    
    return df[columnas_finales] if columnas_finales else df

def obtener_nombre_pais(codigo: str) -> str:
    """Obtiene el nombre del país a partir de su código o nombre en inglés."""
    if pd.isna(codigo):
        return "Desconocido"
        
    codigo = str(codigo).strip().upper()
    
    # Buscar por código de país (ej: 'MEX')
    if codigo in PAISES:
        return PAISES[codigo]['nombre']
    
    # Buscar por nombre en inglés (ej: 'Mexico')
    for datos in PAISES.values():
        if codigo == datos['nombre_ingles'].upper():
            return datos['nombre']
    
    return f"Desconocido ({codigo})"

@st.cache_data(ttl=3600)  # Cachear por 1 hora
def obtener_datos_indicador(codigo_indicador: str, codigos_paises: List[str], anio_inicio: int, anio_fin: int) -> pd.DataFrame:
    """Obtiene datos de un indicador específico desde la API del Banco Mundial."""
    try:
        nombre_columna = INDICADORES.get(codigo_indicador, {}).get('nombre', codigo_indicador)
        resultados = []
        
        # Ajustar el rango de años si es necesario
        anio_actual = pd.Timestamp.now().year
        anio_fin_ajustado = min(anio_fin, anio_actual)
        
        if anio_fin_ajustado < anio_fin:
            st.warning(f"El año máximo disponible es {anio_fin_ajustado}. Ajustando...")
            anio_fin = anio_fin_ajustado
        
        # Solo consultamos los países seleccionados
        codigos_a_consultar = codigos_paises
        
        with st.spinner(f"Obteniendo datos de {nombre_columna}..."):
            for pais in codigos_a_consultar:
                try:
                    datos = wb.get_series(
                        codigo_indicador,
                        country=pais,
                        date=f"{anio_inicio}:{anio_fin}",
                        id_or_value='id',
                        simplify_index=True,
                        raise_on_error=False
                    )
                    if datos is None or datos.empty:
                        # Solo mostrar advertencia para los países seleccionados originalmente
                        if pais in codigos_paises:
                            st.warning(f"No se encontraron datos para {obtener_nombre_pais(pais)} en el rango {anio_inicio}-{anio_fin}")
                        continue
                        
                    if isinstance(datos, pd.Series):
                        df_pais = datos.reset_index()
                        if len(df_pais.columns) == 2:
                            df_pais.columns = ['anio', 'valor']
                            df_pais['codigo_pais'] = pais
                        elif len(df_pais.columns) == 3:
                            df_pais.columns = ['codigo_pais', 'anio', 'valor']
                        else:
                            st.warning(f"Formato de datos inesperado para {pais}")
                            continue
                            
                        if 'valor' not in df_pais.columns or 'anio' not in df_pais.columns:
                            st.warning(f"Datos incompletos para {pais}")
                            continue
                            
                        df_pais['anio'] = pd.to_numeric(df_pais['anio'], errors='coerce')
                        df_pais['valor'] = pd.to_numeric(df_pais['valor'], errors='coerce')
                        df_pais = df_pais.dropna(subset=['anio', 'valor'])
                        
                        # Solo agregar si hay datos válidos
                        if not df_pais.empty:
                            df_pais['pais'] = df_pais['codigo_pais'].apply(obtener_nombre_pais)
                            df_pais['indicador'] = nombre_columna
                            df_pais['codigo_indicador'] = codigo_indicador
                            if 'pib_per_capita_usd' not in df_pais.columns and 'valor' in df_pais.columns:
                                df_pais['pib_per_capita_usd'] = df_pais['valor']
                            
                            # Marcar si es un país originalmente seleccionado o no
                            df_pais['seleccionado'] = pais in codigos_paises
                            resultados.append(df_pais)
                except Exception as e:
                    if pais in codigos_paises:  # Solo mostrar error para países seleccionados
                        st.error(f"Error al obtener datos para {obtener_nombre_pais(pais)}: {str(e)}")
                    continue
        
        if not resultados:
            return pd.DataFrame()
            
        df_final = pd.concat(resultados, ignore_index=True)
        
        # Ordenar para que los países seleccionados aparezcan primero en las leyendas
        df_final = df_final.sort_values(['seleccionado', 'pais', 'anio'], ascending=[False, True, True])
        
        # Asegurar que tenemos todas las columnas necesarias
        if 'pib_per_capita_usd' not in df_final.columns and 'valor' in df_final.columns:
            df_final['pib_per_capita_usd'] = df_final['valor']
            
        # Seleccionar columnas de salida
        columnas_salida = ['codigo_pais', 'pais', 'anio', 'valor', 'pib_per_capita_usd', 'indicador', 'codigo_indicador']
        columnas_salida = [col for col in columnas_salida if col in df_final.columns]
        
        return df_final[columnas_salida]
                
    except Exception as e:
        st.error(f"Error al obtener datos del indicador {codigo_indicador}: {str(e)}")
        import traceback
        st.text(traceback.format_exc())
        return pd.DataFrame()

def obtener_datos_multiples_indicadores(codigos_indicadores: List[str], codigos_paises: List[str], anio_inicio: int, anio_fin: int) -> Dict[str, pd.DataFrame]:
    """Obtiene datos para múltiples indicadores y los devuelve en un diccionario."""
    datos_por_indicador = {}
    
    # Asegurar que el rango de años sea válido
    anio_actual = pd.Timestamp.now().year
    anio_fin = min(anio_fin, anio_actual)
    
    if anio_inicio > anio_fin:
        st.error("El año de inicio no puede ser mayor al año final")
        return {}
    
    for codigo in codigos_indicadores:
        try:
            df = obtener_datos_indicador(codigo, codigos_paises, anio_inicio, anio_fin)
            if not df.empty:
                datos_por_indicador[codigo] = df
            else:
                nombre_indicador = INDICADORES.get(codigo, {}).get('nombre', codigo)
                st.warning(f"No se encontraron datos para el indicador: {nombre_indicador} ({codigo})")
        except Exception as e:
            nombre_indicador = INDICADORES.get(codigo, {}).get('nombre', codigo)
            st.error(f"Error al obtener datos para {nombre_indicador} ({codigo}): {str(e)}")
    
    if not datos_por_indicador:
        st.error("No se pudieron obtener datos para ningún indicador. Por favor intenta con otros parámetros.")
    
    return datos_por_indicador

def crear_grafico_pib(df: pd.DataFrame, anio_inicio: int, anio_fin: int) -> None:
    """Crea y muestra un gráfico de líneas con los datos de PIB."""
    if df.empty:
        st.warning("No hay datos para mostrar en el gráfico.")
        return
        
    fig = px.line(
        df, 
        x='anio', 
        y='pib_per_capita_usd',
        color='pais',
        title=f'PIB per cápita (USD) - {anio_inicio} a {anio_fin}',
        labels={
            'pib_per_capita_usd': 'PIB per cápita (USD)', 
            'anio': 'Año',
            'pais': 'País'
        },
        markers=True
    )
    
    fig.update_layout(
        hovermode='x unified',
        xaxis_title='Año',
        yaxis_title='PIB per cápita (USD)',
        legend_title='País',
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)

def mostrar_sidebar() -> Tuple[List[str], List[str], int, int]:
    """Muestra la barra lateral y devuelve la configuración."""
    st.sidebar.header("Configuración")
    
    # Selección de indicadores
    st.sidebar.subheader("Indicadores Económicos")
    opciones_indicadores = [
        f"{datos['nombre']} ({codigo})" 
        for codigo, datos in INDICADORES.items()
    ]
    
    # Establecer PIB per cápita como selección por defecto
    indice_por_defecto = [i for i, opcion in enumerate(opciones_indicadores) 
                         if 'NY.GDP.PCAP.CD' in opcion]
    
    indicadores_seleccionados = st.sidebar.multiselect(
        "Selecciona uno o más indicadores:",
        options=opciones_indicadores,
        default=[opciones_indicadores[i] for i in indice_por_defecto],
        help="Selecciona los indicadores económicos que deseas analizar"
    )
    
    # Extraer códigos de indicadores seleccionados
    codigos_indicadores = [
        opcion.split('(')[-1].rstrip(')') 
        for opcion in indicadores_seleccionados
    ]
    
    # Selección de países
    st.sidebar.subheader("Países")
    paises_disponibles = [f"{datos['nombre']} ({codigo})" for codigo, datos in PAISES.items()]
    paises_seleccionados = st.sidebar.multiselect(
        "Selecciona uno o más países:",
        options=paises_disponibles,
        default=[paises_disponibles[0]],  # México por defecto
        help="Selecciona los países que deseas comparar"
    )
    
    # Extraer códigos de países seleccionados
    codigos_paises = [p.split('(')[-1].rstrip(')') for p in paises_seleccionados]
    
    # Rango de años
    st.sidebar.subheader("Rango de Años")
    anio_actual = datetime.now().year
    anio_inicio = st.sidebar.slider(
        "Año de inicio:",
        min_value=1960,
        max_value=anio_actual,
        value=anio_actual - 10,
        step=1,
        help="Selecciona el año de inicio para el análisis"
    )
    
    anio_fin = st.sidebar.slider(
        "Año final:",
        min_value=1960,
        max_value=anio_actual,
        value=anio_actual,
        step=1,
        help="Selecciona el año final para el análisis"
    )
    
    # Asegurar que el año final sea mayor o igual al año de inicio
    if anio_fin < anio_inicio:
        st.sidebar.warning("El año final no puede ser menor al año de inicio. Ajustando...")
        anio_fin = anio_inicio
    
    return codigos_indicadores, codigos_paises, anio_inicio, anio_fin

def get_download_link(content: bytes, filename: str, button_text: str, file_type: str) -> str:
    """Genera un enlace para descargar contenido en diferentes formatos."""
    b64 = base64.b64encode(content).decode()
    mime_types = {
        'csv': 'text/csv',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'pdf': 'application/pdf',
        'svg': 'image/svg+xml'
    }
    mime_type = mime_types.get(file_type.lower(), 'application/octet-stream')
    href = f'<a href="data:{mime_type};base64,{b64}" download="{filename}">{button_text}</a>'
    return href

def get_table_download_link(df: pd.DataFrame, filename: str, button_text: str) -> str:
    """Genera un enlace para descargar un DataFrame como archivo CSV o Excel."""
    if filename.endswith('.csv'):
        content = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        return get_download_link(content, filename, button_text, 'csv')
    elif filename.endswith('.xlsx'):
        towrite = io.BytesIO()
        df.to_excel(towrite, index=False, engine='openpyxl')
        return get_download_link(towrite.getvalue(), filename, button_text, 'xlsx')
    return ""

def get_figure_download_link(fig, filename: str, button_text: str, width: int = 1200, height: int = 700) -> str:
    """Genera un enlace para descargar una figura de Plotly como imagen."""
    try:
        # Determinar el formato basado en la extensión del archivo
        if filename.lower().endswith('.png'):
            img_bytes = fig.to_image(format='png', width=width, height=height, scale=2)
            mime_type = 'image/png'
        elif filename.lower().endswith(('.jpg', '.jpeg')):
            img_bytes = fig.to_image(format='jpeg', width=width, height=height, scale=2)
            mime_type = 'image/jpeg'
        elif filename.lower().endswith('.pdf'):
            img_bytes = fig.to_image(format='pdf', width=width, height=height)
            mime_type = 'application/pdf'
        elif filename.lower().endswith('.svg'):
            img_bytes = fig.to_image(format='svg', width=width, height=height)
            mime_type = 'image/svg+xml'
        else:
            return "Formato de archivo no soportado"
        
        # Codificar en base64
        b64 = base64.b64encode(img_bytes).decode()
        
        # Crear enlace de descarga
        href = f'<a href="data:{mime_type};base64,{b64}" download="{filename}">{button_text}</a>'
        return href
        
    except Exception as e:
        st.error(f"Error al generar el enlace de descarga: {str(e)}")
        return ""

def mostrar_datos_tabulares(datos_por_indicador: Dict[str, pd.DataFrame]):
    """Muestra los datos en formato tabular organizados por indicador con opciones de exportación."""
    for codigo_indicador, df in datos_por_indicador.items():
        if df.empty:
            continue
            
        nombre_indicador = INDICADORES.get(codigo_indicador, {}).get('nombre', codigo_indicador)
        st.subheader(nombre_indicador)
        
        # Obtener la columna de valor correcta
        valor_col = 'valor' if 'valor' in df.columns else 'pib_per_capita_usd'
        
        # Preparar datos para mostrar
        df_pivot = df.pivot_table(
            index='anio',
            columns='pais',
            values=valor_col,
            aggfunc='first'
        ).round(2)
        
        # Mostrar tabla con los datos
        st.dataframe(df_pivot, use_container_width=True)
        
        # Botones de exportación
        col1, col2, _ = st.columns([1, 1, 3])
        
        with col1:
            st.markdown(get_table_download_link(
                df_pivot.reset_index(), 
                f"{nombre_indicador.replace(' ', '_')}.csv", 
                "📥 Descargar CSV"
            ), unsafe_allow_html=True)
            
        with col2:
            st.markdown(get_table_download_link(
                df_pivot.reset_index(),
                f"{nombre_indicador.replace(' ', '_')}.xlsx",
                "📥 Descargar Excel"
            ), unsafe_allow_html=True)

def crear_grafico_indicador(df: pd.DataFrame, codigo_indicador: str, anio_inicio: int, anio_fin: int) -> None:
    """Crea y muestra un gráfico interactivo con múltiples opciones de visualización."""
    if df.empty:
        st.warning(f"No hay datos disponibles para el indicador: {codigo_indicador}")
        return
    
    # Obtener metadatos del indicador
    nombre_indicador = INDICADORES.get(codigo_indicador, {}).get('nombre', codigo_indicador)
    unidad = INDICADORES.get(codigo_indicador, {}).get('unidad', '')
    
    # Determinar la columna de valor
    valor_col = 'valor' if 'valor' in df.columns else 'pib_per_capita_usd'
    
    # Filtrar por rango de años
    df_filtrado = df[(df['anio'] >= anio_inicio) & (df['anio'] <= anio_fin)].copy()
    
    if df_filtrado.empty:
        st.warning(f"No hay datos disponibles para el rango de años seleccionado: {anio_inicio}-{anio_fin}")
        return
    
    # Opciones de visualización
    with st.sidebar.expander("⚙️ Opciones de visualización", expanded=True):
        tipo_grafico = st.selectbox(
            "Tipo de gráfico",
            ["Línea", "Barras", "Área"],
            key=f"tipo_grafico_{codigo_indicador}"
        )
        
        # Opción para mostrar líneas de tendencia
        mostrar_tendencia = st.checkbox(
            "Mostrar línea de tendencia",
            value=False,
            key=f"tendencia_{codigo_indicador}"
        )
        
        # Opciones de promedios
        st.markdown("**Promedios a incluir:**")
        col1, col2 = st.columns(2)
        with col1:
            mostrar_promedio_mundo = st.checkbox(
                "Mundial",
                value=True,
                key=f"prom_mundo_{codigo_indicador}",
                help="Mostrar promedio mundial"
            )
        with col2:
            mostrar_promedio_region = st.checkbox(
                "Regionales",
                value=True,
                key=f"prom_region_{codigo_indicador}",
                help="Mostrar promedios regionales relevantes"
            )
    
    # Agregar promedios si está habilitado
    df_original = df_filtrado.copy()
    if mostrar_promedio_mundo or mostrar_promedio_region:
        df_filtrado = agregar_promedios(
            df_original,
            incluir_mundo=mostrar_promedio_mundo,
            incluir_regiones=mostrar_promedio_region
        )
    
    # Crear gráfico según el tipo seleccionado
    if tipo_grafico == "Línea":
        # Asegurar que los datos tengan el formato correcto
        if 'anio' not in df_filtrado.columns or valor_col not in df_filtrado.columns or 'pais' not in df_filtrado.columns:
            st.error("Error: Datos incompletos para generar el gráfico")
            return
        
        # Asegurar que los tipos de datos sean correctos
        df_plot = df_filtrado.copy()
        df_plot['anio'] = pd.to_numeric(df_plot['anio'], errors='coerce')
        df_plot[valor_col] = pd.to_numeric(df_plot[valor_col], errors='coerce')
        
        # Identificar promedios para el estilo de línea
        df_plot['es_promedio'] = df_plot['pais'].str.startswith('Promedio ')
        
        # Ordenar los datos: primero por si es promedio (para el z-index), luego por país y año
        df_plot = df_plot.sort_values(['es_promedio', 'pais', 'anio'])
        
        # Crear el gráfico con configuración mejorada
        fig = px.line(
            df_plot,
            x='anio',
            y=valor_col,
            color='pais',
            title=f"{nombre_indicador} ({anio_inicio}-{anio_fin})",
            labels={
                'anio': 'Año', 
                valor_col: f"{nombre_indicador} {f'({unidad})' if unidad else ''}", 
                'pais': 'País'
            },
            markers=True,
            line_shape='linear',
            template='plotly_white'
        )
        
        # Actualizar el estilo de línea para los promedios
        for trace in fig.data:
            if trace.name and trace.name.startswith('Promedio'):
                trace.line.dash = 'dash'
        
        # Asegurar que las líneas se conecten correctamente
        fig.update_traces(connectgaps=False)
    elif tipo_grafico == "Barras":
        fig = px.bar(
            df_filtrado,
            x='anio',
            y=valor_col,
            color='pais',
            title=f"{nombre_indicador} ({anio_inicio}-{anio_fin})",
            labels={'anio': 'Año', valor_col: nombre_indicador, 'pais': 'País'},
            barmode='group',
            template='plotly_white'
        )
    else:  # Área
        fig = px.area(
            df_filtrado,
            x='anio',
            y=valor_col,
            color='pais',
            title=f"{nombre_indicador} ({anio_inicio}-{anio_fin})",
            labels={'anio': 'Año', valor_col: nombre_indicador, 'pais': 'País'},
            template='plotly_white'
        )
    
    # Añadir línea de tendencia si está habilitado
    if mostrar_tendencia and tipo_grafico in ["Línea", "Área"]:
        # Solo agregar tendencia a los países, no a los promedios
        for trace in fig.data:
            if not trace.name.startswith('Promedio'):  # No agregar tendencia a los promedios
                x_vals = np.array(trace.x)
                y_vals = np.array(trace.y)
                
                # Filtrar valores NaN
                mask = ~np.isnan(x_vals) & ~np.isnan(y_vals)
                x_vals = x_vals[mask]
                y_vals = y_vals[mask]
                
                if len(x_vals) > 1:  # Necesitamos al menos 2 puntos para una línea de tendencia
                    try:
                        # Ajuste polinómico de grado 1 (línea recta)
                        z = np.polyfit(x_vals, y_vals, 1)
                        p = np.poly1d(z)
                        
                        # Crear puntos para la línea de tendencia
                        x_trend = np.linspace(min(x_vals), max(x_vals), 100)
                        y_trend = p(x_trend)
                        
                        # Determinar el color basado en el tipo de gráfico
                        line_color = trace.line.color if hasattr(trace, 'line') and hasattr(trace.line, 'color') else trace.fillcolor
                        
                        # Agregar la línea de tendencia
                        fig.add_scatter(
                            x=x_trend,
                            y=y_trend,
                            mode='lines',
                            name=f"Tendencia {trace.name}",
                            line=dict(dash='dash', width=2, color=line_color),
                            showlegend=True,
                            opacity=0.7,
                            hoverinfo='skip',  # No mostrar información al pasar el mouse
                            legendgroup=trace.name  # Agrupar con la traza original
                        )
                    except Exception as e:
                        st.warning(f"No se pudo calcular la tendencia para {trace.name}")
    
    # Añadir anotaciones para valores máximos y mínimos
    for pais in df_filtrado['pais'].unique():
        df_pais = df_filtrado[df_filtrado['pais'] == pais]
        if not df_pais.empty:
            max_idx = df_pais[valor_col].idxmax()
            min_idx = df_pais[valor_col].idxmin()
            
            # Añadir anotación para el valor máximo
            fig.add_annotation(
                x=df_pais.loc[max_idx, 'anio'],
                y=df_pais.loc[max_idx, valor_col],
                text=f"Máx: {df_pais.loc[max_idx, valor_col]:.2f}",
                showarrow=True,
                arrowhead=1,
                ax=0,
                ay=-40,
                bgcolor='white',
                bordercolor='black',
                borderwidth=1,
                borderpad=4,
                opacity=0.8
            )
            
            # Añadir anotación para el valor mínimo si es significativamente diferente
            if df_pais.loc[min_idx, valor_col] < df_pais[valor_col].mean() * 0.9:  # Solo si es al menos 10% menor que el promedio
                fig.add_annotation(
                    x=df_pais.loc[min_idx, 'anio'],
                    y=df_pais.loc[min_idx, valor_col],
                    text=f"Mín: {df_pais.loc[min_idx, valor_col]:.2f}",
                    showarrow=True,
                    arrowhead=1,
                    ax=0,
                    ay=40,
                    bgcolor='white',
                    bordercolor='black',
                    borderwidth=1,
                    borderpad=4,
                    opacity=0.8
                )
    
    # Mejorar el diseño del gráfico
    fig.update_layout(
        hovermode='x unified',
        xaxis_title='Año',
        yaxis_title=f"{nombre_indicador} ({unidad})",
        legend_title='País',
        height=600,
        showlegend=len(df_filtrado['pais'].unique()) > 1,
        margin=dict(l=50, r=50, t=80, b=50),
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Arial"
        )
    )
    
    # Mejorar los tooltips
    fig.update_traces(
        hovertemplate="<b>%{x}</b><br>" +
                    f"<b>{nombre_indicador}:</b> %{{y:,.2f}} {unidad}<br>" +
                    "<extra></extra>"
    )
    
    # Mostrar el gráfico
    st.plotly_chart(fig, use_container_width=True)
    
    # Opciones de exportación
    with st.expander("💾 Exportar gráfico", expanded=False):
        st.markdown("**Exportar como imagen:**")
        col1, col2, col3, col4 = st.columns(4)
        
        nombre_archivo = f"{nombre_indicador.replace(' ', '_')}_{anio_inicio}-{anio_fin}"
        
        with col1:
            st.markdown(get_figure_download_link(
                fig, 
                f"{nombre_archivo}.png", 
                "📷 PNG",
                width=1200,
                height=700
            ), unsafe_allow_html=True)
            
        with col2:
            st.markdown(get_figure_download_link(
                fig,
                f"{nombre_archivo}.jpg",
                "🖼️ JPG",
                width=1200,
                height=700
            ), unsafe_allow_html=True)
            
        with col3:
            st.markdown(get_figure_download_link(
                fig,
                f"{nombre_archivo}.pdf",
                "📄 PDF",
                width=1200,
                height=700
            ), unsafe_allow_html=True)
            
        with col4:
            st.markdown(get_figure_download_link(
                fig,
                f"{nombre_archivo}.svg",
                "🖌️ SVG",
                width=1200,
                height=700
            ), unsafe_allow_html=True)
    
    # Mostrar estadísticas resumidas
    with st.expander("📊 Estadísticas resumidas", expanded=False):
        # Calcular estadísticas básicas
        stats = df_filtrado.groupby('pais')[valor_col].agg(['mean', 'min', 'max', 'std']).round(2)
        stats.columns = ['Promedio', 'Mínimo', 'Máximo', 'Desv. Estándar']
        
        # Identificar promedios
        promedios = stats[stats.index.str.startswith('Promedio')]
        paises = stats[~stats.index.str.startswith('Promedio')]
        
        # Si hay promedios, calcular diferencias porcentuales
        if not promedios.empty and not paises.empty:
            st.markdown("### Comparación con promedios")
            
            # Para cada país, comparar con cada promedio
            comparaciones = []
            for idx, pais in paises.iterrows():
                for prom_idx, promedio in promedios.iterrows():
                    dif_promedio = ((pais['Promedio'] - promedio['Promedio']) / promedio['Promedio'] * 100).round(2)
                    comparacion = {
                        'País': idx,
                        'Promedio': prom_idx.replace('Promedio ', ''),
                        'Valor': pais['Promedio'],
                        'Promedio Valor': promedio['Promedio'],
                        'Diferencia %': dif_promedio,
                        'Comparación': 'Mayor' if dif_promedio > 0 else 'Menor' if dif_promedio < 0 else 'Igual'
                    }
                    comparaciones.append(comparacion)
            
            # Mostrar tabla de comparación
            if comparaciones:
                df_comparacion = pd.DataFrame(comparaciones)
                st.dataframe(
                    df_comparacion.pivot_table(
                        index='País',
                        columns='Promedio',
                        values='Diferencia %',
                        aggfunc='first'
                    ).style.format('{:.2f}%').applymap(
                        lambda x: 'color: green' if x > 0 else 'color: red' if x < 0 else 'color: gray'
                    ),
                    use_container_width=True
                )
        
        # Mostrar estadísticas completas
        st.markdown("### Estadísticas detalladas")
        st.dataframe(
            stats.style.format('{:,.2f}'),
            use_container_width=True
        )
        
        # Nota explicativa
        st.caption("ℹ️ Los valores positivos en la comparación indican que el país está por encima del promedio.")

def main():
    # Configurar la página
    configurar_pagina()
    st.write("Visualización de datos económicos del Banco Mundial")
    
    # Obtener configuración de la barra lateral
    codigos_indicadores, codigos_paises, anio_inicio, anio_fin = mostrar_sidebar()
    
    # Verificar selección
    if not codigos_indicadores:
        st.warning("Por favor selecciona al menos un indicador económico.")
        return
        
    if not codigos_paises:
        st.warning("Por favor selecciona al menos un país.")
        return
    
    try:
        # Mostrar indicadores seleccionados
        with st.expander("🔍 Indicadores seleccionados", expanded=True):
            cols = st.columns(3)
            for i, codigo in enumerate(codigos_indicadores):
                with cols[i % 3]:
                    st.metric(
                        label=INDICADORES.get(codigo, {}).get('nombre', codigo),
                        value=INDICADORES.get(codigo, {}).get('unidad', '')
                    )
        
        # Obtener datos
        with st.spinner("Cargando datos..."):
            datos_por_indicador = obtener_datos_multiples_indicadores(
                codigos_indicadores,
                codigos_paises,
                anio_inicio,
                anio_fin
            )
            
            if not datos_por_indicador:
                st.error("No se pudieron obtener los datos. Por favor intenta con otros parámetros.")
                return
            
            # Limpiar y procesar los datos
            for codigo, df in datos_por_indicador.items():
                if not df.empty:
                    datos_por_indicador[codigo] = limpiar_datos(df)
        
        # Mostrar pestañas para cada indicador
        tabs = st.tabs([INDICADORES.get(codigo, {}).get('nombre', codigo) for codigo in codigos_indicadores])
        
        for idx, codigo_indicador in enumerate(codigos_indicadores):
            with tabs[idx]:
                df = datos_por_indicador.get(codigo_indicador, pd.DataFrame())
                if not df.empty:
                    crear_grafico_indicador(df, codigo_indicador, anio_inicio, anio_fin)
                else:
                    st.warning(f"No hay datos disponibles para {INDICADORES.get(codigo_indicador, {}).get('nombre', codigo_indicador)}")
        
        # Mostrar datos tabulares en una sección colapsable
        with st.expander("📊 Ver datos tabulares", expanded=False):
            mostrar_datos_tabulares(datos_por_indicador)
    
    except Exception as e:
        st.error(f"❌ Error al procesar los datos: {str(e)}")
        st.exception(e)
        
        # Información adicional para depuración
        st.markdown("""
        ### Solución de problemas
        1. Verifica tu conexión a Internet
        2. Intenta con un rango de años diferente
        3. Verifica que los países seleccionados tengan datos disponibles
        4. Si el problema persiste, intenta recargar la página
        """)

if __name__ == "__main__":
    main()
