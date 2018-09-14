import json
import os
import os.path
import binascii
import random
import time
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def read_json(path):
    data = {}
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    data = sorted(data, key=lambda k: k["date"
    ])
    return data

def get_subdata(path):
    data = read_json(path)
    sub = []
    for d in data:
        if '2017-03-30' in d.get('date'):
            sub.append(d)

    print(len(sub))

    with open('20170330_1.json', 'w', encoding='utf-8') as f:
        json.dump(sub, f, ensure_ascii=False)

def read_subData(path):
    data = []
    with open(path, 'r') as f:
        file = json.load(f)
    data = []
    contents = []
    titles = []
    for i in range(len(file)):
        data.append(file[i]['body'])
        contents.append(file[i]['contents'].split())
        titles.append(file[i]['title'])
    #print(len(data))
    #print(data[0])
    return data, contents, titles

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

from operator import itemgetter

def sigJaccard(signature,hash_num,id,titles):
    numOfDocs = len(signature[id])
    print(titles[id])
    prob = []
    for i in range(0, numOfDocs):
        if id != i:
            same = 0
            for h in range(0,hash_num):
                if(signature[h][id] == signature[h][i]):
                    same = same +1
            if same/hash_num > 0.01:
                prob.append([same/hash_num,titles[i]])
                #print('%s %f'%(titles[i],same/hash_num))

    prob2 = sorted(prob, key=itemgetter(0), reverse=True)
    for prob in prob2:
        if prob[0] > 0.03:
            print(prob)
        else:
            break

def docTosig(signature,hash_num):
    numOfDocs = len(signature[0])
    result = []
    for d in range(0,numOfDocs):
        dochash = []
        for i in range(0,hash_num):
            dochash.append(signature[i][d])
        result.append(dochash)

    return result

def divNhash(signature,hash_num, band_num):
    i = 0
    hashT = [[0 for i in range(len(signature))] for j in range(band_num)]
    print(len(hashT))
    print(len(hashT[0]))

    rowNum = int(hash_num/band_num)
    for doc_idx in range(len(signature)):
        for idx in range(0, band_num):
            #print(idx*rowNum, (idx+1)*rowNum)
            hashT[idx][doc_idx] = hash(tuple(signature[doc_idx][idx*rowNum:(idx+1)*rowNum]))
    return hashT

def divNhash2(signature,hash_num, band_num):
    i = 0
    hashT = [[0 for j in range(band_num)] for i in range(len(signature))]

    rowNum = int(hash_num/band_num)
    for doc_idx in range(len(signature)):
        for idx in range(0, band_num):
            #print(idx*rowNum, (idx+1)*rowNum)
            hashT[doc_idx][idx] = hash(tuple(signature[doc_idx][idx*rowNum:(idx+1)*rowNum]))
            #if doc_idx == 0:
            #    print(hash(tuple(signature[doc_idx][idx*rowNum:(idx+1)*rowNum])))
    #print(hashT[0])
    return hashT

def divNhashBYmyself(signature,hash_num, band_num):
    C = findPrimary(shingle_cnt)
    Acoeff = findCoeff(band_num)
    Bcoeff = findCoeff(band_num)
    hashT = [[0 for i in range(len(signature))] for j in range(band_num)]

    rowNum = int(hash_num/band_num)
    for doc_idx in range(len(signature)):
        for idx in range(0, band_num):

            tmp = [i*Acoeff[idx]+Bcoeff[idx] for i in signature[doc_idx][idx*rowNum:(idx+1)*rowNum]]
            hashT[idx][doc_idx] = sum(tmp) % C

            #hashT[idx][doc_idx] = hash(tuple(signature[doc_idx][idx*rowNum:(idx+1)*rowNum]))
    return hashT

def LSHJaccard(signature, hashT, hash_num, band_num, id,titles):
    numOfDocs = len(signature)
    probabilities = [0 for x in range(numOfDocs)]
    for b in range(band_num):
        for i in range(numOfDocs):
            if hashT[b][id] == hashT[b][i] and id != i:
                #print(signature[id])
                #print(signature[i])
                source = set(signature[id])
                target = set(signature[i])
                total = len(set().union(source,target))
                same = len(source&target)
                probabilities[i] = same/total
                #if(prob > 0.01):
                #    print("id:%d %s, prob: %f" %(i,titles[i], prob))

    for i in range(numOfDocs):
        if(probabilities[i] > 0.01):
            print("id:%d %s, prob: %f" %(i,titles[i], probabilities[i]))

def LSHJaccard2(signature, hashT, hash_num, band_num, id,titles):
    numOfDocs = len(signature)
    probabilities = [0 for x in range(numOfDocs)]

    prob = []
    probID = []
    for b in range(band_num):
        for i in range(numOfDocs):
            if hashT[id][b] == hashT[i][b] and id != i:
                #print(signature[id])
                #print(signature[i])
                source = set(signature[id])
                target = set(signature[i])
                total = len(set().union(source,target))
                same = len(source&target)
                probabilities[i] = same/total
                if same/hash_num > 0.01 and i not in probID:
                    probID.append(i)
                    prob.append([same/hash_num,titles[i]])

    prob2 = sorted(prob, key=itemgetter(0), reverse=True)
    for prob in prob2:
        print(prob)



def lenChk(data,contents,titles):
    sum = 0
    lenList = []
    Max = 0
    for i in range(len(data)):
        lenList.append(len(data[i]))
    lenList.sort()
    cntList = [ 0 for x in range(30)]
    #print(len(cntList))
    #print(max(lenList))
    tiList = [ 0 for x in range(30)]
    for i in range(len(data)):
        #print(lenList[i])
        if 2 <= int(len(data[i])/10) and int(len(data[i])/10) < 3:
            print(titles[i])

        if int(len(data[i])/10) < 30:
            if int(len(contents[i])/10) == 0:
                tiList[int(len(data[i])/10)] = tiList[int(len(data[i])/10)] +1
            elif '포토' in titles[i] or '부고' in titles[i] or '날씨' in titles[i] or '속보' in titles[i]:
                tiList[int(len(data[i])/10)] = tiList[int(len(data[i])/10)] +1
            cntList[int(len(data[i])/10)] = cntList[int(len(data[i])/10)]+1
    print(cntList[0:5])
    print(tiList[0:5])
    plt.plot(cntList[0:5])
    plt.plot(label='Document Length')
    plt.plot(tiList[0:5],'red')
    red_patch = mpatches.Patch(color='red', label='less important articles')
    blue_patch = mpatches.Patch(color='blue', label='total articles')
    plt.xlabel('length/10')
    plt.ylabel('number of articles')
    plt.legend(handles=[blue_patch,red_patch])
    #plt.axis([0, 300, 0, 150])
    plt.show()
    #plt.savefig('tmp.png')


if __name__=="__main__":
    #get_subdata("201703.json")

    data,contents, titles = read_subData('2017-03-30.json')
    #lenChk(data,contents, titles)


    shingle_num = 2
    shingles, shingle_cnt = makeShingle(data, shingle_num)
    #shingles, shingle_cnt = makeShingle(contents, shingle_num)
    #"""
    print("< Shingle Jaccard >")
    #shingleJaccard(shingles,0)


    hash_num = 100
    signature = makeSignature(shingles,shingle_cnt, hash_num)
    print("< MinHash Jaccard >")
    t1 = time.time()
    sigJaccard(signature,hash_num, 6,titles)
    t2 = time.time()-t1
#    print("----------",t2)


    transSig = docTosig(signature,hash_num)


    band_num = 50
    hashT = divNhash2(transSig,hash_num, band_num)
    #hashT = divNhashBYmyself(transSig,hash_num, band_num)
    #"""
    print("< LSH Jaccard >")
    t1 = time.time()
    LSHJaccard2(transSig, hashT, hash_num, band_num,6,titles)
    t2 = time.time()-t1
    print("----------",t2)
    #"""
