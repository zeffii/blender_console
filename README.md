README.md
=========

An interactive command prompt for Blender nodeview. Originally written for B2.74, but updated to work in B2.93+. At the moment it only uses `blf` module because the `bgl` module's capacity to use openGL in direct mode was droppen in 2.93.

There are limitations to the bpy UI features that provide search boxes, this add-on explores alternative visions of text-input to call operators and return a variety of results.

When enabled the keymap for nodeview is `shift + semicolon`, it will spawn a `>>>`. Then you type a string or part of a command
