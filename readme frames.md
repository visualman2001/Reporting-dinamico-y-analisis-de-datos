# frames.py — Referencia de argumentos

Este script procesa datos desde SQL o archivo y permite agrupaciones, cálculos, filtros, pivoteos y salida como Excel o JSON.  
Todos los argumentos son posicionales. Si no se usa alguno, debe pasarse como `"None"` o equivalente.

---

## 📌 Argumentos esperados

1. **origen** (str) — Obligatorio  
   Consulta SQL o ruta a archivo `.csv` o `.xlsx`.  

   Ejemplo:  
   - `"SELECT * FROM dfacturas"`  
   - `"c:/temp/ventas.csv"`

2. **agrupacion** (list o None) — Opcional  
   Lista de campos por los que agrupar si no se usa pivoteo.  

   Ejemplo: `"['IDcliente', 'producto']"`

3. **acciones** (dict o None) — Opcional  
   Diccionario de agregados si se usa `groupby`.  

   Ejemplo: `"{'importe': 'sum', 'cantidad': 'mean'}"`

4. **calculados** (dict o None) — Opcional  
   Campos derivados a partir de otros.  

   Ejemplo: `"{'total': 'precio * cantidad'}"`

5. **destino** (str o None) — Opcional  
   Ruta a archivo donde guardar resultado. Puede ser `.xlsx`, `.csv`, `.json`.  

   Ejemplo: `"c:/temp/resultado.xlsx"`

6. **pivoteo** (dict o None) — Opcional  
   Diccionario con parámetros para `pivot_table`.  

   Ejemplo:  
   ```json
   {
     "index": ["IDseccion", "descripcion", "nombre"],
     "columns": ["IDsucursal"],
     "values": ["cantidad"],
     "aggfunc": "sum",
     "fill_value": 0
   }

7. **mostrar** (bool: "True" o "False") — Opcional (default: False)
   Muestra el resultado en consola de forma legible (si es True) o como JSON (si es False).

8. **decimales** (int) — Opcional (default: 0)
   Redondeo decimal del resultado.

9. **retornar_base64** (bool: "True" o "False") — Opcional (default: False)
   Si es True y hay destino .xlsx, devuelve el contenido como string en base64.

10. **filtro** (dict o None) — Opcional
    Diccionario con condiciones {campo: [comparación, valor]}
    Comparadores válidos: "==", "!=", ">", "<", ">=", "<=", "in", "not in", "contains", "startswith", "endswith"

    Ejemplo:

    ```json
    {
      "descripcion": ["startswith", "REMERA"],
      "nombre": ["contains", "JUAN"]
    }

11. **orden** (dict o None) — Opcional
    Diccionario de ordenamiento {campo: orden}
    Ordenamiento válido: "asc" o "desc"
    
    Ejemplo:

    ```json
    {
      "descripcion": "asc",
      "precio": "desc"
    }

12. **filtro final** (dict o None) — Opcional
    Diccionario con condiciones {campo: [comparación, valor]}
    Comparadores válidos: "==", "!=", ">", "<", ">=", "<=", "in", "not in", "contains", "startswith", "endswith"

    Este filtro se asigna luego del agrupamiento o pivoteo y filtra sobre el resultado ya generado.

    ⚠️ Nota: Este filtro solo se aplica si se realiza una agrupación o un pivoteo. Si no se agrupa ni pivotea, se ignora automáticamente.

    Ejemplo:

    ```json
    {
      "importe": [">", 15000],
      "IDseccion": ["=", 1]
    }

## 📌 Ejemplo

  ```bash
  python frames.py "SELECT * FROM dfacturas WHERE fecha >= '01-08-2025'" \
                   "None" \
                   "None" \
                   "{'importe': 'precio * cantidad'}" \
                   "c:/temp/archivo.xlsx" \
                   "{'index': ['IDseccion', 'descripcion', 'nombre'], 'columns': ['IDsucursal'], 'values': ['cantidad'], 'aggfunc': 'sum', 'fill_value': 0}" \
                   "True" \
                   "2" \
                   "False" \
                   "{'descripcion': ['startswith','REMERA'], 'nombre': ['startswith', 'LEVIN']}" \
                   "{'precio': 'desc'}"

## 📌 Notas

"None" puede pasarse como string para indicar omisión de argumento.

El orden de los argumentos debe respetarse, si no se usa alguno tienr que ir "None".

Todos los dict deben estar en formato válido y entre comillas dobles " para shell y simples ' para claves/valores.

Se puede usar desde SQL Server con xp_cmdshell y retornar resultados como Excel o JSON.
