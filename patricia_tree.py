import pickle
import os
from hashlib import sha256

from leveldb_handler import LvlDB
from nodes import *
from encoding import *


# This Patricia Tree implementation does not use RLP-encoding, as I was interesting in logic
# pickle.dumps and pickle.loads could be swapped for rlp easily
class MerklePatriciaTree:
	debug = False

	def __init__(self, from_scratch=None, debug=None):
		if debug:
			self.debug = debug
		if from_scratch:
			self.db = LvlDB(debug=self.debug, from_scratch=True)
			self.root_hash = self.init_new_root()
		else:
			self.db = LvlDB(debug=self.debug, from_scratch=False)
			try:
				self.root_hash = self.db.get(b'root_hash')
			except KeyError:
				raise Exception("ERROR. Attempted to read \'root_hash\' from DB, but it was not found." + os.linesep +
								"Repair your DB, delete it or request PatriciaTree to be built from scratch")

		if debug:
			print("PatriciaTree.root_hash", self.root_hash)
			print("PatriciaTree.db.get(self.root_hash)", self.db.get(self.root_hash))

	def init_new_root(self):
		root = BranchNode()
		root_str = pickle.dumps(root)
		root_hash = binstr(sha256(root_str).hexdigest())
		self.db.put(root_hash, root_str)
		self.db.put(b'root_hash', root_hash)
		return root_hash

	def insert(self, value):
		key_nibbles = hexdigest_to_nib(sha256(binstr(value)).hexdigest())
		if key_nibbles[0] == HEX_SEQUENCE_ODD:
			key_nibbles = key_nibbles[1:]
		elif key_nibbles[0] == HEX_SEQUENCE_EVEN:
			key_nibbles = key_nibbles[2:]
		else:
			raise ExtensionNode("Incorrect key_nibbles:", key_nibbles)

		curr_node_hash = self.root_hash
		curr_node = pickle.loads(self.db.get(curr_node_hash))
		curr_nibble_index = 0
		visited_hashes = list()
		while True:
			visited_hashes.append(curr_node_hash)
			if self.debug:
				print("DEBUG> curr_node:", curr_node)
			if type(curr_node) == BranchNode:
				if len(key_nibbles) == curr_nibble_index - 1:
					# if key ended:
					#    write to branch.value

					if self.debug:
						print("key ended -> write to branch.value")
					curr_node.value = value
					curr_node_str = pickle.dumps(curr_node)
					self.db.put(curr_node_hash, curr_node_str)
					self._recursive_hash_update(visited_hashes)
					break
				elif not curr_node[key_nibbles[curr_nibble_index]]:
					# if hash_by_current_nibble = NULL:
					leaf_str = pickle.dumps(LeafNode(value))
					leaf_hash = binstr(sha256(leaf_str).hexdigest())
					self.db.put(leaf_hash, leaf_str)
					if len(key_nibbles) - curr_nibble_index >= 2:
						if self.debug:
							print(">create extension node pointing to new kv node, that stores the value.")
						# 	create extension node pointing to new kv node, that stores the value.
						extension = ExtensionNode(subnib_to_binstr(key_nibbles[curr_nibble_index + 1:]), leaf_hash)
						extension_str = pickle.dumps(extension)
						extension_hash = binstr(sha256(extension_str).hexdigest())
						self.db.put(extension_hash, extension_str)

						curr_node[key_nibbles[curr_nibble_index]] = extension_hash
						curr_node_str = pickle.dumps(curr_node)
						self.db.put(curr_node_hash, curr_node_str)
						self._recursive_hash_update(visited_hashes)
						break
					elif len(key_nibbles) - curr_nibble_index == 1:
						if self.debug:
							print(">point branch directly to new kv node, that stores the value")
						# 	point branch directly to new kv node, that stores the value.
						curr_node[key_nibbles[curr_nibble_index]] = leaf_hash
						curr_node_str = pickle.dumps(curr_node)
						self.db.put(curr_node_hash, curr_node_str)
						self._recursive_hash_update(visited_hashes)
						break
					else:
						raise Exception("len(key_nibbles)=", len(key_nibbles), "curr_nibble_index=", curr_nibble_index)
				else:
					# else get down
					if self.debug:
						print(">BranchNode: get down")
					curr_node_hash = curr_node[key_nibbles[curr_nibble_index]]
					curr_node_str = self.db.get(curr_node_hash)

					curr_node = pickle.loads(curr_node_str)
					curr_nibble_index += 1
			elif type(curr_node) == ExtensionNode:
				node_key = binstr_to_nib(curr_node.key)
				if node_key[0] == HEX_SEQUENCE_ODD:
					node_key = node_key[1:]
				elif node_key[0] == HEX_SEQUENCE_EVEN:
					node_key = node_key[2:]
				else:
					raise ExtensionNode("Incorrect node_key:", node_key)

				if node_key == key_nibbles[curr_nibble_index:]:
					if self.debug:
						print(">ExtensionNode.key completely equal to rest of the key -> overwrite")
					# if ExtensionNode.key completely equal to rest of the key
					#   it is definitely Extension, that points to Leaf
					# 	overwrite!
					new_child_str = pickle.dumps(LeafNode(value))
					new_child_hash = binstr(sha256(new_child_str).hexdigest())
					self.db.put(new_child_hash, new_child_str)
					self.db.delete(curr_node.child_hash)

					curr_node.child_hash = new_child_hash
					curr_node_str = pickle.dumps(curr_node)
					self.db.put(curr_node_hash, curr_node_str)
					self._recursive_hash_update(visited_hashes)
					break
				else:
					# check how many nibbles are same
					equal_elems = self._get_amount_of_equal_elements(node_key, key_nibbles[curr_nibble_index:])

					if equal_elems == len(node_key):
						if self.debug:
							print(">branch -> just keep on traversing")
						# (but it is not the whole remaining key)
						# just keep on traversing
						curr_node_hash = curr_node.child_hash
						curr_node_str = self.db.get(curr_node_hash)
						curr_node = pickle.loads(curr_node_str)
						curr_nibble_index += equal_elems
					elif equal_elems == 0:
						if self.debug:
							print(">extension, no equal elems -> switch it to branch")
						# no equal elems -> switch it to branch
						# branch will have 2 entries: to old extension and new extention to leaf
						branch = BranchNode()

						leaf_str = pickle.dumps(LeafNode(value))
						leaf_hash = binstr(sha256(leaf_str).hexdigest())
						self.db.put(leaf_hash, leaf_str)

						# extension to new node
						extension = ExtensionNode(subnib_to_binstr(key_nibbles[curr_nibble_index + 1:]), leaf_hash)
						extension_str = pickle.dumps(extension)
						extension_hash = binstr(sha256(extension_str).hexdigest())
						self.db.put(extension_hash, extension_str)

						# old extension
						self.db.delete(curr_node_hash)
						if len(node_key) == 1:
							branch[node_key[0]] = curr_node.child_hash
						else:
							curr_node.key = subnib_to_binstr(node_key[1:])
							curr_node_str = pickle.dumps(curr_node)
							curr_node_hash = binstr(sha256(curr_node_str).hexdigest())
							branch[node_key[0]] = curr_node_hash
							self.db.put(curr_node_hash, curr_node_str)

						branch[key_nibbles[curr_nibble_index]] = extension_hash
						branch_str = pickle.dumps(branch)
						branch_hash = binstr(sha256(branch_str).hexdigest())
						self.db.put(branch_hash, branch_str)

						old_curr_node_hash = visited_hashes.pop()

						prev_node_hash = visited_hashes[-1]
						prev_node = pickle.loads(self.db.get(prev_node_hash))
						if type(prev_node) != BranchNode:
							raise Exception("prev_node is of unexpected type:", type(curr_node))
						nibble = prev_node.get_index(old_curr_node_hash)
						prev_node[nibble] = branch_hash
						prev_node_str = pickle.dumps(prev_node)
						self.db.put(prev_node_hash, prev_node_str)

						self._recursive_hash_update(visited_hashes)
						break
					elif equal_elems < len(node_key):
						# have to split into extension -> branch -> extension
						if self.debug:
							print(">have to split into extension -> branch -> extension")
						leaf_str = pickle.dumps(LeafNode(value))
						leaf_hash = binstr(sha256(leaf_str).hexdigest())
						branch = BranchNode()
						curr_nibble_index += equal_elems
						self.db.put(leaf_hash, leaf_str)
						if equal_elems == len(key_nibbles[curr_nibble_index:]):
							# store value branch.value
							branch.value = value
						else:
							# split into extension -> branch -> (extension, leaf)
							if len(key_nibbles[curr_nibble_index:]) == 1:
								if self.debug:
									print(">straight to leaf")
								# e.g. straight to leaf
								branch[key_nibbles[-1]] = leaf_hash
							else:
								# split into extension -> branch -> (extension, extension)
								if self.debug:
									print(">create extra extension going to new leaf")
								# e.g. create extra extension
								extension_to_leaf = ExtensionNode(subnib_to_binstr(
									key_nibbles[curr_nibble_index + 1:]), leaf_hash)
								extension_to_leaf_str = pickle.dumps(extension_to_leaf)
								extension_to_leaf_hash = binstr(sha256(extension_to_leaf_str).hexdigest())
								self.db.put(extension_to_leaf_hash, extension_to_leaf_str)
								branch[key_nibbles[curr_nibble_index]] = extension_to_leaf_hash

						# this extension goes back to original node, as before splitting
						if self.debug:
							print(">this extension goes back to original node, as before splitting")
						ext_after_branch = ExtensionNode(subnib_to_binstr(node_key[equal_elems + 1:]),
														curr_node.child_hash)
						ext_after_branch_str = pickle.dumps(ext_after_branch)
						ext_after_branch_hash = binstr(sha256(ext_after_branch_str).hexdigest())
						self.db.put(ext_after_branch_hash, ext_after_branch_str)

						# new branch with 2 extensions: original node + new node just added
						if self.debug:
							print(">new branch with 2 extensions: original node + new node just added")
						branch[node_key[equal_elems]] = ext_after_branch_hash

						branch_str = pickle.dumps(branch)
						branch_hash = binstr(sha256(branch_str).hexdigest())
						self.db.put(branch_hash, branch_str)

						# this extension goes to new branch
						if self.debug:
							print(">this extension goes to new branch")
						ext_before_branch = ExtensionNode(subnib_to_binstr(node_key[:equal_elems]), branch_hash)
						ext_before_branch_str = pickle.dumps(ext_before_branch)
						ext_before_branch_hash = binstr(sha256(ext_before_branch_str).hexdigest())
						self.db.delete(curr_node_hash)
						self.db.put(ext_before_branch_hash, ext_before_branch_str)

						visited_hashes.pop()

						prev_node_hash = visited_hashes[-1]
						prev_node = pickle.loads(self.db.get(prev_node_hash))
						# it has to be Branch, as we cannot have 2 Extensions in a row
						nibble = prev_node.get_index(curr_node_hash)
						prev_node[nibble] = ext_before_branch_hash
						prev_node_str = pickle.dumps(prev_node)
						self.db.put(prev_node_hash, prev_node_str)
						self._recursive_hash_update(visited_hashes)
						break
					elif equal_elems > len(node_key):
						raise Exception("equal_elems(", equal_elems, ") > len(node_key) (", len(node_key), ")")
			elif type(curr_node) == LeafNode:
				raise Exception("curr_node is LeafNode!")
			else:
				raise Exception("curr_node is of unknown type:", type(curr_node))

	def remove(self, value):
		key_nibbles = hexdigest_to_nib(sha256(binstr(value)).hexdigest())
		if key_nibbles[0] == HEX_SEQUENCE_ODD:
			key_nibbles = key_nibbles[1:]
		elif key_nibbles[0] == HEX_SEQUENCE_EVEN:
			key_nibbles = key_nibbles[2:]
		else:
			raise ExtensionNode("Incorrect key_nibbles:", key_nibbles)

		curr_node_hash = self.root_hash
		curr_node = pickle.loads(self.db.get(curr_node_hash))
		curr_nibble_index = 0
		visited_hashes = list()
		while True:
			visited_hashes.append(curr_node_hash)
			if self.debug:
				print("DEBUG> curr_node:", curr_node)
			if type(curr_node) == BranchNode:
				if len(key_nibbles) == curr_nibble_index - 1:
					# if key ended:
					#    erase to branch.value
					curr_node.value = b''
					curr_node_str = pickle.dumps(curr_node)
					self.db.put(curr_node_hash, curr_node_str)
					self._recursive_hash_update(visited_hashes)
					return
				elif not curr_node[key_nibbles[curr_nibble_index]]:
					# if hash_by_current_nibble = NULL:
					print("key_nibbles", key_nibbles)
					print("curr_nibble_index", curr_nibble_index)
					print(curr_node)
					raise Exception("curr_node[key_nibbles[curr_nibble_index]]",
									curr_node[key_nibbles[curr_nibble_index]])
				else:
					# else get down
					if self.debug:
						print(">BranchNode: get down")
					curr_node_hash = curr_node[key_nibbles[curr_nibble_index]]
					curr_node_str = self.db.get(curr_node_hash)
					curr_node = pickle.loads(curr_node_str)
					curr_nibble_index += 1
			elif type(curr_node) == ExtensionNode:
				nib = binstr_to_nib(curr_node.key)
				curr_nibble_index += len(nib) - nib[0]
				curr_node_hash = curr_node.child_hash
				curr_node_str = self.db.get(curr_node_hash)
				curr_node = pickle.loads(curr_node_str)
			elif type(curr_node) == LeafNode:
				self.db.delete(curr_node_hash)
				prev_node = None
				while(len(visited_hashes) > 1):
					visited_hashes.pop()
					prev_node_hash = visited_hashes[-1]
					prev_node = pickle.loads(self.db.get(prev_node_hash))
					if type(prev_node) == BranchNode:
						nibble = prev_node.get_index(curr_node_hash)
						prev_node[nibble] = b''
						links_left = 0
						for n in range(16):
							if prev_node[n] != b'':
								links_left += 1
						if not links_left:
							self.db.delete(prev_node_hash)
						else:
							break
					elif type(prev_node) == ExtensionNode:
						self.db.delete(prev_node_hash)
					else:
						raise Exception("Unexpected type:", type(curr_node))
					curr_node_hash = prev_node_hash
				if prev_node:
					prev_node_str = pickle.dumps(prev_node)
					self.db.put(prev_node_hash, prev_node_str)
					self._recursive_hash_update(visited_hashes)
				return

	@staticmethod
	def _get_amount_of_equal_elements(array1, array2):
		"""
		:return: amount of equal elements
		"""
		for i in range(min(len(array1), len(array2))):
			if array1[i] != array2[i]:
				return i
		return min(len(array1), len(array2))

	def _recursive_hash_update(self, hashes):
		"""type hashes: list

		Usage: top node in hashes should be left inconsistent, e.g. its key(hash)
		does not correspond to actual hash"""

		# Handle top node, which only has hash inconsistency, as opposed to other nodes,
		# which have to update links
		if self.debug:
			print()
			print("## Starting _recursive_hash_update")
			print(hashes)
		prev_node_former_hash = hashes.pop()
		prev_node_str = self.db.get(prev_node_former_hash)
		prev_node_real_hash = binstr(sha256(prev_node_str).hexdigest())
		self.db.delete(prev_node_former_hash)
		self.db.put(prev_node_real_hash, prev_node_str)

		while len(hashes):
			curr_hash = hashes.pop()
			curr_node_str = self.db.get(curr_hash)
			curr_node = pickle.loads(curr_node_str)
			if type(curr_node) == BranchNode:
				nibble = curr_node.get_index(prev_node_former_hash)
				curr_node[nibble] = prev_node_real_hash
			elif type(curr_node) == ExtensionNode:
				curr_node.child_hash = prev_node_real_hash
			elif type(curr_node) == LeafNode:
				raise Exception("Recursive hash update hit LeafNode")
			else:
				raise Exception("Incorrect type:", type(curr_node))
			prev_node_former_hash = curr_hash
			prev_node_str = pickle.dumps(curr_node)
			prev_node_real_hash = binstr(sha256(prev_node_str).hexdigest())

			if prev_node_former_hash != prev_node_real_hash:
				self.db.delete(prev_node_former_hash)
				self.db.put(prev_node_real_hash, prev_node_str)

		# Update root node
		self.root_hash = prev_node_real_hash
		self.db.put(b'root_hash', self.root_hash)

		if self.debug:
			print("## Finished _recursive_hash_update")
			print()
