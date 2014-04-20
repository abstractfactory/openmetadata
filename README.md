![](https://dl.dropbox.com/s/frgz506hx49i9rt/openmetadata_black_med_rgb_aw1.png)

Associate metadata with folders on your file-system.

```python
# Simplest use-case
>>> import openmetadata as om
>>> om.write('/home/marcus', 'description', 'Creator of Open Metadata')
>>> om.read('/home/marcus', 'description')
Creator of Open Metadata
```

For more, head over to [/samples](https://github.com/abstractfactory/openmetadata/tree/master/samples)

Usergroup here
https://groups.google.com/forum/#!forum/open-metadata

# Features

There for you when..

* ..change is common
* ..space is cheap
* ..control outweighs performance

> Open Metadata is in early development (current version `0.4`) but below is what it can do for you today.

#### Non-destructive

Every change you make is maintained in history; facilitating persistent undo/redo, traceable history of who did what and when, including incremental versioning with arbitrary metadata, like a changelog or description. All retrievable at any point in time.

#### Full disclosure

You may at any point in time browse to data at any hierarchical level using your native file-browser; read, write, modify, delete or debug malicious data with tools you know.

#### Partial I/O

As a side-effect to its inherently simplistic design, reading and writing within large sets of data doesn't require reading everything into memory nor does it affect surrounding data; facilitating distributed collaborative editing. See [RFC13][] for more information.

#### No limits on size nor complexity

Store millions of strings, booleans, matrices.. groups of matrices.. matrices of groups, strings, booleans and vectors. On consumer hardware, in a matter of megabytes, without compression. Then go ahead and store billions.

#### Open specification, open source

There are no mysteries about the inner-workings of the data that you write; you may write personal tools for debugging, graphical interfaces or extensions to the standard. The specifications are all laid out below and collaboration is welcome. (Want Open Metadata in Lua, Java, PHP or C++?)

# Installation

Download a [release][], unpack into site-packages.

```python
# Example
>>> site_packages = r'c:\python27\lib\site-packages'

# To test, run
>>> import openmetadata-0.4 as om
>>> print om.version
'0.4.0'
```

# Specifications

The Open Metadata technology is designed to organize, store, discover, access, analyze, share, and preserve diverse, complex data in continuously evolving heterogeneous computing and storage environments.

Open Metadata is LGPLv3 licensed software built upon the following open-source specifications:

* [General Introduction](http://rfc.abstractfactory.io/spec/10)
* [Temporal Open Metadata](http://rfc.abstractfactory.io/spec/14)
* [Cascading Metadata](http://rfc.abstractfactory.io/spec/12)
* [Zero Open Metadata](http://rfc.abstractfactory.io/spec/13)
* [Meta Metadata](http://rfc.abstractfactory.io/spec/15)
* [Metadata Types](http://rfc.abstractfactory.io/spec/18)
* [Metadata Blob](http://rfc.abstractfactory.io/spec/16)
* [Metadata Referencing](http://rfc.abstractfactory.io/spec/20)
* [Garbage Metadata](http://rfc.abstractfactory.io/spec/20)
* [Cross-referencing Metadata](http://rfc.abstractfactory.io/spec/17)
* [Storage Agnostic Metadata](http://rfc.abstractfactory.io/spec/19)

# FAQ

> Why Open Metadata and not Technology X?

Many alternatives were, and continue to be evaluated. Head over to [RFC24](http://rfc.abstractfactory.io/spec/24/) for an overview.

> What is programmable content?

In a data-oriented architecture, data controls the flow of information, not your software. Your software is designed to take instructions from data external to itself as a way to de-couple programmers from implementers.

This way, implementers can design their software by means of placing content, in a hierarchy for instance, that governs what actions the software may take in which order.

Open Metadata was designed to facilitate metadata in content management. With metadata in content, it is possible to treat each file or folder as an stateful, intelligent unit capable of making desicions; this is what I call programmable content.

# Usergroup

We're all having a good time, here, join us
https://groups.google.com/forum/#!forum/open-metadata

[RFC13]: http://rfc.abstractfactory.io/spec/13
[release]: https://github.com/abstractfactory/openmetadata/releases