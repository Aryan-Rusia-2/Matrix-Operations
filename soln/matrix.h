#ifndef _MATRIX_H_
#define _MATRIX_H_
#include <iostream>

using namespace std;

class Matrix
{

public:

  // Constructors and Destructors
  Matrix(size_t num_rows, size_t num_columns, float init); // Parametrized Constructor 1 
  Matrix(size_t num_rows, size_t num_columns, float *arr_ptr); // Parametrized Constructor 2
  Matrix(const Matrix &second_matrix); // Copy Constructor

  ~Matrix(); // Defining Destructor

  // Addition, Subtraction and Multiplication
  Matrix operator+(const Matrix &second_matrix) const; // Addition
  Matrix operator-(const Matrix &second_matrix) const; // Subtraction
  Matrix operator*(const Matrix &another_matrix) const; // Multiplication

  // Bracket Operator
  float *&operator[](const size_t &index) const;

  // Negation of a matrix
  Matrix operator-() const;

  // Transpose of a matrix
  Matrix transpose();

  // ostream and istream
  friend ostream &operator<<(ostream &output, const Matrix &mat); // ostream
  friend istream &operator>>(istream &input, Matrix &mat); // istream
  

private:
  float **matrix_array; // Defining 2d array of type float
  size_t rows, columns; 

};

#endif
