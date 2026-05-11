# Text to Speech through a Virtual Input Device
A script that uses a virtual audio input device to play text to speech messages generated via the gTTS (Google Text to Speech) library. It plays the generated audio file through both the input and output devices specified simultaneously, so you both hear and speak it. The gTTS library also allows for custom accents and language options, which can be easily configured.

### Requires:
- Python (3.12 or similar)
- Text editor or IDE of choice (for configuration only)

## 1. Installation
- Use `git clone` or download the repository
- In a command line, run `pip install -r "requirements.txt"` to install the required Python libraries

## 2. Setup Virtual Audio Device
- Download and install the [VB-CABLE Virtual Audio Device](https://vb-audio.com/Cable)
- Configure the output device in `config.ini` to match the name of your headphones, speakers, or output device as it appears in audio settings
- Set the input device for your desired application to be VB-CABLE
- Your physical microphone or other input device will no longer, by default, be picked up by that application (see **Step 4**)

## 3. Configure Region and Accent
- Language codes control the language of the text interpretted by gTTS
- Top-level domain (TLD) controls the region, accent, and dialect of speech
- The [gTTS documentation](https://gtts.readthedocs.io/en/latest/module.html#localized-accents) contains some (but not all) possible combinations of language and TLD for certain accents
- Language and TLD will be automatically applied as they appear in config.ini, but can be changed at any time under the **Settings** tab

## 4. Route Microphone Input through Virtual Input (Optional)
By default, a physical microphone or other input device is on its own channel and will not be picked up by VB-CABLE. To use TTS and your microphone simultaneously, you must route the input through VB-CABLE in sound settings.
- In Windows Search or the Run Terminal (`Win + R`), open `mmsys.cpl`
- Under the **Recording** tab, locate your microphone or input device
- Select **Properties**, and then go to the **Listen** tab
- Ensure ``Listen to this device`` is checked, and then under ``Playback through this device``, select ``CABLE Input (VB-Audio Virtual Cable)``

## Additional Notes
- VB-CABLE is not compatible with Linux operating systems. This application was built on Windows 11 and may not run or function as intended on MacOS.
- The field `device_suffix` contains `, Windows WASAPI` by default — a Windows-exclusive audio driver. If you are on Windows, leave this as is. On MacOS, you will need to change or remove this.
- The minmum window size is `380x200` and the default, configurable size is `440x220` with resizing disabled. While it is possible to adjust these settings under the "window" category of `config.ini` (minimum is not configurable to preserve usability), it is not reccomended as all content was designed to fit within the preset values.
- Under the **Settings** tab, you can adjust the gain (volume) of TTS messages by ±10 decibels (limits are not configurable). Be wary that anything in excess of ~5 dB will be extremely loud because dB is on a logarithmic scale.
