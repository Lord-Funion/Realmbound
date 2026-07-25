cmake_minimum_required(VERSION 3.16)

project(AdventureGameCpp VERSION 1.0.0 LANGUAGES CXX)

find_package(Python3 COMPONENTS Interpreter REQUIRED)

set(GENERATED_ADVENTURE_SOURCE "${CMAKE_BINARY_DIR}/generated/adventure_game_cloud.cpp")
add_custom_command(
  OUTPUT "${GENERATED_ADVENTURE_SOURCE}"
  COMMAND "${Python3_EXECUTABLE}"
          "${CMAKE_CURRENT_SOURCE_DIR}/patch_cloud_saves.py"
          "${CMAKE_CURRENT_SOURCE_DIR}/adventure_game.cpp"
          "${GENERATED_ADVENTURE_SOURCE}"
  COMMAND "${Python3_EXECUTABLE}"
          "${CMAKE_CURRENT_SOURCE_DIR}/patch_cpp_cloud_slot_names.py"
          "${GENERATED_ADVENTURE_SOURCE}"
  DEPENDS
          "${CMAKE_CURRENT_SOURCE_DIR}/adventure_game.cpp"
          "${CMAKE_CURRENT_SOURCE_DIR}/patch_cloud_saves.py"
          "${CMAKE_CURRENT_SOURCE_DIR}/patch_cpp_cloud_slot_names.py"
  COMMENT "Generating C++ cloud-save source"
  VERBATIM
)

add_executable(adventure-game "${GENERATED_ADVENTURE_SOURCE}")
target_compile_features(adventure-game PRIVATE cxx_std_17)
set_target_properties(adventure-game PROPERTIES OUTPUT_NAME "Adventure-Game")

if(MSVC)
  target_compile_options(adventure-game PRIVATE /W4)
else()
  target_compile_options(adventure-game PRIVATE -Wall -Wextra -pedantic)
endif()

if(MINGW)
  target_link_options(adventure-game PRIVATE -static -static-libgcc -static-libstdc++ -mconsole)
endif()

if(UNIX AND NOT APPLE)
  set(LINUX_LAUNCHER "${CMAKE_BINARY_DIR}/Adventure-Game-Linux.sh")
  configure_file(
    "${CMAKE_CURRENT_SOURCE_DIR}/linux-launcher.sh.in"
    "${LINUX_LAUNCHER}"
    @ONLY
    NEWLINE_STYLE UNIX
  )
  execute_process(COMMAND chmod +x "${LINUX_LAUNCHER}")

  set(LINUX_DESKTOP_FILE "${CMAKE_BINARY_DIR}/Adventure-Game.desktop")
  configure_file(
    "${CMAKE_CURRENT_SOURCE_DIR}/adventure-game.desktop.in"
    "${LINUX_DESKTOP_FILE}"
    @ONLY
    NEWLINE_STYLE UNIX
  )
  execute_process(COMMAND chmod +x "${LINUX_DESKTOP_FILE}")
endif()
