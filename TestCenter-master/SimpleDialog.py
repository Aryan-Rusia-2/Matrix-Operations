######################################################################
#   File: SimpleDialog.py
#
#   Description:
#       Contains classes used for creating popup windows (quick
#       difference, error messages, help menu, etc)
#
#   Included classes:
#       - Dialog(tk.Toplevel)
#       - TextDialog(Dialog) - used primarily for quick difference
#       - ErrorDialog(Dialog) - used for viewing runtime error messages
#       - HelpMenu(tk.Toplevel) - custom designed, used for help menu
#
######################################################################

import tkinter as tk
from tkinter import ttk
import os
import sys

#@todo: Make the text selectable
#@todo: On a Mac, map Command+W to close

class Dialog(tk.Toplevel):
    """ Creates a basic text box with a single OK button.
        Requires a parent widget and a title.
        This class is not designed to be used on its own,
        but always as a template parent class.
    """
    def __init__(self, parent, title = ''):
        tk.Toplevel.__init__(self, parent, height=5)
        self.transient(parent) # in front of parent, minimized together with it
        self.title(title)
        self.parent = parent
        # frm fils the whole window --- therefore the dialog becomes themed, too
        frm = self.frm = tk.Frame(self)
        frm.pack(fill=tk.BOTH, expand=tk.YES)

        self.buttonbox()

    def body(self, master):
        # create dialog body.  return widget that should have
        # initial focus.  this method should be overridden
        pass

    def buttonbox(self):
        # add standard button box. override if you don't want the
        # standard buttons
        box = ttk.Frame(self.frm)
        b = ttk.Button(box, text="OK", command=self.ok, default=tk.ACTIVE)
        b.pack(padx=5, pady=5)
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)
        box.pack(side=tk.BOTTOM)
    
    ############################
    # Standard button semantics:
    ############################
    def ok(self, event=None):
        if not self.validate():
            self.initial_focus.focus_set() # put focus back
            return
        self.withdraw()
        self.update_idletasks()
        self.apply()
        self.cancel()

    def cancel(self, event=None):
        # put focus back to the parent window
        self.parent.focus_set()
        self.destroy()  # destroy the widget


    ############################
    # Command hooks:
    ############################
    def validate(self):
        return True # override

    def apply(self):
        pass # override
    
class TextDialog(Dialog):
    """ Inherits from the dialog class and is designed
    to display a simple, non-editable static text message.

    This class is used for Quick Difference display and
    is called from testcenter_gui.pyw.
    """
    def __init__(self, parent, title ='', text=''):
        self.text_msg = text
        Dialog.__init__(self, parent, title)

        body = ttk.Frame(self.frm,relief="sunken")
        self.initial_focus = self.body(body)
        body.pack(padx=5, pady=5, fill=tk.BOTH, expand=tk.YES)
        self.grab_set()
        if not self.initial_focus:
            self.initial_focus = self
        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.geometry("400x300+%d+%d" % (self.parent.winfo_rootx()+50,
                                  self.parent.winfo_rooty()+50))
        self.initial_focus.focus_set()
        self.wait_window(self)
        
    def body(self,master):
        self.text = tk.Text(master,wrap="word", background="white", 
                        borderwidth=0, highlightthickness=0)
        self.vsb = ttk.Scrollbar(master,orient="vertical",
                                command=self.text.yview)
        self.text.configure(yscrollcommand=self.vsb.set)
        self.text.insert(tk.END, self.text_msg)
        self.text.config(state=tk.DISABLED)
        self.vsb.pack(in_=master,side=tk.RIGHT,fill="y")
        self.text.pack(in_=master,side=tk.LEFT,fill=tk.BOTH,expand=tk.YES)

class ErrorDialog(Dialog):
    """ Inherits from the dialog class and is designed
    to display an error message in a more visually pleasing
    way than the basic TextDialog.

    The main differences are a predetermined window size (around
    the same width as a standard terminal window) and changes
    to colours and fonts.
    """
    def __init__(self, parent, title ='', text=''):
        self.text_msg = text
        Dialog.__init__(self, parent, title)

        body = tk.Frame(self.frm,relief="sunken")
        self.initial_focus = self.body(body)
        body.pack(padx=3, pady=3, fill=tk.BOTH, expand=tk.YES)
        self.grab_set()
        if not self.initial_focus:
            self.initial_focus = self
        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.geometry("%dx%d+%d+%d" % (750, 200, self.parent.winfo_rootx()+50,
                                  self.parent.winfo_rooty()+50))
        self.initial_focus.focus_set()
        self.wait_window(self)
        
    def body(self,master):
        self.text = tk.Text(master,wrap="word", background="#200020", fg="white",
                        borderwidth=0, highlightthickness=0, spacing1=2, spacing2=2, spacing3=2)
        self.vsb = tk.Scrollbar(master,orient="vertical",
                                command=self.text.yview, bg="#200020")
        self.text.configure(yscrollcommand=self.vsb.set)
        self.text.configure(font=("Calibri", 10))
        self.text.insert(tk.END, self.text_msg)
        self.text.config(state=tk.DISABLED)
        self.vsb.pack(in_=master,side=tk.RIGHT,fill="y")
        self.text.pack(in_=master,side=tk.LEFT,fill=tk.BOTH,expand=tk.YES)

class HelpMenu(tk.Toplevel):
    """ The help menu class. Contains a button and corresponding
    function for each page of the menu.

    The names and text of each window are read in from files in the
    "help_files" folder. 

    These files must be named 
        - home.txt
        - running_instructions.txt
        - options.txt
        - test_center_debug.txt
        - debugging_tips.txt

    The first line of each file should contain only the text of 
    the button name. The remainder of the file will be displayed 
    on-screen when the button is pressed.

    """
    def __init__(self, parent, title = ''):
        tk.Toplevel.__init__(self, parent)
       
        self.transient(parent) # in front of parent, minimized together with it
        self.title(title)
        self.parent = parent

        # frm fils the whole window --- therefore the dialog becomes themed, too
        frm = self.frm = ttk.Frame(self)
        frm.pack(fill=tk.BOTH, expand=tk.YES)

        self.box = ttk.Frame(self.frm)

        # Create the path to the help menu in the test center directory
        self.help_files_path = os.path.dirname(sys.argv[0]) + "/help_files/"
        # print("Finding help files in: {}".format(self.help_files_path))

        # Below is a list of variables that will store 
        #   a) the body text (suffix "_msg")
        #   b) the button text (suffix "_button").
        #   c) the file name where the body and button text are read
        #   The variables in a) and b) will be overwritten upon reading from 
        #   the appropriate file.
        #   All variables are listed in the same order as their corresponding 
        #   buttons are shown on the help menu.

        # HOME BUTTON
        self.home_msg = None
        self.home_button = None
        self.home_file = "home.txt"
        self.homeButton()

        # RUNNING INSTRUCTIONS BUTTON
        self.run_msg = None
        self.run_button = None
        self.run_file = "running_instructions.txt"
        self.runButton()

        # OPTIONS AND CONFIGURATION BUTTON
        self.options_msg = None
        self.options_button = None
        self.options_file = "options.txt"
        self.optionsButton()

        # TEST CENTER DEBUG (tcd) BUTTON
        self.tcd_msg = None
        self.tcd_button = None
        self.tcd_file = "test_center_debug.txt"
        self.tcdButton()

        # DEBUGGING TIPS BUTTON
        self.debug_msg = None
        self.debug_button = None
        self.debug_file = "debugging_tips.txt"
        self.debugButton()

        # create the button menu
        self.box.pack(side=tk.TOP)
        self.master = ttk.Frame(frm, relief="ridge")
        self.body(self.master)
        self.master.pack(padx=5, pady=5, fill=tk.BOTH, expand=tk.YES)

        # grab current allows switching back to the main window while leaving 
        # this help menu open
        self.grab_current()
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.geometry("+%d+%d" % (self.parent.winfo_rootx()+50,
                                  self.parent.winfo_rooty()+50))
        self.wait_window(self)


    def body(self,master):
        self.text = tk.Text(self.master, wrap="word", background="white", 
                        borderwidth=0, highlightthickness=0)
        self.vsb = ttk.Scrollbar(self.master,orient="vertical",
                                command=self.text.yview)
        self.text.configure(yscrollcommand=self.vsb.set)
        for i in self.home_msg:
            self.text.insert(tk.END, i)
        self.text.config(state=tk.DISABLED)
        self.vsb.pack(in_=self.master,side=tk.RIGHT,fill="y")
        self.text.pack(in_=self.master,side=tk.LEFT,fill=tk.BOTH,expand=tk.YES)

    def homeButton(self):
        f = open(self.help_files_path + "home.txt", "r")
        self.home_button = f.readline().strip()
        self.home_msg = f.readlines()
        f.close()

        b = ttk.Button(self.box, text=self.home_button, command=self.home, default=tk.ACTIVE)
        b.pack(padx=5, pady=5, side=tk.LEFT)

    def home(self):
        self.text.config(state=tk.NORMAL)
        self.text.delete(1.0, tk.END)
        for i in self.home_msg:
            self.text.insert(tk.END, i)
        self.text.config(state=tk.DISABLED)
        
    def runButton(self):
        f = open(self.help_files_path + self.run_file, "r")
        self.run_button = f.readline().strip()
        self.run_msg = f.readlines()
        f.close()
        b = ttk.Button(self.box, text=self.run_button, command=self.howToRun, default=tk.ACTIVE)
        b.pack(padx=5, pady=5, side=tk.LEFT)

    def howToRun(self):
        self.text.config(state=tk.NORMAL)
        self.text.delete(1.0, tk.END)
        for i in self.run_msg:
            self.text.insert(tk.END, i)
        self.text.config(state=tk.DISABLED)

    def debugButton(self):
        # Read the information for the debugging page from the file debugging_tips.txt
        f = open(self.help_files_path + self.debug_file, "r")
        self.debug_button = f.readline().strip()
        self.debug_msg = f.readlines()
        f.close()

        # prep the button
        b = ttk.Button(self.box, text=self.debug_button, command=self.debug, default=tk.ACTIVE)
        b.pack(padx=5, pady=5, side=tk.LEFT)

    def debug(self):
        self.text.config(state=tk.NORMAL)
        self.text.delete(1.0, tk.END)

        for i in self.debug_msg:
            self.text.insert(tk.END, i)

        self.text.config(state=tk.DISABLED)

    def optionsButton(self):
        f = open(self.help_files_path + self.options_file, "r")
        self.options_button = f.readline().strip()
        self.options_msg = f.readlines()
        f.close()
        b = ttk.Button(self.box, text=self.options_button, command=self.options, default=tk.ACTIVE)
        b.pack(padx=5, pady=5, side=tk.LEFT)

    def options(self):
        self.text.config(state=tk.NORMAL)
        self.text.delete(1.0, tk.END)

        for i in self.options_msg:
            self.text.insert(tk.END, i)

        self.text.config(state=tk.DISABLED)

    def tcdButton(self):
        f = open(self.help_files_path + self.tcd_file, "r")
        self.tcd_button = f.readline().strip()
        self.tcd_msg = f.readlines()
        f.close()
        b = ttk.Button(self.box, text=self.tcd_button, command=self.test_center_debug, default=tk.ACTIVE)
        b.pack(padx=5, pady=5, side=tk.LEFT)

    def test_center_debug(self):
        self.text.config(state=tk.NORMAL)
        self.text.delete(1.0, tk.END)
        for i in self.tcd_msg:
            self.text.insert(tk.END, i)
        self.text.config(state=tk.DISABLED)

    def cancel(self, event=None):
        # put focus back to the parent window
        self.parent.focus_set()
        self.destroy()
