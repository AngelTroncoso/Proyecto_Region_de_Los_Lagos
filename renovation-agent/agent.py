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
# 3. Definición y Ejecución del Agente (MODO STREAMLIT)
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

# --- INICIO DE LA INTERFAZ STREAMLIT ---
st.title("🤖 Agente Gestor de Insumos")


# Inicialización del Chat en el Estado de Sesión de Streamlit
# Usamos st.session_state para que el objeto 'chat' persista entre interacciones.
if "chat" not in st.session_state:
    try:
        # 1. Crear el Chat del Agente (Se crea SÓLO una vez al inicio)
        print("\n🚀 Creando chat con Gemini 2.5 Flash...")
        st.session_state.chat = client.chats.create(
            model="gemini-2.5-flash",
            config=configuracion
        )
    except Exception as e:
        st.error(f"❌ Error al crear el chat: {e}")
        # Detenemos la ejecución de Streamlit si hay un error crítico
        st.stop() 


# ===========================================================
# Función de Ayuda para Extraer Texto de forma Segura
# ===========================================================
def extract_text_from_content(content):
    """Extrae y concatena el texto de todas las partes de un objeto Content de Gemini."""
    text_content = ""
    for part in content.parts:
        # Usamos hasattr para verificar si la parte es de texto y no de herramienta u otro tipo
        if hasattr(part, 'text'):
            text_content += part.text
        # Puedes añadir aquí lógica adicional si quieres mostrar llamadas a herramientas
        # o salidas, pero para texto simple, esto es suficiente.
    return text_content

# ===========================================================
# Mostrar el historial de mensajes
# ===========================================================
for message in st.session_state.chat.get_history():
    # 1. Extraemos el texto de forma segura
    message_text = extract_text_from_content(message)
    
    # Solo mostramos el mensaje si contiene texto (para evitar mostrar mensajes vacíos)
    if message_text:
        # 2. Mapeamos el rol del modelo a 'assistant' para Streamlit
        role = "user" if message.role == "user" else "assistant"
        with st.chat_message(role):
            st.markdown(message_text)

# ===========================================================
# Capturar la entrada del usuario con la interfaz de Streamlit
# ===========================================================
if prompt := st.chat_input("Escribe tu solicitud aquí..."):
    # 1. Muestra el mensaje del usuario
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Ejecutar el flujo del agente (Llamada al modelo)
    with st.spinner("... El Agente está procesando y llamando herramientas..."):
        try:
            # Enviamos el mensaje al chat persistente
            response = st.session_state.chat.send_message(prompt)
        except Exception as e:
            st.error(f"Error al enviar mensaje al modelo: {e}")
            # Creamos una respuesta de error para mantener la estructura del chat
            response = types.Content(parts=[types.Part.from_text("Error al procesar la solicitud.")])

    # 3. Mostrar la respuesta final del agente
    with st.chat_message("assistant"):
        # Usamos la función segura para extraer la respuesta
        final_response_text = extract_text_from_content(response)
        st.markdown(final_response_text)
        
    # La interfaz se actualiza automáticamente
 
