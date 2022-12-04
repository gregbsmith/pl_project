#!/usr/bin/python3
# Gregory Smith     b00095534
# Joseph Press      b00095348
# Abdu Sallouh      b00087818
# TODO
# * catch multiple errors per invalid program
# * give more informative error messages (it could help to keep a dictionary of lines with keys as numbers and values as contents)
import itertools

class Parser():
    """Parser class that takes a program and tells whether it is valid according
    to the simplified prolog grammar."""

    class ParserError(Exception):
        """Exception raised by the parser
        Attributes:
            message -- explanation of the exception including
            the line number where this exception happened
            line -- line number where the error was found"""
        def __init__(self, description, ln):
            self.message="Line " + str(ln) + ": " + description
            self.line = ln
        def __str__(self):
            return self.message

    def __init__(self, cont):
        self.contents = cont
        self.program_gen=iter(cont)
        self.line_num=1
        self.error_list=[]
        self.line_buffer=''
        self.line_buffer_num=0
        self.next_token=''
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
        except StopIteration:
            self.error_list.append("Error: program was the empty string")
            return self.error_list
        try:
            self.program()
        except StopIteration as si:
            self.error_list.append(str(si))
        return self.error_list

    def program(self):
        """Subroutine for the <program> symbol.
            Valid programs have a <query>, optionally preceded by a <clause-list>."""
        # To preserve the state of self.program_gen and allow reversion back to
        # this state, save program_gen to a backup
        local_errors = []
        if self.peek_ch(skip_blanks=True) != '?':
            # looking for a clause list, then a query
            try:
                self.clause_list()
            except Parser.ParserError as perr:
                local_errors.append(str(perr))
                self.error_list += local_errors
                return
            self.skip_blanks()
        try:
            self.query()
        except Parser.ParserError as perr:
            local_errors.append(str(perr))
            self.error_list += local_errors
            return
        
        try:
            self.skip_blanks()
        except StopIteration:
            # This is good, the file is done
            return
        local_errors.append('After parsing the program, the following remained in the file:\n'+''.join(self.program_gen))
        self.error_list += local_errors
    
    def clause_list(self):
        """Subroutine for the <clause-list> symbol.
            Valid clause lists have a <clause>, optionally followed by a <clause-list>
            Do not catch StopIteration in call to self.clause()"""
        # no need to skip blanks; clauses must start with predicates, and predicate()
        # skips leading blanks
        self.clause()
        # make a backup of program_gen and line_num
        pgb_str = ''.join(self.program_gen)
        lnumbackup=self.line_num
        self.program_gen = iter(pgb_str)
        try:
            self.skip_blanks()
        except StopIteration:
            raise StopIteration("Line "+str(self.line_num)+': reached EOF while parsing clause list')

        try:
            self.clause_list()
        except Parser.ParserError:
            self.program_gen = iter(pgb_str)
            self.line_num = lnumbackup
            pass

    def clause(self):
        """Subroutine for the <clause> symbol.
            Valid clauses follow this BNF rule:
            <clause> -> <predicate> . | <predicate> :- <predicate-list> ."""
        # no need to skip leading blanks; predicate() does this
        pgb_str = ''.join(self.program_gen)
        self.program_gen = iter(pgb_str)
        lnumbackup = self.line_num
        try:
            self.predicate()
        except Parser.ParserError as perr:
            self.program_gen = iter(pgb_str)
            self.line_num = lnumbackup
            raise perr
        try:
            pkch = self.peek_ch(skip_blanks=True)
        except StopIteration:
            raise StopIteration("Line "+str(self.line_num)+': reached EOF after first <predicate>')
        if pkch == ':':
            #it should be a predicate list
            self.token(skip_blanks=True)
            try:
                pkch = self.peek_ch(skip_blanks=False)
            except StopIteration:
                raise StopIteration("Line "+str(self.line_num)+': reached EOF after ":" after first <predicate>')
            if pkch != '-':
                raise Parser.ParserError('clause must have ":-" between predicate and predicate list', self.line_num)
            
            self.token() # get rid of -
            try:
                self.predicate_list()
            except Parser.ParserError as perr:
                self.program_gen = iter(pgb_str)
                self.line_num = lnumbackup
                raise perr
            except StopIteration:
                raise StopIteration("Line "+str(self.line_num)+': reached EOF while parsing <predicate-list>')

            try:
                pkch = self.peek_ch(skip_blanks=True)
            except StopIteration:
                raise StopIteration("Line "+str(self.line_num)+': reached EOF before "." found to terminate <clause>')
        if pkch == '.':
            self.token(skip_blanks=True)
        else:
            raise Parser.ParserError('"." must come at the end of a clause; found "'+pkch+'" after <predicate> instead', self.line_num)

    def query(self):
        """Subroutine for the <query> symbol.
            <query> -> ?- <predicate-list> ."""
        # skipping blanks here is redundant because that has already been
        # taken care of by the program() subroutine
        pgb_str = ''.join(self.program_gen)
        self.program_gen = iter(pgb_str)
        lnumbackup = self.line_num
        try:
            n=self.peek_ch(skip_blanks=True)
        except StopIteration:
            raise StopIteration("Line " + str(self.line_num) + ": reached EOF before <query>")
        if n != '?':
            self.program_gen = iter(pgb_str)
            self.line_num = lnumbackup
            raise Parser.ParserError('<query> must start with "?-", not "' + n + '"', self.line_num)
        self.token(skip_blanks=True)
        try:
            n=self.next_ch()
        except StopIteration:
            raise StopIteration("Line " + str(self.line_num) + ": reached EOF after '?' in <query>")
        if n != '-':
            self.program_gen = iter(pgb_str)
            self.line_num = lnumbackup
            raise Parser.ParserError('<query> must start with "?-", not "?' + n + '"', self.line_num)
        # check <predicate-list>
        # no need to skip leading blanks; <predicate> does this
        try:
            self.predicate_list()
        except StopIteration:
            #self.program_gen = iter(pgb_str)
            #self.line_num = lnumbackup
            raise StopIteration("Line "+str(self.line_num)+": reached EOF while parsing predicate-list in query")
        # check for period terminating <query>
        try:
            n=self.peek_ch(skip_blanks=True)
        except StopIteration:
            raise StopIteration("Line " + str(self.line_num) + ": no '.' found after <predicate-list>")
        if n != '.':
            self.program_gen = iter(pgb_str)
            self.line_num = lnumbackup
            raise Parser.ParserError('<query> must end with ".", not "' + n + '"', self.line_num)
        self.token() # get rid of the period
        # not skipping blanks after the period, because this is checked in the
        # program() subroutine

    def predicate_list(self):
        """Subroutine for the <predicate-list> symbol.
            <predicate-list> -> <predicate> | <predicate> , <predicate-list>
            No need to skip leading blanks; predicate function does this"""
        pgb_str = ''.join(self.program_gen)
        self.program_gen = iter(pgb_str)
        lnumbackup = self.line_num
        self.predicate()
        if self.peek_ch(skip_blanks=True) == ',':
            self.token(skip_blanks=True)
            # predicate list again
            try:
                self.predicate_list()
            except Parser.ParserError as perr:
                self.program_gen = iter(pgb_str)
                self.line_num = lnumbackup
                raise perr

    def predicate(self):
        """Subroutine for <predicate>
            <predicate> -> <atom> | <atom> ( <term-list> )
            This rule can be simplified to:
            <predicate> -> <structure> | <atom>
            must skip leading blanks
            Do not catch StopIteration"""
        self.skip_blanks()
        pgb_str = ''.join(self.program_gen)
        self.program_gen = iter(pgb_str)
        lnumbackup = self.line_num
        try:
            self.structure()
        except Parser.ParserError:
            self.program_gen = iter(pgb_str)
            self.line_num = lnumbackup
            try:
                self.atom()
            except Parser.ParserError:
                self.program_gen = iter(pgb_str)
                self.line_num = lnumbackup
                raise Parser.ParserError("Could not parse as a predicate (atom or structure)", self.line_num)
            except StopIteration:
                raise StopIteration("Line " + str(self.line_num) + ": reached EOF while parsing <atom>")
        except StopIteration:
            raise StopIteration("Line " + str(self.line_num) + ": reached EOF while parsing <structure>")

    def term_list(self):
        """Subroutine for <term-list>
            <term-list> -> <term> | <term> , <term-list>
            Do not catch StopIteration
            leading blanks will be skipped in self.term() function"""
        # only call this function after a right p (
        pgb_str = ''.join(self.program_gen)
        self.program_gen = iter(pgb_str)
        lnumbackup = self.line_num
        self.term()
        pkch = self.peek_ch(skip_blanks=True)
        if pkch == ')':
            return
        while pkch in self.specials:
            self.error_list.append("Line " + str(self.line_num) + ': <special> characters like "' + pkch + '" are not allowed in non-string terms')         
            self.token(skip_blanks=True)
            pkch = self.peek_ch(skip_blanks=True)
        
        if pkch != ',':
            self.error_list.append("Line " + str(self.line_num) + ": <terms> in a <term-list> must be comma-separated")
        else:
            self.token(skip_blanks=True)
        # do not pass on Parser.ParserError
        # If no ')' was found, there should be another term
        try:
            self.term_list()
        except Parser.ParserError as perr:
            self.program_gen = iter(pgb_str)
            self.line_num = lnumbackup
            raise perr

    def term(self):
        """Subroutine for <term>
            <term> -> <atom> | <variable> | <structure> | <numeral>
            Must skip leading blanks"""
        pgb_withblanks_str = ''.join(self.program_gen)
        self.program_gen = iter(pgb_withblanks_str)
        ln_blanks_backup = self.line_num
        self.skip_blanks()
        pgb_str = ''.join(self.program_gen)
        self.program_gen = iter(pgb_str)
        lnbackup = self.line_num
        try:
            self.structure()
        except Parser.ParserError:
            self.program_gen = iter(pgb_str)
            self.line_num = lnbackup
            try:
                self.numeral()
            except Parser.ParserError:
                self.program_gen = iter(pgb_str)
                self.line_num = lnbackup
                try:
                    self.variable()
                except Parser.ParserError:
                    self.program_gen = iter(pgb_str)
                    self.line_num = lnbackup
                    try:
                        self.atom()
                    except Parser.ParserError:
                        self.program_gen = iter(pgb_withblanks_str)
                        self.line_num = ln_blanks_backup
                        raise Parser.ParserError("could not resolve to a term", self.line_num)

    def structure(self):
        """Subroutine for <structure>
            <structure> -> <atom> ( <term-list> )
            Do not skip leading blanks
            Do not catch StopIteration"""
        # This subroutine involves calling multiple different subroutines.
        # It should succeed fully and "eat" the proper characters, or fail entirely.
        # Therefore, it is necessary to back up and restore self.program_gen
        pgb_str = ''.join(self.program_gen)
        self.program_gen = iter(pgb_str)
        lnbackup = self.line_num
        
        try:
            self.atom()
        except Parser.ParserError as perr:
            self.program_gen = iter(pgb_str)
            self.line_num = lnbackup
            raise perr
        
        try:
            self.skip_blanks()
        except StopIteration:
            raise StopIteration("Line " + str(self.line_num) + ": reached EOF in <structure> after <atom> before ( <term-list> )")
        if self.peek_ch() != '(':
            self.program_gen = iter(pgb_str)
            self.line_num = lnbackup
            raise Parser.ParserError('<structure> must have <term-list> enclosed in parentheses', self.line_num)
        
        self.token()
        
        try:
            # do not need to skip blanks; self.term() function skips leading blanks
            self.term_list()
        except Parser.ParserError as perr:
            self.program_gen = iter(pgb_str)
            self.line_num = lnbackup
            raise perr
        except StopIteration as si:
            raise StopIteration("Line "+str(self.line_num)+": reached EOF while reading <term-list>")
        
        if self.peek_ch(skip_blanks=True) != ')':
            self.program_gen = iter(pgb_str)
            self.line_num = lnbackup
            raise Parser.ParserError('must close parentheses around <term-list> in <structure>',self.line_num)
        self.token(skip_blanks=True)

    def atom(self):
        """Subroutine for <atom>
            <atom> -> <small-atom> | ' <string> '
            Do not skip leading blanks
            Do not catch StopIteration (Should not reach EOF while parsing atom)"""
        # may need to back up self.program_gen
        if self.peek_ch() == "'":
            # we're trying to match a string
            self.token()
            # may need try/except here
            try:
                self.string()
            except StopIteration:
                raise StopIteration("Line "+str(self.line_num)+": reached eof while parsing string")
            pkch = self.peek_ch()
            if pkch == '\n':
                raise Parser.ParserError("reached newline while parsing <string>", self.line_num)
            elif pkch != "'":
                raise Parser.ParserError('<string> must be enclosed in single quotes; "'+
                pkch+'" not allowed in <string>', self.line_num)
            self.token()
        else:
            # we're looking to match a small-atom
            self.small_atom()

    def small_atom(self):
        """Subroutine for <small-atom>
            <small-atom> -> <lowercase-char> | <lowercase-char> <character-list>
            Do not catch StopIteration
            Do not skip leading blanks"""
        try:
            self.lowercase_char()
        except Parser.ParserError:
            raise Parser.ParserError('<small_atom> must start with <lowercase-char>, not "'+self.peek_ch()+'"',self.line_num)
        try:
            self.character_list()
        except Parser.ParserError:
            pass

    def variable(self):
        """Subroutine for <variable>
            <variable> -> <uppercase-char> | <uppercase-char> <character-list>
            Do not catch StopIteration
            Do not skip leading blanks"""
        try:
            self.uppercase_char()
        except Parser.ParserError:
            raise Parser.ParserError('<variable> must start with <uppercase-char>, not "'+self.peek_ch()+'"',self.line_num)
        try:
            self.character_list()
        except Parser.ParserError:
            pass

    def character_list(self):
        """Subroutine for <character-list>
            <character-list> -> <alphanumeric> | <alphanumeric> <character-list>
            Do not catch StopIteration
            Do not consume character on which recursive calls fail
            Do not skip leading whitespace"""
        self.alphanumeric()
        try:
            self.character_list()
        except Parser.ParserError:
            pass

    def alphanumeric(self):
        """Subroutine for <alphanumeric>
            <alphanumeric> -> <lowercase-char> | <uppercase-char> | <digit>
            Do not skip blanks
            Do not catch StopIteration"""
        p_tok = self.peek_token()
        if p_tok != 'lowercase-char' and p_tok != 'uppercase-char' and p_tok != 'digit':
            raise Parser.ParserError('Invalid alphanumeric "'+self.peek_ch()+'"',self.line_num)
        self.token()

    def lowercase_char(self):
        """Subroutine for <lowercase-char>
            <lowercase-char> -> a | b | c | ... | x | y | z
            do not catch StopIteration
            do not skip blanks"""
        if self.peek_token() == 'lowercase-char':
            self.token()
        else:
            raise Parser.ParserError('"'+self.peek_ch() + '" is not a lowercase char', self.line_num)

    def uppercase_char(self):
        """Subroutine for <uppercase-char>
            <uppercase-char> -> A | B | C | ... | X | Y | Z | _
            do not catch StopIteration
            do not skip blanks"""
        if self.peek_token() == 'uppercase-char':
            self.token()
        else:
            raise Parser.ParserError('"'+self.peek_ch() + '" is not an uppercase char', self.line_num)

    def numeral(self):
        """Subroutine for <numeral>
            <numeral> -> <digit> | <digit> <numeral>
            catches StopIteration on recursive calls (and passes on it)"""
        self.digit()
        try:
            self.numeral()
        except Parser.ParserError:
            pass
        except StopIteration:
            pass # this is the first time we've done this for tail recursive calls
            # this may be a good pattern to reuse

    def digit(self):
        """Subroutine for <digit>
            <digit> -> 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9
            Do not skip blanks
            Do not catch StopIteration"""
        p_tok=self.peek_token()
        if p_tok != 'digit':
            raise Parser.ParserError('Expected <digit>, found "'+self.peek_ch()+'" instead.', self.line_num)
        self.token()

    def string(self):
        """Subroutine for <string>
            <string> -> <character> | <character> <string>
            Do not skip blanks
            Do not catch StopIteration (single quote should appear after a string)
            According to the rule for <string>, the empty string is not accepted
            Catch ParserError on recursive calls
            Do not consume the character on which the recursive call fails"""
        self.character()
        try:
            self.string()
        except Parser.ParserError:
            pass

    def character(self):
        """Subroutine for the <character> symbol.
            Valid characters are <alphanumeric> or <special>.
            Do not skip blanks
            Do not catch StopIteration"""
        try:
            self.alphanumeric()
        except Parser.ParserError:
            try:
                self.special()
            except Parser.ParserError:
                raise Parser.ParserError('"'+self.peek_ch()+'" is not a <character> (<special> or <alphanumeric>)', self.line_num)

    def special(self):
        """Subroutine for the <special> symbol.
            Raise a ParserError and do not consume character if the token is not special.
            "consume" the character if it is special"""
        peeked=self.peek_token()
        if peeked != 'special':
            raise Parser.ParserError('"'+self.peek_ch()+'" belongs to token "'+peeked+'" not "special"',self.line_num)
        else:
            self.token()

    def peek_token(self, skip_blanks=False):
        """Retrieve and return the next token without changing the state of
        self.program_gen or the self.next_tok variable
            Do not catch StopIteration"""
        pgb_str = ''.join(self.program_gen)
        temp_gen = iter(pgb_str)
        self.program_gen = iter(pgb_str)
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
        elif n == '\n': # don't want to raise an error for newlines
            return 'newline'
        elif n == '(':
            return '('
        elif n == ')':
            return ')'
        elif n == ',':
            return ','
        elif n == "'":
            return "'"
        else: # unrecognized token
            return 'unrecognized'
    
    def token(self, skip_blanks=False):
        """Store the name of the next token in the self.next_tok variable
            Return the character n that was tokenized.
            Eat the next character, no matter what.
            Do not catch StopIteration
            If an unrecognized character is found, simply add an error message and return the next recognized token"""
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
        elif n == '\n': # newlines aren't in the grammar, but we do not want to add errors for them
            self.next_token = 'newline'
        elif n == '(':
            self.next_token = '('
        elif n == ')':
            self.next_token = ')'
        elif n == ',':
            self.next_token = ','
        elif n == "'":
            self.next_token = "'"
        else: # unrecognized token
            self.add_error('Line '+ str(self.line_num)+': Unrecognized token: "' + n + '"')
            self.token(skip_blanks)
        return n

    def add_error(self, message):
        """Add the error message to the list of errors that will be returned by
        this parser."""
        self.error_list.append(message)

    def next_nonblank(self):
        """Return the next non blank character from self.program_gen
            Do not catch StopIteration"""
        n = self.next_ch()
        while n.isspace():n = self.next_ch()
        return n

    def skip_blanks(self):
        """Skip blank space, don't return anything
            Do not catch StopIteration"""
        n = self.next_ch()
        while n.isspace():
            n = self.next_ch()
        self.program_gen = itertools.chain([n],self.program_gen)

    def peek_ch(self, skip_blanks=False):
        """Peek at the next character from the program generator.
            Return the peeked value
            Do not catch StopIteration"""
        peeked = []
        # This function uses next(self.program_gen) rather than self.next_ch()
        # because we do not need to increment the line number here
        peek = next(self.program_gen)
        peeked.append(peek)
        if skip_blanks:
            while peek.isspace():
                peek = next(self.program_gen)
                peeked.append(peek)
        self.program_gen = itertools.chain(peeked,self.program_gen)
        return peek

    def next_ch(self):
        """Call next(self.program_gen), increment self.line_num if necessary
            Do not catch StopIteration"""
        n=next(self.program_gen)
        if n == '\n':
            self.line_num += 1
        return n
    
    def next_line(self):
        """Set the self.line_buffer variable by reading until the next period.
            Do not catch StopIteration"""
        self.line_buffer = ''
        self.line_buffer_num=self.line_num
        n=self.next_nonblank()
        while n!='.':
            self.line_buffer+=n
            n=self.next_ch()
        self.line_buffer+='.'
        return self.line_buffer

    def whats_left(self):
        """debug function to see what's remaining in the self.program_gen
        iterator"""
        remaining = ''.join(self.program_gen)
        self.program_gen = iter(remaining)
        return remaining

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
        if len(output) == 0:
            outputs_lst.append(str(i)+".txt:\n"+"Valid program\n")
        else:
            outputs_lst.append(str(i)+".txt:\n"+'\n'.join(output)+'\n')
        i+=1
    return 0

if __name__=="__main__": exit(main())