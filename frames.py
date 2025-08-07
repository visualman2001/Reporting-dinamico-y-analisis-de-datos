"""
Script de análisis y procesamiento de datos para uso combinado con SQL Server o archivos locales.

Funcionalidades:
- Conexión a SQL Server usando pyodbc.
- Carga de datos desde CSV, Excel o comandos SQL.
- Agrupaciones, cálculos, campos derivados y pivoteo dinámico.
- Exportación a CSV o Excel con formato numérico.
- Salida por consola en JSON o DataFrame legible.
- Control total por argumentos vía sys.argv.
- Opcionalmente retorna un XLSX a SQL SERVER
- Permite filtrar por diccionario {campo: [comparacion, valor]}
  comparaciones: "==", "!=", ">", "<", ">=", "<=", "in", "not in", "contains", "startswith", "endswith"
  que son los más comunes pero pueden anexarse más
- Permite ordenar por diccionario {campo: orden}
  órdenes válidos: "asc" o "desc"
- Permite establecer un filtro luego del agrupamiento o pivot {campo: [comparacion, valor]}
  comparaciones: "==", "!=", ">", "<", ">=", "<=", "in", "not in", "contains", "startswith", "endswith"
  que son los más comunes pero pueden anexarse más

Autor: Francisco Pablo Zaidman
Fecha: 04-08-2025 al 06-08-2025
Versión: 1.0
"""
import pandas as pd
import pyodbc as db
import ast
import sys
import warnings
import os
import base64
import logging
from datetime import datetime
from pathlib import Path

# Silencio el warning molesto de Pandas (describrí que Pandas "bufa" con pyodbc)
warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy")

# Configuro el logger (ChtGPT)
logging.basicConfig(
    filename="frames.log",
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S")

# En "producción" sacar el hardcodeo (usaría variables de entorno)
# de momento es testeo de uso interno
def conectar() -> db.Connection:
    # Conecto a la base de datos
    try:
        conn = db.connect('Driver={SQL Server};'
                          'Server=< tu servidor >;'
                          'Database=< tu base >;'
                          'UID=< tu usuario >;'
                          'PWD=< tu clave >;')

    except Exception as e:
        logging.error("Error al abrir la conexión: %s", str(e))
        print("Ocurrió un error al abrir la conexión:\n", e)
        sys.exit(1)

    # Cargo la función
    return conn

# Infaltable así no se daña la base de datos
def desconectar(conn):
    # Cierro la conexión
    conn.close()

# Uso lector de propio Pandas (si llego acá es un string con select o stored procedure)
# si es SQL lo contruyo yo evitando inyección de código malicioso
def devolver(comando:str) -> pd.DataFrame:
    # Conecto a la base de datos
    conn = conectar()

    # Recupero los datos a dataframe
    try:
        df = pd.read_sql(comando, conn)

    except Exception as e:
        logging.error("Error al intentar leer datos: %s", str(e))
        print("Ocurrió un error al intentar leer datos:\n", e)
        sys.exit(1)

    finally:
        # Desconecto la base de datos
        desconectar(conn)

    # Cargo la función
    return df

def obtener_datos(origen) -> pd.DataFrame:
    # Defino valor a retornar
    valor = None

    # Verifico el tipo de origen (a que instancia corresponde)
    if isinstance(origen, str):
        if origen.endswith(".csv"):
            valor = pd.read_csv(origen)
        elif origen.endswith(".xlsx"):
            valor = pd.read_excel(origen, sheet_name=0)
        else:
            valor = devolver(origen) # stored o sentencia sql
    elif isinstance(origen, pd.DataFrame):
        valor = origen
    else:
        logging.error("Origen no válido. Debe ser string (ruta a archivo CSV o sentencia SQL) o DataFrame.")
        raise TypeError("Origen no válido. Debe ser string (ruta a archivo CSV o sentencia SQL) o DataFrame.")

    # Cargo la función
    return valor

def campos_derivados(df:pd.DataFrame, calculados:dict | None) -> pd.DataFrame:
    # Recorro los campos derivados (si no es vacío)
    if calculados is not None:
        for campo, formula in calculados.items():
            df[campo] = df.eval(formula)

    # Cargo la función
    return df

def filtrar(df:pd.DataFrame, filtro:dict | None) -> pd.DataFrame:
    # Recorro los filtros (si no es vacío)
    # (dict {campo: [comparacion, valor]} ejemplo: {'descripcion': ['==', 'REMERA']}) 
    if filtro is not None:
        for campo, valor in filtro.items():
            if isinstance(valor, list) and len(valor) == 2:
                operador, valor = str(valor[0]).lower(), valor[1]
                if operador == "==":
                    df = df[df[campo] == valor]
                elif operador == "!=":
                    df = df[df[campo] != valor]
                elif operador == ">":
                    df = df[df[campo] > valor]
                elif operador == "<":
                    df = df[df[campo] < valor]
                elif operador == ">=":
                    df = df[df[campo] >= valor]
                elif operador == "<=":
                    df = df[df[campo] <= valor]
                elif operador == "in":
                    df = df[df[campo].isin(valor)]
                elif operador == "not in":
                    df = df[~df[campo].isin(valor)]
                elif operador == "contains":
                    df = df[df[campo].astype(str).str.contains(valor, na=False)]
                elif operador == "startswith":
                    df = df[df[campo].astype(str).str.startswith(valor, na=False)]
                elif operador == "endswith":
                    df = df[df[campo].astype(str).str.endswith(valor, na=False)]

    # Cargo la función
    return df

def ordenar(df: pd.DataFrame, orden: dict | None) -> pd.DataFrame:
    # Ordeno el resultado
    if orden is not None:
        columnas = list(orden.keys())
        ascendente = [True if str(orden[col]).lower() == "asc" else False for col in columnas]
        df = df.sort_values(by=columnas, ascending=ascendente)

    # Cargo la función
    return df

def exportar(df:pd.DataFrame, destino:str | None, mostrar:bool) -> None:
    # Verifico si hay destino y si debo abrirlo (sólo en Windwos)
    if mostrar == True and destino is not None:
        # Verifico la extensión del archivo
        if destino.endswith(".csv"):
            df.to_csv(destino, index=True)
        elif destino.endswith(".xlsx"):
            df.to_excel(destino, index=True)

        # Abrir automáticamente si el archivo existe (sólo en Windwos)
        if os.path.exists(destino) and os.name == "nt":
            os.startfile(destino)

##############################
# Cuerpo principal del scrip #
##############################

# Guardo cantidad de argumentos pasado para control
logging.info("Inicio de ejecución con argumentos: %s", str(sys.argv[1:]))

# Verifico cantidad de argumentos
if len(sys.argv) < 2:
    logging.error("Faltan argumentos. El origen no puede omitirse.")
    print("Faltan argumentos. El origen no puede omitirse.")
    sys.exit(1)

# Recupero la lista de argumentos
origen = sys.argv[1] # único argumento obligatorio

# Verifico argumentos opcionales (uso eval sino los toma como str)
agrupacion = ast.literal_eval(sys.argv[2]) if len(sys.argv) > 2 else None
acciones = ast.literal_eval(sys.argv[3]) if len(sys.argv) > 3 else None
calculados = ast.literal_eval(sys.argv[4]) if len(sys.argv) > 4 else None
destino = sys.argv[5] if len(sys.argv) > 5 else None
pivoteo = ast.literal_eval(sys.argv[6]) if len(sys.argv) > 6 else None

# Mostrar es si quiero verlo legible por consola (True) o 
# sino (False) devueve JSON para ser consumido por SQL
mostrar = sys.argv[7].lower() in ("true", "1", "yes") if len(sys.argv) > 7 else False

# Verifico los decimales antes de la conversión
# convirto primero a float que es menos quisquilloso
try:
    decimales = int(float(sys.argv[8])) if len(sys.argv) > 8 else 0

except Exception as e:
    decimales = 0

# Argumento adicional: retornar_base64 (por defecto False)
# es por si quiero que SQL me devuelve un Excel en lugar de un key-value para
# generar datatable desde mi app VB.NET.
retornar_base64 = sys.argv[9].lower() in ("true", "1", "yes") if len(sys.argv) > 9 else False

# Filtro (dict {campo: [comparacion, valor]} ejemplo {'descripcion': ['==', 'REMERA']}) 
filtro = ast.literal_eval(sys.argv[10]) if len(sys.argv) > 10 else None

# Ordenamiento (dict {campo: orden]} ejemplo {'descripcion': 'asc', 'precio': 'desc'}) 
orden = ast.literal_eval(sys.argv[11]) if len(sys.argv) > 11 else None

# Filtro final (post agrupación o pivoteo)
filtro_final = ast.literal_eval(sys.argv[12]) if len(sys.argv) > 12 else None

# Si no hay agrupación ni pivoteo, desactivo filtro_final por completo
if agrupacion is None and pivoteo is None:
    filtro_final = None

# Inicializo variables de trabajo
df = obtener_datos(origen)

# Cargo campos calculados (derivados)
df = campos_derivados(df, calculados)

# Verifico si hay filtro (propuesto Amazon Q)
# Cargo el filtro
df = filtrar(df, filtro)

# Inicializo variables de devolver
resultado = None

# Verifico si hay pivoteo
if pivoteo is not None:
    resultado = df.pivot_table(**pivoteo) # propuesto Amazon Q (formato **pivoteo)
elif agrupacion is not None and acciones is not None:
    resultado = df.groupby(agrupacion).agg(acciones).reset_index()
elif agrupacion is not None and acciones is None:
    resultado = df.groupby(agrupacion).size().reset_index(name="cantidad") # hacerlo legible (ChatGPT)
elif agrupacion is None and acciones is not None:
    resultado = df.agg(acciones).reset_index()
else:
    resultado = df

# Redondeo números a "n" decimales
if decimales != 0:
    resultado = resultado.round(decimales)

# Filtro post-agrupación / pivot (uso misma función que para el filtro común)
resultado = filtrar(resultado, filtro_final)

# Ordeno el resultado
resultado = ordenar(resultado, orden)

# Verifico si hay destino y si debo abrirlo (sólo en Windwos)
exportar(resultado, destino, mostrar)

# Imprimo para devolver a consola o a SQL (mostrar = True es legible de consola)
try:
    if mostrar == True:
        print(resultado)  # salida legible para consola
        sys.stdout.flush() # Asegura todo el "volcado" de buffer

    else:
        if destino != "" and destino.strip().lower() != "none":
            # Graba CSV si corresponde
            if destino.lower().endswith(".csv"):
                resultado.to_csv(destino, index=True, encoding="utf-8-sig")
            elif destino.lower().endswith(".xlsx"):
                resultado.to_excel(destino, index=True)
        else:
            # Devuelve JSON a consola
            json_resultado = resultado.reset_index().to_json(orient="records", force_ascii=False)
            print(json_resultado)
            sys.stdout.flush() # Asegura todo el "volcado" de buffer

            # Si hay destino definido, guarda JSON a archivo
            if destino and destino.strip().lower() != "none":
                ruta_json = Path(destino).with_suffix('.json')
                with open(ruta_json, 'w', encoding='utf-8') as f:
                    f.write(json_resultado)

    # Si se solicita base64 y el archivo existe (ChatGPT)
    if retornar_base64 and destino and destino.lower().endswith(".xlsx") and os.path.exists(destino):
        with open(destino, "rb") as f:
            contenido = f.read()
            base64_excel = base64.b64encode(contenido).decode("utf-8")
            print(base64_excel)
            sys.stdout.flush() # Asegura todo el "volcado" de buffer
        
        # Borro el archivo para no dejar "residuos"
        try:
            os.remove(destino)
        except Exception as e:
            print("No se pudo borrar el archivo temporal:", e)
        
        sys.exit(0)

except Exception as e:
    logging.error(f"ERROR_JSON: {str(e)}")
    print(f"ERROR_JSON: {str(e)}")
    sys.stdout.flush()
