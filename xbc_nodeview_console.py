# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####


import string

import bpy
# import bgl
import blf
import gpu
from gpu_extras.batch import batch_for_shader
from bpy.types import SpaceNodeEditor

import sverchok
from sverchok.menu import make_node_cats
from sverchok.utils.modules.shader_utils import ShaderLib2D

from .xbc_nodeview_macro_routing import route_as_macro
from .xbc_nodeview_console_routing import route_as_websearch
# from .utils.xbc_bgl_lib import draw_rect, draw_border

# pylint: disable=C0326
# pylint: disable=w0612

sv_types = {'SverchCustomTreeType', 'SverchGroupTreeType'}
ddir = lambda content: [n for n in dir(content) if not n.startswith('__')]

### ---- Key Handling ----------------------------------------------------------

verbose_nums = "ZERO ONE TWO THREE FOUR FIVE SIX SEVEN EIGHT NINE".split(" ")
verbose_numpads = [('NUMPAD_' + n) for n in string.digits]

CAPS = set(a for a in string.ascii_uppercase)
NUMS = set(verbose_nums)
NUMS2 = set(verbose_numpads)

NUMS = NUMS.union(NUMS2)
SPECIALS = set('BACK_SPACE LEFT_ARROW DOWN_ARROW RIGHT_ARROW UP_ARROW SPACE'.split(' '))
KEYBOARD = CAPS.union(SPECIALS)
KEYBOARD = KEYBOARD.union(NUMS)

remap_nums = {k: str(idx) for idx, k in enumerate(verbose_nums)}
remap_extras = {k: str(idx) for idx, k in enumerate(verbose_numpads)}
remap_nums.update(remap_extras)

### ---- Category Handling -----------------------------------------------------

node_cats = make_node_cats()

def removed_sv_prefix(str_in):
    if str_in.startswith("Sv"):
        return str_in[2:]
    return str_in

def make_flat_nodecats():
    flat_node_list = []
    for ref in sverchok.node_list:
        for iref in ddir(ref):
            rref = getattr(ref, iref)
            if 'sv_init' in ddir(rref) and 'bl_idname' in ddir(rref):
                items = [rref.bl_label, rref.bl_idname, str(rref.__module__).replace('sverchok.nodes.', '')]
                flat_node_list.append('  |  '.join(items))
    return flat_node_list

flat_node_cats = {}
event_tracking = {'previous_event': None}

def return_search_results(search_term):
    prefilter = []
    if search_term:
        idx = 1
        for item in flat_node_cats.get('results'):
            if search_term in removed_sv_prefix(item).lower() and not item.startswith('NodeReroute'):
                prefilter.append(item.split('  |  '))
                idx += 1
            if idx > 10:
                break
    return prefilter


def route_as_nodelookup(operator, context):

    found_results = flat_node_cats.get('list_return')
    if found_results and len(found_results) > operator.current_index:
        try:
            operator.ensure_nodetree(context)
            node_bl_idname = found_results[operator.current_index][1]
            new_node = context.space_data.edit_tree.nodes.new(node_bl_idname)
            new_node.select = False
            return True
        except Exception as err:
            print(repr(err))




### ------------------------------------------------------------------------------

# BL_IDNAME_COLOR = [0.708376, 0.708376, 0.708376, 1.000000]
# BL_CLASSNAME_COLOR = [0.708376, 0.708376, 0.708376, 1.000000]
# BL_DISKLOCATION_COLOR = [0.708376, 0.708376, 0.708376, 1.000000]
text_highest = (0.99, 0.99, 0.99, 1.0)
text_high = (0.93, 0.93, 0.93, 1.0)
text_low = (0.83, 0.83, 0.83, 1.0)
highcol = [0.255861, 0.539657, 1.0, 1.0]
lowcol = [0.215861, 0.439657, 1.0, 1.0]
console_bg_color = [0.028426, 0.028426, 0.028426, 1.0]

search_colors = (text_highest, text_high, text_low)


def draw_string(x, y, packed_strings, highlite=False):
    x_offset = 0
    font_id = 0
    for pstr, pcol in packed_strings:
        pstr2 = ' ' + pstr + ' '

        blf.color(font_id, *pcol)
        text_width, text_height = blf.dimensions(font_id, pstr2)
        blf.position(font_id, (x + x_offset), y, 0)
        blf.draw(font_id, pstr2)
        x_offset += text_width
    if highlite:
        blf.position(font_id, x_offset + 20, y, 0)
        blf.draw(font_id, " <")        

def draw_prompt(height, caret, current_string):
    font_id = 0
    blf.color(font_id, *text_highest)
    blf.position(font_id, 20, height-40, 0)
    blf.size(font_id, 12, 72)
    blf.draw(font_id, '>>> ' + current_string)

def draw_callback_px(self, context, start_position):

    header_height = context.area.regions[0].height
    width = context.area.width
    height = context.area.height - header_height
    begin_height = height-40

    font_id = 0
    content = []
    
    canvas = ShaderLib2D()
    canvas.add_rect(0, height-46, width, 10*20, console_bg_color)
    
    nx = 20
    found_results = flat_node_cats.get('list_return')

    if found_results:

        # highlight
        canvas.add_rect(0, begin_height-(20*self.current_index)-7, width, 18, lowcol, highcol)
        canvas.add_rect_outline(0, begin_height-(20*self.current_index)-7, width, 18, 1.0, "inside", (0.3, 0.3, 0.9, 1.0))

        # collect search item strings
        for idx, search_item_result in enumerate(found_results, start=1):
            ny = begin_height-(20*idx)
            if '.' in search_item_result[2]:
                search_item_result[2] = search_item_result[2].replace('.', '/')

            highlite = (idx == self.current_index + 1)
            content.append((nx, ny, zip(search_item_result, search_colors), highlite))
  
    geom = canvas.compile()
    shader = gpu.shader.from_builtin('2D_SMOOTH_COLOR')
    batch = batch_for_shader(
        shader, 
        'TRIS',
        {"pos": geom.vectors, "color": geom.vertex_colors}, indices=geom.indices
    )
    batch.draw(shader)

    for element in content:
        draw_string(*element)
    draw_prompt(height, '>>> ', self.current_string)


class XBCNodeViewConsole(bpy.types.Operator):
    """Implementing of bgl console"""
    bl_idname = "node.xbc_nodeview_console"
    bl_label = "Nodeview Console"

    current_string: bpy.props.StringProperty()
    chosen_bl_idname: bpy.props.StringProperty()
    current_index: bpy.props.IntProperty(default=0)
    new_direction: bpy.props.IntProperty(default=1)

    @classmethod
    def poll(cls, context):
        return context.space_data.type == 'NODE_EDITOR'


    def ensure_nodetree(self, context):
        '''
        if no active nodetree
        add new empty node tree, set fakeuser immediately
        '''
        if not context.space_data.tree_type in sv_types:
            print('not running from a sv nodetree')
            return

        if not hasattr(context.space_data.edit_tree, 'nodes'):
            msg_one = 'going to add a new empty node tree'
            msg_two = 'added new node tree'
            print(msg_one)
            self.report({"WARNING"}, msg_one)
            ng_params = {'name': 'unnamed_tree', 'type': 'SverchCustomTreeType'}
            ng = bpy.data.node_groups.new(**ng_params)
            ng.use_fake_user = True
            context.space_data.node_tree = ng
            self.report({"WARNING"}, msg_two)


    def modal(self, context, event):
        context.area.tag_redraw()

        if event.shift and event.type == 'SLASH' and event.value == 'PRESS':
            self.current_string = self.current_string + '?'

        elif event.type in KEYBOARD and event.value == 'PRESS':
            if event.type in CAPS or event.type in remap_nums.keys() or event.type == 'SPACE':

                if event.type == 'SPACE':
                    final_value = ' '
                else:
                    final_value = remap_nums.get(event.type, event.type.lower())

                self.current_string = self.current_string + final_value
            elif event.type == 'BACK_SPACE':
                has_length = len(self.current_string)
                self.current_string = self.current_string[:-1] if has_length else ''
            elif event.type in {'UP_ARROW', 'DOWN_ARROW'}:
                self.new_direction = {'UP_ARROW': -1, 'DOWN_ARROW': 1}.get(event.type)
                self.current_index += self.new_direction

            flat_node_cats['list_return'] = results = return_search_results(self.current_string)
            if results and len(results):
                self.current_index %= len(results)

        elif event.type in {'LEFTMOUSE', 'RET'}:
            SpaceNodeEditor.draw_handler_remove(self._handle, 'WINDOW')

            if route_as_nodelookup(self, context):
                pass
            elif route_as_macro(self, context):
                pass
            elif route_as_websearch(self):
                pass
           
            print('completed')
            flat_node_cats['list_return'] = []
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            SpaceNodeEditor.draw_handler_remove(self._handle, 'WINDOW')
            flat_node_cats['list_return'] = []
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}


    def invoke(self, context, event):
        if context.area.type == 'NODE_EDITOR':

            # [ ] make current session history available, maybe with ctrl+up/down ?
            # [ ] make longterm session history available?

            # unusually, if this is not set the operator seems to behave like it remembers the last string.
            self.current_string = ""  

            flat_node_cats['results'] = make_flat_nodecats()
            start_position = 20, 20   # event.mouse_region_x, event.mouse_region_y
            args = (self, context, start_position)
            self._handle = SpaceNodeEditor.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_PIXEL')
            
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "NODE_EDITOR not found, cannot run operator")
            return {'CANCELLED'}


classes = [XBCNodeViewConsole,]
register, unregister = bpy.utils.register_classes_factory(classes)

