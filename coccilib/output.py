import pygtk
import gtk, gobject
import coccilib.coccigui
import coccilib.coccigui.coccigui
from threading import Thread, Lock
import time

class Output:
	"""In order to implement an output class for use with Coccinelle,
	one can inherit from this class and overload register_match with
	the same number of arguments.

	include_match will be overwritten by inheriting from your actual
	class, and thus if your class is a.b.C then Coccinelle will create
	a Python class "class Coccinelle(a.b.C)" that hooks include_match
	into the O'Caml internals.
	"""
	def include_match(self, b):
		pass

	def register_match(self, include, messages):
		pass

	def combine(self, meta_variable, locations):
		meta_variable.location = locations[0]
		return meta_variable

class Console(Output):
	def __init__(self):
		pass

	def register_match(self, include, messages):
		self.include_match(include)
		if include:
			for variable, message in messages:
				print "%s:%s:%s: %s - %s" % (variable.location.file, variable.location.line, variable.location.column, message, variable)

class GtkRunner(Thread):
	def __init__(self):
		Thread.__init__(self)
		self.lock = Lock()
		self.rows = []

	def add_row(self, cocci, l):
		for i in xrange(0, len(l)):
			l[i] = (l[i][1], l[i][0].location.file, l[i][0].location.line, l[i][0].location.column)

		self.lock.acquire()
		try:
			self.rows.append((cocci, l))
		finally:
			self.lock.release()

	def has_row(self):
		self.lock.acquire()
		try:
			return len(self.rows) > 0
		finally:
			self.lock.release()

	def get_row(self):
		self.lock.acquire()
		try:
			return self.rows.pop(0)
		finally:
			self.lock.release()

	def update(self):
		while self.has_row():
			cocci, l = self.get_row()
			self.gui.add_result(cocci, l)
		gobject.timeout_add(1000, self.update)

	def run(self):
		self.gui = coccilib.coccigui.coccigui.pycocci()
		globals()['gtk_sock'] = self.gui
		gobject.timeout_add(1000, self.update)

		gtk.gdk.threads_init()
		gtk.gdk.threads_enter()

		gtk.main()

		gtk.gdk.threads_leave()

		globals().pop('gtk_thread')
		globals().pop('gtk_sock')

class Gtk(Output):
	def check_availability(self):
		if not globals().has_key('gtk_sock'):
			t = GtkRunner()
			globals()['gtk_thread'] = t
			globals()['gtk_thread'].start()
			time.sleep(2)

	def register_match(self, include, messages):
		self.check_availability()

		self.include_match(include)
		if include:
			globals()['gtk_thread'].add_row(self.cocci_file, messages)
