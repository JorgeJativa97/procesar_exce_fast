from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse
import pandas as pd
from io import BytesIO

app = FastAPI()

@app.post("/procesar-excel/")
async def procesar_excel(archivo: UploadFile = File(...)):
    # Leer el contenido del archivo subido
    contenido = await archivo.read()
    buffer_entrada = BytesIO(contenido)
    
    # Leer ambas hojas del Excel
    hojas = pd.read_excel(
        buffer_entrada,
        sheet_name=["Hoja1", "Hoja2"],
        engine="openpyxl"
    )
    df_recaudos = hojas["Hoja1"]
    df_tarjetas = hojas["Hoja2"]
    
    # Buscar coincidencias
    df_coincidencias = pd.merge(
        df_recaudos[["FECHA", "VALOR"]],
        df_tarjetas[["Valor Total Pago", "Comprobante de pago"]],
        left_on="VALOR",
        right_on="Valor Total Pago",
        how="inner"
    )
    
    # Renombrar columnas
    df_coincidencias = df_coincidencias.rename(columns={
        "VALOR": "Valor Recaudo",
        "Valor Total Pago": "Valor Tarjeta",
        "Comprobante de pago": "Comprobante"
    })
    
    # Crear el Excel de salida en memoria
    buffer_salida = BytesIO()
    with pd.ExcelWriter(buffer_salida, engine="openpyxl") as writer:
        df_recaudos.to_excel(writer, sheet_name="Hoja1", index=False)
        df_tarjetas.to_excel(writer, sheet_name="Hoja2", index=False)
        df_coincidencias.to_excel(writer, sheet_name="Coincidencias", index=False)
    
    # Preparar la respuesta
    buffer_salida.seek(0)
    headers = {
        "Content-Disposition": 'attachment; filename="resultado.xlsx"'
    }
    return StreamingResponse(
        buffer_salida,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers
    )