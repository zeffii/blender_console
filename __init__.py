# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you may redistribute it, and/or
# modify it, under the terms of the GNU General Public License
# as published by the Free Software Foundation - either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, write to:
#
#   the Free Software Foundation Inc.
#   51 Franklin Street, Fifth Floor
#   Boston, MA 02110-1301, USA
#
# or go online at: http://www.gnu.org/licenses/ to view license options.
#
# ***** END GPL LICENCE BLOCK *****

bl_info = {
    "name": "blender console",
    "author": "Dealga McArdle",
    "version": (0, 1, 0),
    "blender": (2, 7, 8),
    "location": "Console - keystrokes",
    "description": "Adds feature to intercept console input and parse accordingly.",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Nodeview"}

if 'bpy' in globals():
    msg = ": detected reload event! cool."
    print(__package__ + msg)

    if 'xbc_nodeview_console' in globals():
        import imp
        imp.reload(xbc_nodeview_console)
        imp.reload(xbc_nodeview_console_routing)
        imp.reload(xbc_nodeview_macro_routing)
        imp.reload(keymaps.console_keymaps)
        print_addon_msg(__package__, ': reloaded')


else:
    from . import xbc_operators
    from .keymaps import console_keymaps

import bpy


def register():
    bpy.utils.register_module(__name__)
    console_keymaps.add_keymap(__package__)


def unregister():
    console_keymaps.remove_keymap()
    bpy.utils.unregister_module(__name__)

