#!/usr/bin/env python3

######################################################################
#   File: testcenter_gui.pyw
#
#   Description:
#       This is the main file for the test center application and 
#       contains most of the gui implementation.
#       The Application class is the first one initialized, and it
#       creates instances of the MyStatusBar(), ResultViewer(),
#       and TestSuite() classes.
#
#   Included classes:
#       Application() - The main class of the test center, containing
#                       most of the interface and having several subclasses
#                       as attributes.
#
#       MyStatusBar() - Each instance is a different row on the bottom of 
#                       the application (eg, to show timeout, soln
#                       directory, etc)
#
#       ResultViewer()- Creates and implements the menu that displays
#                       when you right click on a failed test case.
#
######################################################################

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import myplatform
import TestSuite
import configparser
#import TestCase
import subprocess
import os
from SimpleDialog import TextDialog, HelpMenu, ErrorDialog

#@todo: Add diffmerge exec to the config file 
#@todo: Recent file history
#@todo: Configuration: strict mode, generation mode(?), diffmerge_exec
#@todo: Tooltips
#@todo: Nicer status bar
#@todo: Run selected tests (context menu, global menu)
#@todo: Instead of messagebox, use Labels as popups for showing differences
#@todo: Add progress bar to notify user of progress when running tests
#@todo: Add standard menu items (about) 
#@todo: many tabs in Notebook: hide some tabs, scroll them, etc.
#@todo: ordering tabs: alphabetic(?)
#@todo: reordering of tests based on Results

INI_FILE = "testcenter.ini"

def enable_menu_item(menu,entry,enable=True):
    menu.entryconfig(entry,state=(tk.ACTIVE if enable else tk.DISABLED))


class MyStatusBar:
    def __init__(self, master,format_str):
        self.label = ttk.Label(master, text='',  relief=tk.SUNKEN, anchor=tk.W)
        self.label.pack(fill=tk.X,side=tk.BOTTOM)
        self.format_str = format_str
#        self.label.config(bg='lightgrey')

    def set_data(self, *args):
        self.label.config(text=self.format_str % args)
        self.label.update_idletasks()

    def clear(self):
        self.label.config(text="")
        self.label.update_idletasks()
        
class ResultViewer(ttk.Frame):
    def __init__(self,parent,config,script_name,script_tests):

        # creating tags: empty, accept, fail

        ttk.Frame.__init__(self, parent)
        self.parent = parent
        self.config = config
        self.script_tests = script_tests
        self.pack(fill=tk.BOTH, expand=tk.YES)
        treeview = self.treeview = ttk.Treeview(self,columns=('Test','Result'),show="headings")
        treeview.heading('Test', text='Test')
        treeview.heading('Result', text='Result')
        
        vsb = ttk.Scrollbar(orient="vertical", command=treeview.yview)
        treeview.configure(yscrollcommand=vsb.set) #, xscrollcommand=hsb.set)
        treeview.grid(column=0, row=0, sticky='nsew', in_=self)
        vsb.grid(column=1, row=0, sticky='ns', in_=self)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        for k in sorted(list(script_tests.keys())):
            treeview.insert("", tk.END, iid=k, values = (k, 'N/A'), tags = ("empty", ))
            
        if self.is_aqua(): 
            # Mac OS aqua handles right-click in a special fashion 
            treeview.bind('<2>',         self.on_rightclick)
            treeview.bind('<Control-1>', self.on_rightclick)
        else:
            treeview.bind('<3>', self.on_rightclick)

        treeview.tag_configure("empty", foreground="black", background="white")
        treeview.tag_configure("fail", foreground="black", background="#FFAAAA")
        treeview.tag_configure("accept", foreground="black", background="white")

        # treeview.tag_configure("empty", foreground="black", background="white")
        # treeview.tag_configure("fail", foreground="black", background="#FFAAAA")
        # treeview.tag_configure("accept", foreground="black", background="#AAFFAA")
            
        parent.add(self,text=script_name)
            
            
    def is_aqua(self):
        # direct call into Tcl/Tk
        return self.treeview.tk.call('tk', 'windowingsystem')=='aqua'
    
    def on_rightclick(self,event):
        if self.is_aqua() and not event.state & 0x04: # right-click emulation?
#            print("Right click false alarm")
            return
        item = self.treeview.identify('item', event.x, event.y)
#        self.treeview.focus(item)
        self.treeview.selection_set(item)
        test_case = self.script_tests[item]
        
        if not test_case.is_pass():
            self.treeview.after_idle(lambda : self.context_menu(event,item))
        return "break"

    def open_file(self, path, test_case):
        """ Iterates through all the files in the chosen directory
        and opens any that match the test_case name and do not
        contain the word "err" (to avoid opening error files as well).
        """
        tests = os.listdir(path)

        for i in tests:
            if test_case.name in i and "err" not in i:
                # open with default text editor
                if myplatform.is_mac():
                    os.system("open " + path + "/" + i)

                elif myplatform.is_linux():
                    os.system("xdg-open " + path + "/" + i)

                else:
                    #TODO: add windows functionality and check that it works on mac
                    pass

    def input_file(self, test_case):
        """ Open the input file for the given test case."""
        path = os.getcwd() + "/" + test_case.output_path
        path = path[:-7] + "Inputs"
        self.open_file(path, test_case)

    def output_file(self, test_case):
        """ Open the output file for the given test case."""
        path = os.getcwd() + "/" + test_case.output_path
        self.open_file(path, test_case)

    def expected(self, test_case):
        """ Open the expected file for the given test case."""
        path = os.getcwd() + "/" + test_case.exp_path
        self.open_file(path, test_case)

    def open_all(self, test_case):
        """ Allows viewing of all three files, input, output, and expected,
        to find the error more easily. """
        self.input_file(test_case)
        self.output_file(test_case)
        self.expected(test_case)

    def context_menu(self,event,item):
        """ Set up the menu that appears when the user right-clicks on a 
        failed testcase (any test case that did not pass)
        """
        test_case = self.script_tests[item]

        menu = tk.Menu(root, tearoff=0)
        menu_item = 0

        # ERROR MESSAGE --------------------------------------------------------
        # when the error message button is clicked, open an ErrorDialog with the 
        # error message (see SimpleDialog.py)
        menu.add_command(label="Error message", command=
            lambda: ErrorDialog(self.parent, "Error message", test_case.err_msg()))
        enable_menu_item(menu,menu_item,test_case.is_err())
        menu_item +=1
        
        menu.add_separator()
        menu_item +=1
        # -----------------------------------------------------------------------

        # VIEW FILES ------------------------------------------------------------
        # allows the user to view input, output, and expected files using their
        # default text editor on a failed test case
        menu_view_files = tk.Menu(menu,tearoff=0)
        menu.add_cascade(menu=menu_view_files, label='View Files')

        menu_view_files.add_command(label="Input", command= lambda: self.input_file(test_case))
        menu_view_files.add_command(label="Your Output", command= lambda: self.output_file(test_case))
        menu_view_files.add_command(label="Expected Output", command= lambda: self.expected(test_case))
        menu_view_files.add_command(label="Open All", command= lambda: self.open_all(test_case))


        enable_menu_item(menu,menu_item,test_case.is_fail())
        menu_item +=1
        # -----------------------------------------------------------------------

        # DIFFMERGE -------------------------------------------------------------
        # Attempts to run diffmerge. Note that the diffmerge application must be 
        # installed on your machine for this to work.
        def run_diffmerge(file1,file2):
            diffmerge_exec = self.config['DEFAULT'].get('diffmerge_exec',myplatform.diffmerge_exec()) 
            subprocess.call([diffmerge_exec, "--nosplash", file2,file1])

        menu_diff_files = tk.Menu(menu,tearoff=0)
        if test_case.is_fail():
            match_result = test_case.result_details
            for file_pair in match_result.diff_files():
                menu_diff_files.add_command(label=os.path.basename(file_pair[0])
                    ,command=lambda: run_diffmerge(*file_pair))
        menu.add_cascade(menu=menu_diff_files, label='Diffmerge')
        enable_menu_item(menu,menu_item,test_case.is_fail() and test_case.result_details.diff_files())
        menu_item +=1
        # ------------------------------------------------------------------------
        
        # REMOVED BECAUSE OF LIMITED FUNCTIONALITY (We never need these options)
        # # Extra files ----------------------------------------------------------
        # extra_outfiles = ""
        # if test_case.is_fail():
        #     match_result = test_case.result_details
        #     extra_outfiles = \
        #      "\n".join([os.path.basename(f) for f in match_result.extra_outputs()])
             
        # menu.add_command(label="Extra outputs"
        #     , command = lambda: messagebox.showinfo("Extra output files",extra_outfiles)
        #     )
        # enable_menu_item(menu,menu_item,test_case.is_fail() and extra_outfiles!="")
        # menu_item +=1
        # -----------------------------------------------------------------------

        # # Missing files -------------------------------------------------------
        # missing_outfiles = ""
        # if test_case.is_fail():
        #     match_result = test_case.result_details
        #     missing_outfiles = \
        #      "\n".join([os.path.basename(f) for f in match_result.missing_outputs()])
             
        # menu.add_command(label="Missing outputs"
        #     , command = lambda: messagebox.showinfo("Missing output files",missing_outfiles)
        #     )
        # enable_menu_item(menu,menu_item,test_case.is_fail() and missing_outfiles!="")
        # menu_item +=1
        # -----------------------------------------------------------------------
        
        # QUICK DIFFERENCE ------------------------------------------------------
        # Prints the quick difference output (always available even if diffmerge
        # is not installed or view files does not work)
        quick_diff = ""
        if test_case.is_fail():
            match_result = test_case.result_details
            quick_diff = match_result.to_string()             
        menu.add_command(label="Quick difference"
            #, command = lambda: tk.messagebox.showinfo("Quick difference",quick_diff)
            , command = lambda: TextDialog(self, "Quick difference", quick_diff)
            )
        enable_menu_item(menu,menu_item,test_case.is_fail())
        menu_item +=1
        # -----------------------------------------------------------------------

        menu.post(event.x_root, event.y_root)

    def on_doubleclick(self, event):
        item = self.treeview.identify('item', event.x, event.y)
        print("you clicked on", item, self.treeview.item(item,"values"))
        
    def update_results(self):
        for k,v in self.script_tests.items():

            r = v.get_result_str()

            if r == "Pass" or r == "Presentation Error":
                self.treeview.item(k, tags="accept")

            elif r == "N/A":
                self.treeview.item(k, tags="empty")

            else:
                self.treeview.item(k, tags="fail")

            self.treeview.set(k,'Result',v.get_result_str())


class Application(ttk.Frame):
    def __init__(self, master=None):
        ttk.Frame.__init__(self, master)
        
        self.stop_early = False
        self.verbose = None
        self.test_results = {} # for each script, a ResultViewer
        self.script_source = None
        self.testcase_source = None
        self.script_dir = None # after potentially unzipping the zip file
        self.test_suite = None
        self.verify_script_dir = False # whether the script directory name has to be the same as the assignment name
        self.summary = (0,0,0,0) # Tests, Errs, Soft-test failures, Hard-test failures
        self.any_language = True # whether any language is allowed, or just python
        self.timeout = 5    # default is 5 seconds, change using config file (testcenter.ini)
        self.script_based = 0 # whether the marking will be diff based (distinct correct answers) or script based (multiple correct answers)
        
        self.config = configparser.ConfigParser()
        self.root = master # must be a toplevel window or the root
        self.pack(expand=tk.YES,fill=tk.BOTH) # follow size of parent
        self.createWidgets()
        self.createMenus()
        
        self.update_menustate()

        success = self.read_config()

        if success:
            self.welcome_message()

    def welcome_message(self):
        """ Prints a welcome / intro message in the terminal when the application
        is initialized."""
        acc_str = myplatform.accelerator_string()
        print()
        print("-"*75)
        print("             Welcome to the Morning Problem Test Center!")
        print("-"*75)
        print()
        print("To run your tests, click Run -> Run all in the application window, \nor press {}+R.\n".format(acc_str))
        print("For more information, click Help (in the top bar of the application window)\nor press {}+H to access the help window.".format(acc_str))
        print("-"*75)
        print()
        
    def read_config(self):
        config = self.config
        try:
            config.read(INI_FILE)
        except:
            print("Reading config file failed. Please ensure that the first line of the file reads '[DEFAULT]' and try again.")
            return False

        dc = config['DEFAULT']
        self.verbose = eval(dc.get("verbose", "False"))     # enables or disables additional print statements
        self.menu_options.entryconfigure(0, label="Toggle high print volume? Currently: {}".format(self.verbose))

        self.stop_early = eval(dc.get("stop_early", "True"))   # enables or disables stopping early after the first failed test case
        self.menu_options.entryconfigure(1, label="Stop at first failed test? Currently: {}".format(self.stop_early))

        sst = dc.get('script_source_type',None)
        if sst:
            ss = dc.get('script_source',None)
            if ss:
                self.scripts_changed(sst, ss)
                if self.verbose:
                    print("Script source: %s",self.script_source)
        self.testcase_source = dc.get('testcase_source',None)
        if self.verbose:
            print("Testcase source: %s" % self.testcase_source)
        if self.testcase_source:
            self.testcase_changed()
            
        self.verify_script_dir = dc.get('verify_script_dir',False)

        self.timeout = float(dc.get("timeout", 5))     # set the timeout to 5 if not specified in the file
        self.script_based = dc.get("script_based", 0)       
        print(self.script_based)
        self.update_statusbar()

        # configuration successful
        return True

    def write_config(self):
        with open(INI_FILE,'w') as configfile:
            self.config.write(configfile)
    
    # -----------------------------------------------------------------                
    # Building the GUI 
    # -----------------------------------------------------------------                

    def createWidgets(self):
        self.sb4 = MyStatusBar(self,"Timeout: %s seconds per testcase")
        self.sb4.set_data(self.timeout)
        self.sb3 = MyStatusBar(self,"Script folder: %s")
        self.sb3.set_data("")
        self.sb2 = MyStatusBar(self,"Testcase folder: %s")
        self.sb2.set_data("")
        self.sb1 = MyStatusBar(self,"Tests: %s   Errors: %s   Fails: %s   Presentation Errors: %s")
        self.sb1.set_data(0,0,0,0)
        self.update_statusbar()
        
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill=tk.BOTH, expand=tk.YES, padx=2,pady=3)
        # extend bindings to top level window allowing
        #   CTRL+TAB - cycles thru tabs
        #   SHIFT+CTRL+TAB - previous tab
        #   ALT+K - select tab using mnemonic (K = underlined letter)        
        self.nb.enable_traversal()
        self.empty_notebook()

    def empty_notebook(self):
        self.test_results = {}
        for i in self.nb.tabs():
            self.nb.forget(i)
        rv = self.test_results[''] = ResultViewer(self.nb,self.config,'<script>',dict())
        self.nb.add(rv)

    def add_menu_accelerators(self):
        """ Binds keyboard shortcuts to the appropriate functions. """

        # @todo enable/disable these as the menu state changes 
        acc = ( ("<Control-z>",lambda x: self.select_script_zip())
              , ("<Control-d>",lambda x: self.select_script_dir())
              , ("<Control-t>",lambda x: self.select_testcase_dir())
              , ("<Control-x>",lambda x: self.root.quit())
              , ("<Control-r>",lambda x: self.runall()) 
              , ("<Control-h>",lambda x: self.helpMenu()) 
        )
        if myplatform.is_mac():
            acc = ( ("<Command-z>",lambda x: self.select_script_zip())
                  , ("<Command-d>",lambda x: self.select_script_dir())
                  , ("<Command-t>",lambda x: self.select_testcase_dir())
                  , ("<Command-x>",lambda x: self.root.quit())
                  , ("<Command-r>",lambda x: self.runall()) 
                  , ("<Command-h>",lambda x: self.helpMenu())
            )            
        for a in acc:
            self.root.bind_all(a[0],a[1])        

    def createMenus(self):
        """ Creates the menus visible at the top of the Test Center application. 

        The three menus created are File, Run, and Help."""

        top = tk.Menu(self.root)
        self.root.config(menu=top)

        # CREATE FILE MENU
        file = self.menu_file = tk.Menu(top,tearoff=False)
        acc_str = myplatform.accelerator_string()
        file.add_command(label='Script ZIP file'
            , command=self.select_script_zip, underline=7, accelerator=acc_str+"+Z")
        file.add_command(label='Script directory file'
            , command=self.select_script_dir, underline=7, accelerator=acc_str+"+D")
        file.add_separator()
        file.add_command(label='Testcase directory'
            , command=self.select_testcase_dir, underline=0, accelerator=acc_str+"+T")
        if not myplatform.is_mac(): # on a mac, quit always exists
            file.add_separator()
            file.add_command(label='Exit'
                , command=self.root.quit, underline=1, accelerator=acc_str+"+X")
        top.add_cascade(label='File', menu=file, underline=0)

        ##### CREATE RUN MENU #####
        run = self.menu_run = tk.Menu(top,tearoff=False)
        run.add_command(label="Run all"
            , command=self.runall, underline=0, accelerator
            =acc_str+"+R")
        top.add_cascade(label='Run', menu=run, underline=0)

         ##### OPTIONS MENU #####
        options = self.menu_options = tk.Menu(top,tearoff=False)
        options.add_command(label="Toggle high print volume? Currently: {}".format(self.verbose)
            , command=self.toggleVerbose)
        options.add_command(label="Stop at first failed test? Currently: {}".format(self.stop_early)
            , command=self.toggleStop)
        top.add_cascade(label='Options', menu=options, underline=0)


        ##### CREATE HELP MENU #####
        helpmenu = self.menu_help = tk.Menu(top,tearoff=False)
        top.add_command(label='Help', command=self.helpMenu, underline=0, accelerator=acc_str+"+H")
        
        ##### 
        self.add_menu_accelerators()
        
    # -----------------------------------------------------------------                
    # Update the state of the GUI 
    # -----------------------------------------------------------------
                         
    def update_menustate(self):
        enable_menu_item(self.menu_run,0,self.runall_enabled())

    def update_statusbar(self):
        self.sb4.set_data(self.timeout)
        self.sb3.set_data(self.script_source[1] if self.script_source else None)
        self.sb2.set_data(self.testcase_source)
        self.summary = ((0,0,0,0) if self.test_suite==None else self.test_suite.get_summary())
        self.sb1.set_data(*self.summary)

    def update_notebook(self):
        for v in self.test_results.values():
            v.update_results()

    # -----------------------------------------------------------------                
    # Implementing menu actions 
    # -----------------------------------------------------------------                
        
    def select_script_zip(self):
        zipfile = filedialog.askopenfilename(title='Select a zip-file of the scripts to be tested'
                , filetypes = (("ZIP files", "*.zip"), )
                )
        self.scripts_changed("zip",zipfile)

    def select_script_dir(self):
        fld = filedialog.askdirectory(title='Select the directory of the scripts to be tested')
        self.scripts_changed("dir",fld)
        
    def select_testcase_dir(self):
        fld = filedialog.askdirectory(title='Select the directory containing the testcases')
        if fld:
            self.testcase_source = fld
            
            if self.verbose:
                print("Selected test directory:",fld)
            self.testcase_changed()
                                
    def runall(self):
        if self.runall_enabled():
            self.reset_results()
            self.update_notebook()            
            self.update_statusbar()
            try:
                self.prep_submission()
                print("Running all tests against the submission files: ")
                self.test_suite.run_tests(self.script_dir,timeout=self.timeout,gen_res=False,visible_space_diff=True,verbose=self.verbose, stop_early=self.stop_early, script_based=self.script_based)
                print("Finished running tests.")
            except RuntimeError as err:
                tk.messagebox.showerror("Error", str(err))
            self.update_menustate()
            self.update_notebook()            
            self.update_statusbar()

    def toggleVerbose(self):
        if self.verbose == True:
            self.verbose = False
        else:
            self.verbose = True

        self.menu_options.entryconfigure(0, label="Toggle high print volume? Currently: {}".format(self.verbose))

    def toggleStop(self):
        if self.stop_early == True:
            self.stop_early = False
        else:
            self.stop_early = True

        self.menu_options.entryconfigure(1, label="Stop at first failed test? Currently: {}".format(self.stop_early))

    def helpMenu(self):
        h = HelpMenu(root, "Help Menu")
        


    # -----------------------------------------------------------------                
    # Propagating, managing change of state 
    # -----------------------------------------------------------------                
                
    def runall_enabled(self):
        return self.script_source!=None and self.testcase_source!=None and self.test_suite!=None

    def scripts_changed(self,src_type,src):
        if self.verbose:
            print("scripts_changed: (%s,%s)" % (src_type,src))
        if not src:
            return
        new_source = (src_type,src)
        if new_source!=self.script_source:
            self.script_source = new_source
            self.config['DEFAULT']['script_source_type'] = new_source[0]
            self.config['DEFAULT']['script_source'] = new_source[1]
            self.write_config()

            if self.verbose:
                print("Selected:",new_source[1])
            
            self.script_dir = None
            try:
                self.prep_submission()
            except RuntimeError as err:
                tk.messagebox.showerror("Error", str(err))
                
            self.reset_results()
            self.update_notebook()
            self.files_changed()
    
    def reset_results(self):
        if self.test_suite!=None:
            for test_caselist in self.test_suite.test_cases.values():
                for test_case in test_caselist.values():
                    test_case.reset_result()
        
    def reset_test_suite(self):        
        self.test_suite = None
        self.empty_notebook()
        self.update_statusbar()

    def testcase_changed(self):
        # reset the contents of the notebook
#        num_tabs = self.nb.index("end") # do NOT use numeric indeces with forget: they don't work
#        print(self.nb.tabs()[0])


        print("Creating test suite:")
        try:
            self.test_suite = TestSuite.TestSuite(self.testcase_source,any_language=self.any_language)
        except RuntimeError as err:
            tk.messagebox.showerror("Error creating the test suite", str(err))
            self.reset_test_suite()
            return
        print("Done!")
                        
        print("Collecting tests:")
        try:
            self.test_suite.collect_tests(create_missing_dirs=False)
        except RuntimeError as err:
            tk.messagebox.showerror("Error collecting the tests", str(err))
            self.reset_test_suite()
            return
        print("Done!")
        
        if self.verbose:
            print("Collected %s tests" % len(self.test_suite.test_cases))

        self.config['DEFAULT']['testcase_source'] = self.testcase_source
        self.write_config()
        self.init_notebook()
        
        self.files_changed()
        
    def init_notebook(self):
        print("Initializing test-case display: ")
        if self.test_suite==None:
            print("     Clearing notebook...")
            self.empty_notebook()
            return
        self.test_results = {}
        for i in self.nb.tabs():
            self.nb.forget(i)
        # updating notebook
        for script_name,script_tests in sorted(list(self.test_suite.test_cases.items())):
            print("     Found script: {}.".format(script_name))
            rv = self.test_results[script_name] = ResultViewer(self.nb,self.config,script_name,script_tests)
            self.nb.add(rv)

        print("     Initialization complete.")

    def files_changed(self):
        self.update_menustate()
        self.update_statusbar()

    def prep_submission(self):
        if self.test_suite!=None and self.script_dir==None:

            if self.verbose:
                print("Verifying submission files...")

            self.script_dir = TestSuite.prep_submission(self.script_source[1]
                    ,self.test_suite.assignment_name,self.verify_script_dir)
                

root = tk.Tk()
app = Application(root)
app.master.title('Morning Problem Test Center')
dpi_value = int(root.winfo_fpixels('1i')) # get the number of pixels in one inch
# 96 is the number of pixels per inch that the application was designed for
root.tk.call('tk', 'scaling', '-displayof', '.', dpi_value / 96.0) # set scaling of menus, buttons, etc
root.tk.eval("""
    foreach font [font names] {
        set cursize [font configure $font -size]
        font configure $font -size [expr {int($cursize * %d / 96.0)}]
    }
""" % dpi_value) # set scaling of fonts
app.mainloop()  
