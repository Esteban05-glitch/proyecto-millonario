import world_bank_data as wb
import pandas as pd

def test_connection():
    print("Probando conexión con la API del Banco Mundial...")
    
    try:
        # Intentar obtener datos de un indicador común (PIB per cápita)
        print("Obteniendo datos de PIB per cápita para México...")
        data = wb.get_series('NY.GDP.PCAP.CD', country='MEX', mrv=5)  # Últimos 5 años
        
        if not data.empty:
            print("¡Conexión exitosa! Datos obtenidos:")
            print(data)
            return True
        else:
            print("No se encontraron datos. La conexión se estableció pero no hay datos disponibles.")
            return False
            
    except Exception as e:
        print(f"Error al conectar con la API del Banco Mundial: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection()
