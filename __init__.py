import bpy
import mathutils
from bpy.types import WorkSpaceTool, AddonPreferences

class UnrNavPreferences(AddonPreferences):
    bl_idname = __name__

    move_sensitivity: bpy.props.FloatProperty(
        name="Move Sensitivity",
        default=8.0,
        min=1.0,
        max=20,
        precision=2,
    )
    look_sensitivity: bpy.props.FloatProperty(
        name="Look Sensitivity",
        default=2.0,
        min=0.1,
        max=10.0,
        precision=2,
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "move_sensitivity")
        layout.prop(self, "look_sensitivity")

class VIEW3D_OT_unr_nav_tool(bpy.types.Operator):
    bl_idname = "view3d.unr_nav_tool"
    bl_label = "UNR Navigation"
    bl_options = {'BLOCKING', 'GRAB_CURSOR'}

    def update_status_bar(self, context):
        if self.lmb and self.rmb:
            msg = "LMB+RMB: Move Vertically / Strafe"
        elif self.lmb:
            msg = "LMB: Move Horizontally / Forward"
        elif self.rmb:
            msg = "RMB: Look Around"
        else:
            msg = "LMB: Move, RMB: Look | Shortcut: D"
        context.workspace.status_text_set(msg)

    def modal(self, context, event):
        if event.type == 'LEFTMOUSE':
            self.lmb = (event.value == 'PRESS')
        elif event.type == 'RIGHTMOUSE':
            self.rmb = (event.value == 'PRESS')

        self.update_status_bar(context)

        if not self.is_dragging:
            delta = (mathutils.Vector((event.mouse_x, event.mouse_y)) - self.start_pos).length
            if delta > 8:
                self.is_dragging = True

        if event.value == 'RELEASE':
            if not self.is_dragging:
                menu_name = "VIEW3D_MT_edit_mesh_context_menu" if context.mode == 'EDIT_MESH' else "VIEW3D_MT_object_context_menu"
                if event.type in {'LEFTMOUSE', 'RIGHTMOUSE'}:
                    bpy.ops.view3d.select(extend=False, deselect_all=True, location=(event.mouse_region_x, event.mouse_region_y))
                    if event.type == 'RIGHTMOUSE':
                        bpy.ops.wm.call_menu(name=menu_name)
            
            if not self.lmb and not self.rmb:
                context.workspace.status_text_set(None)
                return {'FINISHED'}

        if self.is_dragging and event.type == 'MOUSEMOVE':
            prefs = context.preferences.addons[__name__].preferences
            move_s = prefs.move_sensitivity / 100
            rot_s = prefs.look_sensitivity / 1000

            dx, dy = event.mouse_x - event.mouse_prev_x, event.mouse_y - event.mouse_prev_y
            rv3d = context.region_data
            view_inv = rv3d.view_matrix.inverted()
            cam_pos = view_inv.to_translation()
            view_rot = rv3d.view_rotation
            f, r, up = view_rot @ mathutils.Vector((0,0,-1)), view_rot @ mathutils.Vector((1,0,0)), mathutils.Vector((0,0,1))

            if self.lmb and self.rmb:
                cam_pos += (r * (dx * move_s)) + (up * (dy * move_s))
            elif self.lmb:
                f_xy = f.copy(); f_xy.z = 0; f_xy.normalize()
                cam_pos += f_xy * (dy * move_s)
                rv3d.view_rotation = mathutils.Quaternion(up, -dx * rot_s) @ rv3d.view_rotation
            elif self.rmb:
                rv3d.view_rotation = mathutils.Quaternion(up, -dx * rot_s) @ rv3d.view_rotation @ mathutils.Quaternion(mathutils.Vector((1,0,0)), dy * rot_s)

            rv3d.view_location = cam_pos + (rv3d.view_rotation @ mathutils.Vector((0,0,-rv3d.view_distance)))
            
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self.start_pos = mathutils.Vector((event.mouse_x, event.mouse_y))
        self.is_dragging = False
        self.lmb, self.rmb = (event.type == 'LEFTMOUSE'), (event.type == 'RIGHTMOUSE')
        self.update_status_bar(context)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

class WM_OT_unr_nav_switcher(bpy.types.Operator):
    bl_idname = "wm.unr_nav_switcher"
    bl_label = "Activate Unreal Nav"
    
    def execute(self, context):
        target_id = "user.unr_nav_edit" if context.mode == 'EDIT_MESH' else "user.unr_nav"
        bpy.ops.wm.tool_set_by_id(name=target_id)
        return {'FINISHED'}

class UnrNavTool(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'
    bl_idname = "user.unr_nav"
    bl_label = "UNR Nav"
    bl_description = "Unreal Style Navigation (Press 'D' to activate)"
    bl_icon = "GHOST_ENABLED"
    bl_group = "user.unr_group"
    
    bl_keymap = (
        ("wm.unr_nav_switcher", {"type": 'D', "value": 'PRESS'}, None),
        ("view3d.unr_nav_tool", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("view3d.unr_nav_tool", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
    )

class UnrNavToolEdit(UnrNavTool):
    bl_context_mode = 'EDIT_MESH'
    bl_idname = "user.unr_nav_edit"

addon_keymaps = []

def register():
    bpy.utils.register_class(UnrNavPreferences)
    bpy.utils.register_class(VIEW3D_OT_unr_nav_tool)
    bpy.utils.register_class(WM_OT_unr_nav_switcher)
    
    bpy.utils.register_tool(UnrNavTool, after={"builtin.select"}, separator=True, group=True)
    bpy.utils.register_tool(UnrNavToolEdit, after={"builtin.select"}, separator=True, group=True)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new("wm.unr_nav_switcher", 'D', 'PRESS')
        addon_keymaps.append((km, kmi))

    def make_default():
        try: bpy.ops.wm.unr_nav_switcher()
        except: pass
        return None
    bpy.app.timers.register(make_default, first_interval=0.1)

def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    
    bpy.utils.unregister_tool(UnrNavTool)
    bpy.utils.unregister_tool(UnrNavToolEdit)
    bpy.utils.unregister_class(WM_OT_unr_nav_switcher)
    bpy.utils.unregister_class(VIEW3D_OT_unr_nav_tool)
    bpy.utils.unregister_class(UnrNavPreferences)

if __name__ == "__main__":
    register()