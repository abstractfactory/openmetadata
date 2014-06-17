# 0.5.3

### Strict

pull() is more strict, it doesn't assume an alternate suffix when one has been supplied.

```python
# Pre 0.5.3 - custom.string does not exist, but custom.int does
>>> entry = Entry('custom.string', parent=location)
>>> pull(entry)
# This would pull from custom.int, and implicitly alter the
# type of `entry`

# New in 0.5.3
>>> pull(entry)
error.Exists("custom.string does not exist")
```

### read() now works with suffixes

In cases where the user wishes to retrieve a specific entry by a specific type, he may now type:

```python
# This will return the string, only if the specific types exists
>>> read('/home/marcus', '/my/specific.list/type.string')
```

### split() now returns suffixes

Before, split returned a pure metapath without suffixes, it is now the users responsibility to strip suffixes from split if so is required.

### convert() now works with suffixes

Before, convert would disregard suffixes in its metapath, resulting in invalid return values when a suffix was included, but not existing.

# If entry.string exists, convert would silently return it
# and disregard the users request for a .text.
>>> convert('/home/marcus/.meta/custom/entry.text')

# If the user wishes to get any suffix, he could say..
>>> convert('/home/marcus/.meta/custom/entry')
# ..which would return any existing entry, regardless of suffix.

### Suffix-independend find()

Find is supposed to "find" an entry within a directory, regardless of its suffix, and return the existing one (if one exists):

```python
>>> om.find('/home/marcus', 'myentry')
'myentry.bool'
```

However, when querying by a specific suffix, it couldn't properly do its job.

```python
>>> om.find('/home/marcus', 'myentry.int')
None
```

In 0.5.3, it does.

```python
>>> om.find('/home/marcus', 'myentry.int')
'myentry.bool'
```

### No more name-conflicts

Prior to 0.5.3, an entry could get written under multiple suffixes:

```python
om.write('/home/marcus', 'isawesome.string', 'True')
om.write('/home/marcus', 'isawesome.int', 'True')
```

This would produce two entries of `isawesome`, without incrementing history for the original when attempting to write to the new.

```bash
$ ls
isawesome.string
isawesome.int
```

Names of entries MUST remain unique and so now, in 0.5.3, this is true.

```python
# First entry is written.
om.write('/home/marcus', 'isawesome.string', 'True')

# Before writing, history is maintained for original `isawesome.string`
# in addition to the original being removed.
om.write('/home/marcus', 'isawesome.int', 'True')
```

```bash
$ ls
isawesome.int
```

### Case-insensitivity

Open Metadata now defaults to case-insensitivity; meaning that utilities such as..

```python
>>> om.find('/home/marcus', 'MynAME')
```

..will return identical results as..

```python
>>> om.find('/home/marcus', 'myname')
```

# 0.5.2

om.split(path=string) -- Break apart location from metapath
om.convert(path=string) -- Turn an absolute path into Entry object

# 0.5

An *Epic Eureka Moment (tm)* release

1. Unification of `Group` and `Dataset` into `Entry`
2. New `Path` object
3. Ineritance
4. Type-changes maintained in history
5. dump() is flush()

### Unification into `Entry`

This has been an amazing discovery! No more is there a need to separate between what is a "folder" or what is a "file". A Entry may contain any data and if said data is more appropriately stored on a file-system as a folder, then a folder it will become. To the user, it makes little difference.

This is in relation to the common notion of "variables" in dynamic programming languages, such as Python:

```python
# `my_var` is of type <int> here
>>> my_var = 5

# But now we're changing it to <list> with a <string> inside
>>> my_var = ['string']

# To the end user, it makes little difference;
# what matters is the reference 'my_var'.
```

So, the equivalent in Open Metadata syntax:

```python
>>> location = om.Location('/home/marcus')
>>> my_var = om.Entry('my_var', parent=location)
>>> my_var.value = 5
>>> my_var.value = ['string']
>>> om.dump(my_var)
# Produces a folder of type <list> with a file of type <string>
```

### New `Path` object

Fetching the path from any node now gives you an object with proper OS facilities; e.g. Windows and Posix system methods.

### Ineritance

This is another amazing discovery. You can use it as an alternative to om.pull, it will behave just as such, only it will also pull from parents and parents parents; in effect "inheriting" from above hierarchy.

### Type-changes maintained in history

Prior to 0.5, altering the type of a Dataset would break any prior history to said Dataset.

```python
om.write(path, 'my_age', 5)
om.write(path, 'my_age', 6.0)
```

Here, history would not be maintained between the two different types (int, and float).

Now it does, it preserves the type too so that you get back both value and type when restoring from history.

### `dump()` is `flush()`

This is to separate the Entry.dump() from om.flush(), flush performs an I/O operation whereas Entry.dump() serialises data internal to itself. This also conforms to the HDF5 standard.

# 0.4

Mainly a maintenance release, but does contain backwards-incompatible changes; marked [INCOMPATIBLE] below.

### Client-side serialisation

One of the major changes made was the transiton from ad-hoc serialisation to disk into JSON; making data readable from other programming languages without additional serialisation, one could simply use JSON.

The serialisation and de-serialisation processes are happening on the client-end, so as to further support interchangeable languages in communication between api and service, as well as to spare whatever central server exposing the service from needless serialisation; each client now serialises prior to communicating with the service.

### Simplified lib.py

Node now allows for children; descendants of Blob merely have their children de-activated.

### Modifications

* om.pull(node, lazy=False, depth=1)
	* depth	-- (new) how deep in the hierarchy to pull
	* lazy 	-- whether or not to pull if node already has data

* om.read(path, metapath, native=True) [INCOMPATIBLE]
	* metapath 	-- now in metapath-syntax, '/meta/path'
	* native 	-- Return Python object if True, OM object if False

* om.write(path, metapath, data) [INCOMPATIBLE]
	* metapath 	-- now in metapath-syntax, '/meta/path'

* Node
	* path 		-- Now returns a Path object
	* basename 	-- Now in Node.path.basename
	* name 		-- Now in Node.path.name
	* clear()   -- Remove existing data

* om.metadata 	-- Replaced by om.read(native=False)

### Additions

* om.ls 			-- List contents of node
* lib.Path 			-- Platform agnostic path-manipultaion object
* Node.__getitem__  -- Children may now be accessed via dict syntax
* Node.haschildren  -- Returns whether or not `node` has children

### Removals

* lib.TreeNode  -- Was removed due to unifications of children in all Node objects
