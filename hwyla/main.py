import sys
import itertools
import gi
import cairo
import pyclip
from datetime import datetime
import model

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gdk, Gtk, Adw


class MainWindow(Gtk.ApplicationWindow):
    CANVAS_WIDTH = 512
    CANVAS_HEIGHT = 512

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_default_size(612, 600)
        self.container = Gtk.Box()
        self.set_child(self.container)
        self._active_stroke = False
        self.symbol_store = Gtk.ListStore(int, str)
        self.symbol_list = Gtk.TreeView(model=self.symbol_store)
        self.symbol_list.set_size_request(200, -1)
        self.symbol_list.set_vexpand(True)
        text_renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Symbol", text_renderer, text=1)
        self.symbol_list.append_column(column)
        selection = self.symbol_list.get_selection()
        selection.set_mode(Gtk.SelectionMode.SINGLE)
        selection.connect("changed", self._copy_selection)

        self.character_canvas = Gtk.DrawingArea()
        self.character_canvas.set_draw_func(self._draw, None)
        self.character_canvas.set_size_request(
            MainWindow.CANVAS_WIDTH, MainWindow.CANVAS_HEIGHT
        )
        self.character_canvas.set_vexpand(True)
        self.character_canvas.set_hexpand(True)
        self.container.append(self.character_canvas)
        self.container.append(self.symbol_list)
        evk = Gtk.GestureClick.new()
        evk.connect("pressed", self._initiate_stroke)
        evk.connect("released", self._deactivate_stroke)
        self.character_canvas.add_controller(evk)
        self.classifier = model.Classifier()
        motion = Gtk.EventControllerMotion.new()
        motion.connect("motion", self._stroke)
        self.character_canvas.add_controller(motion)
        self._cur_stroke = []
        self._accumulated_path = []
        self.header_bar = Gtk.HeaderBar()
        self.reset_button = Gtk.Button()
        self.reset_button.set_icon_name("view-refresh")
        self.reset_button.connect("clicked", self._reset_canvas)
        self.header_bar.pack_start(self.reset_button)
        self.set_titlebar(self.header_bar)

    def _copy_selection(self, selection):
        model, iter = selection.get_selected()
        sel = model.get(iter, 1)[0]
        pyclip.copy(sel)

    def _reset_canvas(self, button):
        self._accumulated_path = []
        self._cur_stroke = []
        self.character_canvas.queue_draw()
        self.symbol_store.clear()

    def _draw_stroke(self, context, stroke):
        _, prev_x, prev_y = stroke[0]
        for _, x, y in stroke[1:]:
            context.move_to(prev_x, prev_y)
            context.line_to(x, y)
            prev_x, prev_y = x, y
        context
        context.stroke()

    def _draw(self, character_canvas, context, w, h, data):
        context.set_source_rgb(1, 1, 1)
        context.paint()
        context.set_source_rgb(0, 0, 0)
        context.set_line_width(10)
        context.set_line_cap(cairo.LINE_CAP_ROUND)
        for stroke in self._accumulated_path:
            self._draw_stroke(context, stroke)
        if self._cur_stroke:
            self._draw_stroke(context, self._cur_stroke)

    def _initiate_stroke(self, gesture, data, x, y):
        self._active_stroke = True

    def _stroke(self, motion, x, y):
        if self._active_stroke:
            self._cur_stroke.append((datetime.now().timestamp() * 1e3, x, y))
            self.character_canvas.queue_draw()

    def _deactivate_stroke(self, gesture, data, x, y):
        self._active_stroke = False
        self._accumulated_path.append(self._cur_stroke)
        self._cur_stroke = []
        classes = self.classifier.classify(
            list(itertools.chain(*self._accumulated_path)), k=10
        )
        self.symbol_store.clear()
        for i, character in enumerate(classes):
            self.symbol_store.insert_with_values(-1, (0, 1), (i, character))


class Hwyla(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect("activate", self.on_activate)

    def on_activate(self, app):
        self.win = MainWindow(application=app)
        self.win.present()


if __name__ == "__main__":
    app = Hwyla(application_id="com.github.triagle.hwyla")
    app.run(sys.argv)
