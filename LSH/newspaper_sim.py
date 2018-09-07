import os
import os.path
import binascii
import random


def readData(path):
    data = []
    for file in os.listdir(path):
        if file.endswith('.txt'):
            print(os.path.join(path,file))
            with open(os.path.join(path,file), 'r') as f:
                words = f.read().lower().split()
                data.append(words)
    return data

def makeShingle(dataset, shingle_num):
    shingles = []
    shingle_cnt = 0
    for data in dataset:
        shingle = []
        for i in range(0,len(data)-shingle_num):
            str = ' '.join(data[i:i+shingle_num])
            crc = binascii.crc32(str.encode('utf8')) & 0xffffffff
            #shingle.append(str)
            if crc not in shingle:
                shingle.append(crc)
                shingle_cnt = shingle_cnt + 1
        shingles.append(shingle)
    return shingles, shingle_cnt

def shingleJaccard(shingles, id):
    source = shingles[id]
    numOfDocs = len(shingles)
    for i in range(0,numOfDocs):
        target = shingles[i]
        if i != id:
            total = len(set().union(source,target))
            same = len(set(source)&set(target))
            print('%d:%d = %f'%(id,i,same/total))

def MillerRabinPrimalityTest(n):
    assert n >= 2
    # special case 2
    if n == 2:
        return True
    # ensure n is odd
    if n % 2 == 0:
        return False
    # write n-1 as 2**s * d
    # repeatedly try to divide n-1 by 2
    s = 0
    d = n-1
    while True:
        quotient, remainder = divmod(d, 2)
        if remainder == 1:
            break
        s += 1
        d = quotient
    assert(2**s * d == n-1)

    # test the base a to see whether it is a witness for the compositeness of n
    def try_composite(a):
        if pow(a, d, n) == 1:
            return False
        for i in range(s):
            if pow(a, 2**i * d, n) == n-1:
                return False
        return True # n is definitely composite

    for i in range(5):
        a = random.randrange(2, n)
        if try_composite(a):
            return False

    return True # no base tested showed n as composite

def findPrimary(cnt):
    i = 1
    while not MillerRabinPrimalityTest(cnt+i):
        i = i+1
    print('Prime: ', cnt+i)
    return cnt+i

def findCoeff(cnt):
    coeff = []
    max = cnt*2+1
    while(cnt):
        rand = random.randint(0,max)
        if rand+1 not in coeff:
            coeff.append(rand+1)
            cnt = cnt -1
    return coeff

def makeSignature(shingles,shingle_cnt, hash_num):
    C = findPrimary(shingle_cnt)
    Acoeff = findCoeff(hash_num)
    Bcoeff = findCoeff(hash_num)

    signature = []
    for i in range(0,hash_num):
        sig = []
        for shingle in shingles:
            minVal = C+1
            for sVal in shingle:
                val = (Acoeff[i]*sVal + Bcoeff[i]) % C
                if val < minVal:
                    minVal = val
            sig.append(minVal)
        signature.append(sig)
    #print(signature)
    #print(len(signature))
    return signature

def sigJaccard(signature,hash_num,id):
    numOfDocs = len(signature[id])

    for i in range(0, numOfDocs):
        if id != i:
            same = 0
            for h in range(0,hash_num):
                if(signature[h][id] == signature[h][i]):
                    same = same +1
            print('%d:%d = %f'%(id,i,same/hash_num))


if __name__ == "__main__":
    data = readData('./data')

    shingle_num = 2;

    shingles, shingle_cnt = makeShingle(data,shingle_num)
    print("< Shingle Jaccard >")
    shingleJaccard(shingles,1)

    #print(shingle_cnt)
    hash_num = 5
    signature = makeSignature(shingles,shingle_cnt, hash_num)
    print("< MinHash Jaccard >")
    sigJaccard(signature,hash_num, 1)

    print(signature)
    s1 = signature[0]
    for s2 in range(1,len(signature)):
        s1 = list(zip(s1,signature[s2]))

    print(s1)
