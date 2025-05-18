import os


def get_end_line(lines,start_line):
    bracket_stack=[]
    content_start_line=start_line
    content_end_line=start_line
    find_function_body=False
    left_bracket=0
    for line in range(start_line-1,len(lines)):
        if not find_function_body:
            if '{' in lines[line]:
                # If '{' is at the beginning or end of the line, it is likely the start of a function body
                l=lines[line].strip()
                if l[0]=='{' or l[-1]=='{':
                    find_function_body=True
                    if len(l)>1: # If the line contains both the function signature and '{', the next line is the actual start of the function body
                        content_start_line=line+2
                    else:
                        content_start_line=line+1
                left_bracket+=1
            else:
                continue
        elif '{' in lines[line] or '}' in lines[line]:
            left_bracket+=lines[line].count('{')
            left_bracket-=lines[line].count('}')
            if left_bracket==0:
                content_end_line=line+1
                return [content_start_line,content_end_line] # Return the line numbers where '{' and '}' are found
   
def get_end_line_(lines,start_line):
    bracket_stack=[]
    content_start_line=start_line
    content_end_line=start_line
    find_function_body=False
    left_bracket=0
    for line in range(start_line-1,len(lines)):
        if not find_function_body:
            if '{' in lines[line]:
                # If '{' is at the beginning or end of the line, it is likely the start of a function body
                l=lines[line].strip()
                if l[0]=='{' or l[-1]=='{':
                    find_function_body=True
                    if len(l)>1: # If the line contains both the function signature and '{', the next line is the actual start of the function body
                        content_start_line=line+2
                    else:
                        content_start_line=line+1
                left_bracket+=1
            else:
                continue
        elif '{' in lines[line] or '}' in lines[line]:
            left_bracket+=lines[line].count('{')
            left_bracket-=lines[line].count('}')
            if left_bracket==0:
                content_end_line=line+1
                return [content_start_line,content_end_line] # Return the line numbers where '{' and '}' are found
            if lines[line]=='}\n':
                content_end_line=line+1
                return [content_start_line,content_end_line] # Return the line numbers where '{' and '}' are found      


def parse_c_file_by_line(file_path):
    delete_lines=[]
    with open(file_path,'r',errors='ignore') as f:
        lines=f.readlines()
        for i,line in enumerate(lines):
            line_number=i+1
            if line_number==36:
                a=1
            if line.strip().endswith('{'):
                line_info=get_end_line(lines,line_number)
                # Handle bracket matching issues in C code
                if line_info==None:
                    line_info=get_end_line_(lines,line_number)
                start_line=line_info[0]
                end_line=line_info[1]
                delete_lines.append((start_line,end_line)) # Store the start and end line numbers of the function body (i.e., lines containing '{' and '}')
    return delete_lines


# Input format: /path/kernel/linux-5.6.7/drivers/acpi/acpi_lpss.c
def summary_file_by_Fline(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return None
    useless_line=parse_c_file_by_line(file_path)
    refined_file=''
    with open(file_path,'r',errors='replace') as f:
        all_lines=f.readlines()
        for i in range(len(all_lines)):
            line=all_lines[i]
            line_number=i+1
            is_useless=False
            for t in useless_line:
                if line_number>=t[0] and line_number<=t[1]:
                    is_useless=True
                    break
            if is_useless:
                #print(f"delete line:{line_number}")
                continue
            else:
                if line.strip().endswith('= {'):
                    line=line.replace('= {','')
                if line.strip().endswith('{'):
                    line=line.replace('{','')
                refined_file+=line
    return refined_file 