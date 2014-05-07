![](images/title.png)

![](images/basic.png)

*Open Metadata* is a library used in associating metadata to folders on your file-system, designed for concurrent, high-performance and scalable digital asset management (DAM) systems.

### Installing

1. Download a [release][]
2. Unpack

```bash
# 3. Install
$ python setup.py
```

* Note that the installer requires [setuptools][] which you can get by installing [pip][].

### Zen

* ..change is common
* ..space is cheap
* ..control outweighs performance


|Feature                          |Description  |
|:--------------------------------|:------------|
|Non-destructive                  | Every change you make is maintained in history; facilitating persistent undo/redo, traceable history of who did what and when, including incremental versioning with arbitrary metadata, like a changelog or description. All retrievable at any point in time. |
|Full disclosure                  | You may at any point in time browse to data at any hierarchical level using your native file-browser; read, write, modify, delete or debug malicious data with tools you know.    |
|Partial I/O                      | As a side-effect to its inherently simplistic design, reading and writing within large sets of data doesn't require reading everything into memory nor does it affect surrounding data; facilitating distributed collaborative editing. See [RFC13][] for more information.
|No limits on size nor complexity | Store millions of strings, booleans, matrices.. groups of matrices.. matrices of groups, strings, booleans and vectors. On consumer hardware, in a matter of megabytes, without compression. Then go ahead and store billions.
|Open specification, open source  | There are no mysteries about the inner-workings of the data that you write; you may write personal tools for debugging, graphical interfaces or extensions to the standard. The specifications are all laid out below and collaboration is welcome. (Want Open Metadata in Lua, Java, PHP or C++?)

### Specifications

The Open Metadata technology is designed to organize, store, discover, access, analyze, share, and preserve diverse, complex data in continuously evolving heterogeneous computing and storage environments.

The implementation you are reading about right now is LGPLv3 licensed software, however Open Metadata itself is language- and implementation-agnostic, built upon the following open-source specifications:

* [RFC10][]: Main Specification
* [RFC12][]: Cascading
* [RFC13][]: Task Distribution
* [RFC14][]: Temporal Metadata
* [RFC15][]: Meta Metadata
* [RFC16][]: Blob
* [RFC17][]: Cross-referencing
* [RFC18][]: Types
* [RFC19][]: Storage Agnostic
* [RFC20][]: Referencing
* [RFC35][]: Garbage Collection
* [RFC41][]: Driver
* [RFC46][]: Temporal Resolution
* [RFC59][]: Omlang, pure programmable content
* [RFC61][]: Terminal Metadata

### FAQ

> Who uses Open Metadata?

As part of developing a Digital Asset Management System here at Abstract Factory, we develop Open Metadata as the foundational building-block with which all metadata - including configuration, geometric proxy shapes, thumbnails and plain-old-data - is created and maintained.

Read more about [us and Pipi here](http://abstractfactory.io)

> Why Open Metadata and not Technology X?

Many alternatives were, and continue to be evaluated. Head over to [RFC24](http://rfc.abstractfactory.io/spec/24/) for an overview.

> What is programmable content?

In a data-oriented architecture, data controls the flow of information, not your software. Your software is designed to take instructions from data external to itself as a way to de-couple programmers from implementers.

This way, implementers can design their software by means of placing content, in a hierarchy for instance, that governs what actions the software may take in which order.

Open Metadata was designed to facilitate metadata in content management. With metadata in content, it is possible to treat each file or folder as an stateful, intelligent unit capable of making desicions; this is what I call programmable content.

### Usergroup

We're all having a good time, here, join us
https://groups.google.com/forum/#!forum/open-metadata

[RFC10]: http://rfc.abstractfactory.io/spec/10
[RFC12]: http://rfc.abstractfactory.io/spec/12
[RFC13]: http://rfc.abstractfactory.io/spec/13
[RFC14]: http://rfc.abstractfactory.io/spec/14
[RFC15]: http://rfc.abstractfactory.io/spec/15
[RFC16]: http://rfc.abstractfactory.io/spec/16
[RFC17]: http://rfc.abstractfactory.io/spec/17
[RFC18]: http://rfc.abstractfactory.io/spec/18
[RFC19]: http://rfc.abstractfactory.io/spec/19
[RFC20]: http://rfc.abstractfactory.io/spec/20
[RFC35]: http://rfc.abstractfactory.io/spec/35
[RFC41]: http://rfc.abstractfactory.io/spec/41
[RFC46]: http://rfc.abstractfactory.io/spec/46
[RFC59]: http://rfc.abstractfactory.io/spec/59
[RFC61]: http://rfc.abstractfactory.io/spec/61

[setuptools]: https://pypi.python.org/pypi/setuptools
[pip]: http://pip.readthedocs.org/en/latest/installing.html
[Download repository]: https://github.com/abstractfactory/openmetadata/archive/master.zip
[/examples]: https://github.com/abstractfactory/openmetadata/tree/master/openmetadata/examples
[release]: https://github.com/abstractfactory/openmetadata/releases