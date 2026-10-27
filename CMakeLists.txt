cmake_minimum_required(VERSION 3.18)
project(gcc_dev_meta LANGUAGES NONE)

enable_testing()
find_program(MAKE_EXECUTABLE NAMES gmake make REQUIRED)
# Keep the Makefile as the authority for repository metadata checks.
add_test(NAME check-meta
    COMMAND "${MAKE_EXECUTABLE}" -C "${CMAKE_CURRENT_SOURCE_DIR}" check-meta)
