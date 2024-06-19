bl_info = {
    "name": "Imgage Empty To Mesh",
    "author": "NinKorr",
    "version": (1, 0, 1),
    "blender": (2, 92, 0),
    "location": "View3D/context menu",
    "description": "Turns image empty into mesh object",
    "category": "Misc",
    }

import bpy
from bpy.types import Operator
from bpy.utils import register_class, unregister_class

def popup(text="WARNING: something's wrong..."):
    def draw(self, context):
        self.layout.label(text=text)
    bpy.context.window_manager.popup_menu(draw,title='',icon='NONE')
    return

def image_to_material(img):
    mat = bpy.data.materials.new(img.name)
    mat.use_nodes = True
    NT = mat.node_tree
    NT.nodes.remove(NT.nodes['Principled BSDF'])  # No shading is needed
    output = NT.nodes[0]  # only 1 node exists
    tex = NT.nodes.new("ShaderNodeTexImage")
    tex.location = [0,300]
    tex.image = img
    NT.links.new(tex.outputs['Color'],output.inputs['Surface'])
    return mat

def img_empty_to_plane(obj):
    #collecting info about image
    size = obj.empty_display_size
    matrix = obj.matrix_world
    img = obj.data
    ratio = img.size[0]/img.size[1]
    if ratio > 1:
        x = size
        y = (size/ratio)
    else:
        x = (size*ratio)
        y = size
    offset = [obj.empty_image_offset[0]*x, obj.empty_image_offset[1]*y]

    # mesh creation
    mesh = bpy.data.meshes.new(img.name)

    verts =[[offset[0],     offset[1],      0],
            [offset[0] + x, offset[1],      0],
            [offset[0] + x, offset[1] + y,  0],
            [offset[0],     offset[1] + y,  0],
           ]

    faces = [[0,1,2,3]]  # simple quad
    mesh.from_pydata(verts,[],faces)  # no edges needed
    mesh.uv_layers.new(do_init = True)

    new_obj = bpy.data.objects.new(img.name, mesh)
    # transforms and replacing in collections
    new_obj.matrix_world = matrix
    for col in obj.users_collection:
        col.objects.link(new_obj)
        col.objects.unlink(obj)
    # material
    mat = bpy.data.materials.get(img.name)  # might exist already
    if mat is None:
        mat = image_to_material(img)
    mesh.materials.append(mat)
    # don't need original object anymore
    bpy.data.objects.remove(obj)
    return

def get_sel_img_nodes(context):
    sel=[obj for obj in context.selected_objects if obj.type=='EMPTY'
         and obj.empty_display_type == 'IMAGE'
         and obj.data is not None]
    return sel

#menus

#Converter for a context menu
def image_empty_to_mesh_menu(self,context):
    l = self.layout
    sel = get_sel_img_nodes(context)
    if sel.__len__() > 0:
        l.operator('object.image_to_plane')
        l.separator()
    return

#OPERATORS

class OBJECT_OT_image_to_plane(Operator):
    bl_idname       = 'object.image_to_plane'
    bl_label        = 'Convert To Plane'
    bl_description  = "Turns image empty into real geometry"
    bl_options      = {'UNDO'}

    def execute(self,context):
        if context.mode != 'OBJECT':
            popup('Works only in OBJECT mode')
            return {'CANCELLED'}

        sel = get_sel_img_nodes(context)

        if sel.__len__()==0:
            popup('No Image empties selected!')
            return {'CANCELLED'}

        for obj in sel:
            img_empty_to_plane(obj)
        return {'FINISHED'}

#REGISTER

def register():
    register_class(OBJECT_OT_image_to_plane)
    bpy.types.VIEW3D_MT_object_context_menu.prepend(image_empty_to_mesh_menu)
    return

def unregister():
    unregister_class(OBJECT_OT_image_to_plane)
    bpy.types.VIEW3D_MT_object_context_menu.remove(image_empty_to_mesh_menu)
    return

if __name__ == "__main__":
    register()