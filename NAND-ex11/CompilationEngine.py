import VMWriter as vmw
import SymbolTable as st
import JackTokenizer as tk

KEYWORD_CONST = ['true', 'false', 'null', 'this']
PRIM_VAR_TYPES = ['int', 'char', 'boolean']
OP = ["+", "-", "*", "/", "&amp;", "|", "&lt;", "&gt;", "="]
UNARY_OP = ["-", "~"]
STATEMENT_STARTERS = ["let", "if", "while", "do", "return"]
SYMBOL = 'SYMBOL'
KEYWORD = 'KEYWORD'
STRING_CONST = 'STRING_CONST'
INT_CONST = 'INT_CONST'
IDENTIFIER = 'IDENTIFIER'


# todo change this module to work with VMWriter.py. the API is the same


class CompilationEngine:
    def __init__(self, jack_lines):
        self._jack_lines = jack_lines
        self._token = tk.JackTokenizer(jack_lines)
        self._writer = vmw.VMWriter()
        self._table = st.SymbolTable()
        self._class = None
        self._cur_subroutine_ret_type = None

    def compile(self):
        self.compile_class()
        return self._writer.get_vm()

    def expect(self, e_type, value=None):
        if e_type == SYMBOL:
            if isinstance(value, list):
                if self._token.symbol() not in value:
                    raise SyntaxError("Expected" + str(value) + "symbol")
            else:
                if self._token.symbol() != value:
                    raise SyntaxError("Expected" + str(value) + "symbol")
            result = self._token.symbol()
            self._token.advance()
        elif e_type == KEYWORD:
            if isinstance(value, list):
                if self._token.keyword() not in value:
                    raise SyntaxError("Expected" + str(value) + "keyword")
            else:
                if self._token.keyword() != value:
                    raise SyntaxError("Expected" + str(value) + "keyword")
            result = self._token.keyword()
            self._token.advance()
        elif e_type == IDENTIFIER:
            if self._token.get_type() != IDENTIFIER:
                raise SyntaxError("Expected an identifier")
            result = self._token.identifier()
            self._token.advance()
        elif e_type == INT_CONST:
            if self._token.get_type() != INT_CONST:
                raise SyntaxError("Expected an int_const")
            result = self._token.int_val()
            self._token.advance()
        elif e_type == STRING_CONST:
            if self._token.get_type() != STRING_CONST:
                raise SyntaxError("Expected a string_const")
            result = self._token.string_val()
            self._token.advance()
        return result

    def compile_class(self):
        if not self._token.has_more_tokens():
            return
        self.expect(KEYWORD, 'class')
        self._class = self.expect(IDENTIFIER)
        self.expect(SYMBOL, '{')
        self.compile_class_var_dec()
        self.compile_subroutines()
        self.expect(SYMBOL, '}')

    def compile_var_name_sequence(self, type, kind):
        self._table.define(self.expect(IDENTIFIER), type, kind)
        if self._token.get_type() == SYMBOL:
            if self._token.symbol() == ';':
                self.expect(SYMBOL, ';')
                return True
        self.expect(SYMBOL, ',')
        return False

    def compile_class_var_dec(self):
        still_var_dec = True
        while still_var_dec:
            if self._token.keyword() in ['static', 'field']:
                # get 'static' or 'field'
                kind = self.expect(KEYWORD, ['static', 'field'])
                # get type of variable
                if self._token.get_type() == IDENTIFIER:
                    type = self.expect(IDENTIFIER)
                else:
                    type = self.expect(KEYWORD, PRIM_VAR_TYPES)
                done = False
                while not done:
                    done = self.compile_var_name_sequence(type, kind)
            else:
                still_var_dec = False
        return

    def compile_subroutines(self):
        while self.compile_subroutine():
            pass

    def func_kind_manager(self, kind):
        if kind == 'method':
            self._writer.write_push(vmw.ARG, 0)
            self._writer.write_pop(vmw.POINTER, 0)
        if kind == 'constructor':
            amount = self._table.var_count(st.FIELD)
            self._writer.write_push(vmw.CONST, amount)
            self._writer.write_function("Memory.alloc", 1)
            self._writer.write_pop(vmw.POINTER, 0)

    def compile_subroutine(self):
        self._table.start_subroutine()
        if self._token.get_type() == SYMBOL and \
                        self._token.symbol() == "}":
            return False
        if self._token.keyword() in ['constructor', 'function', 'method']:
            func_id = self.expect(KEYWORD,
                                  ['constructor', 'function', 'method'])
            if self._token.get_type() == KEYWORD:
                self._cur_subroutine_ret_type = self.expect(KEYWORD,
                                                            PRIM_VAR_TYPES +
                                                            ['void'])
            else:
                self._cur_subroutine_ret_type = self.expect(IDENTIFIER)
            name = '.'.join([self._class, self.expect(IDENTIFIER)])
            self.expect(SYMBOL, '(')
            if func_id == "method":
                self._table.define("this", "int", st.ARG)
            self.compile_parameter_list()
            self.expect(SYMBOL, ')')
            self.expect(SYMBOL, '{')
            n_locals = self.compile_var_dec()
            self._writer.write_function(name, n_locals)
            self.func_kind_manager(func_id)
            self.compile_statements()
            self.expect(SYMBOL, '}')
            # TODO free local objects ??
            return True
        return False

    def compile_parameter_list(self):
        var_counter = 0
        while self._token.get_type() != SYMBOL:
            var_counter += 1
            if self._token.get_type() == KEYWORD:
                type = self.expect(KEYWORD, PRIM_VAR_TYPES)
            else:
                type = self.expect(IDENTIFIER)
            name = self.expect(IDENTIFIER)
            self._table.define(name, type, "ARG")
            if self._token.symbol() != ')':
                self.expect(SYMBOL, ',')
        return var_counter

    def compile_var_dec(self):
        counter = 0
        while self._token.get_type() == KEYWORD \
                and self._token.keyword() == "var":
            self.expect(KEYWORD, "var")
            counter += 1
            if self._token.get_type() == IDENTIFIER:
                type = self.expect(IDENTIFIER)
            else:
                type = self.expect(KEYWORD, PRIM_VAR_TYPES)
            self._table.define(self.expect(IDENTIFIER), type, st.LOCAL)
            while self._token.get_type() == SYMBOL \
                    and self._token.symbol() == ",":
                self.expect(SYMBOL, ',')
                self._table.define(self.expect(IDENTIFIER), type, st.LOCAL)
            self.expect(SYMBOL, ';')
        return counter

    def compile_statements(self):
        while self.compile_statement():
            pass

    def compile_statement(self):
        if self._token.get_type() == KEYWORD and \
                        self._token.keyword() in STATEMENT_STARTERS:
            if self._token.keyword() == 'let':
                self.compile_let()
            elif self._token.keyword() == 'if':
                self.compile_if()
            elif self._token.keyword() == 'while':
                self.compile_while()
            elif self._token.keyword() == 'do':
                self.compile_do()
            elif self._token.keyword() == 'return':
                self.compile_return()
            return True
        return False

    def compile_do(self):
        self.expect(KEYWORD, 'do')
        self.compile_subroutine_call()
        self.expect(SYMBOL, ';')

    def compile_let(self):
        # 'let' keyword
        self.expect(KEYWORD, 'let')
        # varName
        name = self.expect(IDENTIFIER)
        is_an_array_var = False
        # ( '[' expression ']' )?  - optional
        if self._token.get_type() == SYMBOL and self._token.symbol() == '[':
            is_an_array_var = True
            self._writer.write_push(self._table.kind_of(name),
                                    self._table.index_of(name))
            self.expect(SYMBOL, '[')
            self.compile_expression()
            self.expect(SYMBOL, ']')
            self._writer.write_arithmetic("ADD")
        # '=' symbol
        self.expect(SYMBOL, '=')
        # expression
        self.compile_expression()
        # ';' symbol
        self.expect(SYMBOL, ';')
        if is_an_array_var:
            self._writer.write_pop(vmw.TEMP, 0)
            self._writer.write_pop(vmw.POINTER, 1)
            self._writer.write_push(vmw.TEMP, 0)
            self._writer.write_pop(vmw.THAT, 0)
        else:
            self._writer.write_pop(self._table.kind_of(name),
                                   self._table.index_of(name))

    def compile_while(self):
        # 'while' keyword
        self.expect(KEYWORD, 'while')
        # '(' symbol
        self.expect(SYMBOL, '(')
        # expression
        self.compile_expression()
        # ')' symbol
        self.expect(SYMBOL, ')')
        # '{' symbol
        self.expect(SYMBOL, '{')
        # statements
        self.compile_statements()
        # '}' symbol
        self.expect(SYMBOL, '}')

    def compile_return(self):
        # 'return' keyword
        self.expect(KEYWORD, 'return')
        # expression? - optional
        if self._cur_subroutine_ret_type != 'void':
            self.compile_expression()
        else:
            self._writer.write_push(vmw.CONST, 0)
        # ';' symbol
        self.expect(SYMBOL, ';')
        self._writer.write_return()

    def compile_if(self):
        # 'if' keyword
        self.expect(KEYWORD, 'if')
        # '(' symbol
        self.expect(SYMBOL, '(')
        # expression
        self.compile_expression()
        # ')' symbol
        self.expect(SYMBOL, ')')
        # '{' symbol
        self.expect(SYMBOL, '{')
        # statements
        self.compile_statements()
        # '}' symbol
        self.expect(SYMBOL, '}')
        # (else clause) - optional
        if self._token.get_type() == KEYWORD and \
                        self._token.keyword() == 'else':
            # 'else' keyword
            self.expect(KEYWORD, 'else')
            # '{' symbol
            self.expect(SYMBOL, '{')
            # statements
            self.compile_statements()
            # '}' symbol
            self.expect(SYMBOL, '}')

    def compile_expression(self, mandatory=True):
        # term - mandatory
        if not self.compile_term():
            self._vm.pop()
            if mandatory:
                raise SyntaxError("Expected term")
            else:
                return False
        # (op term)*
        while self._token.get_type() == SYMBOL and self._token.symbol() in OP:
            self.expect(SYMBOL, OP)
            self.compile_term()
        return True

    def compile_term(self):
        if self._token.get_type() == INT_CONST:
            value = self.expect(INT_CONST)
            self._writer.write_push(vmw.CONST, value)
        elif self._token.get_type() == STRING_CONST:
            string = self.expect(STRING_CONST)
            self.string_constant_manager(string)
        elif self._token.get_type() == KEYWORD \
                and self._token.keyword() in KEYWORD_CONST:
            keyword = self.expect(KEYWORD, KEYWORD_CONST)
            if keyword == "true":
                self._writer.write_push(vmw.CONST, 0)
                self._writer.write_arithmetic("neg")
            elif keyword in ["null", "false"]:
                self._writer.write_push(vmw.CONST, 0)
            elif keyword == "this":
                self._writer.write_push(vmw.POINTER, 0)
        elif self._token.get_type() == SYMBOL:
            if self._token.symbol() == '(':
                self.expect(SYMBOL, '(')
                self.compile_expression()
                self.expect(SYMBOL, ')')
            elif self._token.symbol() in UNARY_OP:
                op = self.expect(SYMBOL, UNARY_OP)
                self.compile_term()
                if op == "-":
                    self._writer.write_arithmetic("NEG")
                elif op == "~":
                    self._writer.write_arithmetic("NOT")
            else:
                return False
        elif self._token.get_type() == IDENTIFIER:
            next_token, next_type = self._token.peak(1)
            if next_type == SYMBOL and next_token in ['(', '.']:
                self.compile_subroutine_call()
            elif next_type == SYMBOL and next_token == '[':
                var_name = self.expect(IDENTIFIER)
                kind = self._table.kind_of(var_name)
                if kind in [st.STATIC, st.ARG, st.LOCAL]:
                    self._writer.write_push(kind, self._table.index_of(var_name))
                elif kind == st.FIELD:
                    self._writer.write_push(vmw.THIS, self._table.index_of(var_name))
                self.expect(SYMBOL, '[')
                self.compile_expression()
                self.expect(SYMBOL, ']')
                self._writer.write_arithmetic("ADD")
                self._writer.write_pop(vmw.POINTER, 1)
                self._writer.write_push(vmw.THAT, 0)
            else:
                var_name = self.expect(IDENTIFIER)
                self.push_variable(var_name)


        else:
            # self._vm.pop() TODO check this shit
            return False
        return True

    def compile_expression_list(self):
        arg_count = 0
        if self.compile_expression(mandatory=False):
            arg_count += 1
            while self._token.get_type() == SYMBOL \
                    and self._token.symbol() == ',':
                self.expect(SYMBOL, ',')
                self.compile_expression()
                arg_count += 1
        return arg_count

    def compile_subroutine_call(self):
        n_args = 0
        name = self.expect(IDENTIFIER)
        if self._token.get_type() == SYMBOL and self._token.symbol() == ".":
            # indicated it is a function call operated on an object
            if self._table.index_of(name):
                n_args = 1
                self.push_variable(name)
                name = self._table.type_of(name)
            name += self.expect(SYMBOL, '.')
            name += self.expect(IDENTIFIER)
        else:
            name = '.'.join([self._class, name])
            if self._table.index_of("this"):
                pass
            else:
                raise SyntaxError('subroutine() calls can only be used in'
                                  'a method or a constructor')
        # check if method or function
        # if method - push this pointer to stack + increase n_args
        self.expect(SYMBOL, '(')
        n_args += self.compile_expression_list()
        self.expect(SYMBOL, ')')
        self._writer.write_call(name, n_args)


        # n_args += self.compile_parameter_list()

    def string_constant_manager(self, string):
        length = len(string)
        self._writer.write_push(vmw.CONST, length)
        self._writer.write_call("String.new", 1)
        for char in string:
            # push char to stack
            # call appendChar on the returned string
            pass

    def push_variable(self, var_name):
        kind = self._table.kind_of(var_name)
        if kind in [st.STATIC, st.ARG, st.LOCAL]:
            self._writer.write_push(kind, self._table.index_of(var_name))
        elif kind == st.FIELD:
            self._writer.write_push(vmw.THIS, self._table.index_of(var_name))
