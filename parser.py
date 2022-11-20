#!/usr/bin/python3
# Gregory Smith     b00095534
# Joseph Press      b00095348
# Abdu Sallouh      b00087818
import itertools
import copy

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

    class ErrorEOF(Parser.ParserError):
        """Exception raised by the parser when EOF is encountered"""
        def __init__(self, d, l):
            super().__init__(d, l)

    def __init__(self, cont):
        self.contents = cont
        self.program_gen=iter(cont)
        self.line_num=0
        self.error_list=[]
        self.line_buffer=''
        self.line_buffer_num=0
        self.next_tok=''
        self.specials=['+','-','*','/',"\\",'^','~',':','.','?',' ','#','$','&']
        self.digits=[str(i) for i in range(10)]
        self.uppercase_chars=[chr(i) for i in range(65,91)]+['_']
        self.lowercase_chars=[chr(i) for i in range(97,123)]

    # backtrack by saving a copy of the self.program_gen in another variable
    # by forcing generation of a list
    def parse(self):
        """Parse a program.
        Output a list of descriptions of errors in the program"""
        try:
            self.program()
        except Parser.ErrorEOF as eof:
            self.error_list.append(eof.message)
        return self.error_list

    def program(self):
        """Subroutine for the <program> symbol.
            Valid programs have a <query>, optionally preceded by a <clause-list>."""
        # To preserve the state of self.program_gen and allow reversion back to
        # this state, save program_gen to a backup
        local_errors = []
        program_gen_backup = copy.deepcopy(self.program_gen)
        try:
            self.clause_list()
        except Parser.ParserError as err:
            local_errors.append(err.message)
            self.program_gen = program_gen_backup
        try:
            self.query()
        except Parser.ParserError as err:
            local_errors.append(err.message)
            self.error_list += local_errors
    
    def clause_list(self):
        """Subroutine for the <clause-list> symbol.
            Valid clause lists have a <clause>, optionally followed by a <clause-list>"""
        pass

    #TODO
    def clause(self):
        """Subroutine for the <clause> symbol.
            Valid clauses follow this BNF rule:
            <clause> -> <predicate> . | <predicate> :- <predicate-list> ."""
        pass

    #TODO
    def query(self):
        """Subroutine for the <query> symbol.
            <query> -> ?- <predicate-list> ."""
        n=self.peek_ch(skip_blanks=True)
        if n != '?':
            raise Parser.ParserError('<query> must start with "?-", not "' + n + '"', self.line_num)
        program_gen_backup = copy.deepcopy(self.program_gen)
        _ = self.next_nonblank()
        if self.next_ch() != '-':
            self.program_gen = program_gen_backup
            raise Parser.ParserError('<query> must start with "?-", not "?' + n + '"', self.line_num)
        # check <predicate-list>
        self.predicate_list()
        # check for period terminating <query>
        n=self.peek_ch(skip_blanks=True)
        if n != '.':
            raise Parser.ParserError('<query must end with ".", not "' + n + '"', self.line_num)


    #TODO
    def predicate_list(self):
        """Subroutine for the <predicate-list> symbol.
            <predicate-list> -> <predicate> | <predicate> , <predicate-list>"""
        pass

    #TODO
    def predicate(self):
        """Subroutine for <predicate>
            <predicate> -> <atom> | <atom> ( <term-list> )
            This rule can be simplified to:
            <predicate> -> <atom> | <structure>"""
        pass

    #TODO
    def term_list(self):
        """Subroutine for <term-list>
            <term-list> -> <term> | <term> , <term-list>"""
        pass

    #TODO
    def term(self):
        """Subroutine for <term>
            <term> -> <atom> | <variable> | <structure> | <numeral>"""
        pass

    #TODO
    def structure(self):
        """Subroutine for <structure>
            <structure> -> <atom> ( <term-list> )"""
        pass

    #TODO
    def atom(self):
        """Subroutine for <atom>
            <atom> -> <small-atom> | ' <string> '"""
        pass

    #TODO
    def small_atom(self):
        """Subroutine for <small-atom>
            <small-atom> -> <lowercase-char> | <lowercase-char> <character-list>"""
        pass

    #TODO
    def variable(self):
        """Subroutine for <variable>
            <variable> -> <uppercase-char> | <uppercase-char> <character-list>"""
        pass

    #TODO
    def character_list(self):
        """Subroutine for <character-list>
            <character-list> -> <alphanumeric> | <alphanumeric> <character-list>"""
        pass

    #TODO
    def alphanumeric(self):
        """Subroutine for <alphanumeric>
            <alphanumeric> -> <lowercase-char> | <uppercase-char> | <digit>"""
        pass

    #TODO
    def lowercase_char(self):
        """Subroutine for <lowercase-char>
            <lowercase-char> -> a | b | c | ... | x | y | z"""
        pass

    #TODO
    def uppercase_char(self):
        """Subroutine for <uppercase-char>
            <uppercase-char> -> A | B | C | ... | X | Y | Z | _"""
        pass

    #TODO
    def numeral(self):
        """Subroutine for <numeral>
            <numeral> -> <digit> | <digit> <numeral>"""
        pass

    def digit(self):
        """Subroutine for <digit>
            <digit> -> 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9
            Do not skip blanks"""
        p_tok=self.peek_token()
        if p_tok != 'digit':
            raise Parser.ParserError('Expected "digit", found "'+p_tok+'" instead.', self.line_num)
        else: self.token()
        pass

    def string(self):
        """Subroutine for <string>
            <string> -> <character> | <character> <string>"""
        self.character()
        program_gen_backup = copy.deepcopy(self.program_gen)
        try:
            self.string()
        except Parser.ParserError:
            self.program_gen = program_gen_backup
        except StopIteration:
            raise Parser.ErrorEOF('Encountered EOF while parsing string', self.line_num)

    def character(self):
        """Subroutine for the <character> symbol.
            Valid characters are <alphanumeric> or <special>."""
        n=self.peek_ch()
        program_gen_backup=copy.deepcopy(self.program_gen)
        try:
            alphanumeric()
        except Parser.ParserError:
            self.program_gen = program_gen_backup
            try:
                special()
            except Parser.ParserError:
                raise Parser.ParserError('"'+n+'" is not a <character> (<special> or <alphanumeric>)', self.line_num)

    def special(self):
        """Subroutine for the <special> symbol.
            Raise a ParserError if the token is not special."""
        n=self.token()
        if self.next_token != 'special':
            raise Parser.ParserError('"'+n+'" belongs to token "'+self.next_token+'" not "special"',self.line_num)

    def peek_token(self, skip_blanks=False):
        """Retrieve and return the next token without changing the state of
        self.program_gen or the self.next_tok variable"""
        temp_gen = copy.deepcopy(self.program_gen)
        n=next(temp_gen)
        if skip_blanks:
            while n.isspace():
                n=next(temp_gen)

        if n in self.specials:
            return 'special'
        elif n in self.digits:
            return 'digit'
        elif n in self.uppercase_chars:
            return 'uppercase-char'
        elif n in self.lowercase_chars:
            return 'lowercase-char'
        else: # unrecognized token
            raise Parser.ParserError('Unrecognized token: "' + n + '"', self.line_num)

    def token(self, skip_blanks=False):
        """Store the name of the next token in the self.next_tok variable
            Return the character n that was tokenized."""
        if skip_blanks:
            n=self.next_nonblank()
        else:
            n=self.next_ch()

        if n in self.specials:
            self.next_token = 'special'
        elif n in self.digits:
            self.next_token = 'digit'
        elif n in self.uppercase_chars:
            self.next_token = 'uppercase-char'
        elif n in self.lowercase_chars:
            self.next_token = 'lowercase-char'
        else: # unrecognized token
            raise Parser.ParserError('Unrecognized token: "' + n + '"', self.line_num)
        return n

    def add_error(self, message):
        """Add the error message to the list of errors that will be returned by
        this parser."""
        self.error_list.append(message)

    def next_nonblank(self):
        "Return the next non blank character from self.program_gen"
        n = self.next_ch()
        while n.isspace():n = self.next_ch()
        return n

    def skip_blanks(self):
        """Skip blank space, don't return anything"""
        n = self.peek_ch()
        while n.isspace():
            n = next_ch()
        self.program_gen = itertools.chain([n],self.program_gen)

    def peek_ch(self, skip_blanks=False):
        """Peek at the next character from the program generator.
            Return the peeked value"""
        peeked = []
        peek = next(self.program_gen)
        peeked.append(peek)
        if skip_blanks:
            while peek.isspace():
                peek = next(self.program_gen)
                peeked.append(peek)
        self.program_gen = itertools.chain(peeked,self.program_gen)
        return peek

    def next_ch(self):
        "Call next(self.program_gen), increment self.line_num if necessary"
        try:
            n=next(self.program_gen)
        except StopIteration:
            return 'EOF'
        if n == '\n':
            self.line_num += 1
        return n
    
    def next_line(self):
        "Set the self.line_buffer variable by reading until the next period."
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
        output = parser.special()
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
