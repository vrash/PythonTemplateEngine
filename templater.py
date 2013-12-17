#!/usr/bin/env python


import re
import operator
import ast
import json
import sys


#Create all predefined reg exp variables that define
#1. Variable - Individual variable substitutions
#2. Blocks - Blocks of code such as loops and conditionals
beginvar = '<*'
endvar = '*>'
beginblock = '<%'
endblock = '%>'

##regex we want = (\<\*.*?\*\> | \<\%.*?\%\>)
regexp = re.compile(r"(%s.*?%s|%s.*?%s)" % (
    re.escape(beginvar),
    re.escape(endvar),
    re.escape(beginblock),
    re.escape(endblock)
))

#Create holders for different types of blocks
variableshard = 0
beginblockshard = 1
endblockshard = 2
textshard = 3

#whitespaces holder
spacedout = re.compile('\s+')

operator_lookup_table = {
    '<': operator.lt,
    '>': operator.gt,
    '==': operator.eq,
    '!=': operator.ne,
    '<=': operator.le,
    '>=': operator.ge
}


class TemplateError(Exception):
    pass


class TemplateContextError(TemplateError):

    def __init__(self, context_var):
        self.context_var = context_var

    def __str__(self):
        return "cannot resolve '%s'" % self.context_var


class TemplateSyntaxError(TemplateError):

    def __init__(self, error_syntax):
        self.error_syntax = error_syntax

    def __str__(self):
        return "'%s' seems like invalid syntax" % self.error_syntax


def evaluatexp(expr):
    try:
        #print(expr)
        return 'literal', ast.literal_eval(expr)
    except ValueError:
        return 'name', expr


def resolve(name, context):
    if name.startswith('..'):
        context = context.get('..', {})
        name = name[2:]
    try:
        for tok in name.split('.'):
            context = context[tok]
        return context
    except KeyError:
        raise TemplateContextError(name)


class _Fragment(object):
    def __init__(self, raw_text):
        self.raw = raw_text
        self.clean = self.clean_fragment()

    def clean_fragment(self):
        if self.raw[:2] in (beginvar, beginblock):
            return self.raw.strip()[2:-2].strip()
        return self.raw

    @property
    def type(self):
        raw_start = self.raw[:2]
        #print(raw_start)
        if raw_start == beginvar:
            return variableshard
        elif raw_start == beginblock:
            return endblockshard if self.clean[:3].lower() == 'end' else beginblockshard
        else:
            return textshard

#The heart of the code -  class to hold node type and each variable type becomes a concrete
#subclass that implements process_shard and render
class _Node(object):
    creates_scope = False

    def __init__(self, fragment=None):
        self.children = []
        self.process_fragment(fragment)

    def process_fragment(self, fragment):
        pass

    def enter_scope(self):
        pass

    def render(self, context):
        pass

    def exit_scope(self):
        pass

    def render_children(self, context, children=None):
        if children is None:
            children = self.children
        def render_child(child):
            child_html = child.render(context)
            return '' if not child_html else str(child_html)
        return ''.join(map(render_child, children))


class _ScopableNode(_Node):
    creates_scope = True

class _Root(_Node):
    def render(self, context):
        return self.render_children(context)

#Concrete variable class
class _Variable(_Node):
    def process_fragment(self, fragment):
        self.name = fragment

    def render(self, context):
        return resolve(self.name, context)

#Looping 
class _Each(_ScopableNode):
    def process_fragment(self, fragment):
        try:
            _, it = spacedout.split(fragment, 1)
            self.it = evaluatexp(it)
        except ValueError:
            raise TemplateSyntaxError(fragment)

    def render(self, context):
        items = self.it[1] if self.it[0] == 'literal' else resolve(self.it[1], context)
        def render_item(item):
            return self.render_children({'..': context, 'it' : item})
        return ''.join(map(render_item, items))


#If conditionals
class _If(_ScopableNode):
    def process_fragment(self, fragment):
        bits = fragment.split()[1:]
        if len(bits) not in (1, 3):
            raise TemplateSyntaxError(fragment)
        self.lhs = eval_expression(bits[0])
        if len(bits) == 3:
            self.op = bits[1]
            self.rhs = eval_expression(bits[2])

    def render(self, context):
        lhs = self.resolve_side(self.lhs, context)
        if hasattr(self, 'op'):
            op = operator_lookup_table.get(self.op)
            if op is None:
                raise TemplateSyntaxError(self.op)
            rhs = self.resolve_side(self.rhs, context)
            exec_if_branch = op(lhs, rhs)
        else:
            exec_if_branch = operator.truth(lhs)
        if_branch, else_branch = self.split_children()
        return self.render_children(context,
            self.if_branch if exec_if_branch else self.else_branch)

    def resolve_side(self, side, context):
        return side[1] if side[0] == 'literal' else resolve(side[1], context)

    def exit_scope(self):
        self.if_branch, self.else_branch = self.split_children()

    def split_children(self):
        if_branch, else_branch = [], []
        curr = if_branch
        for child in self.children:
            if isinstance(child, _Else):
                curr = else_branch
                continue
            curr.append(child)
        return if_branch, else_branch

#Else of the conditionals
class _Else(_Node):
    def render(self, context):
        pass


class _Text(_Node):
    def process_fragment(self, fragment):
        self.text = fragment

    def render(self, context):
        return self.text


class Compiler(object):
    def __init__(self, template_string):
        self.template_string = template_string

    def each_fragment(self):
        for fragment in regexp.split(self.template_string):
            if fragment:
                yield _Fragment(fragment)

    def compile(self):
        root = _Root()
        scope_stack = [root]
        for fragment in self.each_fragment():
            if not scope_stack:
                raise TemplateError('nesting issues')
            parent_scope = scope_stack[-1]
            if fragment.type == endblockshard:
                parent_scope.exit_scope()
                scope_stack.pop()
                continue
            new_node = self.create_node(fragment)
            if new_node:
                parent_scope.children.append(new_node)
                if new_node.creates_scope:
                    scope_stack.append(new_node)
                    new_node.enter_scope()
        return root

    def create_node(self, fragment):
        node_class = None
        if fragment.type == textshard:
            node_class = _Text
        elif fragment.type == variableshard:
            node_class = _Variable
        elif fragment.type == beginblockshard:
            cmd = fragment.clean.split()[0]
            if cmd.lower() == 'each':
                node_class = _Each
            #Sample If else conditional classes
            elif cmd.lower() == 'if':
                node_class = _If
            elif cmd.lower() == 'else':
                node_class = _Else
        if node_class is None:
            raise TemplateSyntaxError(fragment)
        return node_class(fragment.clean)


class TemplateEngine(object):
    def __init__(self, contents):
        self.contents = contents
        self.root = Compiler(contents).compile()

    def render(self, **args):
        return self.root.render(args)


def main():
    if len(sys.argv)<>4:
        print("Usage: python templater.py file.template data.json output.html")
    else:
    #Get file arguments, comply with big brother
        jsonfile = sys.argv[2]
        templatefile = sys.argv[1]
        outputfile = sys.argv[3]
    #Read json
        with open(jsonfile) as f:
            jsondata = json.loads(f.read())
            #Read template
        with open(templatefile) as f:
            html = f.read()

        #perform jedi mind tricks
        template = TemplateEngine(html)

        #print output
        with open(outputfile, 'w') as f:
            rendered = template.render(**jsondata)
            f.write(rendered)
            #print (rendered)
        print("Process Completed")
     
if __name__ == "__main__":
    main()
