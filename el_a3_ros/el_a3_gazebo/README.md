# EL-A3 Gazebo Simulation

`el_a3_gazebo` provides Gazebo Classic simulation launch files, Gazebo-specific `ros2_control` controller configuration, and a MoveIt2 integration launch for the EL-A3 robot arm.

This package is intended for ROS 2 Humble on Ubuntu 22.04.

---

## What This Package Starts

### Gazebo Only

```bash
ros2 launch el_a3_gazebo el_a3_gazebo.launch.py
```

Starts:

- Gazebo Classic server/client
- `robot_state_publisher`
- `gazebo_ros2_control`
- `joint_state_broadcaster`
- `arm_controller`
- `gripper_controller`

### Gazebo + MoveIt2

```bash
ros2 launch el_a3_gazebo el_a3_moveit_gazebo.launch.py
```

Starts everything above, plus:

- `move_group`
- MoveIt RViz configuration
- MoveIt controller bridge to Gazebo `ros2_control`

---

## Package Layout

```text
el_a3_gazebo/
├── CMakeLists.txt
├── package.xml
├── README.md
├── config/
│   └── el_a3_gazebo_controllers.yaml
├── launch/
│   ├── el_a3_gazebo.launch.py
│   └── el_a3_moveit_gazebo.launch.py
└── worlds/
    └── el_a3_empty.world
```

---

## Dependencies

Install the main simulation and MoveIt dependencies:

```bash
sudo apt update
sudo apt install \
  git-lfs \
  ros-humble-gazebo-ros-pkgs \
  ros-humble-gazebo-ros2-control \
  ros-humble-ros2-control \
  ros-humble-ros2-controllers \
  ros-humble-moveit \
  ros-humble-pick-ik \
  ros-humble-pinocchio
```

If you cloned the repository before installing Git LFS, pull the real mesh files:

```bash
cd /home/ros/edulite_ws/src/EDULITE_A3
git lfs pull
```

Verify that the STL files are real mesh files, not Git LFS pointer files:

```bash
ls -lh /home/ros/edulite_ws/src/EDULITE_A3/el_a3_ros/el_a3_description/meshes/*.stl
```

The files should be KB/MB sized. If they are around `130 bytes`, the meshes were not downloaded.

---

## Build

From the workspace root:

```bash
cd /home/ros/edulite_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

For simulation-only development:

```bash
cd /home/ros/edulite_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select el_a3_description el_a3_moveit_config el_a3_gazebo
source install/setup.bash
```

---

## Launch Gazebo Simulation

```bash
cd /home/ros/edulite_ws
source install/setup.bash
ros2 launch el_a3_gazebo el_a3_gazebo.launch.py
```

Headless mode:

```bash
ros2 launch el_a3_gazebo el_a3_gazebo.launch.py gui:=false
```

Verbose Gazebo logs:

```bash
ros2 launch el_a3_gazebo el_a3_gazebo.launch.py verbose:=true
```

Useful launch arguments:

| Argument | Default | Description |
|---|---:|---|
| `gui` | `true` | Start Gazebo GUI client |
| `pause` | `false` | Start simulation paused |
| `verbose` | `false` | Print verbose Gazebo logs |
| `use_sim_time` | `true` | Use `/clock` simulation time |
| `use_rviz` | `false` | Start RViz display config |
| `wrist_motor_type` | `EL05` | Wrist motor type: `EL05` or `RS05` |
| `world` | `el_a3_empty.world` | Gazebo world file |

---

## Verify Gazebo Controllers

In another terminal:

```bash
cd /home/ros/edulite_ws
source install/setup.bash
ros2 control list_controllers
```

Expected:

```text
joint_state_broadcaster  joint_state_broadcaster/JointStateBroadcaster          active
arm_controller           joint_trajectory_controller/JointTrajectoryController  active
gripper_controller       joint_trajectory_controller/JointTrajectoryController  active
```

Check trajectory actions:

```bash
ros2 action list | grep follow_joint_trajectory
```

Expected actions:

```text
/arm_controller/follow_joint_trajectory
/gripper_controller/follow_joint_trajectory
```

---

## Launch Gazebo With MoveIt2

Use this when you want to plan in MoveIt RViz and execute on the Gazebo robot:

```bash
cd /home/ros/edulite_ws
source install/setup.bash
ros2 launch el_a3_gazebo el_a3_moveit_gazebo.launch.py
```

If Gazebo is already running, start only MoveIt2:

```bash
ros2 launch el_a3_gazebo el_a3_moveit_gazebo.launch.py launch_gazebo:=false
```

Headless Gazebo with MoveIt RViz:

```bash
ros2 launch el_a3_gazebo el_a3_moveit_gazebo.launch.py gui:=false
```

Useful launch arguments:

| Argument | Default | Description |
|---|---:|---|
| `launch_gazebo` | `true` | Start Gazebo before MoveIt |
| `gui` | `true` | Start Gazebo GUI client |
| `use_rviz` | `true` | Start MoveIt RViz |
| `pause` | `false` | Start Gazebo paused |
| `use_sim_time` | `true` | Use simulation time |
| `wrist_motor_type` | `EL05` | Wrist motor type: `EL05` or `RS05` |

---

## Control The Robot In MoveIt RViz

1. Start Gazebo + MoveIt:

   ```bash
   ros2 launch el_a3_gazebo el_a3_moveit_gazebo.launch.py
   ```

2. In RViz, open the `MotionPlanning` panel.

3. Set `Planning Group` to `arm`.

4. Choose a named target such as `home` or `ready`, or drag the interactive marker.

5. Click `Plan`.

6. Click `Execute`.

The planned trajectory is sent to:

```text
/arm_controller/follow_joint_trajectory
```

For the gripper group, MoveIt sends trajectories to:

```text
/gripper_controller/follow_joint_trajectory
```

Do not use this launch for Gazebo control:

```bash
ros2 launch el_a3_moveit_config demo.launch.py
```

That launch starts mock hardware and is intended for RViz-only MoveIt testing.

---

## Send A Test Trajectory Without MoveIt

This command sends a simple arm trajectory directly to the Gazebo controller:

```bash
ros2 action send_goal /arm_controller/follow_joint_trajectory \
  control_msgs/action/FollowJointTrajectory \
  "{
    trajectory: {
      joint_names: [L1_joint, L2_joint, L3_joint, L4_joint, L5_joint, L6_joint],
      points: [
        {
          positions: [0.0, 0.785, -0.785, 0.0, 0.0, 0.0],
          velocities: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          time_from_start: {sec: 2, nanosec: 0}
        }
      ]
    }
  }"
```

---

## Important Implementation Notes

### Gazebo Mesh Paths

Gazebo Classic does not reliably resolve `package://` mesh URIs in spawned URDF models. The Gazebo launch passes:

```text
mesh_prefix:=file://<el_a3_description share>/meshes/
```

This avoids slow Gazebo model database lookups and makes startup much faster.

### Gazebo ros2_control Mode

`el_a3_description/urdf/el_a3.urdf.xacro` supports three modes:

- Real hardware: `use_mock_hardware:=false`, `use_gazebo:=false`
- Mock hardware: `use_mock_hardware:=true`
- Gazebo: `use_gazebo:=true`

In Gazebo mode, the xacro uses:

```text
gazebo_ros2_control/GazeboSystem
```

and loads:

```text
el_a3_gazebo/config/el_a3_gazebo_controllers.yaml
```

### MoveIt Controller Bridge

MoveIt uses:

```text
el_a3_moveit_config/config/moveit_controllers.yaml
```

to map MoveIt trajectory execution to:

```text
arm_controller
gripper_controller
```

The MoveIt-Gazebo launch sets:

```text
moveit_manage_controllers: false
```

because Gazebo/ros2_control is responsible for loading and activating the controllers.

---

## Troubleshooting

### Robot Does Not Appear In Gazebo

Check whether the STL files are Git LFS pointer files:

```bash
ls -lh /home/ros/edulite_ws/src/EDULITE_A3/el_a3_ros/el_a3_description/meshes/*.stl
```

If they are around `130 bytes`, run:

```bash
sudo apt install git-lfs
cd /home/ros/edulite_ws/src/EDULITE_A3
git lfs pull
```

Then rebuild and relaunch.

### Controller Spawners Wait Forever

If you see:

```text
waiting for service /controller_manager/list_controllers to become available
```

Gazebo has not loaded `gazebo_ros2_control` yet, or Gazebo is not running.

Check:

```bash
ros2 service list | grep controller_manager
ros2 node list
```

You should eventually see `/controller_manager` services.

### Gazebo Takes Several Minutes To Start

Run with verbose logs:

```bash
ros2 launch el_a3_gazebo el_a3_gazebo.launch.py verbose:=true
```

If logs mention `models.gazebosim.org` or `Failed to find mesh file`, check that the current launch is the updated one and rebuild:

```bash
colcon build --symlink-install --packages-select el_a3_description el_a3_gazebo
source install/setup.bash
```

### MoveIt Cannot Use Pose Goals

If MoveIt logs show:

```text
pick_ik/PickIkPlugin ... does not exist
```

install Pick IK:

```bash
sudo apt install ros-humble-pick-ik
```

Then restart the MoveIt launch.

### Gazebo GUI Closes But Server Keeps Running

Try headless mode:

```bash
ros2 launch el_a3_gazebo el_a3_gazebo.launch.py gui:=false
```

If headless works, the issue is likely GUI, GPU, OpenGL, or display forwarding related.

### Multiple Gazebo Instances Conflict

Stop old launches with `Ctrl+C`. If a stale `gzserver` remains:

```bash
ps -ef | grep gzserver
kill <PID>
```

### ROS_DOMAIN_ID Mismatch

All terminals must use the same ROS domain:

```bash
echo $ROS_DOMAIN_ID
```

Empty is equivalent to domain `0`. To set explicitly:

```bash
export ROS_DOMAIN_ID=0
source /home/ros/edulite_ws/install/setup.bash
```

---

## Useful Inspection Commands

```bash
ros2 node list
ros2 topic list
ros2 service list | grep controller_manager
ros2 control list_controllers
ros2 action list | grep follow_joint_trajectory
ros2 topic echo /joint_states
ros2 topic echo /clock
```

---

## Clean Rebuild

If launch behavior looks stale after editing launch or xacro files:

```bash
cd /home/ros/edulite_ws
rm -rf build/el_a3_gazebo install/el_a3_gazebo log
colcon build --symlink-install --packages-select el_a3_description el_a3_moveit_config el_a3_gazebo
source install/setup.bash
```

---

## Quick Reference

Gazebo only:

```bash
ros2 launch el_a3_gazebo el_a3_gazebo.launch.py
```

Gazebo only, headless:

```bash
ros2 launch el_a3_gazebo el_a3_gazebo.launch.py gui:=false
```

Gazebo + MoveIt:

```bash
ros2 launch el_a3_gazebo el_a3_moveit_gazebo.launch.py
```

MoveIt only, when Gazebo is already running:

```bash
ros2 launch el_a3_gazebo el_a3_moveit_gazebo.launch.py launch_gazebo:=false
```
