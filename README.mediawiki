=Mydy=

Mydy is a Python MIDI IO library, and a fork of <a href="https://github.com/vishnubob/python-midi">python-midi</a> by Giles Hall. Mydy is specifically re-written for Python 3, and does not support Python 2.

Mydy supports vectorized operations on MIDI Patterns, Tracks and Events by overloading builtin operators.

==Features==

Features specific to Mydy:

* Designed for Python 3
* Transpose patterns/tracks/events using the <code>+ and -</code> operators
* Change the speed of patterns/tracks/events using the <code>* and /</code> operators
* Change velocity of patterns/tracks/events using the <code>>> and <<</code> operators
* Extend a track with copies of itself using the <code>**</code> operator
* Map functions of events over tracks with the <code>map</code> method

Features from the base python-midi:

* High level class types that represent individual MIDI events.
* A multi-track aware container, that allows you to manage your MIDI events.
* A reader and writer, so you can read and write your MIDI tracks to disk.

==Installation==

After cloning the directory, 
<pre>
python setup.py install
</pre>

===Examine a MIDI File===

To examine the contents of a MIDI file run

<pre>
$ mididump.py mary.mid
</pre>

This will print out a representation of "Mary had a Little Lamb" as executable python code.

==Example Usage==

===Building a MIDI File from scratch===

It is easy to build a MIDI track from scratch.

<pre>
import midi
# Instantiate a MIDI Pattern (contains a list of tracks)
pattern = midi.Pattern()
# Instantiate a MIDI Track (contains a list of MIDI events)
track = midi.Track()
# Append the track to the pattern
pattern.append(track)
# Instantiate a MIDI note on event, append it to the track
on = midi.NoteOnEvent(tick=0, velocity=20, pitch=midi.G_3)
track.append(on)
# Instantiate a MIDI note off event, append it to the track
off = midi.NoteOffEvent(tick=100, pitch=midi.G_3)
track.append(off)
# Add the end of track event, append it to the track
eot = midi.EndOfTrackEvent(tick=1)
track.append(eot)
# Print out the pattern
print pattern
# Save the pattern to disk
midi.write_midifile("example.mid", pattern)
</pre>

A MIDI file is represented as a hierarchical set of objects.  At the top is a
Pattern, which contains a list of Tracks, and a Track is is a list of MIDI
Events.  

The MIDI Pattern class inherits from the standard python list, so it supports
all list features such as append(), extend(), slicing, and iteration.  Patterns
also contain global MIDI metadata: the resolution and MIDI Format.

The MIDI Track class also inherits from the standard python list.  It does not
have any special metadata like Pattern, but it does provide a few helper
functions to manipulate all events within a track.

There are 27 different MIDI Events supported.  In this example, three different
MIDI events are created and added to the MIDI Track:  

# The NoteOnEvent captures the start of note, like a piano player pushing down on a piano key.  The tick is when this event occurred, the pitch is the note value of the key pressed, and the velocity represents how hard the key was pressed.

# The NoteOffEvent captures the end of note, just like a piano player removing her finger from a depressed piano key.  Once again, the tick is when this event occurred, the pitch is the note that is released, and the velocity has no real world analogy and is usually ignored.  NoteOnEvents with a velocity of zero are equivalent to NoteOffEvents.

# The EndOfTrackEvent is a special event, and is used to indicate to MIDI sequencing software when the song ends.  With creating Patterns with multiple Tracks, you only need one EndOfTrack event for the entire song.  Most MIDI software will refuse to load a MIDI file if it does not contain an EndOfTrack event.

You might notice that the EndOfTrackEvent has a tick value of 1.  This is
because MIDI represents ticks in relative time.  The actual tick offset of the
MidiTrackEvent is the sum of its tick and all the ticks from previous events.
In this example, the EndOfTrackEvent would occur at tick 101 (0 + 100 + 1).

====Side Note: What is a MIDI Tick?====

The problem with ticks is that they don't give you any information about when
they occur without knowing two other pieces of information, the resolution, and
the tempo.  The code handles these issues for you so all you have to do is
think about things in terms of milliseconds, or ticks, if you care about the beat.  

A tick represents the lowest level resolution of a MIDI track.  Tempo is always
analogous with Beats per Minute (BPM) which is the same thing as Quarter notes
per Minute (QPM).  The Resolution is also known as the Pulses per Quarter note
(PPQ).  It analogous to Ticks per Beat (TPM).

Tempo is set by two things.  First, a saved MIDI file encodes an initial
Resolution and Tempo.  You use these values to initialize the sequencer timer.
The Resolution should be considered static to a track, as well as the
sequencer.  During MIDI playback, the MIDI file may have encoded sequenced
(that is, timed) Tempo change events.  These events will modulate the Tempo at
the time they specify.  The Resolution, however, can not change from its
initial value during playback.

Under the hood, MIDI represents Tempo in microseconds.  In other words, you
convert Tempo to Microseconds per Beat.  If the Tempo was 120 BPM, the python
code to convert to microseconds looks like this:

<pre>
>>> 60 * 1000000 / 120
500000
</pre>

This says the Tempo is 500,000 microseconds per beat.  This, in combination
with the Resolution, will allow you to convert ticks to time.  If there are
500,000 microseconds per beat, and if the Resolution is 1,000 than one tick is
how much time?

<pre>
>>> 500000 / 1000
500
>>> 500 / 1000000.0
0.00050000000000000001
</pre>

In other words, one tick represents .0005 seconds of time or half a
millisecond.  Increase the Resolution and this number gets smaller, the inverse
as the Resolution gets smaller.  Same for Tempo.

Although MIDI encodes Time Signatures, it has no impact on the Tempo.  However,
here is a quick refresher on Time Signatures:

http://en.wikipedia.org/wiki/Time_signature

===Reading our Track back from Disk===

It's just as easy to load your MIDI file from disk.

<pre>
import midi
pattern = midi.read_midifile("example.mid")
print pattern
</pre>

==Website, support, bug tracking, development etc.==

You can find the latest code on the home page:
https://github.com/jameswenzel/mydy/

You can also check for known issues and submit new ones to the
tracker: https://github.com/jameswenzel/mydy/issues/

