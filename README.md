# Text to Speech through a Virtual Input Device
A script that uses a virtual audio input device to play text to speech messages generated via the gTTS (Google Text to Speech) library. It plays the generated audio file through both the input and output devices specified simultaneously, so you both hear and speak it. The gTTS library also allows for custom accents and language options, which can be easily configured.

### Requires:
- Python (3.12 or similar)
- Code editor or IDE of choice

## 1. Installation
- Use `git clone` or download the repository
- In a command line, run `pip install -r "requirements.txt"` to install the required Python libraries

## 2. Setup Virtual Audio Device
- Download and install the [VB-CABLE Virtual Audio Device](https://vb-audio.com/Cable)
- Configure the output device in `config.ini` to match the name of your headphones, speakers, or output device as it appears in audio settings
- You can adjust the size and properties of the TTS typing window under the "window" category of `config.ini`

## 3. Configure Region and Accent
- Language codes control the language of the text interpretted by gTTS
- Top-level domain (TLD) controls the region, accent, and dialect of speech
- The [gTTS documentation](https://gtts.readthedocs.io/en/latest/module.html#localized-accents) contains some (but not all) possible combinations of language and TLD for certain accents