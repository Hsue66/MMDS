import os
import json
import binascii
from tqdm import tqdm

def make_datedict(path):
    """
    make date dictionary depends on month
    : param path :  file path
    : return datedict :  date dictionary     ex) {'2017-01-01':[], ... }
    """
    days_in_month = [0,31,29,31,30,31,30,31,31,30,31,30,31]
    datedict = {}
    year = path[0:4]
    month = path[4:6]
    form = year+'-'+month+'-{0:0>2}'
    day = days_in_month[(int)(month)]

    for i in range(1,day+1):
        datedict[form.format(i)] = []

    return datedict


def mkdir(dirname):
    """
    make directory
    : param dirname : directory name
    """
    if not os.path.exists(dirname):
        os.makedirs(dirname)


def remove(path):
    """
    remove files in path
    : param path : path
    """
    print('remove temp files ...')
    temp_list = os.listdir(path)
    for file in temp_list:
        os.remove(os.path.join(path, file))


def month_to_daily(path):
    """
    separate articles by date (delete articles under 30 words)
    : param path : date.json    ex) '2017-01-01.json',...
    """
    print('divide aritcle by date...')
    datedict = make_datedict(path)
    data = {}
    with open('./Data/'+path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for d in tqdm(data):
        for date in datedict.keys():
            if date in d.get('date') and len(d.get('body'))>30:
                datedict[date].append(d)

    print('make daily json file ...')
    for date in tqdm(datedict.keys()):
        mkdir('./NCdata/')
        filename = './NCdata/'+date+'.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(datedict[date], f, ensure_ascii=False)


def read_daily_and_convert_shingle(path, shingle_num):
    """
    read daily articles and make shingles
    : param path :  file path
    : param shingle_num :  k value
    : return titles :  list of aritcle title
    : return  shingles :  list of shingle
    : return shingle_cnt :  total number of shingles
    """
    with open(path, 'r') as f:
        files = json.load(f)
    ### 지울것
    #file = file[0:1000]

    shingles = []
    titles = []
    shingle_cnt = 0
    print('read daily articles and convert it to shingles ...')
    for i in tqdm(range(len(files))):
        titles.append(files[i]['title'])
        body = files[i]['body']
        shingle = []
        for i in range(0,len(body)-shingle_num):
            str = ' '.join(body[i:i+shingle_num])
            crc = binascii.crc32(str.encode('utf8')) & 0xffffffff
            if crc not in shingle:
                shingle.append(crc)
                shingle_cnt = shingle_cnt + 1
        shingles.append(shingle)

    return files, titles, shingles, shingle_cnt


def save_file(idlist, files):
    print('make new json file ...')
    newfile = []
    for id in tqdm(idlist):
        newfile.append(files[id])

    filename = './editNCdata/2017_03_301.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(newfile, f, ensure_ascii=False)

def save_newfile(path, newfile):
    mkdir('./editNCdata/')
    filename = './editNCdata/'+path
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(newfile, f, ensure_ascii=False)
