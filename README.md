## mtdoor - Meshtastic Door

Quick hack of a bot for Meshtastic. Responds to keyword commands sent in DMs.

In the spirit of [doors on bulletin board systems](https://en.wikipedia.org/wiki/Door_\(bulletin_board_system\)).

Current features:
- ping
- fortunes
- weather forecast
- personalized node position log (not persistent)
- sun and moon positions
- gateway to ChatGPT
- very little error checking or concurrency testing

Assumes:
- `fortune` is installed (`sudo apt install fortune-mod fortunes`)
- Internet for the [NWS/NOAA forecast API](https://www.weather.gov/documentation/services-web-api)
- Internet the first time you use the sun and moon functions
- Internet and `OPENAI_API_KEY` environment variable set for ChatGPT

### Installation

This should work on any machine that can run the [Meshtastic Python](https://github.com/meshtastic/python) library.

```bash
sudo apt install fortune-mod fortunes python3-virtualenv python3-pip

virtualenv mesh_env

source mesh_env/bin/activate

# (clone this repository and change into the directory)

pip install -r requirements.txt
```

### Running

```bash
export OPENAI_API_KEY=...

python mtdoor.py
```

