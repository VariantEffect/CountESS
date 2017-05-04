#  Copyright 2016 Alan F Rubin, Daniel C Esposito.
#
#  This file is part of Enrich2.
#
#  Enrich2 is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Enrich2 is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Enrich2.  If not, see <http://www.gnu.org/licenses/>.


from tkinter import *
from tkinter.messagebox import askyesno
from tkinter.filedialog import asksaveasfile
import logging


LOG_FORMAT = "%(asctime)-15s [%(oname)s] %(message)s"


class ScrolledText(Frame):

    def __init__(self, parent=None):
        Frame.__init__(self, parent)
        self.parent = parent
        self.text = self._make_scrolling_text()
        self.pack(expand=YES, fill=BOTH)

        self.menu = Menu(self, tearoff=0)
        self.menu.add_command(label="Copy", command=self.copy_text)
        self.parent.bind_class("Text", "<Button-2>", self.show_menu)

    def _make_scrolling_text(self):
        sbar = Scrollbar(self)
        text = Text(self, relief=SUNKEN)
        # Cross-link and move scrollbar to follow text
        sbar.config(command=text.yview)
        text.config(yscrollcommand=sbar.set)
        sbar.pack(side=RIGHT, fill=Y)
        text.pack(side=LEFT, expand=YES, fill=BOTH)
        return text

    def show_menu(self, event):
        self.menu.post(event.x_root, event.y_root)
        return self

    def copy_text(self):
        try:
            selection = self.text.selection_get()
            self.parent.clipboard_clear()
            self.parent.clipboard_append(str(selection))
        except TclError:
            return
        return self

    def set_text(self, text=''):
        self.set_text_widget_state("normal")
        self.text.insert(END, text)
        self.text.see(END)
        self.set_text_widget_state("disabled")
        return self

    def get_text(self):
        return self.text.get('1.0', END + '-1c')

    def save_text(self):
        fp = asksaveasfile()
        if fp is not None:
            fp.write(self.get_text())
            fp.close()
        return self

    def set_text_widget_state(self, state):
        self.text.config(state=state)
        return self


class WindowLoggingHandler(logging.Handler):
    def __init__(self, window=None, level=logging.NOTSET):
        logging.Handler.__init__(self, level)
        self.window = window
        if window is None:
            self.window = Tk()

        self.scrolling_text = ScrolledText(parent=self.window)
        self.scrolling_text.set_text_widget_state("disabled")
        self.scrolling_text.pack(side=TOP, expand=YES, fill=BOTH)

        save_btn = Button(
            master=self.window,
            text='Save As...',
            command=self.scrolling_text.save_text
        )
        save_btn.pack(side=RIGHT, anchor=S, padx=2, pady=2)

        close_btn = Button(
            master=self.window,
            text='Close',
            command=self.close
        )
        close_btn.pack(side=RIGHT, anchor=S, padx=2, pady=2)
        self.window.protocol("WM_DELETE_WINDOW", self.close)

    def close(self):
        if askyesno('Verify', 'Do you really want to quit?'):
            self.close()
            logger = logging.getLogger()
            logger.removeHandler(self)
            self.window.destroy()

    def show(self):
        self.window.update()
        self.window.deiconify()

    def hide(self):
        self.window.withdraw()

    def emit(self, record):
        text = self.format(record) + '\n'
        self.scrolling_text.set_text(text)

    def mainloop(self):
        self.window.mainloop()

    @classmethod
    def basic_handler(cls, toplevel=None,
                      fmt=LOG_FORMAT, level=logging.NOTSET):
        handler = cls(window=toplevel, level=level)
        formatter = logging.Formatter(fmt=fmt)
        handler.setFormatter(formatter)
        return handler