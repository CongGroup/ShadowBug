import re
import random

headers = '''#include <sys/types.h>
#include <sys/ipc.h>
#include <sys/shm.h>
'''

shared_var_reg = '''
key_t brid_key = 0xdeadbeef;
int shmid;
char *brid_data;
int* brid_value;

'''

shared_mem_reg = '''

/*  create the segment: */
if ((shmid = shmget(brid_key, %d, 0644 | IPC_CREAT)) == -1) {
    perror("shmget");
    exit(1);
}
/* attach to the segment to get a pointer to it: */
if ((brid_data = shmat(shmid, NULL, 0)) == (void *)-1) {
    perror("shmat");
    exit(1);
}
brid_value = brid_data;
*brid_value = 0;

'''%(4)
shared_mem_det = "if (shmdt(brid_data) == -1){perror(\"shmdt\");exit(1);}\n"
brid_assign_template = "*brid_value = {};\n"


brid_re_pattern = r"^\[(If|For|While|Switch|Main)\](.+\.[c|cpp])\:(\d+)\:(\d+).*"
main_func_pattern = r"^\[Main\](.+\.[c|cpp])\:(\d+)\:(\d+)\|(.+\.[c|cpp])\:(\d+)\:(\d+)"

class BridManager:
    def __init__(self):
        self.brid_matches = {}

    def gen_brid(self, line_off, col_off, source_filename = None):
    # source_filename is enabled for bin with multiple source files
        if source_filename is None:
            brid_id = str(line_off) + "|" + str(col_off)
        else:
            brid_id = str(line_off) + "|" + str(col_off) + "|" + source_filename
        
        brid_value = random.randint(1,10000000)
        while brid_value in self.brid_matches.keys():
            brid_value = random.randint(1,10000000)
        self.brid_matches[brid_value] =  brid_id
        return brid_value

    def find_brid_id(self, brid_value):
        if brid_value in self.brid_matches:
            return brid_matches[brid_value]
        else:
            return None

    def dump(self):
        pass

brid_manager = BridManager()


def brid_ins(brid_info_filename):
    
    with open(brid_info_filename, "r") as f:
        content = f.readlines()
    
    ins_pos = []
    # TODO support for multiple source file and cpp file
    # Now aussume there is only one C file
    path = ''
    main_loc = -1
    for l in content:
        result = re.match(brid_re_pattern, l)
        if result:
            stmt, path, lineOff, colOff = result.groups()
            if stmt == "Main":
                result = re.match(main_func_pattern, l)
                main_sourcefile, startLine, _, __, endLine, _ = result.groups()
                ins_pos.append((int(startLine), -1))
                ins_pos.append((int(endLine), -2))
            else:
                ins_pos.append((int(lineOff), int(colOff)))

    ins_pos = sorted(ins_pos, key = lambda x:x[0], reverse=True)
    source_file = path
    print(path, ins_pos)
    output_source_filename = source_file + ".bridinfo.c"
    source_code = []
    with open(source_file, "r") as f:
        source_code = f.readlines()
    
    for i in range(len(ins_pos)):
        lineOff, colOff = ins_pos[i]
        print(lineOff, colOff)
    # TODO multiple if statements in one line
        if lineOff < 2:
            continue

        if colOff == -1:
        # Main func start
            para_idx = 0
            while "{" not in source_code[lineOff-1+para_idx]:
                para_idx += 1
            source_code[lineOff-1+para_idx] = source_code[lineOff-1+para_idx] + shared_mem_reg
            source_code = source_code[:lineOff-1] + [shared_var_reg] + source_code[lineOff-1:]
            
        elif colOff == -2:
        # Main func end
            ret_idx = 0
            # Find last statement
            # Assume there are no comments after the return or the last statement
            while ";" not in source_code[lineOff-2-ret_idx] and "}" not in source_code[lineOff-2-ret_idx]:
                ret_idx +=1
            if ";" in source_code[lineOff-2-ret_idx]:
                source_code = source_code[:lineOff-2-ret_idx] + [shared_mem_det] + source_code[lineOff-2-ret_idx:]
            elif "}" not in source_code[lineOff-2-ret_idx]:
                source_code = source_code[:lineOff-1-ret_idx] + [shared_mem_det] + source_code[lineOff-1-ret_idx:]
        else:
            brid_value = brid_manager.gen_brid(lineOff, colOff)
            source_code = source_code[:lineOff-1] + [brid_assign_template.format(brid_value)] + source_code[lineOff-1:]
    
    source_code = [headers] + source_code[:]

    with open(output_source_filename, "w") as f:
        for l in source_code:
            f.write(l)    


if __name__ == "__main__":
    brid_ins("./brid_info")
