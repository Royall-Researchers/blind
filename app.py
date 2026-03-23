import os
import base64
import json
import urllib.request
import urllib.error

try:
    import pyaudio
    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False
    print("[Flask] Warning: pyaudio not found. Server-side playback disabled.")

try:
    from flask import Flask, jsonify, request
    from flask_cors import CORS
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False
    print("[Flask] Error: flask or flask-cors not found.")

# --- CONFIGURATION ---
NODE_SERVICE_URL = "http://localhost:3000/gemini-audio"
FLASK_PORT = 5000

if HAS_FLASK:
    app = Flask(__name__)
    CORS(app)

    # Audio Playback Config (Matches Gemini output)
    if HAS_PYAUDIO:
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000 # Standard for Gemini native audio output

    def get_current_detections():
        """
        PLACEHOLDER: Replace with your actual YOLO26 detection logic.
        This should return a list of labels currently detected in the frame.
        """
        # Example mock detections
        return ["person", "chair", "laptop"]

    def play_audio_from_base64(audio_b64):
        """Decodes base64 audio and plays it using PyAudio."""
        if not HAS_PYAUDIO:
            print("[Flask] PyAudio not available. Skipping server-side playback.")
            return

        if not audio_b64:
            print("[Flask] No audio data to play.")
            return

        try:
            audio_data = base64.b64decode(audio_b64)
            print(f"[Flask] Playing {len(audio_data)} bytes of audio...")
            
            p = pyaudio.PyAudio()
            stream = p.open(format=FORMAT,
                            channels=CHANNELS,
                            rate=RATE,
                            output=True)
            
            stream.write(audio_data)
            stream.stop_stream()
            stream.close()
            p.terminate()
            print("[Flask] Playback finished.")
        except Exception as e:
            print(f"[Flask] Playback Error: {e}")

    def get_current_frame_base64():
        """
        PLACEHOLDER: Replace with logic to capture the current frame from your camera
        and return it as a base64 encoded string.
        """
        return None # Return base64 string if image-to-voice is needed

    @app.route('/voice-describe', methods=['GET', 'POST'])
    def voice_describe():
        """
        MAIN PIPELINE:
        1. Get YOLO detections
        2. Capture current frame (optional)
        3. Get user query (if any)
        4. Call Node.js Gemini service
        5. Play received audio
        """
        print("[Flask] Voice request received.")
        
        # Get query from request (if POST)
        query = None
        if request.method == 'POST':
            query = request.json.get('query')

        # 1. Get detections
        detections = get_current_detections()
        
        # 2. Get image (optional)
        image_b64 = get_current_frame_base64()

        # 3. Call Node service
        try:
            payload = {
                "detections": detections,
                "query": query
            }
            if image_b64:
                payload["image"] = image_b64
                
            print(f"[Flask] Requesting Gemini Audio for: {query or 'Scene Description'}")
            
            # Use urllib.request instead of requests
            req = urllib.request.Request(
                NODE_SERVICE_URL,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            try:
                with urllib.request.urlopen(req, timeout=30) as response:
                    data = json.loads(response.read().decode('utf-8'))
            except urllib.error.URLError as e:
                print(f"[Flask] Node Service Error: {e}")
                return jsonify({"status": "failure", "error": f"Node service unreachable: {e}"}), 502
            
            text_desc = data.get("text", "")
            audio_b64 = data.get("audio_base64", "")
            
            # 4. Play audio (Server-side playback)
            if audio_b64:
                if HAS_PYAUDIO:
                    play_audio_from_base64(audio_b64)
                
                return jsonify({
                    "status": "success",
                    "description": text_desc,
                    "audio_base64": audio_b64 # Also return to frontend just in case
                })
            else:
                return jsonify({"status": "error", "message": "No audio returned"}), 500

        except Exception as e:
            print(f"[Flask] Error: {e}")
            return jsonify({"status": "failure", "error": str(e)}), 500

    # Keep existing YOLO endpoints if any
    @app.route('/video_feed')
    def video_feed():
        return "YOLO26 Stream Active"

    if __name__ == "__main__":
        print(f"--- VisionPro Hybrid Backend ---")
        print(f"Flask running on port {FLASK_PORT}")
        print(f"Node Service expected at {NODE_SERVICE_URL}")
        app.run(host="0.0.0.0", port=FLASK_PORT, threaded=True)
else:
    if __name__ == "__main__":
        print("[Flask] CRITICAL: Flask or Flask-CORS not found. Backend cannot start.")
        # Keep the process alive so concurrently doesn't keep restarting it too fast
        import time
        while True:
            time.sleep(60)
