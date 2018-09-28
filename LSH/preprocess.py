import json
import os
import os.path
import binascii
import random
import time
from tqdm import tqdm


def make_datedict(path):
    """
    make date dictionary depends on month
    : return :
        date dictionary     ex) '2017-01-01', ...
    """
    datedict = {}
    year = path[0:4]
    month = path[4:6]
    form = year+'-'+month+'-{0:0>2}'
    day = 31
    for i in range(1,day):
        datedict[form.format(i)] = []

    return datedict

def month_to_daily(path):
    """
    separate articles by date (delete articles under 30 words)
    : date.json :   ex) '2017-01-01.json',...
    """
    datedict = make_datedict(path)
    data = {}
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print('combine aritcle by date...')
    for d in tqdm(data):
        for date in datedict.keys():
            if date in d.get('date') and len(d.get('body'))>30:
                datedict[date].append(d)

    print('make daily json file ...')
    for date in tqdm(datedict.keys()):
        filename = './NCdata/'+date+'.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(datedict[date], f, ensure_ascii=False)

def read_daily_and_convert_shingle(path, shingle_num):
    """
    read daily articles and make shingles
    : titles :
        list of aritcle title
    : shingles :
        list of shingle
    : shingle_cnt :
        total number of shingles
    """
    with open(path, 'r') as f:
        file = json.load(f)
    ### 지울것
    #file = file[0:1000]

    shingles = []
    titles = []
    shingle_cnt = 0
    print('read daily articles and convert it to shingles ...')
    for i in tqdm(range(len(file))):
        titles.append(file[i]['title'])
        body = file[i]['body']
        shingle = []
        for i in range(0,len(body)-shingle_num):
            str = ' '.join(body[i:i+shingle_num])
            crc = binascii.crc32(str.encode('utf8')) & 0xffffffff
            if crc not in shingle:
                shingle.append(crc)
                shingle_cnt = shingle_cnt + 1
        shingles.append(shingle)

    return file, titles, shingles, shingle_cnt

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

#############################
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

def make_signature(shingles, total_shingle, hash_num):
    """
    make signature from shingles
    : signature :
        signature array (docNum x hashNum)
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
#################################

def hash_signature(signature, hash_num, band_num):
    """
    hash signature
    : hashT :
        hash Table (docNum x bandNum)
    : bucketlist :
        dictionary of hashValue  ex) { 234234:[1,23], ... }
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
    source = set(sig1)
    target = set(sig2)
    total = len(set().union(source,target))
    same = len(source&target)
    return same/total

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

def find_clustroid(signature, hashT, bucketlist):
    numOfDocs = len(titles)
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
                    if saved_jaccard[key] > 0.01 and i not in cluster:
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

        cId = cluster[distance.index(max(distance))]
        left_aritcles.add(cId)

    print(numOfDocs)
    print(len(left_aritcles))
    return left_aritcles

def save_file(idlist, file):
    print('make dialy json file ...')
    for date in tqdm(datedict.keys()):
        filename = './NCdata/'+date+'.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(datedict[date], f, ensure_ascii=False)



if __name__=="__main__":
    #month_to_daily("201703.json")
    file, titles, shingles, total_shingle = read_daily_and_convert_shingle('./NCdata/2017-03-30.json',2)
    #shingleJaccard(shingles,69,titles)

    hash_num = 100
    band_num = 50
    #print(len(titles))
    signature = make_signature(shingles, total_shingle, hash_num)
    #sigJaccard(signature, 100, 69, titles)

    hashT, bucketlist = hash_signature(signature, hash_num, band_num)
    #LSHJaccard(signature, hashT, bucketlist, 69,titles)

    t1 = time.time()
    idlist = find_clustroid(signature, hashT, bucketlist)
    t2 = time.time()-t1
    print('take %f'%(t2))

    save_file(idlist, file)
