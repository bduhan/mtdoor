# Mail command

A command handler for mtdoor that allows users to exchange mail maeesages over Meshtastic.

**This command is under development and is not yet ready for testing.**

## Installation

Copy `example.ini` and list any commands you would like to have loaded.

```bash
[door.commands.mail]
enabled = true
admins = !mynodeid, !nodeid02
```

### Using the mail command

The Mail command has several subcommands:

`read`, `send`, reply`,` `delete`, and `admin`

You may send any of these commands and Mail will interactively present you with the commands or options provided to you at that level. You can send `help` at any time to get help for the current subcommand.

Mail commands and parameters may be stacked in a single message, so `mail read 1` will read the 1st message in your mailbox and is equivalent to sending `mail`, then sending `read`, then sending `1` to choose from the list of available messages.

 