# A Meshtastic Door Bot

A bot for Meshtastic activities. Responds to keyword commands sent in DMs. Built in the spirit of [doors in bulletin board systems](https://en.wikipedia.org/wiki/Door_\(bulletin_board_system\)).

Current activities include: ping, node info, fortunes, RSS headlines, weather, sun/moon position, and ChatGPT.

Users can DM the bot anything to get started.
- `help` lists loaded commands.
- `help <command>` provides detail about a command.


## Installation

This should work on any computer compatible with the [Meshtastic Python](https://github.com/meshtastic/python) library. Presently USB-connected nodes are supported.


```bash
# Debian/Ubuntu
sudo apt install python3-virtualenv python3-pip

virtualenv mesh_env

source mesh_env/bin/activate

# (clone this repository and change into the directory)

pip install -r requirements.txt
```

### Running

Copy `example.ini` and list any commands you would like to have loaded.

```bash
cp example.ini my_door_config.ini

# set this environment variable if you are using ChatGPT
export OPENAI_API_KEY=...

# run it
python mtdoor.py my_door_config.ini
```


### Command Handlers

A modular command handling system makes it easy to write new commands, perform longer-running tasks in a background thread, access information about your users, and persist data. Lifecycle events for each command include: load, invoke, and shutdown.

Commands should check requirements to operate (e.g. files, Internet, API key) in their `.load()` method and raise `CommandLoadError` to be ignored.


## Mesh logging

Enabling `door.commands.mesh_logger` will create an SQLite database with a log of common packets. Use this feature for good, not evil.

Datasette is a handy tool for navigating SQLite databases. Install with:

```bash
pip install datasette

# nice-to-have plugins
datasette install datasette-vega datasette-cluster-map datasette-saved-queries

# run
datasette <path to plugin data>
```