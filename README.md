Open Metadata
=============

![](https://dl.dropbox.com/s/av2x8gel580ow48/om2_hierarchy.png)

Open Metadata lets you associate metadata with a location; such as a path on a file-system.

```python
# Simplest use-case
>>> import openmetadata as om
>>> om.write('/home/marcus', 'Creator of Open Metadata', 'description')
>>> om.read('/home/marcus', 'description')
Creator of Open Metadata

# More in /samples

```

# Specifications

Open Metadata is GPLv3 licensed software built upon the following open-source specifications:

* [General Introduction](http://rfc.abstractfactory.io/spec/10)
* [Object-Oriented Metadata](http://rfc.abstractfactory.io/spec/12)
* [Zero Open Metadata](http://rfc.abstractfactory.io/spec/13)
* [Temporal Open Metadata](http://rfc.abstractfactory.io/spec/14)
* [Meta Open Metadata](http://rfc.abstractfactory.io/spec/15)
* [Open Metadata Blob](http://rfc.abstractfactory.io/spec/16)
* [Cross-referencing Metadata](http://rfc.abstractfactory.io/spec/17)
* [Open Metadata Types](http://rfc.abstractfactory.io/spec/18)
* [Storage Agnostic Metadata](http://rfc.abstractfactory.io/spec/19)
* [Mirrored Metadata](http://rfc.abstractfactory.io/spec/20)

# Why Open Metadata and not Technology X?

Many alternatives were, and continue to be evaluated. Head over to [RFC24](http://rfc.abstractfactory.io/spec/24/) for an overview.

# What is programmable content?

In a data-oriented architecture, data controls the flow of information, not your software. Your software is designed to take instructions from data external to itself as a way to de-couple programmers from implementers.

This way, implementers can design their software by means of placing content, in a hierarchy for instance, that governs what actions the software may take in which order.

Open Metadata was designed to facilitate metadata in content management. With metadata in content, it is possible to treat each file or folder as an stateful, intelligent unit capable of making desicions; this is what I call programmable content.