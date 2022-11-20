#!/usr/bin/python3
# Gregory Smith     b00095534
# Joseph Press      b00095348
# Abdu Sallouh      b00087818
# TODO
# * the restorations of self.program_gen also need to be done with
# copy.deepcopy
# * the self.line_num variable should also be backed up
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
    
    class TerminalError(ParserError):
        """Exception raised by the parser that will terminate the parsing of
        the current file; usually when unexpected end of file is found."""
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
    def parse(self):
        """Parse a program.
        Output a list of descriptions of errors in the program"""
        try:
            self.skip_blanks()
        except Parser.TerminalError:
            self.error_list.append("Program was the empty string")
            return self.error_list
        try:
            self.program()
        except Parser.TerminalError as terr:
            self.error_list.append(terr.message)
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
            self.skip_blanks()
        except Parser.TerminalError:
            local_errors.append('valid programs must have a <query>')
            self.error_list += local_errors
            return
        try:
            self.query()
        except Parser.ParserError as err:
            local_errors.append(err.message)
            self.error_list += local_errors
        try:
            self.skip_blanks()
        except Parser.TerminalError:
            # This is good, the file is done
            return
        local_errors.append('After parsing the program, the following remained in the file:\n'+''.join(self.program_gen))
        self.error_list += local_errors
    
    def clause_list(self):
        """Subroutine for the <clause-list> symbol.
            Valid clause lists have a <clause>, optionally followed by a <clause-list>"""
        self.skip_blanks()
        self.clause()
        try:
            self.clause_list()
        except Parser.ParserError:
            pass

    def clause(self):
        """Subroutine for the <clause> symbol.
            Valid clauses follow this BNF rule:
            <clause> -> <predicate> . | <predicate> :- <predicate-list> ."""
        self.skip_blanks()
        self.predicate()
        self.skip_blanks()

        if self.peek_ch() == ':':
            #it should be a predicate list
            self.token()
            if self.peek_ch() != '-':
                raise Parser.ParserError('clause must have ":-" between predicate and predicate list', self.line_num)
            else:
                self.predicate_list()

        self.skip_blanks()

        if self.peek_ch() == '.':
            self.token()
        else:
            raise Parser.ParserError('"." must come at the end of a clause', self.line_num)

    def query(self):
        """Subroutine for the <query> symbol.
            <query> -> ?- <predicate-list> ."""
        # skipping blanks here is redundant because that has already been
        # taken care of by the program() subroutine
        n=self.peek_ch(skip_blanks=True)
        if n != '?':
            raise Parser.ParserError('<query> must start with "?-", not "' + n + '"', self.line_num)
        program_gen_backup = copy.deepcopy(self.program_gen)
        _ = self.next_nonblank()
        if self.next_ch() != '-':
            self.program_gen = program_gen_backup
            raise Parser.ParserError('<query> must start with "?-", not "?' + n + '"', self.line_num)
        # check <predicate-list>, but skip blanks first
        self.skip_blanks()
        self.predicate_list()
        # check for period terminating <query>
        n=self.peek_ch(skip_blanks=True)
        if n != '.':
            raise Parser.ParserError('<query must end with ".", not "' + n + '"', self.line_num)
        _ = self.next_nonblank() # get rid of the period
        # not skipping blanks after the period, because this is checked in the
        # program() subroutine

    def predicate_list(self):
        """Subroutine for the <predicate-list> symbol.
            <predicate-list> -> <predicate> | <predicate> , <predicate-list>"""
        self.skip_blanks()
        self.predicate()
        self.skip_blanks()
        if self.peek_ch() == ',':
            self.next_ch()
            # predicate list again
            self.predicate_list()

    def predicate(self):
        """Subroutine for <predicate>
            <predicate> -> <atom> | <atom> ( <term-list> )
            This rule can be simplified to:
            <predicate> -> <atom> | <structure>"""
        self.skip_blanks()
        program_gen_backup = copy.deepcopy(self.program_gen)
        try:
            self.atom()
        except Parser.ParserError as err1:
            self.program_gen = program_gen_backup
            try:
                self.structure()
            except Parser.ParserError as err2:
                self.program_gen = program_gen_backup
                raise Parser.ParserError("Could not parse as an atom or structure", self.line_num)

    def term_list(self):
        """Subroutine for <term-list>
            <term-list> -> <term> | <term> , <term-list>"""
        self.skip_blanks()
        self.term()
        self.skip_blanks()
        if self.peek_ch() == ',':
            self.next_ch()
            self.term_list()
        pass

    def term(self):
        """Subroutine for <term>
            <term> -> <atom> | <variable> | <structure> | <numeral>"""
        self.skip_blanks()
        p_gen_backup = copy.deepcopy(self.program_gen)
        try:
            self.atom()
        except Parser.ParserError:
            self.program_gen = p_gen_backup
            try:
                self.variable()
            except Parser.ParserError:
                self.program_gen = p_gen_backup
                try:
                    self.structure()
                except Parser.ParserError:
                    self.program_gen = p_gen_backup
                    try:
                        self.numeral()
                    except Parser.ParserError:
                        self.program_gen = p_gen_backup
                        raise Parser.ParserError("could not resolve to a term", self.line_num)

    def structure(self):
        """Subroutine for <structure>
            <structure> -> <atom> ( <term-list> )"""
        pgbackup = copy.deepcopy(self.program_gen)
        self.skip_blanks()
        self.atom()
        self.skip_blanks()
        if self.peek_ch() != '(':
            self.program_gen = copy.deepcopy(pgbackup)
            raise Parser.ParserError('structure must have parentheses', self.line_num)
        self.next_ch()
        self.skip_blanks()
        self.term_list()
        self.skip_blanks()
        if self.peek_ch() != ')':
            self.program_gen = copy.deepcopy(pgbackup)
            raise Parser.ParserError('must close parentheses on structure',self.line_num)
        self.next_ch()

    def atom(self):
        """Subroutine for <atom>
            <atom> -> <small-atom> | ' <string> '"""
        self.skip_blanks()
        pgb = copy.deepcopy(self.program_gen)
        if self.peek_ch() == "'":
            _ = self.next_ch()
            try:
                self.string()
            except StopIteration:
                raise Parser.TerminalError('Encountered EOF while parsing string', self.line_num)
            except Parser.ParserError as err:
                if self.peek_ch() == "'":
                    return
                else:
                    self.program_gen = copy.deepcopy(pgb)
                    raise err
        else:
            try:
                self.small_atom()
            except Parser.ParserError as err:
                self.program_gen = copy.deepcopy(pgb)
                raise err

    def small_atom(self):
        """Subroutine for <small-atom>
            <small-atom> -> <lowercase-char> | <lowercase-char> <character-list>"""
        self.skip_blanks()
        if self.peek_token() != 'lowercase-char':
            raise Parser.ParserError('small atoms must start with lowercase chars, not "' + self.peek_ch() + '"',self.line_num)
        else:
            self.token()
            self.character_list()
        pass

    def variable(self):
        """Subroutine for <variable>
            <variable> -> <uppercase-char> | <uppercase-char> <character-list>"""
        self.skip_blanks()
        if self.peek_token() != 'uppercase-char':
            raise Parser.ParserError('Variables must start with uppercase chars, not "' + self.peek_ch() + '"', self.line_num)
        else:
            self.token()
            self.character_list()

    def character_list(self):
        """Subroutine for <character-list>
            <character-list> -> <alphanumeric> | <alphanumeric> <character-list>"""
        program_gen_backup = copy.deepcopy(self.program_gen)
        try:
            self.alphanumeric()
        except Parser.ParserError:
            self.program_gen = program_gen_backup
            return
        self.character_list()

    def alphanumeric(self):
        """Subroutine for <alphanumeric>
            <alphanumeric> -> <lowercase-char> | <uppercase-char> | <digit>"""
        p_tok = self.peek_token()
        if p_tok != 'lowercase-char' and p_tok != 'uppercase-char' and p_tok != 'digit':
            raise Parser.ParserError('Invalid alphanumeric "'+self.peek_ch()+'"',self.line_num)

    def lowercase_char(self):
        """Subroutine for <lowercase-char>
            <lowercase-char> -> a | b | c | ... | x | y | z"""
        if self.peek_token() == 'lowercase-char':
            self.token()
        else:
            raise Parser.ParserError('"'+self.peek_ch() + '" is not a lowercase char', self.line_num)

    def uppercase_char(self):
        """Subroutine for <uppercase-char>
            <uppercase-char> -> A | B | C | ... | X | Y | Z | _"""
        if self.peek_token() == 'uppercase-char':
            self.token()
        else:
            raise Parser.ParserError('"'+self.peek_ch() + '" is not an uppercase char', self.line_num)
        pass

    def numeral(self):
        """Subroutine for <numeral>
            <numeral> -> <digit> | <digit> <numeral>"""
        self.digit()
        try:
            self.numeral()
        except Parser.ParserError:
            pass

    def digit(self):
        """Subroutine for <digit>
            <digit> -> 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9
            Do not skip blanks"""
        p_tok=self.peek_token()
        if p_tok != 'digit':
            raise Parser.ParserError('Expected "digit", found "'+p_tok+'" instead.', self.line_num)
        self.token()

    def string(self):
        """Subroutine for <string>
            <string> -> <character> | <character> <string>"""
        self.character()
        program_gen_backup = copy.deepcopy(self.program_gen)
        try:
            self.string()
        except Parser.ParserError:
            self.program_gen = program_gen_backup

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
        peeked=self.peek_token()
        if peeked != 'special':
            raise Parser.ParserError('"'+self.peek_ch()+'" belongs to token "'+peeked+'" not "special"',self.line_num)
        else:
            self.token()

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
        try:
            n = self.next_ch()
            while n.isspace():
                n = next_ch()
        except StopIteration:
            raise Parser.TerminalError("Reached end of file while skipping blank space", self.line_num)
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
