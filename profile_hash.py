import hashlib
import timeit


def sha1():
    hashlib.sha1("BedWoodenLogExcellent".encode('UTF8')).hexdigest()


hashes = 1000000
time_taken = timeit.timeit(stmt=sha1, number=hashes)
h = 1 / (time_taken / hashes)
print('Approximately {:,.0f} SHA1 hashes/second'.format(h))
