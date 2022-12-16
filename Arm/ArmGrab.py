#!/usr/bin/env python

from __future__ import print_function
from six.moves import input
import sys
import copy
import rospy
import moveit_commander
import moveit_msgs.msg
import geometry_msgs.msg

class MoveGroupPython(object):
    def __init__(self):
        moveit_commander.roscpp_initialize(sys.argv)
        rospy.init_node("move_ball_python", anonymous=True)

        robot = moveit_commander.RobotCommander()

        scene = moveit_commander.PlanningSceneInterface()
        group_name = "panda_arm"
        move_group = moveit_commander.MoveGroupCommander(group_name)

        display_trajectory_publisher = rospy.Publisher(
            "/move_group/display_planned_path",
            moveit_msgs.msg.DisplayTrajectory,
            queue_size=20,
        )

        planning_frame = move_group.get_planning_frame()
        eef_link = move_group.get_end_effector_link()
        group_names = robot.get_group_names()
        
        self.desk_name = ""
        self.sphere_name = ""
        self.robot = robot
        self.scene = scene
        self.move_group = move_group
        self.display_trajectory_publisher = display_trajectory_publisher
        self.planning_frame = planning_frame
        self.eef_link = eef_link
        self.group_names = group_names
        self.homepose = self.move_group.get_current_pose().pose

    def plan_cartesian_path(self, pose="target"):
        waypoints = []
        if pose == "target":
            wpose = self.move_group.get_current_pose().pose
            wpose.position.z = 0.35
            wpose.position.x = 0.4
            waypoints.append(copy.deepcopy(wpose))
        elif pose == 'home':
            waypoints.append(self.homepose)
        (plan, fraction) = self.move_group.compute_cartesian_path(
            waypoints, 0.01, 0.0
        )
        return plan, fraction

    def execute_plan(self, plan):
        self.move_group.execute(plan, wait=True)

    def wait_for_attach_object_state_update(self, object_name, object_is_known=False, object_is_attached=False, timeout=4):
        start = rospy.get_time()
        seconds = rospy.get_time()
        while (seconds - start < timeout) and not rospy.is_shutdown():
            attached_objects = self.scene.get_attached_objects([object_name])
            is_attached = len(attached_objects.keys()) > 0
            is_known = object_name in self.scene.get_known_object_names()
            if (object_is_attached == is_attached) and (object_is_known == is_known):
                return True
            rospy.sleep(0.1)
            seconds = rospy.get_time()
        return False

    def wait_for_add_object_state_update(self, object_name, object_is_known=False, timeout=4):
        start = rospy.get_time()
        seconds = rospy.get_time()
        while (seconds - start < timeout) and not rospy.is_shutdown():
            is_known = object_name in self.scene.get_known_object_names()
            if object_is_known == is_known:
                return True
            rospy.sleep(0.1)
            seconds = rospy.get_time()
        return False

    def add_sphere(self, timeout=4):
        sphere_pose = geometry_msgs.msg.PoseStamped()
        sphere_pose.header.frame_id = "panda_link0"
        sphere_pose.pose.orientation.w = 1.0
        sphere_pose.pose.position.x = 0.4
        sphere_pose.pose.position.z = 0.25
        self.sphere_name = "sphere"
        self.scene.add_sphere(self.sphere_name, sphere_pose, radius=0.0315)
        return self.wait_for_add_object_state_update(self.desk_name, object_is_known=True, timeout=timeout)

    def attach_sphere(self, timeout=4):
        grasping_group = "panda_hand"
        touch_links = self.robot.get_link_names(group=grasping_group)
        self.scene.attach_box(self.eef_link, self.sphere_name, touch_links=touch_links)
        return self.wait_for_attach_object_state_update(self.sphere_name, object_is_known=True, object_is_attached=True, timeout=timeout)

    def add_desk(self, timeout=4):
        desk_pose = geometry_msgs.msg.PoseStamped()
        desk_pose.header.frame_id = "panda_link0"
        desk_pose.pose.position.x = 0.4
        desk_pose.pose.position.z = 0.2
        self.desk_name = "desk"
        self.scene.add_box(self.desk_name, desk_pose, size=(0.5, 0.8, 0.05))
        return self.wait_for_add_object_state_update(self.desk_name, object_is_known=True, timeout=timeout)

    def detach_sphere(self, timeout=4):
        self.scene.remove_attached_object(self.eef_link, name=self.sphere_name)
        return self.wait_for_attach_object_state_update(self.sphere_name, object_is_known=True, object_is_attached=False, timeout=timeout)

    def remove_object(self, object_name, timeout=4):
        self.scene.remove_world_object(object_name)
        return self.wait_for_add_object_state_update(object_name, object_is_known=False, timeout=timeout)


def main():
    try:
        movearm = MoveGroupPython()
        input("-----add desk-----")
        movearm.add_desk()
        input("-----add sphere-----")
        movearm.add_sphere()
        input("-----plan-----")
        cartesian_plan, fraction = movearm.plan_cartesian_path()
        input("-----execute-----")
        movearm.execute_plan(cartesian_plan)
        input("-----attach sphere-----")
        movearm.attach_sphere()
        input("-----plan-----")
        cartesian_plan, fraction = movearm.plan_cartesian_path('home')
        input("-----execute-----")
        movearm.execute_plan(cartesian_plan)
        input("-----deattach sphere-----")
        movearm.detach_sphere()
        input("-----remove sphere-----")
        movearm.remove_object("sphere")
    except rospy.ROSInterruptException:
        return
    except KeyboardInterrupt:
        return


if __name__ == "__main__":
    main()
