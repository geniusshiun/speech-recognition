
from os.path import join
import io,glob,os,sys,functools,re
import logging
import jieba.analyse,jieba,time
import multiprocessing as mp
from opencc import OpenCC

def myCompare(a,b):
    if( int(a.split('.')[-2]) > int(b.split('.')[-2]) ):
            return 1
    elif(int(a.split('.')[-2]) < int(b.split('.')[-2]) ):
            return -1
    else:
            return 0

def gethint(line):    
      
    line = line.strip()
    if len(line.split('\t')) < 11:
        return ''
    abspath = line.split('\t')[0]
    data = line.split('\t')[11]
    filename = abspath[-19:-11]
    if len(re.findall('(A\d+)',filename)) == 0:
        return ''
    if data == '':
        return ''
    afterjieba = []
    #print(abspath,data[:3],filename)
    
    seg_list = jieba.analyse.extract_tags(data, 500)
    for item in seg_list:
        if item in afterjieba:
            continue
        else:
            if re.findall('[一-龥A-Za-z0-9. ]+',item):
                if len(item)==1 or item == '.' or item ==' ': continue
                if len(afterjieba) < 500:
                    afterjieba.append(item)
                else:
                    print('too more keywords!!')
                    break
    return {filename:afterjieba}

if __name__ == '__main__':

    jieba.initialize() 
    path = 'regular_result'
    _pool = mp.Pool()
    tmpdict = {}
    tstart = time.time()
    totaldochintlist = []
    for name in [os.path.basename(x) for x in glob.glob(path+'\*')]:
        print(name)
        try:
            multi_res = [_pool.apply_async(gethint,(line,)) for line in open(join(path,name),'r',encoding='utf8') ]
            hintlist = [res.get() for res in multi_res]
            hintlist = list(filter(lambda a: a != '', hintlist))
            totaldochintlist.extend(hintlist)
        except KeyboardInterrupt:
            _pool.close()
            _pool.join()
        
    tend = time.time()
    print(tend-tstart)
    cc = OpenCC('s2t')
    with open(join(path,'hintlist'),'w',encoding='utf8') as f:
        for eachone in totaldochintlist:
            for goal,jieba in eachone.items():
                jieba = list(filter(lambda a: a != '...', jieba))
                converted = cc.convert(','.join(jieba))
                f.write(goal+'\t'+converted+'\n')
