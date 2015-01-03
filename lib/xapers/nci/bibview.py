import urwid

from ..cli import initdb

############################################################

class Bibview(urwid.WidgetWrap):

    def __init__(self, ui, query):
        self.ui = ui

        self.ui.set_header("Bibtex: " + query)

        string = ''

        with initdb() as db:
            if db.count(query) == 0:
                self.ui.set_status('No documents found.')
            else:
                for doc in db.search(query, limit=20):
                    bibtex = doc.get_bibtex()
                    if bibtex:
                        string = string + bibtex + '\n'

        self.box = urwid.Filler(urwid.Text(string))
        w = self.box

        self.__super.__init__(w)

    def keypress(self, size, key):
        self.ui.keypress(key)
