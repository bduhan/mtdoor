from .mail_utils import (
    is_node_id,
    list_choices,
    make_node_list,
    get_longName,
    get_shortName,
    encode,
    decode,
)
from loguru import logger as log
import sqlite3


def admin(self, node, inp):
    mailbox = self.profile.mailbox(node)
    if inp.get_current() is None:
        return self.helpmgr.get(self.command_stack.get(node), inp.get_list())
    self.command_stack.load(node, inp, ["alias", "peer", "mailbox"])

    ### Manage Aliases ###
    if self.command_stack.get(node, level=2) == "alias":
        self.command_stack.load(node, inp, ["add", "delete"])
        i = inp.get_current()
        aliases = make_alias_list(self.db, mailbox, self.interface.nodes)
        node_list = make_node_list(self.interface.nodes, fmt=self.fmt.get(node))

        ### Add Aliases ###
        if self.command_stack.get(node, level=3) == "add":
            response = ""
            # Check for selected node on stack
            if self.command_stack.get(node, level=4):
                log.debug("Found node to add")
                # The user has chosen a nodeID and we have saved it on the stack and asked
                # for confirmation
                primary = get_primary_alias(self.db, mailbox)
                if primary is None:
                    primary = mailbox
                alias = self.command_stack.get(node, level=4)
                log.debug(f"alias: {alias}")
                log.debug(f"input: {i}")
                if i == "a":  # Approved
                    log.debug(f"Approved")
                    # User has confirmed choice
                    add_alias(self.db, primary, alias)
                    aliases = make_alias_list(self.db, mailbox, self.interface.nodes)
                    node_list = make_node_list(self.interface.nodes, fmt=self.fmt.get(node))
                    response = (
                        f"Added alias {alias} to authorized nodes for this mailbox.\n\n"
                    )
                else:
                    # Negative user confirmation
                    log.debug(f"Denied")
                    response = (
                        f"{alias} NOT added to authorized nodes for this mailbox.\n\n"
                    )
                self.command_stack.pop(node)  # Pop the nodeID off the stack
                self.command_stack.pop(node)  # Pop the 'add' command off the stack
                response += f"Aliases for mailbox {mailbox}:\n"  # Display the alias list so they can see
                response += list_choices(aliases)  # what they have done
                self.output.set(node, prompt="'add', 'delete'", help_cmd="pager")
                return response
            # No selected node on stack yet. See if the user has chosen one to add
            elif (i.isdigit() and 0 <= int(i) < len(node_list)) or is_node_id(i):
                # The user sent a valid numeric choice
                if i.isdigit():
                    log.debug(f"User entered digit: {i}")
                    # User has entered a number from the node list
                    index = int(i) - 1
                    nodes = [item[0] for item in node_list]
                    display = [item[1] for item in node_list]
                    choice = nodes[index]
                    choice_display = display[index]
                # The user sent a valid nodeID
                elif is_node_id(i):
                    log.debug(f"User entered nodeID: {i}")
                    # User has entered a nodeID
                    choice = i
                    choice_display = (
                        f"{i} {get_longName(self.db, i)} ({get_shortname(self.db, i)})"
                    )
                # Reject invalid node choices
                if choice == node or choice in get_aliases(self.db, node):
                    if choice == mailbox:
                        log.debug(f"Invalid choice = mailbox")
                        response = f"You can't add yourself as an alias\n\n"
                    if choice in get_aliases(self.db, mailbox):
                        log.debug(f"Invalid already an alias")
                        response = f"{choice} is already an alias\n\n"
                    # Go back up to the aliases menu
                    self.command_stack.pop(node)
                    response += f"Aliases for mailbox {mailbox}:\n"
                    response += list_choices(aliases)
                    self.output.set(node, prompt="'add', 'delete'", help_cmd="pager")
                    return response
                # Choice is valid. Push it onto the stack and ask for confirmation
                self.command_stack.push(node, choice)  # Push the choice onto the stack
                response = f"Grant node {choice_display} access to your mailbox?\n\n"
                self.output.set(node, prompt="A) Approve\nD) Deny", help_cmd="pager")
                return response
            else:
                # User has not selected a node to add yet
                if i == "q":
                    self.command_stack.pop(node)    # pop 'add' off command stack
                    response = self.helpmgr.get(self.command_stack.get(node), inp.get_list())
                    self.output.clear(node)
                    return response
                if i == "c":
                    i = ""
                prompt = ""
                if i:
                    prompt += "(c)lear search, "
                prompt += "# or !nodeID to add alias"
                self.output.set(node, prompt=prompt, help_cmd="nodelist")
                response = "Nodes:\n"
                response += list_choices(node_list, search=i)
                return response

        ### Delete Aliases ###
        elif self.command_stack.get(node, level=3) == "delete":
            response = ""
            # Check for selected node on stack
            if self.command_stack.get(node, level=4):
                log.debug("Found node to delete")
                # The user has chosen a nodeID and we have saved it on the stack and asked
                # for confirmation
                primary = get_primary_alias(self.db, mailbox)
                if primary is None:
                    primary = mailbox
                alias = self.command_stack.get(node, level=4)
                log.debug(f"alias: {alias}")
                log.debug(f"input: {i}")
                if i == "a":  # Approved
                    log.debug(f"Approved")
                    # User has confirmed choice
                    delete_alias(self.db, primary, alias)
                    aliases = make_alias_list(self.db, mailbox, self.interface.nodes)
                    node_list = make_node_list(self.interface.nodes, fmt=self.fmt.get(node))
                    response = (
                        f"Deleted {alias} from authorized nodes for this mailbox.\n\n"
                    )
                else:
                    # Negative user confirmation
                    log.debug(f"Denied")
                    response = (
                        f"{alias} NOT deleted.\n\n"
                    )
                self.command_stack.pop(node)  # Pop the nodeID off the stack
                self.command_stack.pop(node)  # Pop the 'delete' command off the stack
                response += f"Aliases for mailbox {mailbox}:\n"  # Display the alias list so they can see
                response += list_choices(aliases)  # what they have done
                self.output.set(node, prompt="'add', 'delete'", help_cmd="pager")
                return response
            # No selected node on stack yet. See if the user has chosen one to add
            elif (i.isdigit() and 0 <= int(i) < len(aliases)) or is_node_id(i):
                # The user sent a valid numeric choice
                if i.isdigit():
                    log.debug(f"User entered digit: {i}")
                    # User has entered a number from the alias list
                    index = int(i) - 1
                    nodes = [item[0] for item in aliases]
                    display = [item[1] for item in aliases]
                    choice = nodes[index]
                    choice_display = display[index]
                # The user sent a valid nodeID
                elif is_node_id(i):
                    log.debug(f"User entered nodeID: {i}")
                    # User has entered a nodeID
                    choice = i
                    choice_display = (
                        f"{i} {get_longName(self.db, i)} ({get_shortname(self.db, i)})"
                    )
                # Reject invalid node choices
                if choice == node or choice in get_aliases(self.db, node):
                    if choice == mailbox:
                        log.debug(f"Invalid choice = mailbox")
                        response = f"You can't delete the mailbox nodeID\n\n"
                    if choice not in get_aliases(self.db, mailbox):
                        log.debug(f"Invalid not an alias")
                        response = f"{choice} is not an alias\n\n"
                    # Go back up to the aliases menu
                    self.command_stack.pop(node)
                    response += f"Aliases for mailbox {mailbox}:\n"
                    response += list_choices(aliases)
                    self.output.set(node, prompt="'add', 'delete'", help_cmd="pager")
                    return response
                # Choice is valid. Push it onto the stack and ask for confirmation
                self.command_stack.push(node, choice)  # Push the choice onto the stack
                response = f"Delete node {choice_display} from access to your mailbox?\n\n"
                self.output.set(node, prompt="A) Approve\nD) Deny", help_cmd="pager")
                return response
            else:
                # User has not selected a node to add yet
                if i == "c":
                    i = ""
                prompt = ""
                if i:
                    prompt += "(c)lear search, "
                prompt += "# or !nodeID to delete alias"
                response = "Aliases:\n"
                response += list_choices(node_list, search=i)
                self.output.set(node, prompt=prompt, help_cmd="pager")
                return response
        ### Display Aliases ###
        else:
            response = f"Aliases for mailbox {mailbox}:\n"
            response += list_choices(aliases)
            self.output.set(node, prompt="'add', 'delete'", help_cmd="pager")

    ### Manage Peers ###
    elif self.command_stack.get(node, level=2) == "peer":
        if not self.profile.is_admin():
            return "You do not have permission to administer peers!"
        self.command_stack.load(node, inp, ["add", "delete"])
        if self.command_stack.get(node, level=3) == "add":
            pass
        elif self.command_stack.get(node, level=3) == "delete":
            pass
        else:
            response = self.helpmgr.get(self.command_stack.get(node), inp.get_list())

    ### Manage Mailboxes ###
    elif self.command_stack.get(node, level=2) == "mailbox":
        if not self.profile.is_admin():
            return "You do not have permission to administer mailboxes!"
        self.command_stack.load(node, inp, ["select", "delete"])
        if self.command_stack.get(node, level=3) == "select":
            pass
        elif self.command_stack.get(node, level=3) == "delete":
            pass
        else:
            response = self.helpmgr.get(self.command_stack.get(node), inp.get_list())
    else:
        response = self.helpmgr.get(self.command_stack.get(node), inp.get_list())
    log.debug(f"response: {response}")
    return response


def make_alias_list(db, node, nodes):
    my_list = []
    aliases = get_aliases(db, node)
    if len(aliases) > 1:
        aliases.pop()
    for alias in aliases:
        value = alias
        longName = get_longName(alias, nodes)
        shortName = get_shortName(alias, nodes)
        display = f"{alias} {longName} ({shortName})"
        item = (value, display)
        my_list.append(item)
    return my_list


def get_primary_alias(db, node):
    # Open a database connection
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    try:
        # Query for rows where node_id matches the search node
        cursor.execute(
            """
        SELECT node_id
        FROM aliases
        WHERE node_id = ?
        """,
            (node,),
        )
        result = cursor.fetchone()
        if result:
            return result[0]

        # Query for rows where alias matches the search node
        cursor.execute(
            """
        SELECT node_id
        FROM aliases
        WHERE alias = ?
        """,
            (node,),
        )
        result = cursor.fetchone()
        if result:
            return result[0]

        # Return None if no matches are found
        return None
    finally:
        # Ensure the connection is closed
        conn.close()


def get_aliases(db, node):
    # Get the primary alias
    primary_node_id = get_primary_alias(db, node)

    # If no primary alias is found, return an empty list
    if not primary_node_id:
        return []

    # Open a new database connection
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    try:
        # Query for all rows that match the primary node_id
        cursor.execute(
            """
        SELECT alias
        FROM aliases
        WHERE node_id = ?
        """,
            (primary_node_id,),
        )
        rows = cursor.fetchall()

        # Build the list with the primary node_id as the first item
        aliases = [primary_node_id] + [row[0] for row in rows]
        return aliases
    finally:
        # Ensure the connection is closed
        conn.close()


def add_alias(db, primary_node_id, alias):
    try:
        # Open a database connection
        conn = sqlite3.connect(db)
        cursor = conn.cursor()

        # Insert the new alias into the table
        cursor.execute(
            """
        INSERT INTO aliases (node_id, alias)
        VALUES (?, ?)
        """,
            (primary_node_id, alias),
        )

        # Commit the changes
        conn.commit()
        log.debug(f"Alias '{alias}' added for primary node '{primary_node_id}'.")
    except sqlite3.IntegrityError as e:
        # Handle the case where the row already exists
        log.debug(
            f"Error: Could not add alias '{alias}' for primary node '{primary_node_id}'. {e}"
        )
    except Exception as e:
        # Handle other potential exceptions
        log.debug(f"An unexpected error occurred: {e}")
    finally:
        # Ensure the connection is closed
        conn.close()


def delete_alias(db, primary_node_id, alias=None):
    try:
        # Open a database connection
        conn = sqlite3.connect(db)
        cursor = conn.cursor()

        if alias is None:
            # Delete all aliases for the given primary node_id
            cursor.execute(
                """
            DELETE FROM aliases
            WHERE node_id = ?
            """,
                (primary_node_id,),
            )
            log.debug(
                f"All aliases for primary node '{primary_node_id}' have been deleted."
            )
        else:
            # Delete the specific alias for the primary node_id
            cursor.execute(
                """
            DELETE FROM aliases
            WHERE node_id = ? AND alias = ?
            """,
                (primary_node_id, alias),
            )
            if cursor.rowcount > 0:
                log.debug(
                    f"Alias '{alias}' deleted for primary node '{primary_node_id}'."
                )
            else:
                log.debug(
                    f"No such alias '{alias}' found for primary node '{primary_node_id}'."
                )

        # Commit the changes
        conn.commit()
    except Exception as e:
        # Handle unexpected errors
        log.debug(
            f"An error occurred while deleting alias for primary node '{primary_node_id}': {e}"
        )
    finally:
        # Ensure the connection is closed
        conn.close()
