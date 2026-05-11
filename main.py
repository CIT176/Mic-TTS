import customtkinter
import sounddevice as sd
import numpy as np
from gtts import gTTS
from pydub import AudioSegment
import tempfile
import configparser
import os
import sys

class TTSGeneration():
    def __init__(self):
        self.app_path = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(self.app_path, "config.ini")
        self.config = configparser.ConfigParser()
        self.config.read(self.config_path)

        self.target_sr = self.config["audio"]["target_samplerate"]
        self.target_device = self.config["audio"]["input_device"] + ", Windows WASAPI"
        self.speaker_device = self.config["audio"]["output_device"] + ", Windows WASAPI"

        sd.default.dtype = "float32"
        sd.default.latency = "high"

    def speak(self, text, lang, tld, gain: float = 0):
        """Converts text to speech and plays it through the specified audio device"""
        try:
            tts = gTTS(text=text, lang=lang, tld=tld)
        except ValueError as e:
            raise ValueError(
                f"Invalid gTTS parameters: lang={lang!r}, tld={tld!r}. "
                f"Check available options from the gTTS documentation. Original error: {e}"
            ) from e

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            tts.save(f.name)

        base_audio = AudioSegment.from_mp3(f.name)

        gain = max(-10, min(10, gain))
        base_audio = base_audio.apply_gain(gain)
        
        # Get device info independently
        target_info = sd.query_devices(self.target_device)
        speaker_info = sd.query_devices(self.speaker_device)

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
            device=self.target_device,
            samplerate=target_sr,
            channels=1,
            dtype="float32",
            callback=make_callback(samples_target, "target")
        ), sd.OutputStream(
            device=self.speaker_device,
            samplerate=speaker_sr,
            channels=1,
            dtype="float32",
            callback=make_callback(samples_speaker, "speaker")
        ):
            sd.sleep(int(len(samples_target) / target_sr * 1000) + 200)

        if os.path.exists(f.name):
            os.remove(f.name)

class TTS(customtkinter.CTkTabview):
    def __init__(self, master, tts_engine, config, **kwargs):
        super().__init__(master, **kwargs)
        self.tts_engine = tts_engine

        self.add("TTS")
        self.add("Settings")

        # ------------------------------------
        # TTS Tab
        # ------------------------------------
        # Text input field 
        # ------------------
        self.textbox = customtkinter.CTkTextbox(
            master=self.tab("TTS"),
            font=("Arial", 14)
        )
        self.textbox.grid(row=0, column=0, padx=20, pady=(10, 0), sticky="nsew")
        self.textbox.configure(wrap="word")
        self.textbox.bind("<Return>", self.message_submit)

        # Submission button
        # ------------------
        self.button = customtkinter.CTkButton(
            master=self.tab("TTS"),
            height=40,
            width=150,
            text="Speak Message",
            font=("Arial", 14),
            command=self.message_submit
        )
        self.button.grid(row=1, column=0, pady=(10, 5))

        # ------------------------------------
        # Settings Tab
        # ------------------------------------
        # Volume adjustment
        # ------------------
        self.gain = 0.0

        self.volume_label = customtkinter.CTkLabel(
            master=self.tab("Settings"),
            text="Volume [±10 dB]",
            font=("Arial", 16)
        )
        self.volume_label.grid(row=0, column=0, padx=20, pady=(10, 5), sticky="nw")

        self.volume = customtkinter.CTkSlider(
            master=self.tab("Settings"),
            height=20,
            width=250,
            from_=-10,
            to=10,
            command=self.change_volume
        )
        self.volume.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="nw")
        
        self.gain_value_label = customtkinter.CTkLabel(
            master=self.tab("Settings"),
            text=f"+0 dB",
            font=("Arial", 20)
        )
        self.gain_value_label.grid(row=1, column=1, padx=20, pady=(0, 15), sticky="ne")

        # Language and TLD selection
        # ------------------
        self.lang = config["TTS"]["default_language"]
        self.tld = config["TTS"]["default_top_level_domain"]

        available_languages = [lang.strip().strip('"') for lang in config["TTS"]["languages"].split(",")]
        available_tlds = [tld.strip().strip('"') for tld in config["TTS"]["tlds"].split(",")]

        # Reorder to put defaults first as they appear in the config
        languages = [self.lang] + [lang for lang in available_languages if lang != self.lang]
        tlds = [self.tld] + [tld for tld in available_tlds if tld != self.tld]

        self.lang_label = customtkinter.CTkLabel(
            master=self.tab("Settings"),
            text="Language / Region",
            font=("Arial", 16)
        )
        self.lang_label.grid(row=3, column=0, padx=20, pady=0, sticky="nw")

        self.lang_menu = customtkinter.CTkOptionMenu(
            master=self.tab("Settings"),
            values=languages,
            command=self.change_lang
        )
        self.lang_menu.grid(row=3, column=1, padx=20, pady=0, sticky="ne")

        self.volume_label = customtkinter.CTkLabel(
            master=self.tab("Settings"),
            text="Top-Level Domain",
            font=("Arial", 16)
        )
        self.volume_label.grid(row=4, column=0, padx=20, pady=10, sticky="nw")

        self.tld_menu = customtkinter.CTkOptionMenu(
            master=self.tab("Settings"),
            values=tlds,
            command=self.change_tld
        )
        self.tld_menu.grid(row=4, column=1, padx=20, pady=10, sticky="ne")

    def message_submit(self, event = None):
        message = self.textbox.get("0.0", "end").strip()
        
        if not message:
            return "break"

        self.tts_engine.speak(message, lang=self.lang, tld=self.tld, gain=self.gain)
        self.textbox.delete("0.0", "end")
        return "break"

    def change_volume(self, value):
        self.gain = round(float(value), 1)
        color = "red" if self.gain >= 7.0 else "yellow" if self.gain >= 4.0 else "white"
        self.gain_value_label.configure(text=f"{"+" if self.gain >= 0 else ""}{self.gain} dB", text_color=color)
        
    def change_lang(self, choice):
        self.lang = choice

    def change_tld(self, choice):
        self.tld = choice

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Text to Speech")
        self.iconbitmap("mic.ico")
        
        self.app_path = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(self.app_path, "config.ini")
        self.config = configparser.ConfigParser()
        self.config.read(self.config_path)

        # Window appearance and behaviour
        height = int(self.config["window"]["window_height"])
        width = int(self.config["window"]["window_width"])
        self.geometry(f"{width}x{height}")
        self.minsize(380, 200)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        is_resizeable = self.config["window"]["is_resizeable"].strip().lower() == "true"
        self.resizable(is_resizeable, is_resizeable)

        is_always_on_top = self.config["window"]["always_on_top"].strip().lower() == "true"
        self.attributes("-topmost", is_always_on_top)

        self.tts_engine = TTSGeneration()

        # Tab view grid configuration
        self.tab_view = TTS(master=self, tts_engine=self.tts_engine, config=self.config)
        self.tab_view.grid(row=0, column=0, padx=0, pady=0, stick="nsew")

        self.tab_view.tab("TTS").grid_rowconfigure(0, weight=1)
        self.tab_view.tab("TTS").grid_columnconfigure(0, weight=1)

        self.tab_view.tab("Settings").grid_columnconfigure(0, weight=1)

if __name__ == "__main__":
    app = App()
    app.mainloop()