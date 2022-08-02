######################################################################
#   File: testcenter.py
#
#   Description:
#       Seems to be a command-line parser that runs tests alongside a
#       marking script (but in the current implementation there is
#       no use for it).
#
#   Included functions:
#       - main()
#
######################################################################

#!/usr/bin/env python3

import argparse
import TestSuite
import logging
import os
logging.basicConfig(level=logging.DEBUG)
# logging.basicConfig(level=logging.WARNING)

# @todo: Test generation

# Version 1.2
''' The marking script is intended for three primary use-cases, 1) To allow
students to run their program against some inputs, and compare their results
to the expected outputs. 2) To allow graders to run student submissions against
a larger set of testcases and see the differences. And 3) to allow graders to
easily generate a set of test cases

To run this script as a student simple create the appropriate zipfile as you
would for submission, and place it in the same directory as marking.pl

TODO: There are still some improvements yet to be made to the marking script.
1) Report missing/extra output files as errors.
2) Maybe --generate should re-generate results even when other results already
exist. Though this should probably be double protected with a --overwrite flag
AND a confirmation to avoid students screwing up their test dirs.
3) Run pep8 on the code and do some processing on the results
'''


def main():
    # default directory for the tests: the current working directory
    # @todo: test these
    cwd = os.path.abspath(os.getcwd())
    # default script file path: in the parent directory a zip file
    # whose basename is identical to the basename of the current working
    # directory
    script_source = cwd + "../" + os.path.basename(cwd) + ".zip"

    # for testing:
    cwd = '/Users/csaba/Dropbox/Public/CMPUT-174-2012-Fall/assignments/as-174-2-marking-basic'
    script_source = '/Users/csaba/Dropbox/Public/CMPUT-174-2012-Fall/assignments/as-174-2'

    parser = argparse.ArgumentParser(
        description='Run tests against a submission file.'
        #            , epilog='''aaa'''
    )
    parser.add_argument(
        '--submission',
        '-s',
        default=script_source,
        help='Scripts to be tested again (zip or dir)')
    parser.add_argument(
        '--test_directory',
        '-t',
        default=cwd,
        help='Directory containing the tests (defaults to current)')
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='show the detailed outcome of the tests')
    parser.add_argument(
        '--visible_space_diff',
        '-p',
        action='store_true',
        help='show the results of the diff')
    parser.add_argument('--timeout', type=int,default=200
                       ,  help='Terminate the script with an error after the '\
                               'timeout has passed')
    parser.add_argument(
        '--generate',
        '-g',
        action='store_true',
        help='generates expected outputs')
    #    parser.add_argument('--pep8', action='store_true'
    #                       , help='Run pep8 on the source files')
    parser.add_argument(
        '--stop_early',
        '-e', 
        action='store_true',
        help='stop running test cases after first failure')
    parser.add_argument('--wait_on_exit', '-w', action='store_true'
                       , help='Exit on finish instead of pausing and waiting '\
                              'for the user')
    parser.add_argument(
        '--verify_script_dir',
        action='store_true',
        help='Verify whether the script directory is correctly formatted')
    parser.add_argument(
        '--python_only', action='store_true', help='Allow python only')
    args = parser.parse_args()

    testcase_source = os.path.abspath(os.getcwd())
    if args.test_directory:
        testcase_source = args.test_directory
    try:
        any_language = not args.python_only
        print("Creating test suite")
        test_suite = TestSuite.TestSuite(testcase_source, any_language)
        print("Collecting script-tests")
        test_suite.collect_tests(create_missing_dirs=False)
        print("Collected %s script-tests" % len(test_suite.test_cases))

        print("Verifying submission files")
        script_source = args.submission
        script_dir = TestSuite.prep_submission(
            script_source, test_suite.assignment_name, args.verify_script_dir)

        print("Running tests")
        test_suite.run_tests(
            script_dir,
            timeout=args.timeout,
            gen_res=args.generate,
            visible_space_diff=args.visible_space_diff,
            verbose=args.verbose,
            stop_early=args.stop_early)
        summary = test_suite.get_summary()
        print(
            "Number of tests: %s Errors: %s Serious failures: %s All failures: %s"
            % summary)
        # report the results

        if args.wait_on_exit:
            input("Press <Enter> to exit")
    except RuntimeError as err:
        print("Error:\n" + str(err))


if __name__ == "__main__":
    main()
