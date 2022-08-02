/*

Name:  Aryan Rusia

-------------------------------------------

*/

#include <iostream>
#include <cassert>
#include "matrix.h" // added the header file 'maatrix.h'
using namespace std;

// First Parametrized Constructor as given in the description of 'MATRIX CLASS' pdf.
Matrix::Matrix(size_t total_rows, size_t total_colums, float init)
{
    this->rows = total_rows;
    this->columns = total_colums;

    matrix_array = new float *[rows];

    for (size_t r = 0; r < rows; r++)
    {
        matrix_array[r] = new float[columns];
    }

    size_t r = 0;

    while (r < rows)
    {
        size_t c = 0;
        while (c < columns)
        {
            matrix_array[r][c] = init;
            c++;
        }
        r++;
    }
}

// Second Parametrized Constructor as given in the description of 'MATRIX CLASS' pdf.
Matrix::Matrix(size_t total_rows, size_t total_colums, float *arr_ptr)
{
    this->rows = total_rows;
    this->columns = total_colums;
    matrix_array = new float *[rows];

    for (int r = 0; r < rows; r++)
    {
        matrix_array[r] = new float[columns];
    }

    int r = 0;
    while (r < rows)
    {
        int c = 0;

        while (c < columns)
        {
            matrix_array[r][c] = arr_ptr[c + (r * columns)];
            c++;
        }
        r++;
    }
}

// The snippet of code below is of copy constructor
Matrix::Matrix(const Matrix &second_matrix)
{
    this->columns = second_matrix.columns;
    this->rows = second_matrix.rows;
    this->matrix_array = new float *[second_matrix.rows];

    assert(this->matrix_array);

    for (int r = 0; r < second_matrix.rows; r++)
    {
        this->matrix_array[r] = new float[second_matrix.columns];
        assert(this->matrix_array[r]);
    }

    int r = 0;

    while (r < second_matrix.rows)
    {
        int c = 0;
        while (c < second_matrix.columns)
        {
            this->matrix_array[r][c] = second_matrix[r][c];
            c++;
        }
        r++;
    }
}

// The following snippet of code is for Destructor
Matrix::~Matrix()
{
    for (int r = 0; r < rows; r++)
    {
        delete[] matrix_array[r];
    }

    delete[] matrix_array;
}

// Addition of two matrix
Matrix Matrix::operator+(const Matrix &second_matrix) const
{
    Matrix added_array(rows, columns, 0.0);

    int c = 0;
    while (c < columns)
    {
        int r = 0;
        while (r < rows)
        {
            added_array.matrix_array[r][c] = matrix_array[r][c] + second_matrix.matrix_array[r][c];
            r++;
        }
        c++;
    }

    return added_array;
}

// The following snippet of code is for Matrix Subtraction
Matrix Matrix::operator-(const Matrix &second_matrix) const
{
    Matrix subtracted_matrix(rows, columns, 0.0);
    int r = 0;

    while (r < rows)
    {
        int c = 0;
        while (c < columns)
        {
            subtracted_matrix.matrix_array[r][c] = matrix_array[r][c] - second_matrix.matrix_array[r][c];
            c++;
        }
        r++;
    }

    return subtracted_matrix;
}

// THe following snippet of code is for matrix multiplication
Matrix Matrix::operator*(const Matrix &another_matrix) const
{
    Matrix multiply_array(rows, another_matrix.columns, 0.0);

    int r = 0;

    while (r < rows)
    {
        int c = 0;

        while (c < another_matrix.columns)
        {
            int a = 0;

            while (a < another_matrix.rows)
            {
                multiply_array.matrix_array[r][c] += this->matrix_array[r][a] * another_matrix.matrix_array[a][c];
                a++;
            }
            c++;
        }

        r++;
    }

    return multiply_array;
}

// The given snippet of code is for Negation, performed it using operator overloading
Matrix Matrix::operator-() const
{
    Matrix negation_matrix(rows, columns, 0.0);
    int c = 0;

    while (c < columns)
    {
        int r = 0;
        while (r < rows)
        {
            negation_matrix.matrix_array[r][c] = -1 * matrix_array[r][c];
            r++;
        }
        c++;
    }

    return negation_matrix;
}

// The following snippet of code finds the transpose of any given matrix
Matrix Matrix::transpose()
{
    Matrix transpose_matrix(columns, rows, 0.0);
    int c = 0;

    while (c < columns)
    {
        int r = 0;
        while (r < rows)
        {
            transpose_matrix.matrix_array[c][r] = matrix_array[r][c];
            r++;
        }

        c++;
    }
    return transpose_matrix;
}

// The snippet of code below is of Bracket operator
float *&Matrix::operator[](const size_t &index) const
{
    return matrix_array[index];
}

// The snippet of code below is of ostream
ostream &operator<<(ostream &output, const Matrix &mat)
{
    int r = 0;
    int matrix_row = mat.rows;
    int matrix_column = mat.columns;

    while (r < matrix_row)
    {
        int c = 0;
        while (c < matrix_column)
        {
            output << mat.matrix_array[r][c];
            if (c != matrix_column - 1)
            {
                output << " ";
            }
            c++;
        }

        if (r != matrix_row - 1)
        {
            output << endl;
        }

        r++;
    }
    return output;
}

// The snippet of code below is of istream
istream &operator>>(istream &input, Matrix &mat)
{
    int r = 0;
    int matrix_row = mat.rows;
    int matrix_column = mat.columns;

    while (r < matrix_row)
    {
        int c = 0;
        while (c < matrix_column)
        {
            input >> mat.matrix_array[r][c];
            c++;
        }
        r++;
    }

    return input;
}
