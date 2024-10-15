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
- `fortune` is installed
- Internet connectivity for the [NWS/NOAA forecast API](https://www.weather.gov/documentation/services-web-api)
- `OPENAI_API_KEY` environment variable for ChatGPT

