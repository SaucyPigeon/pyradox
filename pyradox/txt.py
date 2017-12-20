import pyradox.config
import pyradox.primitive
import pyradox.struct
import pyradox.color
import re
import os
import warnings

from pyradox.error import ParseError, ParseWarning

gameEncodings = {
    'EU4' : ['cp1252', 'utf_8_sig'],
    'HoI3' : ['cp1252', 'utf_8_sig'],
    'HoI3_vanilla' : ['cp1252', 'utf_8_sig'],
    'HoI4' : ['utf_8_sig', 'cp1252'],
    'HoI4_beta' : ['utf_8_sig', 'cp1252'],
    'Stellaris' : ['utf_8_sig', 'cp1252'],
}
        
def readlines(filename, encodings):
    for encoding in encodings:
        try:
            f = open(filename, encoding=encoding)
            lines = f.readlines()
            f.close()
            return lines
        except UnicodeDecodeError:
            warnings.warn(ParseWarning("Failed to decode input file %s using codec %s." % (filename, encoding)))
            f.close()
    raise ParseError("All codecs failed for input file %s." % filename)

def parse(s, filename=""):
    """Parse a string."""
    lines = s.splitlines()
    tokenData = lex(lines, filename)
    return parseTree(tokenData, filename)

def parseFile(filename, verbose=False, game=None):
    """Parse a single file and return a Tree."""
    if game is None: game = pyradox.config.getDefaultGame()
    encodings = gameEncodings[game]
    
    lines = readlines(filename, encodings)
    if verbose: print('Parsing file %s.' % filename)
    tokenData = lex(lines, filename)
    return parseTree(tokenData, filename)
    
def parseDir(dirname, *args, **kwargs):
    """Given a directory, iterate over the content of the .txt files in that directory as Trees"""
    for filename in os.listdir(dirname):
        fullpath = os.path.join(dirname, filename)
        if os.path.isfile(fullpath):
            _, ext = os.path.splitext(fullpath)
            if ext == ".txt":
                yield filename, parseFile(fullpath, *args, **kwargs)

def parseMerge(dirname, mergeLevels = 0, *args, **kwargs):
    """Given a directory, return a Tree as if all .txt files in the directory were a single file"""
    result = pyradox.struct.Tree()
    for filename in os.listdir(dirname):
        fullpath = os.path.join(dirname, filename)
        if os.path.isfile(fullpath):
            _, ext = os.path.splitext(fullpath)
            if ext == ".txt":
                tree = parseFile(fullpath, *args, **kwargs)
                result.merge(tree, mergeLevels)
    return result

def parseWalk(dirname, *args, **kwargs):
    """Given a directory, recursively iterate over the content of the .txt files in that directory as Trees"""
    for root, dirs, files in os.walk(dirname):
        for filename in files:
            fullpath = os.path.join(root, filename)
            _, ext = os.path.splitext(fullpath)
            if ext == ".txt":
                yield filename, parseFile(fullpath, *args, **kwargs)

# open questions:
# what characters are allowed in key strings?
# in value strings?
# are there escape characters?

tokenTypes = [
    # keysymbols
    ('whitespace', r'\s+'),
    ('operator', r'[=><]'),
    ('begin', r'\{'),
    ('end', r'\}'),
    ('comment', r'#.*'),
    ] + pyradox.primitive.tokenPatterns

omnibusPattern = ''
for tokenType, p in tokenTypes:
    omnibusPattern += '(?P<' + tokenType + '>' + p + ')'
    omnibusPattern += '|'
omnibusPattern += '(.+)'

omnibusPattern = re.compile(omnibusPattern)

def lex(fileLines, filename):
    return list(lexIter(fileLines, filename))

def lexIter(fileLines, filename):
    """Lexer. Given the contents of a file, produces a list of (tokenType, tokenString, lineNumber)."""
    return (
        (m.lastgroup, m.group(0), lineNumber)
        for lineNumber, line in enumerate(fileLines)
        for m in omnibusPattern.finditer(line) if m.lastgroup not in ('whitespace',)
        )
        
class TreeParseState():
    def __init__(self, tokenData, filename, startPos, isTopLevel):
        self.tokenData = tokenData          # The tokenized version of the file. List of (tokenType, tokenString, tokenLineNumber) tuples.
        self.filename = filename            # File the tree is being parsed from. Used for warning and error messages.
        self.isTopLevel = isTopLevel        # True iff this tree is the top level of the file.
    
        self.result = pyradox.struct.Tree() # The resulting tree.
        
        self.pos = startPos                 # Current token position.
        self.pendingComments = []           # Comments pending assignment.
        self.key = None                     # The key currently being processed.
        self.keyString = None               # The original token string for that key.
        self.operator = None                # The operator currently being processed. Usually '='.
        self.next = self.processKey         # The next case to execute.
    
    def getPreviousLineNumber(self):
        """ Line number of the token just before the one consumed. Returns -1 if the token just consumed was the first one."""
        if len(self.tokenData) > 0 and self.pos > 1:
            return self.tokenData[self.pos-2][2]
        return -1
    
    def parse(self):
        """ Called once to parse. """
        while self.pos < len(self.tokenData):
            if self.next is not None:
                self.next() # Keep parsing.
            else:
                self.appendPostComments()
                return self.result, self.pos
        
        # End of file reached.
        if self.isTopLevel:
            self.appendPostComments()
            return self.result
        else:
            raise ParseError('%s, line %d: Error: Cannot end inner level with end of file.' % (self.filename, self.getPreviousLineNumber() + 1))
    
    def consume(self):
        """ Read the next tuple from the list and advance the position counter. """
        tokenType, tokenString, tokenLineNumber = self.tokenData[self.pos]
        self.pos += 1
        return tokenType, tokenString, tokenLineNumber
        
    def appendToResult(self, value, **kwargs):
        """ 
        Append the current value to result. 
        key and operator are set by internal state. 
        Also consumes any pending comments.
        """
        self.result.append(self.key, value, preComments = self.pendingComments, operator = self.operator, **kwargs)
        self.pendingComments = []
        
    def appendLineComment(self, comment):
        """
        Appends a line comment if not already set; otherwise appends to postComments.
        """
        
        if self.result.getLineCommentAt(-1) is None:
            self.result.setLineCommentAt(-1, comment)
        else:
            self.result.getPostCommentsAt(-1).append(comment)
        
    def appendPostComments(self):
        """
        Consumes pending comments and adds them to the last item's postComments.
        """
        postComments = self.result.getPostCommentsAt(-1) 
        postComments += self.pendingComments
        self.pendingComments = []
        
    def processKey(self):
        tokenType, tokenString, tokenLineNumber = self.consume()
        
        if pyradox.primitive.isPrimitiveKeyTokenType(tokenType):
            self.keyString = tokenString
            self.key = pyradox.primitive.makePrimitive(tokenString, tokenType)
            self.next = self.processOperator
        elif tokenType == 'comment':
            if tokenLineNumber == self.getPreviousLineNumber():
                # Comment following a previous value.
                self.appendLineComment(tokenString[1:])
            else:
                self.pendingComments.append(tokenString[1:])
            self.next = self.processKey
        elif tokenType == 'end':
            if self.isTopLevel:
                # top level cannot be ended, warn
                warnings.warn_explicit('Unmatched closing bracket. Skipping token.', ParseWarning, self.filename, tokenLineNumber + 1)
                self.next = self.processKey
            else:
                self.next = None
        else:
            #invalid key
            warnings.warn_explicit('Token "%s" is not valid key. Skipping token.' % tokenString, ParseWarning, self.filename, tokenLineNumber + 1)
            self.next = self.processKey
    
    def processOperator(self):
        # expecting an operator
        tokenType, tokenString, tokenLineNumber = self.consume()
        
        if tokenType == 'operator':
            self.operator = tokenString
            self.next = self.processValue
        elif tokenType == 'comment':
            self.pendingComments.append(tokenString[1:])
            self.next = self.processOperator
        else:
            # missing operator; unconsume the token and move on
            warnings.warn_explicit('Expected operator after key "%s". Treating operator as "=" and token "%s" as value.' % (self.keyString, tokenString), ParseWarning, self.filename, tokenLineNumber + 1)
            self.pos -= 1
            self.operator = '='
            self.next = self.processValue
        
    def processValue(self):
        # expecting a value
        tokenType, tokenString, tokenLineNumber = self.consume()
        
        if pyradox.primitive.isPrimitiveValueTokenType(tokenType):
            maybeColor = self.maybeSubprocessColor(tokenString, tokenLineNumber)
            if maybeColor is not None:
                value = maybeColor
            else:
                # normal value
                value = pyradox.primitive.makePrimitive(tokenString, tokenType)
            self.appendToResult(value)
            self.next = self.processKey
        elif tokenType == 'begin':
            # Value is a tree or group. First, determine whether this is a tree or group.
            lookaheadPos = self.pos
            level = 0
            # Empty brackets are trees.
            isTree = True
            while lookaheadPos < len(self.tokenData) and level >= 0:
                tokenType, tokenString, tokenLineNumber = self.tokenData[lookaheadPos]
                lookaheadPos += 1
                if tokenType == 'end':
                    level -= 1
                elif tokenType == 'comment':
                    continue
                else:
                    # Non-empty brackets are groups unless an operator is found.
                    isTree = False
                
                    if tokenType == 'begin':
                        # Assume any nesting indicates a tree.
                        isTree = True
                        break
                        # level += 1
                    elif tokenType == 'operator':
                        # Tree if operator detected at current level.
                        if level == 0: 
                            isTree = True
                            break
            if isTree:
                # Recurse.
                value, self.pos = parseTree(self.tokenData, self.filename, self.pos)
                self.appendToResult(value)
                self.next = self.processKey
            else:
                # Go to group state.
                self.next = self.processGroup
                
        elif tokenType == 'comment':
            self.pendingComments.append(tokenString[1:])
            self.next = self.processValue
        else:
            raise ParseError('%s, line %d: Error: Invalid token type %s after key "%s", expected a value type.' % (self.filename, tokenLineNumber + 1, tokenType, self.keyString))
        
    def maybeSubprocessColor(self, colorspaceTokenString, colorspaceTokenLineNumber):
        # Try to parse a color. 
        # Return the color if this is a color and change the parser state to match. 
        # Otherwise, return None with no change in parser state.
        colorspace = colorspaceTokenString.lower()
        
        if colorspace not in pyradox.color.Color.COLORSPACES:
            return None
        
        # Possible comments to add.
        maybePreComments = []
        
        # Expected sequence of non-comment tokens.
        COLOR_SEQUENCE = [['begin']] + [['int', 'float']] * 3 + [['end']]
        
        # Current position in the sequence.
        seq = 0
        
        channels = []
        
        maybePos = self.pos
        
        while maybePos < len(self.tokenData):
            tokenType, tokenString, tokenLineNumber = self.tokenData[maybePos]
            maybePos += 1
            if tokenType == 'comment':
                maybePreComments.append(tokenString)
            elif tokenType in COLOR_SEQUENCE[seq]:
                if tokenType in ['int', 'float']:
                    channels.append(pyradox.primitive.makePrimitive(tokenString, tokenType))
                seq += 1
                if seq >= len(COLOR_SEQUENCE):
                    # Finished color. Update state.
                    self.pendingComments += maybePreComments
                    self.pos = maybePos
                    color = pyradox.color.Color(channels, colorspace)
                    return color
            else:
                # Unexpected token.
                break
        
        warnings.warn_explicit('Found colorspace token %s without following color.' % (colorspaceTokenString.lower()), ParseWarning, self.filename, colorspaceTokenLineNumber)
        return None
        
    def processGroup(self):
        tokenType, tokenString, tokenLineNumber = self.consume()
        
        if pyradox.primitive.isPrimitiveValueTokenType(tokenType):
            value = pyradox.primitive.makePrimitive(tokenString, tokenType)
            self.appendToResult(value, inGroup = True)
        elif tokenType == "comment":
            if tokenLineNumber == self.getPreviousLineNumber():
                self.appendLineComment(tokenString[1:])
            else:
                self.pendingComments.append(tokenString[1:])
        elif tokenType == "end":
            self.appendPostComments()
            self.next = self.processKey
        elif tokenType == "begin":
            raise ParseError('%s, line %d: Error: Cannot nest inside a group.' % (filename, tokenLineNumber + 1))
        else:
            raise ParseError('%s, line %d: Error: Invalid value type %s.' % (filename, tokenLineNumber + 1, tokenType))

def parseTree(tokenData, filename, startPos = 0):
    """Given a list of (tokenType, tokenString, lineNumber) from the lexer, produces a Tree."""
    isTopLevel = (startPos == 0)
     # if starting position is 0, check for extra token at beginning
    if startPos == 0 and len(tokenData) >= 1 and tokenData[0][1] == 'EU4txt':
        tokenType, tokenString, lineNumber = tokenData[0]
        print('%s, line %d: Skipping header token "%s".' % (filename, lineNumber + 1, tokenString))
        startPos = 1 # skip first token
    
    state = TreeParseState(tokenData, filename, startPos, isTopLevel)
    return state.parse()
