# have to have reproducible tests to find bugs easier
from patricia_tree import MerklePatriciaTree
from nodes import *
from encoding import *
import time

class PTTester:

	def __init__(self, debug=None):
		if debug:
			self.pt = MerklePatriciaTree(debug=True, from_scratch=True)
		else:
			self.pt = MerklePatriciaTree(debug=False, from_scratch=True)

	def pt_test_suite1(self):
		self.pt.insert("dog")
		self.pt.insert("doge")
		self.pt.insert("dogging")
		self.pt.insert("god")
		self.pt.insert("doggie")


		self.pt.remove("dog")
		self.pt.remove("doge")
		self.pt.remove("dogging")
		self.pt.remove("god")
		self.pt.remove("doggie")

	def pt_performance_suite1_dictionary(self, dict_file=None):
		add_times = dict()
		del_times = dict()
		for i in range(1000, 99000, 1000):
			add_times[i] = self._pt_test_insert_dict(num_lines=i)
			del_times[i] = self._pt_test_remove_dict(num_lines=i)

		print("Addition times:")
		for k, v in sorted(add_times.items()):
			print(k, " ", v)
		print()

		print("Deletion times:")
		for k, v in sorted(del_times.items()):
			print(k, " ", v)

	def _pt_test_insert_dict(self, dict_file=None, num_lines=None):
		if dict_file:
			dictionary = open(dict_file, 'r')
		else:
			dict_file = "/usr/share/dict/words"
			dictionary = open(dict_file, 'r')
		lines = dictionary.readlines()
		if num_lines:
			lines = lines[:num_lines]
		t = time.time()
		for l in lines:
			self.pt.insert(l)
		elapsed_time = time.time() - t
		print("Addition: " + str(len(lines)) + " lines in " + str(elapsed_time) + " seconds")
		return elapsed_time

	def _pt_test_remove_dict(self, dict_file=None, num_lines=None):
		if dict_file:
			dictionary = open(dict_file, 'r')
		else:
			dict_file = "/usr/share/dict/words"
			dictionary = open(dict_file, 'r')
		lines = dictionary.readlines()
		if num_lines:
			lines = lines[:num_lines]
		t = time.time()
		for l in lines:
			self.pt.remove(l)
		elapsed_time = time.time() - t
		print("Deletion: " + str(len(lines)) + " lines in " + str(elapsed_time) + " seconds")
		return elapsed_time


	def encoding_test_suite1(self):
		self._test_nib("dog", [1, 0, 6, 4, 6, 15, 6, 7])
		self._test_nib("horse", [1, 0, 6, 8, 6, 15, 7, 2, 7, 3, 6, 5])
		self._test_nib("do", [1, 0, 6, 4, 6, 15])
		self._test_nib("doge", [1, 0, 6, 4, 6, 15, 6, 7, 6, 5])

	def encoding_test_suite2(self):
		self._test_binnib(binstr("dog"), [1, 0, 6, 4, 6, 15, 6, 7])
		self._test_binnib(binstr("horse"), [1, 0, 6, 8, 6, 15, 7, 2, 7, 3, 6, 5])
		self._test_binnib(binstr("do"), [1, 0, 6, 4, 6, 15])
		self._test_binnib(binstr("doge"), [1, 0, 6, 4, 6, 15, 6, 7, 6, 5])

	def encoding_test_ext(self):
		e = ExtensionNode(subnib_to_binstr([15, 7, 2, 7, 3, 6, 5]), b"qweqwe")
		print(e)
		binstr = binstr_to_nib(e.key)
		print(binstr)
		be = ExtensionNode(nib_to_binstr(binstr), b'asdasd')
		print(be)

	def _test_nib(self, word, expected_nibbles):
		nib = str_to_nib(word)
		if nib != expected_nibbles:
			print("ERROR! nibbles(" + word + ")=", str_to_nib(word), ". Expected:", expected_nibbles)

	def _test_binnib(self, word, expected_nibbles):
		nib = binstr_to_nib(word)
		if nib != expected_nibbles:
			print("ERROR! nibbles(" + word.decode('utf-8') + ")=", binstr_to_nib(word), ". Expected:", expected_nibbles)

if __name__ == "__main__":
	tester = PTTester(debug=False)
	tester.pt_performance_suite1_dictionary()
