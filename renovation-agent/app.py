import streamlit as st
import os
import requests
from dotenv import load_dotenv

# Importar Google GenAI SDK
from google import genai
from google.genai import types

# --- 1. CONFIGURACIÓN Y DEFINICIÓN DE HERRAMIENTAS ---

# Cargar variables de entorno
load_dotenv()
API_KEY = os.environ.get("GOOGLE_API_KEY")

# URLs de Gist (Copias de agent.py)
URL_INSUMOS_HISTORICOS = "https://gist.githubusercontent.com/AngelTroncoso/09343994ea886e2cdacc82ffcdef89f2/raw/9c37a67ff8bfcd9db4f85f0b83bbd7b4de994979/insumos%2520Quir%25C3%25BArgicos%2520Historicos"
URL_INVENTARIO = "https://gist.githubusercontent.com/AngelTroncoso/bda68c3c7f4c95e20651954fb5e21737/raw/4c32c31b666033cedf39ba6beb35b4ad79b57a0d/insumos%2520Quir%25C3%25BArgicos"
URL_COTIZACIONES = "https://gist.githubusercontent.com/AngelTroncoso/7d8476ce28a059f1b51694b20ba5b7e5/raw/f5e4827237b23f422fbf6127f369e3d8d85bef71/Codigo_para_Cotizaciones"

# Definición de las Herramientas (Copias de agent.py)
# --- Nuevas Herramientas para el Agente Planificador ---

def Identify_Surgery_Type(fonaza_code: str) -> str:
    """Identifica el tipo de cirugia asociado a un codigo FONASA o nombre descriptivo."""
    st.info(f"🔧 TOOL 1: Identificando cirugía para código {fonaza_code}...")
    if "012546" in fonaza_code or "craneo" in fonaza_code.lower():
        return "Cirugía de Cráneo (Neurocirugía)"
    return "Cirugía Genérica (Requerida Definición Manual)"

def Get_Historical_Kit(surgery_type: str) -> str:
    """Devuelve el kit de insumos estandar y sus cantidades minimas/maximas segun el tipo de cirugia."""
    st.info(f"🔧 TOOL 2: Recuperando kit histórico para {surgery_type}...")
    if "Cráneo" in surgery_type:
        return """
        Kit Histórico Propuesto para Cirugía de Cráneo:
        - Suturas de Nylon (unidades): 20
        - Grapas Quirúrgicas (unidades): 10
        - Catéter de Drenaje (unidades): 1
        - Gasa Quirúrgica (paquetes): 8
        """
    return "No se encontró un kit histórico definido. Se requiere definición manual."

def Check_Inventory_And_Order_Status(kit_list: str) -> str:
    """Cruza la lista de insumos FINALIZADA contra el stock actual y genera la lista de articulos a solicitar (Solicitud de Pedido)."""
    st.info("🔧 TOOL 3a: Cruzando lista final con inventario y generando solicitud de pedido...")
    # Simulación de Stock actual (Hardcodeado para el demo): Suturas: 15, Grapas: 5, Catéter: 2, Gasa: 8
    
    # Esta función debería parsear 'kit_list' (la lista final del humano)
    # y compararla con el inventario real.
    
    order_required = """
    Artículos con Déficit (Solicitud de Pedido Generada):
    - Suturas de Nylon: Faltan 5 unidades (20 requeridas - 15 en stock)
    - Grapas Quirúrgicas: Faltan 5 unidades (10 requeridas - 5 en stock)
    """
    inventory_summary = "Catéter de Drenaje y Gasa Quirúrgica tienen stock suficiente."
    return f"Resumen de Inventario: {inventory_summary}. **Solicitud de Pedido:** {order_required}"

def Update_Historical_Data(final_purchase_list: str) -> str:
    """Simula el guardado de la lista final de compra y disponibilidad para actualizar la base de datos histórica (NUEVO REQUISITO)."""
    st.info("🔧 TOOL 3b: Guardando datos de utilización en el registro histórico...")
    if final_purchase_list:
        return f"✅ **Registro Histórico Actualizado:** Los datos de uso y disponibilidad se guardaron con éxito."
    return "❌ Error: No se pudo actualizar la data histórica."

# ¡Importante! Asegúrate de actualizar el CONFIGURACION para incluir las 4 herramientas
# CONFIGURACION = types.GenerateContentConfig(..., tools=[Identify_Surgery_Type, Get_Historical_Kit, Check_Inventory_And_Order_Status, Update_Historical_Data])
# Instrucción del sistema
SYSTEM_PROMPT = """
Eres un Agente Senior de Gestión de Insumos Quirúrgicos. Tu misión es crear un 'Kit Quirúrgico' personalizado basado en el flujo de trabajo de 4 etapas:

1. IDENTIFICACIÓN: Recibe un código FONASA o el nombre de una cirugía (ej: 012546). Llama inmediatamente a la herramienta Identify_Surgery_Type.
2. PROPUESTA INICIAL: Usando el resultado de la identificación, llama a Get_Historical_Kit para obtener un listado base de insumos históricos (Kit Propuesto). Presenta este listado AL USUARIO de manera clara.
3. INTERACCIÓN HUMANA (Human-in-the-Loop): ESPERA la confirmación del usuario, o la lista de insumos FINALIZADA/MODIFICADA por el profesional. NO AVANCES al paso 4 hasta tener una lista confirmada.
4. PROCESAMIENTO FINAL: Una vez confirmada la lista final, debes:
    a) Llamar a Check_Inventory_And_Order_Status con la lista final para cruzarla contra el stock y generar una lista de pedido.
    b) Generar un informe de compra final.
    c) Llamar a Update_Historical_Data con la lista de compra/uso final para actualizar los registros.

Tu salida debe ser siempre clara y profesional.
"""

# Configuración de herramientas
CONFIGURACION = types.GenerateContentConfig(
    system_instruction=SYSTEM_PROMPT, # Usamos el nuevo prompt
    tools=[
        Identify_Surgery_Type,
        Get_Historical_Kit,
        Check_Inventory_And_Order_Status,
        Update_Historical_Data
    ]
)

# --- 2. INICIALIZACIÓN DE STREAMLIT Y CHAT ---

st.set_page_config(page_title="Agente de Gestión de Insumos (Demo Web)", layout="wide")
st.title("🤖 Agente Gestor de Insumos")
st.caption("Implementación de Agente Gemini 2.5 Flash con llamadas a funciones.")
st.write("Inicia la conversación pidiendo una propuesta de compra para materiales de sutura.")

# Inicializar el cliente Gemini y el chat en el estado de sesión
if "client" not in st.session_state or "chat" not in st.session_state:
    try:
        if not API_KEY:
            st.error("❌ API Key no encontrada. Asegúrate de que GOOGLE_API_KEY esté en tu archivo .env.")
            st.stop()
            
        st.session_state.client = genai.Client(api_key=API_KEY, http_options={'api_version': 'v1beta'})
        
        # Crear el chat (La memoria de la conversación)
        st.session_state.chat = st.session_state.client.chats.create(
            model="gemini-2.5-flash", 
            config=CONFIGURACION
        )
        # Inicializar el historial de mensajes de la sesión
        st.session_state.messages = []
        
    except Exception as e:
        st.error(f"❌ Error al inicializar el cliente o el chat: {e}")
        st.stop()


# --- 3. BUCLE DE CHAT DE STREAMLIT ---

# Mostrar el historial de chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Capturar la entrada del usuario
if prompt := st.chat_input("¿Qué insumos deseas analizar?"):
    
    # 1. Mostrar la entrada del usuario
    with st.chat_message("user"):
        st.markdown(prompt)
        
    # 2. Agregar la entrada del usuario al historial
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 3. Llamar al Agente
    with st.chat_message("assistant"):
        with st.spinner("El agente está pensando y llamando herramientas..."):
            try:
                # Enviar mensaje al chat persistente
                response = st.session_state.chat.send_message(prompt)
                
                # Mostrar la respuesta del agente
                st.markdown(response.text)
                
                # 4. Agregar la respuesta del agente al historial
                st.session_state.messages.append({"role": "assistant", "content": response.text})

            except Exception as e:
                st.error(f"❌ Error del Agente: {e}")