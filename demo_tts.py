from google.cloud import texttospeech
from google.api_core.client_options import ClientOptions

PROJECT_ID = "lively-aloe-411504"
API_ENDPOINT = "texttospeech.googleapis.com"
MODEL = "gemini-2.5-pro-tts"

client = texttospeech.TextToSpeechClient(
    client_options=ClientOptions(api_endpoint=API_ENDPOINT)
)

def synthesize_gemini_kannada():

    text = """
ಪ್ರಿಯ ವಿದ್ಯಾರ್ಥಿಗಳೇ,
ಇಂದು ನಾವು ಹಳೆ ಶಿಲಾಯುಗದ ಪ್ರಮುಖ ಲಕ್ಷಣಗಳನ್ನು ತಿಳಿದುಕೊಳ್ಳೋಣ.

ಈ ಕಾಲದಲ್ಲಿ ಮಾನವರು ಅಲೆಮಾರಿ ಜೀವನ ನಡೆಸುತ್ತಿದ್ದರು.
ಅವರು ಒರಟಾದ ಕಲ್ಲಿನ ಉಪಕರಣಗಳನ್ನು ಬಳಸುತ್ತಿದ್ದರು.

ಇದೇ ಶಿಲಾಯುಗದ ಆರಂಭಿಕ ಹಂತದ ಮೂಲಭೂತ ಸ್ವರೂಪವಾಗಿದೆ.
"""

    response = client.synthesize_speech(
        input=texttospeech.SynthesisInput(
            text=text,
            prompt="""
You are a knowledgeable female Kannada history teacher.
Speak clearly, calmly, and in an instructional tone.
Pause naturally between concepts.
"""
        ),
        voice=texttospeech.VoiceSelectionParams(
            language_code="kn-IN",
            name="Puck",              # Gemini voice
            model_name=MODEL
        ),
        audio_config=texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            speaking_rate=1.0,
            pitch=0
        ),
    )

    with open("gemini_kannada_demo.wav", "wb") as f:
        f.write(response.audio_content)

    print("🎧 gemini_kannada_demo.wav created")

if __name__ == "__main__":
    synthesize_gemini_kannada()