Getting started
===============

Since _libmapper_ uses GNU autoconf, getting started with the library
is the same as any other library on Linux; use `./configure` and then
`make` to compile it.  You'll need the `Java Developer Kit (JDK)` 
available if you want to compile the Java bindings.

Once you have libmapper installed, it can be imported into your program:

    import Mapper.*;

Overview of the API organization
================================

The libmapper API is is divided into the following sections:

* Signals
* Devices
* Admins
* Device database
* Signal database
* Connections database
* Links database
* Monitors

For this tutorial, the only sections to pay attention to are **Devices**
and **Signals**.  Use of **Admins** is reserved for providing custom networking configurations, and in general you don't need to worry about it.

**Monitors** and the various **database** modules are used to keep track of
what devices, signals and connections are on the network.  Devices do
not need to worry about this.  It is used mainly for creating user
interfaces for mapping design and will also not be covered in this tutorial.

Devices
=======

Creating a device
-----------------

To create a _libmapper_ device, it is necessary to provide a device
name to the constructor.  There is an initialization period after a
device is created where a unique ordinal is chosen to append to the
device name.  This allows multiple devices with the same name to
exist on the network.

If no other arguments are given, libmapper will randomly choose a port
to use for exchanging signal data.  If desired, a second argument setting
a specific "starting port" can be given, but the allocation algorithm will
possibly choose another port number close to it if the port is in use.

A third optional parameter of the constructor is an admin object.  It is
not necessary to provide this, but can be used to specify different
networking parameters, such as specifying the name of the network
interface to use.

An example of creating a device:

    final Mapper.Device dev = new Mapper.Device( "my_device" );

Polling the device
------------------

The device lifecycle looks like this, in terrible ASCII diagram art:

    creation --> poll --+--> destruction
                  |     |
                  +--<--+

In other words, after a device is created, it must be continuously
polled during its lifetime.

The polling is necessary for several reasons: to respond to administrative messages; to check for incoming signals.  Therefore even a device that does not have signals must be polled.  The user program must organize to have a timer or idle handler which can poll the device often enough.  The polling interval is not extremely sensitive, but should be 100 ms or less.  The more often it is polled, the faster it can handle incoming and outgoing
signals.

The `poll()` function can be blocking or non-blocking, depending on
how you want your application to behave.  It takes a number of
milliseconds during which it should do some work, or 0 if it should
check for any immediate actions and then return without waiting:

    int count = dev.poll( int block_ms );

An example of calling it with non-blocking behaviour:

    dev.poll( 0 );

If your polling is in the middle of a processing function or in
response to a GUI event for example, non-blocking behaviour is
desired.  On the other hand if you put it in the middle of a loop
which reads incoming data at intervals or steps through a simulation
for example, you can use `poll()` as your "sleep" function, so that
it will react to network activity while waiting.

It returns the number of messages handled, so optionally you could
continue to call it until there are no more messages waiting.  Of
course, you should be careful doing that without limiting the time it
will loop for, since if the incoming stream is fast enough you might
never get anything else done!

Note that an important difference between blocking and non-blocking
polling is that during the blocking period, messages will be handled
immediately as they are received.  On the other hand, if you use your
own sleep, messages will be queued up until you can call `poll()`;
stated differently, it will "time-quantize" the message handling.
This is not necessarily bad, but you should be aware of this effect.

Since there is a delay before the device is completely initialized, it
is sometimes useful to be able to determine this using `ready()`.
Only when `ready()` returns non-zero is it valid to use the
device's name.


Signals
=======

Now that we know how to create a device and poll it, we only
need to know how to add signals in order to give our program some
input/output functionality.

We'll start with creating a "sender", so we will first talk about how
to update output signals.

Creating a signal
-----------------

A signal requires a bit more information than a device, much of which
is optional:

* a name for the signal (must be unique within a device's inputs or outputs)
* the signal's vector length
* the signal's data type expressed as a character 'i', 'f' or 'd'
* the signal's unit (optional)
* the signal's minimum value (optional)
* the signal's maximum value (optional)

for input signals there is an additional argument:

* a function to be called when the signal is updated

examples:

    Mapper.Device.Signal in = dev.addInput( "/my_input", 1, 'f', "m/s",
                                             new PropertyValue(-10.f),
                                             null, new InputListener() {
            public void onInput( Mapper.Device.Signal sig,
                                 int instanceID,
                                 float[] value,
                                 Mapper.TimeTag tt) {
                System.out.println("got input for signal "+sig.name);
            }});

    Mapper.Device.Signal out = dev.addOutput( "/my_output", 4, 'i', null, 0, 1000 )

The only _required_ parameters here are the signal "length", its name,
and data type.  Signals are assumed to be vectors of values, so for
usual single-valued signals, a length of 1 should be specified.
Finally, supported types are currently 'i', 'f' or 'd' for `int`,
`float` or `double` values, respectively.

The other parameters are not strictly required, but the more
information you provide, the more the mapper can do some things
automatically.  For example, if the `minimum` and `maximum` properties
are provided, it will be possible to create linear-scaled connections
very quickly. If `unit` is provided, the mapper will be able to similarly figure out a linear scaling based on unit conversion. (Centimeters to
inches for example.)^[Currently automatic unit-based scaling is not a supported feature, but will be added in the future.  You can take advantage of this future development by simply providing unit information whenever
it is available.  It is also helpful documentation for users.]

Lastly, it is usually necessary to be informed when input signal
values change.  This is done by providing a function to be called
whenever its value is modified by an incoming message.  It is passed
in the `InputListener` parameter.

An example of creating a "barebones" integer scalar output signal with
no unit, minimum, or maximum information:

    Mapper.Device.Signal outA = dev.addOutput( "/outA", 1, 'i', null, null, null );

An example of a `float` signal where some more information is provided:

    Mapper.Device.Signal sensor1_voltage = dev.addOutput( "/sensor1", 1,     'f',
                                                                      "V", 0.0, 5.0 )

So far we know how to create a device and to specify an output signal
for it.  To recap, let's review the code so far:

    import Mapper.*;

    class test {
        public static void main() {
            final Mapper.Device dev = new Mapper.Device( "testDevice" );
            Mapper.Device.Signal sensor1 =
                dev.addOutput( "sensor1", 1, 'f', "V",
                               new PropertyValue( 0.f ),
                               new PropertyValue( 5.f ) );
            while ( 1 ) {
                dev.poll(50);
                ... do stuff ...
                ... update signals ...
            }
        }
    }

It is possible to retrieve a device's inputs or outputs by name or by
index at a later time using the functions `getInput()` and `getOutput()`,
passing either the signal name or its index as an argument.

Updating signals
----------------

We can imagine the above program getting sensor information in a loop.
It could be running on an network-enabled ARM device and reading the
ADC register directly, or it could be running on a computer and
reading data from an Arduino over a USB serial port, or it could just
be a mouse-controlled GUI slider.  However it's getting the data, it
must provide it to _libmapper_ so that it will be sent to other
devices if that signal is mapped.

This is accomplished by the `update()` function:

    <sig>.update( <value> )

So in the "sensor 1 voltage" example, assuming we have some code which
reads sensor 1's value into a float variable called `v1`, the loop becomes:

    while ( 1 ) {
        dev.poll( 50 );
        v1 = read_sensor_1();
        sensor1.update( v1 );
    }

This is about all that is needed to expose sensor 1's voltage to the
network as a mappable parameter.  The _libmapper_ GUI can now be used
to create a mapping between this value and a receiver, where it could
control a synthesizer parameter or change the brightness of an LED,
or whatever else you want to do.

Signal conditioning
-------------------

Most synthesizers of course will not know what to do with
"voltage" – it is an electrical property that has nothing to do with
sound or music.  This is where _libmapper_ really becomes useful.

Scaling or other signal conditioning can be taken care of _before_
exposing the signal, or it can be performed as part of the mapping.
Since end users can demand any mathematical operation be performed
on the signal, they can perform whatever mappings between signals they
wish.

As a developer, it is therefore your job to provide information that
will be useful to the end user.

For example, if sensor 1 is a position sensor, instead of publishing
"voltage", you could convert it to centimeters or meters based on the
known dimensions of the sensor, and publish a "/sensor1/position"
signal instead, providing the unit information as well.

We call such signals "semantic", because they provide information with
more meaning than a relatively uninformative value based on the
electrical properties of the sensing technique.  Some sensors can
benefit from low-pass filtering or other measures to reduce noise.
Some sensor data may need to be combined in order to derive physical
meaning.  What you choose to expose as outputs of your device is
entirely application-dependent.

You can even publish both "/sensor1/position" and "/sensor1/voltage"
if desired, in order to expose both processed and raw data.  Keep in
mind that these will not take up significant processing time, and
_zero_ network bandwidth, if they are not mapped.

Receiving signals
-----------------

Now that we know how to create a sender, it would be useful to also
know how to receive signals, so that we can create a sender-receiver
pair to test out the provided mapping functionality.

As mentioned above, the `add_input()` function takes an optional
`InputListener`.  This is a function that will be called whenever the value
of that signal changes.  To create a receiver for a synthesizer
parameter "pulse width" (given as a ratio between 0 and 1), specify
a handler when calling `add_input`.  We'll imagine there is some
Java synthesizer implemented as a class `Synthesizer` which has
functions `setPulseWidth()` which sets the pulse width in a
thread-safe manner, and `startAudioInBackground()` which sets up the
audio thread.

We need to create a handler function for libmapper to update the synth:

    InputListener freqHandler = new InputListener() {
        public void onInput( Mapper.Device.Signal sig,
                             int instanceId,
                             float[] value,
                             TimeTag tt ) {
            setPulseWidth( value );
        }}

Then our program will look like this:

    import Mapper.*;

    # Some synth stuff
    startAudioInBackground();

    InputListener freqHandler = new InputListener() {
        public void onInput( Mapper.Device.Signal sig,
                             int instanceId,
                             float[] value,
                             Mapper.TimeTag tt ) {
            setPulseWidth( value );
        }}

    final Mapper.Device dev = new Mapper.Device( "mySynth" );
    Mapper.Device.Signal pw = dev.addInput( "pulseWidth", 1, 'f', "Hz",
                                            new PropertyValue( 0.f ),
                                            new PropertyValue( 1.f ),
                                            freqHandler );

    while (1) {
        dev.poll( 100 );
    }

    synth.stop()

Alternately, we can declare the InputListener as part of the `addInput()` function:

    Mapper.Device.Signal pw = dev.addInput( "pulseWidth", 1, 'f', "Hz",
                                            new PropertyValue( 0.f ),
                                            new PropertyValue( 1.f ),
                                            new InputListener() {
        public void onInput( Mapper.Device.Signal sig,
                             int instanceId,
                             float[] value,
                             Mapper.TimeTag tt ) {
            setPulseWidth( value );
        }});


Working with timetags
=====================
_libmapper_ uses the `TimeTag` class to store 
[NTP timestamps](http://en.wikipedia.org/wiki/Network_Time_Protocol#NTP_timestamps) associated with signal updates.
For example, the handler function called when a signal update is received
contains a `timetag` argument.  This argument indicates the time at
which the source signal was _sampled_ (in the case of sensor signals)
or _generated_ (in the case of sequenced or algorithimically-generated
signals).

The signal `update()` function for output signals is overloaded; calling the function
without a timetag argument will automatically label the outgoing signal
update with the current time. In cases where the update should more
properly be labeled with another time, this can be accomplished by simply
adding the timetag as a second argument.  This timestamp should only be
overridden if your program has access to a more accurate measurement
of the real time associated with the signal update, for example if
you are writing a driver for an outboard sensor system that provides
the sampling time.

_libmapper_ also provides helper functions for getting the current
device-time:

    Mapper.TimeTag now = <device>.now();

Working with signal instances
=============================
_libmapper_ also provides support for signals with multiple _instances_,
for example:

* control parameters for polyphonic synthesizers;
* touches tracked by a multitouch surface;
* "blobs" identified by computer vision systems;
* objects on a tabletop tangible user interface;
* _temporal_ objects such as gestures or trajectories.

The important qualities of signal instances in _libmapper_ are:

* **instances are interchangeable**: if there are semantics attached
  to a specific instance it should be represented with separate signals
  instead.
* **instances can be ephemeral**: signal instances can be dynamically
  created and destroyed. _libmapper_ will ensure that linked devices
  share a common understanding of the relatonships between instances
  when they are mapped.
* **one mapping connection serves to map all of its instances.**

All signals possess one instance by default. If you would like to reserve
more instances you can use:

    <sig>.reserveInstances( int num );

After reserving instances you can update a specific instance:

    <sig>.updateInstance( int instanceId, <value> );

or

    <sig>.updateInstance( int instanceId, <value>, TimeTag tt );

All of the arguments except one should be familiar from the
documentation of `update()` presented earlier.
The `instanceId` argument does not have to be considered as an array
index - it can be any integer that is convenient for labelling your
instance. _libmapper_ will internally create a map from your id label
to one of the preallocated instance structures.

Receiving instances
-------------------
You might have noticed earlier that the handler function called when
a signal update is received has a argument called `instanceId`. Here
again is the function prototype for a float signal:

	new InputListener( Mapper.Device.Signal sig,
	                   int instanceId,
	                   float[] value,
	                   Mapper.TimeTag tt );

Under normal usage, the `instanceId` argument will have a value (0 <= n <= numInstances)
and can be used as an array index. Remember that you will need to reserve
instances for your input signal using `<sig>.reserveInstances()` if you
want to receive instance updates.

Instance Stealing
-----------------

For handling cases in which the sender signal has more instances than
the receiver signal, the _instance allocation mode_ can be set for an
input signal to set an action to take in case all allocated instances are in
use and a previously unseen instance id is received. Use the function:

    <sig>.setInstanceAllocationMode( mode );

The argument `mode` can have one of the following values:

* `Mapper.Signal.IN_UNDEFINED` Default value, in which no stealing of instances will occur;
* `Mapper.Signal.IN_STEAL_OLDEST` Release the oldest active instance and reallocate its
  resources to the new instance;
* `Mapper.Signal.IN_STEAL_NEWEST` Release the newest active instance and reallocate its
  resources to the new instance;

If you want to use another method for determining which active instance
to release (e.g. the sound with the lowest volume), you can create an `instanceEventListener` for the signal and write the method yourself:

    Mapper.instanceEventListener myHandler = new Mapper.instanceEventListener() {    
        public void onEvent( Mapper.Device.Signal sig,
                             int instanceId,
                             int event,
                             Mapper.TimeTag tt ) {
            int id = chooseInstanceToRelease( sig ); // user function
            sig.releaseInstance( id, tt );
        }
    }

For this function to be called when instance stealing is necessary, we
need to register it for `Mapper.instanceEventListener.IN_OVERFLOW` events:

    <sig>.setInstanceEventCallback( myHandler,
                                    Mapper.instanceEventListener.IN_OVERFLOW );


Publishing metadata
===================

Things like device names, signal units, and ranges, are examples of
metadata – information about the data you are exposing on the network.

_libmapper_ also provides the ability to specify arbitrary extra
metadata in the form of name-value pairs.  These are not interpreted
by _libmapper_ in any way, but can be retrieved over the network.
This can be used for instance to label a device with its location, or
to perhaps give a signal some property like "reliability", or some
category like "light", "motor", "shaker", etc.

Some GUI implementing a Monitor could then use this information to
display information about the network in an intelligent manner.

Any time there may be extra knowledge about a signal or device, it is
a good idea to represent it by adding such properties, which can be of
any OSC-compatible type.  (So, numbers and strings, etc.)

The property interface is through the functions,

    <object>.setProperty( String key, PropertyValue value );

where the value can any OSC-compatible type. This function can be called
for devices or signals.

For example, to store a `float vector` indicating the 2D position of a device
`dev`, you can call it like this:

    dev.setProperty( "position", new PropertyValue( new float[] { 12.5f, 40.f } ) );

To specify a string property of a signal `sig`:

    sig.setProperty( "sensingMethod", new PropertyValue( "resistive" ) );

In general you can use any property name not already in use by the
device or signal data structure.  Reserved words for signals are:

    device_name, direction, length, max, maximum, min, minimum,
    name, type, unit, user_data, value

for devices, they are:

    host, port, name, user_data

By the way, if you query or set signal properties using these
keywords, you will get or modify the same information that is
available directly from the `signal` data structure.
Therefore this can provide a unified string-based method for accessing
any signal property:

    props = sig.properties();
    sensingMethod = props.property( "sensingMethod" );
    minimum = props.property( "min" );

Primarily this is an interface meant for network monitors, but may
come in useful for an application implementing a device.
