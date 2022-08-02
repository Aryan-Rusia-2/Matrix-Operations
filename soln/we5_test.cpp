#include <iostream>
#include <string>
#include <unordered_map>
#include <vector>
#include <cassert>
#include "matrix.h"

using namespace std;

// Check if a matrix with given name exists in the map
bool matExist(unordered_map<string, int> mat_map, string mat_name) {
  if (mat_map.find(mat_name) != mat_map.end()) {
    return true;
  } else {
    return false;
  }
}

// Instruction Table:
// C: Create a matrix
// A: Matrix addition
// S: Matrix subtraction
// M: Matrix multiplication
// N: Unary negation
// T: Transpose matrix
// P: Print matrix
// R: Read matrix
// B: Bracket operator
// BA: Assign new value using bracket operator
// D: Make a deep copy of a matrix
// Q: Exit
int main() {
  // Map matrix name and index in the vector.
  // Key: name of matrix; Val: id/counter apprears in the vector
  unordered_map<string, int> mat_map;

  vector<Matrix> mat_list;  // Store matrices
  vector<bool> const_list;  // Set true if a matrix is declared as const

  int counter = 0;

  while (true) {
    // Get instruction
    string ins;
    cin >> ins;
    if (ins == "C") {
      // Test matrix constructors
      // Usage: C [mat_name] [row] [col] (-c) -i [init] / -a [arr_ptr]
      // -c: const flag (optional), use to create const matrix
      // -i: initialization flag: initialize with an init value
      // -a: initialization flag: initialize with array pointer
      // Example (non-const):
      // C my_mat 2 3 -i 1.0 -> Matrix(2, 3, 1.0)
      // C my_mat 2 3 -a 1.0 2.0 3.0 4.0 5.0 6.0
      // -> Matrix(2, 3, arr_ptr), arr_ptr = [1.0 2.0 3.0 4.0 5.0 6.0]
      // Exmaple (const):
      // C my_mat 2 3 -c -i 1.0 -> const Matrix(2, 3, 1.0)
      // C my_mat 2 3 -c -a 1.0 2.0 3.0 4.0 5.0 6.0
      // -> const Matrix(2, 3, arr_ptr), arr_ptr = [1.0 2.0 3.0 4.0 5.0 6.0]
      string mat_name;
      string flag;
      size_t row, col;
      cin >> mat_name >> row >> col >> flag;
      if (flag == "-i") {
        // Create with an initial value
        float init;
        cin >> init;
        Matrix tmp_mat = Matrix(row, col, init);
        mat_list.push_back(tmp_mat);
        const_list.push_back(false);
        mat_map.emplace(mat_name, counter++);
      } else if (flag == "-a") {
        // Create with the array pointer
        int arr_size = row*col;
        float * arr_pointer = new float[arr_size];
        for (int i = 0; i < arr_size; i++) {
          cin >> arr_pointer[i];
        }
        Matrix tmp_mat = Matrix(row, col, arr_pointer);
        delete [] arr_pointer;
        mat_list.push_back(tmp_mat);
        const_list.push_back(false);
        mat_map.emplace(mat_name, counter++);
      } else if (flag == "-c") {
        // Create const matrix
        string sub_flag;
        cin >> sub_flag;
        if (sub_flag == "-i") {
          // Create with an initial value
          float init;
          cin >> init;
          const Matrix const_tmp_mat = Matrix(row, col, init);
          Matrix tmp_mat = const_tmp_mat;  // store as non-const
          mat_list.push_back(tmp_mat);
          const_list.push_back(true);  // set true if declared as const
          mat_map.emplace(mat_name, counter++);
        } else if (sub_flag == "-a") {
          // Create with the array pointer
          int arr_size = row*col;
          float * arr_pointer = new float[arr_size];
          for (int i = 0; i < arr_size; i++) {
            cin >> arr_pointer[i];
          }
          const Matrix const_tmp_mat = Matrix(row, col, arr_pointer);
          delete [] arr_pointer;
          Matrix tmp_mat = const_tmp_mat;  // store as non-const
          mat_list.push_back(tmp_mat);
          const_list.push_back(true);  // set true if declared as const
          mat_map.emplace(mat_name, counter++);
        }
      } else {
        cout << "ERROR: Invalid constructor flag!" << endl;
        return 0;
      }
      continue;
    } else if (ins == "A") {
      // Test matrix addition
      // Usage: A [mat_name1] [mat_name2] [res_name]
      // res_name: a string to store the results for future use
      // Example: A my_mat1 my_mat2 result -> result = my_mat1 + my_mat2
      string mat_name_A, mat_name_B, mat_name_res;
      cin >> mat_name_A >> mat_name_B >> mat_name_res;
      if (matExist(mat_map, mat_name_A) && matExist(mat_map, mat_name_B)) {
        mat_list.push_back(mat_list[mat_map[mat_name_A]] + mat_list[mat_map[mat_name_B]]);
        const_list.push_back(false);
        mat_map.emplace(mat_name_res, counter++);
      } else {
        cout << "ERROR: Matrix not found!" << endl;
      }
      continue;
    } else if (ins == "S") {
      // Test matrix subtraction
      // Usage: S [mat_name1] [mat_name2] [res_name]
      // res_name: a string to store the results for future use
      // Example: S my_mat1 my_mat2 result -> result = my_mat1 - my_mat2
      string mat_name_A, mat_name_B, mat_name_res;
      cin >> mat_name_A >> mat_name_B >> mat_name_res;
      if (matExist(mat_map, mat_name_A) && matExist(mat_map, mat_name_B)) {
        mat_list.push_back(mat_list[mat_map[mat_name_A]] - mat_list[mat_map[mat_name_B]]);
        const_list.push_back(false);
        mat_map.emplace(mat_name_res, counter++);
      } else {
        cout << "ERROR: Matrix not found!" << endl;
      }
      continue;
    } else if (ins == "M") {
      // Test matrix multiplication
      // Usage: M [mat_name1] [mat_name2] [res_name]
      // res_name: a string to store the results for future use
      // Example: M my_mat1 my_mat2 result -> result = my_mat1 * my_mat2
      string mat_name_A, mat_name_B, mat_name_res;
      cin >> mat_name_A >> mat_name_B >> mat_name_res;
      if (matExist(mat_map, mat_name_A) && matExist(mat_map, mat_name_B)) {
        mat_list.push_back(mat_list[mat_map[mat_name_A]] * mat_list[mat_map[mat_name_B]]);
        const_list.push_back(false);
        mat_map.emplace(mat_name_res, counter++);
      } else {
        cout << "ERROR: Matrix not found!" << endl;
      }
      continue;
    } else if (ins == "N") {
      // Test unary negation
      // Usage: N [mat_name] [res_name]
      // Example: N my_mat result -> result = -my_mat
      string mat_name, mat_name_res;
      cin >> mat_name >> mat_name_res;
      if (matExist(mat_map, mat_name)) {
        mat_list.push_back(-mat_list[mat_map[mat_name]]);
        const_list.push_back(false);
        mat_map.emplace(mat_name_res, counter++);
      } else {
        cout << "ERROR: Matrix " << mat_name << " not found!" << endl;
      }
      continue;
    } else if (ins == "T") {
      // Test matrix transpose
      // Usage: T [mat_name] [res_name]
      // Example: T my_mat result -> result = my_mat.transpose()
      string mat_name, mat_name_res;
      cin >> mat_name >> mat_name_res;
      if (matExist(mat_map, mat_name)) {
        mat_list.push_back(mat_list[mat_map[mat_name]].transpose());
        const_list.push_back(false);
        mat_map.emplace(mat_name_res, counter++);
    } else {
        cout << "ERROR: Matrix " << mat_name << " not found!" << endl;
      }
      continue;
    } else if (ins == "B") {
      // Test bracket operator
      // Usage: B [mat_name] [row] [col]
      // Example: B my_mat 2 3 -> my_mat[2][3]
      string mat_name;
      size_t row, col;
      cin >> mat_name >> row >> col;
      if (matExist(mat_map, mat_name)) {
        cout << mat_list[mat_map[mat_name]][row][col] << endl;
      } else {
        cout << "ERROR: Matrix " << mat_name << " not found!" << endl;
      }
      continue;
    } else if (ins == "BA") {
      // Test bracket operator + assign value to non-const
      // Example: BA my_mat 2 3 1.0 -> my_mat[2][3] = 1.0
      // We don't test the BA command with a const matrix,
      // so all matrices are stored in a vector as non-const.
      string mat_name;
      size_t row, col;
      float val;
      cin >> mat_name >> row >> col >> val;
      if (matExist(mat_map, mat_name)) {
        if (const_list[mat_map[mat_name]]) {
          // We don't test the BA command with a const matrix
          assert(false);
        } else {
          mat_list[mat_map[mat_name]][row][col] = val;
        }
      } else {
        cout << "ERROR: Matrix " << mat_name << " not found!" << endl;
      }
      continue;
    } else if (ins == "P") {
      // Test insertion operator: print the given matrix
      // Usage: P [mat_name] -> cout << mat_name << endl;
      string mat_name;
      cin >> mat_name;
      if (matExist(mat_map, mat_name)) {
        cout << mat_list[mat_map[mat_name]] << endl;
      } else {
        cout << "ERROR: Matrix " << mat_name << " not found!" << endl;
      }
      continue;
    } else if (ins == "R") {
      // Test extraction operator: operating on an existing matrix
      // Usage: R [mat_name] [arr_ptr] -> cin >> my_mat;
      // Example: R my_mat 1 2 3 4 5 6
      string mat_name;
      cin >> mat_name;
      if (matExist(mat_map, mat_name)) {
        if (const_list[mat_map[mat_name]]) {
          // We don't test the R command with a const matrix
          assert(false);
        } else {
          cin >> mat_list[mat_map[mat_name]];
        }
      } else {
        cout << "ERROR: Matrix " << mat_name << " not found!" << endl;
      }
      continue;
    } else if (ins == "D") {
      // Test copy constructor: creating a deep copy of an existing matrix
      // Usage: D [mat_name] [new_mat_name]
      // Example: D my_mat result -> Matrix result = my_mat
      string mat_name, mat_name_res;
      cin >> mat_name >> mat_name_res;
      if (matExist(mat_map, mat_name)) {
        Matrix res = mat_list[mat_map[mat_name]];
        mat_list.push_back(res);
        const_list.push_back(false);
        mat_map.emplace(mat_name_res, counter++);
      } else {
        cout << "ERROR: Matrix " << mat_name << " not found!" << endl;
      }
      continue;
    } else if (ins == "Q") {
      // Exit program
      break;
    }
  }
  return 0;
}
