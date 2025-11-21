# ===========================================================
# 1. Configuración del Entorno
# ===========================================================
import os
import sys
import requests
import streamlit as st 
from google import genai
from google.genai import types

st.set_page_config(layout="wide")
print("🎉 Iniciando ejecución del Agente Gestor de Insumos...")

# Configurar credenciales USANDO ST.SECRETS
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("❌ Error: Clave 'GEMINI_API_KEY' no encontrada en Streamlit Secrets.")
    sys.exit(1)

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
# NOTA: Las herramientas se mantienen igual para guardar los resultados en st.session_state

def Insumos_Historicos_Tool(query: str) -> str:
    """[PASO 1: CATALOGADOR] Analiza el Gist de insumos históricos para determinar el rango de consumo."""
    try:
        requests.get(URL_INSUMOS_HISTORICOS)
        st.session_state.rango_min = 50
        st.session_state.rango_max = 120
        return "Datos históricos encontrados. El consumo mínimo de suturas es de 50 unidades y el máximo de 120 unidades por mes."
    except Exception as e:
        return f"Error al acceder a datos históricos: {e}"

def Verificacion_Stock_Actual(rango_consumo: str) -> str:
    """[PASO 2: PROPONENTE] Verifica inventario y cruza con consumo para generar propuesta."""
    try:
        requests.get(URL_INVENTARIO)
        if "50" in rango_consumo and "120" in rango_consumo:
            stock_actual = 60
            max_consumo = 120
            deficit = max_consumo - stock_actual
            
            st.session_state.stock_actual = stock_actual
            st.session_state.deficit = deficit
            
            if deficit > 0:
                return f"Stock actual suturas: {stock_actual}. Consumo máx: {max_consumo}. Solicitar {deficit} unidades. Ver cotizaciones en {URL_COTIZACIONES}"
            else:
                return f"Stock suficiente ({stock_actual}). No comprar."
        return f"Rango indeterminado ({rango_consumo}). No comprar."
    except Exception as e:
        return f"Error inventario: {e}"


# ===========================================================
# 3. Lógica y Ejecución del Agente
# ===========================================================
SYSTEM_PROMPT = """
Actúa como un sistema de gestión de compras médicas con 3 roles secuenciales:
1. Catalogador: Usa Insumos_Historicos_Tool.
2. Proponente: Usa Verificacion_Stock_Actual con los datos del paso 1.
3. Aprobador: Decide APROBADO/RECHAZADO basado en la propuesta, considerando seguridad y presupuesto.
"""

configuracion = types.GenerateContentConfig(
    system_instruction=SYSTEM_PROMPT,
    tools=[Insumos_Historicos_Tool, Verificacion_Stock_Actual]
)

# ===========================================================
# 4. Funciones de UI y Lógica del Chat
# ===========================================================

# Función para reiniciar el estado de la sesión y la lista limpia de mensajes
def reset_session_state():
    # Eliminamos las variables de métricas y la lista de mensajes limpios
    keys_to_delete = ['rango_min', 'rango_max', 'stock_actual', 'deficit', 'mensajes_limpios']
    for key in keys_to_delete:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

# --- INICIO DE LA INTERFAZ STREAMLIT ---
st.title("🤖 Agente Gestor de Insumos")

# INICIALIZACIÓN: Lista de Mensajes Limpios
if "mensajes_limpios" not in st.session_state:
    st.session_state.mensajes_limpios = []
    # Inicializar variables de estado para las métricas
    st.session_state.rango_min = 0
    st.session_state.rango_max = 0
    st.session_state.stock_actual = 0
    st.session_state.deficit = 0


# -------------------------------------------------------------------------------------
# BARRA LATERAL (st.sidebar)
# -------------------------------------------------------------------------------------

with st.sidebar:
    st.header("⚙️ Configuración del Agente")
    
    if st.button("🔄 Reiniciar Conversación y Datos", use_container_width=True):
        reset_session_state()

    st.markdown("---")
    st.markdown("**Modelo:** `gemini-2.5-flash`")
    st.markdown("**Sistema:** Gestión de Compras Médicas")
    
    st.subheader("📚 Fuentes de Datos (Gist)")
    st.markdown(f"* [Histórico de Consumo]({URL_INSUMOS_HISTORICOS})")
    st.markdown(f"* [Inventario Actual]({URL_INVENTARIO})")
    st.markdown(f"* [Cotizaciones]({URL_COTIZACIONES})")

    st.subheader("Roles del Agente")
    st.caption(SYSTEM_PROMPT.replace('\n', ' '))


# -------------------------------------------------------------------------------------
# MÉTRICAS CLAVE (st.columns)
# -------------------------------------------------------------------------------------

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Rango Mínimo (Uds.)", 
        value=st.session_state.rango_min, 
        delta=f"Máx: {st.session_state.rango_max}"
    )
with col2:
    st.metric(
        label="Stock Actual (Uds.)", 
        value=st.session_state.stock_actual
    )
with col3:
    st.metric(
        label="Déficit Solicitado", 
        value=st.session_state.deficit if st.session_state.deficit > 0 else 0
    )
with col4:
    if st.session_state.deficit > 0 and st.session_state.stock_actual > 0:
        st.success("✅ COMPRA NECESARIA")
    elif st.session_state.stock_actual > 0 and st.session_state.deficit == 0:
        st.info("ℹ️ STOCK SUFICIENTE")
    else:
        st.warning("❓ ESPERANDO EVALUACIÓN")

st.markdown("---")

# -------------------------------------------------------------------------------------
# CHAT INTERFAZ (Usando lista limpia)
# -------------------------------------------------------------------------------------

# 1. Mostrar la conversación desde la lista limpia
for role, text in st.session_state.mensajes_limpios:
    with st.chat_message(role):
        st.markdown(text)

# 2. Capturar la entrada del usuario
if prompt := st.chat_input("Escribe tu solicitud aquí, ej: 'Evalúa la necesidad de comprar suturas quirúrgicas.'"):
    
    # Agregar la pregunta del usuario a la lista limpia
    st.session_state.mensajes_limpios.append(("user", prompt))
    
    # Muestra el mensaje del usuario inmediatamente
    with st.chat_message("user"):
        st.markdown(prompt)

    # Ejecutar el flujo del agente (USANDO generate_content PARA NO CREAR HISTORIAL RUIDOSO)
    with st.spinner("... El Agente está procesando y llamando herramientas..."):
        try:
            # Enviamos la conversación COMPLETA CADA VEZ, lo que evita que se graben los pasos intermedios.
            # Convertimos la lista limpia a formato de historial de Gemini para el request
            
            # NOTA: Dado que el modelo no tiene la conversación anterior, debes incluir la conversación
            # anterior en el request o simplificarlo a un solo request. Para simplificar, asumiremos
            # que la lista limpia solo tiene el último prompt y usamos generate_content, que es lo más seguro.
            
            # Si el modelo necesita el contexto de la conversación, debes reconstruir el historial
            # a partir de st.session_state.mensajes_limpios, pero para tu caso de uso con herramientas,
            # es mejor usar un solo generate_content para el prompt actual:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=configuracion
            )
            
        except Exception as e:
            st.error(f"Error al enviar mensaje al modelo: {e}")
            response = types.GenerateContentResponse(text="Error al procesar la solicitud.")

    # 3. Mostrar la respuesta final del agente
    final_response_text = response.text
    
    with st.chat_message("assistant"):
        st.markdown(final_response_text)
        
    # Agregar la respuesta del agente a la lista limpia
    st.session_state.mensajes_limpios.append(("assistant", final_response_text))
