# To run:
```
python -m app_qt.main
```

## Speech-to-text setup

The Swedish reading plugin uses QtMultimedia for microphone recording and Vosk
for local speech recognition.

Install the Python package:

```
python3 -m pip install vosk
```

On Debian/Ubuntu, install the native Qt audio dependencies:

```
sudo apt install libpulse0 libpipewire-0.3-0
```

Download the Swedish Vosk model under the repository root.

Preferred mirror:

```
mkdir -p models
cd models
wget -O vosk-model-small-sv-rhasspy-0.15.zip https://huggingface.co/mychen76/vosk-models/resolve/c9782a244440e607b7e0119dbdd2c766905e12cf/sv/vosk-model-small-sv-rhasspy-0.15.zip
unzip vosk-model-small-sv-rhasspy-0.15.zip
cd ..
```

Official Vosk model URL, if its TLS certificate is valid:

```
wget https://alphacephei.com/vosk/models/vosk-model-small-sv-rhasspy-0.15.zip
```

The app looks for:

```
models/vosk-model-small-sv-rhasspy-0.15
```

Alternatively, point to the model explicitly:

```
export VOSK_MODEL_PATH=/path/to/vosk-model-small-sv-rhasspy-0.15
python3 -m app_qt.main
```
