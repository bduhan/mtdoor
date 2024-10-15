## mtdoor - Meshtastic Door

Quick hack of a bot for Meshtastic. Keyword based commands, it responds only to DMs.

Current features:
- ping
- fortunes
- weather forecast
- personalized node position log (not persistent)
- sun and moon positions
- gateway to ChatGPT
- very little error checking or concurrency testing

Assumes `fortune` is installed and Internet connectivity for NOAA forecast and ChatGPT (set `OPENAI_API_KEY` environment variable).

