import os, jsonlines,json,bm25s,re


linux_main_root_V0=['boot','drivers','fs','ibcs','include','init','ipc','kernel','lib','mm','net','tools','zBoot']
linux_main_root_V1=['Documentation','arch','drivers','fs','include','init','ipc','kernel','lib','mm','net','scripts']
linux_main_root_V2=['Documentation','arch','block','crypto','drivers','firmware','fs','include','init','ipc','kernel','lib','mm','net','samples','scripts','security','sound','tools','usr','virt']
linux_main_root_V3=['Documentation','arch','block','crypto','drivers','firmware','fs','include','init','ipc','kernel','lib','mm','net','samples','scripts','security','sound','tools','usr','virt']
linux_main_root_V4=['Documentation','LICENSES','arch','block','certs','crypto','drivers','firmware','fs','include','init','ipc','kernel','lib','mm','net','samples','scripts','security','sound','tools','usr','virt']
linux_main_root_V5=['Documentation','LICENSES','arch','block','certs','crypto','drivers','fs','include','init','io_uring','ipc','kernel','lib','mm','net','samples','scripts','security','sound','tools','usr','virt']
linux_main_root_V6=['Documentation','LICENSES','arch','block','certs','crypto','drivers','fs','include','init','io_uring','ipc','kernel','lib','mm','net','rust','samples','scripts','security','sound','tools','usr','virt']
linux_dic={'0':linux_main_root_V0,'1':linux_main_root_V1,'2':linux_main_root_V2,'3':linux_main_root_V3,'4':linux_main_root_V4,'5':linux_main_root_V5,'6':linux_main_root_V6}
re_rule1=re.compile(r"([A-Za-z0-9_\-/]+[A-Za-z0-9_\-/]+\.[a-z]+)\s+")
mail_head_word = ['From:', 'To:', 'Subject:', 'Cc:', 'Date:', 'Message-ID', 'In-Reply-To:']
mail_end_word = ['Signed-off-by:', 'Cc:']
diff_start_word = ['diff --git a','+++','@@']
def normalize_path(search_path):
    norm_path=[]
    for one_path in search_path:
        one_path=one_path.split('/')
        file_path=''
        for dir in one_path:
            a=dir.find('.')
            if dir.find('.')!=-1:
                break
            file_path=file_path+dir+'/'
        if file_path!='' and file_path[:len(file_path)-1] not in norm_path:
            norm_path.append(file_path[:len(file_path)-1])
    return norm_path


def str2int(s):
    num = 0
    for ch in s:
        num = num * 10 + int(ch)
    return num

def time_cmp(time_A, time_B):
    year_A = str2int(time_A[0:4])
    year_B = str2int(time_B[0:4])
    if year_A > year_B:
        return 1
    elif year_A < year_B:
        return -1
    else:
        month_A = str2int(time_A[5:7])
        month_B = str2int(time_B[5:7])
        if month_A > month_B:
            return 1
        elif month_A < month_B:
            return -1
        else:
            day_A = str2int(time_A[8:])
            day_B = str2int(time_B[8:])
            if day_A > day_B:
                return 1
            elif day_A < day_B:
                return -1
            else:
                return 0


def find_mails_simplify(search_path,query_titles,bug_date='2000-01-01'):
    mail_titles=[]
    # Merge mail data for the entire conversation, used for similarity matching or GPT enhancement
    merge_mail_data=[]
    # Only patch mail data, used for similarity matching or GPT enhancement
    patch_mail_data=[]
    # Patch content
    # patch_data=[]

    # search_path=normalize_path(search_path)
    summary=query_titles[0]
    query_titles=[summary]
    # For fast retrieval, directly search the mail dataset based on the target path
    mail_dataset_path = "./new_mail_dataset"

    # There may be multiple search paths, each one needs to be searched
    for one_path in search_path:
        one_path = one_path.replace('.','++')
        file_path = os.path.join(mail_dataset_path, one_path, "mails.json")
        print(f"Processing file: {file_path}")
        if os.path.exists(file_path):
            print('Found search_path ',one_path.replace('++','.'),' in ', file_path.replace('++','.'))
            f=open(file_path,'r')
            for item in jsonlines.Reader(f):
                title = item['title']
                mail_date=item['date'][:len(item['date'])-1]
                print(f"bug date is {bug_date} mail date is {mail_date}")
                if time_cmp(mail_date,bug_date)!=-1:
                    continue
                # merge_mails=item['merge mails']
                patch_mail=item['patch mail'][0]
                # patch_content=item['patch content']
                if title in mail_titles:
                    continue
                mail_titles.append(title)
                #this is for similarity prediction, try using all emails in the conversation for similarity calculation or only use patch emails for similarity calculation
                # merge_mail_data.append(merge_mails)
                if patch_mail not in patch_mail_data:
                    patch_mail_data.append(patch_mail)
                            # patch_data.append(patch_content)
    # return (patch_mail_data,merge_mail_data)
    return (patch_mail_data, [])

def BM25s(query_titles,mail_data,topK,result_path):
    f=open(result_path,'a')
    corpus = mail_data
    if len(corpus)==0:
        data={'email_content':['']}
        f.write(json.dumps(data)+'\n')
        return

    # optional: create a stemmer
    #stemmer = Stemmer.Stemmer("english")

    # Tokenize the corpus and only keep the ids (faster and saves memory)
    corpus_tokens = bm25s.tokenize(corpus, stopwords="en")

    # Create the BM25 model and index the corpus
    retriever = bm25s.BM25()
    retriever.index(corpus_tokens)
    search_results=[]
    patch_results=[]
    for query in query_titles:
        #mail4one_query+=(query_prompt[query_title.index(query)]+'\n')
        if len(query)==0:
            continue
    # Query the corpus
        query_tokens = bm25s.tokenize(query)
        # Get top-k results as a tuple of (doc ids, scores). Both are arrays of shape (n_queries, k)
        if len(corpus)>=topK:
            results, scores = retriever.retrieve(query_tokens, corpus=corpus, k=topK)
            for i in range(results.shape[1]):
                doc, score = results[0, i], scores[0, i]
                print(f"Rank {i+1} (score: {score:.2f}): {doc}")
                search_results.append(doc)
                # patch_index=corpus.index(doc)
                # patch_results.append(patch_data[patch_index])
        else:
            results, scores = retriever.retrieve(query_tokens, corpus=corpus, k=len(corpus))
            for i in range(results.shape[1]):
                doc, score = results[0, i], scores[0, i]
                print(f"Rank {i+1} (score: {score:.2f}): {doc}")
                search_results.append(doc)

    data={'email_content':search_results}
    f.write(json.dumps(data)+'\n')


def extract_patch(mail):
    mail = mail.split('\n')
    print('extracting patch info')
    finish_extract = False
    mail_end_line = 0
    # Loop to find the last line of the mail content
    for content in mail:
        if finish_extract:
            break
        for word in mail_end_word:
            if word in content:
                mail_end_line = mail.index(content)
                break
    if mail_end_line==0:# If no signed-off-by or other end markers found, start extracting patch from the line where diff exists
        for content in mail:
            for word in diff_start_word:
                if word in content and word[0] == content[0]:
                    mail_end_line = mail.index(content)
                    break
        patch_info=''
        for i in range(mail_end_line+1, len(mail)):
            patch_info = patch_info + mail[i]
        return patch_info
    else:
        patch_info = ''
        for i in range(mail_end_line+1, len(mail)):
            patch_info = patch_info + mail[i]+'\n'
        return patch_info
    
def normalize_file_path(file_path):
    each_file=file_path.split('/')
    if each_file[0].isdigit() or each_file[0]=='a' or each_file[0]=='b':
        file_path=file_path[2:]
    no_alpha=True
    for c in each_file[0]:
        if c.isalpha():
            no_alpha=False
            break
    # If the filename only contains numbers and symbols but no letters, it is obviously invalid and should be removed
    if no_alpha:
        each_file.pop(0)
        file_path=''
        for file in each_file:
            file_path+=file
            file_path+='/'
        file_path=file_path[:len(file_path)-1]
    '''It is not reasonable to directly judge if the first file in the path is standard, as we have seen paths like t/xxx.c.
    However, if the second file in the path has a duplicate name in linux_main_root, then the first file in the path is likely dirty data.
    '''
    linux_main_root=[]
    for i in linux_dic.keys():
        for file_name in linux_dic[i]:
            linux_main_root.append(file_name)
    if len(each_file)>1:
        if each_file[0] in linux_main_root:
            return file_path
        if each_file[0] not in linux_main_root and each_file[1] in linux_main_root:
            each_file.pop(0)
            file_path = ''
            for file in each_file:
                file_path += file
                file_path += '/'
            file_path = file_path[:len(file_path) - 1]
        else:
            return ''
    else:
        return ''
    return file_path

def extract_path(mail):
    mail = mail.split('\n')
    file_list=[]
    # print('extracting file info')
    finish_extract=False
    mail_end_line = 0
    for content in mail:
        if finish_extract:
            break
        for word in mail_end_word:
            if word in content:
                mail_end_line = mail.index(content)
                break
        for word in diff_start_word:
            if word in content and word[0] == content[0]:
                finish_extract=True
                for i in range(mail_end_line, mail.index(content)):
                    # if ('.py' in mail[i].lower() or '.s' in mail[i].lower()
                    #         or '.rst' in mail[i].lower() or '.o' in mail[i].lower() or '.ko' in mail[i].lower() or '.sh' in mail[i].lower() or '.yaml' in mail[i].lower()):
                    #     return ''
                    # else:
                    line=mail[i]
                    file_paths=re.findall(re_rule1,mail[i])
                    if len(file_paths)>0:
                        if normalize_file_path(file_paths[0]) not in file_list:
                            file_list.append(normalize_file_path(file_paths[0]))
                break
    return file_list

def search_mails(query_titles:list, 
                search_path:list,
                topK:int,
                result_path:str,
                mail_type='patch',
                bug_date='2025-01-01'):
    find_result = find_mails_simplify(search_path, query_titles, bug_date)
    print("*"*50)
    print(find_result[0])
    if mail_type == 'patch':
        BM25s(query_titles, find_result[0], topK, result_path)
    else:
        BM25s(query_titles, find_result[1], topK, result_path)


def mails_dedupe(mail_list):
    mail_list = [mail[mail.find("*")+1:] for mail in mail_list]
    deduped_mail_list = []
    for mail in mail_list:
        if mail not in deduped_mail_list:
            deduped_mail_list.append(mail)
    return deduped_mail_list
