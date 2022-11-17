#!/usr/bin/python3
# Gregory Smith     b00095534
# Joseph Press      b00095348
import itertools

class Parser():
    def __init__(self, cont):
        def prog_gen(prog):
            for ch in prog:
                yield ch
        self.contents = cont
        self.program_gen=prog_gen(cont)

    # TODO
    def parse(self):
        """
        Parse a program.
        Output "valid program" or a string listing errors."""
        return ''.join(list(self.program_gen))

    def nextNonBlank(self):
        """
        Return the next non blank character from CPG"""
        n = next(self.program_gen)
        while n.isspace():n = next(self.program_gen)
        return n

    def peek_ch(self):
        """
        Peek at the next character from the program generator.
        Return the peeked value"""
        peek = next(self.program_gen)
        self.program_gen = itertools.chain([peek],self.program_gen)
        return peek

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
        parser = Parser(contents)
        output = parser.parse()
        outputs_lst.append(str(i)+".txt:\n"+output)
        i+=1
    return 0

if __name__=="__main__": exit(main())
