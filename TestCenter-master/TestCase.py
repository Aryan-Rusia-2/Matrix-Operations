######################################################################
#   File: TestCase.py
#
#   Description:
#       Used to manage the data associated with individual test cases.
#
#   Included classes:
#       - TestCase() used to store each test case and run individual
#       tests.
#       - MatchResult() used to determine results (differences between
#       student and expected output) and display quick difference output.
#
######################################################################


import os
import signal
import myplatform
import glob
import shutil
import distutils.dir_util
import tempfile
import sys
import time
from subprocess import Popen, PIPE, TimeoutExpired, run
import mimetypes
import diffs
import logging

def verbose(*args):
    print('-' * 80)
    for arg in args:
        print(arg)

def quiet(*args):
    pass

# trace = logging.debug # allows debug output 
trace = quiet # nullifies debug output

class MatchResult:
    def __init__(self):
        self.match_result = dict() # maps output files to pairs of soft-test and hard-test differences
        self.unmatched_output_files = set()
        self.unmatched_exp_files    = set()
        
    def add_match_result(self,output_file,match_info):
        '''Stores the result of a match
        matchinfo is a tuple of the form:
        (softtest_diffs, hardtest_diffs, actual_dest, exp_path) 
        Here the last two parameters are full filenames.
        '''
        self.match_result[output_file] = match_info
        
    def has_diff(self):
        return self.unmatched_output_files or self.unmatched_output_files or self.match_result
    
    def print(self):
        if self.unmatched_output_files:
            print("Extra output files: %s" % tuple(self.unmatched_output_files))
        if self.unmatched_exp_files:
            print("Missing output files: %s" % tuple(self.unmatched_exp_files))
        if self.match_result:
            for (k,v) in sorted(list(self.match_result.items())):
                print("File: %s" % (os.path.basename(k),))
                print("------------")
                if v[0]:
                    for d in v[0]: print(d,end='')
                else:
                    for d in v[1]: print(d,end='')
                print("------------")
                
    def to_string(self):
        """ Converts the differences found in diffs.py into a usable string that
        will be printed along with some help information for Quick Difference.
        """
        ret = ""
        if self.unmatched_output_files:
            ret += "Extra output files: %s" % tuple(self.unmatched_output_files) + "\n"
        if self.unmatched_exp_files:
            ret += "Missing output files: %s" % tuple(self.unmatched_exp_files) + "\n"
        if self.match_result:
            ret += """This tool summarizes the differences between your output \
and the expected output for a given test case.

Symbol Legend:
-       your output is missing this expected line
+       you output this line but it was not expected
?       highlights the exact change in a line 
        using + or - if applicable
#       for Presentation Error only: spaces and
        newlines display visibly as #

"""
            for (k,v) in sorted(list(self.match_result.items())):
                ret += "Difference in output: %s" % (os.path.basename(k),) + "\n"
                ret += "------------\n"
                if v[0]:
                    for d in v[0]: ret += d
                else:
                    for d in v[1]: ret += d
                ret += "------------\n"
        return ret
    
    def diff_files(self):
        '''Returns the list of files where differences were detected'''
        return [(v[2],v[3]) for k,v in sorted(list(self.match_result.items()))]
    
    def extra_outputs(self):
        return self.unmatched_output_files
    
    def missing_outputs(self):
        return self.unmatched_exp_files


# TODO: doesn't support multiple files passed in yet, also should handle
# expected outputs here
class TestCase:
    
    # result of testing
    TESTRESULT = (PASS, SOFTTEST_FAIL, HARDTEST_FAIL, ERR, TIMEOUT) = range(5)

    def __init__(self, name, script_name,exp_path,output_path,err_path):
        self.name = name
        self.script_name = script_name
        self.exp_path = exp_path
        self.output_path = output_path
        self.err_path = err_path
        # name of assignment
        self.assignment_name = ''
        # inputs
        self.stdin = ''     # standard input (read in during setup)
        self.cli_files = [] # list of files (with full path) available from command line
        self.cli_args = ''  # string holding the command line arguments
        # list of files holding expected results (stdout, stderr, ..):
        self.exp_paths = []
        # list of resource files:
        self.resources = []
        self.result = None # one of TESTRESULT
        self.result_details = MatchResult() # When Error, the exitmsg, otherwise MatchResult

        self.work_path = None
        self.command   = None

    def openExp(self):
        pass

    def is_fail(self):
        return self.result==TestCase.SOFTTEST_FAIL or self.result==TestCase.HARDTEST_FAIL

    def is_err(self):
        return self.result==TestCase.ERR or self.result==TestCase.TIMEOUT

    def is_pass(self):
        return self.result==TestCase.PASS

    def reset_result(self):
        self.result = None
        self.result_details = None

    def get_result_str(self):
        if self.result==None:
            return "N/A"
        return ("Pass", "Fail", "Presentation Error", "Runtime Error", "Timeout Error")[self.result]

    def add_input(self, test_type, input_path):
        if test_type == 'stdin':
            with open(input_path, 'r') as input_file:
                self.stdin = str(''.join(input_file.readlines()))
        elif test_type == 'args':
            with open(input_path, 'r') as input_file: 
                self.cli_args = str(''.join(input_file.readlines())).rstrip()
        else:
            self.cli_files.append(os.path.abspath(input_path))

    def add_resource(self, resource):
        self.resources.append(resource)

    def add_exp_path(self, test_type, exp_path):
        self.exp_paths.append(exp_path)

    def get_cli(self):
        '''Get the command line arguments for this test'''
        args = self.cli_args

        # if we have only a single file, or no args, just return the file
        if len(args) == 0 and len(self.cli_files) == 1:
            return self.cli_files[0]

        # len(args) == 0 or len(self.cli_files)!=1:
        for file in self.cli_files:
            # Replace the bare file name with the full path to the file
            #@todo: this assumes bare file names passed in through args are bare filenames
            args_repl = args.replace(os.path.basename(file), '"' + file + '"')
            if args_repl == args:
                raise RuntimeError("""The test file %s found in the """
                    """input directory does not appear to be called by """
                    """the arguments %s""" % (os.path.basename(file),self.cli_args))
            args = args_repl
        return args

    def __copy_resources(self,work_path, print_cmd):
        '''Copy all resources from the resource directory
         to the working directory. 
         Return the names of resource files.
         '''
        res_basenames = []
        for res_file in self.resources:
            res_base = os.path.basename(res_file)
            pure_name = res_base.replace(self.name + "-", "")
            if print_cmd:
                print("Copying %s to %s" %(res_file,os.path.join(work_path, pure_name)))
            shutil.copyfile(res_file, os.path.join(work_path, pure_name))
            res_basenames.append(pure_name)
        return res_basenames

    def __copy_sourcefiles(self,script_path,work_path, up_dir, print_cmd):
        '''Copy all files from the script source directory
        to the working directory.
        Return the names of files copied.
        '''
        basenames = []
        if up_dir:
            spath = os.path.join(os.path.dirname(script_path), '..', '*')
        else:
            spath = os.path.join(os.path.dirname(script_path), '*')
        files = glob.glob(spath)
        for filepath in files:
            filename = os.path.basename(filepath)
            tofile = os.path.join(work_path,filename)
            if os.path.isfile(filepath):
                shutil.copyfile(filepath, tofile)
                if print_cmd:
                    print("Copying %s to %s" %(filename,tofile))
                basenames.append(filename)

        # print(basenames)
        return basenames

    def __run_script(self,work_path,script_path,timeout,any_language,print_cmd=False):
        """ Runs a test using the script. 
        
        Arguments:
            work_path and script_path are used to run the test
            timeout is the timeout per test case
            any_language is a boolean set to False if the script file has a .py extension
            print_cmd is the same as verbose in other files
        """

        # Run the test with redirected streams
        interpreter_path = sys.executable
        (base,ext) = os.path.splitext(script_path)
        if ext==".py": 
            any_language = False
        command = '%s "%s" %s' % (interpreter_path, script_path, self.get_cli()) \
            if not any_language else "%s %s" % (script_path, self.get_cli())
        extra_files_in_workpath = []
        if any_language:
            # copy all files from the script_path to the work directory
            extra_files_in_workpath = self.__copy_sourcefiles(script_path,work_path, False, print_cmd)
            extra_files_in_workpath += self.__copy_sourcefiles(script_path, work_path, True, print_cmd)
            
        if print_cmd:
            print("From directory %s, on test-case %s, running command:\n%s"
                % (work_path,self.name,command) 
            )
        self.work_path = work_path
        self.command   = command
        process = Popen(command, shell=True, stdin=PIPE
                    , stdout=PIPE, stderr=PIPE, cwd=work_path
                    , preexec_fn=os.setsid)
        usePoll = False;
        if usePoll:
            process.stdin.write(bytes(self.stdin, "utf-8"))
            fin_time = time.time() + timeout
            s = 0.01
            while process.poll() == None and fin_time > time.time():
                print("Sleeping for",s,"seconds")
                time.sleep(s)
                s *= 2.0
            # if timeout reached, raise an exception
            if fin_time < time.time():
                print("Script has not exited after " + str(timeout) +
                      " seconds. So forcing termination.")
                process.terminate()
    
            outdata = process.stdout.read()
            errdata = process.stderr.read()   # data are bytes
        else:
            # fin_time = time.time() + timeout
            try:
                outdata, errdata = process.communicate(bytes(self.stdin, "utf-8"),timeout=timeout)    
            except TimeoutExpired:
                if print_cmd:
                    print("Timeout of %s seconds expired. Trying to kill process." % timeout)
                else:
                    print("Timeout of %s seconds expired." % timeout, end=" ")
                # because we started with shell=True, we need to kill the process group on Linux:
                # see http://stackoverflow.com/questions/4789837/how-to-terminate-a-python-subprocess-launched-with-shell-true
                if myplatform.is_linux():
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                else:
                    process.kill()

                if print_cmd:
                    print("Kill sent. Waiting for process to return.", end=" ")
                # process.wait()
                outdata, errdata = (b"",b"")
                try:
                    outdata, errdata = process.communicate(timeout=0.1)
                except TimeoutExpired:
                    outdata, errdata = (b"",b"")
                    print("OOPS: process got stuck")
                
                if print_cmd:
                    print("Process returned.")
                
                errdata = b"Timeout expired.\n" + errdata

                self.result = TestCase.TIMEOUT   # et result to TIMEOUT
                #~ exitstatus = process.wait()
                #~ print("outs",outs,"\nerrs:", errs, "\nexitstatus", exitstatus)
                #~ raise
        exitstatus = process.wait()       # requires binary files

        if print_cmd:
            trace(exitstatus)
        # trace(outdata + errdata + exitstatus)
        return (outdata,errdata,exitstatus,extra_files_in_workpath)
    
    def run_test(self,submission_dir,timeout,gen_res,visible_space_diff,any_language,print_cmd=False,script_based=False):
        script_path = os.path.abspath(os.path.join(submission_dir, self.script_name))
        # If C++
        if any_language:
            script_path = os.path.abspath(os.path.join(submission_dir, ".build/build.sh"))
        if not os.path.exists(script_path):
            raise RuntimeError("Submission is missing script %s from directory %s" % (self.script_name,submission_dir))

        if print_cmd:
            print("Running",script_path)
        else:
            print("Running {}...".format(self.name), end = " ")
        work_path = tempfile.mkdtemp(prefix="work-") #@todo clean this up at the end
        res_basenames = self.__copy_resources(work_path, print_cmd)

        # remove all the old outputs from this test
        old_outs = glob.glob(os.path.join(self.output_path, self.name) + "*")
        for old_out in old_outs:
            os.remove(old_out)

        # remove all the old error reports from this test
        err_file = os.path.join(self.err_path, self.name + ".txt")

        if os.path.exists(err_file):
            os.remove(err_file)

        (outdata,errdata,exitstatus,extra_files_in_workpath) = \
        self.__run_script(work_path,script_path,timeout,any_language,print_cmd)
        
        res_basenames += extra_files_in_workpath
        
        if exitstatus or errdata:  # save status+stderr
            open(err_file, 'wb').write(errdata)  # redundant??
            outpathbad = os.path.join(self.output_path, self.name + '.stdout.txt') # during generation mode!?
            open(outpathbad, 'wb').write(outdata)

            if self.result != TestCase.TIMEOUT:
                self.result = TestCase.ERR
            self.result_details = (exitstatus,errdata,err_file,outpathbad)
#            self.info = "Crashed with error message and status:" + str(exitstatus)
        else:
            stdout_path = os.path.join(work_path, 'stdout.txt')
            stderr_path = os.path.join(work_path, 'stderr.txt')
    
            with open(stderr_path, "wb") as stderr_file:
                stderr_file.write(errdata)        
            with open(stdout_path, "wb") as stdout_file:
                stdout_file.write(outdata)

        self.__compare_results(outdata,errdata,exitstatus,work_path,res_basenames,gen_res,visible_space_diff,script_based)
            
        return (self.result,self.result_details)

    def err_msg(self):
        '''Returns the error message from the result (if there was an error)'''
        if self.result==TestCase.ERR or self.result==TestCase.TIMEOUT:
            return self.result_details[1].decode('utf-8') 
        return ""
    
    def __create_exp_files(self,actual_files):
        for actual_path in actual_files:
            actual_name = os.path.basename(actual_path)
            # don't copy anything but stderr or stdout
            if actual_name in ["stderr.txt", "stdout.txt"]:
                # Move it to the expected folder with a name corresponding to the test
                actual_basename = self.name + "-" + actual_name
                print("Saving", actual_path, "to", actual_basename)
                exp_dest = os.path.join(self.exp_path, actual_basename)
                shutil.move(actual_path, exp_dest)
        
    @staticmethod
    def __read_file(filename):
        file_type = mimetypes.guess_type(filename)[0]
        contents = None
        is_text = (file_type==None or file_type.startswith('text'))
        if is_text:
            with open(filename, 'r', errors="replace") as file: 
                contents = file.readlines()
        else:
            with open(filename, 'rb', errors="replace") as file:
                contents = file.read()
        return (contents,is_text)
                
    def __compare_results(self,outdata,errdata,exitstatus,work_path,res_basenames,gen_res,visible_diff,script_based=False):
        trace("Comparing results")
        self.result = TestCase.PASS
        self.result_details = MatchResult()
            
        output_files = glob.glob(os.path.join(work_path, "*"))

        if len(self.exp_paths) == 0 and not gen_res:
            raise RuntimeError("Testcase %s for script %s missing Expected directory."
                % (self.name,self.script_name))

        # Generate expected files to compare to
        if len(self.exp_paths) == 0:
            print("Generating expected result files for test %s and script %s." 
                  % (self.name,self.script_name))
            self.__create_exp_files(output_files)
            return

#        self.result_details.unmatched_output_files = set(output_files)
#        self.result_details.unmatched_exp_files = set(self.exp_paths)
        self.result_details.unmatched_output_files = set(output_files)
        self.result_details.unmatched_exp_files = set(self.exp_paths)
        for output_file in output_files:
            output_file_basename = os.path.basename(output_file)
            # ignore resources, __pycache__, and files from the script source dir
            # and leave them in the work dir
            if output_file_basename in res_basenames or output_file_basename=="__pycache__":
                self.result_details.unmatched_output_files.remove(output_file)
                continue
            # Move the actual file to Outputs with a name corresponding
            # to the test
            actual_basename = self.name + "-" + output_file_basename
            # Deprecated style:
#            actual_basename = self.script_name + "-" + self.name + "-" + output_file_basename
            # move the actual file into the output directory and rename it
            actual_dest = os.path.join(self.output_path, actual_basename)

            shutil.move(output_file, actual_dest)
            actual,is_text = TestCase.__read_file(actual_dest)
            trace("Looking for match for output file %s" % (actual_basename,))

            if script_based:
                script_path = os.path.join(os.getcwd(), "soln/mark_script.py")
                # Compare actual output against marking script
                args = ["python", script_path]
                args.extend(actual)
                out = run(args)
                if out.returncode == 0: self.result = TestCase.HARDTEST_FAIL

                print("finished script test: ", self.result)
            else:
                # Compare a diff of every expected output
                for exp_path in self.exp_paths:
                    exp_path_basename = os.path.basename(exp_path)
                    if exp_path_basename == actual_basename:
                        self.result_details.unmatched_exp_files.remove(exp_path)
                        self.result_details.unmatched_output_files.remove(output_file)
                        expected, is_text = TestCase.__read_file(exp_path)
                        trace("Comparing %s and %s" % (exp_path, output_file))
                        
                        (softtest_diffs,hardtest_diffs) =\
                            diffs.diff(actual, expected, is_text, visible_diff)
                        if softtest_diffs or hardtest_diffs:
                            outpathbad = os.path.join(self.output_path, actual_basename+".err")                        
                            open(outpathbad, 'wb').write(outdata)
                            self.result = TestCase.SOFTTEST_FAIL if softtest_diffs else TestCase.HARDTEST_FAIL 
                            self.result_details.add_match_result( output_file_basename, (softtest_diffs, hardtest_diffs, actual_dest, exp_path) )
                        break
                                        
        for exp_path in self.result_details.unmatched_exp_files:
            errdata = errdata.decode('utf-8')
            errdata += "\nExpected file \"{}\" has no output file match".format(exp_path)
            errdata = str.encode(errdata)
            trace(errdata)

            basename = os.path.basename(exp_path)

            err_file = os.path.join(self.err_path, basename)
            open(err_file, 'wb').write(errdata + b"\n")

            self.result = TestCase.ERR
            self.result_details = (
                0,
                errdata,
                err_file,
                os.path.join(self.output_path, basename)
            )
