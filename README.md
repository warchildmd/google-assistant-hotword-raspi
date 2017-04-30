# google-assistant-hotword-raspi
Simple Google Assistant with hotword activation from Snowboy setup for my Pi Zero W.

# Setup
#### 1. [Google Assistant Python setup on Raspbery Pi](https://developers.google.com/assistant/sdk/prototype/getting-started-pi-python/)
  * [Configure a Developer Project and Account Settings](https://developers.google.com/assistant/sdk/prototype/getting-started-pi-python/config-dev-project-and-account)
  * [Configure and Test the Audio](https://developers.google.com/assistant/sdk/prototype/getting-started-pi-python/configure-audio)
  * Setup virtual environment
    ```
    -   (Recommended) For Python 3:
    
        sudo apt-get update
        sudo apt-get install python3-dev python3-venv
        python3 -m venv env
        env/bin/python -m pip install pip setuptools --upgrade
        source env/bin/activate
    
    -   For Python 2:
    
        sudo apt-get update
        sudo apt-get install python-dev python-virtualenv
        virtualenv env --no-site-packages
        env/bin/pip install pip setuptools --upgrade
        source env/bin/activate
    ```
  * Install dependencies
    `sudo apt-get install portaudio19-dev libffi-dev libssl-dev`
  * Install Google Assistant SDK + Samples
    ` python -m pip install google-assistant-sdk[samples]`
  * Get credentials
    `python -m googlesamples.assistant.auth_helpers --client-secrets /home/pi/client_secret_XXXX.json`
  * Test using the sample
    `python -m googlesamples.assistant`
    Issue commands after pressing `enter` and if you did all the steps above Google Assistant should respond.

***PS** On Raspberry Pi Zero W this setup takes about 30-40 minutes.*

#### 2. [Snowboy Python setup on Pi](http://docs.kitt.ai/snowboy/) - [Github](https://github.com/Kitt-AI/snowboy)
  * Download Snowboy [compiled library for all versions of Pi + demo](https://s3-us-west-2.amazonaws.com/snowboy/snowboy-releases/rpi-arm-raspbian-8.0-1.2.0.tar.bz2)
  *  Install dependencies
    `sudo apt-get install python-pyaudio python3-pyaudio sox`
  * Install BLAS
    `sudo apt-get install libatlas-base-dev`
  * Install PyAudio
    `pip install pyaudio`
    You should be able to recored audio using:
    `rec temp.wav`

#### Train your own hotwords or download existing ones from https://snowboy.kitt.ai/

#### 2. Run `gassistant.py` and you should have a working Google Assistant with hotword activation
    `python gassistant.py models/ok_google.pmdl`
