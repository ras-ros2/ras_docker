<pre>
```markdown
## ROS Interface Overview

This section provides an organized list of all **topics** and **nodes** published or subscribed by both the **Server App** and **Robot App** components.

---

### Topics

#### Server App Topics
/attached_collision_object  
/clicked_point  
/client_count  
/clock  
/collision_object  
/connected_clients  
/despawn_model  
/display_contacts  
/display_planned_path  
/dynamic_joint_states  
/goal_pose  
/initialpose  
/joint_state_broadcaster/transition_event  
/joint_states  
/joint_trajectory_controller/controller_state  
/joint_trajectory_controller/state  
/joint_trajectory_controller/joint_trajectory  
/joint_trajectory_controller/transition_event  
/log_receiver/transition_event  
/monitored_planning_scene  
/motion_plan_request  
/parameter_events  
/planning_scene  
/planning_scene_world  
/realsense_camera/image_raw  
/realsense_depth_camera/depth_raw  
/recognized_object_array  
/robot_description  
/robot_description_semantic  
/rosout  
/rviz_noveit_notion_planning_display/robot_interaction_interactive_marker_topic/feedback  
/rviz_noveit_notion_planning_display/robot_interaction_interactive_marker_topic/update  
/tf  
/tf_static  
/trajectory_execution_event  
/trajectory_topic  

#### Robot App Topics
/aruco_markers  
/attached_collision_object  
/camera/camera/color/image_raw  
/camera/camera/depth/color/points  
/camera/camera/depth/image_rect_raw  
/clicked_point  
/collision_object  
/display_contacts  
/display_planned_path  
/dynamic_joint_states  
/goal_pose  
/log_receiver/transition_event  
/initialpose  
/joint_state_broadcaster/transition_event  
/joint_states  
/lite/joint_states  
/lite/robot_states  
/lite/uf_ftsensor_ext_states  
/lite/uf_ftsensor_raw_states  
/lite/xarm_cgpio_states  
/lited_traj_controller/controller_state  
/lited_traj_controller/joint_trajectory  
/lited_traj_controller/state  
/lited_traj_controller/transition_event  
/log_sender/transition_event  
/monitored_planning_scene  
/motion_plan_request  
/parameter_events  
/planning_scene  
/planning_scene_world  
/recognized_object_array  
/robot_description  
/robot_description_semantic  
/rosout  
/rviz_moveit_notion_planning_display/robot_interaction_interactive_marker_topic/feedback  
/rviz_moveit_notion_planning_display/robot_interaction_interactive_marker_topic/update  
/tf  
/tf_static  
/trajectory_execution_event  
/trajectory_topic  

---

### Nodes

#### Server App Nodes
/batman  
/bt_executor  
/bt_executor_node  
/controller_manager  
/experiment_service  
/fake_gripper_node  
/gz_ros2_control  
/interactive_marker_display_100930990871392  
/log_receiver  
/mot_sender  
/joint_state_broadcaster  
/joint_trajectory_controller  
/nove_group  
/nove_group_private_95038449106432  
/novelt_server  
/novett_server  
/novett_simple_controller_manager  
/planning_scene_interface_168404006119136  
/robot_state_publisher  
/ros_gz_bridge  
/rosbridge_websocket  
/rviz2  
/rviz2_private_128764869124416  
/spawn_tgn_node  
/spawn_model_node  
/trajectory_recoder_service  
/transform_listener_impl_566fdd3dcdb6  
/transform_listener_tmpl_5bcbd2636420  
/transform_listener_tmpl_5bcbd276ed40  
/transform_listener_tmpl_750e70002e50  
/transport_server_service  

#### Robot App Nodes
/aruco_tf_publisher  
/bt_executor  
/bt_executor_node  
/camera/camera  
/controller_manager  
/dummy_logging_server  
/gripper_controller  
/interactive_marker_display_100189515690272  
/log_sender  
/logging_manager  
/lited_traj_controller  
/lite/joint_state_broadcaster  
/lite/lot_receiver  
/lite/tot_receiver  
/move_group  
/nove_group_private_95175533699232  
/novelt_server  
/novelt_simple_controller_manager  
/planning_scene_interface_163796493256912  
/robot_state_publisher  
/rvizz  
/rvizz_private_136173548845184  
/static_transform_publisher  
/trajectory_recoder_service  
/transform_listener_tmpl_568fc7d83150  
/transform_listener_tmpl_5b1f2f24cb20  
/transform_listener_tmpl_5b1f2f38f806  
/transform_listener_tmpl_7bd960003300  
/transform_publisher  
/transport_robot_service  
/ufactory_driver  
/ufactory_robot_hw  
```
</pre>