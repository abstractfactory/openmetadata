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