import os,glob,functools,Levenshtein,io,datetime,logging
from os.path import join
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
from opencc import OpenCC
from pytz import timezone

utc_now = datetime.datetime.utcnow()
tzTW = timezone('Asia/Taipei')
utc = timezone('UTC')
utc_now.replace(tzinfo=utc).astimezone(tzTW)

logger = logging.getLogger('useHintASR')
logger.setLevel(logging.DEBUG)
formatter=logging.Formatter('%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')
fh = logging.FileHandler('useHintASR.log', mode='a',encoding='utf8')
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)
logger.addHandler(fh)

def googleASR(hints,filename,audiopath,client):
    config = types.RecognitionConfig(
    encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=16000,
    language_code='zh-TW',
    speech_contexts=[speech.types.SpeechContext(phrases=hints)]
    )
    
    #logging.info('process'+filename)
    # Loads the audio into memory
    with io.open(audiopath, 'rb') as audio_file:
        content = audio_file.read()
        audio = types.RecognitionAudio(content=content)

    # Detects speech in the audio file
    response = client.recognize(config, audio)
    googleresult = ''
    confidence = ''
    for result in response.results:
        try:
            googleresult = result.alternatives[0].transcript
        except Exception as e:
            googleresult = ''
        try:
            confidence = result.alternatives[0].confidence
        except Exception as e:
            confidence = ''
        break
    return googleresult,confidence
def myCompare(a,b):
    if( int(a.split('.')[-2]) > int(b.split('.')[-2]) ):
            return 1
    elif(int(a.split('.')[-2]) < int(b.split('.')[-2]) ):
            return -1
    else:
            return 0

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'googlespeech.json'#""
client = speech.SpeechClient()
googleSearchfolder = 'humanCrawl'
firstASRres = 'firstASR'
secondASRres = 'secondASR'
segoutdirA = 'inputPCM'
regularresult = 'regular_result'
cc = OpenCC('s2t')

if not os.path.exists(secondASRres):
    os.makedirs(secondASRres)

with open(join(regularresult,'hintlist'),'r',encoding='utf8') as f:
    for line in f.readlines():
        line = line.strip()
        filename = line.split('\t')[0]
        goalfilepath = [join(googleSearchfolder,os.path.basename(x)) for x in glob.glob(join(googleSearchfolder,(filename+'*')))]
        
        if not goalfilepath:
            continue
        else:
            print('process',goalfilepath)
        
        data = ''.join([line for lin in open(goalfilepath[0],'r',encoding='utf8')])
        data = cc.convert(data)
        hint = line.split('\t')[1].split(',')
        audiofname = filename+'.pcm'
        audiolist = [join(segoutdirA,os.path.basename(x)) for x in glob.glob(segoutdirA+'\\'+filename+'*')]
        audiolist= sorted(audiolist, key=functools.cmp_to_key(myCompare))
        logger.info(filename+'\t audiolist'+str(audiolist))
        nowASRresult = []
        print('copy'+filename)
        if not [x for x in glob.glob(firstASRres+'\\'+filename+'*')]:
            continue
        with open(join(firstASRres,filename+'.cm'),'r',encoding='utf8') as fread:
            freadin = fread.readlines()
            lastgoogleASRresult = []
            for line in freadin:
                if line == '\n' or line == '': continue
                else:
                    try: lastgoogleASRresult.append(line.strip().split('\t')[1])
                    except: logger.warning('cm file has some error' + line)
        
        for audiopath in audiolist:
            googleresult,confidence = googleASR(hint,filename,audiopath,client)
            with open(join(secondASRres,filename)+'.cm','a',encoding='utf8') as fw:
                fw.write('1\t'+googleresult+'\t'+confidence+'\n')
            if googleresult == '': 
                print(audiopath+' ASR empty')
            else: 
                nowASRresult.append(googleresult)
        
        logger.info('now ASR:'+'\n'+ ''.join(nowASRresult))
        logger.info('last ASR:'+'\n'+' '.join(lastgoogleASRresult))
        logger.info(str(Levenshtein.ratio(data,','.join(nowASRresult)))+'/'+str(Levenshtein.ratio(data,','.join(lastgoogleASRresult))))
        if Levenshtein.ratio(data,','.join(nowASRresult)) > Levenshtein.ratio(data,','.join(lastgoogleASRresult)):
            logger.info('good')
            print('good')
        elif Levenshtein.ratio(data,','.join(nowASRresult)) == Levenshtein.ratio(data,','.join(lastgoogleASRresult)):
            logger.info('equal')
        else:
            logger.warning('check')
            print('check!!!')
        