import wx
from typing import List, Set, Dict, Tuple, Optional
from view.display_model import GraphNode, UmlNode, CommentNode
from gui.node_edit_multi_purpose import node_edit_multi_purpose

MENU_ID_SHAPE_PROPERTIES = wx.NewIdRef()
MENU_ID_BEGIN_LINE = wx.NewIdRef()
MENU_ID_CANCEL_LINE = wx.NewIdRef()

class ShapeMenu:
    def __init__(self, frame, shapehandler):
        self.frame = frame
        self.shapehandler = shapehandler  # UmlShapeHandler

        self.popupmenu = wx.Menu()  # This is the popup menu to which we attach menu items
        self.submenu = wx.Menu()  # This is the sub menu within the popupmenu
        self.accel_entries : List[wx.AcceleratorEntry] = []

    def BuildPopupMenuItems(self):
        """
        Builds the MenuItems used in the r.click popup and also builds the accelerator table.
        Returns: -

        Fun Facts
        ---------
        Keyboard shortcuts in wxPython are actually menu events
        (i.e. wx.EVT_MENU), probably because the shortcuts are usually also a menu item.
        Id's seems to be 'broadcast' and any handler bound to that id gets called
        wx.EVT_MENU is an object, not an id.  All menu events and presumably
        key events emit this event, and the 'id' is needed to distinguish between the events.

        Accelerator tables work using keycodes and menu/key 'event' int ids - they do not involve
        menuitem objects or any other object, only ids.  There is only one global accelerator table
        per frame.
        https://wxpython.org/Phoenix/docs/html/wx.AcceleratorEntryFlags.enumeration.html#wx-acceleratorentryflags

        On Binding
        ----------
        https://wxpython.org/Phoenix/docs/html/wx.EvtHandler.html#wx.EvtHandler.Bind

        third parameter is 'source'   <--- this is not an id, but an object e.g. a frame, a menuitem
        Sometimes the event originates from a different window than self, but you still want
        to catch it in self

        fourth parameter is 'id' – Used to specify the event source by ID instead of instance.

        ** Initially this didn't make sense.  if the event source is a 'window', which means a
        canvas or control etc. a frame, a menuitem etc. then how can you alternatively
        refer to that 'window' by id?
        do windows have id's?  I thought id's were the pseudo 'events' that get broadcast
        and bound to.
        ** ANSWER: Source is not an id - its an object e.g. a frame, a menuitem

        and the window/control.Bind() construct suggests that the id is expected to come
        from that window (AHA which makes sense re the definition above of 'source')

        OBJ.Bind(event_type, handler, source)
        but why bother with source - you always specify where events come from by the OBJ
        and you can bind to any destination with the handler method.  what does it mean to
        specify both source and OBJ, as the destination is always 'handler' !
        Why not just always have OBJ as your source?
        Perhaps menuitem.Bind() wouldn't work? as the events are coming from frame?  e.g.
        accelerator key id's come from the frame.  main menu event come from the frame.
        Menuitem event would surely come from the menuitem?

        OBJ.Bind(event_type, handler, source)
        OBJ.Bind(event_type, handler, id=integer_id)
        I thus think OBJ and source are both places where events 'come from'.  Specifying
        both means you can get them from either e.g. a frame or from a menuitem, if you had
        specified a menuitem as source.
        Presumably one doesn't override the other?  In other words you can get events from
        both places, not just 'source'.?
        Perhaps menuitems don't have a Bind() method, so you have to do it this way, and source
        does indeed override.  CONFIRMED
            AttributeError: 'MenuItem' object has no attribute 'Bind'
        I wonder what 'propagation', if any, happens

        OBJ.Bind(event_type, handler, integer_id)
        only seems to work with pre-allocated ids or wx.NewIdRef() but not wx.ID_ANY which is
        -1 which is strange since the passing of wx.ID_ANY into .Append() works?
        Perhaps the adding to the menu and the binding need different thinking.
        YES
        The creation of a menuitem via .Append(wx.ID_ANY, text) will give that menu item
        an id of -1 which means how do we get to it?  Well the Bind() with the menu item as the
        third parameter which is the 'source' allows the Bind to work and "receive" from the
        menuitem even though the id is generically wx.ID_ANY -1
        But if we don't specify the 'source' then we must rely on a general broadcast of the id
        and thus we need a specific id to distinguish on.  Its kind of making sense now.

        If you want both a menu item and an accelerator then you need to use a unique id
        binding technique, not 'source' based, because you can't have accelerator tables
        broadcasting wx.ID_ANY -1 everywhere, nobody would be able to tell them apart.
        How I learned this:
        At one stage I thought I would be tricky
            if not id:
                id = wx.NewIdRef() if keycode_only else wx.ID_ANY
        then the following:
            if keycode_only:
                # Need a unique id in Bind() because id broadcast from frame
                self.frame.Bind(wx.EVT_MENU, method, id=id)
            else:
                # Can use a generic wx.ID_ANY -1 id because binding directly to menuitem thus don't need id
                to_menu = self.submenu if submenu else self.popupmenu
                item = to_menu.Append(id, text)
                self.frame.Bind(wx.EVT_MENU, method, source=item)
            if key_code:
                entry = wx.AcceleratorEntry()
                entry.Set(wx.ACCEL_NORMAL, key_code, id)
                self.accel_entries.append(entry)
        BUT the wx.ID_ANY -1 in the accelerator table didn't trigger anything!

        Perhaps 'source=menuitem' binding to menu items is the only correct way cos
            to_menu = self.submenu if submenu else self.popupmenu
            item = to_menu.Append(id, text)
         1. self.frame.Bind(wx.EVT_MENU, method, source=item)   <- WORKS
         2. self.frame.Bind(wx.EVT_MENU, method, id=id)    <- DOESN'T TRIGGER THE HANDLER
        AH BUT it WORKS when the ids are unique it does, but they must be freshly allocated
        each time the menu it built, for some reason?  Otherwise the handlers don't get called?
        Possibly the 'shape' isn't in the broadcast zone of the frame - but it is, when using
        freshly allocated ids.
        Even when using a unique, pre-allocated id, the (2.) technique doesn't work?
        Even when the menuitem in question is getting a freshly allocated id, if the surrounding
        menuitems are reusing ids, no accelerator shortcuts work and I even see that CMD Q
        of the main menu stops working - something seriously screwy here.

        Here is an example illustrating the above comment.
            if not id or id == wx.ID_ANY:
                # Accelerator tables need unique ids, whereas direct menuitem binding
                # with Bind(....source=menuitem)
                # don't care about ids and can thus use wx.ID_ANY (which is always -1)
                id = wx.NewIdRef() if key_code or keycode_only else wx.ID_ANY

            # id = wx.NewIdRef()  <--- need to uncomment this to make the (2) binding technique work
            if key_code:
                assert id != wx.ID_ANY
            if keycode_only:
                assert id != wx.ID_ANY
            print(f"id={id} used for {text}")

            if keycode_only:
                self.frame.Bind(wx.EVT_MENU, method, id=id)
            else:
                to_menu = self.submenu if submenu else self.popupmenu
                item = to_menu.Append(id, text)
                # self.frame.Bind(wx.EVT_MENU, method, source=item) # (1)
                self.frame.Bind(wx.EVT_MENU, method, id=id)  # (2) doesn't work unless all ids fresh

                # self.frame.Bind(wx.EVT_UPDATE_UI, self.TestUpdateUI, item)  # future update ?

            if key_code:
                entry = wx.AcceleratorEntry()
                entry.Set(wx.ACCEL_NORMAL, key_code, id)
                self.accel_entries.append(entry)

        Summary
        -------
        Thus when creating a menu item to_menu.Append(id, text) you can specify wx.ID_ANY -1
        as the id, but this means you MUST do a Bind() with the third parameter
        which is the 'source' set to the menuitem that was just created.
        A kind of 'hard wiring / direct broadcast' which doesn't rely on unique ids.
            item = to_menu.Append(wx.ID_ANY, text)
            self.frame.Bind(wx.EVT_MENU, method, source=item)

        When creating a menu item with unique ids
        (pre-allocated ids or wx.NewIdRef() but not wx.ID_ANY) you have the option in the Bind
        to not specify the 'source' and just to specify the id.
        Warning, the third parameter is 'source', if you want to specify id, that's the
        fourth parameter, so you are typically going to need to use a keyword arg id= approach.
            id = wx.NewIdRef()               <-- this could be a pre-allocated constant
            item = to_menu.Append(id, text)              <--- id specified
            self.frame.Bind(wx.EVT_MENU, method, id=id)  <--- same id specified

        """

        self.popupmenu = wx.Menu()  # This is the popup menu to which we attach menu items
        self.submenu = wx.Menu()  # This is the sub menu within the popupmenu
        self.accel_entries : List[wx.AcceleratorEntry] = []

        def add_menuitem(text, method, id=None, submenu=False, key_code=None, keycode_only=False):

            def check_id(id):
                """
                Accelerator tables need unique ids, whereas direct menuitem binding with Bind(...source=menuitem)
                doesn't care about ids and can thus use wx.ID_ANY (which is always -1)
                """
                if not id or id == wx.ID_ANY:
                    id = wx.NewIdRef() if key_code or keycode_only else wx.ID_ANY
                return id

            item: wx.MenuItem = None
            id = check_id(id)

            if keycode_only:
                self.frame.Bind(wx.EVT_MENU, method, id=id)
            else:
                to_menu = self.submenu if submenu else self.popupmenu
                item = to_menu.Append(id, text)
                self.frame.Bind(wx.EVT_MENU, method, source=item)
                # self.frame.Bind(wx.EVT_UPDATE_UI, self.TestUpdateUI, item)  # future update ?

            if key_code:
                entry = wx.AcceleratorEntry()
                entry.Set(wx.ACCEL_NORMAL, key_code, id)
                self.accel_entries.append(entry)
                # print("accel built", entry, key_code, id)

            return item

        def add_submenu_to_popup():
            self.popupmenu.Append(wx.ID_ANY, "Draw Line", self.submenu)

        def add_separator():
            self.popupmenu.AppendSeparator()

        def add_properties():
            add_menuitem("Properties...\ts",
                         self.OnNodeProperties,
                         id=MENU_ID_SHAPE_PROPERTIES,
                         key_code=ord('S'),
                         )

        def add_from(keycode_only=False):
            item : wx.MenuItem = add_menuitem(
                "Begin - Remember selected class as FROM node (for drawing lines)\tq",
                self.OnDrawBegin,
                id=MENU_ID_BEGIN_LINE,
                submenu=True,
                key_code=ord('Q'),
                keycode_only=keycode_only
            )
            # item.Enable(False)  # hmm, accelerator still fires :-(

        def add_from_cancel(keycode_only=False):
            add_menuitem(
                "Cancel Line Begin\tx",
                self.OnCancelDrawBegin,
                id=MENU_ID_CANCEL_LINE,
                submenu=True,
                key_code = ord('X'),
                keycode_only = keycode_only
            )

        def add_association_edge():
            add_menuitem(
                "End - Draw Line TO selected comment/class (association - dashed)\ta",
                self.OnDrawEnd3,
                submenu = True
            )

        def add_generalise_composition_edges():
            add_menuitem(
                "End - Draw Line TO selected class (composition)\tw",
                self.OnDrawEnd1,
                submenu=True
            )
            add_menuitem(
                "End - Draw Line TO selected class (generalisation)\te",
                self.OnDrawEnd2,
                submenu = True
            )

        def add_reset_image_size():
            add_menuitem("Reset Image Size", self.OnResetImageSize)

        def add_delete():
            add_menuitem("Delete\tDel", self.OnRightClickDeleteNode)

        def add_cancel():
            add_menuitem("Cancel", self.OnPopupMenuCancel)


        shape = self.shapehandler.GetShape()
        from_node : GraphNode = self.shapehandler.umlcanvas.new_edge_from
        is_bitmap = shape.__class__.__name__ == "BitmapShapeResizable"
        is_comment = isinstance(shape.node, CommentNode)
        is_umlclass = isinstance(shape.node, UmlNode)
        assert not is_umlclass == (is_comment or is_bitmap)
        started_connecting = from_node != None
        from_is_comment = isinstance(from_node, CommentNode)

        if is_umlclass or is_comment:
            add_properties()
            add_separator()
            if not from_node:
                add_from()
            else:
                add_from(keycode_only=True)  # always allow begin line draw as shortcut

        if is_umlclass:
            if started_connecting:
                add_association_edge()
                if not from_is_comment:
                    add_generalise_composition_edges()
            else:
                pass  # don't offer 'to' menu choices cos haven't started connecting yet
        elif is_comment:
            if started_connecting:
                add_association_edge()
            else:
                pass  # don't offer 'to' menu choices cos haven't started connecting yet
        elif is_bitmap:
            add_reset_image_size()
        else:
            raise RuntimeError("Right click on unknown shape")

        if is_umlclass or is_comment:
            if from_node:
                add_from_cancel()
            else:
                add_from_cancel(keycode_only=True)  # always allow begin line cancel as shortcut

        add_submenu_to_popup()

        add_separator()
        add_delete()
        add_separator()
        add_cancel()

        accel_tbl = wx.AcceleratorTable(self.accel_entries)
        self.frame.SetAcceleratorTable(accel_tbl)

        # wx.GetApp().Bind(wx.EVT_UPDATE_UI, self.TestUpdateUI, id=506)
        # self.frame.Bind(wx.EVT_UPDATE_UI, updateUI, item)
        #
        # def doBind(item, handler, updateUI=None):
        #     self.Bind(wx.EVT_TOOL, handler, item)
        #     if updateUI is not None:
        #         self.Bind(wx.EVT_UPDATE_UI, updateUI, item)
        #
        # doBind(tbar.AddTool(-1, images._rt_bold.GetBitmap(), isToggle=True, shortHelpString="Bold"),
        #        self.OnBold,
        #        self.OnUpdateBold)

    # Handy Redirections
    
    def GetShape(self):
        return self.shapehandler.GetShape()

    def focus_shape(self):
        self.shapehandler.focus_shape()

    # Handlers
    
    def OnNodeProperties(self, event):
        node_edit_multi_purpose(self.GetShape(), self.shapehandler.app)

    def OnDrawBegin(self, event):
        print("OnDrawBegin")
        # if not is_item_enabled(event.GetId()):
        #     print("OnDrawBegin THWARTED")
        #     return
        self.GetShape().GetCanvas().NewEdgeMarkFrom()
        # self._update_line_state()
        self.focus_shape()  # rebuild the accelerator table and menus cos situation changed

    def OnCancelDrawBegin(self, event):
        self.GetShape().GetCanvas().OnCancelLine(event)  # delegate to canvas handler - event dodgy
        self.focus_shape()  # rebuild the accelerator table and menus cos situation changed

    def OnDrawEnd1(self, event):
        self.GetShape().GetCanvas().NewEdgeMarkTo(edge_type="composition")
        # self._update_line_state()

    def OnDrawEnd2(self, event):
        self.GetShape().GetCanvas().NewEdgeMarkTo(edge_type="generalisation")
        # self._update_line_state()

    def OnDrawEnd3(self, event):
        self.GetShape().GetCanvas().NewEdgeMarkTo(edge_type="association")
        # self._update_line_state()

    def OnResetImageSize(self, event):
        shape = self.GetShape()
        shape.ResetSize()
        # shape.GetCanvas().Refresh(False)   # don't seem to need since SelectNodeNow() might be doing it for us
        shape.GetCanvas().SelectNodeNow(shape)
        self.UpdateStatusBar(shape)

    def OnRightClickDeleteNode(self, event):
        self.app.run.CmdNodeDelete(self.GetShape())

    def OnPopupMenuCancel(self, event):
        pass


# # Central place to check whether menu is enabled.  Can be checked by handlers
# popup_menu_central : Dict[int, bool] = {
#     MENU_ID_SHAPE_PROPERTIES: True,
#     MENU_ID_BEGIN_LINE: True,
# }
#
# def is_item_enabled(id):
#     print(f"checking is item {id} is enabled")
#     return popup_menu_central[id]
#
# def set_item_state(id, state):
#     popup_menu_central[id] = state
#
# def accelerate(frame):
#     """ accelerator stuff
#     this is what is called when
#     """
#     accel_tbl = wx.AcceleratorTable([
#         (wx.ACCEL_CTRL, ord('Z'), MENU_ID_SHAPE_PROPERTIES),
#         (wx.ACCEL_NORMAL, ord('Q'), MENU_ID_BEGIN_LINE),
#     ])
#     frame.SetAcceleratorTable(accel_tbl)
#
#
#     frame.Bind(wx.EVT_MENU, OnNodeProperties, id=MENU_ID_SHAPE_PROPERTIES)
#     frame.Bind(wx.EVT_MENU, OnDrawBegin, id=MENU_ID_BEGIN_LINE)
#
# def focus_canvas(frame, canvas):
#     """ accelerator stuff
#     this is what is called when shape is deselected
#     the only acceleration should be to cancel the pending line drawing
#
#     """
#     accel_tbl = wx.AcceleratorTable([
#         (wx.ACCEL_NORMAL, ord('X'), MENU_ID_CANCEL_LINE),
#     ])
#     frame.SetAcceleratorTable(accel_tbl)
#
#     frame.Bind(wx.EVT_MENU, OnCancelLine, id=MENU_ID_SHAPE_PROPERTIES)
#     frame.Bind(wx.EVT_MENU, OnDrawBegin, id=MENU_ID_BEGIN_LINE)
#
# def OnNodeProperties(event):
#     print("global OnNodeProperties")
#
# def OnDrawBegin(event):
#     print("global OnDrawBegin")



# class PopupMenuItems:
#     """
#     Builds the MenuItems used in the r.click popup and stores them
#     which allows them to be accessed later, to check if they are enabled or not
#     by the handler.
#
#     The handler unfortunately, has to check if its associated menuitem is enabled
#     since the accelerator key for a menu item will trigger regardless.
#     """
#
#     def __init__(self, frame):
#         self.frame = frame
#         self.menu_items : List[wx.MenuItem] = []
#         self.sub_menu_items : List[wx.MenuItem] = []  # currently support one submenu for popup
#         self.accel_entries : List[wx.AcceleratorEntry] = []
#
#     def create(self, text, method, update_method=None, is_sub_menu=False, key_code=None, help=""):
#         """
#         Creates a menu item but does not add it to any menu - this will be done later
#
#         Re update_method - whenever a menu is about to be presented to the user, 'update_method'
#         is called, per item/binding. In the handler you can
#
#             - if the update handler is specific to each item, then you already know which item it caters to
#             - if the update handler is used by more than one menu item, check event.GetId()
#             - event.SetText(text) sets the text of the menuitem
#             - event.Enable(False) enables or disabled the menuitem
#
#         returns: menu item
#         """
#
#         item = wx.MenuItem(parentMenu=None,  # None cos item is going to be added to the menu later
#                            id=wx.ID_ANY,
#                            text=text,
#                            subMenu=None,
#                            helpString=help)
#
#         self.frame.Bind(wx.EVT_MENU, method, item)
#
#         if update_method:
#             self.frame.Bind(wx.EVT_UPDATE_UI, update_method, item)
#
#         if key_code:
#             # https://wxpython.org/Phoenix/docs/html/wx.AcceleratorEntryFlags.enumeration.html#wx-acceleratorentryflags
#             entry = wx.AcceleratorEntry()
#             entry.Set(wx.ACCEL_NORMAL, key_code, item.GetId())
#             self.accel_entries.append(entry)
#
#         if is_sub_menu:
#             self.sub_menu_items.append(item)
#         else:
#             self.menu_items.append(item)
#
#         return item
#
#     def finish(self):
#         accel_tbl = wx.AcceleratorTable(self.accel_entries)
#         # self.frame.SetAcceleratorTable(accel_tbl)
#
#     def find_by_text(self, text):
#         for item in self.menu_items + self.sub_menu_items:
#             if item.GetItemLabel() == text:
#                 return item
#         raise RuntimeError(f"Unknown menuitem with text '{text}' when searching through popup menuitems.")
#
#     def IsEnabled(self, id):
#         for item in self.menu_items + self.sub_menu_items:
#             if item.GetId() == id:
#                 return item.Enabled
#         raise RuntimeError(f"Unknown menuitem id {id} when searching through popup menuitems.")
#
#
# class ShapePopupMenuMgr(PopupMenuItems):
#
#     TXT_PROPERTIES = "Properties..."
#     TXT_BEGIN_LINE = "Begin Line\tZ"
#
#     def __init__(self, frame, uml_shape_handler):
#         super().__init__(frame)
#         self.popupmenu = wx.Menu()  # This is the popup menu to which we attach menu items
#         self.submenu = wx.Menu()  # This is the sub menu within the popupmenu
#         self.create_menu_items(uml_shape_handler)
#         self.finish()
#
#     def create_menu_items(self, uml_shape_handler):
#         """
#         Creates all menu items but does not assign them to menus.
#         All menu items trigger methods on the 'uml_shape_handler' object
#         """
#         self.create(
#             text=self.TXT_PROPERTIES,
#             method=uml_shape_handler.OnNodeProperties,
#             update_method=None,
#             is_sub_menu=False,
#             key_code=None,
#             help=""
#             )
#         self.create(
#             text=self.TXT_BEGIN_LINE,
#             method=uml_shape_handler.OnDrawBegin,
#             update_method=None,
#             is_sub_menu=True,
#             key_code=ord('Z'),
#             help=""
#             )
#
#
#     def clear(self):
#         self.popupmenu = wx.Menu()
#         self.submenu = wx.Menu()
#
#     # def finish(self):
#     #     super().finish()
#     #     # self.popupmenu.Append(wx.ID_ANY, "Subbbb", self.submenu, help="hacky line drawing stuff...")
#
#     # Add methods - call 'clear' then go for it to compose a menu
#
#     def add_separator(self):
#         self.popupmenu.AppendSeparator()
#
#     def add_properties(self):
#         self.popupmenu.Append(self.find_by_text(self.TXT_PROPERTIES))
#
#     def add_from(self):
#         self.submenu.Append(self.find_by_text(self.TXT_BEGIN_LINE))
