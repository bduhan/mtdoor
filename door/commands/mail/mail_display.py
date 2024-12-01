from .mail_help import HelpManager

class DisplayManager:
    def __init__(self):
        # Dictionary to store display states for each node
        self.states = {}
        self.max_length = 200
        self.helpmgr = HelpManager()

    def set(self, node, text=None, page=None, prompt=None, help_cmd=None):
        if node not in self.states: self.clear(node)
        if prompt:
            self.states[node]["prompt"] = prompt
            if not text and self.states[node].get("raw", None):
                text = self.states[node]["raw"]
        if text:
            delimiter, items = self.split_string(text)
            pages = self.make_pages(node, [], delimiter, items)
            self.states[node]["pages"] = pages
            self.states[node]["current_page"] = 0
            self.states[node]["raw"] = text
        if page:
            self.states[node]["current_page"] = page
        if help_cmd:
            self.states[node]["help"] = help_cmd

    def clear(self, node):
        """
        Initialize the display state for a node.
        """
        if node not in self.states:
            self.states[node] = {
                "pages": [],
                "current_page": 0,
                "prompt": "",
                "raw": None,
                "help": "pager",
            }

    def split_string(self, text):
        """
        Split a string based on available delimiters (newlines, spaces, or characters).
        """
        if "\n" in text:
            return "\n", text.split("\n")
        elif " " in text:
            return " ", text.split()
        else:
            return "", list(text)

    def display_pages(self, node, inp, text=None, prompt=None):
        """
        Display text on multiple pages and alow navigation beween pages
        """
        if inp.get_raw().lower() == "p":
            self.previous_page(node)
        if inp.get_raw().lower() == "n":
            self.next_page(node)
        if inp.get_raw().lower() == "help":
            help_cmd = self.states[node]["help"]
            self.set(node, text=self.helpmgr.get([help_cmd]))

        if text or prompt:
            # Re-build pages if new content is provided
            self.set(node, text=text, prompt=prompt)
        page = self.states[node]["current_page"]
        return self.states[node]["pages"][page]

    def active(self, node):
        if not self.states.get(node, None):
            return False
        return len(self.states[node]["pages"]) > 1

    def make_pages(self, node, pages, delimiter, chunks):
        """
        Split a long text into pages that fit within the max_length limit.
        """
        if not self.states.get(node, None):
            self.clear(node)
        if len(pages) == 0:
            pages.append("")
        page = len(pages) - 1

        add_delimiter = False
        for chunk in chunks:
            nxt = ""
            if page == 0:
                prev = ""
            else:
                prev = "(p)rev, "
            footer = f"\n{prev}{nxt}(q)uit, {self.states[node]["prompt"]}"
            l = len(footer)
            if len(pages[page]) + len(chunk) + len(delimiter) + l > self.max_length:
                # This chunk is going to run onto a new page
                nxt = "(n)ext, "
                footer = f"\n{prev}{nxt}(q)uit, {self.states[node]["prompt"]}"
                l = len(footer)
            max_length = self.max_length - l
            if len(pages[page]) + len(chunk) + len(delimiter) > max_length:
                # Adding this chunk to the page will exceed max length
                if max_length - len(pages[page]) > max_length / 2:
                    # Not adding anything will leave the page less
                    # than half full. Break up the chunk and add as
                    # much as possible to this page.
                    delimiter, items = self.split_string(text)
                    pages = self.make_pages(node, [], delimiter, items)
                else:
                    # The page is already mostly full. Add the footer
                    # and put this chunk on the next page.
                    pages[page] += footer
                    page += 1
                    pages.append("")
                    pages[page] = f"{chunk}"
            else:
                # Add the line to the current page
                if add_delimiter:
                    pages[page] += f"{delimiter}"
                pages[page] += f"{chunk}"
            add_delimiter = True
        if page == 0:
            pages[page] += self.states[node]["prompt"]
        else:
            pages[page] += footer
        return pages

    def next_page(self, node):
        """
        Advance to the next page for a node, if possible.
        """
        if node not in self.states: return
        if self.states[node]["current_page"] + 1 < len(self.states[node]["pages"]):
            self.states[node]["current_page"] += 1

    def previous_page(self, node):
        """
        Go back to the previous page for a node, if possible.
        """
        if node not in self.states: return
        if self.states[node]["current_page"] > 0:
            self.states[node]["current_page"] -= 1
