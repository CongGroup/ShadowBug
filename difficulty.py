import angr
import sys
import claripy
import logging
import math
from config import *

function_list = ["strncmp", "strcmp", "memcmp"]

global path_abs

rebase_addr = 0x400000

def cut_nonlinear(c):
    c.args = list(c.args)
    
    for im in range(len(c.args)):
        cut_list = []
        
        for ia, ar in enumerate(c.args[im].args):
            if(isinstance(ar, claripy.ast.bv.BV) and len(ar.variables)>1):
                cut_list.append(ia)
# TODO x^y not consider
        new_args = list(ar if ia not in cut_list else claripy.BVV(0, 32) for ia, ar in enumerate(c.args[im].args))
        # print("new:  ", new_args)
        c.args[im] = c.args[im].swap_args(new_args)

    return c

def extract_linear(c):
    
    if c.op == "Not":
        tc = cut_nonlinear(c.args[0])
    else:
        tc = cut_nonlinear(c)
    # Iregular constraints
    
    for ia in tc.args:
        if ia.op in ["If"]:
            return None
        for var in ia.variables:
            for b_func in function_list:
                if b_func in var:
                    return None 
    if tc.op in ["And", "Or", "Not"]:
        return None
    
    return tc.args[0] - tc.args[1]

path_to_binary = './dummy'

p = angr.Project(path_to_binary, load_options={"auto_load_libs":False})

data_len = 160
bitlen = 8
sp_ratio = 1

filename = 'input'
# simfile = angr.SimFile(filename, content=data)
with open(filename, "rb") as f:
    seed_cont = f.read()
data_len = min(len(seed_cont), data_len)
affected_bytes = []

# readble CFG from PIN?
seed_path = []
bytevar = [claripy.BVS('bytevar_%d' % i, bitlen) for i in range(data_len)]
# Find affected input bytes && calculate sp

data = [claripy.BVS('data_%d' % i, bitlen) for i in range(data_len)]
for j in affected_bytes:
    data[j] = claripy.BVV(seed_cont[j], 8)
print(affected_bytes)
print(data)
path_abs_interval = claripy.Solver()
path_abs_poly = []
content = claripy.Concat(*data)
simfile = angr.SimFile(filename, content=content)
# simfile_concre = angr.SimFile(filename, content=seed_cont)
state =  p.factory.full_init_state(
                        args=[path_to_binary], 
                        fs={filename: simfile},
                        add_options={angr.options.LAZY_SOLVES})

while True:
    while True:
        succ = state.step()
        if len(succ.successors) == 2 or len(succ.successors) == 0:
            break
        state = succ.successors[0]
    if len(succ.successors) == 0:
        break

    cur_addr = state.addr
    print(hex(cur_addr))
    if cur_addr not in seed_path:
        print("can't follow seed path")
        exit(-1)
    pos = seed_path.index(cur_addr)
    
    seed_path = seed_path[pos+1:]
    st1, st2 = succ.successors
    if st1.addr not in seed_path:
        p1 = -1
    else:
        p1 = seed_path.index(st1.addr)
    if st2.addr not in seed_path:
        p2 = -1
    else:
        p2 = seed_path.index(st2.addr)
    # print([hex(a) for a in seed_path], p1, p2)
    if p1==-1 and p2 == -1:
        print("can't follow seed path")
        exit(-1)
    if p1 == -1:
        st_nd = st2
    elif p2 == -1:
        st_nd = st1
    else:
        if p1<p2:
            st_nd = st1
        else:
            st_nd = st2
    print(hex(st1.addr), hex(st2.addr), "=>", hex(st_nd.addr))
    state = st_nd
    # print(st_nd.solver.constraints)
    # last constraints opt
    if not st_nd.solver.satisfiable():
        print("last opt: ****")
        last_cons =  st_nd.solver.constraints[-1]
        while len(st_nd.solver.constraints):
            st_nd.solver.constraints.pop()
        st_nd.solver.reload_solver()
        st_nd.solver.add(last_cons)
        if not st_nd.solver.satisfiable():
        # can't even solve last cons, just reload
            st_nd.solver.constraints.pop()
            st_nd.solver.reload_solver()
        # clear all path abstractions based on unsatisfiable cons
        while len(path_abs_interval.constraints):
            path_abs_interval.constraints.pop()
        continue

    for c in st_nd.solver.constraints:
        tc = st_nd.solver.simplify(c)
        if tc.op == "Or":
            continue
        
        if tc.is_true():
            continue
        tc = extract_linear(tc)
        if tc is None:
            continue    
        print(tc)   
        li = st_nd.solver.simplify(tc.args[0])
        mini = st_nd.solver.min(li)
        maxi = st_nd.solver.max(li)
        path_abs_poly.append(li>=mini)
        path_abs_poly.append(li<=maxi)
    

# TODO give corsed difficulty
# manually locate some insert places
# grined difficulty and insert bugs
    
    upper_bound = 2**bitlen - 1
    for i in range(data_len):
        
        mini = st_nd.solver.min(data[i])
        maxi = st_nd.solver.max(data[i])
        # print(mini, maxi)
        if mini == 0 and maxi == upper_bound:
            continue
        if mini == maxi:
            path_abs_interval.add(bytevar[i] == mini)
        else:
            path_abs_interval.add(bytevar[i]>=mini)
            path_abs_interval.add(bytevar[i]<=maxi)
        if i in affected_bytes:
            continue
        else:
            affected_bytes.append(i)

upper_bound = 2**bitlen - 1

for li_cons in path_abs_poly:
    path_abs_interval.add(li_cons)
    if not path_abs_interval.satisfiable():
        path_abs_interval.constraints.pop(-1)

print(path_abs_interval.constraints)

for i in affected_bytes:
    mini = path_abs_interval.min(bytevar[i])
    maxi = path_abs_interval.max(bytevar[i])
    sp_ratio *= (maxi-mini+1)/(upper_bound)

print(math.log(sp_ratio, 0.1))
    
