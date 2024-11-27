# This file adds a command to the mtdoor node-bot.
# The 'zork' command will allow the user to play
# a minimal version of the classic adventure game
# Zork I. Just because.

from . import BaseCommand
from loguru import logger as log
import re


class Zork(BaseCommand):
    command = "zork"
    description = "A Classic text-based adventure game"
    help = "'zork' to play Zork"

    def load(self):
        self.room = {}

    def invoke(self, msg: str, node: str) -> str:

        response = ""
        inp = msg.lower().strip()

        # See if the user wants to exit
        if msg.lower().split()[0] == "exit":
            self.persistent_session(node, False)
            del self.room[node]
            return "Goodbye. Send 'zork' to play again"

        # Set up a persistent session
        self.persistent_session(node, True)

        # Set up new game if none in progress
        if not self.room.get(node, False):
            # Initialize the game
            self.room[node] = 4
            response += "Welcome to Zork\n\n"

        match self.room[node]:
            # House
            case 4:
                if re.fullmatch(
                    r"^(go|walk|run)\s(.*\s)*(sw|southwest)$", inp
                ) or re.fullmatch(r"^(sw|southwest)$", inp):
                    self.room[node] = 8
                elif re.fullmatch(
                    r"^(go|walk|run)\s(.*\s)*(n|north)$", inp
                ) or re.fullmatch(r"^(n|north)$", inp):
                    response += "There is an impenetrable forest to the north.\n\n"
                elif re.fullmatch(
                    r"^(go|walk|run)\s(.*\s)*(s|south)$", inp
                ) or re.fullmatch(r"^(s|south)$", inp):
                    response += "The forest is too thick to go south.\n\n"
                elif re.fullmatch(
                    r"^(go|walk|run)\s(.*\s)*(e|east)$", inp
                ) or re.fullmatch(r"^(e|east)$", inp):
                    response += (
                        "The door is boarded and you cannot remove the boards.\n\n"
                    )
                elif re.fullmatch(
                    r"^(go|walk|run)\s(.*\s)*(w|west)$", inp
                ) or re.fullmatch(r"^(w|west)$", inp):
                    response += "A swamp full of crocodiles blocks the way west.\n\n"
                elif re.fullmatch(r"(take|get|steal)\s(.*\s)*mailbox", inp):
                    response += "It is securely anchored.\n\n"
                elif re.fullmatch(r"(open|look)\s(.*\s)*mailbox", inp):
                    response += "Opening the small mailbox reveals a leaflet.\n\n"
                elif re.fullmatch(
                    r"(open|look|break|smash|go|enter)\s(.*\s)*door", inp
                ):
                    response += "The door cannot be opened.\n\n"
                elif re.fullmatch(
                    r"(remove|look|break|smash|take|get)\s(.*\s)*boards", inp
                ):
                    response += "The boards are securely fastened.\n\n"
                elif re.fullmatch(r"(look|enter|go)\s(.*\s)*house", inp):
                    response += "The house is a beautiful colonial house which is painted white. "
                    response += (
                        "It is clear that the owners must have been extremely wealthy. "
                    )
                    response += "One of the windows seems to be slightly ajar."
                    return response
                elif re.fullmatch(r"(open|enter|go)\s(.*\s)*window", inp):
                    response += "You force the window open and climb in. "
                    self.room[node] = 1
                elif re.fullmatch(
                    r"(read|look|open)\s(.*\s)*(mail|letter|leaflet)", inp
                ):
                    response += "It says, Welcome to the Unofficial Meshtastic Version of Zork. "
                    response += "Your mission is to find a Jade Statue."
                    return response
                elif inp == "help":
                    return help()
                elif inp == "zork":
                    pass
                elif inp == "look":
                    pass
                else:
                    response += "Invalid action\n"

            # HAM Shack
            case 1:
                if re.fullmatch(
                    r"^(go|walk|run)\s(.*\s)*(n|north)$", inp
                ) or re.fullmatch(r"^(n|north)$", inp):
                    response += "A desk full of radio equipment blocks your way.\n\n"
                elif re.fullmatch(
                    r"^(go|walk|run)\s(.*\s)*(s|south)$", inp
                ) or re.fullmatch(r"^(s|south)$", inp):
                    response += "A bookshelf full of radio manuals blocks your way.\n\n"
                elif re.fullmatch(
                    r"^(go|walk|run)\s(.*\s)*(e|east)$", inp
                ) or re.fullmatch(r"^(e|east)$", inp):
                    response += "The door exiting this room is locked.\n\n"
                elif re.fullmatch(
                    r"^(go|walk|run)\s(.*\s)*(w|west)$", inp
                ) or re.fullmatch(r"^(w|west)$", inp):
                    response += "You exit the room through the same window where you came in.\n\n"
                    self.room[node] = 4
                elif re.fullmatch(
                    r"(go|walk|run|exit|climb)\s(.*\s)*window", inp
                ) or re.fullmatch(r"(leave|back|out).*", inp):
                    response += "You exit the room through the same window where you came in.\n\n"
                    self.room[node] = 4
                elif re.fullmatch(
                    r"(turn|power|talk)\s(.*\s)*radios?", inp
                ) or re.fullmatch(r"(turn|power|talk)\s(.*\s)*equipment", inp):
                    response += "You cannot turn on the radios, there is no electricity in the house.\n\n"
                elif re.fullmatch(r"(look)\s(.*\s)*(device|meshtastic).*", inp):
                    response += "The small device is a battery powered meshtastic node. A message on the screen says: "
                    response += "'I hope you are enjoying Zork for Meshtastic!'\n\n"
                    return response
                elif re.fullmatch(r"(look)\s(.*\s)*(radio|radios).*", inp):
                    response += "The radios are of all different kinds with analog and digital displays, dials and "
                    response += "meters. The owner of this house must have been a HAM radio operator.\n\n"
                    return response
                elif re.fullmatch(r"(take|get|steal).*", inp):
                    response += "What are you, some kind of theif?\n\n"
                elif re.fullmatch(r"(.*\s)door", inp):
                    response += "The door leading from the ham shack to the rest of the house is locked. "
                    response += "Despite your repeated valiant attempts to open it, it will not budge.\n\n"
                    return response
                elif inp == "help":
                    return help()
                elif inp == "look":
                    pass
                else:
                    response += "Invalid action\n"

            # Southwest Loop
            case 8:
                if re.fullmatch(
                    r"^(go|walk|run)\s(.*\s)*(ne|northeast)$", inp
                ) or re.fullmatch(r"^(ne|northeast)$", inp):
                    self.room[node] = 4
                elif re.fullmatch(
                    r"^(go|walk|run)\s(.*\s)*(n|north)$", inp
                ) or re.fullmatch(r"^(n|north)$", inp):
                    response += "The forest becomes impenetrable to the north.\n\n"
                elif re.fullmatch(
                    r"^(go|walk|run)\s(.*\s)*(s|south)$", inp
                ) or re.fullmatch(r"^(s|south)$", inp):
                    response += "Storm-tossed trees block your way.\n\n"
                elif re.fullmatch(
                    r"^(go|walk|run)\s(.*\s)*(e|east)$", inp
                ) or re.fullmatch(r"^(e|east)$", inp):
                    self.room[node] = 9
                elif re.fullmatch(
                    r"^(go|walk|run)\s(.*\s)*(w|west)$", inp
                ) or re.fullmatch(r"^(w|west)$", inp):
                    response += "You would need a machete to go further west.\n\n"
                elif inp == "help":
                    return help()
                elif inp == "look":
                    pass
                else:
                    response += "Invalid action\n"

            # East Loop and Grating Input
            case 9:
                if re.fullmatch(
                    r"^(go|walk|run)\s(.*\s)*(n|north)$", inp
                ) or re.fullmatch(r"^(n|north)$", inp):
                    response += "The forest becomes impenetrable to the north.\n\n"
                elif re.fullmatch(
                    r"^(go|walk|run)\s(.*\s)*(s|south)$", inp
                ) or re.fullmatch(r"^(s|south)$", inp):
                    response += "You see a large ogre and turn around.\n\n"
                elif re.fullmatch(
                    r"^(go|walk|run)\s(.*\s)*(e|east)$", inp
                ) or re.fullmatch(r"^(e|east)$", inp):
                    response += "The forest becomes impenetrable to the east.\n\n"
                elif re.fullmatch(
                    r"^(go|walk|run)\s(.*\s)*(w|west|back)$", inp
                ) or re.fullmatch(r"^(w|west|back)$", inp):
                    self.room[node] = 8
                elif re.fullmatch(
                    r"^(go|walk|run)\s(.*\s)*(d|down)$", inp
                ) or re.fullmatch(r"^(d|down)$", inp):
                    self.room[node] = 10
                elif re.fullmatch(
                    r"(go|walk|run|down|enter|descend)\s(.*\s)*grating", inp
                ):
                    self.room[node] = 10
                elif inp == "help":
                    return help()
                elif inp == "look":
                    pass
                else:
                    response += "Invalid action\n"

            # Grating Loop and Cave Input
            case 10:
                if (
                    re.fullmatch(r"^(go|walk|run)\s(.*\s)*(n|north)$", inp)
                    or re.fullmatch(r"^(n|north)$", inp)
                    or re.fullmatch(r"^(go|walk|run)\s(.*\s)*(s|south)$", inp)
                    or re.fullmatch(r"^(s|south)$", inp)
                    or re.fullmatch(r"^(go|walk|run)\s(.*\s)*(e|east)$", inp)
                    or re.fullmatch(r"^(e|east)$", inp)
                    or re.fullmatch(r"^(go|walk|run)\s(.*\s)*(w|west)$", inp)
                    or re.fullmatch(r"^(w|west)$", inp)
                ):
                    response += "There are cave walls on all sides.\n\n"
                elif re.fullmatch(
                    r"^(go|walk|run)\s(.*\s)*(u|up|back)$", inp
                ) or re.fullmatch(r"^(u|up|back)$", inp):
                    self.room[node] = 9
                elif re.fullmatch(
                    r"^(go|walk|run)\s(.*\s)*(d|down)$", inp
                ) or re.fullmatch(r"^(d|down)$", inp):
                    self.room[node] = 11
                elif re.fullmatch(
                    r"(go|walk|run|down|enter|descend)\s(.*\s)*staircase", inp
                ):
                    self.room[node] = 11
                elif re.fullmatch(r"(light|illuminate)\s(.*\s)*room", inp):
                    response += "You would need a torch or lamp to do that.\n\n"
                elif re.fullmatch(r"(take|get|steal)\s(.*\s)*skeleton", inp):
                    response += "Why would you do that? Are you some sort of sicko?\n\n"
                elif re.fullmatch(r"(kill|attack|hit|fight)\s(.*\s)*skeleton", inp):
                    response += "Why? The skeleton is already dead!\n\n"
                elif re.fullmatch(r"(break|smash)\s(.*\s)*skeleton", inp):
                    response += "I have two questions: Why and With What?\n\n"
                elif re.fullmatch(r"(.*\s)+skeleton", inp):
                    response += "Sick person. Have some respect mate.\n\n"
                elif re.fullmatch(
                    r"(go|walk|down|scale|descend)\s(.*\s)*(stair|stairs|staircase)",
                    inp,
                ):
                    self.room[node] = 11
                elif re.fullmatch(r"(.*\s)*suicide", inp):
                    response += "You throw yourself down the staircase as an attempt at suicide. You die.\n"
                    response += "Send 'zork' to play again"
                    self.persistent_session(node, False)
                    del self.room[node]
                    return response
                elif inp == "help":
                    return help()
                elif inp == "look":
                    pass
                else:
                    response += "Invalid action\n"

            # End of game
            case 11:
                if (
                    re.fullmatch(r"^(go|walk|run)\s(.*\s)*(n|north)$", inp)
                    or re.fullmatch(r"^(n|north)$", inp)
                    or re.fullmatch(r"^(go|walk|run)\s(.*\s)*(s|south)$", inp)
                    or re.fullmatch(r"^(s|south)$", inp)
                    or re.fullmatch(r"^(go|walk|run)\s(.*\s)*(e|east)$", inp)
                    or re.fullmatch(r"^(e|east)$", inp)
                    or re.fullmatch(r"^(go|walk|run)\s(.*\s)*(w|west)$", inp)
                    or re.fullmatch(r"^(w|west)$", inp)
                ):
                    response += "There are walls on all sides.\n\n"
                elif re.fullmatch(
                    r"^(go|walk|run)\s(.*\s)*(u|up|back)$", inp
                ) or re.fullmatch(r"^(u|up|back)$", inp):
                    self.room[node] = 10
                elif re.fullmatch(r"(.*\s)+chest", inp):
                    response += "You have found the Jade Statue and have completed your quest!\n"
                    response += "Send 'zork' to play again"
                    self.persistent_session(node, False)
                    del self.room[node]
                    return response
                elif inp == "help":
                    return help()
                elif inp == "look":
                    pass
                else:
                    response += "Invalid action\n"

        if self.room[node] == 1:
            response += "You are in a room full of radio equipment. "
            response += (
                "A small device with an antenna and a //\\ logo is lying on the desk."
            )

        if self.room[node] == 4:
            response += "You are in a field west of a white house with a boarded up front door. "
            response += "A path leads southwest into the forest. "
            response += "There is a Small Mailbox."

        if self.room[node] == 8:
            response += "This is a forest, with trees in all directions. "
            response += "To the east, there appears to be sunlight."

        if self.room[node] == 9:
            response += "You are in a clearing, with a forest surrounding you on all sides. A path leads south. "
            response += "There is an open grating, descending into darkness."

        if self.room[node] == 10:
            response += (
                "You are in a tiny cave with a dark, forbidding staircase leading down."
            )
            response += "There is a skeleton of a human male in one corner."

        if self.room[node] == 11:
            response += "You have entered a mud-floored room. "
            response += (
                "Lying half buried in the mud is an old chest, bulging with jewels."
            )

        response += "\nWhat do you do?"

        return response


def help():
    return (
        "To play, you must describe the player's actions. An action is generally "
        "composed of a verb followed by a direction, a place, an object. Send 'exit' to quit\n\n"
    )
