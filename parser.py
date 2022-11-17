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
        self.line_num=0
        self.error_list=[]
        self.line_buffer=''
        self.line_buffer_num=0

    # TODO
    def parse(self):
        """
        Parse a program.
        Output "valid program" or a string listing errors."""
        return self.error_list

    def next_nonblank(self):
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

    def next_ch(self):
        """
        Call next(self.program_gen), increment self.line_num if necessary"""
        n=next(self.program_gen)
        if n == '\n':
            self.line_num += 1
        return n

    def next_line(self):
        """
        Set the self.line_buffer variable by reading until the next period."""
        self.line_buffer = ''
        self.line_buffer_num=self.line_num
        n=self.next_nonblank()
        while n!='.':
            self.line_buffer+=n
            n=self.next_ch()
        self.line_buffer+='.'

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
        outputs_lst.append(str(i)+".txt:\n")
        if len(output) == 0:
            outputs_lst.append("Valid program")
        else:
            outputs_lst.append('\n'.join(output))
        i+=1
    return 0

if __name__=="__main__": exit(main())
