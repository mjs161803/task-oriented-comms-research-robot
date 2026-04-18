cmake_minimum_required(VERSION 3.8)
project(turtlebot_simulation)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)

# Generate custom messages
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/SensorsAggregated.msg"
  DEPENDENCIES std_msgs sensor_msgs
)

# Install launch files, worlds, config files, and models
install(DIRECTORY
  launch
  worlds
  config
  urdf
  DESTINATION share/${PROJECT_NAME}/
)

# Install scripts
install(PROGRAMS
  scripts/block_observer.py
  scripts/episode_manager.py
  scripts/local_perception.py
  DESTINATION lib/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
