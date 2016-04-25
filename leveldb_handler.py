import leveldb
import os
import pickle
from nodes import *

class LvlDB:
	path_to_db = "./db"
	debug = False

	def __init__(self, _path_to_db=None, from_scratch=None, debug=None):
		if _path_to_db:
			self.path_to_db = _path_to_db
		if debug:
			self.debug = debug
		if from_scratch:
			try:
				import shutil
				shutil.rmtree(self.path_to_db)
			except OSError:
				pass

		self.db = leveldb.LevelDB(self.path_to_db, create_if_missing=True)
		if self.debug:
			print("#READ DB FROM FILE", self.path_to_db)
			self.print_all()

	def put(self, key, value):
		self.db.Put(key, value)
		if self.debug:
			print("#NEW DB STATE after adding key", key)
			self.print_all()

	def get(self, key):
		try:
			value = self.db.Get(key)
		except KeyError:
			value = None
		except Exception as e:
			e.args += (key,)
			raise e
		return value

	def delete(self, key):
		self.db.Delete(key)

	def print_all(self):
		for k, v in self.db.RangeIter(include_value=True):
			if k == b'root_hash':
				print("root_hash=", v)
			else:
				n = pickle.loads(v)
				print(k, n)

	def status(self):
		extensions = 0
		branches = 0
		leafs = 0
		for k, v in self.db.RangeIter(include_value=True):
			if k == b'root_hash':
				print("root_hash=", v)
			else:
				n = pickle.loads(v)
				if type(n) == ExtensionNode:
					extensions += 1
				elif type(n) == BranchNode:
					branches += 1
				elif type(n) == LeafNode:
					leafs += 1
				else:
					raise Exception("Unknown type:", type(n), ".", k, n)
		print("extensions", extensions)
		print("branches", branches)
		print("leafs", leafs)
