import binascii
from rlp.utils import ascii_chr

HEX_SEQUENCE_ODD  = 1
HEX_SEQUENCE_EVEN = 2
# if even: zero second nibble of first pair and ignore it

asciihex_to_int = {}
int_to_asciihex = {}
for i, c in enumerate(b'0123456789abcdef'):
	asciihex_to_int[c] = i
	int_to_asciihex[i] = c


def binstr(string):
	return bytes(string, 'utf-8')


def str_to_nib(string):
	return binstr_to_nib(binstr(string))


def hexdigest_to_nib(hexdigest):
	if len(hexdigest) % 2:
		nib = [HEX_SEQUENCE_ODD]
	else:
		nib = [HEX_SEQUENCE_EVEN, 0]
	nib += [int(char, 16) for char in hexdigest]
	return nib


def binstr_to_nib(string):
	nib = [asciihex_to_int[char] for char in binascii.hexlify(string)]
	return nib


def nib_to_binstr(nibblearr):
	if len(nibblearr) % 2:
		raise Exception("nibbles must be of even numbers")
	if nibblearr[0] == HEX_SEQUENCE_EVEN:
		starting_index = 2
	elif nibblearr[0] == HEX_SEQUENCE_ODD:
		starting_index = 1
	else:
		raise Exception("nibblearr starts with unexpected number:", nibblearr)
	return subnib_to_binstr(nibblearr[starting_index:])


def subnib_to_binstr(nibblearr):
	# Used in situation, when you take nibblearr not from the beginning, thus lost 1 char with metadata
	if len(nibblearr) % 2:
		nibblearr = [HEX_SEQUENCE_ODD] + nibblearr
	else:
		nibblearr = [HEX_SEQUENCE_EVEN, 0] + nibblearr
	binstring = b''
	for i in range(0, len(nibblearr), 2):
		if nibblearr[i] > 15 or nibblearr[i] < 0:
			raise Exception("invalid nibblearr[" + str(i) + "] =", nibblearr[i])
		if nibblearr[i + 1] > 15 or nibblearr[i + 1] < 0:
			raise Exception("invalid nibblearr[" + str(i+1) + "] =", nibblearr[i+1])
		binstring += ascii_chr(16 * nibblearr[i] + nibblearr[i + 1])
	return binstring
