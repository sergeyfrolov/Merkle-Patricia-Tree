class BranchNode:
	value = b''

	def __init__(self):
		self.branches = [b'']*16

	def __getitem__(self, key):
		if key < 0 or key > 15:
			raise Exception("invalid key: " + str(key))
		return self.branches[key]

	def __setitem__(self, key, value):
		if key < 0 or key > 15:
			raise Exception("invalid key: " + str(key))
		self.branches[key] = value

	def __str__(self):
		return "BranchNode " + str(self.branches) + " value=" + str(self.value)

	def get_index(self, value):
		for i in range(16):
			if self.branches[i] == value:
				return i
		raise KeyError("Value", value, "was not found in BranchNode")


class ExtensionNode:
	key = b''
	child_hash = b''

	def __init__(self, _key, _leaf_hash):
		self.key = _key
		self.child_hash = _leaf_hash

	def __str__(self):
		return "ExtensionNode key=" + str(self.key) + " child_hash=" + str(self.child_hash)

class LeafNode:
	value = b''

	def __init__(self, _value):
		self.value = _value

	def __str__(self):
		return "LeafNode value=" + str(self.value)
