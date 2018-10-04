import os
import random
import time
from tqdm import tqdm
import utils


def MillerRabinPrimalityTest(n):
    """
    find Primary value by Miller_Rabin
    : param n :  number
    : return TRUE/FALSE :  number is primary or not
    """
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
    """
    find primary number
    : param cnt :  total number of shingles
    : return cnt+i :  primary value
    """
    i = 1
    while not MillerRabinPrimalityTest(cnt+i):
        i = i+1
    #print('Prime: ', cnt+i)
    return cnt+i

def findCoeff(cnt):
    """
    find Coeff values
    : param cnt :  number of hash function
    : return coeff :  coeff array
    """
    coeff = []
    max = cnt*2+1
    while(cnt):
        rand = random.randint(0,max)
        if rand+1 not in coeff:
            coeff.append(rand+1)
            cnt = cnt -1
    return coeff

def make_signature(shingles, total_shingle, hash_num):
    """
    make signature from shingles
    : param shingles :  shingle array
    : param total_shingle :  total number of shingles
    : param hash_num :  number of hash function
    : return signature :  signature array (docNum x hashNum)
    """
    C = findPrimary(total_shingle)
    Acoeff = findCoeff(hash_num)
    Bcoeff = findCoeff(hash_num)

    print("make signature from shingles...")
    signature = []
    for shingle in tqdm(shingles):
        sig = []
        for i in range(0,hash_num):
            minVal = C+1
            for each in shingle:
                val = (Acoeff[i]*each + Bcoeff[i]) % C
                if val < minVal:
                    minVal = val
            sig.append(minVal)
        signature.append(sig)

    return signature

def hash_signature(signature, hash_num, band_num):
    """
    hash signature
    : param shingles :  shingle array
    : param hash_num :  number of hash function
    : param band_num :  number of band
    : return hashT :  hash Table (docNum x bandNum)
    : return bucketlist :  dictionary of hashValue  ex) { 234234:[1,23], ... }
    """
    numOfDocs = len(signature)
    hashT = [[0 for j in range(band_num)] for i in range(numOfDocs)]

    bucketlist = {}
    rowNum = int(hash_num/band_num)
    for doc_idx in range(numOfDocs):
        for idx in range(0, band_num):
            hashVal = hash(tuple(signature[doc_idx][idx*rowNum:(idx+1)*rowNum]))
            hashT[doc_idx][idx] = hashVal
            if hashVal not in bucketlist.keys():
                bucketlist[hashVal] = []
            bucketlist[hashVal].append(doc_idx)

    return hashT, bucketlist

def calcJaccard(sig1, sig2):
    """
    calculate jaccard similarity
    : param sig1 :  row of signature
    : param sig2 :  row of signature
    : return same/total :  jaccard similarity
    """
    source = set(sig1)
    target = set(sig2)
    total = len(set().union(source,target))
    same = len(source&target)
    return same/total

def find_clustroid(signature, hashT, bucketlist, jaccard_sim):
    """
    find clustroid
    : param signature :  signature array (docNum x hashNum)
    : param hashT :  hash Table (docNum x bandNum)
    : param bucketlist :  dictionary of hashValue  ex) { 234234:[1,23], ... }
    : param jaccard_sim :  jaccard similarity
    : return left_articles :  set of clustroids
    """
    numOfDocs = len(signature)
    left_aritcles = set([])
    saved_jaccard = dict()

    print('find clustroid and left only clustroid ...')
    for id in tqdm(range(numOfDocs)):
        cluster = []
        for hashVal in hashT[id]:
            simlist = bucketlist[hashVal]
            for i in simlist:
                if i != id:
                    key = str(i)+','+str(id) if id > i else str(id)+','+str(i)
                    if key not in saved_jaccard.keys():
                        saved_jaccard[key] = calcJaccard(signature[id],signature[i])
                    if saved_jaccard[key] > jaccard_sim and i not in cluster:
                        cluster.append(i)
        cluster.append(id)

        distance = []
        for i in range(len(cluster)):
            dist = 0
            for j in range(len(cluster)):
                if i != j:
                    key = str(i)+','+str(id) if id > i else str(id)+','+str(i)
                    if key not in saved_jaccard.keys():
                        saved_jaccard[key] = calcJaccard(signature[i],signature[j])
                    dist = dist + saved_jaccard[key]
            distance.append(dist)

        cId = cluster[distance.index(min(distance))]
        left_aritcles.add(cId)

    #print(numOfDocs)
    #print(len(left_aritcles))
    return left_aritcles

#################################
def shingleJaccard(shingles, id,titles):
    print(titles[id])
    source = shingles[id]
    numOfDocs = len(shingles)
    for i in range(0,numOfDocs):
        target = shingles[i]
        if i != id:
            total = len(set().union(source,target))
            same = len(set(source)&set(target))
            if(same/total > 0.05):
                print('%d %s = %f'%(i,titles[i],same/total))

def sigJaccard(signature,hash_num,id,titles):
    numOfDocs = len(titles)
    print(titles[id])
    source = shingles[id]
    for i in range(0,numOfDocs):
        target = shingles[i]
        if i != id:
            total = len(set().union(source,target))
            same = len(set(source)&set(target))
            if(same/total > 0.05):
                print('%d %s = %f'%(i,titles[i],same/total))

def LSHJaccard(signature, hashT, bucketlist, id,titles):
    numOfDocs = len(titles)
    print(titles[id])
    for hashVal in hashT[id]:
        simlist = bucketlist[hashVal]
        for i in simlist:
            if i != id:
                prob = calcJaccard(signature[id],signature[i])
                if prob > 0.01:
                    print('%d%s: %f'%(i,titles[i],prob))

def read_and_check(path):
    with open(path, 'r') as f:
        files = json.load(f)

    print(len(files))
    cnt = 0
    for i in tqdm(range(len(files))):
        if '박근혜' in files[i]['title'] or '대통령' in files[i]['title'] or "법정" in files[i]['title'] or "중앙지검" in files[i]['title'] or "구속" in files[i]['title'] or "영장" in files[i]['title'] or "심사" in files[i]['title']:
            cnt = cnt + 1
            if cnt < 100:
                print(files[i]['title'])
    print(cnt)


def main(args):
    """
    do preprocessing
    : param args :  arguments
    """
    folder = args.folder
    shingle_num = args.shingle_num
    hash_num = args.hash_num
    band_num = args.band_num
    jaccard_sim = args.jaccard_sim

    rawfile_list = os.listdir(folder)
    for rawfile in rawfile_list:
        print('processing '+rawfile+' ...')
        utils.month_to_daily(folder, rawfile)
        datelist = os.listdir('./NCdata')

        newfile = []
        file_length = 0
        t1 = time.time()
        for filename in datelist:
            print('------'+filename+'------')

            idlist = []
            files, titles, shingles, total_shingle = utils.read_daily_and_convert_shingle('./NCdata/'+filename,shingle_num)
            if total_shingle > 0:
                signature = make_signature(shingles, total_shingle, hash_num)
                hashT, bucketlist = hash_signature(signature, hash_num, band_num)

                idlist = find_clustroid(signature, hashT, bucketlist, jaccard_sim)

            file_length = file_length + len(files)
            for id in idlist:
                newfile.append(files[id])

        print(file_length)
        print(len(newfile))
        utils.save_newfile(rawfile, newfile)

        t2 = time.time()-t1
        print('take %f'%(t2))
        utils.remove('./NCdata')
    #"""

if __name__=="__main__":
    shingle_num = 2
    hash_num = 100
    band_num = 50
    jaccard_sim = 0.05

    rawfile_list = os.listdir('./qData')
    for rawfile in rawfile_list:
        print('processing '+rawfile+' ...')
        utils.month_to_daily(rawfile)
        datelist = os.listdir('./NCdata')

        newfile = []
        file_length = 0
        t1 = time.time()
        for filename in datelist:
            print('------'+filename+'------')

            files, titles, shingles, total_shingle = utils.read_daily_and_convert_shingle('./NCdata/'+filename,shingle_num)
            if total_shingle > 0:
                signature = make_signature(shingles, total_shingle, hash_num)
                hashT, bucketlist = hash_signature(signature, hash_num, band_num)

                idlist = find_clustroid(signature, hashT, bucketlist, jaccard_sim)

            file_length = file_length + len(files)
            for id in idlist:
                newfile.append(files[id])
            break

        print(file_length)
        print(len(newfile))
        utils.save_newfile(rawfile, newfile)

        t2 = time.time()-t1
        print('take %f'%(t2))
        utils.remove('./NCdata')
