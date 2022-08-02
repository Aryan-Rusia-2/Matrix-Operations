######################################################################
#   File: diffs.py
#
#   Description: Compares the actual and expected files and returns
#       any differences found. These are used to determine if a test
#       has passed or failed and to prepare quick difference output.
#
#   NOTE: YOU CAN SET A "FUZZ LEVEL" which will allow a test case to
#         pass if it has fewer than X errors (where X is the fuzz level)
#         This is set to 0 by default.
#
#   Included functions:
#       - diff(), clean_data(), get_hardtest_diff(), 
#         get_softtest_diff()
#
######################################################################

import difflib  # tool used to generate quick difference output
import re       

def diff(actual,expected,is_text_exp,visible_diff):
    '''Compares actual and expected and returns differences.

        When expected parameter is text (is_text_exp==True) then
        runs two comparisons (soft-test and hard-test) and returns a pair: 

        In the soft-test, whitespace differences are completely
        ignored (whitespaces are stripped before the comparison is made), while
        in the hard-test whitespace differences are taken into account.
        The 1st component of the returned pair is the outcome of the soft-test,
        while the 2nd component is the outcome of the hard-test.

        When visible_diff==True, whitespaces are replaced by '#'
        when computing the soft-test diff.

        When the expected parameter is binary, byte-by-byte comparison
        is used and the pair (actual,None) is returned if differences
        are detected. 

        Arguments: 
            actual (str): the student's output
            expected (str): what is expected as the correct answer
            is_text_exp (bool): text flag (if true, expect text, else expect binary)      
            visible_diff (bool): determines whether or not to replace spaces with # characters
                          to make differences visible

        Returns:
            A tuple of (incorrect output diffs, whitespace diffs)
    '''

    softtest_diffs = None       # initialize to None
    hardtest_diffs = None

    if is_text_exp:
        # determine if there are softtest differences
        softtest_diffs = get_softtest_diff(expected, actual)

        if not softtest_diffs:

            if visible_diff:  # show a visible diff by replacing spaces with #
                expected = clean_data(expected, r'[\s\n]', '#', True)
                actual = clean_data(actual, r'[\s\n]', '#', True)

            # determine if there are whitespace differences
            hardtest_diffs = get_hardtest_diff(expected,actual)

        else:
            softtest_diffs = get_hardtest_diff(expected,actual)

    elif actual!=expected: # binary diff is byte by byte comparison
            softtest_diffs = actual

    return (softtest_diffs,hardtest_diffs)

def clean_data(data, patt, repl, hard_test=False):
    '''Replaces the given pattern throughout the data
       and returns the result.
       
       Arguments:
            data (list): A list of strings
            patt (str): the string that should be replaced
            repl (str): the string to replace the pattern.
            hard_test (bool): True if this is a hard_test

       This function is used to replace the pattern of spaces 
       with strings (hashtags) if visible_diff is true.
    '''
    cleaned = [] 

    # "clean" each line by replacing (in this case) any space
    # character with a hashtag 
    for line in data:

        # remove lines that only contain whitespace when
        # checking for soft_test difference
        if not hard_test:
            line = line.strip()
            if not line:
                continue

        end = '\n'
        stripped_line = re.sub(patt, repl, line) + end

        if len(stripped_line) > 0:
            cleaned.append(stripped_line)

    return cleaned


def get_hardtest_diff(expected, actual, fuzz_level=0):
    """Finds all differences between expected and actual,
    including whitespace differences.

    Line by line comparison of two lists of strings.
    Returns a list of the lines where differences were found.
    Prefix of differences:
    '- ': lines missing from actual
    '+ ': extra lines in actual
    '  ': lines common to both actual and expected

    Arguments:
        actual (str): the student's output
        expected (str): what is expected as the correct answer
        fuzz_level: the number of allowable differences before 
                    they are considered significant.

    Returns:
        diff_result (list): the quick difference output showing differences
        or
        []: if a non-significant number of errors were found
    """   
    diff_engine = difflib.Differ()
    diff_result = list(diff_engine.compare(expected, actual))

    # print("HERE")
    count = 0
    found_diff = False
    for line in diff_result:
        if line[0] == '+' or line[0] == '-':
            count += 1

            # if line.strip() == '+' or line.strip() == "-":
                # print("NEWLINE")

            if count >= fuzz_level:
                found_diff = True
                break
    if found_diff:
        return diff_result
    return []



def get_softtest_diff(expected, actual, fuzz_level=0):
    """ Same as get_hardtest_diff(), but before comparison all
    whitespace is stripped from the expected and actual data.

    Arguments:
        actual (str): the student's output
        expected (str): what is expected as the correct answer
        fuzz_level: the number of allowable differences before 
                    they are considered significant.
    """
    stripped_one = clean_data(expected, r'\s+', '')
    stripped_two = clean_data(actual, r'\s+', '')
    return get_hardtest_diff(stripped_one, stripped_two, fuzz_level)
