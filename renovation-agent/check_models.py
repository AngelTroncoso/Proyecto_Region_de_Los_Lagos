import os
from dotenv import load_dotenv
from google import genai

# Cargar entorno
load_dotenv()
api_key = os.environ.get("GOOGLE_API_KEY")

print(f"🔑 Probando con API Key que termina en: ...{api_key[-4:] if api_key else 'NONE'}")

try:
    client = genai.Client(api_key=api_key)
    print("\n📡 Consultando modelos disponibles en tu cuenta...")
    
    # Listar modelos
    for m in client.models.list():
        if "generateContent" in m.supported_actions:
            print(f"✅ Disponible: {m.name}")
            
except Exception as e:
    print(f"\n❌ Error al conectar: {e}")