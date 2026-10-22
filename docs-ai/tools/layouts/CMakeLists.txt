# SPDX-License-Identifier: GPL-2.0-only
cmake_minimum_required(VERSION 3.20)
project(PlatydocLayoutEngine LANGUAGES C CXX)

if(NOT TARGET clangFrontend)
  find_package(Clang 20.1.8 EXACT REQUIRED CONFIG)
endif()
get_target_property(LAYOUT_CLANG_IMPORTED clangFrontend IMPORTED)
if(NOT LAYOUT_CLANG_IMPORTED)
  # Clang's in-tree include_directories are scoped to its own subdirectory,
  # not inherited by a sibling LLVM external project.
  get_target_property(LAYOUT_CLANG_SOURCE clangFrontend SOURCE_DIR)
  get_target_property(LAYOUT_CLANG_BINARY clangFrontend BINARY_DIR)
  list(APPEND CLANG_INCLUDE_DIRS
    "${LAYOUT_CLANG_SOURCE}/../../include" "${LAYOUT_CLANG_BINARY}/../../include")
endif()
if(NOT LAYOUT_LLVM_REVISION)
  message(FATAL_ERROR "LAYOUT_LLVM_REVISION must identify the source revision")
endif()
add_executable(layout-engine engine.cpp)
if(LAYOUT_RUNTIME_OUTPUT_DIRECTORY)
  set_target_properties(layout-engine PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${LAYOUT_RUNTIME_OUTPUT_DIRECTORY}")
endif()
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/engine.cpp")
file(SHA256 "${CMAKE_CURRENT_SOURCE_DIR}/engine.cpp" LAYOUT_ENGINE_SOURCE_SHA256)
target_compile_features(layout-engine PRIVATE cxx_std_17)
target_compile_options(layout-engine PRIVATE -fno-rtti -fno-exceptions)
target_compile_definitions(layout-engine PRIVATE
  LAYOUT_LLVM_REVISION="${LAYOUT_LLVM_REVISION}"
  LAYOUT_ENGINE_SHA256="${LAYOUT_ENGINE_SOURCE_SHA256}")
target_include_directories(layout-engine SYSTEM PRIVATE ${LLVM_INCLUDE_DIRS} ${CLANG_INCLUDE_DIRS})
target_link_libraries(layout-engine PRIVATE clangFrontend clangAST clangBasic LLVMSupport)

if(EMSCRIPTEN)
  set_target_properties(layout-engine PROPERTIES SUFFIX ".js")
  target_compile_options(layout-engine PRIVATE -Oz)
  target_link_options(layout-engine PRIVATE
    -Oz --no-entry
    "-sMODULARIZE=1" "-sEXPORT_NAME=createLayoutEngine"
    "-sENVIRONMENT=web,node,worker" "-sFILESYSTEM=1"
    "-sALLOW_MEMORY_GROWTH=1" "-sINITIAL_MEMORY=67108864"
    "-sMAXIMUM_MEMORY=2147483648" "-sSTACK_SIZE=8388608"
    "-sEXPORTED_FUNCTIONS=['_layout_analyze','_layout_free','_malloc','_free']"
    "-sEXPORTED_RUNTIME_METHODS=['UTF8ToString','stringToUTF8','lengthBytesUTF8','HEAPU8']"
    "-sINCOMING_MODULE_JS_API=['wasmBinary','printErr','onAbort']"
    "-sEXIT_RUNTIME=0" "-sASSERTIONS=1")
endif()
