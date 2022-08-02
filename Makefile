run:
	chmod u+x soln/.build/build.sh
	bash setup.sh
	python3 TestCenter-master/testcenter.py -s soln -t test-cases -e --timeout 5
all:
	chmod u+x soln/.build/build.sh
	bash setup.sh
	python3 TestCenter-master/testcenter.py -s soln -t test-cases --timeout 5
verbose:
	chmod u+x soln/.build/build.sh
	bash setup.sh
	python3 TestCenter-master/testcenter.py -s soln -t test-cases -e -v --timeout 5
all-verbose:
	chmod u+x soln/.build/build.sh
	bash setup.sh
	python3 TestCenter-master/testcenter.py -s soln -t test-cases -v --timeout 5
validate:
	python3 submission_validator.py
