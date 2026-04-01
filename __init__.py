import bpy
import mathutils
import os
from bpy.types import WorkSpaceTool

# --- THE OPERATOR ---
class VIEW3D_OT_unr_nav_tool(bpy.types.Operator):
    bl_idname = "view3d.unr_nav_tool"
    bl_label = "UNR Navigation"
    bl_options = {'BLOCKING', 'GRAB_CURSOR'}

    def modal(self, context, event):
        if event.type == 'LEFTMOUSE':
            self.lmb = (event.value == 'PRESS')
        elif event.type == 'RIGHTMOUSE':
            self.rmb = (event.value == 'PRESS')

        if not self.is_dragging:
            delta = (mathutils.Vector((event.mouse_x, event.mouse_y)) - self.start_pos).length
            if delta > 8:
                self.is_dragging = True

        if event.value == 'RELEASE':
            if not self.is_dragging:
                menu_name = "VIEW3D_MT_edit_mesh_context_menu" if context.mode == 'EDIT_MESH' else "VIEW3D_MT_object_context_menu"

                if event.type == 'LEFTMOUSE':
                    bpy.ops.view3d.select(extend=False, deselect_all=True, location=(event.mouse_region_x, event.mouse_region_y))
                elif event.type == 'RIGHTMOUSE':
                    bpy.ops.view3d.select(extend=False, deselect_all=True, location=(event.mouse_region_x, event.mouse_region_y))
                    bpy.ops.wm.call_menu(name=menu_name)
            
            if not self.lmb and not self.rmb:
                return {'FINISHED'}

        if self.is_dragging and event.type == 'MOUSEMOVE':
            dx, dy = event.mouse_x - event.mouse_prev_x, event.mouse_y - event.mouse_prev_y
            rv3d = context.region_data
            view_inv = rv3d.view_matrix.inverted()
            cam_pos = view_inv.to_translation()
            view_rot = rv3d.view_rotation
            f, r, up = view_rot @ mathutils.Vector((0,0,-1)), view_rot @ mathutils.Vector((1,0,0)), mathutils.Vector((0,0,1))

            if self.lmb and self.rmb:
                cam_pos += (r * (dx * 0.08)) + (up * (dy * 0.08))
            elif self.lmb:
                f_xy = f.copy(); f_xy.z = 0; f_xy.normalize()
                cam_pos += f_xy * (dy * 0.08)
                rv3d.view_rotation = mathutils.Quaternion(up, -dx * 0.002) @ rv3d.view_rotation
            elif self.rmb:
                yaw = mathutils.Quaternion(up, -dx * 0.002)
                pitch = mathutils.Quaternion(mathutils.Vector((1,0,0)), dy * 0.002)
                rv3d.view_rotation = yaw @ rv3d.view_rotation @ pitch

            rv3d.view_location = cam_pos + (rv3d.view_rotation @ mathutils.Vector((0,0,-rv3d.view_distance)))
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self.start_pos = mathutils.Vector((event.mouse_x, event.mouse_y))
        self.is_dragging = False
        self.lmb, self.rmb = (event.type == 'LEFTMOUSE'), (event.type == 'RIGHTMOUSE')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

# --- THE TOOL DEFINITIONS ---
class UnrNavTool(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'
    bl_idname = "user.unr_nav"
    bl_label = "UNR Nav"
    bl_description = "LMB: Move/Select, RMB: Look/Menu, Both: Strafe"
    
    # Using a high-quality internal icon that looks like a pointer + camera
    bl_icon = "ops.generic.select" 
    
    # This ID links it to the standard Tweak/Box/Lasso group
    bl_group = "builtin.select" 
    
    # A low order number puts it at the top of the fly-out menu
    bl_order = 0
    
    bl_keymap = (
        ("view3d.unr_nav_tool", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("view3d.unr_nav_tool", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
    )

class UnrNavToolEdit(UnrNavTool):
    bl_context_mode = 'EDIT_MESH'
    bl_idname = "user.unr_nav_edit"
    bl_order = 0

# --- REGISTRATION ---

def register():
    bpy.utils.register_class(VIEW3D_OT_unr_nav_tool)
    
    # We must register the tools with group=True to allow bl_group to function
    bpy.utils.register_tool(UnrNavTool, separator=True, group=True)
    bpy.utils.register_tool(UnrNavToolEdit, separator=True, group=True)

    def make_default():
        try:
            target = "user.unr_nav_edit" if bpy.context.mode == 'EDIT_MESH' else "user.unr_nav"
            bpy.ops.wm.tool_set_by_id(name=target)
        except: pass
        return None
    bpy.app.timers.register(make_default, first_interval=0.1)

def unregister():
    try:
        bpy.utils.unregister_tool(UnrNavTool)
        bpy.utils.unregister_tool(UnrNavToolEdit)
    except: pass
    bpy.utils.unregister_class(VIEW3D_OT_unr_nav_tool)

if __name__ == "__main__":
    register()