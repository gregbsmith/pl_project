#!/usr/bin/python3
# Gregory Smith     b00095534
# Joseph Press      b00095348
import itertools

# Current Program Generator that will be set in the parse() function.
# This generator will produce the next non-blank character
# of the input program when next(CPG) is called
CPG = None

def nextNonBlank():
    """
    Return the next non blank character from CPG"""
    n = next(CPG)
    while n.isspace():n = next(CPG)
    return n

def peek():
    """
    Peek at the next element from the CPG generator.
    Return a tuple (peeked_value, original_iterator)"""
    peek = next(CPG)
    CPG = itertools.chain([peek],CPG)
    return peek

# TODO
def parse(contents):
    """
    Parse a program.
    Output "valid program" or a string listing errors."""
    def program_gen(contents):
        for ch in contents:
            #if ch.isspace():continue
            yield ch
    CPG = program_gen(contents)
    return ''.join(list(CPG))

def main() -> int:
    i = 1
    outputs_lst = []
    while True: # loop until file open fails
        try:
            f=open(str(i)+'.txt','r')
        except FileNotFoundError:
            # write the output and terminate
            out = open('parser_output.txt','w')
            out.write('\n'.join(outputs_lst))
            return 0
        # read and parse the contents of the file
        contents = f.read()
        output = parse(contents)
        outputs_lst.append(str(i)+".txt:\n"+output)
        i+=1
    return 0

if __name__=="__main__":
    exit(main())
