#!/bin/bash

#
# Checks a collection of morning problem submissions, sorting the submissions
# by pass/fail.
#
# To use, download all student submissions from e-class and extract to a 
# folder, along with the test-cases. As an example:
#
#   slimes/
#     Student_A_slimes.py
#     Student_B_slimes.py
#     Student_C_slimes.py
#     ... etc.
#     test-cases/
#       as-275-9-slimes.py-test/
#         ... etc.
#
# If a student submitted a .zip, extract it and rename the .py file to 
# something meaningful.
# 
# Place this script in the TestCentre directory, and run it:
#
#   $> ./run-tests.sh ../path/to/slimes/ slimes.py
#
# This will test all .py files in slimes/, renaming them to slimes.py first,
# and will test them against the data in slimes/test-cases/. Two new folders
# will be created: slimes/passed/ and slimes/failed/. If a submission 
# passes/fails, it will be copied into the appropriate folder.
#

# Uncomment to debug this script.
#set -o xtrace

if [[ $# < 2 ]] || [[ $1 == "--help" ]] ; then
  echo "Usage: $0 [directory] [py-name] {OPT-submission-to-run.py}"
  echo ""
  echo "  directory - a folder containing all student .py files downloaded from eclass,"
  echo "              as well as a test-cases/ folder containing the TestCenter input"
  echo "  py-name   - the problem's python filename; e.g. songs.py"
  echo "  OPT-submission-to-run"
  echo "            - optional; if omitted all assignments in directory are graded, and"
  echo "              the submissions are sorted into passed/ and failed/ directories;"
  echo "              if provided only the given student's assignment is tested, and the"
  echo "              result is printed to the terminal"
  echo ""
  echo "This script MUST be run from the TestCenter directory."
  exit 1
fi

if [ ! -e testcenter.py ] ; then
  echo "Please run this from the TestCenter directory."
  exit 1
fi

srcdir=$1
pyname=$2
file=$3
have_file=$(( $# >= 3 ? 1 : 0 ))

echo "-----------------------------------------------------------"
if [[ $have_file == 0 ]] ; then
  echo "Batch testing ..."
else
  echo "Testing single file ..."
fi

# Timeout for running ALL test cases. This should be sufficient for all
# reasonable solutions.
maxtime="120s"

# How many test cases are there?
test_case_dir="test-cases"
num_tests=$( ls -1 $srcdir/$test_case_dir/*/Inputs/ | wc -l )
echo "# of tests found = $num_tests"

# If bulk-marking, then create the output directories.
if [[ $have_file == 0 ]] ; then
  if [ -d "$srcdir/passed" ] ; then rm -R "$srcdir/passed"; fi
  if [ -d "$srcdir/failed" ] ; then rm -R "$srcdir/failed"; fi
  mkdir "$srcdir/passed"
  mkdir "$srcdir/failed"
fi

# Prepare the temporary marking directory.
if [ -d tmp ] ; then rm -R tmp; fi
mkdir tmp
cp -fR "$srcdir/$test_case_dir" tmp/
#if [ "$test_case_dir" != "test-cases" ] ; then
#  mv "tmp/$test_case_dir" tmp/test-cases
#fi

# Runs the tests on $file.
function run_test() {
  echo $file
  cp -f "$file" "tmp/$pyname"
  cp -f $srcdir/*.sh "tmp/" # for cpp files
  timeout $maxtime python3 testcenter.py -t tmp/test-cases -s tmp/ 2> /dev/null | grep 'Number of tests' > tmp/result
  failed=$?
  #echo "errcode = $failed"
  if [[ $failed == 0 ]] ; then
    if [[ "$(cat tmp/result)" == "Number of tests: $num_tests Errors: 0 Serious failures: 0"* ]] ; then
      echo "Passed"
      if [[ $have_file == 0 ]] ; then cp "$file" "$srcdir/passed/"; fi
    else
      echo "Failed - incorrect output"
      if [[ $have_file == 0 ]] ; then cp "$file" "$srcdir/failed/"; fi
    fi
  else
    echo "Failed - timeout ($maxtime)"
    if [[ $have_file == 0 ]] ; then cp "$file" "$srcdir/failed/"; fi
  fi
}

# Bulk-mark.
if [[ $have_file == 0 ]] ; then
  for file in $srcdir/*.py ; do
  # for file in $srcdir/*.cpp ; do # for cpp files
    run_test
  done
# Single-mark.
else
  run_test
fi

exit 0
