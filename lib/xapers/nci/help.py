import urwid

############################################################

class Help(urwid.WidgetWrap):

    def __init__(self, ui, widget):
        self.ui = ui
        self.widget = widget

        wname = self.widget.__class__.__name__

        self.ui.set_header("help: %s" % wname)

        pile = []

        pile.append(urwid.Text('%s commands:' % (wname)))
        pile.append(urwid.Text(''))

        for key, cmd in sorted(widget.keys.iteritems()):
            pile.append(self.row('widget', cmd, key))

        pile.append(urwid.Text(''))
        pile.append(urwid.Text(''))
        pile.append(urwid.Text('Global commands:'))
        pile.append(urwid.Text(''))

        for key, cmd in sorted(self.ui.keys.iteritems()):
            pile.append(self.row('ui', cmd, key))

        w = urwid.Filler(urwid.Pile(pile))
        self.__super.__init__(w)

    def row(self, c, cmd, key):
        hstring = eval('str(self.%s.%s.__doc__)' % (c, cmd))
        return urwid.Columns(
            [
                ('fixed', 8,
                 urwid.Text(key)),
                urwid.Text(hstring),
                 ]
                )

    def keypress(self, size, key):
        self.ui.keypress(key)
