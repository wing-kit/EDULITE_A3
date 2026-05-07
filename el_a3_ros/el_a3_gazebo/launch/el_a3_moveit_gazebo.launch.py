"""
Launch EL-A3 Gazebo simulation with MoveIt2 connected to Gazebo controllers.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare
import yaml


def load_yaml(package_name, file_path):
    package_path = get_package_share_directory(package_name)
    absolute_file_path = os.path.join(package_path, file_path)
    try:
        with open(absolute_file_path, "r") as file:
            return yaml.safe_load(file)
    except EnvironmentError:
        return None


def generate_launch_description():
    launch_gazebo = LaunchConfiguration("launch_gazebo")
    use_sim_time = LaunchConfiguration("use_sim_time")
    use_rviz = LaunchConfiguration("use_rviz")
    gui = LaunchConfiguration("gui")
    pause = LaunchConfiguration("pause")
    verbose = LaunchConfiguration("verbose")
    world = LaunchConfiguration("world")
    wrist_motor_type = LaunchConfiguration("wrist_motor_type")

    gazebo_pkg = FindPackageShare("el_a3_gazebo")
    description_pkg = FindPackageShare("el_a3_description")
    moveit_pkg = FindPackageShare("el_a3_moveit_config")

    default_world = PathJoinSubstitution([gazebo_pkg, "worlds", "el_a3_empty.world"])
    controllers_file = PathJoinSubstitution(
        [gazebo_pkg, "config", "el_a3_gazebo_controllers.yaml"]
    )

    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution([description_pkg, "urdf", "el_a3.urdf.xacro"]),
            " use_gazebo:=true",
            " gazebo_ros2_control_params:=",
            controllers_file,
            " mesh_prefix:=file://",
            PathJoinSubstitution([description_pkg, "meshes"]),
            "/",
            " wrist_motor_type:=",
            wrist_motor_type,
        ]
    )
    robot_description = {
        "robot_description": ParameterValue(robot_description_content, value_type=str)
    }

    robot_description_semantic_content = Command(
        ["cat ", PathJoinSubstitution([moveit_pkg, "config", "el_a3.srdf"])]
    )
    robot_description_semantic = {
        "robot_description_semantic": ParameterValue(
            robot_description_semantic_content, value_type=str
        )
    }

    kinematics_yaml = load_yaml("el_a3_moveit_config", "config/kinematics.yaml")
    joint_limits_yaml = load_yaml("el_a3_moveit_config", "config/joint_limits.yaml")
    ompl_planning_yaml = load_yaml("el_a3_moveit_config", "config/ompl_planning.yaml")
    moveit_controllers_yaml = load_yaml(
        "el_a3_moveit_config", "config/moveit_controllers.yaml"
    )

    robot_description_planning = {"robot_description_planning": joint_limits_yaml}
    ompl_planning_pipeline_config = {"move_group": ompl_planning_yaml}
    trajectory_execution = {
        "moveit_manage_controllers": False,
        "trajectory_execution.allowed_execution_duration_scaling": 2.0,
        "trajectory_execution.allowed_goal_duration_margin": 1.0,
        "trajectory_execution.allowed_start_tolerance": 0.05,
    }
    planning_scene_monitor_parameters = {
        "publish_planning_scene": True,
        "publish_geometry_updates": True,
        "publish_state_updates": True,
        "publish_transforms_updates": True,
        "publish_planning_scene_hz": 4.0,
    }

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [gazebo_pkg, "/launch", "/el_a3_gazebo.launch.py"]
        ),
        launch_arguments={
            "gui": gui,
            "pause": pause,
            "verbose": verbose,
            "world": world,
            "use_rviz": "false",
            "use_sim_time": use_sim_time,
            "wrist_motor_type": wrist_motor_type,
        }.items(),
        condition=IfCondition(launch_gazebo),
    )

    static_tf_node = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        arguments=["0", "0", "0", "0", "0", "0", "world", "base_link"],
        output="log",
    )

    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            robot_description,
            robot_description_semantic,
            robot_description_planning,
            kinematics_yaml,
            ompl_planning_pipeline_config,
            trajectory_execution,
            moveit_controllers_yaml,
            planning_scene_monitor_parameters,
            {"use_sim_time": use_sim_time},
        ],
    )

    robot_description_kinematics = {"robot_description_kinematics": kinematics_yaml}
    rviz_config_file = PathJoinSubstitution([moveit_pkg, "config", "moveit.rviz"])
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config_file],
        parameters=[
            robot_description,
            robot_description_semantic,
            robot_description_planning,
            robot_description_kinematics,
            {"use_sim_time": use_sim_time},
        ],
        condition=IfCondition(use_rviz),
    )

    delayed_moveit = TimerAction(period=6.0, actions=[move_group_node, rviz_node])

    declared_arguments = [
        DeclareLaunchArgument(
            "launch_gazebo",
            default_value="true",
            description="Start Gazebo before MoveIt. Set false if Gazebo is already running.",
        ),
        DeclareLaunchArgument(
            "world",
            default_value=default_world,
            description="Gazebo world file.",
        ),
        DeclareLaunchArgument(
            "gui",
            default_value="true",
            description="Start Gazebo client.",
        ),
        DeclareLaunchArgument(
            "pause",
            default_value="false",
            description="Start Gazebo paused.",
        ),
        DeclareLaunchArgument(
            "verbose",
            default_value="false",
            description="Print verbose Gazebo output.",
        ),
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="true",
            description="Use simulation clock.",
        ),
        DeclareLaunchArgument(
            "use_rviz",
            default_value="true",
            description="Start RViz with the MoveIt plugin.",
        ),
        DeclareLaunchArgument(
            "wrist_motor_type",
            default_value="EL05",
            description="Wrist motor type for joints 4-7: EL05 or RS05.",
        ),
    ]

    return LaunchDescription(
        declared_arguments
        + [
            gazebo,
            static_tf_node,
            delayed_moveit,
        ]
    )
