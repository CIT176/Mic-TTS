import tkinter as tk
import sounddevice as sd
import numpy as np
from gtts import gTTS
from pydub import AudioSegment
import tempfile
import configparser
import os

config = configparser.ConfigParser()
config.read('config.ini')

lang = config["TTS"]["language"]
tld = config["TTS"]["top_level_domain"]

target_sr = config["audio"]["target_samplerate"]
target_device = config["audio"]["input_device"]
speaker_device = config["audio"]["output_device"]

sd.default.dtype = 'float32'
sd.default.latency = 'high'

def speak(text):
    """Converts text to speech and plays it through the specified audio device"""
    try:
        tts = gTTS(text=text, lang=lang, tld=tld)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
            tts.save(fp.name)

        base_audio = AudioSegment.from_mp3(fp.name)
        
        # Get device info independently
        target_info = sd.query_devices(target_device)
        speaker_info = sd.query_devices(speaker_device)

        target_sr = int(target_info["default_samplerate"])
        speaker_sr = int(speaker_info["default_samplerate"])

        # Resample independently
        audio_target = base_audio.set_frame_rate(target_sr)
        audio_speaker = base_audio.set_frame_rate(speaker_sr)

        samples_target = np.array(audio_target.get_array_of_samples()).astype(np.float32)
        samples_target /= np.iinfo(audio_target.array_type).max  # Normalize to [-1.0, 1.0]

        samples_speaker = np.array(audio_speaker.get_array_of_samples()).astype(np.float32)
        samples_speaker /= np.iinfo(audio_speaker.array_type).max  # Normalize to [-1.0, 1.0]

        def make_callback(samples, pos_name):
            pos = 0
            def callback(outdata, frames, *_):
                nonlocal pos
                chunk = samples[pos:pos + frames]
                if len(chunk) < frames:
                    assert outdata.shape[1] >= 1, "Output stream must have at least one channel"
                    assert outdata.shape[0] >= len(chunk), "Output buffer too small for chunk"
                    outdata[:len(chunk), 0] = chunk
                    outdata[len(chunk):, 0] = 0
                    raise sd.CallbackStop()
                else:
                    assert outdata.shape[1] >= 1, "Output stream must have at least one channel"
                    outdata[:, 0] = chunk
                    pos += frames
            return callback

        # Open both streams simultaneously
        with sd.OutputStream(
            device=target_device,
            samplerate=target_sr,
            channels=1,
            dtype='float32',
            callback=make_callback(samples_target, "target")
        ), sd.OutputStream(
            device=speaker_device,
            samplerate=speaker_sr,
            channels=1,
            dtype='float32',
            callback=make_callback(samples_speaker, "speaker")
        ):
            sd.sleep(int(len(samples_target) / target_sr * 1000) + 200)

    except Exception as e:
        print(f"An error occured: {e}")
        raise e

    finally:
        if os.path.exists(fp.name):
            os.remove(fp.name)

def submit():
    message = text_widget.get("1.0", tk.END).strip()
    if message:
        speak(message)
        text_widget.delete("1.0", tk.END)

root = tk.Tk()
root.title("Text to Speech")
root.geometry(f"{config["window"]["window_width"]}x{config["window"]["window_height"]}")
root.resizable(False, False)
root.attributes("-topmost", (config["window"]["always_on_top"].strip().lower() == "true"))

main_label = tk.Label(root, text="Enter TTS Message:")
main_label.pack(pady=10)

text_widget = tk.Text(root, height=5, width=35)
text_widget.pack(padx=10, pady=10)
text_widget.focus_set()

submit_btn = tk.Button(root, text="Speak Message", command=submit, padx=40, pady=20)
submit_btn.pack()

root.mainloop()