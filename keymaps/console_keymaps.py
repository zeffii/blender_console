import os
import bpy


nodeview_keymaps = []


def add_keymap():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')

        # ctrl+F        ( show the nodeview console)
        kmi = km.keymap_items.new('node.xbc_nodeview_console', 'F', 'PRESS', ctrl=True)
        nodeview_keymaps.append((km, kmi))


def remove_keymap():

    for km, kmi in nodeview_keymaps:
        try:
            km.keymap_items.remove(kmi)
        except Exception as e:
            err = repr(e)
            if "cannot be removed from 'Node Editor'" in err:
                print('keymaps for Node Editor already removed by another add-on')
                break

    nodeview_keymaps.clear()