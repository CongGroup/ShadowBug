
/*! @file
 *  This is an example of the PIN tool that demonstrates some basic PIN APIs 
 *  and could serve as the starting point for developing your first PIN tool
 */

#include "pin.H"
#include <iostream>
#include <fstream>
#include <sys/types.h>
#include <sys/ipc.h>
#include <sys/shm.h>
using std::cerr;
using std::endl;
using std::string;

#define SHM_SIZE 4

/* ================================================================== */
// Global variables
/* ================================================================== */

UINT64 path_len    = 0; //number of dynamically executed basic blocks
UINT64 threadCount = 0; //total number of threads, including main thread

std::ostream* out = &cerr;
key_t key = 0xdeadbeef;
int shmid;
void *data;

static UINT64 icount = 0;
UINT64 cur_bbl_addr = 0;
UINT64 cur_ins_bbl_addr = 0;
/* ===================================================================== */
// Command line switches
/* ===================================================================== */
KNOB< string > KnobOutputFile(KNOB_MODE_WRITEONCE, "pintool", "o", "", "specify file name for MyPinTool output");

INT32 Usage()
{
    cerr << "This tool prints out the number of dynamically executed " << endl
         << "instructions, basic blocks and threads in the application." << endl
         << endl;

    cerr << KNOB_BASE::StringKnobSummary() << endl;

    return -1;
}

// This function is called before every instruction is executed
VOID docount() { 
    if (!cur_ins_bbl_addr){
        cur_ins_bbl_addr = cur_bbl_addr;
    }
    else if (cur_ins_bbl_addr != cur_bbl_addr){    
        *out <<"[INSCNT][Addr]"<<std::hex<<cur_ins_bbl_addr<<"|[Value]"<< std::setbase(10) <<icount<<std::endl;
        cur_ins_bbl_addr = cur_bbl_addr;
    }
    
    icount++; 

}

// Pin calls this function every time a new instruction is encountered
VOID Instruction(INS ins, VOID* v)
{
    // Insert a call to docount before every instruction, no arguments are passed
    INS_InsertCall(ins, IPOINT_BEFORE, (AFUNPTR)docount, IARG_END);
    
}

VOID path_tracing(UINT64 bbl_addr)
{
    if (1){
        path_len++;
        *out <<"[BRID][Addr]"<<std::hex<<bbl_addr<<"|[Value]"<< std::setbase(10) <<*(int*)data<<"[Len]"<<path_len<<std::endl;
        cur_bbl_addr = bbl_addr;
    }
}

VOID Trace(TRACE trace, VOID* v)
{
    // Visit every basic block in the trace
    for (BBL bbl = TRACE_BblHead(trace); BBL_Valid(bbl); bbl = BBL_Next(bbl))
    {
        // Insert a call to CountBbl() before every basic bloc, passing the number of instructions
        // *out <<"bbl addr:"<<std::hex<<BBL_Address(bbl)<<std::endl;
        BBL_InsertCall(bbl, IPOINT_BEFORE, (AFUNPTR)path_tracing, IARG_UINT64, BBL_Address(bbl), IARG_END);
    }
}

VOID ThreadStart(THREADID threadIndex, CONTEXT* ctxt, INT32 flags, VOID* v) { threadCount++; }

VOID Fini(INT32 code, VOID* v)
{
    *out<<endl;
}

int main(int argc, char* argv[])
{
    // Initialize PIN library. Print help message if -h(elp) is specified
    // in the command line or the command line is invalid
    if (PIN_Init(argc, argv))
    {
        return Usage();
    }

    string fileName = KnobOutputFile.Value();

    if (!fileName.empty())
    {
        out = new std::ofstream(fileName.c_str());
    }

    if ((shmid = shmget(key, SHM_SIZE, 0644 | IPC_CREAT)) == -1) {
        perror("shmget");
        exit(1);
    }


    /* attach to the segment to get a pointer to it: */
    if ((data = shmat(shmid, NULL, 0)) == (void *)-1) {
        perror("shmat");
        exit(1);
    }
    
    memset(data, sizeof(char), SHM_SIZE);    

    // Register function to be called to instrument traces
    TRACE_AddInstrumentFunction(Trace, 0);

    // Register function to be called for every thread before it starts running
    PIN_AddThreadStartFunction(ThreadStart, 0);
    
    INS_AddInstrumentFunction(Instruction, 0);

    // Register function to be called when the application exits
    PIN_AddFiniFunction(Fini, 0);
    

    // Start the program, never returns
    PIN_StartProgram();
    
    if (icount != 0){
        *out <<"[INSCNT][Addr]"<<std::hex<<cur_ins_bbl_addr<<"|[Value]"<<icount<<std::endl;
    }

    /* detach from the segment: */
    if (shmdt(data) == -1) {
        perror("shmdt");
        exit(1);
    }
    return 0;
}
