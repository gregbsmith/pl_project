#!/usr/bin/python3
# Gregory Smith     b00095534
# Joseph Press      b00095348
# Abdu Sallouh      b00087818
import itertools

class Parser():
    """Parser class that takes a program and tells whether it is valid according
    to the simplified prolog grammar."""

    class ParserError(Exception):
        """Exception raised by the parser
        Attributes:
            message -- explanation of the exception including
            the line number where this exception happened"""
        def __init__(self, description, ln):
            self.message="Line " + str(ln) + ": " + description

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
        self.next_tok=''
        self.specials=['+','-','*','/',"""\""",'^','~',':','.','?',' ','#','$','&']
        self.digits=[str(i) for i in range(10)]
        self.uppercase-chars=[chr(i) for i in range(65,91)]+['_']
        self.lowercase-chars=[chr(i) for i in range(97,123)]

    # TODO implement this
    # backtrack by saving a copy of the self.program_gen in another variable
    def parse(self):
        """Parse a program.
            Output a list of descriptions of errors in the program"""
        self.program()
        return self.error_list

    def program(self):
        """Subroutine for the <program> symbol.
            Valid programs have a <query>, optionally preceded by a <clause-list>."""
        # To preserve the state of self.program_gen and allow reversion back to
        # this state, save program_gen to a backup
        local_errors = []
        program_gen_backup = self.program_gen
        try:
            self.clause_list()
        except ParserError as err:
            local_errors.append(err.message)
            self.program_gen = program_gen_backup
        try:
            self.query()
        except ParserError as err:
            local_errors.append(err.message)
            self.error_list += local_errors
    #TODO
    def clause_list(self):
        pass

    #TODO
    def clause(self):
        pass

    #TODO
    def query(self):
        pass

    #TODO
    def predicate_list(self):
        pass

    #TODO
    def predicate(self):
        pass

    #TODO
    def term_list(self):
        pass

    #TODO
    def term(self):
        pass

    #TODO
    def structure(self):
        pass

    #TODO
    def atom(self):
        pass

    #TODO
    def small_atom(self):
        pass

    #TODO
    def variable(self):
        pass

    def peek_token(self, skip_blanks=False):
        """Retrieve and return the next token without changing the state of
        self.program_gen or the self.next_tok variable"""
        temp_gen = self.program_gen
        n=next(temp_gen)
        if skip_blanks:
            while n.isspace():
                n=next(temp_gen)
        if n == '.':
            return '.'
        elif n==',':
            return ','
        elif n == "'":
            return "'"
        elif n == '(':
            return '('
        elif n == ')':
            return ')'
        elif n == '?':
            if next(temp_gen) == '-':
                return '?-'
            else:
                return 'special'
        elif n == ':':
            if next(temp_gen) == '-':
                return ':-'
            else:
                return 'special'
        elif n in self.specials:
            return 'special'
        elif n in self.digits:
            return 'digit'
        elif n in self.uppercase-chars:
            return 'uppercase-char'
        elif n in self.lowercase-chars:
            return 'lowercase-char'
        else: # unrecognized token
            raise ParserError('Unrecognized token: "' + n + '"', self.line_num)

    def token(self, skip_blanks=False):
        """Store the name of the next token in the self.next_tok variable"""
        if skip_blanks:
            n=self.next_nonblank()
        else:
            n=self.next_ch()

        if n == '.':
            self.next_token = '.'
        elif n == ',':
            self.next_token = ','
        elif n == "'":
            self.next_token = "'"
        elif n == '(':
            self.next_token = '('
        elif n == ')':
            self.next_token = ')'
        elif n == '?':
            if self.peek_ch() == '-':
                self.next_ch() # get rid of '-'
                self.next_token = '?-'
            else:
                self.next_token = 'special'
        elif n == ':':
            if self.peek_ch() == '-':
                self.next_ch() # get rid of '-'
                self.next_token = ':-'
            else:
                self.next_token = 'special'
        elif n in self.specials:
            self.next_token = 'special'
        elif n in self.digits:
            self.next_token = 'digit'
        elif n in self.uppercase-chars:
            self.next_token = 'uppercase-char'
        elif n in self.lowercase-chars:
            self.next_token = 'lowercase-char'
        else: # unrecognized token
            raise ParserError('Unrecognized token: "' + n + '"', self.line_num)

    def add_error(self, message):
        """Add the error message to the list of errors that will be returned by
        this parser."""
        self.error_list.append(message)

    def next_nonblank(self):
        """Return the next non blank character from self.program_gen"""
        n = next(self.program_gen)
        while n.isspace():n = next(self.program_gen)
        return n

    def peek_ch(self):
        """Peek at the next character from the program generator.
            Return the peeked value"""
        peek = next(self.program_gen)
        self.program_gen = itertools.chain([peek],self.program_gen)
        return peek

    def next_ch(self):
        """Call next(self.program_gen), increment self.line_num if necessary"""
        n=next(self.program_gen)
        if n == '\n':
            self.line_num += 1
        return n
    
    def next_line(self):
        """Set the self.line_buffer variable by reading until the next period."""
        self.line_buffer = ''
        self.line_buffer_num=self.line_num
        n=self.next_nonblank()
        while n!='.':
            self.line_buffer+=n
            n=self.next_ch()
        self.line_buffer+='.'
        return self.line_buffer

# debugging:
def debug() -> int:
    i = 1
    while True: # loop until file open fails
        try:
            f=open(str(i)+'.txt','r')
        except FileNotFoundError:
            return 0
        contents = f.read()
        parser = Parser(contents)
        output = parser.next_line()
        print(output)
        i+=1
    return 0


# main function
# reads input files numbered 1.txt and up, parses them and gives output
# to parser_output.txt
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
        outputs_lst.append(str(i)+".txt: ")
        if len(output) == 0:
            outputs_lst.append("Valid program\n")
        else:
            outputs_lst.append('\n'.join(output))
        i+=1
    return 0

#TODO uncomment this
#if __name__=="__main__": exit(main())
#delete this
if __name__=="__main__": exit(debug())
