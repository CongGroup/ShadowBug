
# bit_2_ctype = {8:"char", 16:"short", 32:"int", 64:"long"}
gadget_template = {
"flag_start":
        '''
        long {tmp1_name}_flag = 0;
        asm ("push %%rax\\n\\t"
                "pushf\\n\\t"
                "pop %%rax\\n\\t"
                :"=a" ({tmp1_name}_flag));
        '''
        ,
"flag_end":
        '''
        asm("pushf\\n\\t"\ 
            "pop %%rax\\n\\t"
            :"=a" ({tmp1_name}_flag));
        asm("pop %%rax\\n\\t"::); 
        ''',
"pos_var_filter":
        '''
        {tmp1_name} *= 1-is_OF({tmp1_name}_flag);
        ''',
"neg_var_filter":
        '''
        {tmp1_name} *= is_OF({tmp1_name}_flag);
        ''',
"overflow_8":
        '''
        unsigned char {tmp1_name};
        asm(    \"push %%rax\\n\\t\":);
        asm(    \"add ${cons_value}, %%al\\n\\t\"
                :\"=a\" ({tmp1_name})
                :\"a\"({var_name}));
        asm(    \"pop %%rax\\n\\t":);
        ''',
"overflow_16": 
        '''
        unsigned short {tmp1_name};
        asm(    \"push %%rax\\n\\t\":);
        asm(    \"add ${cons_value}, %%ax\\n\\t\"
                :\"=a\" ({tmp1_name})
                :\"a\"({var_name}));
        asm(    \"pop %%rax\\n\\t":);
        ''',
"overflow_32": 
        '''
        unsigned int {tmp1_name};
        asm(    \"push %%rax\\n\\t\":);
        asm(    \"add ${cons_value}, %%eax\\n\\t\"
                :\"=a\" ({tmp1_name})
                :\"a\"({var_name}));
        asm(    \"pop %%rax\\n\\t":);
        ''',

"underflow_8":
        '''
        unsigned char {tmp1_name};
        asm(    \"push %%rax\\n\\t\":);
        asm(    \"sub ${cons_value}, %%al\\n\\t\"
                :\"=a\" ({tmp1_name})
                :\"a\"({var_name}));
        asm(    \"pop %%rax\\n\\t":);
        ''',
"underflow_16": 
        '''
        unsigned short {tmp1_name};
        asm(    \"push %%rax\\n\\t\":);
        asm(    \"sub ${cons_value}, %%ax\\n\\t\"
                :\"=a\" ({tmp1_name})
                :\"a\"({var_name}));
        asm(    \"pop %%rax\\n\\t":);
        ''',
"underflow_32": 
        '''
        unsigned int {tmp1_name};
        asm(    \"push %%rax\\n\\t\":);
        asm(    \"sub ${cons_value}, %%eax\\n\\t\"
                :\"=a\" ({tmp1_name})
                :\"a\"({var_name}));
        asm(    \"pop %%rax\\n\\t":);
        '''
}