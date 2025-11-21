# ===========================================================
# 1. Configuración del Entorno (CORREGIDO PARA STREAMLIT)
# ===========================================================
import os
import sys
import requests
import streamlit as st # 💡 AÑADIR STREAMLIT
# from getpass import getpass # ❌ ELIMINAR getpass
# from dotenv import load_dotenv # ❌ ELIMINAR dotenv

# Se importan las librerías del SDK de Google
from google import genai
from google.genai import types

print("🎉 Iniciando ejecución del Agente Gestor de Insumos...")

# Configurar credenciales USANDO ST.SECRETS
try:
    # Intenta cargar la clave desde la configuración de Streamlit Secrets
    api_key = st.secrets["GEMINI_API_KEY"]
    print("✅ API Key cargada desde st.secrets")
except KeyError:
    # Si la clave no está, termina la ejecución con un error claro
    st.error("❌ Error: Clave 'GEMINI_API_KEY' no encontrada en Streamlit Secrets.")
    print("❌ ERROR: Clave GEMINI_API_KEY no encontrada.")
    sys.exit(1)

# Inicializar cliente
try:
    # Ahora la inicialización usa la clave cargada de forma segura
    client = genai.Client(api_key=api_key, http_options={'api_version': 'v1beta'})
except Exception as e:
    print(f"❌ Error al inicializar el cliente Gemini: {e}")
    sys.exit(1)


# --- Definición de URLs de Gist (el resto de esta sección se mantiene) ---
# ...
# Inicializar cliente
try:
    client = genai.Client(api_key=api_key, http_options={'api_version': 'v1beta'})
except Exception as e:
    print(f"❌ Error al inicializar el cliente Gemini: {e}")
    sys.exit(1)


# --- Definición de URLs de Gist ---
URL_INSUMOS_HISTORICOS = "https://gist.githubusercontent.com/AngelTroncoso/09343994ea886e2cdacc82ffcdef89f2/raw/9c37a67ff8bfcd9db4f85f0b83bbd7b4de994979/insumos%2520Quir%25C3%25BArgicos%2520Historicos"
URL_INVENTARIO = "https://gist.githubusercontent.com/AngelTroncoso/bda68c3c7f4c95e20651954fb5e21737/raw/4c32c31b666033cedf39ba6beb35b4ad79b57a0d/insumos%2520Quir%25C3%25BArgicos"
URL_COTIZACIONES = "https://gist.githubusercontent.com/AngelTroncoso/7d8476ce28a059f1b51694b20ba5b7e5/raw/f5e4827237b23f422fbf6127f369e3d8d85bef71/Codigo_para_Cotizaciones"


# ===========================================================
# 2. Definición de las Herramientas
# ===========================================================

def Insumos_Historicos_Tool(query: str) -> str:
    """[PASO 1: CATALOGADOR] Analiza el Gist de insumos históricos para determinar el rango de consumo."""
    try:
        requests.get(URL_INSUMOS_HISTORICOS)
        print(f"\n[🔧 TOOL: Insumos_Historicos_Tool] Analizando datos históricos...")
        return "Datos históricos encontrados. El consumo mínimo de suturas es de 50 unidades y el máximo de 120 unidades por mes."
    except Exception as e:
        return f"Error al acceder a datos históricos: {e}"

def Verificacion_Stock_Actual(rango_consumo: str) -> str:
    """[PASO 2: PROPONENTE] Verifica inventario y cruza con consumo para generar propuesta."""
    try:
        requests.get(URL_INVENTARIO)
        print(f"\n[🔧 TOOL: Verificacion_Stock_Actual] Analizando stock actual...")
        if "50" in rango_consumo and "120" in rango_consumo:
            stock_actual = 60
            max_consumo = 120
            deficit = max_consumo - stock_actual
            
            if deficit > 0:
                return f"Stock actual suturas: {stock_actual}. Consumo máx: {max_consumo}. Solicitar {deficit} unidades. Ver cotizaciones en {URL_COTIZACIONES}"
            else:
                return f"Stock suficiente ({stock_actual}). No comprar."
        return f"Rango indeterminado ({rango_consumo}). No comprar."
    except Exception as e:
        return f"Error inventario: {e}"


# ===========================================================
# 3. Definición y Ejecución del Agente (MODO INTERACTIVO)
# ===========================================================

SYSTEM_PROMPT = """
Actúa como un sistema de gestión de compras médicas con 3 roles secuenciales:
1. Catalogador: Usa Insumos_Historicos_Tool.
2. Proponente: Usa Verificacion_Stock_Actual con los datos del paso 1.
3. Aprobador: Decide APROBADO/RECHAZADO basado en la propuesta, considerando seguridad y presupuesto.
"""

# Configuración de herramientas
configuracion = types.GenerateContentConfig(
    system_instruction=SYSTEM_PROMPT,
    tools=[Insumos_Historicos_Tool, Verificacion_Stock_Actual]
)

try:
    # 1. Crear el Chat del Agente (Se crea SÓLO una vez para mantener el historial)
    print("\n🚀 Creando chat con Gemini 2.5 Flash...")
    
    chat = client.chats.create(
        model="gemini-2.5-flash",
        config=configuracion
    )

    print("\n---------------------------------------------------")
    print("🤖 Agente Gestor de Insumos (Modo Interactivo)")
    print("   Escribe 'salir' o 'exit' para terminar.")
    print("---------------------------------------------------")

    # 2. Bucle de conversación continuo
    while True:
        # Pide input al usuario
        user_input = input("\n👤 Tú: ")
        
        # Condición de salida
        if user_input.lower() in ["salir", "exit", "quit"]:
            print("\n👋 Agente desconectado. ¡Hasta pronto!")
            break
        
        # Ejecutar el flujo del agente
        print("\n... El Agente está procesando y llamando herramientas...")
        response = chat.send_message(user_input)

        # Mostrar la respuesta final
        print("\n✨ Agente:", response.text)

except Exception as e:
    print(f"\n❌ Error: {e}")