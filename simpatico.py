#!/usr/bin/env python
# simpatico.py
""" This is a complete rewrite of the old simpatico.
Hopefully it's good. """

import sys

import headers


DEBUG = True

INDENT_SIZE = 4
LINE_CONTINUATION_SIZE = 8
ALLOW_ZERO = True
(NO_NEWLINE, MAY_NEWLINE, MUST_NEWLINE) = range(3)
IS_TYPEDEF = True
MISSING_TYPE = False

def d(elements):
    if DEBUG:
        print "D: " + " ".join([str(x) for x in elements])

TYPE_SPECIFIERS = ['void', 'char', 'short', 'int', 'long', 'float', 'double',
                 'signed', 'unsigned', '_Bool', '_Imaginary', '_Complex']
DEFINED_TYPES = ['__UINTMAX_TYPE__', '__SIZE_TYPE__', '__CHAR16_Type__',
        '__WCHAR_TYPE__', '__WINT_TYPE__', '__CHAR32_TYPE__',
        '__INTMAX_TYPE__', '__PTRDIFF_TYPE__'] #default defines with gcc
STRUCT_UNION = ["struct", "union"]
STORAGE_CLASS = ["register", "static", "extern", "auto", "typedef"]
TYPE_QUALIFIERS = ["const", "restrict", "volatile"]

class Terminals(object):
    KW_AUTO = "auto"
    KW_BREAK = "break"
    KW_CASE = "case"
    KW_CHAR = "char"
    KW_CONST = "const"
    KW_CONTINUE = "continue"
    KW_DEFAULT = "default"
    KW_DO = "do"
    KW_DOUBLE = "double"
    KW_ELSE = "else"
    KW_ENUM = "enum"
    KW_EXTERN = "extern"
    KW_FLOAT = "float"
    KW_FOR = "for"
    KW_GOTO = "goto"
    KW_IF = "if"
    KW_INLINE = "inline"
    KW_INT = "int"
    KW_LONG = "long"
    KW_REGISTER = "register"
    KW_RESTRICT = "restrict"
    KW_RETURN = "return"
    KW_SHORT = "short"
    KW_SIGNED = "signed"
    KW_SIZEOF = "sizeof"
    KW_STATIC = "static"
    KW_STRUCT = "struct"
    KW_SWITCH = "switch"
    KW_TYPEDEF = "typedef"
    KW_UNION = "union"
    KW_UNSIGNED = "unsigned"
    KW_VOID = "void"
    KW_VOLATILE = "volatile"
    KW_WHILE = "while"
    KW_BOOL = "_Bool"
    KW_COMPLEX = "_Complex"
    KW_IMAGINARY = "_Imaginary"

BINARY_OPERATORS = ["+", "/", "%", ">>", "<<", "|", "^", "->", ".", "?", ":"]
UNARY_OPERATORS = ["--", "++", "!"]
LOGICAL_OPERATORS = ["&&", "||", "<", ">", "<=", ">=", "==", "!="]
ASSIGNMENTS = ["=", "%=", "+=", "-=", "*=", "/=", "|=", "&=", "<<=", ">>="]
ALL_OPS = BINARY_OPERATORS + UNARY_OPERATORS + ASSIGNMENTS + LOGICAL_OPERATORS
#by the time we use this one, there's no natural \t chars left
COMMENT = '\t'

class Type(object):
    """ Yes, this could be an Enum, but I'm being kind to older versions of
    Python """
    ANY = -1
    (   ERROR_TYPE, DEFINE, INCLUDE, COMMENT, NEWLINE, COMMA, LBRACE, RBRACE,
        LPAREN, RPAREN, MINUS, BINARY_OP, LOGICAL_OP, STAR,
        AMPERSAND, TYPE, CREMENT, IGNORE, KW_EXTERN, BREAK, FOR, SWITCH, CASE,
        STRUCT, CONTINUE, TYPEDEF, RETURN, UNKNOWN, CONSTANT, WHILE, DO,
        SEMICOLON, COLON, TERNARY, ASSIGNMENT, IF, ELSE, LSQUARE, RSQUARE,
        LINE_CONT, DEFAULT, NOT, SIZEOF, PRECOMPILER, ATTRIBUTE, HASH
    ) = range(46)

class Word(object):
    """ Keeps track of contextual details about the word """
    def __init__(self):
        self.space = -1
        self.line_number = -1
        self.line = []
        self.start = -1
        self._type = Type.ERROR_TYPE
        self.whitespace_checked = 0
        self.inner_tokens = []
        self.inner_position = 0
        
    def get_type(self):
        if self.inner_tokens:
            return self.inner_tokens[self.inner_position].get_type()
        else:
            return self._type

    def get_string(self):
        return "".join(self.line)

    def get_position(self):
        return self.start

    def get_spacing_left(self):
        return self.space

    def append(self, char, space_left, line_number, char_location):
        if self.line_number == -1:
            self.line_number = line_number
            self.space = space_left
            self.start = char_location
        self.line.append(char)

    def empty(self):
        return len(self.line) == 0

    def finalise(self):
        """ here's where we work out what type of thing this word is """
        self.line = "".join(self.line)
        line = self.line
        #prepare thyself for many, many elifs
        if line.lower() == "define":
            self._type = Type.DEFINE
        elif line in ["ifdef", "ifndef", "endif", "undef"]:
            self._type = Type.PRECOMPILER
        elif line == "include":
            self._type = Type.INCLUDE
        elif line == "#":
            self._type = Type.HASH
        elif line == Terminals.KW_IF:
            self._type = Type.IF
        elif line == Terminals.KW_ELSE:
            self._type = Type.ELSE
        elif line == "\t":
            self._type = Type.COMMENT
        elif line == ";":
            self._type = Type.SEMICOLON
        elif line == "!":
            self._type = Type.NOT
        elif line in ASSIGNMENTS:
            self._type = Type.ASSIGNMENT
        elif line == "\n":
            self._type = Type.NEWLINE
        elif line == ",":
            self._type = Type.COMMA
        elif line == "{":
            self._type = Type.LBRACE
        elif line == "?":
            self._type = Type.TERNARY
        elif line == ":":
            self._type = Type.COLON
        elif line == "}":
            self._type = Type.RBRACE
        elif line == "(":
            self._type = Type.LPAREN
        elif line == ")":
            self._type = Type.RPAREN
        elif line == "-":
            self._type = Type.MINUS
        elif line in BINARY_OPERATORS:
            self._type = Type.BINARY_OP
        elif line in LOGICAL_OPERATORS:
            self._type = Type.LOGICAL_OP
        elif line == "*":
            self._type = Type.STAR
        elif line == "&":
            self._type = Type.AMPERSAND
        elif line in TYPE_SPECIFIERS + DEFINED_TYPES:
            self._type = Type.TYPE
        elif line in ["--", "++"]:
            self._type = Type.CREMENT
        elif line == Terminals.KW_EXTERN:
            self._type = Type.KW_EXTERN
        elif line == Terminals.KW_BREAK:
            self._type = Type.BREAK
        elif line == Terminals.KW_FOR:
            self._type = Type.FOR
        elif line == Terminals.KW_DO:
            self._type = Type.DO
        elif line == Terminals.KW_WHILE:
            self._type = Type.WHILE
        elif line == Terminals.KW_SWITCH:
            self._type = Type.SWITCH
        elif line == Terminals.KW_CASE:
            self._type = Type.CASE
        elif line == Terminals.KW_DEFAULT:
            self._type = Type.DEFAULT
        elif line in STRUCT_UNION:
            self._type = Type.STRUCT
        elif line == Terminals.KW_CONTINUE:
            self._type = Type.CONTINUE
        elif line == "typedef":
            self._type = Type.TYPEDEF
        elif line in TYPE_QUALIFIERS + STORAGE_CLASS:
            self._type = Type.IGNORE        
        elif line == Terminals.KW_RETURN:
            self._type = Type.RETURN
        elif line[0] == '"' or line[0] == "'" or line.isdigit():
            self._type = Type.CONSTANT
        elif line == "[":
            self._type = Type.LSQUARE
        elif line == "]":
            self._type = Type.RSQUARE
        elif line == "\\":
            self._type = Type.LINE_CONT
        elif line == Terminals.KW_SIZEOF:
            self._type = Type.SIZEOF
        elif line == "__attribute__":
            self._type = Type.ATTRIBUTE
        else:
            #d(["finalise() could not match type for", self])
            self._type = Type.UNKNOWN #variables and externally defined types

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        rep = "%d:%d  i:%d '\033[1m%s\033[0m'" % (self.line_number,
                self.start, self.space, "".join(self.line))
        if len(self.inner_tokens) != 0:
            rep += "-> defined as \033[1m" + \
                    "".join([x.line for x in self.inner_tokens]) + "\033[0m" \
                    + " current:" + str(self.inner_tokens[self.inner_position])
        return rep

class Tokeniser(object):
    """ The thing that turns a gigantic file of hopefully not terrible code
    into tokens that we can then deal with """
    DUPLICATE_OPS = ['|', '&', '<', '>', '+', '-', '=']
    def __init__(self, filename):
        self.tokens = []
        self.line_number = 1
        self.line_start = 0
        self.in_operator = False
        self.in_string = False
        self.in_char = False
        self.multi_char_op = False
        self.multiline_comment = 0
        self.in_singleline_comment = False
        self.deal_breakers = [' ', '.', '-', '+', '/', '*', '>', '<', '&',
                '|', '!', '~', '%', '^', '(', ')', '{', '}', ';', ',', ':',
                '?', '[', ']', '#']
        self.current_word = Word()
        self.space_left = 0
        self.current_word_start = 1
        #well that was fun, now we should do some real work
        f = open(filename, "r")
        allllll_of_it = str.replace(f.read().expandtabs(8), '\r', '')
        f.close()
        self.tokenise(allllll_of_it)

    def end_word(self):
        if self.current_word.empty():
            return
        self.current_word.finalise()
        self.tokens.append(self.current_word)
        self.current_word = Word()
        self.in_operator = False
        self.in_string = False
        self.in_char = False
        self.multi_char_op = False

    def add_to_word(self, char, n):
        self.current_word.append(char, self.space_left, self.line_number, n)
        self.space_left = 0

    def tokenise(self, megastring):
        """ Why yes, this is a big function. Be glad it's not the usual parser
        switch statement that's 1000 lines long. """
        for n, c in enumerate(megastring):
            #step 0: if we were waiting for the second char in a "==" or
            # similar, grab it and move on already
            if self.multi_char_op:
                self.add_to_word(c, n - self.line_start)
                #catch dem silly >>= and <<= ops
                if self.current_word.get_string() + "=" in ASSIGNMENTS:
                    continue
                self.end_word()
                continue
            #step 1: deal with the case of being in a //comment
            if self.in_singleline_comment:
                if c == '\n':
                    self.in_singleline_comment = False
                    self.add_to_word(COMMENT, n - self.line_start)
                    self.end_word()
                    #then add the newline
                    self.add_to_word(c, n - self.line_start)
                    self.end_word()
                    self.line_number += 1
                    self.line_start = n + 1
                else:
                    continue

            #step 2: continue on while inside a multiline comment
            elif self.multiline_comment:
                #if we've reached the end of the comment
                if self.multiline_comment == n:
                    self.multiline_comment = 0
                    self.add_to_word(COMMENT, n - self.line_start)
                    self.end_word()
                #but update line numbers if it's a newline
                if c == '\n':
                    self.line_number += 1
                    self.line_start = n + 1
            #step 3: deal with newlines, ends the current word
            elif c == '\n':
                #out with the old
                self.end_word()
                #in with the new..
                self.line_number += 1
                self.line_start = n + 1
                #...line AHYUK, AHYUK
                self.add_to_word(c, n - self.line_start)
                self.end_word()

            #don't want to get caught interpreting chars in strings as real
            elif self.in_string:
                self.add_to_word(c, n - self.line_start)
                #string ending
                if c == '"':
                    #but not if it's escaped
                    if megastring[n-1] == '\\':
                        #make sure the slash wasn't itself escaped
                        if megastring[n-2] == '\\':
                            self.end_word()
                    else:
                        #eeennnd it, and escape this if tree
                        self.end_word()
            #that was fuuun, but it repeats with chars
            elif self.in_char:
                self.add_to_word(c, n - self.line_start)
                #first: is it a '; second: are sneaky people involved
                if c == "'" and megastring[n-1] != '\\':
                    self.end_word()
            #catch dem spaces
            elif c == ' ':
                self.end_word()
                self.space_left += 1

            #catch the start of a string
            elif c == '"':
                self.in_string = not self.in_string
                self.add_to_word(c, n - self.line_start)
            #or, for that matter, the start of a char
            elif c == "'":
                self.in_char = not self.in_char
                self.add_to_word(c, n - self.line_start)
            #now we just have to catch the possible word seperators
            elif c in self.deal_breakers:
                if c == "/" and megastring[n+1] == "*":
                    self.multiline_comment = megastring.find("*/", n) + 1
                elif c == "/" and megastring[n+1] == "/":
                    self.in_singleline_comment = True
                elif c + megastring[n+1] in ALL_OPS:
                    self.end_word()
                    self.multi_char_op = True
                    self.add_to_word(c, n - self.line_start)
                #ennnnd of ze word
                else:
                    self.end_word()
                    #only single character constructs remain, so add them and
                    #include "bad_jokes.h"
                    #... END THEM
                    self.add_to_word(c, n - self.line_start)
                    self.end_word()
            else:
                self.add_to_word(c, n - self.line_start)

    def get_tokens(self):
        return self.tokens

class Errors(object):
    """Everyone's favourite"""
    (IF, ELSE, ELSEIF, RUNON, FUNCTION, GLOBALS, VARIABLE, TYPE,
            DEFINE, MISSING, CLOSING) = range(11)
    def __init__(self):
        self.naming_d = {}
        self.whitespace_d = {}
        self.comments_d = {}
        self.braces_d = {}
        self.line_length_d = {}
        self.func_length_d = {}
        self.total = 0

    def naming(self, token, name_type):
        self.total += 1
        msg = "WHOOPS"
        if name_type == Errors.TYPE:
            msg = " misnamed, types should be NamedLikeThis"
        elif name_type == Errors.FUNCTION:
            msg = " misnamed, functions should be named_like_this"
        elif name_type == Errors.DEFINE:
            msg = " misnamed, #defines should be NAMED_LIKE_THIS"
        elif name_type == Errors.VARIABLE:
            msg = " misnamed, variables should be namedLikeThis"
        self.naming_d[token.line_number] = "[NAMING] " + \
                token.get_string() + msg

    def whitespace(self, token, expected):
        self.total += 1
        assert token.get_spacing_left() != expected
        self.whitespace_d[token.line_number] = "[WHITESPACE] At " + \
                "position %d: expected %d whitespace, found %d " % (
                token.get_position(), expected, token.get_spacing_left())
        
    def line_length(self, line_number, length):
        self.total += 1
        self.line_length_d[line_number] = "line is %d chars long" % length

    def func_length(self, line_number, length):
        self.total += 1
        self.func_length_d[line_number] = "[OVERALL] Function length of" \
                + " %d is over the maximum of 50" % length

    def braces(self, token, error_type):
        self.total += 1
        msg = "WHOOPS"
        if error_type == Errors.IF:
            msg = ", if braces should look like: if (cond) {"
        elif error_type == Errors.ELSE:
            msg = ", else braces should look like: } else {"
        elif error_type == Errors.ELSEIF:
            msg = ", else if braces should look like: } else if (cond) {"
        elif error_type == Errors.RUNON:
            msg = ", an opening brace should be the last character on the line"
        elif error_type == Errors.MISSING:
            msg = ", braces are required, even for single line blocks"
        self.braces_d[token.line_number] = \
                "[BRACES] at position %d%s" % (token.get_position(), msg)

    def comments(self, line_number, error_type):
        self.total += 1
        msg = "WHOOPS"
        if error_type == Errors.FUNCTION:
            msg = "Functions should be preceeded by explanatory comments"
        elif error_type == Errors.GLOBALS:
            msg = "Global variables should be commented"
        self.comments[line_number] = msg

    def get(self, line_number):
        result = []
        for error_type in [self.braces_d, self.whitespace_d,
                self.line_length_d, self.naming_d, self.func_length_d,
                self.comments_d]:
            result.extend(error_type.get(line_number, []))
        return result

    def print_lines(self):
        for error_type in [self.braces_d, self.whitespace_d,
                self.line_length_d, self.naming_d, self.func_length_d,
                self.comments_d]:
            for key in sorted(error_type.keys()):
                print "line", key, ":", error_type[key]

    def __repr__(self):
        if not self.total:
            return "no errors found"
        counts = [len(error_type.keys()) for error_type in [
                self.braces_d, self.whitespace_d, self.comments_d,
                self.naming_d, self.func_length_d, self.line_length_d
                ]]
        for i in range(len(counts)):
            if counts[i] > 5:
                counts[i] = 5
        return " ".join(["%d total errors found, capped at " % self.total,
                "B:%d W:%d C:%d N:%d O:%d L:%d" % tuple(counts)])

class Styler(object):
    MAX = False
    """ Where style violations are born """
    def __init__(self, filename, verbose = True, output_file = False):
        #some setup
        self.errors = Errors()
        self.found_types = []
        #quick run for line lengths
        line_number = 0
        self.infile = open(filename, "r")
        for line in self.infile:
            line_number += 1
            if len(line) > 79:
                self.errors.line_length(line_number, len(line))
        self.infile.close()
        self.position = 0
        self.depth = 0
        self.comments = {}
        self.line_continuation = False
        #then the guts of it all
        tokeniser = Tokeniser(filename)
        self.tokens = tokeniser.get_tokens()
        self.current_token = self.tokens[self.position]
        try:
            while self.current_type() in [Type.NEWLINE, Type.COMMENT]:
                d(["pre-process: skipping newline/comment", self.current_token])
                if self.current_type() == Type.COMMENT:
                    self.check_whitespace()
                    self.comments[self.current_token.line_number] = True
                self.position += 1
                self.current_token = self.tokens[self.position]
            self.process_globals()
        except IndexError:
            #that'd be us finished
            pass
        #make sure no changes skip whitespace
        if DEBUG:
            for token in self.tokens:
                if token.get_type() not in [Type.NEWLINE, Type.LINE_CONT,
                        Type.COMMENT]:
                    if token.whitespace_checked == 0:
                        print "whitespace check missed:", token
                    elif token.whitespace_checked > 1:
                        print "whitespace check duplicated:", token
                    
        if output_file:
            self.write_output_file(filename)

        if verbose:
            self.errors.print_lines()

    def current_type(self):
        return self.current_token.get_type()    

    def match(self, req_type = Type.ANY, post_newline = NO_NEWLINE,
            pre_newline = NO_NEWLINE):
        #store interesting parts
        old = self.current_token
        d(["matching", old])
        if old.inner_tokens:
            if req_type != Type.ANY and old.get_type() != req_type:
                print "match fail:", old.get_type(), req_type
                assert old.get_type() == req_type
            if old.inner_position < len(old.inner_tokens) - 1:
                old.inner_position += 1
                old = old.inner_tokens[old.inner_position - 1]
            else:
                self.position += 1
                self.current_token = self.tokens[self.position]
                while self.current_token.get_type() in [Type.NEWLINE,
                        Type.COMMENT, Type.LINE_CONT]:
                    self.position += 1
                    self.current_token = self.tokens[self.position]
            return

        # ensure we're matching what's expected
        if req_type != Type.ANY and old.get_type() != req_type:
            print "match fail:", self.current_token, old.get_type(), req_type
            assert old.get_type() == req_type
       # do a whitespace check for semicolons
        if old.get_type() == Type.SEMICOLON:
            if self.previous_token().get_type() == \
                    [Type.COMMENT, Type.NEWLINE]:
                self.check_whitespace(self.depth * INDENT_SIZE)
            else:
                self.check_whitespace(0)
        # check pre-token newlines if {}
        elif old.get_type() in [Type.LBRACE, Type.RBRACE]:
            # previous was a newline but shouldn't have been
            if self.previous_token().get_type() in [Type.NEWLINE,
                    Type.COMMENT]:
                if pre_newline == NO_NEWLINE:
                    err = Errors.IF
                    if self.peek().get_type() == Type.ELSE:
                        err = Errors.ELSE
                    self.errors.braces(self.current_token, err)
            else: #previous wasn't a newline but should've been
                if pre_newline == MUST_NEWLINE:
                    self.errors.braces(self.current_token, Errors.RUNON)
        #update
        self.position += 1
        self.current_token = self.tokens[self.position] #deliberately unsafe
        
        # clear comments
        while self.current_type() == Type.COMMENT:
            self.comments[self.current_token.line_number] = True
            self.position += 1
            self.current_token = self.tokens[self.position]
       
        # check for extra post-token newlines
        if post_newline == NO_NEWLINE and self.current_type() \
                in [Type.NEWLINE, Type.LINE_CONT, Type.COMMENT]:
            if old.get_type() == Type.RBRACE:
                self.errors.braces(old, Errors.RUNON)
            
            if old.get_type() not in [Type.SEMICOLON, Type.LBRACE]:
                pass #self.line_continuation = True
        # check for missing post-token newlines
        elif post_newline == MUST_NEWLINE \
                and self.current_type() not in [Type.NEWLINE,
                Type.LINE_CONT, Type.COMMENT]:
            if old.get_type() not in [Type.LBRACE, Type.RBRACE]:
                pass #TODO for now, might have to add semicolon checks
            elif self.tokens[self.position-2].get_type() == Type.ELSE:
                self.errors.braces(self.previous_token(), Errors.ELSE)
            else:
                self.errors.braces(self.previous_token(), Errors.RUNON)
        # consume all the newlines that may or may not have been there
        while self.current_type() in [Type.NEWLINE, Type.LINE_CONT,
                Type.COMMENT]:
            self.position += 1
            self.current_token = self.tokens[self.position]

    def check_whitespace(self, expected = -1, one_or_zero = not ALLOW_ZERO):
        token = self.current_token
        #skip checks for tokens that are precompiler definitions 
        #(provided they aren't the first)
        if token.inner_tokens and token.inner_position != 0:
            return
        if expected == -1:
            expected = self.depth * INDENT_SIZE
        if self.line_continuation and token.get_type() != Type.RBRACE:
            expected = self.depth * INDENT_SIZE + LINE_CONTINUATION_SIZE
        if token.whitespace_checked and DEBUG:
            print "whitespace check duplicated:", token
            token.whitespace_checked += 1
            return
        token.whitespace_checked += 1
        if one_or_zero:
            if expected <= 1 and token.get_spacing_left() > 1:
                d(["whitespace \033[1merror\033[0m:", "expected", "1 or 0",
                        "with token", token, "but had",
                        token.get_spacing_left()])
                self.errors.whitespace(token, expected)
        elif token.get_spacing_left() != expected:
            d(["whitespace \033[1merror\033[0m:", "expected", expected,
                    "with token", token, "but had", token.get_spacing_left()])
            self.errors.whitespace(token, expected)
        if self.line_continuation:
            self.line_continuation = False

    def previous_token(self):
        return self.tokens[self.position - 1]

    def peek(self):
        i = self.position + 1
        while self.tokens[i].get_type() in [Type.COMMENT, Type.NEWLINE,
                Type.LINE_CONT]:
            i += 1
        return self.tokens[i]
    
    def has_matching_else(self):
        d(["has matching_else: starting at ", self.current_token])
        i = self.position
        depth = 0
        try:
            while self.tokens[i].get_type() not in [Type.IF, Type.RBRACE,
                    Type.ELSE]:
                i += 1
                if self.tokens[i].get_type() == Type.RBRACE:
                    depth -= 1
                    if depth >= 0:
                        i += 1
                elif self.tokens[i].get_type() == Type.LBRACE:
                    depth += 1
            d(["has matching_else: ending at ", self.tokens[i]])
            return self.tokens[i].get_type() == Type.ELSE
        except IndexError:
            d(["has matching_else: hit end of file"])
            return False

    def write_output_file(self, filename):
        """go over the file and insert messages when appropriate"""
        line_number = 1
        outf = open(filename+".style", "w")
        infile = open(filename, "r")
        for line in infile:
            outf.writelines(self.errors.get(line_number) + [line])
        infile.close()
        outf.close()

    def consume_line(self):
        while self.current_type() != Type.NEWLINE:
            d(["consume_line(): consuming:", self.current_token, 
                    self.current_type() == Type.NEWLINE])
            self.position += 1
            self.current_token = self.tokens[self.position]
        d(["consume_line(): consuming:", self.current_token])
        self.position += 1
        self.current_token = self.tokens[self.position]

    def match_type(self):
        d(["match_type(): entered", self.current_token])
        self.match() #the initial type/qualifier/specifier
        while self.current_type() in [Type.STRUCT, Type.TYPE,
                Type.IGNORE]:
            self.check_whitespace(1)
            self.match()
        # check if function pointer
        if self.current_type() == Type.LPAREN:
            self.check_whitespace(1)
            self.match(Type.LPAREN) #(
            self.check_whitespace(0)
            #allow for pointers to pointers
            while self.current_type() == Type.STAR:
                self.match(Type.STAR) #(*
                self.check_whitespace(0)
            #allow for non-declaration
            if self.current_type() == Type.UNKNOWN:
                self.match(Type.UNKNOWN) #(id
                self.check_whitespace(0)
            self.match(Type.LPAREN) #(id(
            self.check_whitespace(0)
            if self.current_type() != Type.RPAREN:
                self.match_type() #(id(types
                while self.current_type() == Type.COMMA:
                    self.check_whitespace(0)
                    self.match(Type.COMMA)
                    self.check_whitespace(1)
                    self.match_type() #(id(types,types
            self.check_whitespace(0)
            self.match(Type.RPAREN) #(id(types,types)
            self.check_whitespace(0)
            self.match(Type.RPAREN) #(id(types,types))
        # strip the pointers if
        elif self.current_type() == Type.STAR:
            self.check_whitespace(1, ALLOW_ZERO)
            self.match(Type.STAR)
            while self.current_type() == Type.STAR:
                self.check_whitespace(0)
                self.match(Type.STAR)
        d(["match_type(): exited", self.current_token])

    def process_globals(self):
        """ There's an assumption here that the code compiles to start with.
        Only checking the types of tokens that can start lines in this
        context (compiler directives, prototypes, declarations, definitions).
        """
        while True:
            d(["global space: ", self.current_token])
            self.check_whitespace(0)
            #check for compiler directives that aren't #define
            if self.current_type() == Type.HASH:
                self.check_precompile()
            #declaration
            elif self.current_type() == Type.TYPE:
                self.check_declaration()
            elif self.current_type() == Type.UNKNOWN:
                self.check_declaration(MISSING_TYPE)
            #function returning a function pointer, since it's complicated
            elif self.current_type() == Type.LPAREN:
                d(["dealing with a function prototype return value"])
                #example is (*indentifier())(char *, int)
                self.match(Type.LPAREN) #(
                self.check_whitespace(0)
                self.match(Type.STAR) #(*
                self.check_naming(self.current_token, Errors.FUNCTION)
                self.check_whitespace(1, ALLOW_ZERO)
                self.match(Type.UNKNOWN) #(*indentifier
                self.check_whitespace(0)
                self.match(Type.LPAREN) #(*indentifier(
                #match args to this func (including naming checks)
                self.check_whitespace(0)
                if self.current_type() != Type.RPAREN:
                    self.check_declaration()
                    while self.current_type() == Type.COMMA:
                        self.check_whitespace(1)
                        self.match(Type.COMMA)
                        self.check_whitespace(0)
                        self.check_declaration()
                    self.check_whitespace(0)
                self.match(Type.RPAREN) #(*indentifier()
                self.check_whitespace(0)
                self.match(Type.RPAREN) #(*indentifier())
                self.check_whitespace(0)
                self.match(Type.LPAREN) #(*indentifier())(
                self.check_whitespace(0)
                #match types of function pointer
                if self.current_type() != Type.RPAREN:
                    self.match_type()
                    self.check_whitespace(0)
                    while self.current_type() == Type.COMMA:
                        self.match(Type.COMMA)
                        self.check_whitespace(1)
                        self.match_type()
                self.check_whitespace(0)
                self.match(Type.RPAREN) #(*indentifier(...))(...)
                d(["finished with function prototype return value"])
                if self.previous_token() == Type.NEWLINE:
                    self.check_whitespace()
                else:
                    self.check_whitespace(1)
                self.match(Type.LBRACE, MUST_NEWLINE, MAY_NEWLINE)
                self.check_block()
                self.check_whitespace()
                self.match(Type.RBRACE, MUST_NEWLINE, MUST_NEWLINE)
            #type qualifiers
            elif self.current_type() == Type.IGNORE:
                self.match()
                self.check_declaration()
            #skippable
            elif self.current_type() in [Type.NEWLINE, Type.COMMENT]:
                self.match(Type.ANY, MUST_NEWLINE)
                continue
            #struct definition/declaration
            elif self.current_type() == Type.STRUCT:
                self.match()
                self.check_struct()
                self.match(Type.SEMICOLON, MUST_NEWLINE)
            #typedef
            elif self.current_type() == Type.TYPEDEF:
                self.match()
                self.check_typedef()
            #ruh roh
            else:
                print "found an awkward type in global space:", \
                        self.current_token
                self.match()

    def check_precompile(self):
        self.match(Type.HASH)
        self.check_whitespace(0)
        if self.current_type() == Type.INCLUDE:
            self.match(Type.INCLUDE)
            include_std = False
            include_name = []
            #include "stuff.h"
            if self.current_type() == Type.CONSTANT:
                self.check_whitespace(1)
                include_name.append(self.current_token.line)
                self.match(Type.CONSTANT, MUST_NEWLINE)
            #include <std_stuff.h>
            else:
                include_std = True
                self.check_whitespace(1)
                self.match() #<
                while self.current_token.line != ">":
                    include_name.append(self.current_token.line)
                    self.check_whitespace(0)
                    self.match()
                self.check_whitespace(0)
                self.match(Type.ANY, MUST_NEWLINE) #>
            include_name = "".join(include_name)
            new_types = []
            if include_std:
                new_types = headers.standard_header_types.get(include_name, -1)
                if new_types == -1:
                    print "".join([
                        "\nThe header <", include_name,
                        "> was not found in the preprocessed list.\n"
                        "Please report this to the maintainer so it ",
                        "can be fixed.\n",
                        "Since the parsing will likely break terribly due to ",
                        "unknown types\n(C is not a context free language), ",
                        "simpatico will end parsing now."])
                    exit(1)
            #custom header
            else:
                fun_with_recursion = Styler(include_name[1:-1]) #" "
                new_types = [x.line for x in fun_with_recursion.found_types]
            d(["including", len(new_types), "types from", include_name])
            #add the types
            self.update_types(new_types)                               
        #define
        elif self.current_type() == Type.DEFINE:
            self.match()
            self.check_define()
#TODO undefine
        elif self.current_type() == Type.PRECOMPILER:
            self.match(Type.PRECOMPILER)
            self.check_whitespace(1)
            self.consume_line()

    def update_types(self, new_types):
        self.found_types.extend(new_types)
        count = 0
        for token in self.tokens:
            #we use the actual token type here and not defined ones
            #that's because #defined overrides it and the inner ones will
            #update anyway
            if token._type == Type.UNKNOWN and token.line in new_types:
                token._type = Type.TYPE
                count += 1
        d(["updated token type for", count, "tokens"])

    def check_naming(self, token, name_type = Errors.VARIABLE):
        name = token.line
        if name_type == Errors.VARIABLE:
            if "_" in name or len(name) == 1 and name.isupper():
                self.errors.naming(token, name_type)
        elif name_type == Errors.FUNCTION:
            for c in name:
                if c.isupper():
                    self.errors.naming(token, name_type)
                    break
        elif name_type == Errors.TYPE:
            if "_" in name or not name[0].isupper():
                self.errors.naming(token, name_type)
        elif name_type == Errors.DEFINE:
            if not name.isupper():
                self.errors.naming(token, name_type)
        else:
            print "check_naming(): unknown naming type given: token=", token

    def check_struct(self, isTypedef = False):
        d(["check_struct() entered"])
        #skip the type name
        if self.current_type() == Type.UNKNOWN:
            self.check_whitespace(1)
            self.match(Type.UNKNOWN) # indentifier
        #ensure it's the block, then start it
        assert self.current_type() == Type.LBRACE
        self.check_whitespace(1)
        self.match(Type.LBRACE, MAY_NEWLINE, MAY_NEWLINE)
        self.check_block()
        self.check_whitespace()
        self.match(Type.RBRACE, MAY_NEWLINE, MAY_NEWLINE)
        if self.current_type() == Type.ATTRIBUTE:
            #ruh roh
            #TODO better manual checking required
            print "manual checking of __attribute__ tag required on line", \
                    self.current_token.line_number
            self.check_whitespace(1)
            self.match(Type.ATTRIBUTE)
            self.check_whitespace(1, ALLOW_ZERO)
            self.match(Type.LPAREN)
            depth = 1
            while depth != 0:
                if self.current_type() == Type.LPAREN:
                    depth += 1
                elif self.current_type() == Type.RPAREN:
                    depth -= 1
                self.check_whitespace(1, ALLOW_ZERO)
                self.match()
        d(["check_struct() exited", self.current_token])

    def check_typedef(self):
        d(["check_typedef() entered", self.current_token])
        if self.current_type() == Type.STRUCT:
            self.check_whitespace(1)
            self.match(Type.STRUCT)
            self.check_struct(IS_TYPEDEF)
            self.check_whitespace(1)
            ident = self.current_token.line
            for token in self.tokens:
                if token.line == ident:
                    token._type = Type.TYPE
            self.match(Type.TYPE)
        else:
            self.check_whitespace(1)
            self.match_type()
            identifier = self.current_token
            self.match(Type.UNKNOWN) #our shiny new type
            self.update_types([identifier])
        self.match(Type.SEMICOLON, MUST_NEWLINE)
        d(["check_typedef() exited", self.current_token])

    def check_for(self):
        d(["check_for() entered", self.current_token])
        self.match(Type.LPAREN)
        self.check_whitespace(0)
        d(["checking for init", self.current_token])
        if self.current_type() != Type.SEMICOLON:
            if self.current_type() == Type.TYPE:
                self.check_statement(True) #for (type thing;
            else:
                self.check_expression() #for (thing;
                self.match(Type.SEMICOLON)
        else:
            self.match(Type.SEMICOLON)
        d(["checking for conditional", self.current_token])
        self.check_whitespace(1)
        if self.current_type() != Type.SEMICOLON:
            self.check_expression() #for (thing; thing
        self.match(Type.SEMICOLON)
        self.check_whitespace(1)
        if self.current_type() != Type.RPAREN:
            d(["checking for post-loop", self.current_token])
            self.check_expression() #for (thing; thing; thing
        while self.current_type() == Type.COMMA:
            self.check_whitespace(1)
            self.match(Type.COMMA)
            self.check_whitespace(1)
            self.check_expression() #for (thing; thing; thing, ...)
        self.check_whitespace(0)
        self.match(Type.RPAREN)
        self.should_have_block()
        d(["check_for() exited", self.current_token])

    def should_have_block(self, is_chained = False):
        if self.current_type() == Type.LBRACE:
            self.check_whitespace(1)
            self.match(Type.LBRACE, MUST_NEWLINE) # {\n regardless
            self.check_block()
            self.check_whitespace() #based on current depth
            if is_chained:
                self.match(Type.RBRACE, NO_NEWLINE, MUST_NEWLINE) #\n}
            else:
                self.match(Type.RBRACE, MUST_NEWLINE, MUST_NEWLINE) #\n}\n
        else:
            self.check_whitespace((self.depth + 1) * INDENT_SIZE)
            self.errors.braces(self.current_token, Errors.MISSING)
            self.check_statement()

    def check_condition(self):
        # check spacing on the parenthesis
        self.check_whitespace(1, ALLOW_ZERO) # if/while (
        self.match(Type.LPAREN)
        self.check_whitespace(0) # (exp
        self.check_expression()
        self.check_whitespace(0) # exp)
        self.match(Type.RPAREN)

    def check_do(self):
        self.match(Type.LBRACE, MUST_NEWLINE)
        self.check_block()
        self.match(Type.RBRACE, NO_NEWLINE, MUST_NEWLINE)
        self.match(Type.WHILE)
        self.match(Type.LPAREN)
        if self.current_type() != Type.RPAREN:
            self.check_expression() # exp )
        self.match(Type.RPAREN)
        self.match(Type.SEMICOLON, MUST_NEWLINE)

    def check_switch(self):
        d(["check_switch(): entered", self.current_token])
        self.match(Type.LPAREN)
        self.check_whitespace(0)
        self.check_expression()
        self.check_whitespace(0)
        self.match(Type.RPAREN)
        self.check_whitespace(1)
        self.match(Type.LBRACE, MUST_NEWLINE)
        self.depth += 1
        while self.current_type() == Type.CASE:
            self.check_whitespace(self.depth * INDENT_SIZE)
            self.match(Type.CASE)
            self.check_whitespace(1)
            self.match(Type.CONSTANT)
            self.check_whitespace(0)
            self.match(Type.COLON, MUST_NEWLINE)
            self.check_case()
        if self.current_type() == Type.DEFAULT:
            self.check_whitespace(self.depth * INDENT_SIZE)
            self.match(Type.DEFAULT)
            self.check_whitespace(0)
            self.match(Type.COLON, MUST_NEWLINE)
            self.check_case()
        self.depth -= 1
        self.check_whitespace(self.depth * INDENT_SIZE)
        self.match(Type.RBRACE, MUST_NEWLINE, MUST_NEWLINE)
        d(["check_switch(): exited", self.current_token])

    def check_case(self):
        d(["check_case(): entered", self.current_token])
        while self.current_type() not in [Type.CASE, Type.DEFAULT]:
            if self.current_type() == Type.RBRACE:
                break #catches end of block
            self.check_whitespace((self.depth + 1) * INDENT_SIZE)
            self.check_statement()
        d(["check_case(): exited", self.current_token])

    def check_statement(self, in_for = False):
        d(["check_statement(): entered", self.current_token])
        if self.current_type() == Type.TYPE:
            self.check_declaration()
            self.match(Type.SEMICOLON, MUST_NEWLINE)
        elif self.current_type() == Type.UNKNOWN:
            self.check_expression()
            if self.current_type() == Type.ASSIGNMENT:
                self.check_whitespace(1)
                self.match(Type.ASSIGNMENT)
                self.check_whitespace(1)
                self.check_expression()
        if self.current_type() == Type.LPAREN:
            self.match(Type.LPAREN)
            self.check_whitespace(0)
            self.check_expression()
            self.match(Type.RPAREN)
            while self.current_type() in [Type.BINARY_OP, Type.ASSIGNMENT]:
                if self.current_type() == Type.BINARY_OP:
                    self.check_whitespace(1, ALLOW_ZERO)
                    self.match(Type.BINARY_OP)
                    self.check_whitespace(1, ALLOW_ZERO)
                else:
                    self.check_whitespace(1)
                    self.match(Type.ASSIGNMENT)
                    self.check_whitespace(1)
                self.check_expression()
            while self.current_type() == Type.COMMA:
                self.match(Type.COMMA)
                self.check_whitespace(1)
                self.check_expression()
        elif self.current_type() == Type.BREAK:
            self.match(Type.BREAK)
        elif self.current_type() == Type.RETURN:
            self.match(Type.RETURN)
            #return value?
            if self.current_type() != Type.SEMICOLON:
                self.check_whitespace(1)
                self.check_expression()
        elif self.current_type() == Type.CREMENT:
            self.check_whitespace(0)
            self.match(Type.CREMENT)
        if not in_for:
            self.match(Type.SEMICOLON, MUST_NEWLINE)
        d(["check_statement(): exited", self.current_token])

    def check_sizeof(self):
        d(["check_sizeof(): entered", self.current_token])
        #size of type
        if self.current_type() == Type.LPAREN:
            self.check_whitespace(0)
            self.match(Type.LPAREN)
            self.check_whitespace(0)
            self.match_type()
            self.check_whitespace(0)
            self.match(Type.RPAREN)
        #size of variable
        elif self.current_type() == Type.UNKNOWN:
            self.check_whitespace(1)
        else:
            print "check_sizeof(): unexpected token:", self.current_token
        
        d(["check_sizeof(): exited", self.current_token])

    def check_expression(self):
        d(["check_exp(): entered", self.current_token])
        #clear out any pre-value modifiers
        if self.current_type() == Type.AMPERSAND:
            self.match(Type.AMPERSAND)
            self.check_whitespace(0)
        elif self.current_type() == Type.STAR:
            self.match(Type.STAR)
            self.check_whitespace(0)
        elif self.current_type() == Type.MINUS:
            self.match(Type.MINUS)
            self.check_whitespace(0)
        elif self.current_type() == Type.CREMENT:
            self.match(Type.CREMENT)
            self.check_whitespace(0)
        elif self.current_type() == Type.LPAREN:
            self.match(Type.LPAREN)
            self.check_whitespace(0)
            #is this empty
            if self.current_type() == Type.RPAREN:
                pass
            #if it's not a typecast
            elif self.current_type() == Type.TYPE:
                self.match_type()
                self.check_whitespace(0)
            #match a whole new expression
            else:
                self.check_expression()
            self.match(Type.RPAREN)
            self.check_whitespace(1)                
        elif self.current_type() == Type.NOT:
            self.match(Type.NOT)
            self.check_whitespace(0)
        elif self.current_type() == Type.RPAREN:
            #end this
            self.match(Type.RPAREN)
            d(["check_exp(): exited", self.current_token])
            return
        elif self.current_type() not in [Type.UNKNOWN, Type.CONSTANT,
                Type.SIZEOF]:
            d(["check_exp(): unexpected token:", self.current_token])

        #grab a value of some form
        while self.current_type() in [Type.UNKNOWN, Type.CONSTANT,
                Type.SIZEOF, Type.ASSIGNMENT]:
            if self.current_type() == Type.SIZEOF:
                self.match(Type.SIZEOF)
                self.check_sizeof()
            elif self.current_type() == Type.ASSIGNMENT:
                self.check_whitespace(1)
                self.match(Type.ASSIGNMENT)
                self.check_whitespace(1)
                self.check_expression()
            else:
                self.match() #the value
            #get rid of post operators if they're there
            if self.current_type() == Type.CREMENT:
                self.check_whitespace(0)
                self.match(Type.CREMENT)
            #check if it was a function, check if it's being called
            #possibly also a indexing operation with equivalent contents
            while self.current_type() in [Type.LPAREN, Type.LSQUARE]:
                recovery = Type.RPAREN
                if self.current_type() == Type.LSQUARE:
                    recovery = Type.RSQUARE
                self.check_whitespace(0)
                self.match(Type.ANY)
                self.check_whitespace(0)
                #does it have args/index
                if self.current_type() != recovery:
                    #process first arg/index
                    self.check_expression()
                    #process others, if they exist (only for funcs)
                    while self.current_type() == Type.COMMA:
                        self.check_whitespace(0)
                        self.match(Type.COMMA)
                        self.check_whitespace(1)
                        self.check_expression()
                    self.check_whitespace(0)
                self.match(recovery)
            # now grab the operators before the next value
            while self.current_type() in [Type.CREMENT, Type.BINARY_OP,
                    Type.LOGICAL_OP, Type.MINUS, Type.STAR]:
                self.check_whitespace(1, ALLOW_ZERO)
                self.match() #'-- / - &&' etc
                self.check_whitespace(1, ALLOW_ZERO)
                self.check_expression()
        d(["check_exp(): exited", self.current_token])

    def check_block(self):
        d(["\nD: check_block(): entered", self.current_token])
        self.depth += 1
        #block ends if we hit the matching brace
        while self.current_type() != Type.RBRACE:
            d(["in block while: ", self.current_token])
            if self.current_type() == Type.HASH:
                self.check_whitespace(0)
                self.check_precompile()
            self.check_whitespace()
            if self.current_type() == Type.TYPE:
                self.check_declaration()
                if self.current_type() == Type.SEMICOLON:
                    self.match(Type.SEMICOLON, MUST_NEWLINE)
            elif self.current_type() == Type.STRUCT:
                self.match(Type.STRUCT)
                self.check_whitespace(1)
                self.match(Type.UNKNOWN) #the struct type
                first = True
                while first or self.current_type() == Type.COMMA:
                    if first:
                        first = False
                    else:
                        self.match(Type.COMMA)
                    if self.current_type() == Type.STAR: #them pointers again
                        self.check_whitespace(1, ALLOW_ZERO)
                        self.match(Type.STAR)
                        while self.current_type() == Type.STAR:
                            self.check_whitespace(0)
                            self.match(Type.STAR)
                        self.check_whitespace(1, ALLOW_ZERO)
                
                    self.check_whitespace(1)
                    #TODO check var name
                    self.match(Type.UNKNOWN)
                    if self.current_type() == Type.ASSIGNMENT:
                        self.check_whitespace(1)
                        self.match(Type.ASSIGNMENT)
                        self.check_whitespace(1)
                        #awkward types of struct initialisers to deal with
                        #if it's {.member = } style
                        if self.current_type() == Type.LBRACE:
                            d(["struct assignment {.x = ...} style"])
                            self.match(Type.LBRACE)
                            self.check_whitespace(0)
                            while self.current_type() == Type.BINARY_OP: # .
                                self.match(Type.BINARY_OP)
                                d(["next member", self.current_token])
                                self.check_whitespace(0)
                                self.match(Type.UNKNOWN)
                                self.check_whitespace(1)
                                self.match(Type.ASSIGNMENT)
                                self.check_whitespace(1)
                                self.check_expression()
                                self.check_whitespace(0)
                                if self.current_type() == Type.COMMA:
                                    self.match(Type.COMMA)
                                    self.check_whitespace(1)
                            self.match(Type.RBRACE, NO_NEWLINE)
                        #otherwise it's just a normal expression
                        else:
                            self.check_expression()
                self.match(Type.SEMICOLON)
            elif self.current_type() == Type.RETURN:
                self.match(Type.RETURN)
                if self.current_type() != Type.SEMICOLON:
                    self.check_whitespace(1)
                    self.check_expression()
                self.match(Type.SEMICOLON, MUST_NEWLINE)
            elif self.current_type() == Type.BREAK:
                self.match(Type.BREAK)
                self.match(Type.SEMICOLON, MUST_NEWLINE)
            elif self.current_type() == Type.CREMENT:
                self.match(Type.CREMENT)
                self.check_whitespace(0)
                self.match(Type.UNKNOWN) # identifier
                self.match(Type.SEMICOLON, MUST_NEWLINE)
            elif self.current_type() == Type.FOR:
                self.match(Type.FOR)
                self.check_whitespace(1, ALLOW_ZERO)
                self.check_for()
            elif self.current_type() == Type.WHILE:
                self.match(Type.WHILE)
                self.check_condition()
                self.should_have_block()
            elif self.current_type() == Type.DO:
                self.match(Type.DO)
                self.check_do()
            elif self.current_type() == Type.SWITCH:
                self.match(Type.SWITCH)
                self.check_whitespace(1)
                self.check_switch()
            elif self.current_type() == Type.SEMICOLON:
                self.match(Type.SEMICOLON, MUST_NEWLINE)
            elif self.current_type() == Type.IF:
                self.match(Type.IF)
                has_else = self.has_matching_else()
                d(["check_block(): ", self.previous_token(), 
                        " has else:", has_else])
                self.check_condition()
                self.should_have_block(has_else)
                while self.current_type() == Type.ELSE:
                    self.check_whitespace(1)
                    self.match(Type.ELSE)
                    if self.current_type() == Type.IF:
                        self.check_whitespace(1, ALLOW_ZERO)
                        self.match(Type.IF)
                        has_else = self.has_matching_else()
                        d(["check_block(): ", self.previous_token(), 
                                " has else:", has_else])
                        self.check_condition()
                        self.should_have_block(has_else)
                    else:
                        self.should_have_block() #else already
            elif self.current_type() == Type.UNKNOWN:
                self.check_statement()
            elif self.current_type() == Type.LBRACE:
                d(["found a block inside a block"])
                self.match(Type.LBRACE, MUST_NEWLINE, MUST_NEWLINE)
                self.check_block()
                self.check_whitespace()
                self.match(Type.RBRACE, MUST_NEWLINE, MUST_NEWLINE)
            elif self.current_type() == Type.LPAREN:
                self.check_statement()
            elif self.current_type() in [Type.CONSTANT, Type.SIZEOF]:
                #legit, but stupid
                self.check_expression()
                self.match(Type.SEMICOLON, MUST_NEWLINE)
            else:
                print "check_block(): unexpected token:", self.current_token
                self.match()
        self.depth -= 1
        d(["check_block(): exited", self.current_token, "\n"])

    def check_define(self):
#TODO mark it to be manually checked, since it's haaard to parse
        self.check_whitespace(1)
        first = self.current_token
        self.match() #the identifier (can't rely on it being Type.UNKNOWN)
        #is it a macro
        if self.current_type() == Type.LPAREN and \
                self.current_token.get_spacing_left() == 0:
            self.check_whitespace(0)
            #consume until newline for now
            #TODO but will have to be fixed later in case of awkwardness
            while self.current_type() != Type.NEWLINE:
                self.position += 1
                self.current_token = self.tokens[self.position]
                self.check_whitespace(1, ALLOW_ZERO)
            self.position += 1
            self.current_token = self.tokens[self.position]
        #just a plain identifier swap
        else:
            self.check_whitespace(1)
            tokens = []
            while self.current_type() not in [Type.NEWLINE,
                    Type.COMMENT]:
                tokens.append(self.current_token)
                self.position += 1
                self.current_token = self.tokens[self.position]
                self.check_whitespace(1, ALLOW_ZERO)
            self.match()
            if first._type == Type.UNKNOWN: #direct access deliberate
                if "".join(first.line).upper() != "".join(first.line):
                    self.errors.naming(first, Errors.DEFINE)
                #complicated
                if len(tokens) > 1:
                    for token in self.tokens:
                        if token.line == first.line:
                            token.inner_tokens = tokens
                #simple one-to-one
                else:
                    if tokens[0] != Type.UNKNOWN:
                        for n in xrange(self.position + 1, len(self.tokens)):
                            if self.tokens[n].line == first.line:
                                self.tokens[n]._type = tokens[0]._type
            #oh my, they #defined an existing symbol/keyword
            else:
                if len(tokens) > 1:
                    print "this is terrible, why do this to me"
#TODO violate them
                    for token in self.tokens:
                        if token._type == first._type:
                            token.inner_tokens = tokens
                else:
                    for n in xrange(self.position + 1, len(self.tokens)):
                        if self.tokens[n]._type == first._type:
                            self.tokens[n]._type = tokens[0]._type
        
    def check_array_assignment(self):
        if self.current_type() == Type.UNKNOWN:
            #assignment is to another variable
            self.check_whitespace(1)
            self.match() # identifier
            return
        self.match(Type.LBRACE, MAY_NEWLINE)
        self.check_whitespace(0)
        self.check_expression()
        while self.current_type() == Type.COMMA:
            self.check_whitespace(0)
            self.match(Type.COMMA)
            if self.current_type() == Type.LINE_CONT: # /
#TODO: more checking here, probs
                self.check_whitespace(1)
                self.match(Type.LINE_CONT)
            else:
                self.check_whitespace(1)
            self.check_expression()
        self.check_whitespace(0)
        self.match(Type.RBRACE, MAY_NEWLINE, MAY_NEWLINE)
        assert self.current_type() == Type.SEMICOLON

    def check_declaration(self, match_types = True):
        d(["check_declaration() entered", self.current_token])
        if match_types:
            self.match_type()
            #ALLOW_ZERO here because if it's not a pointer, zero spaces will
            #actually break C anyway
            self.check_whitespace(1, ALLOW_ZERO)
        else:
            d(["skipping types, match_types = False"])
        array = False
        name = self.current_token
        self.match(Type.UNKNOWN)
        #is this a function?
        if self.current_type() == Type.LPAREN:
            d(["decl is a func", self.previous_token()])
            self.check_naming(name, Errors.FUNCTION)
            self.check_whitespace(0)
            self.match(Type.LPAREN)
            self.check_whitespace(0)
#TODO need to chomp some args here and test naming
            #but for now
            if self.current_type() != Type.RPAREN:
                self.match_type() #type
                if self.current_type() == Type.UNKNOWN:
                    self.check_whitespace(1, ALLOW_ZERO)
                    self.match(Type.UNKNOWN)
                while self.current_type() == Type.COMMA:
                    self.check_whitespace(0)
                    self.match(Type.COMMA)
                    self.check_whitespace(1)
                    self.match_type()
                    self.check_whitespace(1, ALLOW_ZERO) #pointers again
                    self.match(Type.UNKNOWN)
            self.check_whitespace(0)
            self.match(Type.RPAREN)
            if self.current_type() == Type.LBRACE:
                start_line = self.current_token.line_number
                if self.previous_token().get_type() == Type.NEWLINE:
                    self.check_whitespace()
                else:
                    self.check_whitespace(1)
                self.match(Type.LBRACE, MUST_NEWLINE, MAY_NEWLINE)
                self.check_block()
                self.check_whitespace()
                self.match(Type.RBRACE, MUST_NEWLINE, MUST_NEWLINE)
                func_length = self.current_token.line_number - start_line
                if func_length >= 50:
                    self.errors.func_length(start_line, func_length)
            d(["check_declaration() exited a func", self.current_token])
            return
        d(["decl is a var", self.previous_token()])
        #well, it's a non-func then
        self.check_naming(self.previous_token(), Errors.VARIABLE)
        #is it an array?
        if self.current_type() == Type.LSQUARE:
            self.check_whitespace(0)
            self.match(Type.LSQUARE)
            self.check_expression()
            self.check_whitespace(0)
            self.match(Type.RSQUARE)
            array = True
            
        #token will now be , or = or ;
        if self.current_type() == Type.ASSIGNMENT:
            self.check_whitespace(1)
            self.match(Type.ASSIGNMENT)
            self.check_whitespace(1)
            if array:
                self.check_array_assignment()
                assert self.current_type() == Type.SEMICOLON
            else:
                self.check_expression()
        
        #is it a multi-var declaration?
        while self.current_type() == Type.COMMA:
            self.check_whitespace(0)
            self.match(Type.COMMA)
            self.check_whitespace(1)
            #in case this is pointers to the type
            while self.current_type() == Type.STAR:
                self.match(Type.STAR)
                if self.current_type() == Type.STAR:
                    self.check_whitespace(0)
                else:
                    self.check_whitespace(1, ALLOW_ZERO)
            self.match(Type.UNKNOWN) #identifier
            if self.current_type() == Type.ASSIGNMENT:
                self.check_whitespace(1)
                self.match(Type.ASSIGNMENT)
                self.check_whitespace(1)
                self.check_expression() #match out the expression
                continue
        if self.depth == 0: #since parent can't tell if it was func or not
            self.match(Type.SEMICOLON, MUST_NEWLINE)
        d(["check_declaration() exited", self.current_token])
            
if __name__ == '__main__':
    if (len(sys.argv)) == 1:
        print "no arguments given"
    for f in range(1, len(sys.argv)):
        if sys.argv[f].strip():
            print 'Parsing %s...' % sys.argv[f]
            style = Styler(sys.argv[f])
            print style.errors
            print "THIS IS NOT A GUARANTEE OF CORRECTNESS"

