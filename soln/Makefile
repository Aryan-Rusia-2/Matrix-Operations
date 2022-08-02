we5_solution: we5_test.o matrix.o
	g++ we5_test.o matrix.o -o we5_solution

we5_test.o: we5_test.cpp matrix.h
	g++ -c we5_test.cpp

matrix.o: matrix.cpp matrix.h
	g++ -c matrix.cpp

clean:
	rm: -f we5_solution matrix.o we5_test.o
	echo Cleaned 
