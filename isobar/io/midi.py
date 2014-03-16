import rtmidi

import random
import time

from isobar.note import *

MIDIIN_DEFAULT = "IAC Driver A"
MIDIOUT_DEFAULT = "IAC Driver A"


class MidiIn:
	def __init__(self, target = MIDIOUT_DEFAULT):
		self.midi = rtmidi.MidiIn()
		self.debug = False
		self.clocktarget = None

		ports = self.midi.get_ports()
		if len(ports) == 0:
			raise Exception, "No MIDI output ports found"

		for index, name in enumerate(ports):
			if name == target:
				print "Found MIDI input (%s)" % name
				self.midi.open_port(index)

		if self.midi is None:
			print "Could not find MIDI source %s, using default" % target
			self.midi.open_port(0)

	def callback(self, message, timestamp):
		print "message %s" % message
		data_type, data_note, data_vel = tuple(message)
		if data_type == 248:
			if self.clocktarget is not None:
				self.clocktarget.tick()
		elif data_type == 250:
			# TODO: is this the right midi code?
			print "RESET"
			if self.clocktarget is not None:
				self.clocktarget.reset_to_beat()
		elif data_type & 0x90:
			# note on
			# print "%d (%d)" % (data_note, data_vel)
			pass 
		# print "%d %d (%d)" % (data_type, data_note, data_vel)


	def run(self):
		self.midi.set_callback(self.callback)

	def poll(self):
		""" used in markov-learner -- can we refactor? """
		message = self.midi.get_message()
		if not message:
			return

		print message
		data_type, data_note, data_vel = message[0]

		if (data_type & 0x90) > 0 and data_vel > 0:
			# note on
			return Note(data_note, data_vel)

	def close(self):
		del self.midi


class MidiOut:
	def __init__(self, target = MIDIOUT_DEFAULT):
		self.midi = rtmidi.MidiOut()
		self.debug = False

		ports = self.midi.get_ports()
		if len(ports) == 0:
			raise Exception, "No MIDI output ports found"

		for index, name in enumerate(ports):
			if name == target:
				print "Found MIDI output (%s)" % name
				self.midi.open_port(index)

		if self.midi is None:
			print "Could not find MIDI target %s, using default" % target
			self.midi.open_port(0)

	def tick(self, ticklen):
		pass

	def noteOn(self, note = 60, velocity = 64, channel = 0):
		if self.debug:
			print "channel %d, noteOn: %d" % (channel, note)
		self.midi.send_message([ 0x90 + channel, int(note), int(velocity) ])

	def noteOff(self, note = 60, channel = 0):
		if self.debug:
			print "channel %d, noteOff: %d" % (channel, note)
		self.midi.send_message([ 0x80 + channel, int(note), 0 ])

	def allNotesOff(self, channel = 0):
		if self.debug:
			print "channel %d, allNotesOff"
		for n in range(128):
			self.noteOff(n, channel)

	def control(self, control = 0, value = 0, channel = 0):
		# print "*** [CTRL] channel %d, control %d: %d" % (channel, control, value)
		if self.debug:
			print "channel %d, control %d: %d" % (channel, control, value)
		self.midi.send_message([ 0xB0 + channel, int(control), int(value) ])

	def __destroy__(self):
		del self.midi
