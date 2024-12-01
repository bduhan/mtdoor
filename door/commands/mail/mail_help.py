from loguru import logger as log

class HelpManager:
    def __init__(self):
        # Define the help text dictionary as a class attribute
        self.help_text = {
            "mail": """
read <#>
delete <# | all>
reply <#> <msg>
send <node_id> <subj> -- <msg>
admin <alias | peer | mailbox>
""",
            "mail:read": """
read = Read mail messages
read # = Read message number #
""",
            "mail:reply": """
reply = Reply to message (interactive)
reply # = Reply to message number #
reply # <message> = Quick reply
""",
            "mail:delete": """
delete = Delete mail messages
delete # = Delete message number #
delete all = Delete all messages
""",
            "mail:send": """
send = Send mail (interactive)
send !1234 Hi There -- message text = Quick send
""",
            "mail:admin": """
alias <add | delete> <node_id>
peer <add | delete> <node_id>
mailbox <select | delete>
""",
            "mail:admin:alias": """
add <node_id> = Add node to access mailbox
delete <node_id> = Remove node from mailbox
""",
            "mail:admin:peer": """
add <node_id> = Sync mail with another node
delete <node_id> = Remove sync peer
""",
            "mail:admin:mailbox": """
list 
select <node_id>
delete <node_id>
""",
            "mail:admin:mailbox:select": """
select = Admin access to mailbox (interactive)
select <node_id> = Admin access to mailbox
""",
            "mail:admin:mailbox:delete": """
delete = Delete mailbox (interactive)
delete <node_id> = Delete mailbox
""",
            "pager": """
p = Previous page
n = Next page
q = Quit viewing pages
or send text to search/filter output
""",
            "nodelist": """
p = Previous page
n = Next page
- = Short format
+ = Long format
i = Toggle nodeID
l = Toggle longName
s = Toggle shortName
q = Quit viewing pages
or send text to search/filter output
""",
        }

    def get(self, commands=None, args=None) -> str:
        log.debug(f"commands: {commands}")
        log.debug(f"args: {args}")
        # Ensure arguments are defaulted to empty lists if not provided
        if commands is None:
            commands = []
        if args is None:
            args = []

        if "help" in commands:
            commands.remove("help")
        stack = list(commands)
        n = len(stack)
        log.debug(f"stack: {stack}")
        header = f"Command: {':'.join(stack)}\n"
        log.debug(f"header: {header}")
        for item in args:
            stack.append(item.lower())
        if "help" in stack:
            stack.remove("help")
        response = None
        while len(stack) > 0:
            index = ":".join(map(str, stack))
            response = self.help_text.get(index, None)
            if response:
                response = response.strip()
                if len(stack) > n:
                    header += f"Help: {':'.join(stack[n:])}\n"
                break
            else:
                stack.pop()
        if not response:
            response = self.help_text["mail"].strip()
        footer = ""
        level = list(commands)
        if len(level) > 1:
            level.pop()
            footer += f"\n'back' to return to {':'.join(level)}"
        footer += "\n'exit' to quit mail"
        footer += "\nor send command"
        return header + response + footer
