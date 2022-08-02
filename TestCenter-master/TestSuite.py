######################################################################
#   File: TestSuite.py
#
#   Description:
#       Contains functions and classes to manage test case information,
#       including running tests and updating data.
#
#   Included functions:
#       None of these are ever called the way we use the testcenter.
#       - prepSubmission(), verbose(), quiet()
#
#   Included classes:
#       - TestSuite() manages test case information using instances
#       of the TestCase() class. Important functions to note:
#           - print_result(): used to print result information to
#                             the terminal
#           - run_tests(): called from testcenter_gui.pyw to run all
#                          test cases
#
######################################################################
import glob
import os
import re
from TestCase import TestCase
import logging
# logging.basicConfig(level=logging.DEBUG)
# logging.basicConfig(level=logging.WARNING)

import zipfile
import tempfile

# @todo: Separate initialization was the test structure (so that alternate initialization becomes possible)
# testcase_dir = None  # The base marking dir


def verbose(*args):
    print('-' * 80)
    for arg in args:
        print(arg)

def quiet(*args):
    pass

# trace = logging.debug # allows debug output 
trace = quiet # nullifies debug output

def prep_submission(submission,assignment_name,verify_dir_structure=True):
    '''Prepares the submission for testing.
    If the submission is a zip file, it is unzipped
    to a temporary directory, otherwise submission
    must be a directory.
    The directory itself must end with assignment_name.
    If some problem is found, an exception is thrown.
    Otherwise the directory containing the scripts
    to be tested is returned.
    '''
    # If the submission is a zip file expand it into the temp dir
    if submission.lower().endswith(".zip"):
        temp_path = tempfile.mkdtemp(prefix=assignment_name + '-')
        trace("Expanding %s into %s" % (submission, temp_path))
        zfile = zipfile.ZipFile(submission)
        zfile.extractall(temp_path)
        submission = os.path.join(temp_path,assignment_name)
        trace("Checking for the existence of %s" % (submission,))
        if not os.path.exists(submission):
            raise RuntimeError("The zip file must contain a directory called %s"
                  % (assignment_name,))
    elif not os.path.exists(submission):
        raise RuntimeError("Missing directory %s" % (submission,))
    submission = os.path.normpath(submission) #  remove duplicates // etc..
    basename = os.path.basename(submission)
    #  check whether the submission directory ends with the assignment_name
    if verify_dir_structure and basename != assignment_name:
        raise RuntimeError("""The submission directory must end with %s, """
              """not with %s""" % (assignment_name, basename) )
    return submission


class TestSuite:
    #  the pattern of testcase names is ASSIGNMENTNAME-SCRIPTNAME-test, as below:
    TESTCASENAME_REGEXP_PY = re.compile("(as-(\d+)-(\d+))-([\w\-]+\.py)-test")
    TESTCASENAME_REGEXP_ANY = re.compile("(as-(\d+)-(\d+))-([\w\-\.]+)-test")

    #  An input file in a test case has the format <testname>-<type>.txt,
    #  where <testname> is the name of the testcase,
    #  and type is either "stdin", or "arg" or something else.
    #  When type is "stdin", the contents of the input file determines the standard
    #  input for the test case.
    #  When type is "arg", the contents of the input file determines the arguments
    #  to be passed to the script to be tested.
    #  In the remaining cases, the file is treated as a command line
    #  input file (<testname>- is chopped from the filename).
    #  In case more than one command line file
    #  is present they will not be passed in automatically, instead
    #  <name>-arg.txt will need to call the files in their
    #  appropriate order. When an <arg> file is present, the file names will
    #  not be passed automatically regardless.
    INPUT_TYPE_RE_PTN = "(\w+)-(\w+)\.(?:\w+)"
    INPUT_TYPE_RE = re.compile(INPUT_TYPE_RE_PTN)

    #  Resource filename pattern: <testname>-<resource_name>.<ext>
    #  Here, resource_name and ext cannot have a dash in it (the last dash is taken
    #  in determining the two parts).
    RESOURCE_RE = re.compile("(\w+)-([^-]*)")

    #  Deprecated: Expected output file pattern: <scriptname>.<ext>-<testname>-<type>.<ext>
    #  Expected output file pattern: <testname>-<type>.<ext>
    #
    OUTPUT_RE = INPUT_TYPE_RE #  re.compile("(?:\w)+\.(?:\w+)-(\w+)-([^.]+)\.(?:\w+)")
    #                     in1 - stdout.text

    #  the subdirectories for each script to be tested:
    TESTCASE_SUBDIRECTORIES = \
    (EXPECTED_DIR, ERROR_DIR, INPUT_DIR, OUTPUT_DIR, RESOURCE_DIR) =\
     ("Expected", "Errors", "Inputs", "Outputs", "Resources")

    #  list of files allowed to be in the test directory:
    allowed_files = ("marking.py", "pep8.py", "marking.ini", "marking_gui.pyw"
        , "diffs.py", "TestCase.py", "TestSuite.py", "myplatform.py"
        , "SimpleDialog.py"
        )

    def __init__(self,testcase_dir,any_language):
        ''' Sets up the TestSuite by collecting all the test cases
            from the testcase_dir directory.
        '''
        self.testcase_dir = testcase_dir
        self.any_language = any_language
        self.TESTCASENAME_REGEXP = TestSuite.TESTCASENAME_REGEXP_ANY if self.any_language else TestSuite.TESTCASENAME_REGEXP_PY
        self.test_cases = {} #  dict of dict; usage: test_cases[scriptname][testname]
        self.assignment_name = self.__verify_testdir_contents()
        self.testpaths = None

    def collect_tests(self, create_missing_dirs):
        ''' Collects all test cases in the given marking dir.
            - create_missing_dirs (boolean): Whether to create missing directories
            (set this to True when the suite is used to generate the expected output files)
        '''
        test_cases = self.test_cases = {}

        test_directories = glob.glob(os.path.join(self.testcase_dir, "*"))
        self.testpaths = test_directories

        script_names = []
        #  Go through each of the test scripts
        for test_path in test_directories:
            print("     Looking into {}...".format(test_path))
            m = self.TESTCASENAME_REGEXP.match(os.path.basename(test_path))
            if m==None:  #  Not a script test directory
                continue
            if m.group(1)!=self.assignment_name:
                raise RuntimeError("Unexpected directory %s; does not match assignment-name %s" %(test_path,self.assignment_name))
            #  check that the full directory structure is there. If absent error
            #  and exit unless gen_results is present, in which case generate
            self.__verify_scripttest_dir(test_path, create_missing_dirs)

            script_name = m.group(4)
            self.problem_name = script_name[:-3]
            self.problem_name = "matrix"
            if script_name[-3:] == ".py":
                self.any_language = False
            #  reset the testcases for the given script:
            test_cases = self.test_cases[script_name] = {}

            print("     Adding input files...")
            self.__add_input_files(test_cases,script_name,test_path)
            print("     Adding resource files...")
            self.__add_resource_files(test_cases,script_name,test_path)
            print("     Adding expected output files...", end=" ")
            self.__add_exp_files(test_cases,script_name,test_path)


    def __verify_scripttest_dir(self, test_path, create_missing_dirs):
        for fld in self.TESTCASE_SUBDIRECTORIES:
            dir_path = os.path.join(test_path, fld)
            if not os.path.exists(dir_path):
                if create_missing_dirs:
                    trace("generating directory %s" % (dir_path,))
                    os.mkdir(dir_path)
                else:
                    raise RuntimeError("Missing directory %s" % (dir_path,))

    def print_result(self, result, test_case, detail, stop_early, verbose):
        if result==TestCase.PASS:
            print("Pass")
        elif result==TestCase.SOFTTEST_FAIL:
            print("Failed with incorrect output")
        elif result==TestCase.HARDTEST_FAIL:
            print("Presentation error")
        elif result ==TestCase.TIMEOUT:
            print("Time limit exceeded.")
        else:
            print("Failed with error")

            # PRINT THE ERROR ONLY IF THIS IS THE ONLY ERROR MESSAGE THAT WILL PRINT
            if stop_early:
                print("*"*75)
                print("BEGIN ERROR MESSAGES FOR TESTCASE {}:".format(test_case.name))
                print("-"*75)
                print(test_case.err_msg())
                print("-"*75)
                print("END ERROR MESSAGES FOR TESTCASE {}:".format(test_case.name))
                print("*"*75)

        if (result==TestCase.SOFTTEST_FAIL or result==TestCase.HARDTEST_FAIL) and verbose == True:
            detail.print()

    def run_tests(self, submission_dir, timeout, gen_res, visible_space_diff
                  , verbose, stop_early, script_based = False):
        # if C++, then compile ahead of time
        if self.any_language:
            # os.system("mkdir " + submission_dir + "/.build")
            os.system("g++ " + submission_dir + "/" + self.problem_name + ".cpp -o " + submission_dir + "/.build/" + self.problem_name + " -c -std=c++11")
        for (k,v) in sorted(list(self.test_cases.items())):
            trace("Running tests against script %s" % (k,))
            for (kk,vv) in sorted(list(v.items())):
                trace("Running test %s" % (kk,))
                (result,detail) = \
                    vv.run_test(submission_dir,timeout,gen_res,visible_space_diff,self.any_language,verbose,script_based)
                if verbose:
                    print("Script %s on test %s: " % (k,kk),end='')

                self.print_result(result, vv, detail, stop_early, verbose)

                if stop_early and (result != TestCase.PASS and result != TestCase.HARDTEST_FAIL):
                    print("""FAILED TEST CASE FOUND. STOPPING EARLY and preventing all other test runs
so the issue can be resolved. (To disable this option, see the Options menu\nin the application.)""")
                    if self.any_language:
                        os.system("rm -f " + submission_dir + "/.build/" + self.problem_name)
                    return

        if self.any_language:
            os.system("rm -f " + submission_dir + "/.build/" + self.problem_name)
        if verbose:
            print("All tests complete.")

    def get_summary(self,script_name=None):
        tests = 0
        errs = 0
        softtest_fails = 0
        hardtest_fails = 0
        passes = 0
        for (k,v) in sorted(list(self.test_cases.items())):
            if script_name==None or script_name==k:
                for (kk,vv) in sorted(list(v.items())):
                    tests += 1
                    if vv.result==TestCase.ERR or vv.result==TestCase.TIMEOUT:
                        errs += 1
                    elif vv.result==TestCase.SOFTTEST_FAIL:
                        softtest_fails += 1
                    elif vv.result==TestCase.HARDTEST_FAIL:
                        hardtest_fails += 1
                    elif vv.result == TestCase.PASS:
                        passes += 1

        if (errs == 0 and softtest_fails == 0 and passes == tests):
            print("All tests passed.\n")
        else:
            print()

        return (tests,errs,softtest_fails,hardtest_fails)

#    def run_tests(self,script_paths):
#        '''Runs the tests collected against a list of scripts.
#           - script_paths: List of paths to python scripts to be tested
#        '''
#        basename_set = {os.path.basename(s) for s in script_paths}
#        if len(basename_set)!=len(script_paths):
#            # collect the duplicates to report the error
#            bs  = set()
#            dup = set()
#            for s in script_paths:
#                b = os.path.basename(s)
#                if b in bs:
#                    dup.add(b)
#                else:
#                    bs.add(b)
#            raise RuntimeError("""The script names %s appear """
#                """multiple times on the list of scripts to be tested"""
#                % (tuple(dup),)
#                )
#        for scr in script_paths:
#            scr_base = os.path.basename(scr)
#            if scr_base in self.test_cases:
#                self.test_cases[scr_base].run_test(submission_dir,timeout,gen_res,show_diff,print_cmd=False)


    def __verify_testdir_contents(self):
        '''Verify the contents of the directory containing the test
           to see if there are invalid files there.
           The only permitted files are the ones listed in
           TestSuite.allowed_files.
           In addition to these files, the directory may contain folders
           whose name follows the TESTCASENAME_REGEXP pattern,
           where each directory must belong to the same assignment.
           The method returns the assignment name.
        '''
        testdir_files = glob.glob(os.path.join(os.path.abspath(self.testcase_dir), "*"))  # get test files
        asn_dir = None
        # make sure we don't have any surprises inside the marking directory
        for file in testdir_files:
            base_name = os.path.basename(file)
            print("     Verifying contents of {}...". format(base_name))
            m = self.TESTCASENAME_REGEXP.match(base_name)
            if m is not None:
                if asn_dir == None:
                    asn_dir = m.group(1) #  e.g., returns as-<NUM>-<NUM>
                elif asn_dir!=m.group(1):
                    raise RuntimeError(
                        """The marking directory contains testcases belonging to multiple """
                        """assignments: (%s,%s)""" % (asn_dir,m.group(1))
                    )
            elif base_name == "__pycache__":  # check contents of pycache
                pycache_files = glob.glob(os.path.join(file, "*"))
                for pycache_file in pycache_files:
                    pf_base = os.path.basename(pycache_file)
                    # error if we find anything but compiled marking or pep8
                    is_allowed = False
                    for allowed in TestSuite.allowed_files:
                        # name of file
                        new_patt = re.search("^(\w+)\.", allowed).group(1)
                        if re.match(new_patt + ".*\.pyc", pf_base):
                            is_allowed = True
                    if not is_allowed:
                        raise RuntimeError("Unexpected files in __pycache__ " +
                             " ".join(pycache_files))
            elif base_name not in TestSuite.allowed_files:
                raise RuntimeError("The marking directory is only allowed to contain "
                     'one or more "<assignment>-<scriptfile>-test" directories, '
                     "containing the tests, along with the files: " +
                     " ".join(TestSuite.allowed_files) + ". " +
                     "The test will not run while the following file is in " +
                     "the directory: " + base_name)

        print("     Checked all files.", end=" ")
        if asn_dir==None:
            print("Found suspicious files:",testdir_files)
            raise RuntimeError("""The marking directory must contain at least one """
                """testcase directory named "<assignment>-<scriptfile>-test", """
                """where <assignment> is of the form "as-<courseid>-<asnnum>", """
                """and <scriptfile> is the name of a python script file (together """
                """with the extension .py. The search expression %s did not return """
                """any such directories.""" %(os.path.join(os.path.abspath(self.testcase_dir), "*"),))
        return asn_dir

    # Get the absolute path to every infrastructure directory for the given script

    def __get_paths(self,test_path): #  assignment_name, script_name):
        dirs = []
        for folder in TestSuite.TESTCASE_SUBDIRECTORIES:
            path = os.path.join(test_path
                    #  self.testcase_dir, assignment_name + "-" + script_name + "-test"
                    , folder)
            dirs.append(path)
        return dirs

    def __add_input_files(self,test_cases,script_name,test_path):
        #  Enumerate the input files:
        input_dir =  os.path.join(test_path, TestSuite.INPUT_DIR)
        exp_path = os.path.join(test_path, TestSuite.EXPECTED_DIR)
        output_path = os.path.join(test_path, TestSuite.OUTPUT_DIR)
        err_path = os.path.join(test_path, TestSuite.ERROR_DIR)
        input_files = glob.glob(os.path.join(input_dir, '*'))

        for input_path in input_files:
            filename = os.path.basename(input_path) #  filename without path, basically
            type_match = TestSuite.INPUT_TYPE_RE.match(filename)
            if type_match==None or len(type_match.groups())!=2:
                raise RuntimeError("""File %s in directory %s unexpected: """
                      """the filename did not match the pattern %s."""
                      % (filename, input_dir, TestSuite.INPUT_TYPE_RE_PTN)
                      )
            # test_name = self.script_name+"-"+type_match.group(1)
            test_name  = type_match.group(1)
            input_type = type_match.group(2)
            test_case = test_cases.setdefault(test_name
                        , TestCase(test_name,script_name,exp_path,output_path,err_path)
                        )
            test_case.add_input(input_type, input_path)

    def __add_resource_files(self,test_cases,script_name,test_path):
        exp_path = os.path.join(test_path, TestSuite.EXPECTED_DIR)
        output_path = os.path.join(test_path, TestSuite.OUTPUT_DIR)
        err_path = os.path.join(test_path, TestSuite.ERROR_DIR)

        resource_path = os.path.join(test_path, TestSuite.RESOURCE_DIR)
        resource_dir_files = os.path.join(resource_path, '*')
        resource_files = glob.glob(resource_dir_files)
        # test_name-file_name.extension
        # resources that will be copied into the resource dir

        for resource_path in resource_files:
            filename = os.path.basename(resource_path)
            res_match = TestSuite.RESOURCE_RE.match(filename)
            if res_match==None:
                # add to each testcase
                for test_name, test_case in test_cases.items():
                    test_case.add_resource(resource_path)
#                old behavior:
#                raise RuntimeError("""Unexpected resource: %s."""
#                     """Resources must be named <testname>-<resource_filename>"""
#                     """with no dash in filename or ext""" % (filename, ))
            #  test_name = script_name+"-"+res_match.group(1)
            else:
                test_name = res_match.group(1)
                # print('test_name',test_name,resource_path)
                test_case = test_cases.setdefault(test_name
                    , TestCase(test_name,script_name,exp_path,output_path,err_path)
                )
                test_case.add_resource(resource_path)

    def __add_exp_files(self,test_cases,script_name,test_path):
        exp_path = os.path.join(test_path, TestSuite.EXPECTED_DIR)
        # Now collect all the expected outputs for this test and store them
        # with the test case
        expected_paths = os.path.join(exp_path, '*')
        expected_files = glob.glob(expected_paths)
        expected_files.sort()
        trace("Expected paths: %s" %(expected_paths,))
        for exp_path in expected_files:
            test_name = os.path.basename(exp_path)
            type_match = TestSuite.OUTPUT_RE.match(test_name)
            if type_match==None or len(type_match.groups())!=2:
                raise RuntimeError("Unexpected file %s" % (exp_path,))
            #  test_name = script_name+"-"+m_groups[0]
            test_name = type_match.group(1)
            input_type = type_match.group(2)
            if test_name not in test_cases:
                raise RuntimeError("Expected output (%s) found with no corresponding input"
                    % (exp_path,))
            test_cases[test_name].add_exp_path(input_type, exp_path)
