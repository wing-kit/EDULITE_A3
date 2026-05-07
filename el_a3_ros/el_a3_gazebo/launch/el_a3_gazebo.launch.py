"""
Launch EL-A3 in Gazebo Classic with gazebo_ros2_control.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler, TimerAction
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")
    use_rviz = LaunchConfiguration("use_rviz")
    gui = LaunchConfiguration("gui")
    pause = LaunchConfiguration("pause")
    verbose = LaunchConfiguration("verbose")
    world = LaunchConfiguration("world")
    entity_name = LaunchConfiguration("entity_name")
    wrist_motor_type = LaunchConfiguration("wrist_motor_type")

    gazebo_pkg = FindPackageShare("el_a3_gazebo")
    description_pkg = FindPackageShare("el_a3_description")

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

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [FindPackageShare("gazebo_ros"), "/launch", "/gazebo.launch.py"]
        ),
        launch_arguments={
            "gui": gui,
            "pause": pause,
            "verbose": verbose,
            "world": world,
        }.items(),
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[robot_description, {"use_sim_time": use_sim_time}],
    )

    spawn_entity = Node(
        package="gazebo_ros",
        executable="spawn_entity.py",
        output="screen",
        arguments=[
            "-topic",
            "robot_description",
            "-entity",
            entity_name,
            "-x",
            "0.0",
            "-y",
            "0.0",
            "-z",
            "0.02",
        ],
    )

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager",
            "/controller_manager",
            "--controller-manager-timeout",
            "300",
        ],
    )

    arm_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "arm_controller",
            "--controller-manager",
            "/controller_manager",
            "--controller-manager-timeout",
            "300",
        ],
    )

    gripper_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "gripper_controller",
            "--controller-manager",
            "/controller_manager",
            "--controller-manager-timeout",
            "300",
        ],
    )

    delay_controller_spawners = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_entity,
            on_exit=[
                TimerAction(
                    period=2.0,
                    actions=[
                        joint_state_broadcaster_spawner,
                        arm_controller_spawner,
                        gripper_controller_spawner,
                    ],
                )
            ],
        )
    )

    rviz_config_file = PathJoinSubstitution(
        [description_pkg, "config", "el_a3_view.rviz"]
    )
    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config_file],
        parameters=[robot_description, {"use_sim_time": use_sim_time}],
        condition=IfCondition(use_rviz),
    )

    declared_arguments = [
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
            default_value="false",
            description="Start RViz with the EL-A3 display config.",
        ),
        DeclareLaunchArgument(
            "entity_name",
            default_value="el_a3",
            description="Gazebo entity name.",
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
            robot_state_publisher,
            spawn_entity,
            delay_controller_spawners,
            rviz,
        ]
    )
