#pragma once

#include <cstdint>

namespace ffi {
    extern "C"
    {
        /**
         * @brief Compile the expression into an executable.
         * @param input The expression to compile.
         * @param code_integrity The integrity of the code.
         * @param code_integrity_size Buffer size for the integrity of the code.
         * @param output_error The buffer to write the error message to.
         * @param output_error_len The length of the buffer.
         * @return The compiled executable.
         */
        [[nodiscard]] void* compile_expression(const char* input,
                                               char* code_integrity,
                                               std::size_t code_integrity_size,
                                               char* output_error,
                                               std::size_t output_error_len);

        /**
         * @brief Evaluate the expression with the given variables.
         * @param exe The executable to evaluate.
         * @param keys_ptr The keys of the variables.
         * @param values_ptr The values of the variables.
         * @param variables_len The number of variables.
         * @param output_error The buffer to write the error message to.
         * @param output_error_len The length of the buffer.
         * @return The result of the expression.
         */
        int64_t evaluate_expression(void* exe,
                                    const char* const keys_ptr[],
                                    const int64_t* values_ptr,
                                    std::size_t variables_len,
                                    char* output_error,
                                    std::size_t output_error_len);

        /**
         * @brief Free the executable.
         * @param exe The executable to free.
         */
        void free_executable(void* exe);
    }
}